"""Deployed frozen CUO controller. Residual checkpoint.predict is deliberately not its API."""
import numpy as np
import torch
from pcse_gym.envs.corridor import target
class FrozenCUOController:
 def __init__(self,scorer,residual=None,alpha=0.):
  self.scorer=scorer;self.residual=residual;self.alpha=float(alpha)
  if not 0<=self.alpha<=1:raise ValueError('Frozen shrinkage must be0..1')
 def scores(self,history):
  h=torch.as_tensor(history,dtype=torch.float32)
  with torch.no_grad():
   utility=self.scorer(h[-1,:11])
   if self.residual is not None and self.alpha:
    features=self.residual.extract_features(h[None]);delta=self.residual.action_net(self.residual.mlp_extractor.forward_actor(features))[0,3:9];utility=utility+self.alpha*delta
  return utility
 def act(self,history):
  obs=np.asarray(history,np.float32)
  if obs.ndim!=2 or obs.shape[-1]!=20:raise ValueError('Physical11 + causal mask9 required')
  f=obs[-1,:11];mask=obs[-1,11:]
  if not np.all((mask==0)|(mask==1)) or mask[0]!=1:raise ValueError('Exact legal mask required')
  used=int(round(float(f[5])*400));final=160+10*int(self.scores(obs).argmax()) if .62<=f[0]<=.88 else 190
  desired=float(target(f[0],used,final,(70,130)));a=int(np.clip(np.round((desired-used)/10),0,8))
  return max(i for i in range(a+1) if mask[i])
 def predict(self,history,deterministic=True):
  if not deterministic:raise ValueError('Frozen controller is deterministic')
  obs=np.asarray(history)
  return (np.array([self.act(h) for h in obs]) if obs.ndim==3 else np.array(self.act(obs))),None
