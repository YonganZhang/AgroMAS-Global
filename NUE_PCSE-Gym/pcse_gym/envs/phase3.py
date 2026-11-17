"""Observable, causal Phase 3 controls. No simulator soil pools or forecast inputs."""
import numpy as np
import torch as th
from pcse_gym.agent.ppo_mod import CostActorCriticPolicy
from pcse_gym.envs.observable import ObservableHistory
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

class LastObservableExtractor(BaseFeaturesExtractor):
    def __init__(self,observation_space):
        super().__init__(observation_space,10)
    def forward(self,obs):
        return obs[:,-1,:10]



def envelope(frame, version=1):
    """Observable vigor/rain adjustment around 170 kg/ha; bounded at all inputs."""
    f=np.asarray(frame)
    if version==2:
        return float(np.clip(185+5*np.tanh((f[1]*10-3)/2)+5*np.tanh((f[4]-.03)/.03),130,195))
    return float(np.clip(170+10*np.tanh((f[1]*10-3)/2)+10*np.tanh(f[4]-.5),130,195))


def stage_remaining(dvs, used, cap):
    target=50 if .10<=dvs<=.28 else 110 if .32<=dvs<=.58 else cap if .62<=dvs<=.88 else used
    return max(0.,min(cap-used,target-used))


def prior_action(frame):
    dvs,used=float(frame[0]),float(frame[5])*400
    target=50 if .10<=dvs<.32 else 110 if .32<=dvs<.62 else 160 if .62<=dvs<=.88 else used
    return int(np.clip(np.ceil((target-used-1e-4)/10),0,6))


class Phase3History(ObservableHistory):
    """Append exact decision mask to each frame, preserving it through minibatch shuffle."""
    def __init__(self,env,history=1,aligned=False,guided=False,envelope_version=1):
        super().__init__(env,history)
        import gymnasium as gym
        self.observation_space=gym.spaces.Box(-np.inf,np.inf,shape=(history,19),dtype=np.float32)
        self.aligned,self.guided=aligned,guided
        self.envelope_version=envelope_version
        self.masked_steps=self.interceptions=0
    def frame(self,obs):
        f=super().frame(obs)
        cap=envelope(f,self.envelope_version) if self.guided else 195.
        self.env.n_budget=cap
        f[9]=max(0,cap-self.cumulative)/400
        remaining=max(0,cap-self.cumulative)
        if self.envelope_version==2:remaining=stage_remaining(float(f[0]),self.cumulative,cap)
        mask=self.env.get_action_mask(obs,dict(remaining_budget=remaining,days_since_last=self.since,fert_count=self.env.counter))
        return np.concatenate([f,mask.astype(np.float32)])
    def reset(self,**kw):
        # Parent padding uses ten fields, so build padding after its reset.
        self.masked_steps=self.interceptions=0
        self.previous_wso=0.
        obs,info=self.env.reset(**kw)
        self.cumulative=self.last=0.;self.since=365.;self.frames.clear()
        first=self.frame(obs)
        for _ in range(self.history-1):self.frames.append(np.concatenate([np.zeros(10),[1],np.zeros(8)]).astype(np.float32))
        self.frames.append(first)
        return np.stack(self.frames),info
    def step(self,action):
        current_valid=int(self.frames[-1][10:].sum())
        self.masked_steps+=int(not self.frames[-1][10:].all())
        obs,reward,term,trunc,info=super().step(action)
        self.interceptions+=int(info['shield_triggered'])
        if self.aligned:
            # Dense yield increments telescope; application costs are per kg.
            wso=info.get('WSO',{})
            current=float(list(wso.values())[-1]) if wso else 0.
            reward=(current-getattr(self,'previous_wso',0.))/1000-.002*info['executed_action']*10
            self.previous_wso=0. if term or trunc else current
            # Keep native diagnostic reward explicitly labelled; PPO receives returned reward.
            info['phase3_training_reward']=float(reward)
            info['native_reward']=info.get('reward',{}).copy()
            info['reward']={list(wso)[-1]:float(reward)} if wso else {}
        info.update(mask_active_rate=self.masked_steps/self.env.total_steps,execution_day_guard_interception_rate=self.interceptions/self.env.total_steps,valid_mask_action_count=current_valid)
        return obs,reward,term,trunc,info


class MaskedCostPolicy(CostActorCriticPolicy):
    """Same distribution for collection, shuffled updates and SB3 prediction."""
    def __init__(self,*args,prior_strength=0.,prior_final=160.,**kwargs):
        self.prior_strength=prior_strength
        self.prior_final=prior_final
        super().__init__(*args,**kwargs)
        if len(self.observation_space.shape)!=2 or self.observation_space.shape[-1]!=19:
            raise ValueError("Masked policy requires unnormalized history x19 layout")
    def _get_constructor_parameters(self):
        data=super()._get_constructor_parameters();data['prior_strength']=self.prior_strength;data['prior_final']=self.prior_final;return data
    def distribution(self,obs,latent):
        mask=obs[:,-1,10:]
        if not bool(th.all((mask==0)|(mask==1))) or not bool(th.all(mask[:,0]==1)):
            raise ValueError("Mask must be exact binary with zero-dose always allowed; disable observation normalization")
        logits=self.action_net(latent)
        if self.prior_strength:
            f=obs[:,-1,:10]
            dvs,used=f[:,0],f[:,5]*400
            target=th.where((dvs>=.10)&(dvs<.32),50.,th.where((dvs>=.32)&(dvs<.62),110.,th.where((dvs>=.62)&(dvs<=.88),self.prior_final,used)))
            prior=th.clamp(th.ceil((target-used-1e-4)/10),0,6)
            logits=logits-self.prior_strength*(th.arange(9,device=obs.device)[None]-prior[:,None]).square()
        logits=logits.masked_fill(~obs[:,-1,10:].bool(),-1e8)
        return self.action_dist.proba_distribution(action_logits=logits)
    def get_distribution(self,obs):
        features=self.extract_features(obs)
        return self.distribution(obs,self.mlp_extractor.forward_actor(features))
    def forward(self,obs,deterministic=False):
        pi,vf,cf=self.mlp_extractor(self.extract_features(obs))
        dist=self.distribution(obs,pi);a=dist.get_actions(deterministic=deterministic)
        return a,self.value_net(vf),self.cost_value_net(cf),dist.log_prob(a)
    def evaluate_actions(self,obs,actions):
        pi,vf,cf=self.mlp_extractor(self.extract_features(obs));dist=self.distribution(obs,pi)
        return self.value_net(vf),self.cost_value_net(cf),dist.log_prob(actions),dist.entropy()
