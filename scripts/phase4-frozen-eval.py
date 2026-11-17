"""Unified frozen-policy evaluation; per-episode immutable receipts permit missing-task recovery."""
import pathlib,sys,json,argparse,hashlib,time,concurrent.futures
import numpy as np
import torch
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
envs=SourceFileLoader('phase4_envs',str(R/'scripts/phase4-env.py')).load_module();metrics=SourceFileLoader('phase4_metric_extract',str(R/'scripts/evaluate-baselines.py')).load_module()
from pcse_gym.agent.ppo_mod import LagrangianPPO
from pcse_gym.agent.counterfactual import CounterfactualGRU
from pcse_gym.envs.moisture4 import UtilityScorer
from pcse_gym.envs.moisture import water_cap
from pcse_gym.envs.corridor import target
from pcse_gym.utils.frozen_audit import validate_manifest,exclusive_json,sha,claim_audit
CAL=R/'reports/phase3c-frozen-utility-v1.json'
controllers=SourceFileLoader('frozen_cuo_controller',str(R/'scripts/phase4-controller.py')).load_module()
episode_records=SourceFileLoader('frozen_episode_records',str(R/'scripts/phase4-records.py')).load_module()
EVALUATOR_START_SHA=sha(pathlib.Path(__file__))
ENV_START_SHA=sha(R/'scripts/phase4-env.py')
def model_asset(name,seed):
 if name=='cf-gru':return R/f'reports/phase4-cf-runs/cf-gru-seed{seed}/policy.pt'
 if name=='full4':return R/f'reports/phase3c-runs/v4-sm-final-full4-seed{seed}/model.zip'
 if name=='corrected':return R/f'reports/phase4-ppo-runs/phase4-singledual-corrected-seed{seed}/model.zip'
 if name in ['raw','masked','guided']:return R/f'reports/phase4-ppo-runs/phase4-{name}-seed{seed}/model.zip'
 return CAL if name=='utilityprior' else None

