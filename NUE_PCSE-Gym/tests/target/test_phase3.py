import numpy as np
import torch
import gymnasium as gym
import pytest
from pcse_gym.envs.phase3 import MaskedCostPolicy,envelope,prior_action
from pcse_gym.envs.constraints import AgronomicShield

def test_mask_probability_and_all_policy_paths():
    space=gym.spaces.Box(-np.inf,np.inf,(1,19),dtype=np.float32)
    p=MaskedCostPolicy(space,gym.spaces.Discrete(9),lambda _:1e-3,net_arch=dict(pi=[32,32],vf=[32,32]))
    obs=torch.zeros((16,1,19));obs[:,:,10]=1;obs[:,:,13]=1
    d=p.get_distribution(obs)
    assert torch.all(d.distribution.probs[:,[1,2,4,5,6,7,8]]==0)
    for _ in range(10):
        a,v,c,lp=p(obs)
        assert set(a.tolist())<={0,3}
        assert torch.allclose(lp,p.evaluate_actions(obs,a)[2])
    predicted=p.predict(obs.numpy(),deterministic=True)[0]
    assert set(predicted.tolist())<={0,3}
    loss=-p.evaluate_actions(obs,torch.full((16,),3))[2].mean();loss.backward()
    assert p.action_net.weight.grad.abs().sum()>0

def test_causal_mask_boundaries():
    shield=object.__new__(AgronomicShield)
    shield.current_dvs=.5;shield.day=21;shield.last_day=0;shield.counter=0;shield.n_budget=165;shield.n_counter=120;shield.min_days=14;shield.max_applications=4
    assert shield.get_action_mask().tolist()==[True]*5+[False]*4
    shield.current_dvs=.9
    assert shield.get_action_mask().sum()==1
    shield.current_dvs=.5;shield.counter=4
    assert shield.get_action_mask().sum()==1

def test_envelope_and_prior():
    for rain in [-100,0,100]:
        for lai in [-100,0,100]:
            f=np.zeros(10);f[1]=lai;f[4]=rain
            assert 130<=envelope(f)<=195
    f=np.zeros(10);f[0]=.2;assert prior_action(f)==5
    f[0]=.4;f[5]=50/400;assert prior_action(f)==6
    f[0]=.7;f[5]=110/400;assert prior_action(f)==5

def test_rejected_proposal_keeps_probability_but_zero_step_cost():
    from pcse_gym.agent.ppo_mod import RolloutBufferSteps
    b=RolloutBufferSteps(1,gym.spaces.Box(-1,1,(2,),dtype=np.float32),gym.spaces.Discrete(9),n_envs=1,constraint_mode='corrected')
    b.add_nitrogen_info([0],[0],[False]);b.add_dvs([1.1]);b.executed_actions=np.array([0])
    z=torch.zeros(1);lp=torch.tensor([-.73])
    b.add(np.zeros((1,2)),np.array([8]),np.zeros(1),np.array([True]),z,z,lp)
    assert b.actions[0,0,0]==8 and np.isclose(b.log_probs[0,0],-.73)
    assert b.costs[0,0]==0 and b._running_count[0]==0

@pytest.mark.parametrize("version",[1,2])
def test_full_environment_prior_and_reward_telescope(version):
    from pcse_gym.initialize_envs import initialize_env
    from pcse_gym.envs.observable import OBSERVABLE_CROP
    from pcse_gym.envs.phase3 import Phase3History
    env=initialize_env(pcse_env=2,crop_features=list(OBSERVABLE_CROP),action_features=[],years=[3002],locations=[(52.57,5.63)],random_weather=True,random_init=False,reward='NUE',seed=4)
    env=Phase3History(AgronomicShield(env,n_budget=195),history=4,aligned=True,guided=True,envelope_version=version)
    try:
        obs,_=env.reset();assert obs.shape==(4,19)
        done=False;total=0.;nitrogen=0.;n=0
        while not done:
            a=prior_action(obs[-1,:10]);a=a if obs[-1,10+a] else 0
            valid=int(obs[-1,10:].sum())
            assert abs(obs[-1,9]*400-max(0,env.env.n_budget-env.cumulative))<1e-4
            if version==2:
                from pcse_gym.envs.phase3 import stage_remaining
                remaining=stage_remaining(float(obs[-1,0]),env.cumulative,env.env.n_budget)
                assert all(not obs[-1,10+i] or i*10<=remaining+1e-5 for i in range(1,9))
            obs,r,term,trunc,info=env.step(a);done=term or trunc;total+=r;nitrogen+=info['executed_action']*10;n+=1
            assert info["valid_mask_action_count"]==valid
            assert list(info["reward"].values())[-1]==r
            assert "native_reward" in info
            assert info['executed_violation_rate']==0
            assert info['proposed_action']==a
        yield_t=float(list(info['WSO'].values())[-1])/1000
        assert abs(total-(yield_t-.002*nitrogen))<1e-6
        assert 120<=nitrogen<=195 and n>20
        obs,_=env.reset();assert obs[-1,5]==0 and env.previous_wso==0
    finally:env.close()

