"""Backward stage3->2->1 physical teachers with outer-year-isolated validation.

The intervention book is offline TRAIN evidence only. Online models accept numeric
observables and candidate dose; they cannot access the book or future weather.
"""
from itertools import product
import numpy as np
from sklearn.ensemble import ExtraTreesRegressor
GRID=(0.,10.,20.,40.,60.,80.,100.)


def project_members(prediction,features,budget=220.):
    """Explicit conservative accounting projection; never adjusts yield upward.

    Predictions may undershoot committed N from regression/residual noise. The
    decision table assumes candidate execution; actual daily guards can still skip
    it. That execution uncertainty is measured separately, not hidden as efficacy.
    """
    p=np.maximum(np.array(prediction,dtype=float,copy=True),0.)
    x=np.asarray(features)
    lower=x[:,3]+x[:,-1]
    if np.any(lower>budget+1e-7):raise ValueError('Candidate exceeds available fertilizer budget')
    p[:,:,2]=np.clip(p[:,:,2],lower[:,None],budget)
    # Known scenario control, not an estimated random stock or future observation.
    p[:,:,3]=3.5
    p[:,:,1]=np.minimum(p[:,:,1],1000*p[:,:,0])  # N mass cannot exceed dry grain mass.
    y,grain,fert,nonfert=np.moveaxis(p,-1,0)
    return np.stack([y,grain,fert+nonfert-grain,grain/(fert+nonfert),fert,nonfert],-1)


def target(row):
    m=np.asarray(row['outcome'])
    return m[[0,1,4,5]]


def feature(row,stage,dose):
    return np.r_[row['features'][str(stage)],dose]


def predict_physical(model,x):
    x=np.array(x,dtype=float,copy=True)
    mask=getattr(model,'agromas_feature_mask',())
    if mask:x[:,list(mask)]=0.
    return model.predict(x)


def choose(model,row,stage,beta=200.,cap=40.,price_n=1.5,price_grain=.20,subsidy=0.,ecological=True,objective='profit'):
    if str(stage) not in row['features']:return 0.
    base=np.asarray(row['features'][str(stage)])
    doses=np.array([d for d in GRID if base[3]+d<=220+1e-8])
    x=np.array([np.r_[base,d] for d in doses])
    pred=predict_physical(model,x)[:,None,:]
    members=project_members(pred,x)[:,0]
    joint=(members[:,3]>=.5)&(members[:,3]<=.9)&(members[:,2]<=cap)
    if objective not in ('profit','yield'):raise ValueError('Unknown reference continuation objective')
    value=members[:,0] if objective=='yield' else 1000*price_grain*members[:,0]-price_n*members[:,4]+(subsidy+beta)*joint
    if ecological:
        safe=members[:,2]<=cap
        if not np.any(safe):return 0.
        value=np.where(safe,value,-np.inf)
    return float(doses[np.argmax(value)])


def dataset(books,stage,later,*,objective='profit',ecological=True,mask=()):
    x=[];y=[];years=[];keys=[]
    for key,book in books.items():
        name,year,climate=key
        prefixes=product(GRID,repeat=stage)
        for prefix in prefixes:
            plan=list(prefix)+[0.]*(3-stage)
            row=book[tuple(plan)]
            if str(stage) not in row['features']:continue
            if any((str(s) not in row['features'] and prefix[s-1]!=0) or
                   (str(s) in row['features'] and row['features'][str(s)][3]+prefix[s-1]>220+1e-8)
                   for s in range(1,stage)):continue
            base=np.asarray(row['features'][str(stage)])
            if base[3]+prefix[-1]>220+1e-8:continue
            # Select future actions using only the fitted later-stage models and
            # each resulting observable state, never ranking realized outcomes.
            for future in range(stage+1,4):
                plan[future-1]=choose(later[future],row,future,objective=objective,ecological=ecological)
                row=book[tuple(plan)]
            features=np.r_[base,prefix[-1]]
            if mask:features[list(mask)]=0.
            x.append(features);y.append(target(row));years.append(year)
            keys.append((name,year,climate,tuple(prefix)))
    return np.asarray(x),np.asarray(y),np.asarray(years),keys


def fit_pipeline(books,*,seed=4,n_estimators=64,min_samples_leaf=4,objective='profit',ecological=True,mask=()):
    fitted={}
    for stage in (3,2,1):
        x,y,years,_=dataset(books,stage,fitted,objective=objective,ecological=ecological,mask=mask)
        if len(set(years))<3:raise ValueError('At least3fit TRAIN years required')
        model=ExtraTreesRegressor(n_estimators=n_estimators,min_samples_leaf=min_samples_leaf,
                                   random_state=seed,n_jobs=1).fit(x,y)
        model.agromas_feature_mask=tuple(mask)
        fitted[stage]=model
    return fitted


class FrozenStageOutcome:
    """One frozen stage model plus joint outer-pipeline OOF residual members."""
    def __init__(self,model,residual,model_id,seed=4,ensemble_size=32):
        self.model=model;self.residual=np.asarray(residual)
        if self.residual.ndim!=2 or self.residual.shape[1]!=4 or not np.isfinite(self.residual).all():
            raise ValueError('Outer-pipeline physical residuals required')
        self.model_id=model_id;self.seed=seed;self.ensemble_size=ensemble_size

    def __call__(self,x):
        x=np.asarray(x,dtype=float)
        rng=np.random.default_rng(self.seed)
        ids=rng.integers(len(self.residual),size=self.ensemble_size)
        raw=predict_physical(self.model,x)[:,None,:]+self.residual[ids][None,:,:]
        return project_members(raw,x)
