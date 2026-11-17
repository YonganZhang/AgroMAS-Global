"""V4 measurable-water history and train-only state-adaptive utility prior."""
import numpy as np
import torch as th
from pcse_gym.envs.moisture import MoistureHistory,MoisturePolicy,measured_water as legacy_water
from pcse_gym.envs.observable import ObservableHistory
from pcse_gym.envs.corridor import target,WINDOWS

def measured_water(env):
    model=env.unwrapped.sb3_env.model
    try:depth=float(model.parameterprovider['soil_profile'][0].Thickness)
    except (AttributeError,KeyError,IndexError,TypeError) as exc:raise ValueError('Top-layer depth metadata required') from exc
    if abs(depth-20.)>1e-6:raise ValueError('SM channel requires exactly20cm first soil layer')
    return legacy_water(env)

def utility_features(frame):
    # Physical units shared by NumPy calibration and torch policy. No terminal endpoints.
    stack=th.stack if isinstance(frame,th.Tensor) else np.stack
    return stack([frame[...,1]*10,frame[...,10],frame[...,10]**2,frame[...,4],frame[...,2],frame[...,3]],axis=-1) if not isinstance(frame,th.Tensor) else stack([frame[...,1]*10,frame[...,10],frame[...,10]**2,frame[...,4],frame[...,2],frame[...,3]],dim=-1)

class UtilityScorer(th.nn.Module):
    """Frozen buffers only; state queries are causal, residual actor remains differentiable."""
    def __init__(self,c):
        super().__init__();self.kind=c.get('model','ridge');self.depth=c.get('forest_depth',0)
        for key in ['mean','scale']+(['coefficients','intercepts'] if self.kind=='ridge' else ['forest_features','forest_thresholds','forest_left','forest_right','forest_values']):
            self.register_buffer(key,th.as_tensor(c[key],dtype=th.long if key in ['forest_features','forest_left','forest_right'] else th.float32))
    def forward(self,frame):
        z=th.clamp((utility_features(frame)-self.mean)/self.scale,-5,5)
        if self.kind=='ridge':return z@self.coefficients+self.intercepts
        batch=z.reshape(-1,z.shape[-1]);trees=self.forest_features.shape[0];idx=th.arange(trees,device=z.device)[None,:];nodes=th.zeros((len(batch),trees),dtype=th.long,device=z.device)
        for _ in range(self.depth):
            feature=self.forest_features[idx,nodes];threshold=self.forest_thresholds[idx,nodes]
            v=th.gather(batch,1,feature.clamp(min=0));child=th.where(v<=threshold,self.forest_left[idx,nodes],self.forest_right[idx,nodes]);nodes=th.where(feature<0,nodes,child)
        result=self.forest_values[idx,nodes].mean(1)
        return result.reshape(*z.shape[:-1],6)

def utility_scores(frame,calibration):
    if isinstance(frame,th.Tensor):return UtilityScorer(calibration).to(frame.device)(frame)
    # NumPy uses the same float32 arithmetic as deployment to avoid threshold drift.
    with th.no_grad():return UtilityScorer(calibration)(th.as_tensor(frame,dtype=th.float32)).numpy()

def adaptive_total(frame,calibration):
    scores=utility_scores(frame,calibration)
    return 160+10*(scores.argmax(dim=-1) if isinstance(scores,th.Tensor) else np.argmax(scores,axis=-1))

class Moisture4History(MoistureHistory):
    def frame(self,obs):
        f=np.concatenate([ObservableHistory.frame(self,obs),[measured_water(self.env)]]).astype(np.float32)
        cap=210.;self.env.n_budget=cap if self.budget else 0
        remaining=max(0,cap-self.cumulative);f[9]=remaining/400 if self.budget else -1
        if self.guided:remaining=max(0,min(remaining,float(target(f[0],self.cumulative,cap,self.stages))-self.cumulative))
        mask=self.env.get_action_mask(obs,dict(remaining_budget=remaining,days_since_last=self.since,fert_count=self.env.counter))
        if self.guided and WINDOWS[0]<=f[0]<WINDOWS[2]:
            needed=int(round(remaining/10));mask[1:]=[bool(mask[i] and i==needed) for i in range(1,9)]
        return np.concatenate([f,mask.astype(np.float32)])

class AdaptiveMoisturePolicy(MoisturePolicy):
    def __init__(self,*args,utility_calibration=None,prior_strength=.1,**kwargs):
        if utility_calibration is None:raise ValueError('Frozen train-only utility calibration required')
        self.utility_calibration=utility_calibration
        super().__init__(*args,prior_strength=prior_strength,**kwargs)
        self.utility_model=UtilityScorer(utility_calibration)
    def _get_constructor_parameters(self):
        d=super()._get_constructor_parameters();d['utility_calibration']=self.utility_calibration;return d
    def distribution(self,obs,latent):
        mask=obs[:,-1,11:]
        if not bool(th.all((mask==0)|(mask==1))) or not bool(th.all(mask[:,0]==1)):raise ValueError('Nine exact mask bits required')
        logits=self.action_net(latent)
        if self.prior_strength:
            f=obs[:,-1,:11];final=160+10*self.utility_model(f).argmax(dim=-1)
            prior=th.clamp(th.round((target(f[:,0],f[:,5]*400,final,self.stages)-f[:,5]*400)/10),0,8)
            logits=logits-self.prior_strength*(th.arange(9,device=obs.device)[None]-prior[:,None]).square()
        return self.action_dist.proba_distribution(action_logits=logits.masked_fill(~mask.bool(),-1e8))