def test_second_envelope_uses_observed_rain_scale_and_preserves_v1():
    f=np.zeros(10);f[1]=.4;f[4]=.03
    assert envelope(f)==envelope(f,1)
    assert 175<=envelope(f,2)<=195
    dry=f.copy();dry[4]=0
    wet=f.copy();wet[4]=.1
    assert envelope(dry,2)<envelope(wet,2)
    for x in [-100,100]:
        f[1]=f[4]=x
        assert 130<=envelope(f,2)<=195


def test_mask_layout_rejects_normalization():
    import pytest
    p=MaskedCostPolicy(gym.spaces.Box(-np.inf,np.inf,(1,19),dtype=np.float32),gym.spaces.Discrete(9),lambda _:1e-3)
    obs=torch.zeros((1,1,19));obs[:,:,10]=1;obs[:,:,11]=.5
    with pytest.raises(ValueError,match='exact binary'):
        p(obs)

def test_v2_stage_budget_prevents_pre_window_exploration_exhausting_slots():
    from pcse_gym.envs.phase3 import stage_remaining
    assert stage_remaining(.05,0,190)==0
    assert stage_remaining(.2,0,190)==50
    assert stage_remaining(.2,50,190)==0
    assert stage_remaining(.4,50,190)==60
    assert stage_remaining(.7,110,190)==80
    assert stage_remaining(.9,110,190)==0


def test_prior_final_checkpoint_roundtrip(tmp_path):
    space=gym.spaces.Box(-np.inf,np.inf,(4,19),dtype=np.float32)
    p=MaskedCostPolicy(space,gym.spaces.Discrete(9),lambda _:1e-3,prior_strength=.5,prior_final=170.)
    obs=torch.zeros((1,4,19));obs[:,-1,0]=.7;obs[:,-1,5]=110/400;obs[:,-1,10:]=1
    original=p.get_distribution(obs).distribution.probs.detach()
    p.save(tmp_path/'policy')
    loaded=MaskedCostPolicy.load(tmp_path/'policy')
    assert loaded.prior_final==170 and loaded.prior_strength==.5
    torch.testing.assert_close(original,loaded.get_distribution(obs).distribution.probs)

@pytest.mark.parametrize('once,expected',[(True,2),(False,6)])
def test_dual_cadence_counts_real_rollout_updates(once,expected):
    from pcse_gym.agent.ppo_mod import LagrangianPPO,CostActorCriticPolicy
    from pcse_gym.envs.constraints import corrected_fertilization_action_constraint
    class Tiny(gym.Env):
        observation_space=gym.spaces.Box(-1,1,(1,10),dtype=np.float32)
        action_space=gym.spaces.Discrete(9)
        def reset(self,seed=None,options=None):
            self.k=0;return np.zeros((1,10),dtype=np.float32),{}
        def step(self,a):
            self.k+=1
            return np.zeros((1,10),dtype=np.float32),0.,self.k==2,False,dict(DVS={0:.5},NUE={0:.7},Nsurplus={0:20.},NLOSSCUM={0:0.},WSO={0:8000.},executed_action=0,decision_dvs=.5)
    model=LagrangianPPO(CostActorCriticPolicy,Tiny(),n_steps=2,batch_size=2,n_epochs=3,constraint_mode='corrected',constraint_fn=corrected_fertilization_action_constraint,dual_update_once=once,policy_kwargs=dict(net_arch=dict(pi=[8],vf=[8])),verbose=0)
    calls=[];model.lagrange.update_lagrange_multiplier=lambda c:calls.append(c)
    try:
        model.learn(total_timesteps=4)
        assert len(calls)==expected
    finally:model.env.close()

