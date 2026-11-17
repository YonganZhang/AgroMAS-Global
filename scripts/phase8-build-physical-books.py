"""Once-only TRAIN diagnostic replay and sealed Dev generation; no evaluation labels.

The only configuration extension adds native variables to DAILY OUTPUT in a
worktree-local cached configuration. It changes neither PCSE equations nor inputs.
Dev output is sealed for one-shot G1 calibration after TRAIN-only model freeze.
"""
from pathlib import Path
from itertools import product
from concurrent.futures import ProcessPoolExecutor, as_completed
import argparse, gzip, hashlib, json, logging, multiprocessing, time
import numpy as np
from pcse_gym.agromas.season import build_season, observe, terminal, regional_weather, _template
from pcse_gym.agromas.scheduler import ThreeStageScheduler
from pcse_gym.agromas.weekly import advance_week
from pcse_gym.agromas.final_evaluation import final_stock_diagnostics
from pcse_gym.agromas.features import shared_features, forecast_model
from pcse_gym.agromas.regions import REGIONS
R=Path(__file__).resolve().parents[1]; P=R/'reports/phase8'; O=R/'data/phase8-physical-books'
GRID=(0,10,20,40,60,80,100)
DAILY=('CORGT','NORGT','NO3T','NH4T','NLOSSCUM','RCORGAMTT','RCORGDISTT','RNH4AMTT','RNO3AMTT','RNH4UPTT','RNO3UPTT','RNH4DEPOSTT','RNO3DEPOSTT','RNH4INTT','RNO3INTT','RNH4OUTTT','RNO3OUTTT','RNO3DENITRTT','RNH4MINTT')

def simulate(name,year,climate,role,selection,plan):
 e,meta=build_season(str(R),name,year,role=role,climate=climate,version='v2',**selection)
 sched=ThreeStageScheduler(220.,initial_base_n=meta['initial_base_n']); requested=None; states={}; features={}; steps=0
 def guard(dose,dvs,day):
  if dvs is None:return 0.
  sched.eligible(day,float(dvs))
  return sched.execute(day,float(dvs),dose,expected_stage=requested) if requested is not None else 0.
 e._action_guard=guard
 while not e.terminated and steps<60:
  state=observe(e,sched,name); requested=state.stage or None
  if requested:
   states[str(requested)]=state.__dict__; features[str(requested)]=shared_features(str(R),state.__dict__,climate).tolist()
   dose=min(float(plan[requested-1]),220-sched.cumulative)
  else:dose=0.
  advance_week(e,dose);steps+=1
 if not e.terminated:raise ValueError('Season horizon exceeded')
 outcome=terminal(e,sched); diag=final_stock_diagnostics(e,meta,outcome)
 # Current campaign at-launch source is archived. These additional inline
 # guards are also checked independently for every saved row by endpoint audit.
 if not np.isfinite(outcome).all():raise ValueError('Non-finite physical outcome')
 if abs(diag['native_fertilizer_N_kg_ha']-outcome[4])>1e-6:raise ValueError('Native fertilizer and scheduler disagree')
 daily=[]
 for row in e.get_output():
  daily.append([str(row['day'])]+[None if row.get(k) is None else float(np.asarray(row[k]).sum()) for k in DAILY])
 return dict(status='completed',**meta,plan=list(plan),outcome=outcome.tolist(),states=states,features=features,events=sched.events,stock_diagnostics=diag,daily_columns=['day']+list(DAILY),daily_native=daily,native_weekly_steps=steps)

