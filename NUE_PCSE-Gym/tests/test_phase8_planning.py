import numpy as np
from pcse_gym.agromas_v8.planning import CoreAgronomicAgent,Regime,legal_schedules,upper_cvar,distribution_metrics

def responses(plans,branches=4,basal=0.):
 rng=np.random.default_rng(12);n=len(plans);m=np.zeros((n,branches,32,6));fert=basal+plans.sum(1);m[...,4]=fert[:,None,None];m[...,5]=3.5
 m[...,0]=4+fert[:,None,None]/100+np.arange(branches)[None,:,None]/5
 m[...,1]=70+.45*fert[:,None,None]+rng.normal(0,3,(n,branches,32));m[...,2]=m[...,4]+3.5-m[...,1];m[...,3]=m[...,1]/(m[...,4]+3.5);return m

def test_monolithic_equals_five_specialists_bit_for_bit():
 for stage in [1,2,3]:
  for cap in [25.,35.,40.,50.]:
   for remove in [None,'eco','econ']:
    plans=legal_schedules(stage,0.);m=responses(plans);r=Regime(cap=cap,eco=remove!='eco',econ=remove!='econ');args=(stage,plans,m,np.array([.1,.2,.3,.4]),np.array([0,0,1,1]),np.array([0,1,0,1]))
    a=CoreAgronomicAgent(r).choose(*args);b=CoreAgronomicAgent(r,monolithic=True).choose(*args)
    assert a['dose']==b['dose'] and a['tier']==b['tier'];np.testing.assert_array_equal(a['branch_plan_indices'],b['branch_plan_indices'])
    np.testing.assert_array_equal(a['metrics']['mean'],b['metrics']['mean'])

def test_shared_information_prevents_wait_and_see_actions():
 plans=np.array([[0,0,0],[0,100,0]],float);m=np.zeros((2,2,32,6));m[...,5]=3.5
 m[0,0,:,0]=11;m[0,1,:,0]=1;m[1,0,:,0]=1;m[1,1,:,0]=11;m[...,2]=3.5
 r=Regime(eco=False,econ=False);d=CoreAgronomicAgent(r).choose(2,plans,m,np.array([.5,.5]),np.zeros(2,int),np.zeros(2,int))
 chosen=plans[d['branch_plan_indices'],1];assert chosen[0]==chosen[1]
 assert d['metrics']['mean'][0]==6 # clairvoyant path-specific max would be11

def test_tree_actions_shared_within_each_observable_node():
 plans=legal_schedules(1,0);m=responses(plans,8);rain=np.repeat([0,1],4);temp=np.tile(np.repeat([0,1],2),2)
 d=CoreAgronomicAgent(Regime(eco=False,econ=False)).choose(1,plans,m,np.full(8,1/8),rain,temp);selected=plans[d['branch_plan_indices']]
 assert len(set(selected[:,0]))==1
 for group in [0,1]:assert len(set(selected[rain==group,1]))==1
 for group in [0,1,2,3]:assert len(set(selected[(rain*2+temp)==group,2]))==1

def test_operational_tier_three_zero_is_not_compliant():
 plans=legal_schedules(3,171);m=responses(plans,4,171);m[...,1]=30;m[...,2]=m[...,4]+3.5-30;m[...,3]=30/(m[...,4]+3.5)
 d=CoreAgronomicAgent(Regime(cap=25.)).choose(3,plans,m,np.full(4,.25),np.zeros(4,int),np.zeros(4,int))
 assert d['tier']==3 and d['dose']==0 and 'not_compliance' in d['reason']
 assert not d['metrics']['eco_safe']

def test_weighted_tail_uses_fractional_boundary_mass():
 assert upper_cvar([0,10],[.95,.05],.1)==5

def test_node_marginal_integrates_full_branch_product():
 m=np.zeros((2,32,6));m[0,:,2]=np.arange(32);m[1,:,2]=100+np.arange(32);m[...,5]=3.5
 d=distribution_metrics(m,[.25,.75],Regime(eco=False,econ=False));expected=.25*np.arange(32).mean()+.75*(100+np.arange(32)).mean()
 assert d['mean'][2]==expected

def test_basal171_is_part_of_total_budget_at_every_stage():
 from pcse_gym.agromas_v8.planning import legal_schedules
 for stage in (1,2,3):
  plans=legal_schedules(stage,171.)
  assert np.all(171.+plans.sum(1)<=220.)
  assert np.max(plans)<=40.

