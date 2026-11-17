"""Exercise actual frozen policies on TRAIN prefixes, without native rollouts."""
from pathlib import Path
from datetime import date
import json,numpy as np,torch
from pcse_gym.agromas.season import regional_weather
from pcse_gym.agromas_v8.online_features import history_from_provider
from pcse_gym.agromas_v8.joint_model import FrozenJointWorldModel
from pcse_gym.agromas_v8.controller import FiveSpecialistTeam
from pcse_gym.agromas_v8.policies import TreePolicy,SensorlessPPOPolicy,LegacyV6Policy,FixedDosePolicy
R=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 torch.set_num_threads(2);m=json.loads((R/'cache/phase8-train-arrays/meta.json').read_text())[0];v=np.load(R/'cache/phase8-train-arrays/x.npy')[0];state=dict(zip(['dvs','lai','sm','n_fert_cum','n_uptake','stage'],v[:6]));state.update(region_id=m['region'],as_of=m['as_of'],days_since_last_fert=float(v[25]),climate='Historical');history=history_from_provider(regional_weather(str(R),m['region'],'v2'),m['region'],date.fromisoformat(m['as_of']));case=dict(region=m['region'],year=m['year'],cap=40,price_multiplier=1,subsidy=0);records=[]
 for family in ('MLP','Weather','ExtraTrees','Linear'):
  team=FiveSpecialistTeam(R,FrozenJointWorldModel(R,'Sensorless',family,device='cuda'))
  policies=[(family,TreePolicy(team))]
  if family=='MLP':policies+=[(mode,TreePolicy(team,mode=mode)) for mode in ('soft','open-loop','greedy-frozen')]+[(remove,TreePolicy(team,remove=remove)) for remove in ('climate','eco','econ')]+[('Fixed',FixedDosePolicy(team))]+[(f'PPO{s}',SensorlessPPOPolicy(R,team,s)) for s in (4,17,29)]
  for name,policy in policies:
   decision=policy.choose(state,history,case);assert decision['dose'] in (0,10,20,40,60,80,100);records.append(dict(policy=name,dose=decision['dose'],tier=decision['tier']));print(records[-1],flush=True)
 # Additional final-source interfaces: guarded open-loop Stage2 and Full track.
 meta=json.loads((R/'cache/phase8-train-arrays/meta.json').read_text());xx=np.load(R/'cache/phase8-train-arrays/x.npy');team=FiveSpecialistTeam(R,FrozenJointWorldModel(R,'Sensorless','MLP',device='cuda'));policy=TreePolicy(team,mode='open-loop');first=policy.choose(state,history,case)
 index=next(i for i,q in enumerate(meta) if q['region']==m['region'] and q['year']==m['year'] and q['climate']=='Historical' and q['stage']==2 and q['plan'][0]==first['dose']);q=meta[index];v=xx[index];nextstate=dict(zip(['dvs','lai','sm','n_fert_cum','n_uptake','stage'],v[:6]));nextstate.update(region_id=q['region'],as_of=q['as_of'],days_since_last_fert=float(v[25]),climate='Historical');h=history_from_provider(regional_weather(str(R),q['region'],'v2'),q['region'],date.fromisoformat(q['as_of']));second=policy.choose(nextstate,h,case);assert second['tier'] in (1,2,3);records.append(dict(policy='guarded-open-loop-stage2',dose=second['dose'],tier=second['tier']))
 fullteam=FiveSpecialistTeam(R,FrozenJointWorldModel(R,'Full-Telemetry','MLP',device='cuda'));decision=TreePolicy(fullteam).choose(state,history,case);records.append(dict(policy='Full-Telemetry',dose=decision['dose'],tier=decision['tier']))
 calendar=FixedDosePolicy(fullteam,calendar=True);early=state|dict(as_of=f"{case['year']-1}-11-15");assert calendar.choose(early,history,case)['defer'];records.append(dict(policy='calendar-prior-autumn',deferred=True))
 for seed in (None,4,17,29):
  d=LegacyV6Policy(R,seed).choose(state,history,case);records.append(dict(policy=f'legacy{seed}',dose=d['dose'],tier=d['tier']));print(records[-1],flush=True)
 (R/'reports/phase8/phase8b-policy-interface-smoke.json').write_text(json.dumps(dict(scope='TRAIN interface only,zero native rollouts',records=records),indent=2))
