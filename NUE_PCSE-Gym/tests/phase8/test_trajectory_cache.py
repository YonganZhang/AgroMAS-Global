"""Synthetic unit fixtures for cache control flow, never evaluation evidence."""
from datetime import date
import numpy as np
import pytest
from pcse_gym.agromas.climate_agent import WeatherHistory
from pcse_gym.agromas_v8 import trajectory_cache as module
from pcse_gym.agromas_v8.referee import decision_trace

class Policy:
 def __init__(self,doses=(40.,40.,40.)):self.doses=doses;self.calls=0
 def choose(self,state,history,case):
  assert state['stage']==self.calls+1;self.calls+=1
  return dict(dose=self.doses[state['stage']-1],tier=case['tier'],request_hash=case['tag'],reason='synthetic_unit_fixture_only')

@pytest.fixture
def fixture(monkeypatch):
 calls=[]
 def native(root,case,policy,permit):
  calls.append(case['tag']);fert=0.;trace=[];events=[]
  for stage in (1,2,3):
   day=date(2001,stage+2,1);state=dict(region_id='fixture',as_of=day.isoformat(),stage=stage,n_fert_cum=fert,climate='Historical')
   h=WeatherHistory((day,),np.zeros((1,6)),'fixture','unit_source')
   d=policy.choose(state,h,case);dose=float(d['dose']);fert+=dose;trace.append(decision_trace(state,d,dose));events.append(dict(stage=stage,date=day.isoformat(),dose=dose,reason='chosen'))
  m=[5.,.7*(fert+3.5),.3*(fert+3.5),.7,fert,3.5];joint=0<=m[2]<=case['cap'];profit=1000-1.5*case.get('price_multiplier',1)*fert+case.get('subsidy',0)*joint
  return dict(case=case,outcome=m,trace=trace,events=events,mass_audit={'passed':True,'daily_rows':1},stock_diagnostics={'synthetic_unit_fixture_only':True},Native_N_loss=1.,native_weekly_steps=40,weather_source_id='unit_source',joint=joint,partial_profit=profit,NUE_compliant=True,surplus_compliant=joint)
 monkeypatch.setattr(module,'run_episode',native)
 return module.NativeWorldCache(None,('fixture',2001,'Historical','NASA'),None),calls

def case(tag='a',cap=40.,tier=1):return dict(region='fixture',year=2001,climate='Historical',source='NASA',tag=tag,cap=cap,tier=tier,subsidy=50.)

def test_replay_recomputes_case_trace_joint_and_profit(fixture):
 cache,calls=fixture;a=Policy();first=cache.run(case(),a);b=Policy();second=cache.run(case('b',25.,3),b)
 assert calls==['a'] and a.calls==b.calls==3
 assert first['joint'] and not second['joint']
 assert first['partial_profit']-second['partial_profit']==50.
 assert all(t['request_hash']=='b' and t['tier']==3 for t in second['trace'])
 assert second['outcome']==first['outcome'] and second['events']==first['events']
 assert second['native_cache']['trajectory_replayed']

def test_unknown_suffix_does_not_advance_stateful_policy_twice(fixture):
 cache,calls=fixture;cache.run(case(),Policy());p=Policy((40.,20.,0.));r=cache.run(case('new'),p)
 assert calls==['a','new'] and p.calls==3
 assert [x['dose'] for x in r['trace']]==[40.,20.,0.]
 q=Policy((40.,20.,0.));cached=cache.run(case('again'),q)
 assert len(calls)==2 and q.calls==3 and cached['native_cache']['trajectory_replayed']
 assert cache.receipt()['unique_executed_trajectories']==2

def test_cross_world_access_is_rejected(fixture):
 cache,_=fixture
 with pytest.raises(ValueError,match='Cross-world'):cache.run(case()|{'year':2002},Policy())


def test_archive_seed_never_replays_policy_or_invents_public_prefix(fixture,tmp_path):
 import json,hashlib
 cache,calls=fixture;first=cache.run(case(),Policy());first.pop('native_cache')
 first['mass_audit'].update(daily_records=[dict(N_residual_kg_ha=0.,C_residual_kg_ha=0.)])
 path=tmp_path/'archive.json';path.write_text(json.dumps(first));digest=hashlib.sha256(path.read_bytes()).hexdigest()
 recovered=module.NativeWorldCache(None,cache.world,None);assert recovered.seed_archive(path,digest)
 assert recovered.nodes=={} and recovered.archive_paths==1
 # Synthetic native fixture returns a shorter audit than the real archive;
 # clear terminal expectation to exercise public-prefix recovery only here.
 recovered.executed.clear();p=Policy();recovered.run(case('recovered'),p)
 assert len(calls)==2 and p.calls==3 and recovered.nodes
 q=Policy();r=recovered.run(case('new-policy',25.,3),q)
 assert len(calls)==2 and q.calls==3 and r['trace'][0]['request_hash']=='new-policy'
 with pytest.raises(ValueError,match='hash mismatch'):recovered.seed_archive(path,'bad')
