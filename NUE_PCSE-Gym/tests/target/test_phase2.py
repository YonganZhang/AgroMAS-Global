import numpy as np
import pytest
import torch
import gymnasium as gym
from pcse_gym.envs.constraints import fertilization_action_constraint, AgronomicShield
from pcse_gym.agent.ppo_mod import RolloutBufferSteps
from pcse_gym.envs.observable import ObservableHistory, CausalGRUExtractor
from pcse_gym.utils.attribution import explain_decision
pytestmark=pytest.mark.cea2025

def costs(nue=.7,surplus=20,done=True,action=0,step=3,last=1,dvs=.5,mode='corrected'):
    return fertilization_action_constraint(np.array([action]),np.array([step]),np.array([0]),np.array([last]),np.array([dvs]),np.array([nue]),np.array([surplus]),np.array([done]),constraint_mode=mode)

@pytest.mark.parametrize('nue,surplus',[(.7,20),(.5,0),(.9,40),(.7,.25)])
def test_compliant(nue,surplus): assert sum(costs(nue,surplus))==0
@pytest.mark.parametrize('nue,surplus',[(0,20),(.49,20),(.91,20),(.7,-.01),(.7,40.01)])
def test_violating(nue,surplus): assert sum(costs(nue,surplus))>0

def test_raw_preserved(): assert costs(mode='raw')[-2][0]==1

def test_true_mask_per_environment():
    args=[np.array([0,0]),np.array([3,3]),np.array([0,0]),np.array([-5,-5]),np.array([.5,.5]),np.array([0.,0.]),np.array([99.,99.]),np.array([True,False])]
    c=fertilization_action_constraint(*args,constraint_mode='corrected')
    assert c[-2].tolist()==[1.,0.] and c[-1].tolist()==[1.,0.]

@pytest.mark.parametrize('gap,expected',[(1,3),(2,0)])
def test_spacing(gap,expected): assert costs(action=1,step=10,last=10-gap)[2][0]==expected
@pytest.mark.parametrize('dvs',[.01,1.])
def test_window_inclusive(dvs): assert costs(action=1,dvs=dvs)[1][0]==0

class Fake(gym.Env):
    action_space=gym.spaces.Discrete(9)
    observation_space=gym.spaces.Box(-np.inf,np.inf,(23,),dtype=np.float32)
    def reset(self,seed=None,options=None):
        self.obs=np.ones(23,dtype=np.float32);self.obs[0]=.5
        return self.obs.copy(),{}
    def step(self,a): return self.obs.copy(),0.,False,False,{}

def test_shield_all_constraints_and_budget():
    e=AgronomicShield(Fake(),n_budget=95);e.reset()
    assert e.step(8)[4]['executed_action']==8
    assert e.step(1)[4]['executed_action']==0
    assert e.step(8)[4]['executed_action']==1
    for _ in range(8): assert e.step(8)[4]['executed_action']==0
    assert e.executed_violations==0
    e.reset(); assert e.counter==e.n_counter==0
    for a in [-1,9,1.5,float('nan')]: assert e.step(a)[4]['executed_action']==0
    e.current_dvs=1.1;assert e.step(1)[4]['executed_action']==0

def test_frequency():
    e=AgronomicShield(Fake());e.reset()
    for _ in range(4):
        assert e.step(1)[4]['executed_action']==1
        e.step(0)
    assert e.step(1)[4]['shield_reason']==['application_frequency']

def test_history_reset_and_gradient():
    e=ObservableHistory(AgronomicShield(Fake()),history=4)
    o,_=e.reset(); e.step(1);o,*_=e.step(0)
    assert o[-1,5]>0
    o,_=e.reset();assert np.all(o[:-1]==0) and o[-1,5]==0
    f=CausalGRUExtractor(e.observation_space);z=f(torch.tensor(o[None]));z.sum().backward()
    assert f.gru.weight_ih_l0.grad.abs().sum()>0
    # No batch-neighbor hidden state dependence.
    one=f(torch.tensor(o[None]));both=f(torch.tensor(np.stack([o,o*2])))
    torch.testing.assert_close(one[0],both[0])

def test_buffer_true_done_and_async_reset():
    b=RolloutBufferSteps(4,gym.spaces.Box(-1,1,(2,),dtype=np.float32),gym.spaces.Discrete(9),n_envs=2,constraint_mode='corrected')
    t=torch.zeros(2);obs=np.zeros((2,2))
    b.add_nitrogen_info([.7,0],[20,0],[True,False]);b.add_dvs([.5,.5])
    b.add(obs,np.array([1,1]),np.zeros(2),np.array([True,True]),t,t,t)
    assert b.end_of_episode_mask[0].tolist()==[True,False]
    b.add_nitrogen_info([0,0],[0,0],[False,False]);b.add_dvs([.5,.5])
    b.add(obs,np.array([1,1]),np.zeros(2),np.array([True,False]),t,t,t)
    assert b.episodic_step[1].tolist()==[0,1]
    assert b.costs[1,0]==0 and b.costs[1,1]==3
    b.reset();assert b._running_count.tolist()==[1,2]
    with pytest.raises(ValueError): b.add_nitrogen_info([.7,.7],[20,20])

