"""Causal TRAIN-only direct forecasts with rolling-origin joint residual blocks.

`realistic_noisy` is a statistical forecast, not an operational NWP archive.
Weather columns: Tmin C, Tmax C, radiation MJ/m2/day, rain mm/day, RH %, wind m/s.
"""
from dataclasses import dataclass
from datetime import timedelta
import hashlib
import numpy as np
from .contracts import finite_array


@dataclass(frozen=True)
class WeatherHistory:
    dates: tuple
    values: np.ndarray
    region_id: str
    source_id: str

    def __post_init__(self):
        a=finite_array(self.values,(len(self.dates),6))
        if not self.dates or not self.region_id or not self.source_id:
            raise ValueError('Weather provenance required')
        if any(b-a!=timedelta(days=1) for a,b in zip(self.dates,self.dates[1:])):
            raise ValueError('Daily weather must be consecutive')
        if np.any(a[:,0]>a[:,1]) or np.any(a[:,2:]<0) or np.any(a[:,4]>100):
            raise ValueError('Invalid physical weather')
        object.__setattr__(self,'values',a)

    def through(self, as_of):
        n=sum(d<=as_of for d in self.dates)
        if not n:
            raise ValueError('No causal history')
        return WeatherHistory(self.dates[:n],self.values[:n],self.region_id,self.source_id)

    def observed(self, day, as_of):
        if day>as_of:
            raise ValueError('Future truth access denied')
        return self.values[self.dates.index(day)].copy()


@dataclass(frozen=True)
class Forecast:
    issued_at: object
    valid_dates: tuple
    members: np.ndarray
    region_id: str
    source_vintage: str
    mode: str
    vector: np.ndarray


def _features(day, seven_days):
    angle=2*np.pi*day.timetuple().tm_yday/365.25
    return np.r_[1.,np.sin(angle),np.cos(angle),np.sin(2*angle),np.cos(2*angle),
                 seven_days[-1]/[30,30,25,10,100,5],seven_days.mean(0)/[30,30,25,10,100,5]]


def _solve(x,y,ridge):
    penalty=np.eye(x.shape[1])*ridge
    penalty[0,0]=0
    return np.linalg.solve(x.T@x+penalty,x.T@y)


def _physical(a):
    a=np.array(a,copy=True)
    lo=np.minimum(a[...,0],a[...,1]);hi=np.maximum(a[...,0],a[...,1])
    a[...,0]=lo;a[...,1]=hi
    a[...,2:]=np.maximum(a[...,2:],0)
    a[...,4]=np.clip(a[...,4],0,100)
    return a


class ClimateForecastAgent:
    def __init__(self, ensemble_size=32, ridge=1.):
        if ensemble_size<2 or ridge<=0:
            raise ValueError('Invalid TRAIN forecast config')
        self.ensemble_size=ensemble_size
        self.ridge=ridge
        self.fitted=False

    def fit(self, history, allowed_train_dates, role='Train'):
        if role!='Train':
            raise ValueError('Forecast calibration requires Train')
        allowed=set(allowed_train_dates)
        # Reject mixed-role source tables rather than silently fitting foreign dates.
        if set(history.dates)-allowed:
            raise ValueError('Non-Train weather in fit source')
        x=[];y=[];years=[]
        for i in range(6,len(history.dates)-14):
            x.append(_features(history.dates[i],history.values[i-6:i+1]))
            y.append(history.values[i+1:i+15].reshape(-1))
            years.append(history.dates[i].year)
        x=np.array(x);y=np.array(y);years=np.array(years)
        if len(x)<100 or len(set(years))<3:
            raise ValueError('At least three TRAIN calendar years for rolling-origin calibration')
        residual=[]
        # Forecast residuals come from later TRAIN years never used by their fit fold.
        for year in sorted(set(years))[2:]:
            fit=years<year;valid=years==year
            # Purge target windows that would cross into validation calendar year.
            index_dates=[history.dates[i] for i in range(6,len(history.dates)-14)]
            fit &= np.array([(d+timedelta(days=14)).year<year for d in index_dates])
            if fit.sum()>=50 and valid.any():
                residual.append(y[valid]-x[valid]@_solve(x[fit],y[fit],self.ridge))
        if not residual:
            raise ValueError('No out-of-fold forecast residual blocks')
        self.coef=_solve(x,y,self.ridge)
        self.residual=np.concatenate(residual).reshape(-1,14,6)
        totals=y.reshape(-1,14,6)[:,:,3].sum(1)
        self.rain_totals=np.sort(totals)
        self.rain_lo,self.rain_hi=np.quantile(totals,[.1,.9])
        self.temp_reference=float(history.values[:,:2].mean())
        self.temp_scale=max(float(history.values[:,:2].std()),1e-6)
        self.region_id=history.region_id
        self.source_id=history.source_id
        self.train_dates_sha256=hashlib.sha256('\n'.join(d.isoformat() for d in history.dates).encode()).hexdigest()
        self.model_id=hashlib.sha256(self.coef.tobytes()+self.residual.tobytes()+str((self.ensemble_size,self.ridge,self.train_dates_sha256)).encode()).hexdigest()
        self.fitted=True
        return self

    def forecast(self, history, as_of, seed=0, mode='realistic_noisy', oracle_truth=None):
        if not self.fitted or history.region_id!=self.region_id:
            raise ValueError('Missing region-specific TRAIN calibration')
        h=history.through(as_of)
        if h.dates[-1]!=as_of or len(h.dates)<7:
            raise ValueError('Need seven days ending at as_of')
        valid=tuple(as_of+timedelta(days=i) for i in range(1,15))
        if mode=='realistic_noisy':
            if oracle_truth is not None:
                raise ValueError('Future truth forbidden in causal mode')
            mean=(_features(as_of,h.values[-7:])@self.coef).reshape(14,6)
            rng=np.random.default_rng(seed)
            members=mean+self.residual[rng.integers(len(self.residual),size=self.ensemble_size)]
        elif mode=='perfect':
            if oracle_truth is None or oracle_truth.region_id!=self.region_id:
                raise ValueError('Explicit oracle truth required')
            values=np.array([oracle_truth.values[oracle_truth.dates.index(d)] for d in valid])
            members=np.repeat(values[None],self.ensemble_size,axis=0)
        else:
            raise ValueError('Unknown forecast mode')
        members=_physical(members)
        rain=members[:,:,3].sum(1)
        mean_temp=members[:,:,:2].mean()
        vector=np.array([np.mean(rain>self.rain_hi),np.mean(rain<self.rain_lo),
                         np.tanh((mean_temp-self.temp_reference)/self.temp_scale),
                         1-np.searchsorted(self.rain_totals,float(rain.mean()),side='right')/len(self.rain_totals)])
        return Forecast(as_of,valid,finite_array(members),self.region_id,
                        self.source_id+':'+self.model_id,mode,finite_array(vector,(4,)))
