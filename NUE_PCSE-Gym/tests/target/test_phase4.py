import numpy as np
import torch
import gymnasium as gym
import pytest
from pcse_gym.agent.active_ppo import active_decisions,active_stats,active_mean

def test_active_gradient_invariant_to_passive_padding_and_empty_batch():
 def gradient(passive):
  w=torch.tensor(.2,requires_grad=True);adv=torch.tensor([2.,-1.]+[1e6]*passive);features=torch.tensor([1.,-2.]+[100.]*passive);mask=torch.tensor([True,True]+[False]*passive)
  loss=active_mean(-(w*features).exp()*adv,mask);loss.backward();return w.grad
 assert torch.allclose(gradient(0),gradient(1000))
 x=torch.ones(3,requires_grad=True);loss=active_mean(x,torch.zeros(3,dtype=torch.bool));loss.backward();assert loss==0 and torch.equal(x.grad,torch.zeros(3))

def test_rollout_active_moments_ignore_passive_outliers_and_singleton():
 assert active_stats([1,3,1e10],[True,True,False])==(2.,1.)
 assert active_stats([7,1e10],[True,False])==(0.,1.)
 assert active_stats([7],[False])==(0.,1.)
 obs=torch.zeros(3,4,20);obs[:,-1,11]=1;obs[1,-1,14]=1
 assert active_decisions(obs,11).tolist()==[False,True,False]
 assert active_decisions(obs,None).all()

def test_runtime_depth_fail_closed_before_sm_access():
 from types import SimpleNamespace as S
 from pcse_gym.envs.moisture4 import measured_water
 calls=[];m=S(parameterprovider={'soil_profile':[S(Thickness=10.)]},get_variable=lambda key:calls.append(key) or [.2])
 e=S(unwrapped=S(sb3_env=S(model=m)))
 with pytest.raises(ValueError,match='20cm'):measured_water(e)
 assert calls==[]
 m.parameterprovider['soil_profile'][0].Thickness=20.
 assert measured_water(e)==.2 and calls==['SM']

def test_undiscounted_closed_episode_returns_cancel_intermediate_values():
 from pcse_gym.agent.ppo_mod import RolloutBufferSteps
 b=RolloutBufferSteps(4,gym.spaces.Box(-1,1,(2,),dtype=np.float32),gym.spaces.Discrete(9),n_envs=1,gamma=1,gae_lambda=1,constraint_mode='corrected')
 for i in range(4):
  b.add_nitrogen_info([0],[0],[i==3]);b.add_dvs([1.]);b.executed_actions=np.array([0]);b.add(np.zeros((1,2)),np.array([0]),np.array([8. if i==3 else 0.]),np.array([i==0]),torch.tensor([100.*i]),torch.tensor([10.*i]),torch.zeros(1))
 b.compute_returns_and_advantage(torch.tensor([999.]),torch.tensor([999.]),np.array([True]))
 assert np.allclose(b.returns[:,0],8)

def fixture_cal():
 return dict(model='ridge',mean=[0]*6,scale=[1]*6,coefficients=[[0]*6,[0,0,0,10,0,0],[0]*6,[0]*6,[0]*6,[0]*6],intercepts=[0,0,2,0,0,0])

def test_state_adaptive_distribution_paths_gradient_and_roundtrip(tmp_path):
 from pcse_gym.envs.moisture4 import AdaptiveMoisturePolicy,adaptive_total
 from pcse_gym.envs.observable import CausalGRUExtractor
 c=fixture_cal();space=gym.spaces.Box(-np.inf,np.inf,(4,20),dtype=np.float32);p=AdaptiveMoisturePolicy(space,gym.spaces.Discrete(9),lambda _:1e-3,utility_calibration=c,prior_strength=.1,features_extractor_class=CausalGRUExtractor,features_extractor_kwargs=dict(features_dim=7),net_arch=dict(pi=[32,32],vf=[32,32]))
 obs=torch.zeros(2,4,20);obs[:,-1,0]=.7;obs[:,-1,5]=130/400;obs[:,-1,11:]=1;obs[0,-1,10]=.1;obs[1,-1,10]=.4
 assert adaptive_total(obs[:,-1,:11],c).tolist()==[180,190]
 assert np.array_equal(adaptive_total(obs[:,-1,:11].numpy(),c),[180,190])
 a,v,cv,lp=p(obs,deterministic=True);assert a.tolist()==[5,6];assert torch.allclose(lp,p.evaluate_actions(obs,a)[2])
 (-lp.mean()).backward();assert p.action_net.weight.grad.abs().sum()>0;assert p.features_extractor.gru.weight_ih_l0.grad.abs().sum()>0
 p.save(tmp_path/'policy');q=AdaptiveMoisturePolicy.load(tmp_path/'policy');assert torch.equal(p(obs,True)[0],q(obs,True)[0])
 assert sum(x.numel() for x in p.parameters())==4908

def test_frozen_forest_numpy_torch_and_prior_varies_on_training_states():
 import pathlib,json
 from pcse_gym.envs.moisture4 import utility_scores,adaptive_total
 root=pathlib.Path(__file__).resolve().parents[3];c=json.loads((root/'reports/phase3c-frozen-utility-v1.json').read_text());records=json.loads((root/'reports/phase3c-training-utility-grid.json').read_text())['records'];x=np.array([r['observation'][-1][:11] for r in records],np.float32)
 assert np.allclose(utility_scores(x,c),utility_scores(torch.tensor(x),c).numpy())
 assert len(set(adaptive_total(x,c).tolist()))>=2
