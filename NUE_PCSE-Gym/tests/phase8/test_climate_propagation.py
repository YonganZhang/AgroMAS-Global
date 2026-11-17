"""Exercise policy entry points with adversarial nonhistorical episode context."""
from types import SimpleNamespace
import numpy as np
import pytest
from pcse_gym.agromas_v8 import policies,controller
from pcse_gym.agromas_v8.online_features import public_state

@pytest.mark.parametrize('climate',['idealized_mid','idealized_high'])
@pytest.mark.parametrize('kind',['open-loop','ppo','fixed'])
def test_policy_features_and_tree_receive_active_episode_climate(monkeypatch,climate,kind):
 calls=[]
 def features(root,prefix,plans,climate='Historical',history=None):
  calls.append(('features',climate));assert prefix['climate']==climate
  return np.zeros((len(plans),36))
 def tree(region,asof,climate='Historical',**kw):
  calls.append(('tree',climate));return np.zeros((1,9)),np.ones(1),np.zeros(1),np.zeros(1),{}
 class Model:
  track='Sensorless';radius=0.
  def applicability(self,x):return 0.,True
  def calibration_radius(self,*a):return 0.
  def prior_status(self,*a):return {}
  def response_tensor(self,x,desc,**kw):
   m=np.zeros((len(x),1,32,6));m[...,0]=5.;m[...,2]=20.;m[...,3]=.7;m[...,4]=100.;return m
 team=SimpleNamespace(root='unused',model=Model(),climate=SimpleNamespace(tree=tree))
 monkeypatch.setattr(policies,'candidate_features',features)
 if kind=='open-loop':p=policies.TreePolicy(team,mode='open-loop');p.frozen=np.array([60.,80.,80.])
 elif kind=='fixed':p=policies.FixedDosePolicy(team)
 else:
  p=policies.SensorlessPPOPolicy.__new__(policies.SensorlessPPOPolicy);p.team=team
  p.normalizer=SimpleNamespace(normalize_obs=lambda x:x)
  p.model=SimpleNamespace(predict=lambda obs,deterministic,action_masks:(np.array([int(np.flatnonzero(action_masks[0])[0])]),None))
 state=dict(stage=2,n_fert_cum=60.,region_id='fixture',as_of='2001-04-01',climate='Historical')
 p.choose(state,SimpleNamespace(values=np.zeros((14,6))),{'climate':climate})
 assert ('features',climate) in calls and ('tree',climate) in calls
 assert all(c==climate for _,c in calls)
 assert state['climate']=='Historical' # caller-owned state is immutable.

@pytest.mark.parametrize('climate',['idealized_mid','idealized_high'])
def test_team_propagates_climate_to_response_and_radius_features(monkeypatch,climate):
 calls=[]
 def features(root,prefix,plans,c,history):
  calls.append(c);assert prefix['climate']==climate;return np.zeros((len(plans),36))
 monkeypatch.setattr(controller,'candidate_features',features)
 class Model:
  family='MLP';track='Sensorless'
  def applicability(self,x):return 0.,True
  def response_tensor(self,x,desc,**kw):
   m=np.zeros((len(x),1,32,6));m[...,0]=5.;m[...,2]=20.;m[...,3]=.7;return m
  def calibration_radius(self,*a):return 0.
  def prior_status(self,*a):return {}
 team=controller.FiveSpecialistTeam('unused',Model())
 def tree(name,asof,c,**kw):
  calls.append(c);return np.zeros((1,9)),np.ones(1),np.zeros(1),np.zeros(1),{}
 team.climate=SimpleNamespace(tree=tree)
 state=dict(stage=3,n_fert_cum=60.,region_id='fixture',as_of='2001-04-01',climate=climate)
 team.choose(state,SimpleNamespace(values=np.zeros((14,6)),dates=(),source_id='fixture'))
 assert len(calls)==3 and set(calls)=={climate}
 assert public_state(state,'Sensorless')['climate']==climate


def test_actual_scenario_weather_history_keeps_shift_and_provenance():
 from pathlib import Path
 from datetime import date
 from pcse_gym.agromas.physiology import ScenarioWeather
 from pcse_gym.agromas.season import regional_weather
 from pcse_gym.agromas_v8.online_features import history_from_provider
 root=Path(__file__).resolve().parents[3];name='netherlands_lelystad';day=date(2001,4,1)
 source=regional_weather(str(root),name,'v2');base=history_from_provider(source,name,day)
 shifted=history_from_provider(ScenarioWeather(source,1.8),name,day)
 np.testing.assert_allclose(shifted.values[:,:2],base.values[:,:2]+1.8)
 assert shifted.source_id!=base.source_id and shifted.dates==base.dates
 assert max(shifted.dates)==day