def run(job):
 name,year,climate,role,selection,source=job
 path=O/f'{name}-{year}-{climate}-{role}.jsonl.gz'; errors=[]; maxdiff=0.; maxn=0.;maxc=0.; skips=0
 originals=None
 if source:
  originals={tuple(x['plan']):x for x in map(json.loads,(R/source).read_text().splitlines())}
 with path.open('xb') as raw:
  with gzip.open(raw,'wt') as out:
   for plan in product(GRID,repeat=3):
    try:
     row=simulate(name,year,climate,role,selection,plan)
     if originals is not None:
      diff=float(np.max(np.abs(np.array(row['outcome'])-originals[plan]['outcome'])));maxdiff=max(maxdiff,diff)
      if diff>1e-10:raise ValueError('TRAIN native replay differs from immutable outcome: '+str(diff))
     d=row['stock_diagnostics'];maxn=max(maxn,abs(d['soil_N_mass_balance_residual_kg_ha']));maxc=max(maxc,abs(d['soil_C_mass_balance_residual_kg_ha']))
     if sum(plan)+row['initial_base_n']<=220 and row['outcome'][4]<sum(plan)+row['initial_base_n']-1e-8:skips+=1
    except Exception as exc:
     row=dict(status='failed',region_id=name,harvest_year=year,climate=climate,role=role,plan=plan,error=repr(exc));errors.append(row)
    out.write(json.dumps(row,default=str)+'\n')
 path.chmod(0o444)
 return dict(path=str(path.relative_to(R)),region_id=name,year=year,climate=climate,role=role,rows=343,failed=len(errors),errors=errors,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),source=source,max_immutable_outcome_difference=maxdiff,max_abs_N_residual_kg_ha=maxn,max_abs_C_residual_kg_ha=maxc,budget_legal_skipped_plans=skips)

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--workers',type=int,default=32);args=ap.parse_args();logging.disable(logging.CRITICAL)
 # Claim before any physical call. Do not silently overwrite/resume a campaign.
 claim=P/'phase8b-physical-campaign-claim.json'
 with claim.open('x') as f:json.dump(dict(started=time.time(),scope='TRAIN diagnostic replay + Dev generation ONLY',train_years=[1995,2009],dev_years=[2010,2014],evaluation_years_unlocked=False),f,indent=2)
 O.mkdir(exist_ok=False)
 # The copied cached model configuration is private to this worktree.
 _template(str(R));conf=R/'cache/phase5-regional-config/Wofost81_NWLP_MLWB_SNOMIN.conf'
 with conf.open('a') as f:f.write('\n# Phase8 output-only extension; native equations unchanged.\nOUTPUT_VARS = list(dict.fromkeys(OUTPUT_VARS + '+repr(list(DAILY))+'))\n')
 _template.cache_clear()
 selected=json.loads((R/'reports/phase5/regional-phenology-train-freeze-v2.json').read_text())['selected'];jobs=[]
 registry=json.loads((R/'reports/phase5/teacher-book-receipt-v2.json').read_text())
 for ent in registry['files']:
  source=R/ent['path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==ent['sha256']
  with source.open() as f:first=json.loads(next(f))
  assert first['role']=='Train' and 1995<=first['harvest_year']<=2009
  jobs.append((first['region_id'],first['harvest_year'],first['climate'],'Train',selected[first['region_id']],ent['path']))
 for name in REGIONS:
  regional_weather(str(R),name,'v2');forecast_model(str(R),name)
  for year in range(2010,2015):jobs.append((name,year,'Historical','Dev',selected[name],None))
 assert len(jobs)==250
 receipts=[]
 with (P/'phase8b-physical-progress.jsonl').open('x') as progress:
  with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('fork')) as pool:
   for future in as_completed([pool.submit(run,j) for j in jobs]):
    rec=future.result();receipts.append(rec);progress.write(json.dumps(rec)+'\n');progress.flush()
    print(json.dumps(dict(completed=len(receipts),total=len(jobs),failed=rec['failed'],path=rec['path'])),flush=True)
 result=dict(status='completed' if all(x['failed']==0 for x in receipts) else 'failed_rows_retained',files=receipts,physics_calls=343*len(jobs),heldout_access=False,dev_labels_not_used_for_selection=True)
 with (P/'phase8b-physical-receipt.json').open('x') as f:json.dump(result,f,indent=2)
