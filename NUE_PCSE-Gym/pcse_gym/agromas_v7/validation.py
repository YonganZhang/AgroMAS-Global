"""Fold-local linear maps permit exact nested-Ridge refits for permutation batches."""
import numpy as np

def ridge_map(x,train,test,alpha):
    train=np.asarray(train,int);test=np.asarray(test,int)
    mean=x[train].mean(0);scale=x[train].std(0);scale[scale<1e-12]=1
    a=(x[train]-mean)/scale;b=(x[test]-mean)/scale
    # Targets are centered on this training fold, not globally.
    weights=np.linalg.solve(a@a.T+alpha*np.eye(len(train)),a@b.T).T
    weights-=weights.mean(axis=1,keepdims=True);weights+=1/len(train)
    return weights

def nested_maps(x,groups,alphas=(.1,1,10,100,1000)):
    x=np.asarray(x,float);groups=np.asarray(groups);all_ix=np.arange(len(x));out=[]
    assert np.isfinite(x).all() and len(np.unique(groups))>=3
    for outer in np.unique(groups):
        train=all_ix[groups!=outer];test=all_ix[groups==outer];inner=[]
        for inner_group in np.unique(groups[train]):
            fit=train[groups[train]!=inner_group];valid=train[groups[train]==inner_group]
            inner.append((fit,valid,[ridge_map(x,fit,valid,alpha) for alpha in alphas]))
        out.append(dict(train=train,test=test,inner=inner,outer=[ridge_map(x,train,test,alpha) for alpha in alphas]))
    return out

def predict_nested(maps,y):
    """y shape n x arbitrary independent target/permutation columns, select each separately."""
    y=np.asarray(y,float);one=y.ndim==1
    if one:y=y[:,None]
    pred=np.empty_like(y);chosen=[]
    for fold in maps:
        errors=np.zeros((len(fold['outer']),y.shape[1]))
        for train,valid,weights in fold['inner']:
            for a,w in enumerate(weights):errors[a]+=((w@y[train]-y[valid])**2).mean(axis=0)/len(fold['inner'])
        best=errors.argmin(axis=0);columns=np.arange(y.shape[1])
        forecasts=np.stack([w@y[fold['train']] for w in fold['outer']]);pred[fold['test']]=forecasts[best,:,columns].T;chosen.append(best)
    return (pred[:,0] if one else pred),chosen

def r2(y,p):
    y=np.asarray(y,float);p=np.asarray(p,float);den=((y-y.mean(axis=0))**2).sum(axis=0)
    return np.where(den>1e-14,1-((y-p)**2).sum(axis=0)/np.maximum(den,1e-14),np.nan)

def permutations(regions,years,draws,seed,mode):
    regions=np.asarray(regions);years=np.asarray(years);rng=np.random.default_rng(seed);out=np.tile(np.arange(len(regions))[:,None],(1,draws));unique_regions=np.unique(regions)
    for j in range(draws):
        if mode=='within_region':
            for region in unique_regions:
                ix=np.flatnonzero(regions==region);out[ix,j]=rng.permutation(ix)
        elif mode=='region_blocks':
            donor=rng.permutation(unique_regions)
            for region,source in zip(unique_regions,donor):
                for ix in np.flatnonzero(regions==region):
                    src=np.flatnonzero((regions==source)&(years==years[ix]));assert len(src)==1,'Block null requires balanced years';out[ix,j]=src[0]
        else:raise ValueError(mode)
    return out
