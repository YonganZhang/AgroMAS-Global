"""Observable-only paired-tree predictions and audited bilateral decision tiers."""
from dataclasses import dataclass
import numpy as np
from pcse_gym.agromas.continuation import project_members
GRID=np.array([0.,10.,20.,40.,60.,80.,100.])
CAPS=np.array([25.,35.,40.,50.])
MASKS={'LOAO-climate':(6,7,8,9),'LOAO-core-state':(0,1,2,4)}
FAMILIES=('Full','LOAO-climate','LOAO-surplus-filter','LOAO-soil-mining-guard','LOAO-core-state','LOAO-economics')

@dataclass(frozen=True)
class Policy:
    beta:float=200.
    penalty:float=200.
    family:str='Full'
    def __post_init__(self):
        if self.family not in FAMILIES or not np.isfinite([self.beta,self.penalty]).all() or min(self.beta,self.penalty)<0:raise ValueError('Invalidv6policy')

class PairedStageOutcome:
    """32 disjoint pairs of64 fitted trees; proxy, not calibrated posterior draws."""
    def __init__(self,model,model_id,terminal_fertilizer_known=True):
        if len(model.estimators_)!=64:raise ValueError('Exactly64treesrequired')
        self.model=model;self.model_id=model_id;self.terminal_fertilizer_known=terminal_fertilizer_known
    def __call__(self,x):
        x=np.asarray(x,float);masked=x.copy()
        mask=getattr(self.model,'agromas_feature_mask',())
        if mask:masked[:,list(mask)]=0.
        trees=np.stack([tree.predict(masked) for tree in self.model.estimators_],axis=1)
        if trees.shape!=(len(x),64,4) or not np.isfinite(trees).all():raise ValueError('Invalidpairedtreeoutput')
        raw=.5*(trees[:,::2]+trees[:,1::2])
        if getattr(self,"terminal_fertilizer_known",False):
            terminal=np.isclose(x[:,5],3.)
            raw[terminal,:,2]=(x[terminal,3]+x[terminal,-1])[:,None]
        members=project_members(raw,x)
        if not np.isfinite(members).all():raise ValueError('Invalidphysicalmembers')
        return members

def statistics(members):
    """... x action x member x6 -> ... x action x10; no terminal truth input."""
    m=np.asarray(members,float)
    if m.shape[-2:]!=(32,6) or not np.isfinite(m).all():raise ValueError('Invalidmembershape')
    means=m.mean(axis=-2)
    joint=np.stack([((m[...,3]>=.5)&(m[...,3]<=.9)&(m[...,2]>=0)&(m[...,2]<=cap)).mean(axis=-1) for cap in CAPS],axis=-1)
    return np.concatenate([means[..., [0,1,2,3,4]],np.quantile(m[...,2],.75,axis=-1,method='higher')[...,None],joint],axis=-1)

def decision_metrics(stats,legal,cap,price_multiplier,subsidy,policy):
    s=np.asarray(stats,float);legal=np.asarray(legal,bool)
    if s.shape[-2:]!=(7,10) or legal.shape!=s.shape[:-1] or not np.isfinite(s).all():raise ValueError('Invaliddecisiontable')
    if cap not in CAPS or not np.isfinite([price_multiplier,subsidy]).all() or price_multiplier<=0 or subsidy<0:raise ValueError('Invalidresearchcontext')
    mean_s=s[...,2];nue=s[...,3];q75=s[...,5]
    remove_cap=policy.family=='LOAO-surplus-filter';remove_mining=policy.family=='LOAO-soil-mining-guard'
    upper=np.ones_like(legal) if remove_cap else mean_s<=cap
    tier1=legal&upper&(nue>=.5)
    if not remove_cap:tier1&=q75<=cap
    if not remove_mining:tier1&=(nue<=.9)&(mean_s>=0)
    tier2=legal&upper
    has1=tier1.any(axis=-1);has2=tier2.any(axis=-1)
    allowed=np.where(has1[...,None],tier1,tier2)
    infeasible=~has2
    # Operational zero only when both predicted sets empty, never labelled compliant.
    allowed=np.where(infeasible[...,None],np.arange(7)==0,allowed)
    distance=np.maximum(.5-nue,0)
    if not remove_mining:distance+=np.maximum(nue-.9,0)
    if not remove_cap:distance+=np.maximum(mean_s-cap,0)/cap
    probability=s[...,6+int(np.flatnonzero(CAPS==cap)[0])]
    partial=200*s[...,0]-1.5*price_multiplier*s[...,4]+subsidy*probability
    score=partial+policy.beta*probability-policy.penalty*distance
    if policy.family=='LOAO-economics':score=s[...,0]  # Yield-only refit, no hidden economic weights.
    score=np.where(allowed,score,-np.inf)
    return dict(allowed=allowed,score=score,tier=np.where(has1,1,np.where(has2,2,3)),predicted_infeasible=infeasible,distance=distance,probability=probability)

def select_objective(stats,legal,cap,price_multiplier,subsidy,policy):
    d=decision_metrics(stats,legal,cap,price_multiplier,subsidy,policy)
    # Grid is strictly ascending: first exact maximum gives deterministic smaller dose.
    return np.argmax(d['score'],axis=-1),d

class AgroMASGlobalCoordinator:
    def __init__(self,policy):self.policy=policy
    def choose(self,stats,legal,cap=40.,price_multiplier=1.,subsidy=0.):
        chosen,diagnostic=select_objective(stats,legal,cap,price_multiplier,subsidy,self.policy)
        return chosen,diagnostic
