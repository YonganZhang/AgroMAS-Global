"""Vectorized backward physical-label teachers, fitted only inside year folds."""
import hashlib
import numpy as np
from sklearn.ensemble import ExtraTreesRegressor
from .books import PLANS,FACTORS
from .core import GRID,MASKS,Policy,PairedStageOutcome,statistics,select_objective

def predict_stats(model,x,legal):
    shape=x.shape[:-1];flat=x.reshape(-1,x.shape[-1]);ok=legal.reshape(-1)
    members=np.zeros((len(flat),32,6));fert=flat[:,3]+flat[:,-1]
    members[:,:,4]=fert[:,None];members[:,:,5]=3.5;members[:,:,2]=fert[:,None]+3.5
    if np.any(ok):members[ok]=model(flat[ok])
    return statistics(members).reshape(*shape,10)

def stage3_cache(data,model):
    w=np.repeat(np.arange(len(data.keys)),343);ix=np.tile(np.arange(343),len(data.keys));base=data.features[w,2,ix]
    x=np.c_[base,PLANS[ix,2]];legal=data.available[w,2,ix]&(base[:,3]+x[:,-1]<=220+1e-8)
    return predict_stats(model,x,legal).reshape(len(data.keys),343,10)

def table(data,w,ix,stage,model,cache3=None):
    x,legal=data.candidate_inputs(w,ix,stage)
    if stage==3 and cache3 is not None:
        indices=ix[:,None]+np.arange(7)[None,:]
        stats=cache3[w[:,None],indices]
    else:stats=predict_stats(model,x,legal)
    return stats,legal

def advance(data,w,ix,stage,model,policy,cache3=None,cap=40.,price=1.,subsidy=0.):
    stats,legal=table(data,w,ix,stage,model,cache3)
    choice,diagnostic=select_objective(stats,legal,cap,price,subsidy,policy)
    # Labels are looked up only after the observable-only decision has been fixed.
    return ix+choice*FACTORS[stage-1],diagnostic

def fit_stage(data,worlds,stage,later,policy,cache3=None):
    w,ix=data.cases(worlds,stage);x=np.c_[data.features[w,stage-1,ix],PLANS[ix,stage-1]]
    indices=ix.copy()
    for future in range(stage+1,4):indices,_=advance(data,w,indices,future,later[future],policy,cache3)
    y=data.outcomes[w,indices][:,[0,1,4,5]]
    masked=x.copy();mask=MASKS.get(policy.family,())
    if mask:masked[:,list(mask)]=0.
    if len({data.keys[k][1] for k in worlds})<3:raise ValueError('Atleast3fitTRAINyearsrequired')
    forest=ExtraTreesRegressor(n_estimators=64,min_samples_leaf=4,random_state=4,n_jobs=1).fit(masked,y)
    forest.agromas_feature_mask=mask
    model_id=hashlib.sha256(str((stage,policy,tuple(data.keys[k] for k in worlds))).encode()+y.tobytes()).hexdigest()
    return PairedStageOutcome(forest,model_id)

def fit_pipeline(data,worlds,policy,stage3=None,cache3=None):
    fitted={3:stage3} if stage3 is not None else {}
    if stage3 is None:fitted[3]=fit_stage(data,worlds,3,{},policy)
    if cache3 is None:cache3=stage3_cache(data,fitted[3])
    for stage in (2,1):fitted[stage]=fit_stage(data,worlds,stage,fitted,policy,cache3)
    return fitted,cache3

def replay(data,worlds,models,policy,cache3=None,cap=40.,price=1.,subsidy=0.):
    w=np.asarray(worlds);ix=np.zeros(len(w),int);tiers=[]
    for stage in (1,2,3):
        ix,diagnostic=advance(data,w,ix,stage,models[stage],policy,cache3,cap,price,subsidy);tiers.append(diagnostic['tier'])
    outcomes=data.outcomes[w,ix];joint=(outcomes[:,3]>=.5)&(outcomes[:,3]<=.9)&(outcomes[:,2]>=0)&(outcomes[:,2]<=cap)
    return [dict(region_id=data.keys[k][0],year=data.keys[k][1],climate=data.keys[k][2],outcome=m.tolist(),plan=PLANS[i].tolist(),joint=bool(j),partial_profit=float(200*m[0]-1.5*price*m[4]+subsidy*j),tiers=[int(t[v]) for t in tiers]) for v,(k,i,m,j) in enumerate(zip(w,ix,outcomes,joint))]
