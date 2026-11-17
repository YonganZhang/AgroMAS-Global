"""Once-only adaptive-reuse benchmark from immutable Phase5 physical books."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from itertools import product
from datetime import datetime,timezone
import json,hashlib,pickle,time,argparse,numpy as np,joblib,torch
from sb3_contrib import MaskablePPO
from pcse_gym.agromas.features import shared_features
from pcse_gym.agromas_v6.books import DenseBooks,PLANS,FACTORS
from pcse_gym.agromas_v6.core import Policy,FAMILIES,select_objective,AgroMASGlobalCoordinator
from pcse_gym.agromas_v6.book_env import build_tables,state_table,encode
R=Path(__file__).resolve().parents[1];P=R/'reports/phase6';PERMIT=P/'final-evaluation-permit-v6.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate():
 from pcse_gym.agromas.final_evaluation import validate_external_dependency
 validate_external_dependency(R,R/'reports/phase5/final-evaluation-permit-v4.json')
 permit=json.loads(PERMIT.read_text());assert sha(PERMIT)==PERMIT.with_suffix('.sha256').read_text().strip()
 for name,digest in permit['files'].items():assert sha(R/name)==digest,name
 primary=Path(permit['primary_root'])
 for row in json.loads((P/'phase5-preservation-baseline-v6.json').read_text())['files']:assert sha(primary/row['path'])==row['sha256'],row['path']
 return permit
def load_book(path):
 rows={tuple(r['plan']):r for r in map(json.loads,path.read_text().splitlines())};assert len(rows)==343;first=rows[(0.,0.,0.)];f=np.zeros((1,3,343,22));available=np.zeros((1,3,343),bool);outcomes=[];context={}
 for i,plan in enumerate(PLANS):
  row=rows[tuple(plan)];assert row['status']=='completed';outcomes.append(row['outcome'])
  for s,state in row['states'].items():
   key=(state['region_id'],str(state['as_of']),first['climate'])
   if key not in context:context[key]=shared_features(str(R),state,first['climate'])[6:]
   observed=[state[k] for k in ('dvs','lai','sm','n_fert_cum','n_uptake','stage')];f[0,int(s)-1,i]=np.r_[observed,context[key]];available[0,int(s)-1,i]=True
 data=DenseBooks([(first['region_id'],first['harvest_year'],first['climate'])],f,available,np.array(outcomes)[None]);return rows,data,first
def run(entry):
 torch.set_num_threads(1);permit=json.loads(PERMIT.read_text());path=Path(permit['primary_root'])/entry['path'];assert sha(path)==entry['sha256'];rows,data,first=load_book(path);active=json.loads((P/'ACTIVE_TRAIN_RUN_V6.json').read_text());selected=json.loads((R/active['reports']/'policy-train-selection-v6.json').read_text())['selected'];models_root=R/active['models'];tables={}
 for family in FAMILIES:
  models={s:joblib.load(models_root/family/f'stage-{s}.joblib') for s in (1,2,3)};tables[family]=build_tables(data,models)
 ppos={}
 for seed in (4,17,29):
  folder=models_root/f'PPO-structured-seed{seed}';model=MaskablePPO.load(folder/'model.zip',device='cpu');model.policy.set_training_mode(False)
  with (folder/'vecnormalize.pkl').open('rb') as f:norm=pickle.load(f)
  norm.training=False;norm.norm_reward=False;ppos[seed]=(model,norm)
 contexts=list(product((25.,35.,50.),(1.,2.),(0.,50.,100.,150.,200.)))
 if first['climate']=='Historical':contexts.append((40.,1.,0.))
 reachable=np.ones(343,bool)
 for stage in (1,2,3):
  seen=data.available[0,stage-1];dose=PLANS[:,stage-1];committed=data.features[0,stage-1,:,3];reachable&=(seen&(committed+dose<=220+1e-8))|((~seen)&(dose==0))

 output=P/'final-policy-results-v6'/path.name;count=0;identity=0;clips=0;maxN=maxC=0.;unexecuted=0;pending=[];max_standardized=0.
 for physical in rows.values():
  stock=physical['stock_diagnostics'];n=abs(stock['soil_N_mass_balance_residual_kg_ha']);c=abs(stock['soil_C_mass_balance_residual_kg_ha']);assert n<1e-10 and c<1e-9;maxN=max(maxN,n);maxC=max(maxC,c)
 with output.open('x') as stream:
  for cap,price,subsidy in contexts:
   for family,seed in [(f,None) for f in FAMILIES]+[('Full',s) for s in ppos]:
    policy=Policy(selected['beta'],selected['penalty'],family);t,l=tables[family];ix=0;trace=[]
    for stage in (1,2,3):
     if not data.available[0,stage-1,ix]:continue
     stats,legal,base=state_table(data,t,l,0,ix,stage);action,diag=select_objective(stats[None],legal[None],cap,price,subsidy,policy);action=int(action[0]);clipped=[];standardized_max=None
     if seed is None:
      match,_=AgroMASGlobalCoordinator(policy).choose(stats[None],legal[None],cap,price,subsidy);assert int(match[0])==action;identity+=1
     else:
      obs,mask,diag=encode(base,stats,legal,cap,price,subsidy,policy);model,norm=ppos[seed];z=(obs-norm.obs_rms.mean)/np.sqrt(norm.obs_rms.var+norm.epsilon);clipped=np.flatnonzero(np.abs(z)>norm.clip_obs).tolist();clips+=len(clipped);standardized_max=float(np.max(np.abs(z)));max_standardized=max(max_standardized,standardized_max);chosen,_=model.predict(norm.normalize_obs(obs[None]),deterministic=True,action_masks=mask[None]);action=int(chosen[0]);assert mask[action]
     trace.append(dict(stage=stage,action_index=action,dose=float(PLANS[action*FACTORS[stage-1],stage-1]),tier=int(diag['tier'][0]),predicted_infeasible=bool(diag['predicted_infeasible'][0]),clipped_observation_indices=clipped,max_abs_standardized_observation=standardized_max,normalization_clip_nearly_disabled=1e6 if seed is not None else None));ix+=action*FACTORS[stage-1]
    physical=rows[tuple(PLANS[ix])];m=physical['outcome'];joint=bool(.5<=m[3]<=.9 and 0<=m[2]<=cap);executed=sum(e['dose'] for e in physical['events']);requested=sum(PLANS[ix]);basal=float(first.get('initial_base_n',0));assert np.isclose(executed,requested,rtol=0,atol=1e-8),'Requestedtopdressnotexecuted';assert np.isclose(m[4],basal+executed,rtol=0,atol=1e-6),'Nativefertilizermismatch'
    row=dict(region_id=first['region_id'],harvest_year=first['harvest_year'],climate=first['climate'],role='Adaptive-Reused Temporal Benchmark',source_role=first['role'],cohort='Former-Held-Out' if first['role']=='Held-Out' else 'Public-Reused',policy='Phase6-'+family if seed is None else 'PPO-v6-structured-book',seed=seed,cap=cap,price_multiplier=price,subsidy=subsidy,outcome=m,plan=PLANS[ix].tolist(),events=physical['events'],stock_diagnostics=physical['stock_diagnostics'],joint=joint,partial_profit=float(200*m[0]-1.5*price*m[4]+subsidy*joint),trace=trace,physical_source_id=f"{first['region_id']}:{first['harvest_year']}:{first['climate']}:{ix}",native_daily_rollouts=0)
    pending.append(row);count+=1
  # Separate ex-post oracle diagnostic, after every policy decision is fixed.
  outcome=data.outcomes[0];feasible={cap:bool(np.any(reachable&(outcome[:,3]>=.5)&(outcome[:,3]<=.9)&(outcome[:,2]>=0)&(outcome[:,2]<=cap))) for cap in (25.,35.,40.,50.)}
  for row in pending:
   row['physically_feasible_in_grid']=feasible[row['cap']];stream.write(json.dumps(row)+'\n')
 output.chmod(0o444);return dict(path=str(output.relative_to(R)),sha256=sha(output),rows=count,matched_identity_decisions=identity,clipped_feature_occurrences=clips,all_book_max_N_residual=maxN,all_book_max_C_residual=maxC,requested_vs_event_sum_mismatch_rows=unexecuted,max_abs_standardized_PPO_observation=max_standardized,observation_clip_threshold_nearly_disabled=1e6)
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--workers',type=int,default=8);args=parser.parse_args();permit=validate();claim=P/'final-evaluation-campaign-claim-v6.json'
 with claim.open('x') as f:json.dump(dict(status='claimed_once',permit_sha256=sha(PERMIT),started_UTC=datetime.now(timezone.utc).isoformat(),scope='Adaptive-Reused Temporal Benchmark',no_fitting=True),f,indent=2)
 (P/'final-policy-results-v6').mkdir(exist_ok=False);entries=permit['final_physical_books'];assert len(entries)==177;results=[];start=time.monotonic()
 with ProcessPoolExecutor(max_workers=args.workers) as pool:
  for future in as_completed([pool.submit(run,e) for e in entries]):
   try:result=future.result()
   except Exception as error:
    (P/'final-scoring-failure-v6.json').write_text(json.dumps(dict(status='failed;retainalloutputs;noretuning',error=repr(error),missing_only_recovery_requires_explicit_audited_receipt=True),indent=2));raise
   results.append(result);print(json.dumps(dict(completed=len(results),total=177,**results[-1])),flush=True)
 validate()
 with (P/'final-policy-evaluation-receipt-v6.json').open('x') as f:json.dump(dict(status='completed',scope='Adaptive-Reused Temporal Benchmark',files=results,policy_context_rows=sum(r['rows'] for r in results),elapsed_seconds=time.monotonic()-start,permit_sha256=sha(PERMIT),new_native_daily_rollouts=0,phase5_controls='Read-only recorded v4 outputs; no comparator refitting'),f,indent=2)
