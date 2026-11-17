import numpy as np
import pytest
import torch
from pcse_gym.agromas_v8.models import WorldModel
from pcse_gym.agromas_v8.scoring import project_executed_members,brier,bss,conformal_radius,ranking_regret
from pcse_gym.agromas_v8.data import parity_features

def test_equal_parameter_cap_and_nonzero_gradients():
 torch.set_num_threads(1);counts=[]
 for name in ['mlp','residual-mlp']:
  torch.manual_seed(4);model=WorldModel(architecture=name);model.train()
  x=torch.randn(8,36);y=torch.randn(8,3);loss=(model(x)-y).square().mean();loss.backward()
  assert all(p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum()>0 for p in model.parameters())
  counts.append(sum(p.numel() for p in model.parameters()))
  model.eval();copy=WorldModel(architecture=name);copy.load_state_dict(model.state_dict(),strict=True);copy.eval()
  assert torch.equal(model(x),copy(x))
 assert counts[0]==counts[1]

def test_skipped_dose_not_projected_up_to_nominal_plan():
 x=np.zeros((1,36));x[:,3]=30;x[:,22:25]=[80,60,40]
 m=project_executed_members(np.array([[[6.,50.,70.],[6.,10000.,20.]]]),x)
 assert m[0,0,4]==70 and m[0,1,4]==30
 assert m[0,1,1]==6000
 assert np.allclose(m[...,2],m[...,4]+3.5-m[...,1])
 assert np.allclose(m[...,3],m[...,1]/(m[...,4]+3.5))
 assert np.array_equal(x[:,22:25],[[80,60,40]])

def test_sensorless_removes_only_privileged_telemetry():
 x=np.arange(72.).reshape(2,36);y=parity_features(x,'Sensorless');assert (y[:,[1,2,4]]==0).all()
 keep=[i for i in range(36) if i not in (1,2,4)];assert np.array_equal(x[:,keep],y[:,keep])

def test_brier_skill_detects_climatology_collapse():
 y=np.array([0,0,0,1]);base=brier(np.full(4,.25),y)
 assert bss(brier(np.full(4,.25),y),base)==0
 assert bss(brier(y,y),base)==1
 assert bss(brier(1-y,y),base)<0
 with pytest.raises(ValueError):bss(0,0)

def test_conformal_higher_rank_and_regret():
 assert conformal_radius(np.arange(19.))==17
 meta=[{'prefix':'a'},{'prefix':'a'},{'prefix':'b'},{'prefix':'b'}]
 assert ranking_regret(meta,[0,1,1,0],np.array([1,5,7,3]))==(0.,2)
 assert ranking_regret(meta,[1,0,0,1],np.array([1,5,7,3]))==(4.,2)

def test_ecology_and_economics_are_orthogonal():
 from pcse_gym.agromas_v8.agents import UrbanEcoSafetyAgent,SocioEconomicPolicyAgent
 m=np.array([[[6.,70.,20.,.8,100.,3.5]]*32]);eco=UrbanEcoSafetyAgent();econ=SocioEconomicPolicyAgent()
 assert eco.assess(m)['surplus_safe'][0] and econ.assess(m)['NUE_safe'][0]
 n=m.copy();n[...,3]=1.2
 assert eco.assess(n)['surplus_safe'][0] and not econ.assess(n)['NUE_safe'][0]
 n=m.copy();n[...,2]=90
 assert not eco.assess(n)['surplus_safe'][0] and econ.assess(n)['NUE_safe'][0]

def test_vector_quarantine_for_agent_requests_and_replies():
 from pcse_gym.agromas_v8.agents import validate_public_payload
 validate_public_payload({'members':np.ones((1,32,6)),'site_prior_id':'opaque-id'})
 for payload in [{'A00':.4},{'nested':{'A63':-.3}},{'prior':[float(i) for i in range(64)]}]:
  with pytest.raises(ValueError):validate_public_payload(payload)


def test_projection_cannot_invent_unrequested_fertilizer():
 x=np.zeros((2,36));x[:,3]=[0,171];x[1,22:25]=[10,20,0]
 m=project_executed_members(np.array([[[6.,50.,150.]],[[6.,50.,220.]]]),x)
 assert m[0,0,4]==0 and m[1,0,4]==201

