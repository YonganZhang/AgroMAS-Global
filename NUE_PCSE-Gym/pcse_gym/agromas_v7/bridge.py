"""Explicit observable boundary for retrospective OOF hidden-state imputation."""
import numpy as np
OBSERVED=(0,3,5,6,7,8,9,15,16,17,18)
HIDDEN=(1,2,4,19,20,21)

def features(base,regime,static_prior,satellite=None):
    base=np.asarray(base,float);prior=np.asarray(static_prior,float)
    if base.shape!=(22,) or prior.shape!=(4,):raise ValueError('Invalid bridge inputs')
    v=base[list(OBSERVED)]
    if regime=='Weather_only':return v
    if regime not in ('Static_soil','Satellite_bridge'):raise ValueError(regime)
    v=np.r_[v,prior]
    if regime=='Satellite_bridge':
        missing=satellite is None;z=np.zeros(64) if missing else np.asarray(satellite,float)
        if z.shape!=(64,):raise ValueError('All64 satellite axes required')
        v=np.r_[v,z,float(missing)]
    return v

def reconstruct(base,hidden):
    v=np.asarray(base,float).copy();h=np.asarray(hidden,float)
    if v.shape!=(22,) or h.shape!=(6,) or not np.isfinite(h).all():raise ValueError('Invalid hidden prediction')
    v[10:15]=0 # remove privileged region-identity lookup from every restricted regime
    v[list(HIDDEN)]=h
    v[1]=np.clip(v[1],0,12);v[2]=np.clip(v[2],0,1);v[4]=np.clip(v[4],0,600)
    v[19:21]=np.clip(v[19:21],0,1);v[21]=np.clip(v[21],1e-8,1000)
    return v

def prior_year(aef,region,year):
    key=(region,int(year)-1)
    if year<2018:return None
    if key not in aef:raise ValueError('Missing prior-year product; never substitute current or future year')
    return np.asarray(aef[key],float)
