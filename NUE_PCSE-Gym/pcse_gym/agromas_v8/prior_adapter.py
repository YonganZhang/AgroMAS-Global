"""Fold-local numeric prior encoder; never a public specialist message/state."""
from datetime import date
import numpy as np
from sklearn.linear_model import Ridge
from .planning import weighted_quantile

class LowRankPriorAdapter:
 def __init__(self,kind='AE64',rank=4,alpha=10.,*,anom_alpha=10.,legacy=False):
  if kind not in ('AE64','Static3','Weather'):raise ValueError('Unknown prior')
  self.decomposed=kind=='AE64' and not legacy;self.legacy=legacy;self.anom_alpha=float(anom_alpha)
  self.decomposed=kind=='AE64' and not legacy;self.legacy=legacy;self.anom_alpha=float(anom_alpha)
  self.kind=kind;self.rank=min(rank,3 if kind=='Static3' else 4);self.alpha=alpha;self.radius=0.
 def _raw(self,x,context):
  if self.kind=='Static3':return np.asarray(x)[:,19:22],np.ones(len(x),bool)
  if self.kind=='Weather':return np.asarray(x)[:,[6,7,8,9,15,16,0]],np.ones(len(x),bool)
  # Context belongs solely to this numeric object. Public contexts contain only
  # opaque IDs; the private lookup returns the prior vector and annual end.
  raw=[];valid=[]
  if isinstance(context,dict):context=[(context["prior_id"],context["as_of"])]*len(x)
  for key,day in context:
   vector,annual_end=self._priors[key];valid.append(date.fromisoformat(str(annual_end))<date.fromisoformat(str(day)));raw.append(vector)
  return np.asarray(raw,float),np.asarray(valid,bool)
 def _encode(self,raw):
  z=np.where(self.active,(raw-self.mean)/self.sd,0.);latent=z@self.axes
  reconstruction=np.mean((z-latent@self.axes.T)**2,axis=1);distance=np.sum(latent**2/self.latent_var,axis=1)
  return latent,reconstruction,distance
 def _design(self,x,latent):
  total=(x[:,3]+x[:,22:25].sum(1))/220;stage=x[:,5]/3
  return np.c_[latent,latent*total[:,None],latent*stage[:,None]]
 def _fit_legacy(self,x,target,weights,context,*,priors=None):
  self._priors={} if priors is None else priors
  raw,valid=self._raw(x,context);original=np.asarray(weights,float)[valid].copy();keys=np.asarray([key for key,day in context])[valid]
  for key in np.unique(keys):
   group=keys==key;original[group]/=original[group].sum()
  w=original/original.sum();raw=raw[valid];xx=np.asarray(x)[valid];yy=np.asarray(target)[valid]
  if not len(raw):raise ValueError('No causally admissible prior training rows')
  self.mean=np.sum(raw*w[:,None],axis=0);variance=np.sum((raw-self.mean)**2*w[:,None],axis=0);self.active=variance>1e-12;self.sd=np.sqrt(np.maximum(variance,1e-12));z=np.where(self.active,(raw-self.mean)/self.sd,0.)
  values,axes=np.linalg.eigh((z*w[:,None]).T@z);order=np.argsort(values)[::-1][:min(self.rank,int(self.active.sum()))];self.axes=axes[:,order];self.latent_var=np.maximum(values[order],1e-8)
  latent,reconstruction,distance=self._encode(raw);self.reconstruction_limit=float(weighted_quantile(reconstruction,w,.99));self.distance_limit=float(weighted_quantile(distance,w,.99))
  self.ymean=np.sum(yy*w[:,None],axis=0);self.ysd=np.sqrt(np.maximum(np.sum((yy-self.ymean)**2*w[:,None],axis=0),1e-8))
  # Normalize weights to site-year totals1, preserving the registered Ridge10
  # penalty relative to the number of training site-years.
  self.head=Ridge(alpha=self.alpha).fit(self._design(xx,latent),(yy-self.ymean)/self.ysd,sample_weight=original)
  return self
 def _correction_legacy(self,x,context):
  raw,valid=self._raw(x,context);latent,reconstruction,distance=self._encode(raw);accepted=valid&(reconstruction<=self.reconstruction_limit+1e-10)&(distance<=self.distance_limit+1e-10)
  result=self.head.predict(self._design(np.asarray(x),latent))*self.ysd+self.ymean;result[~accepted]=0.
  return result,accepted
 def predict(self,x,context):return self.correction(x,context)[0]

 def _status_legacy(self,x,context):
  raw,valid=self._raw(x,context);_,reconstruction,distance=self._encode(raw);ood=(reconstruction>self.reconstruction_limit+1e-10)|(distance>self.distance_limit+1e-10)
  return dict(prior_accepted=bool(np.all(valid&~ood)),prior_timing_admissible=bool(np.all(valid)),prior_ood=bool(np.any(ood)),prior_kind=self.kind)

 def _contexts(self,x,context):
  return [(context['prior_id'],context['as_of'])]*len(x) if isinstance(context,dict) else list(context)
 def _anomalies(self,x,context):
  values=[];valid=[]
  for key,day in self._contexts(x,context):
   if ':' not in key:raise ValueError('Causal prior key must contain private site and embedding year')
   region,year=key.rsplit(':',1);year=int(year);issue=date.fromisoformat(str(day))
   vector,end=self._priors[key];ok=date.fromisoformat(str(end))<issue
   # No outcome labels and no satellite year later than the requested t-1 year.
   allowed=[np.asarray(v,float) for name,(v,last) in self._priors.items() if name.rsplit(':',1)[0]==region and int(name.rsplit(':',1)[1])<=year and date.fromisoformat(str(last))<issue]
   if ok and not allowed:raise ValueError('Missing causal satellite climatology')
   values.append(np.asarray(vector,float)-np.mean(allowed,axis=0) if ok else np.zeros(64));valid.append(ok)
  return np.asarray(values),np.asarray(valid,bool)
 def fit(self,x,target,weights,context,*,priors=None):
  if not getattr(self,'decomposed',False):return self._fit_legacy(x,target,weights,context,priors=priors)
  self._priors={} if priors is None else priors;raw,valid=self._anomalies(x,context)
  if not valid.any():raise ValueError('No admissible anomaly training rows')
  self.static=LowRankPriorAdapter('Static3',3,self.alpha).fit(x,target,weights,context)
  static=self.static.predict(x,context);xx=np.asarray(x)[valid];yy=(np.asarray(target)-static)[valid]
  original=np.asarray(weights,float)[valid].copy();keys=np.asarray([k for k,d in self._contexts(x,context)])[valid]
  for key in np.unique(keys):original[keys==key]/=original[keys==key].sum()
  w=original/original.sum();raw=raw[valid];self.mean=np.sum(w[:,None]*raw,axis=0);var=np.sum(w[:,None]*(raw-self.mean)**2,axis=0);self.active=var>1e-12;self.sd=np.sqrt(np.maximum(var,1e-12));z=np.where(self.active,(raw-self.mean)/self.sd,0.)
  eigen,axes=np.linalg.eigh((z*w[:,None]).T@z);order=np.argsort(eigen)[::-1][:min(self.rank,int(self.active.sum()))];self.axes=axes[:,order];self.latent_var=np.maximum(eigen[order],1e-8)
  latent,reconstruction,distance=self._encode(raw);self.reconstruction_limit=float(weighted_quantile(reconstruction,w,.99));self.distance_limit=float(weighted_quantile(distance,w,.99))
  self.ymean=np.sum(w[:,None]*yy,axis=0);self.ysd=np.sqrt(np.maximum(np.sum(w[:,None]*(yy-self.ymean)**2,axis=0),1e-8));self.head=None if latent.shape[1]==0 else Ridge(alpha=self.anom_alpha).fit(self._design(xx,latent),(yy-self.ymean)/self.ysd,sample_weight=original)
  return self
 def correction(self,x,context):
  if not getattr(self,'decomposed',False):
   result,accepted=self._correction_legacy(x,context)
   if self.kind=='Static3' and not getattr(self,'legacy',True):
    latent,_,_=self._encode(self._raw(x,context)[0]);result=self.head.predict(self._design(np.asarray(x),latent))*self.ysd+self.ymean;accepted=np.ones(len(x),bool)
   return result,accepted
  raw,valid=self._anomalies(x,context);latent,reconstruction,distance=self._encode(raw);accepted=valid&(reconstruction<=self.reconstruction_limit+1e-10)&(distance<=self.distance_limit+1e-10)
  delta=np.zeros((len(x),3)) if self.head is None else self.head.predict(self._design(np.asarray(x),latent))*self.ysd+self.ymean;delta[~accepted]=0.
  return self.static.predict(x,context)+delta,accepted
 def status(self,x,context):
  if not getattr(self,'decomposed',False):
   if self.kind=='Static3' and not getattr(self,'legacy',True):return dict(prior_accepted=True,prior_timing_admissible=True,prior_ood=False,prior_kind=self.kind)
   return self._status_legacy(x,context)
  raw,valid=self._anomalies(x,context);_,reconstruction,distance=self._encode(raw);ood=(reconstruction>self.reconstruction_limit+1e-10)|(distance>self.distance_limit+1e-10)
  return dict(prior_accepted=bool(np.all(valid&~ood)),prior_timing_admissible=bool(np.all(valid)),prior_ood=bool(np.any(ood)),prior_kind=self.kind)