def test_v3_shared_windows_and_full_dose_headroom():
    from pcse_gym.envs.corridor import target,CorridorPolicy,cap
    assert float(target(.30,0))==70 and float(target(.60,70))==130
    assert float(target(.62,130))==190 and float(target(.88,130))==190
    assert float(target(.89,130))==130
    p=CorridorPolicy(gym.spaces.Box(-np.inf,np.inf,(4,19),dtype=np.float32),gym.spaces.Discrete(9),lambda _:1e-3,prior_final=210)
    obs=torch.zeros((1,4,19));obs[:,-1,0]=.7;obs[:,-1,5]=130/400;obs[:,-1,10:]=1
    with torch.no_grad():p.action_net.weight.zero_();p.action_net.bias.zero_()
    assert p.predict(obs.numpy(),deterministic=True)[0][0]==8
    for lai in [-100,0,100]:
        f=np.zeros(10);f[1]=lai
        assert 160<=cap(f,dict(intercept=190,LAI_coefficient=10,headroom=10))<=210

def test_v3_directional_reward_and_upper_only_dual():
    from pcse_gym.envs.corridor import terminal_compliance
    from pcse_gym.envs.constraints import upper_surplus_constraint
    assert terminal_compliance(.85,20)>terminal_compliance(1.1,-20)
    assert terminal_compliance(.85,20)>terminal_compliance(.7,65)
    assert terminal_compliance(.92,20)>terminal_compliance(1.02,20)
    args=[np.array([0,0]),np.array([4,4]),np.array([0,0]),np.array([-5,-5]),np.array([.5,.5]),np.array([1.2,.7]),np.array([20.,60.]),np.array([True,True])]
    c=upper_surplus_constraint(*args)
    assert c[3].tolist()==[0,0] and c[4].tolist()==[0,1]

def test_v3_numpy_torch_boundaries_and_buffer_direction():
    from pcse_gym.envs.corridor import target
    from pcse_gym.agent.ppo_mod import RolloutBufferSteps
    for d in [.10,.32,.62,.88]:
        x=np.float32(d);assert float(target(float(x),0))==float(target(torch.tensor([x]),torch.zeros(1))[0])
    b=RolloutBufferSteps(1,gym.spaces.Box(-1,1,(2,),dtype=np.float32),gym.spaces.Discrete(9),n_envs=2,constraint_mode='corrected',endpoint_cost_mode='upper_surplus')
    b.add_nitrogen_info([1.2,.7],[20,60],[True,True]);b.add_dvs([.5,.5]);b.executed_actions=np.array([0,0]);z=torch.zeros(2)
    b.add(np.zeros((2,2)),np.zeros(2),np.zeros(2),np.ones(2),z,z,z)
    assert b.costs[0].tolist()==[0,1]

def test_v3_full_season_terminal_telescope_and_fixed_early_splits():
    from pcse_gym.initialize_envs import initialize_env
    from pcse_gym.envs.observable import OBSERVABLE_CROP
    from pcse_gym.envs.corridor import CorridorHistory,target,terminal_compliance
    e=initialize_env(pcse_env=2,crop_features=list(OBSERVABLE_CROP),action_features=[],years=[3002],locations=[(52.57,5.63)],random_weather=True,random_init=False,reward='NUE',seed=4)
    e=CorridorHistory(AgronomicShield(e,n_budget=210));total=0.;nitrogen=0;done=False
    try:
        obs,_=e.reset()
        while not done:
            f=obs[-1,:10];a=int(np.clip(np.ceil((float(target(f[0],nitrogen))-nitrogen-1e-4)/10),0,8));a=max(i for i in range(a+1) if obs[-1,10+i])
            obs,r,t,tr,info=e.step(a);done=t or tr;total+=r;nitrogen+=info['executed_action']*10
            assert list(info['reward'].values())[-1]==r and info['executed_violation_rate']==0
        last=lambda k:float(list(info[k].values())[-1])
        expected=last('WSO')/1000-.002*nitrogen+terminal_compliance(last('NUE'),last('Nsurplus'))
        assert abs(total-expected)<1e-6 and nitrogen==190
    finally:e.close()

