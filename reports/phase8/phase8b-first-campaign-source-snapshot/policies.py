"""Episode-local policy adapters; native engines never enter these objects."""
from pathlib import Path
import numpy as np
from .planning import GRID
from .online_features import public_state,candidate_features
from .book_policy import stats_from_members,encode,mask_from_stats

class TreePolicy:
 def __init__(self,team,*,mode='tree',remove=None,monolithic=False,adapter_context=None):
  self.team=team;self.mode=mode;self.remove=remove;self.monolithic=monolithic;self.adapter_context=adapter_context;self.frozen=None
 def choose(self,state,history,case):
  if self.mode=='open-loop' and self.frozen is not None:
   from .planning import distribution_metrics,Regime,choose_tier
   stage=int(state['stage']);proposal=self.frozen.copy();proposal[:stage-1]=0.;plans=np.unique(np.stack([proposal,np.zeros(3)]),axis=0)
   prefix=public_state(state,self.team.model.track);x=candidate_features(self.team.root,prefix,plans,history=history);_,applicable=self.team.model.applicability(x)
   if not applicable:return dict(dose=0.,tier=3,reason='OOD_operational_zero_not_compliance',active_eco=True,active_econ=True)
   desc,w,_,_,_=self.team.climate.tree(prefix['region_id'],prefix['as_of'],observed_history=history);tensor=self.team.model.response_tensor(x,desc,adapter_context=self.adapter_context);radius=self.team.model.calibration_radius(x,self.adapter_context);regime=Regime(cap=case.get('cap',40),price_multiplier=case.get('price_multiplier',1),subsidy=case.get('subsidy',0),tax=case.get('tax',0),eco=self.remove!='eco',econ=self.remove!='econ',radius=radius)
   metrics=[]
   for plan,response in zip(plans,tensor):
    metric=distribution_metrics(response,w,regime);metric['score']=float(np.array_equal(plan,proposal));metrics.append(metric)
   # The initial nominal plan never re-optimizes. The common causal safety
   # fallback may suppress its dose; this cannot claim fresh Tier1 compliance.
   j,tier=choose_tier(metrics,[int(np.any(p)) for p in plans],regime,modular=not self.monolithic)
   return dict(dose=float(plans[j,stage-1]),tier=tier,reason='initial_open_loop_proposal_with_shared_causal_guard',active_eco=self.remove!='eco',active_econ=self.remove!='econ',applicable=applicable,OOD_score=float(self.team.model.applicability(x)[0]),radius=radius,request_hash=__import__('hashlib').sha256(__import__('json').dumps(dict(prefix=prefix,history=history.values.tolist(),plans=plans.tolist(),cap=regime.cap,price=regime.price_multiplier,subsidy=regime.subsidy,tax=regime.tax,remove=self.remove,monolithic=self.monolithic,adapter=self.adapter_context),sort_keys=True,default=str).encode()).hexdigest(),**self.team.model.prior_status(x,self.adapter_context))
  decision=self.team.choose(state,history,cap=case.get('cap',40),price_multiplier=case.get('price_multiplier',1),subsidy=case.get('subsidy',0),tax=case.get('tax',0),mode=self.mode,remove=self.remove,monolithic=self.monolithic,adapter_context=self.adapter_context)
  if self.mode=='open-loop':
   ids=decision['branch_plan_indices'];assert np.all(ids==ids[0]);self.frozen=decision['plans'][ids[0]].copy();self.frozen_tier=decision['tier']
  return {k:decision.get(k) for k in ('dose','tier','reason','applicable','OOD_score','request_hash','radius','prior_accepted','prior_timing_admissible','prior_ood','prior_kind')}|dict(active_eco=self.remove!='eco',active_econ=self.remove!='econ')

class SensorlessPPOPolicy:
 def __init__(self,root,team,seed):
  import torch
  from sb3_contrib import MaskablePPO
  from stable_baselines3.common.vec_env import VecNormalize
  torch.set_num_threads(1);self.team=team
  folder=Path(root)/f'models/phase8-controls/PPO-Sensorless-seed{seed}'
  self.model=MaskablePPO.load(folder/'model.zip',device='cpu');self.model.policy.set_training_mode(False)
  import pickle
  with (folder/'vecnormalize.pkl').open('rb') as stream:self.normalizer=pickle.load(stream)
  self.normalizer.training=False;self.normalizer.norm_reward=False
 def choose(self,state,history,case):
  prefix=public_state(state,'Sensorless');stage=int(prefix['stage']);plans=[];legal=state['n_fert_cum']+GRID<=220+1e-8;indices=[]
  for a,dose in enumerate(GRID):
   if not legal[a]:continue
   p=np.zeros(3);p[stage-1]=dose;remaining=220-state['n_fert_cum']-dose
   for s in range(stage,3):p[s]=max(v for v in GRID if v<=min(80,remaining)+1e-8);remaining-=p[s]
   indices.append(a);plans.append(p)
  desc,w,_,_,_=self.team.climate.tree(prefix['region_id'],prefix['as_of'],observed_history=history)
  x=candidate_features(self.team.root,prefix,np.asarray(plans),'Historical',history);_,allowed=self.team.model.applicability(x)
  response=self.team.model.response_tensor(x,desc);branch=np.minimum(np.searchsorted(np.cumsum(w),(np.arange(32)+.5)/32),len(w)-1)
  stats=np.zeros((7,12));stats[indices]=stats_from_members(response[:,branch,np.arange(32)],self.team.model.radius)
  obs,mask,tier=encode(x[0,:22],stats,legal,case.get('cap',40),case.get('price_multiplier',1),case.get('subsidy',0),allowed)
  action,_=self.model.predict(self.normalizer.normalize_obs(obs[None]),deterministic=True,action_masks=mask[None]);a=int(np.asarray(action).item());assert mask[a]
  return dict(dose=float(GRID[a]),tier=tier,reason='fixed_budget_sensorless_PPO_final_checkpoint',applicable=allowed)