def test_read_only_attribution():
    def malicious(x): x['executed_action']=8;return 'text'
    r=explain_decision([1],[2],3,0,['minimum_spacing'],malicious)
    assert r['executed_action']==0 and r['proposed_action']==3

def test_corrected_torch_numpy_parity():
    args=[np.array([1,0]),np.array([2,3]),np.array([4,0]),np.array([1,-5]),np.array([.5,.5]),np.array([.7,0]),np.array([0,99]),np.array([True,False])]
    n=fertilization_action_constraint(*args,constraint_mode='corrected')
    t=fertilization_action_constraint(*[torch.as_tensor(x) for x in args],constraint_mode='corrected')
    for a,b in zip(n,t):np.testing.assert_allclose(a,b.numpy())


def test_buffer_rollout_boundary_and_executed_history():
    b=RolloutBufferSteps(1,gym.spaces.Box(-1,1,(2,),dtype=np.float32),gym.spaces.Discrete(9),n_envs=2,constraint_mode='corrected')
    t=torch.zeros(2);obs=np.zeros((2,2))
    b.add_nitrogen_info([0,0],[0,0],[False,False]);b.add_dvs([.5,.5]);b.executed_actions=np.array([0,1])
    b.add(obs,np.array([1,1]),np.zeros(2),np.array([True,True]),t,t,t)
    assert b._running_count.tolist()==[0,1]
    b.reset();b.add_nitrogen_info([0,0],[0,0],[False,False]);b.add_dvs([.5,.5]);b.executed_actions=np.array([0,1])
    b.tail_cost[0,1]=7
    b.add(obs,np.array([1,1]),np.zeros(2),np.array([False,False]),t,t,t)
    assert b.episodic_step[0].tolist()==[1,1] and b.costs[0,1]==10


def test_live_environment2_observable_contract():
    from pcse_gym.initialize_envs import initialize_env
    from pcse_gym.envs.observable import OBSERVABLE_CROP
    env=initialize_env(pcse_env=2,crop_features=list(OBSERVABLE_CROP),action_features=[],years=[3002],locations=[(52.57,5.63)],random_weather=True,random_init=False,reward='NUE',seed=4)
    wrapped=ObservableHistory(AgronomicShield(env),history=4)
    try:
        obs,_=wrapped.reset(seed=4)
        assert env.crop_features==['DVS','LAI'] and obs.shape==(4,10)
        obs,_,_,_,info=wrapped.step(8)
        assert info['executed_action']==0 and info['executed_violation_rate']==0
        assert np.isfinite(obs).all()
    finally:wrapped.close()

def test_training_only_tail_risk_and_terminal_weight():
    from pcse_gym.utils.tail_risk import episode_risk,tail_cost
    assert episode_risk(dict(surplus=20,yield_t_ha=9,N_loss=20))==0
    risk=episode_risk(dict(surplus=80,yield_t_ha=4,N_loss=80))
    assert risk==2.5
    c,q,selected=tail_cost(risk,[0,1,2,3],.25)
    assert q==2.25 and c==10 and selected
    assert tail_cost(1,[0,1,2,3],.25)[0]==0
    assert tail_cost(100,[],.25)==(0.,None,False)
    assert tail_cost(100,[0,1],None)==(0.,None,False)

def test_full_episode_cost_carries_rollout_boundary():
    b=RolloutBufferSteps(1,gym.spaces.Box(-1,1,(2,),dtype=np.float32),gym.spaces.Discrete(9),n_envs=1,constraint_mode='corrected')
    z=torch.zeros(1)
    def add(done,start):
        b.add_nitrogen_info([.7],[20],[done]);b.add_dvs([1.1])
        b.add(np.zeros((1,2)),np.array([1]),np.zeros(1),np.array([start]),z,z,z)
    add(False,True);assert b.get_costs_per_episode()==[[]]
    b.reset();add(True,False)
    assert b.get_costs_per_episode()==[[103.]] #50 + (50+3); terminal endpoints compliant


def test_execution_day_guard_and_accounting():
    from types import SimpleNamespace
    class EndWeek(Fake):
        def __init__(self):self.sb3_env=SimpleNamespace(model=SimpleNamespace())
        def step(self,a):
            amount=self.sb3_env.model._action_guard(a*10,1.05,'3002-06-01')
            self.sb3_env.model._guard_executed_action=amount
            assert amount==0 #decision was legal .5, actual application day is outside window
            return self.obs.copy(),0.,False,False,{}
    e=AgronomicShield(EndWeek());e.reset();info=e.step(8)[4]
    assert info['application_dvs']==1.05 and info['executed_action']==0 and info['executed_violation_rate']==0


