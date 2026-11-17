"""Full-season analog branches; conservative first7-day observable partitions."""
from datetime import date,timedelta
import numpy as np
from pcse_gym.agromas_v8.climate import ClimateForecastAgent
from pcse_gym.agromas.season import regional_weather

class TreeClimateForecastAgent(ClimateForecastAgent):
 def tree(self,name,as_of,climate='Historical',*,observed_history=None,mean_only=False):
  if isinstance(as_of,str):as_of=date.fromisoformat(as_of)
  source=regional_weather(self.root,name,'v2');past=[];descriptors=[];reveal=[]
  if observed_history is None:observed_history=source.history(as_of-timedelta(days=13),as_of,as_of=as_of)
  if any(d>as_of for d in observed_history.dates):raise ValueError('Future target history denied')
  delta={'Historical':0.,'idealized_mid':1.8,'idealized_high':3.5}[climate]
  correction=delta if delta and observed_history.source_id!=source.source_id else 0.
  target=np.array([observed_history.values[:,:2].mean()-correction,observed_history.values[:,3].sum()])
  for year in self.train_years:
   issue,end=self._window(name,year,as_of);h=source.history(issue-timedelta(days=13),issue,as_of=issue).values;past.append([h[:,:2].mean(),h[:,3].sum()]);descriptors.append(self._descriptor(name,year,as_of,climate))
   # These are forecast scenario observations, never target future weather.
   rows=source.history(issue+timedelta(days=1),min(issue+timedelta(days=7),end),as_of=end).values
   reveal.append([rows[:,3].sum(),rows[:,:2].mean()])
  past=np.array(past);scale=np.maximum(past.std(0),[1.,10.]);dist=np.mean(((past-target)/scale)**2,axis=1);w=np.exp(-np.minimum(dist,50)/2);w/=w.sum();desc=np.array(descriptors);reveal=np.array(reveal)
  if mean_only:return np.sum(desc*w[:,None],axis=0,keepdims=True),np.ones(1),np.zeros(1,int),np.zeros(1,int),{'scope':'TRAIN conditional historical analog mean,notNWP','years':self.train_years}
  rain=(reveal[:,0]>np.median(reveal[:,0])).astype(int);temp=np.zeros(len(w),int)
  for group in np.unique(rain):
   ix=rain==group;temp[ix]=(reveal[ix,1]>np.median(reveal[ix,1])).astype(int)
  return desc,w,rain,temp,{'scope':'TRAIN conditional historical weather analogs,notNWP','years':self.train_years,'revealed_information':'first7daysrain_thenfirst7daystemp;noanalogyidentityorlateseasonreveal'}