def test_observable_domain_ignores_hidden_telemetry_and_scenarios():
 from pcse_gym.agromas_v8.ood import ApplicabilityDomain
 rng=np.random.default_rng(4);x=rng.normal(size=(80,36));d=ApplicabilityDomain('Sensorless').fit(x);s,a=d.score(x)
 y=x.copy();y[:,[1,2,4]]+=1000;y[:,27:]+=10000;y[:,22:25]+=20000
 t,b=d.score(y);assert np.array_equal(s,t) and np.array_equal(a,b)
 y=x.copy();y[:,0]+=1000
 assert not d.score(y)[1].any()

def test_twin_interface_rejects_oracles_hidden_sensorless_and_future_weather():
 from pcse_gym.agromas_v8.agents import SpatialTwinSurrogateAgent
 class Tool:
  def predict_joint_response(self,request):return {'members':np.ones((1,32,6)),'applicable':True}
 a=SpatialTwinSurrogateAgent(Tool());q={'as_of':'2012-04-01','site_prior_id':'id','observable_prefix':{'dvs':.4,'n_fert_cum':0,'stage':1},'dose_schedules':[[0,0,0]]}
 assert a.predict_joint_response(q)['applicable']
 for extra in [{'engine':object()},{'future_weather':[0,1,2]},{'state_dict':{}}]:
  with pytest.raises(ValueError):a.predict_joint_response(dict(q,**extra))
 for hidden in [{'sm':.3},{'soil_N':120},{'weather_prefix':[{'date':'2012-04-02','rain':2.}]}]:
  with pytest.raises(ValueError):a.predict_joint_response(dict(q,observable_prefix=dict(q['observable_prefix'],**hidden)))
 assert a.predict_joint_response(dict(q,information_track='Full-Telemetry',observable_prefix=dict(q['observable_prefix'],sm=.3)))['applicable']

def test_macro_regret_weights_world_stages_and_excludes_singletons():
 meta=[{'prefix':'a','region':'r','year':2000,'stage':1}]*2+[{'prefix':'b','region':'s','year':2000,'stage':1}]*2+[{'prefix':'c','region':'r','year':2000,'stage':1}]
 v,g=ranking_regret(meta,[2,1,1,2,1],np.array([0,10,0,4,100]),macro=True)
 assert v==5 and g==2
 with pytest.raises(ValueError):ranking_regret([{'prefix':'a'}],[1],[2])

def test_exact_conformal_order_and_negative_cqr_scores():
 assert conformal_radius(np.arange(19.))==np.sort(np.arange(19.))[17]
 assert conformal_radius(-np.arange(19.))==-1
 assert np.isinf(conformal_radius(np.array([1.])))
 from pcse_gym.agromas_v8.agents import validate_public_payload
 validate_public_payload({'applicable':np.bool_(True)})
 with pytest.raises(ValueError):validate_public_payload({'prior':np.arange(64).reshape(64,1)})

def test_missing_physical_receipt_does_not_burn_dev_claim(tmp_path):
 from pcse_gym.agromas_v8.data import load_dev_once
 (tmp_path/'reports/phase8').mkdir(parents=True)
 with pytest.raises(ValueError):load_dev_once(tmp_path,'digest')
 assert not (tmp_path/'reports/phase8/phase8b-dev-access-claim.json').exists()

def test_joint_member_center_uses_seed_mean_not_seed_order():
 from pathlib import Path
 import importlib.util
 path=Path(__file__).resolve().parents[2]/'scripts/phase8-evaluate-g1.py'
 spec=importlib.util.spec_from_file_location('phase8_eval_unit',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 p=module.Predictor.__new__(module.Predictor);p.track='Full-Telemetry';p.arch='mlp';p.device='cpu';p.models=[]
 for offset in [1.,2.,9.]:
  model=torch.nn.Linear(36,3)
  with torch.no_grad():model.weight.zero_();model.bias.fill_(offset)
  c={'x_active':np.ones(36,bool),'x_mean':np.zeros(36),'x_std':np.ones(36),'y_std':np.ones(3),'y_mean':np.zeros(3)}
  p.models.append((model.eval(),c))
 x=np.zeros((2,36));before=p.predict(x);p.models.reverse();after=p.predict(x)
 np.testing.assert_allclose(before,4.,atol=0,rtol=0)
 np.testing.assert_array_equal(before,after)