def evaluate(task):
 name,seed,soil,years,audit=task;envs.check_years(years,audit);torch.set_num_threads(1)
 import logging;logging.disable(logging.CRITICAL)
 ck=model_asset(name,seed);digest=sha(ck) if ck else None;scorer=UtilityScorer(json.loads(CAL.read_text()));model=None;alpha=0
 if ck and name not in ['utilityprior']:
  receipt=json.loads((ck.parent/'receipt.json').read_text());assert receipt['status']=='completed' and digest==receipt['checkpoint_sha256']
  for rel,h in receipt['source_sha256'].items():assert sha(R/rel)==h,'Frozen model source drift: '+rel
  if name=='cf-gru':model=CounterfactualGRU.load(ck,device='cpu');model.eval();alpha=receipt['selection']['alpha']
  else:model=LagrangianPPO.load(ck,device='cpu')
 if audit:
  manifest=validate_manifest(R,False)
  if ck:assert manifest['files'][str(ck.relative_to(R))]==digest
 controller=controllers.FrozenCUOController(scorer,model if name=='cf-gru' else None,alpha) if name in ['utilityprior','cf-gru'] else None
 e=envs.make_env(name,seed,soil,years[0],audit);e.unwrapped.sb3_env._phase2_fast_info=True;rows=[];events=[];infer_total=0.;infer_steps=0
 try:
  for year in years:
   saved=R/f'reports/phase4-heldout-episodes/{name}/{seed}/{soil}/{year}.json'
   if audit and saved.exists():
    prior=episode_records.read_episode(saved);assert prior['checkpoint_sha256']==digest and prior['manifest_sha256']==sha(R/'reports/heldout-unlock-manifest.json');assert prior['evaluator_sha256']==EVALUATOR_START_SHA and prior['environment_sha256']==ENV_START_SHA and prior['calibration_sha256']==sha(CAL) and prior['task_claim_sha256']==sha(R/'reports/heldout-audit-claim.json');assert (prior['episode']['year'],prior['episode']['soil'],prior['episode']['seed'])==(year,soil,seed);rows.append(prior['episode']);events+=prior['events'];continue
   e.unwrapped.overwrite_year(year);obs,_=e.reset(seed=seed);done=False;actual=0;merged={};steps=intercepts=0;season_events=[];adapt=None;actual_application_dates=[]
   while not done:
    before=obs.copy();decision_date=str(e.unwrapped.date);start=time.perf_counter()
    if name in ['raw','corrected','masked','guided','full4']:a=int(model.predict(obs,deterministic=True)[0])
    elif name in ['utilityprior','cf-gru']:
     a=controller.act(obs)
    elif name in ['prior160','prior170','prior190','old_SM-adaptiveprior']:
     f=obs[-1];legacy=name!='old_SM-adaptiveprior';final=int(name[-3:]) if legacy else 190
     if not legacy and adapt is None and f[0]>=.62:adapt=water_cap(f[:11],dict(json.loads((R/'reports/phase3b3-frozen-calibration-sm-v1.json').read_text()),headroom=0))
     if not legacy and adapt is not None:final=adapt
     stages=(50,110) if legacy else (70,130);wanted=float(target(f[0],actual,final,stages));a=int(np.clip(np.ceil((wanted-actual-1e-4)/10),0,8));offset=10 if legacy else 11;a=max(i for i in range(a+1) if obs[-1,offset+i])
    else:
     from pcse_gym.utils.nitrogen_helpers import get_standard_practices
     from datetime import timedelta
     dates,doses=get_standard_practices('N2-PA',year);date=e.unwrapped.date;a=sum(n//10 for d,n in zip(dates,doses) if d<date<=d+timedelta(days=7))
    infer_total+=time.perf_counter()-start;infer_steps+=1
    obs,r,t,tr,info=e.step(a);done=t or tr;actual+=10*info['executed_action'];steps+=1;intercepts+=int(info['shield_triggered'])
    for k,v in info.items():
     if isinstance(v,dict):merged.setdefault(k,{}).update(v)
    if info['executed_action']>0:actual_application_dates.append(info['application_date'])
    if a>0:season_events.append(dict(application_date=info['application_date'],decision_date=decision_date,year=year,soil=soil,seed=seed,DVS=float(before[-1,0]),LAI=float(before[-1,1])*10,SM=float(before[-1,10]) if before.shape[-1] in [11,20] else None,past_rain=float(before[-1,4]),history=before.tolist() if audit else None,cumulative_N=float(before[-1,5])*400,proposed=int(a),executed=info['executed_action'],reasons=info['shield_reason']))
   row=metrics.extract(merged,year,name);row.update(native_NUE=row['NUE'],native_surplus_kg_ha=row['N_surplus_kg_ha'],native_joint_satisfied=row['joint_satisfied']);native_input=row['grain_N_kg_ha']/row['NUE'] if row['NUE']>0 else 0;nue=row['grain_N_kg_ha']/(native_input-row['fertilization_kg_ha']+actual) if native_input else 0;surplus=row['N_surplus_kg_ha']-row['fertilization_kg_ha']+actual
   row.update(seed=seed,soil=soil,actual_N=actual,NUE_actual=nue,surplus_actual=surplus,joint_actual=.5<=nue<=.9 and 0<=surplus<=40,NUE=nue,N_surplus_kg_ha=surplus,joint_satisfied=.5<=nue<=.9 and 0<=surplus<=40,NUE_satisfied=.5<=nue<=.9,surplus_satisfied=0<=surplus<=40,proposed_violation_rate=info['proposed_violation_rate'],executed_violation_rate=info['executed_violation_rate'],guard_interception_rate=intercepts/steps)
   from datetime import date
   dates=[date.fromisoformat(d) for d in actual_application_dates];gaps=[(b-a).days for a,b in zip(dates,dates[1:])]
   row.update(actual_application_dates=actual_application_dates,minimum_actual_spacing_days=min(gaps) if gaps else None,actual_spacing_violations=sum(gap<14 for gap in gaps))
   if name not in ['raw','corrected','N2-PA']:assert row['actual_spacing_violations']==0,'Actual-date spacing failed'
   rows.append(row);events+=season_events
   if audit:episode_records.write_episode(saved,dict(evaluator_sha256=EVALUATOR_START_SHA,environment_sha256=ENV_START_SHA,calibration_sha256=sha(CAL),task_claim_sha256=sha(R/'reports/heldout-audit-claim.json'),checkpoint_sha256=digest,manifest_sha256=sha(R/'reports/heldout-unlock-manifest.json'),episode=row,events=season_events))
  if ck:assert sha(ck)==digest
  return dict(model=name,seed=seed,soil=soil,checkpoint_sha256=digest,episodes=rows,events=events,inference_seconds=infer_total,inference_steps=infer_steps,alpha=alpha if name=='cf-gru' else None)
 finally:e.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--models',nargs='+',required=True);p.add_argument('--output',required=True);p.add_argument('--workers',type=int,default=45);p.add_argument('--audit',action='store_true');p.add_argument('--resume',action='store_true');a=p.parse_args();out=R/a.output;assert not out.exists();years=list(range(1983,2022))+list(range(5500,5999)) if a.audit else list(range(5000,5500))
 tasks=[(name,seed,soil,years[i:i+50],a.audit) for name in a.models for seed in ([4,17,29] if name in ['raw','corrected','masked','guided','full4','cf-gru'] else [4]) for soil in ['default','fast','slow'] for i in range(0,len(years),50)]
 if a.audit:
  protocol=SourceFileLoader('phase4_main_protocol',str(R/'scripts/phase4-protocol.py')).load_module();protocol.validate_domain_manifest(R,True)
  if set(a.models)!=set(protocol.validate_domain_manifest(R,False)['evaluation_methods']) or len(a.models)!=len(set(a.models)):raise ValueError('One-shot evaluation must include every frozen method exactly once')
  if a.resume:
   validate_manifest(R,True);claim=json.loads((R/'reports/heldout-audit-claim.json').read_text());assert claim['manifest_sha256']==sha(R/'reports/heldout-unlock-manifest.json');assert claim['tasks']==[list(task) for task in tasks]

  else:claim_audit(R,tasks)
 start=time.monotonic();records=[]
 # No evaluation episode starts until every requested neural checkpoint exists and is completed.
 for name in a.models:
  for seed in ([4,17,29] if name in ['raw','corrected','masked','guided','full4','cf-gru'] else [4]):
   ck=model_asset(name,seed)
   if ck and name!='utilityprior':
    deadline=time.monotonic()+7200
    while not (ck.parent/'receipt.json').exists():
     if time.monotonic()>deadline:raise TimeoutError('Checkpoint wait')
     time.sleep(10)
    assert json.loads((ck.parent/'receipt.json').read_text())['status']=='completed'

 with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:
  for rec in pool.map(evaluate,tasks):records.append(rec);out.with_suffix('.progress.json').write_text(json.dumps(dict(records=records,seconds=time.monotonic()-start)));print(json.dumps({k:v for k,v in rec.items() if k not in ['episodes','events']}),flush=True)
 if a.audit:validate_manifest(R,True)
 assert sha(pathlib.Path(__file__))==EVALUATOR_START_SHA and sha(R/'scripts/phase4-env.py')==ENV_START_SHA
 out.write_text(json.dumps(dict(status='completed',split='heldout' if a.audit else 'dev',records=records,seconds=time.monotonic()-start,evaluator_sha256=EVALUATOR_START_SHA,environment_sha256=ENV_START_SHA,calibration_sha256=sha(CAL))))
