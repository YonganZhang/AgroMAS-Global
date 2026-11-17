"""Matched sensorless91D structured PPO, TRAIN physical-book rewards only."""
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from .planning import GRID
CAPS=np.array([25.,35.,40.,50.]);FACTORS=np.array([49,7,1])

def stats_from_members(members,radius):
 from .planning import upper_cvar
 m=np.asarray(members,float);means=m.mean(1);s=m[...,2];n=m[...,3]
 q90=np.quantile(s,.9,axis=1,method='higher');q95=np.quantile(s,.95,axis=1,method='higher')+radius
 cv=np.array([upper_cvar(v,np.full(32,1/32),.1) for v in s])+max(radius,0.)
 joint=np.stack([((s>=0)&(s<=c)&(n>=.5)&(n<=.9)).mean(1) for c in CAPS],axis=1)
 return np.c_[means[:,:5],q90,q95,cv,joint]

def mask_from_stats(stats,legal,cap,applicable):
 legal=np.asarray(legal,bool)
 if not applicable:return np.arange(7)==0,3
 s=np.asarray(stats);first=legal&(s[:,2]>=0)&(np.maximum(s[:,5],s[:,6])<=cap)&(s[:,7]<=cap)&(s[:,3]>=.5)&(s[:,3]<=.9)
 second=legal&(s[:,2]<=cap)
 if first.any():return first,1
 if second.any():return second,2
 return np.arange(7)==0,3

def encode(base,stats,legal,cap,price,subsidy,applicable):
 b=np.array(base,float,copy=True);b[[1,2,4]]=0;b[10:15]=0;mask,tier=mask_from_stats(stats,legal,cap,applicable);s=np.asarray(stats);joint=s[:,8+int(np.flatnonzero(CAPS==cap)[0])];profit=200*s[:,0]-1.5*price*s[:,4]+subsidy*joint
 action=np.c_[GRID/100,s[:,0]/12,s[:,1]/200,s[:,6]/200,s[:,3]/2,s[:,4]/220,profit/3000,joint]
 obs=np.r_[b,[cap/50,1.5*price/3,1.,subsidy/200,.2,.25],action.ravel(),mask].astype(np.float32)
 if obs.shape!=(91,) or not np.isfinite(obs).all():raise ValueError('Sensorless91D observation contract')
 return obs,mask,tier

class TrainSensorlessBookEnv(gym.Env):
 def __init__(self,data,tables):
  if any(not 1995<=k[1]<=2009 for k in data.keys):raise ValueError('TRAIN-only reward environment')
  self.data=data;self.tables=tables;self.observation_space=spaces.Box(-np.inf,np.inf,(91,),np.float32);self.action_space=spaces.Discrete(7)
 def reset(self,*,seed=None,options=None):
  super().reset(seed=seed);self.world=int(self.np_random.integers(len(self.data.keys)));self.index=0;self.stage=1;self.cap=float(self.np_random.choice(CAPS));self.price=float(self.np_random.choice([1.,2.]));self.subsidy=float(self.np_random.choice([0.,50.,100.,150.,200.]));self.actions=[];self._skip();return self._observe(),{}
 def _skip(self):
  while self.stage<=3 and not self.data.available[self.world,self.stage-1,self.index]:self.stage+=1
 def _observe(self):
  if self.stage>3:self.mask=np.arange(7)==0;return np.zeros(91,np.float32)
  key=(self.world,self.stage,self.index//(7**(4-self.stage)));row=self.tables[key];obs,self.mask,self.tier=encode(row['base'],row['stats'],row['legal'],self.cap,self.price,self.subsidy,row['applicable']);return obs
 def action_masks(self):return self.mask.copy()
 def step(self,action):
  a=int(action)
  if not self.mask[a]:raise ValueError('Masked action')
  self.index+=a*FACTORS[self.stage-1];self.actions.append((self.stage,a));self.stage+=1;self._skip();ended=self.stage>3;reward=0.;info={}
  if ended:
   m=self.data.outcomes[self.world,self.index];joint=bool(.5<=m[3]<=.9 and 0<=m[2]<=self.cap);partial=200*m[0]-1.5*self.price*m[4]+self.subsidy*joint;distance=max(.5-m[3],0)+max(m[3]-.9,0)+max(m[2]-self.cap,0)/self.cap+max(-m[2],0)/self.cap
   reward=float(partial+200*joint-200*distance);info={'joint':joint,'partial_profit':float(partial),'actions':self.actions,'region':self.data.keys[self.world][0],'year':self.data.keys[self.world][1],'plan_index':int(self.index),'cap':self.cap,'price':self.price,'subsidy':self.subsidy}
  return self._observe(),reward,ended,False,info