class FixedDosePolicy:
 """DVS matched transfer. Optional calendar deferral is explicitly labelled."""
 def __init__(self,team,doses=(60,80,80),calendar=False):self.team=team;self.doses=doses;self.calendar=calendar
 def choose(self,state,history,case):
  from datetime import date
  stage=int(state['stage']);day=date.fromisoformat(state['as_of'])
  month,day_of_month=[(2,17),(5,11),(6,21)][stage-1]
  if self.calendar and day<date(case['year'],month,day_of_month):return dict(dose=0.,tier=None,defer=True,reason='native_calendar_date_pending')
  # Same forecast, information track and Tier constraints as modern controls;
  # fixed doses choose the nearest allowed current action rather than optimize.
  from .planning import legal_schedules
  plans=legal_schedules(stage,float(state['n_fert_cum']))
  # Fixed schedule is a proposal, not permission to violate common safety.
  from .planning import distribution_metrics,Regime,choose_tier
  prefix=public_state(state,self.team.model.track);desc,w,_,_,_=self.team.climate.tree(prefix['region_id'],prefix['as_of'],observed_history=history)
  x=candidate_features(self.team.root,prefix,plans,'Historical',history);ood_score,applicable=self.team.model.applicability(x);response=self.team.model.response_tensor(x,desc);r=Regime(cap=case.get('cap',40),radius=self.team.model.radius)
  candidates=[];metrics=[];doses=[]
  from .planning import frozen_continuation_indices
  selected,proposals=frozen_continuation_indices(plans,stage)
  for j,dose in zip(selected,proposals):
   candidates.append(j);doses.append(dose);m=distribution_metrics(response[j],w,r);m['score']=-abs(dose-self.doses[stage-1]);metrics.append(m)
  if not applicable:return dict(dose=0.,tier=3,reason='OOD_operational_zero_not_compliance')
  j,tier=choose_tier(metrics,doses,r);return dict(dose=float(doses[j]),tier=tier,reason='calendar_matched_transfer' if self.calendar else 'DVS_N2_matched_transfer')

class LegacyV6Policy:
 """Frozen Full/PPO v6 transferred to the common v8 tail-safety guard.

The original model, normalization and stage3 nominal-N assumption are preserved.
This matched-guard transfer is not a reproduction of original v6 q75 results.
 """
 def __init__(self,root,seed=None):
  import joblib,pickle
  self.root=Path(root);self.seed=seed;self.models={s:joblib.load(self.root/f'models/phase6/r2/Full/stage-{s}.joblib') for s in (1,2,3)}
  if seed is not None:
   from sb3_contrib import MaskablePPO
   folder=self.root/f'models/phase6/r2/PPO-structured-seed{seed}'
   self.actor=MaskablePPO.load(folder/'model.zip',device='cpu');self.actor.policy.set_training_mode(False)
   with (folder/'vecnormalize.pkl').open('rb') as stream:self.normalizer=pickle.load(stream)
   self.normalizer.training=False;self.normalizer.norm_reward=False
 def choose(self,state,history,case):
  from .online_features import feature_base
  from pcse_gym.agromas.regions import REGIONS
  from pcse_gym.agromas_v6.core import statistics,Policy
  from pcse_gym.agromas_v6.book_env import encode as encode_v6
  base=feature_base(self.root,public_state(state,'Full-Telemetry'),history=history);base[10+list(REGIONS).index(state['region_id'])]=1.
  legal=base[3]+GRID<=220+1e-8;xx=np.c_[np.repeat(base[None],7,axis=0),GRID];members=self.models[int(state['stage'])](xx);stats=stats_from_members(members,0.);mask,tier=mask_from_stats(stats,legal,case.get('cap',40),True);cap=case.get('cap',40);price=case.get('price_multiplier',1);sub=case.get('subsidy',0)
  if self.seed is not None:
   obs,_,_=encode_v6(base,statistics(members),legal,cap,price,sub,Policy());obs[-7:]=mask
   action,_=self.actor.predict(self.normalizer.normalize_obs(obs[None]),deterministic=True,action_masks=mask[None]);a=int(np.asarray(action).item())
  else:
   m=members.mean(1);joint=((members[:,:,2]>=0)&(members[:,:,2]<=cap)&(members[:,:,3]>=.5)&(members[:,:,3]<=.9)).mean(1);distance=np.maximum(.5-m[:,3],0)+np.maximum(m[:,3]-.9,0)+np.maximum(m[:,2]-cap,0)/cap
   score=200*m[:,0]-1.5*price*m[:,4]+sub*joint+200*joint-200*distance;a=int(np.argmax(np.where(mask,score,-np.inf)))
  assert mask[a];return dict(dose=float(GRID[a]),tier=tier,reason='frozen_v6_common_v8_guard_transfer')
