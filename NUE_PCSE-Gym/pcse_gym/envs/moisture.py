"""Shared idealized measurable top0–20cm water observation. Never reads soil-N pools."""
import numpy as np
import torch as th
import gymnasium as gym
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from pcse_gym.agent.ppo_mod import CostActorCriticPolicy
from pcse_gym.envs.observable import ObservableHistory
from pcse_gym.envs.corridor import target,terminal_compliance,WINDOWS

def measured_water(env):
    """All three benchmark profiles have a20cm first layer; SM is m3/m3, not nitrogen."""
    value=np.asarray(env.unwrapped.sb3_env.model.get_variable('SM'),dtype=float).reshape(-1)
    if not len(value) or not np.isfinite(value[0]) or not 0<=value[0]<=1:raise ValueError('Invalid measurable SM channel')
    return float(value[0])

def water_cap(frame,calibration):
    if calibration is None:return 210.
    x=np.array([frame[1]*10,frame[10],frame[10]**2,frame[4]],dtype=float)
    z=(x-np.array(calibration['feature_mean']))/np.array(calibration['feature_scale'])
    estimate=calibration['intercept']+float(z@np.array(calibration['coefficients']))
    return float(np.clip(np.ceil((estimate+calibration['headroom']-1e-6)/10)*10,160,210))

class MoistureHistory(ObservableHistory):
    def __init__(self,env,history=4,guided=True,calibration=None,stages=(70.,130.),joint_bonus=8.,aligned=True,budget=True):
        super().__init__(env,history);self.guided=guided;self.calibration=calibration;self.stages=tuple(stages);self.joint_bonus=joint_bonus;self.aligned=aligned;self.budget=budget
        self.observation_space=gym.spaces.Box(-np.inf,np.inf,shape=(history,20),dtype=np.float32)
    def frame(self,obs):
        f=np.concatenate([ObservableHistory.frame(self,obs),[measured_water(self.env)]]).astype(np.float32)
        cap=water_cap(f,self.calibration) if self.guided else 210.;self.env.n_budget=cap if self.budget else 0
        remaining=max(0,cap-self.cumulative);f[9]=remaining/400 if self.budget else -1
        if self.guided:remaining=max(0,min(remaining,float(target(f[0],self.cumulative,cap,self.stages))-self.cumulative))
        mask=self.env.get_action_mask(obs,dict(remaining_budget=remaining,days_since_last=self.since,fert_count=self.env.counter))
        if self.guided and WINDOWS[0]<=f[0]<WINDOWS[2]:
            needed=int(round(remaining/10));mask[1:]=[bool(mask[i] and i==needed) for i in range(1,9)]
        return np.concatenate([f,mask.astype(np.float32)])
    def reset(self,**kwargs):
        self.masked_steps=self.interceptions=0;self.previous_wso=0.;obs,info=self.env.reset(**kwargs);self.cumulative=self.last=0.;self.since=365.;self.frames.clear()
        for _ in range(self.history-1):self.frames.append(np.array([0.]*11+[1.]+[0.]*8,dtype=np.float32))
        self.frames.append(self.frame(obs));return np.stack(self.frames),info
    def step(self,action):
        mask=self.frames[-1][11:];valid=int(mask.sum());self.masked_steps+=int(not mask.all())
        obs,r,t,tr,info=ObservableHistory.step(self,action);self.interceptions+=int(info['shield_triggered']);terminal=0.
        if self.aligned:
            native=info.get('reward',{}).copy();wso=float(list(info['WSO'].values())[-1]);r=(wso-self.previous_wso)/1000-.002*info['executed_action']*10;self.previous_wso=0. if t or tr else wso
            if t or tr:terminal=terminal_compliance(float(list(info['NUE'].values())[-1]),float(list(info['Nsurplus'].values())[-1]),self.joint_bonus);r+=terminal
            info.update(native_reward=native,reward={list(info['WSO'])[-1]:float(r)},phase3b_training_reward=float(r),terminal_compliance_reward=terminal)
        info.update(valid_mask_action_count=valid if self.env.enabled else 9,mask_active_rate=self.masked_steps/self.env.total_steps if self.env.enabled else 0.,execution_day_guard_interception_rate=self.interceptions/self.env.total_steps,measurable_top20cm_SM=float(obs[-1,10]))
        return obs,r,t,tr,info

class VisibleFrameExtractor(BaseFeaturesExtractor):
    def __init__(self,observation_space):super().__init__(observation_space,11)
    def forward(self,obs):return obs[:,-1,:11]

class StripWaterMask(gym.ObservationWrapper):
    def __init__(self,env):
        super().__init__(env);self.observation_space=gym.spaces.Box(-np.inf,np.inf,shape=(env.history,11),dtype=np.float32)
    def observation(self,obs):return obs[:,:11]

class MoisturePolicy(CostActorCriticPolicy):
    def __init__(self,*args,prior_final=190.,prior_strength=.3,stages=(70.,130.),**kwargs):
        self.prior_final=prior_final;self.prior_strength=prior_strength;self.stages=tuple(stages);super().__init__(*args,**kwargs)
        if self.observation_space.shape[-1]!=20:raise ValueError('Water history requires11observable fields+9mask bits')
    def _get_constructor_parameters(self):
        d=super()._get_constructor_parameters();d.update(prior_final=self.prior_final,prior_strength=self.prior_strength,stages=self.stages);return d
    def distribution(self,obs,latent):
        mask=obs[:,-1,11:]
        if not bool(th.all((mask==0)|(mask==1))) or not bool(th.all(mask[:,0]==1)):raise ValueError('Unnormalized binary mask required')
        logits=self.action_net(latent)
        if self.prior_strength:
            f=obs[:,-1,:11];prior=th.clamp(th.ceil((target(f[:,0],f[:,5]*400,self.prior_final,self.stages)-f[:,5]*400-1e-4)/10),0,8);logits=logits-self.prior_strength*(th.arange(9,device=obs.device)[None]-prior[:,None]).square()
        return self.action_dist.proba_distribution(action_logits=logits.masked_fill(~mask.bool(),-1e8))
    def get_distribution(self,obs):return self.distribution(obs,self.mlp_extractor.forward_actor(self.extract_features(obs)))
    def forward(self,obs,deterministic=False):
        pi,v,c=self.mlp_extractor(self.extract_features(obs));d=self.distribution(obs,pi);a=d.get_actions(deterministic=deterministic);return a,self.value_net(v),self.cost_value_net(c),d.log_prob(a)
    def evaluate_actions(self,obs,actions):
        pi,v,c=self.mlp_extractor(self.extract_features(obs));d=self.distribution(obs,pi);return self.value_net(v),self.cost_value_net(c),d.log_prob(actions),d.entropy()