def test_parameter_fairness_gate():
    from pcse_gym.agent.ppo_mod import CostActorCriticPolicy
    space=gym.spaces.Box(-np.inf,np.inf,(1,10),dtype=np.float32)
    a=CostActorCriticPolicy(space,gym.spaces.Discrete(9),lambda _: .001,net_arch=dict(pi=[32,32],vf=[32,32]))
    space2=gym.spaces.Box(-np.inf,np.inf,(4,10),dtype=np.float32)
    b=CostActorCriticPolicy(space2,gym.spaces.Discrete(9),lambda _: .001,net_arch=dict(pi=[32,32],vf=[32,32]),features_extractor_class=CausalGRUExtractor,features_extractor_kwargs={'features_dim':8})
    na=sum(p.numel() for p in a.parameters());nb=sum(p.numel() for p in b.parameters())
    assert abs(nb/na-1)<=.10

def test_live_shield_application_day_and_fertilizer_accounting():
    from pcse_gym.initialize_envs import initialize_env
    env=initialize_env(pcse_env=2,crop_features=['DVS','LAI'],action_features=[],years=[3002],locations=[(52.57,5.63)],random_weather=True,random_init=False,reward='NUE',seed=4)
    shield=AgronomicShield(env);shield.reset(seed=4);done=False;total=0;native_logged=0;dates=[]
    try:
        while not done:
            _,_,term,trunc,info=shield.step(8);done=term or trunc
            assert info['executed_violation_rate']==0
            native_logged+=sum(info['fertilizer'].values())
            if info['executed_action']>0:
                assert .01<=info['application_dvs']<=1
                total+=info['executed_action']*10;dates.append(info['application_date'])
        from datetime import date
        assert len(dates)<=4 and all((date.fromisoformat(b)-date.fromisoformat(a)).days>=14 for a,b in zip(dates,dates[1:]))
        assert total==shield.n_counter==native_logged==env.reward_container.get_total_fertilization*10
    finally:shield.close()

@pytest.mark.parametrize('shielded',[False,True])
def test_light_evaluation_info_preserves_native_trajectory(shielded):
    from pcse_gym.initialize_envs import initialize_env
    def trajectory(fast):
        base=initialize_env(pcse_env=2,crop_features=['DVS','LAI'],action_features=[],years=[3002],locations=[(52.57,5.63)],random_weather=True,random_init=False,reward='NUE',seed=4)
        base.sb3_env._phase2_fast_info=fast;e=AgronomicShield(base,enabled=shielded);obs,_=e.reset(seed=4);out=[];done=False
        try:
            while not done:
                obs,r,t,tr,i=e.step(8);done=t or tr
                out.append((np.asarray(obs).copy(),r,{k:i[k] for k in ['action','fertilizer','NUE','Nsurplus','profit','executed_action','shield_reason']}, {k:list(i[k].values())[-1] for k in ['DVS','WSO','NLOSSCUM','NamountSO']}))
            return out
        finally:e.close()
    a,b=trajectory(False),trajectory(True);assert len(a)==len(b)
    for (oa,ra,ia,ca),(ob,rb,ib,cb) in zip(a,b):
        np.testing.assert_array_equal(oa,ob);assert ra==rb and ia==ib and ca==cb

def test_real_engine_guard_rejects_application_day_sensor_crossing():
    from pcse_gym.initialize_envs import initialize_env
    base=initialize_env(pcse_env=2,crop_features=['DVS','LAI'],action_features=[],years=[3002],locations=[(52.57,5.63)],random_weather=True,random_init=False,reward='NUE',seed=4)
    shield=AgronomicShield(base);shield.reset(seed=4)
    model=base.sb3_env.model;original=model.get_variable
    # Inject an execution-time observable sensor crossing through the actual Engine._run path.
    model.get_variable=lambda name:1.05 if name=='DVS' else original(name)
    shield.current_dvs=.5
    try:
        _,_,_,_,info=shield.step(8)
        assert info['proposal_dvs']==.5 and info['application_dvs']==1.05
        assert info['executed_action']==0 and 'phenology_window' in info['shield_reason']
        assert sum(info['fertilizer'].values())==0 and base.reward_container.get_total_fertilization==0
    finally:shield.close()

def test_terminal_day_guard_blocks_legal_dvs():
    from types import SimpleNamespace
    class FinalDay(Fake):
        def __init__(self):self.sb3_env=SimpleNamespace(model=SimpleNamespace(flag_terminate=True))
        def step(self,a):
            n=self.sb3_env.model._action_guard(a*10,.5,'3002-08-15')
            assert n==0
            return self.obs.copy(),0.,True,False,{}
    env=AgronomicShield(FinalDay());env.reset();info=env.step(8)[4]
    assert 'season_ended' in info['shield_reason'] and info['executed_action']==0
