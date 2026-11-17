"""Causal full-calendar-horizon conditional historical weather analogs.

These are TRAIN historical analog branches, NOT operational NWP forecasts.
Actual TRAIN future descriptors are used only as offline supervised scenario
covariates. Online/Dev APIs cannot request the target season future weather.
"""
from datetime import date,timedelta
from functools import lru_cache
import numpy as np
from pcse_gym.agromas.regions import REGIONS
from pcse_gym.agromas.season import regional_weather

def _date(year,month,day):
 try:return date(year,month,day)
 except ValueError:return date(year,month,28)

class ClimateForecastAgent:
 def __init__(self,root,train_years=tuple(range(1995,2010))):
  self.root=str(root);self.train_years=tuple(train_years)
  if not self.train_years or any(y<1995 or y>2009 for y in self.train_years):raise ValueError('TRAIN analog years only')
 def _window(self,name,year,as_of):
  reg=REGIONS[name];start,end=reg.crop_dates(year)
  issue=_date(year-(reg.hemisphere=='north' and as_of.month>=9),as_of.month,as_of.day)
  if not start<=issue<=end:raise ValueError('Issue outside analog crop calendar')
  return issue,end
 @lru_cache(maxsize=32768)
 def offline_train_descriptor(self,name,year,as_of,climate='Historical'):
  if year not in self.train_years:raise ValueError('Offline realized weather covariate must be TRAIN')
  return self._descriptor(name,year,as_of,climate)
 @lru_cache(maxsize=32768)
 def _descriptor(self,name,year,as_of,climate):
  issue,end=self._window(name,year,as_of);n=(end-issue).days
  w=regional_weather(self.root,name,'v2');days=[issue+timedelta(days=i+1) for i in range(n)]
  p=w.parameters;delta={'Historical':0.,'idealized_mid':1.8,'idealized_high':3.5}[climate]
  vals=np.array([[(p['T2M_MIN'][d.strftime('%Y%m%d')]+p['T2M_MAX'][d.strftime('%Y%m%d')])/2+delta,p['PRECTOTCORR'][d.strftime('%Y%m%d')],p['ALLSKY_SFC_SW_DWN'][d.strftime('%Y%m%d')]] for d in days])
  if not len(vals):return np.zeros(9)
  return np.concatenate([[v[:,0].mean(),v[:,1].sum(),v[:,2].sum()] if len(v) else [0,0,0] for v in np.array_split(vals,3)])
 def branches(self,name,as_of,climate='Historical',*,observed_history=None):
  if isinstance(as_of,str):as_of=date.fromisoformat(as_of)
  # Only current observed history is read from the target season.
  w=regional_weather(self.root,name,'v2');h=w.history(as_of-timedelta(days=13),as_of,as_of=as_of) if observed_history is None else observed_history
  if any(day>as_of for day in h.dates):raise ValueError('Future target history denied')
  delta={'Historical':0.,'idealized_mid':1.8,'idealized_high':3.5}[climate]
  correction=delta if delta and h.source_id!=w.source_id else 0.
  target=np.array([h.values[:,:2].mean()-correction,h.values[:,3].sum()])
  descriptors=[];past=[]
  for y in self.train_years:
   issue,_=self._window(name,y,as_of)
   h=w.history(issue-timedelta(days=13),issue,as_of=issue).values
   past.append([h[:,:2].mean(),h[:,3].sum()]);descriptors.append(self._descriptor(name,y,as_of,climate))
  past=np.array(past);scale=np.maximum(past.std(0),[1.,10.]);distance=np.mean(((past-target)/scale)**2,axis=1)
  weights=np.exp(-np.minimum(distance,50)/2);weights/=weights.sum()
  return np.array(descriptors),weights,tuple(self.train_years)
