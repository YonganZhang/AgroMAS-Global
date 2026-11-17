"""Typed current-prefix features, with source-correct NASA or WUR weather history."""
from datetime import date,timedelta
import hashlib,json
import numpy as np
from pcse_gym.agromas.climate_agent import WeatherHistory
from pcse_gym.agromas.features import forecast_model,soil_context
from pcse_gym.agromas.season import regional_weather
from pcse_gym.agromas.regions import REGIONS

def history_from_provider(provider,name,as_of,days=14):
 start=as_of-timedelta(days=days-1)
 if hasattr(provider,'history'):return provider.history(start,as_of,as_of=as_of)
 if hasattr(provider,'source') and hasattr(provider.source,'history'):
  # Preserve the observed source RH contract used by the TRAIN books. A
  # dewpoint-derived engine RH is not numerically identical to NASA RH2M.
  h=provider.source.history(start,as_of,as_of=as_of);v=np.array(h.values,copy=True);cold=v[:,:2].mean(1)
  v[:,:2]+=provider.delta_temperature;v[:,2]*=provider.radiation_scale;v[:,3]*=provider.rain_scale
  sat=lambda t:.6108*np.exp(17.27*t/(t+237.3))
  v[:,4]=np.clip(v[:,4]*sat(cold)/sat(cold+provider.delta_temperature),0,100)
  context=dict(source_id=provider.source.source_id,delta_temperature=provider.delta_temperature,rain_scale=provider.rain_scale,radiation_scale=provider.radiation_scale)
  return WeatherHistory(h.dates,v,name,hashlib.sha256(json.dumps(context,sort_keys=True).encode()).hexdigest())
 rows=[];dates=tuple(start+timedelta(days=i) for i in range(days))
 for day in dates:
  v=provider(day);temp=(v.TMIN+v.TMAX)/2;sat=.6108*np.exp(17.27*temp/(temp+237.3));rh=np.clip(v.VAP/10/sat*100,0,100)
  rows.append([v.TMIN,v.TMAX,v.IRRAD/1e6,v.RAIN*10,rh,v.WIND])
 source_id=getattr(provider,'source_id',None)
 if source_id is None and hasattr(provider,'source'):
  context=dict(source_id=provider.source.source_id,delta_temperature=provider.delta_temperature,rain_scale=provider.rain_scale,radiation_scale=provider.radiation_scale)
  source_id=hashlib.sha256(json.dumps(context,sort_keys=True).encode()).hexdigest()
 if source_id is None:raise ValueError('Weather source provenance required')
 return WeatherHistory(dates,np.array(rows),name,source_id)

def public_state(state,track):
 keep=['as_of','region_id','dvs','n_fert_cum','stage','days_since_last_fert','climate']
 if track=='Full-Telemetry':keep+=['lai','sm','n_uptake']
 elif track!='Sensorless':raise ValueError('Unknown information track')
 return {k:state[k] for k in keep if k in state}

def feature_base(root,state,climate='Historical',history=None):
 name=state['region_id'];as_of=state['as_of'];as_of=date.fromisoformat(as_of) if isinstance(as_of,str) else as_of
 if history is None:history=history_from_provider(regional_weather(str(root),name,'v2'),name,as_of)
 if any(d>as_of for d in history.dates):raise ValueError('Future realized weather denied')
 delta,co2={'Historical':(0.,380.),'idealized_mid':(1.8,450.),'idealized_high':(3.5,550.)}[climate]
 source=regional_weather(str(root),name,'v2')
 values=np.array(history.values[-7:],copy=True)
 if delta and history.source_id!=source.source_id:
  # ScenarioWeather keeps vapor pressure fixed, so reverse its RH response too.
  warm=values[:,:2].mean(1);cold=warm-delta
  sat=lambda t:.6108*np.exp(17.27*t/(t+237.3))
  values[:,4]=np.clip(values[:,4]*sat(warm)/sat(cold),0,100)
  values[:,:2]-=delta
 last7=WeatherHistory(history.dates[-7:],values,history.region_id,history.source_id)
 forecast=forecast_model(str(root),name).forecast(last7,as_of,seed=4).vector
 angle=2*np.pi*as_of.timetuple().tm_yday/365.25;delta,co2={'Historical':(0.,380.),'idealized_mid':(1.8,450.),'idealized_high':(3.5,550.)}[climate]
 observed=[state.get(k,0.) for k in ['dvs','lai','sm','n_fert_cum','n_uptake','stage']]
 # Region one-hot stays absent in every new model/control; source-soil priors
 # are numerical model context, not additional native hidden soil observations.
 return np.r_[observed,forecast,np.zeros(5),np.sin(angle),np.cos(angle),delta,co2/550.,soil_context(str(root),name)]

def candidate_features(root,state,plans,climate='Historical',history=None):
 base=feature_base(root,state,climate,history);day=date.fromisoformat(state['as_of']) if isinstance(state['as_of'],str) else state['as_of'];reg=REGIONS[state['region_id']];year=day.year+(reg.hemisphere=='north' and day.month>=9);end=reg.crop_dates(year)[1]
 return np.c_[np.repeat(base[None],len(plans),axis=0),plans,np.full(len(plans),min(60.,max(0.,state.get('days_since_last_fert',60.)))),np.full(len(plans),(end-day).days),np.zeros((len(plans),9))]
