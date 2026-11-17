"""Five specialist boundaries; vectors and physical oracle objects are not messages."""
from dataclasses import dataclass
import re
from datetime import date
import numpy as np


def validate_public_payload(value):
 if isinstance(value,dict):
  if any(re.fullmatch(r'A\d\d',str(k)) for k in value):raise ValueError('Raw satellite channel forbidden in public payload')
  for v in value.values():validate_public_payload(v)
 elif isinstance(value,(list,tuple,np.ndarray)):
  try:
   numeric=np.asarray(value)
   if numeric.size==64 and np.issubdtype(numeric.dtype,np.number):raise ValueError('Reshaped raw 64D vector forbidden')
  except (TypeError,OverflowError):pass
  if len(value)==64 and all(np.isscalar(x) for x in value):raise ValueError('Raw 64D vector forbidden in public payload')
  for x in value:validate_public_payload(x)
 elif isinstance(value,(float,np.floating)) and not np.isfinite(value):raise ValueError('Non-finite public scalar')
 elif not isinstance(value,(str,int,float,bool,np.integer,np.floating,np.bool_,type(None))):raise ValueError('Only typed public scalar/array data; no simulator/model objects')

@dataclass(frozen=True)
class UrbanEcoSafetyAgent:
 cap:float=40.
 epsilon:float=.1
 def __post_init__(self):
  if self.cap not in (25.,35.,40.,50.) or not 0<self.epsilon<.5:raise ValueError('Invalid declared surplus regime')
 def assess(self,members):
  m=np.asarray(members,float);s=m[...,2]
  q=np.quantile(s,1-self.epsilon,axis=-1,method='higher');low=np.quantile(s,self.epsilon,axis=-1,method='lower')
  tail=s>=q[...,None];cvar=np.sum(np.where(tail,s,0),axis=-1)/np.sum(tail,axis=-1)
  return {'surplus_safe':(q<=self.cap)&(low>=0),'surplus_q90':q,'surplus_upper_CVaR':cvar}

@dataclass(frozen=True)
class SocioEconomicPolicyAgent:
 price_n:float=1.5
 price_grain:float=.2
 subsidy:float=0.
 surplus_tax:float=0.
 def __post_init__(self):
  if not np.isfinite([self.price_n,self.price_grain,self.subsidy,self.surplus_tax]).all() or min(self.price_n,self.price_grain)<=0 or min(self.subsidy,self.surplus_tax)<0:raise ValueError('Invalid experimental economic regime')
 def assess(self,members,*,subsidy_eligible=None):
  m=np.asarray(members,float);eff=(m[...,3]>=.5)&(m[...,3]<=.9)
  # Subsidy eligibility belongs to the current declared joint regime; the eco
  # specialist remains independent of NUE. Tax is an illustrative experimental
  # per-kg positive surplus charge, never a claim about implemented regional law.
  if self.subsidy and subsidy_eligible is None:raise ValueError("Declared subsidy eligibility required")
  eligible=np.asarray(subsidy_eligible,bool) if subsidy_eligible is not None else np.zeros_like(eff)
  if eligible.shape!=eff.shape:raise ValueError("Member-wise policy eligibility shape")
  value=1000*self.price_grain*m[...,0]-self.price_n*m[...,4]+self.subsidy*eligible-self.surplus_tax*np.maximum(m[...,2],0)
  return {'NUE_safe':eff.all(axis=-1),'expected_partial_profit':value.mean(axis=-1),'NUE_violation_probability':1-eff.mean(axis=-1)}

class SpatialTwinSurrogateAgent:
 """Returns physical-unit K32 predictions; raw priors remain inside numerical tool.

 The tool resolves site_prior_id privately. Neither raw priors nor torch
 state_dict/latent buffers are returned by this public reasoning interface.
 """
 __slots__=('_numerical_tool',)
 def __init__(self,numerical_tool):self._numerical_tool=numerical_tool
 def predict_joint_response(self,request):
  validate_public_payload(request)
  allowed={'as_of','site_prior_id','observable_prefix','dose_schedules','remaining_budget','model_version','information_track','regime'}
  if set(request)-allowed:raise ValueError('Unknown query fields, possible future/oracle payload')
  required={'as_of','site_prior_id','observable_prefix','dose_schedules'}
  if not required<=set(request):raise ValueError('Incomplete causal numerical query')
  prefix=request['observable_prefix'];allowed_observables={'region_id','dvs','n_fert_cum','stage','days_since_last_fert','weather_prefix','as_of'}
  track=request.get('information_track','Sensorless')
  if track=='Full-Telemetry':allowed_observables|={'lai','sm','n_uptake'}
  elif track!='Sensorless':raise ValueError('Unknown information track')
  if not isinstance(prefix,dict) or set(prefix)-allowed_observables:raise ValueError('Hidden or unavailable telemetry in observable prefix')
  as_of=date.fromisoformat(request['as_of'])
  if prefix.get('as_of') and date.fromisoformat(prefix['as_of'])>as_of:raise ValueError('Future prefix date')
  for weather in prefix.get('weather_prefix',[]):
   if date.fromisoformat(weather['date'])>as_of:raise ValueError('Future realized weather in query')
  result=self._numerical_tool.predict_joint_response(request)
  if set(result)-{'members','applicable','ood_score','model_version','calibration','forecast_scope'}:raise ValueError('Non-public numerical response field')
  validate_public_payload(result)
  members=np.asarray(result['members'],float)
  if members.ndim!=3 or members.shape[1:]!=(32,6):raise ValueError('K32 physical-unit joint members required')
  return result
