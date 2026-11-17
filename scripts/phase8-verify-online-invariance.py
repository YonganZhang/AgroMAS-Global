"""Thirty real frozen-controller action tests, without evaluation physics.

Target-future perturbations use a TRAIN prefix and exclude that entire harvest
season from the analog archive. Past data and all numerical models are fixed.
"""
from pathlib import Path
from datetime import date
import json,hashlib
import numpy as np,torch
from pcse_gym.agromas.season import regional_weather
from pcse_gym.agromas.regions import REGIONS
from pcse_gym.agromas_v8.joint_model import FrozenJointWorldModel
from pcse_gym.agromas_v8.controller import FiveSpecialistTeam
from pcse_gym.agromas_v8.online_features import history_from_provider
from pcse_gym.agromas.climate_agent import WeatherHistory
R=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 torch.set_num_threads(2);meta=json.loads((R/'cache/phase8-train-arrays/meta.json').read_text());x=np.load(R/'cache/phase8-train-arrays/x.npy');records=[]
 for track in ('Full-Telemetry','Sensorless'):
  model=FrozenJointWorldModel(R,track,'MLP',device='cuda');fixture=None
  for i,m in enumerate(meta):
   if m['climate']!='Historical' or m['stage']!=1:continue
   v=x[i];state=dict(zip(['dvs','lai','sm','n_fert_cum','n_uptake','stage'],v[:6]));state.update(region_id=m['region'],as_of=m['as_of'],days_since_last_fert=float(v[25]),climate='Historical')
   team=FiveSpecialistTeam(R,model,train_analog_years=tuple(y for y in range(1995,2010) if y!=m['year']));provider=regional_weather(str(R),m['region'],'v2');history=history_from_provider(provider,m['region'],date.fromisoformat(m['as_of']));baseline=team.choose(state,history)
   if baseline['applicable']:fixture=(m,state,team,provider,history,baseline);break
  assert fixture is not None,'Nontrivial in-domain fixture required'
  m,state,team,provider,history,baseline=fixture;day=date.fromisoformat(m['as_of']);saved={k:{d:v for d,v in values.items() if date.fromisoformat(d[:4]+'-'+d[4:6]+'-'+d[6:])>day and date.fromisoformat(d[:4]+'-'+d[4:6]+'-'+d[6:])<=REGIONS[m['region']].crop_dates(m['year'])[1]} for k,values in provider.parameters.items() if isinstance(values,dict)}
  try:
   for trial in range(15):
    for key,values in saved.items():
     for d,value in values.items():provider.parameters[key][d]=float(value)*(trial+2)+1000*(trial+1)
    team._response_cache.clear();team.climate._descriptor.cache_clear()
    decision=team.choose(state,history)
    assert decision['dose']==baseline['dose'] and decision['tier']==baseline['tier']
    assert np.array_equal(decision['branch_plan_indices'],baseline['branch_plan_indices'])
    records.append(dict(track=track,trial=trial,region=m['region'],year=m['year'],dose=decision['dose'],tier=decision['tier'],applicable=True,plans=team.last_response_plan_count,pass_invariance=True))
  finally:
   for key,values in saved.items():provider.parameters[key].update(values)
   team.climate._descriptor.cache_clear()
  before=set(team._response_cache);changed=WeatherHistory(history.dates,history.values+np.array([0,0,0,1,0,0]),history.region_id,history.source_id);team.choose(state,changed);assert len(set(team._response_cache)-before)==1,'Past changes must invalidate the response cache'
 assert len(records)==30
 (R/'reports/phase8/phase8b-online-action-invariance.json').write_text(json.dumps(dict(tests=records,passed=30,nontrivial_model=True,positive_control_past_change_invalidates_cache=True,physics_evaluation_runs=0),indent=2))
 print('PASS:30 actual online actions; both tracks; past-change cache positive control',flush=True)