def test_v3_guided_wrapper_masks_every_pre_window_positive_dose():
    from pcse_gym.envs.corridor import CorridorHistory
    class PreWindow(gym.Env):
        observation_space=gym.spaces.Box(-np.inf,np.inf,(23,),dtype=np.float32)
        action_space=gym.spaces.Discrete(9)
        def reset(self,seed=None,options=None):
            x=np.zeros(23,dtype=np.float32);x[0]=.05;return x,{}
    e=CorridorHistory(AgronomicShield(PreWindow(),n_budget=210))
    o,_=e.reset();assert o[-1,10:].tolist()==[1]+[0]*8

def test_water_sensor_reads_only_measurable_top_layer_and_profiles_match():
    from types import SimpleNamespace
    from pathlib import Path
    import re
    from pcse_gym.envs.moisture import measured_water
    class Sensor:
        def __init__(self):self.calls=[]
        def get_variable(self,name):
            self.calls.append(name);assert name=='SM';return [.24,.99]
    sensor=Sensor();env=SimpleNamespace(unwrapped=SimpleNamespace(sb3_env=SimpleNamespace(model=sensor)))
    assert measured_water(env)==.24 and sensor.calls==['SM']
    root=Path(__file__).resolve().parents[2]/'pcse_gym/envs/configs/soil'
    for name in ['arminda_soil.yaml','EC1-coarse_soil.yaml','EC6-fine_soil.yaml']:
        assert float(re.search(r'Thickness:\s*([0-9.]+)',(root/name).read_text()).group(1))==20

def test_water_policy_uses_mask_offset11_and_has_nonzero_gradient(tmp_path):
    from pcse_gym.envs.moisture import MoisturePolicy
    from pcse_gym.envs.observable import CausalGRUExtractor
    space=gym.spaces.Box(-np.inf,np.inf,(4,20),dtype=np.float32)
    p=MoisturePolicy(space,gym.spaces.Discrete(9),lambda _:1e-3,prior_final=210,features_extractor_class=CausalGRUExtractor,features_extractor_kwargs=dict(features_dim=7),net_arch=dict(pi=[32,32],vf=[32,32]))
    obs=torch.zeros((3,4,20));obs[:,-1,0]=.7;obs[:,-1,5]=130/400;obs[:,-1,10]=.24;obs[:,-1,11]=1;obs[:,-1,19]=1
    a,v,c,lp=p(obs);assert set(a.tolist())<={0,8};assert torch.allclose(lp,p.evaluate_actions(obs,a)[2]);assert torch.all(p.get_distribution(obs).distribution.probs[:,1:8]==0)
    loss=-p.evaluate_actions(obs,torch.full((3,),8))[2].mean();loss.backward();assert p.action_net.weight.grad.abs().sum()>0
    p.save(tmp_path/'water');q=MoisturePolicy.load(tmp_path/'water');torch.testing.assert_close(p.get_distribution(obs).distribution.probs,q.get_distribution(obs).distribution.probs)
    assert sum(x.numel() for x in p.parameters())==4908

def test_water_full_season_rewards_and_observation_contract():
    from pcse_gym.initialize_envs import initialize_env
    from pcse_gym.envs.observable import OBSERVABLE_CROP
    from pcse_gym.envs.moisture import MoistureHistory
    from pcse_gym.envs.corridor import target,terminal_compliance
    native=initialize_env(pcse_env=2,crop_features=list(OBSERVABLE_CROP),action_features=[],years=[3002],locations=[(52.57,5.63)],random_weather=True,random_init=False,reward='NUE',seed=4)
    e=MoistureHistory(AgronomicShield(native,n_budget=210),joint_bonus=8);done=False;total=0.;N=0
    try:
        obs,_=e.reset();assert obs.shape==(4,20)
        while not done:
            assert 0<=obs[-1,10]<=1 and obs[-1,11]==1
            a=int(np.clip(np.ceil((float(target(obs[-1,0],N))-N-1e-4)/10),0,8));a=max(i for i in range(a+1) if obs[-1,11+i])
            obs,r,t,tr,info=e.step(a);done=t or tr;total+=r;N+=info['executed_action']*10
            assert info['executed_violation_rate']==0 and list(info['reward'].values())[-1]==r
        last=lambda k:float(list(info[k].values())[-1])
        assert abs(total-(last('WSO')/1000-.002*N+terminal_compliance(last('NUE'),last('Nsurplus'),8)))<1e-6
    finally:e.close()
