"""TRAIN-only three-decision PPO environment backed by frozen physical labels.

Policy sees current observables and frozen model statistics, never book labels.
This is decision-step training, explicitly not native weekly simulator training.
"""
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from .core import GRID,CAPS,decision_metrics
from .books import FACTORS,PLANS
from .training import table

def build_tables(data,models):
    tables={};legal={}
    for stage in (1,2,3):
        bases=np.arange(0,343,7**(4-stage));w=np.repeat(np.arange(len(data.keys)),len(bases));ix=np.tile(bases,len(data.keys))
        stats,ok=table(data,w,ix,stage,models[stage]);tables[stage]=stats.reshape(len(data.keys),len(bases),7,10);legal[stage]=ok.reshape(len(data.keys),len(bases),7)
    return tables,legal

def state_table(data,tables,legal,world,index,stage):
    prefix=index//(7**(4-stage))
    return tables[stage][world,prefix],legal[stage][world,prefix],data.features[world,stage-1,index]

def encode(base,stats,legal,cap,price,subsidy,policy):
    diag=decision_metrics(stats[None],legal[None],cap,price,subsidy,policy);mask=diag['allowed'][0]
    joint=stats[:,6+int(np.flatnonzero(CAPS==cap)[0])];profit=200*stats[:,0]-1.5*price*stats[:,4]+subsidy*joint
    action=np.c_[GRID/100,stats[:,0]/12,stats[:,1]/200,stats[:,5]/200,stats[:,3]/2,stats[:,4]/220,profit/3000,joint]
    obs=np.r_[base,[cap/50,1.5*price/3,1.,subsidy/200,policy.beta/1000,policy.penalty/800],action.ravel(),mask].astype(np.float32)
    if obs.shape!=(91,) or not np.isfinite(obs).all():raise ValueError('Invalid91dimobservable')
    return obs,mask,diag

class TrainBookEnv(gym.Env):
    def __init__(self,data,tables,legal,policy):
        if any(not 1995<=k[1]<=2009 for k in data.keys):raise ValueError('TRAINonlyPPOenvironment')
        self.data=data;self.tables=tables;self.legal=legal;self.policy=policy
        self.observation_space=spaces.Box(-np.inf,np.inf,(91,),np.float32);self.action_space=spaces.Discrete(7)
    def reset(self,*,seed=None,options=None):
        super().reset(seed=seed);self.world=int(self.np_random.integers(len(self.data.keys)));self.index=0;self.stage=1
        self.cap=float(self.np_random.choice(CAPS));self.price=float(self.np_random.choice([1.,2.]));self.subsidy=float(self.np_random.choice([0.,50.,100.,150.,200.]))
        self.actions=[];self._skip();return self._observe(),{}
    def _skip(self):
        while self.stage<=3 and not self.data.available[self.world,self.stage-1,self.index]:self.stage+=1
    def _observe(self):
        if self.stage>3:self.mask=np.array([1,0,0,0,0,0,0],bool);return np.zeros(91,np.float32)
        s,l,b=state_table(self.data,self.tables,self.legal,self.world,self.index,self.stage)
        obs,self.mask,self.diag=encode(b,s,l,self.cap,self.price,self.subsidy,self.policy);return obs
    def action_masks(self):return self.mask.copy()
    def step(self,action):
        a=int(action)
        if not self.mask[a]:raise ValueError('MaskedPPOaction')
        if self.stage<=3:self.index+=a*FACTORS[self.stage-1];self.actions.append((self.stage,a));self.stage+=1;self._skip()
        ended=self.stage>3;reward=0.;info={}
        if ended:
            m=self.data.outcomes[self.world,self.index];joint=bool(.5<=m[3]<=.9 and 0<=m[2]<=self.cap)
            partial=200*m[0]-1.5*self.price*m[4]+self.subsidy*joint
            distance=max(0,m[3]-.9)+max(0,.5-m[3])+max(0,m[2]-self.cap)/self.cap
            reward=float(partial+self.policy.beta*joint-self.policy.penalty*distance)
            info=dict(joint=joint,partial_profit=float(partial),plan=PLANS[self.index].tolist(),actions=self.actions,region_id=self.data.keys[self.world][0],year=self.data.keys[self.world][1])
        return self._observe(),reward,ended,False,info
