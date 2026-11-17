"""Evaluate sealed policies across registered final contexts, with no fitting."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from itertools import product
import json,logging,argparse,multiprocessing,hashlib,time
import torch
from pcse_gym.agromas.final_evaluation import replay_final_book,validate_external_dependency,ppo_assets
from pcse_gym.agromas.legacy_comparators import run_nl_reference
from pcse_gym.agromas.regions import frozen_asset_sha,REGIONS
from pcse_gym.agromas.runtime import outcome_model,variant_model
from pcse_gym.agromas.features import forecast_model
from pcse_gym.agromas.season import regional_weather,_template
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5';PERMIT=P/'final-evaluation-permit-v4.json'
D=R/'data/phase5-final-evaluation-books-v4';O=P/'final-policy-results-v4'
ARMS=('A0','A1','A2','A2-oracle','A3','A4','LOAO-climate','LOAO-eco','LOAO-core-state','DVS-N2')

def run(path):
 logging.disable(logging.CRITICAL);torch.set_num_threads(1);start=time.monotonic()
 expected=json.loads((P/'final-physical-book-receipt-v4.json').read_text())
 digest={x['path']:x['sha256'] for x in expected['files']}[str(path.relative_to(R))]
 if frozen_asset_sha(path)!=digest:raise ValueError('Physicalbookdrift')
 book={tuple(r['plan']):r for r in map(json.loads,path.read_text().splitlines())}
 assert len(book)==343 and all(r['status']=='completed' for r in book.values())
 first=book[(0.,0.,0.)];climate=first['climate'];contexts=list(product(('strict_25','buffer_35','outer_50'),(1.,2.),(0,50,100,150,200)))
 if climate=='Historical':contexts.append(('standard_40',1.,0))
 out=O/path.name;count=0
 # References are physical once per NLweather/climate; prices/caps only rescore actual outcome.
 refs=[]
 if first['region_id']=='netherlands_lelystad':
  for policy in ('N2-PA-calendar','Phase4-Forest-transfer'):
   refs.append(run_nl_reference(str(R),first['harvest_year'],policy=policy,role=first['role'],climate=climate,permit_path=str(PERMIT)))
 with out.open('x') as f:
  for zone,price,subsidy in contexts:
   kwargs=dict(zone=zone,price_multiplier=price,subsidy=subsidy,beta=200,permit_path=str(PERMIT))
   for arm in ARMS:
    row=replay_final_book(str(R),book,policy=arm,**kwargs)
    f.write(json.dumps(row,default=str)+'\n');count+=1
   for mode,seed in product(('structured-shared','raw-shared'),(4,17,29)):
    row=replay_final_book(str(R),book,policy='PPO',mode=mode,seed=seed,**kwargs)
    f.write(json.dumps(row,default=str)+'\n');count+=1
   cap={'strict_25':25.,'buffer_35':35.,'standard_40':40.,'outer_50':50.}[zone]
   for reference in refs:
    row=dict(reference);m=row['outcome'];joint=.5<=m[3]<=.9 and m[2]<=cap
    row.update(zone=zone,cap=cap,price_multiplier=price,subsidy=subsidy,seed=None,information_mode='legacy-reference',beta=None,
     joint=bool(joint),NUE_compliant=bool(.5<=m[3]<=.9),surplus_upper_compliant=bool(m[2]<=cap),surplus_corridor_compliant=bool(0<=m[2]<=cap),
     partial_profit=float(200*m[0]-1.5*price*m[4]+subsidy*joint),plan=[e['dose'] for e in row['events']],
     physical_source_id=f"NL-reference:{row['policy']}:{row['harvest_year']}:{climate}")
    f.write(json.dumps(row,default=str)+'\n');count+=1
 out.chmod(0o444)
 return dict(path=str(out.relative_to(R)),rows=count,sha256=hashlib.sha256(out.read_bytes()).hexdigest(),elapsed_seconds=time.monotonic()-start)

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--workers',type=int,choices=[16,24,32,48],default=32);args=parser.parse_args()
 p=json.loads((P/'final-physical-book-receipt-v4.json').read_text());assert p['status']=='completed' and p['failures']==0
 validate_external_dependency(R,PERMIT)
 torch.set_num_threads(1)
 # Fork shares immutable model arrays and avoids racing the derived crop cache.
 for stage in (1,2,3):
  outcome_model(str(R),stage)
  for family in ('A1','A2','A2-oracle','A3','LOAO-climate','LOAO-eco','LOAO-core-state'):variant_model(str(R),stage,family)
 for name in REGIONS:forecast_model(str(R),name);regional_weather(str(R),name,'v2')
 for mode,seed in product(('structured-shared','raw-shared'),(4,17,29)):ppo_assets(str(R),mode,seed)
 _template(str(R))
 O.mkdir(exist_ok=False);rows=[];start=time.monotonic()
 with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('fork')) as pool:
  for future in as_completed([pool.submit(run,R/x['path']) for x in p['files']]):
   result=future.result();rows.append(result);print(json.dumps(dict(completed=len(rows),total=len(p['files']),**result)),flush=True)
 validate_external_dependency(R,PERMIT)
 receipt=P/'final-policy-evaluation-receipt-v4.json'
 with receipt.open('x') as f:json.dump(dict(status='completed',files=rows,policy_context_rows=sum(x['rows'] for x in rows),
  elapsed_seconds=time.monotonic()-start,permit_sha256=hashlib.sha256(PERMIT.read_bytes()).hexdigest(),
  exact_aliases={'LOAO-economics':'A3','matched-monolithic-optimizer':'A4'},training_or_selection=False),f,indent=2)
 receipt.chmod(0o444)
