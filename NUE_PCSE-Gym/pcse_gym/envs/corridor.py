"""Version3 causal corridor. Calibration labels are train-only terminal outcomes."""
import numpy as np
import torch as th
from pcse_gym.envs.phase3 import Phase3History,MaskedCostPolicy
from pcse_gym.envs.observable import ObservableHistory

WINDOWS=(.10,.32,.62,.88)

def target(dvs,used,final=190.,stages=(70.,130.)):
    if not isinstance(dvs,th.Tensor):dvs=np.asarray(dvs,dtype=np.float32)
    where=th.where if isinstance(dvs,th.Tensor) else np.where
    a,b,c,d=WINDOWS
    return where((dvs>=a)&(dvs<b),stages[0],where((dvs>=b)&(dvs<c),stages[1],where((dvs>=c)&(dvs<=d),final,used)))

def terminal_compliance(nue,surplus,joint_bonus=2.):
    """Terminal feedback only; no endpoint is appended to an actor observation."""
    joint=.5<=nue<=.9 and 0<=surplus<=40
    penalty=max(0,nue-.88)/.1+max(0,.52-nue)/.1+max(0,surplus-36)/20+max(0,-surplus)/20
    return float(joint_bonus*joint-penalty)

def cap(frame,calibration=None):
    if calibration is None:return 210.
    lai=float(frame[1])*10
    prediction=calibration['intercept']+calibration['LAI_coefficient']*lai
    return float(np.clip(np.ceil((prediction+calibration['headroom']-1e-6)/10)*10,160,210))

class CorridorHistory(Phase3History):
    def __init__(self,env,history=4,guided=True,calibration=None,stages=(70.,130.),joint_bonus=2.,stage_exact=True):
        self.calibration=calibration;self.stages=tuple(stages);self.joint_bonus=joint_bonus;self.stage_exact=stage_exact
        super().__init__(env,history=history,aligned=True,guided=guided,envelope_version=3)
    def frame(self,obs):
        f=ObservableHistory.frame(self,obs)
        budget=cap(f,self.calibration) if self.guided else 210.
        self.env.n_budget=budget;remaining=max(0,budget-self.cumulative);f[9]=remaining/400
        if self.guided:
            desired=float(target(float(f[0]),self.cumulative,budget,self.stages))
            remaining=max(0,min(remaining,desired-self.cumulative))
        mask=self.env.get_action_mask(obs,dict(remaining_budget=remaining,days_since_last=self.since,fert_count=self.env.counter))
        # Fixed early splits focus learned dose adaptation on the final demand window.
        if self.guided and self.stage_exact and WINDOWS[0]<=f[0]<WINDOWS[2]:
            needed=int(round(remaining/10))
            mask[1:]=[bool(mask[i] and i==needed) for i in range(1,9)]
        return np.concatenate([f,mask.astype(np.float32)])
    def step(self,action):
        obs,r,t,tr,info=super().step(action)
        terminal=0.
        if t or tr:
            nue=float(list(info['NUE'].values())[-1]);surplus=float(list(info['Nsurplus'].values())[-1])
            terminal=terminal_compliance(nue,surplus,self.joint_bonus);r+=terminal
            info['reward']={list(info['WSO'])[-1]:float(r)}
        info.update(terminal_compliance_reward=terminal,phase3b_training_reward=float(r))
        return obs,r,t,tr,info

class CorridorPolicy(MaskedCostPolicy):
    def __init__(self,*args,prior_final=190.,prior_strength=.3,stages=(70.,130.),**kw):
        self.stages=tuple(stages)
        super().__init__(*args,prior_final=prior_final,prior_strength=prior_strength,**kw)
    def _get_constructor_parameters(self):
        d=super()._get_constructor_parameters();d['stages']=self.stages;return d
    def distribution(self,obs,latent):
        mask=obs[:,-1,10:]
        if not bool(th.all((mask==0)|(mask==1))) or not bool(th.all(mask[:,0]==1)):raise ValueError('Exact unnormalized mask required')
        logits=self.action_net(latent)
        if self.prior_strength:
            f=obs[:,-1,:10];prior=th.clamp(th.ceil((target(f[:,0],f[:,5]*400,self.prior_final,self.stages)-f[:,5]*400-1e-4)/10),0,8)
            logits=logits-self.prior_strength*(th.arange(9,device=obs.device)[None]-prior[:,None]).square()
        return self.action_dist.proba_distribution(action_logits=logits.masked_fill(~mask.bool(),-1e8))