def test_frozen_open_loop_rechecks_current_safety_instead_of_reusing_initial_tier(monkeypatch):
 from types import SimpleNamespace
 from pcse_gym.agromas_v8 import policies
 # Both fixed proposal and zero are predicted above the upper corridor; the
 # current action must be operational zero/Tier3 despite an initial Tier1.
 class Model:
  track='Sensorless';radius=0.
  def applicability(self,x):return 0.,True
  def calibration_radius(self,x,context):return 0.
  def prior_status(self,x,context):return {}
  def response_tensor(self,x,desc,**kwargs):
   m=np.zeros((len(x),1,32,6));m[:,:,:,2]=100.;m[:,:,:,3]=.7;return m
 model=Model();climate=SimpleNamespace(tree=lambda *a,**k:(np.zeros((1,9)),np.ones(1),None,None,None));team=SimpleNamespace(model=model,root='unused',climate=climate)
 monkeypatch.setattr(policies,'candidate_features',lambda root,prefix,plans,**kw:np.zeros((len(plans),36)))
 p=policies.TreePolicy(team,mode='open-loop');p.frozen=np.array([60.,80.,80.]);p.frozen_tier=1
 d=p.choose(dict(stage=2,n_fert_cum=60.,region_id='fixture',as_of='2001-04-01'),SimpleNamespace(values=np.zeros((14,6))),{})
 assert d['dose']==0 and d['tier']==3
 np.testing.assert_array_equal(p.frozen,[60,80,80])

def test_frozen80_continuation_prioritizes_the_next_stage_under_budget():
 from pcse_gym.agromas_v8.planning import legal_schedules,frozen_continuation_indices
 plans=legal_schedules(1,0);selected,doses=frozen_continuation_indices(plans,1);chosen=selected[doses.index(100.)]
 np.testing.assert_array_equal(plans[chosen],[100,80,40])
 for stage in (1,2,3):
  for committed in (0,60,171,210,220):
   plans=legal_schedules(stage,committed);selected,doses=frozen_continuation_indices(plans,stage)
   assert len(selected)==len(set(plans[:,stage-1]))
   assert np.all(plans[selected].sum(1)+committed<=220)

def test_legacy_v6_never_queries_illegal_budget_candidates(monkeypatch):
 from pathlib import Path
 from pcse_gym.agromas_v8.policies import LegacyV6Policy
 from pcse_gym.agromas_v8 import online_features
 from pcse_gym.agromas_v8.planning import GRID
 for committed in (160.,171.,210.,220.):
  base=np.zeros(22);base[0]=.9;base[3]=committed;base[5]=3
  monkeypatch.setattr(online_features,'feature_base',lambda *a,**k:base.copy())
  calls=[]
  def model(x):
   assert np.all(x[:,3]+x[:,-1]<=220+1e-8)
   calls.extend(x[:,-1]);members=np.zeros((len(x),32,6));fert=x[:,3]+x[:,-1];members[:,:,4]=fert[:,None];members[:,:,5]=3.5;members[:,:,1]=.7*(fert+3.5)[:,None];members[:,:,2]=.3*(fert+3.5)[:,None];members[:,:,3]=.7;return members
  policy=LegacyV6Policy.__new__(LegacyV6Policy);policy.root=Path('/unused');policy.seed=None;policy.models={3:model}
  decision=policy.choose(dict(stage=3,region_id='china_ncp_luancheng'),None,{})
  np.testing.assert_array_equal(calls,GRID[committed+GRID<=220+1e-8]);assert decision['dose']<=220-committed

def test_wur_driver_satisfies_native_engine_type_without_changing_weather():
 from pathlib import Path
 from datetime import date
 from pcse.base.weather import WeatherDataProvider
 from pcse.input import CSVWeatherDataProvider
 from pcse_gym.agromas_v8.referee import WURHistoricalWeather
 root=Path(__file__).resolve().parents[2];wrapped=WURHistoricalWeather(root);original=CSVWeatherDataProvider(str(root/'data/52.57-5.63_random_weather.csv'))
 assert isinstance(wrapped,WeatherDataProvider)
 assert wrapped.latitude==original.latitude and wrapped.longitude==original.longitude
 for day in (date(2014,9,1),date(2018,4,1),date(2021,8,20)):
  for field in ('TMIN','TMAX','RAIN','VAP','IRRAD','WIND','E0','ES0','ET0'):
   assert getattr(wrapped(day),field)==getattr(original(day),field)
