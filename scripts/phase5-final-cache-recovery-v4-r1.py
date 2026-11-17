"""Audited missing-only recovery after zero-season derived-cache write failure.

Native force_reload=True always writes its derived PKL. During parent template
initialization ONLY, redirect that one write to a new artifact; assert its bytes
match the sealed PKL. Never change a frozen input, parameter, policy or outcome.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from unittest.mock import patch
import argparse,builtins,importlib.util,sys,json,hashlib,logging,multiprocessing
import numpy as np
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5';PERMIT=P/'final-evaluation-permit-v4.json'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def immutable(path,value):
 with path.open('x') as f:json.dump(value,f,indent=2)
 path.chmod(0o444)

def preload(phase):
 from pcse_gym.agromas.season import _template
 original=R/'cache/phase5-regional-config/crop/YAMLCropDataProvider.pkl'
 expected=json.loads(PERMIT.read_text())['files'][str(original.relative_to(R))]
 assert sha(original)==expected
 out=R/f'cache/phase5-cache-recovery-v4-r1/native-{phase}.pkl';out.parent.mkdir(exist_ok=True)
 real_open=builtins.open;writes=[]
 def redirect(file,mode='r',*args,**kwargs):
  if isinstance(file,(str,Path)) and Path(file).resolve()==original.resolve() and mode=='wb':
   writes.append(str(file));return real_open(out,'xb',*args,**kwargs)
  return real_open(file,mode,*args,**kwargs)
 with patch('builtins.open',redirect):_template(str(R))
 assert len(writes)==1 and sha(out)==expected and sha(original)==expected,'Derivedcachebytesnotidentical'
 out.chmod(0o444)
 return dict(original_path=str(original.relative_to(R)),redirected_path=str(out.relative_to(R)),writes_redirected=1,
  sealed_sha256=expected,regenerated_sha256=sha(out),original_untouched=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--run-missing',action='store_true');args=parser.parse_args();assert args.prepare_only!=args.run_missing
 logging.disable(logging.CRITICAL)
 from pcse_gym.agromas.final_evaluation import validate_external_dependency
 from pcse_gym.agromas.regions import load_split_manifest,authorize_year
 from pcse_gym.agromas.season import regional_weather
 validate_external_dependency(R,PERMIT)
 spec=importlib.util.spec_from_file_location('phase5_frozen_final_books_v4',R/'scripts/phase5-generate-final-books.py');m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
 assert m.O.is_dir() and not list(m.O.iterdir()),'Thisrecoveryonlyacceptstheprovenzero-seasonfailedlaunch'
 source_sha=sha(Path(__file__));cache=preload('prepare' if args.prepare_only else 'launch')
 selection=json.loads((P/'regional-phenology-train-freeze-v2.json').read_text())['selected']
 if args.prepare_only:
  name='netherlands_lelystad';row=m.physical_plan(name,2000,'Historical','Train',selection[name],(40.,80.,100.),None)
  path=R/f'data/phase5-teachers-v2/{name}-2000-Historical.jsonl';expected=next(x for x in map(json.loads,path.read_text().splitlines()) if x['plan']==[40.,80.,100.])
  difference=float(np.max(np.abs(np.array(row['outcome'])-expected['outcome'])));assert difference==0 and row['events']==expected['events']
  validate_external_dependency(R,PERMIT)
  immutable(P/'final-cache-recovery-preparation-v4-r1.json',dict(status='passed',all_original235inputs_unchanged=True,cache=cache,Train_only=True,physical_outcome_max_difference=difference,
   soil_C_residual=row['stock_diagnostics']['soil_C_mass_balance_residual_kg_ha'],source_sha256=source_sha,original_failed_claim_sha256=sha(P/'final-evaluation-campaign-claim-v4.json'),
   original_failed_log_sha256=sha(P/'final-physical-book-campaign-v4.log'),final_physical_seasons_before_recovery=0,policy_changes=False,model_changes=False))
  print(json.dumps(dict(status='prepared_only',cache=cache,Train_outcome_max_difference=difference,final_seasons=0)),flush=True);raise SystemExit(0)
 proof=json.loads((P/'final-cache-recovery-preparation-v4-r1.json').read_text());assert proof['status']=='passed' and proof['source_sha256']==source_sha
 gate=P/'final-cache-recovery-review-v4-r1.md';assert gate.exists() and 'COMPLETION_STATUS: COMPLETE' in gate.read_text() and 'ERROR_CLASS: NONE' in gate.read_text()
 addendum=dict(status='missing_only_cache_side_effect_recovery',original_permit_sha256=sha(PERMIT),original_claim_sha256=sha(P/'final-evaluation-campaign-claim-v4.json'),
  source=str(Path(__file__).relative_to(R)),source_sha256=source_sha,preparation_sha256=sha(P/'final-cache-recovery-preparation-v4-r1.json'),review_sha256=sha(gate),
  native_cache_write=cache,original_inputs_or_results_overwritten=False,physical_or_policy_parameters_changed=False,completed_worlds_before_recovery=0)
 immutable(P/'final-evaluation-recovery-addendum-v4-r1.json',addendum)
 manifest=load_split_manifest(P/'global-date-split-manifest.json');jobs=[]
 for name in manifest['regions']:
  regional_weather(str(R),name,'v2')
  for role in ('Held-Out','Public-Reused-Benchmark'):
   for year in manifest['regions'][name]['roles'][role]:
    authorize_year(manifest,name,year,role,permit_path=PERMIT,project_root=R)
    for climate in ('Historical','idealized_mid','idealized_high'):jobs.append((name,year,climate,role,selection[name]))
 assert len(jobs)==177
 receipts=[]
 with (P/'final-physical-book-progress-v4-r1.jsonl').open('x') as log:
  with ProcessPoolExecutor(max_workers=48,mp_context=multiprocessing.get_context('fork')) as pool:
   for future in as_completed([pool.submit(m.run,job) for job in jobs]):
    result=future.result();receipts.append(result);log.write(json.dumps(result)+'\n');log.flush();print(json.dumps(dict(completed=len(receipts),total=177,failed=result['failed'])),flush=True)
 validate_external_dependency(R,PERMIT);assert sha(Path(__file__))==source_sha
 immutable(P/'final-physical-book-receipt-v4.json',dict(status='completed' if all(x['failed']==0 for x in receipts) else 'failures_retained',files=receipts,
  physical_simulation_invocations=sum(x['rows'] for x in receipts),distinct_requested_plan_world_keys=sum(x['rows'] for x in receipts),distinct_executed_event_sequences=sum(x['distinct_executed_event_sequences'] for x in receipts),
  total_integrated_physical_days=sum(x['total_integrated_physical_days'] for x in receipts),failures=sum(x['failed'] for x in receipts),independent_weather_seasons=52,public_reused_weather_seasons=7,
  climate_sensitivities=3,intervention_plans=343,permit_sha256=sha(PERMIT),recovery_addendum_sha256=sha(P/'final-evaluation-recovery-addendum-v4-r1.json'),training_or_selection_use=False))
