"""Causal shared features for physical teacher fitting and all online controllers."""
from datetime import date,timedelta
from functools import lru_cache
from pathlib import Path
import json
import numpy as np
import joblib,yaml
from .regions import REGIONS
from .season import regional_weather


@lru_cache(maxsize=5)
def forecast_model(root,name):
    return joblib.load(Path(root)/'models/phase5/climate-v2'/(name+'.joblib'))


@lru_cache(maxsize=5)
def soil_context(root,name):
    r=Path(root)
    if name=='netherlands_lelystad':
        soil=yaml.safe_load((r/'NUE_PCSE-Gym/pcse_gym/envs/configs/soil/arminda_soil.yaml').read_text())
    else:soil=json.loads((r/'reports/phase5/regional-model-inputs'/name/'soil-v1.json').read_text())
    l=soil['SoilProfileDescription']['SoilLayers'][0]
    pf=np.array(l['SMfromPF'])
    return np.array([np.interp(2,pf[::2],pf[1::2]),np.interp(4.2,pf[::2],pf[1::2]),
                     np.interp(-1,np.array(l['CONDfromPF'])[::2],np.array(l['CONDfromPF'])[1::2])])


def shared_features(root,state,climate='Historical',*,forecast_mode='realistic_noisy'):
    name=state['region_id'];day=state['as_of']
    if isinstance(day,str):day=date.fromisoformat(day)
    weather=regional_weather(str(root),name,'v2')
    history=weather.history(day-timedelta(days=6),day,as_of=day)
    model=forecast_model(str(root),name)
    # All online modes access only observed history. Oracle is handled by explicit
    # evaluation-only caller supplying future truth, never silently here.
    if forecast_mode!='realistic_noisy':raise ValueError('Explicit causal feature mode required')
    forecast=model.forecast(history,day,seed=4)
    climate_vector=forecast.vector
    angle=2*np.pi*day.timetuple().tm_yday/365.25
    delta,co2={'Historical':(0.,380.),'idealized_mid':(1.8,450.),'idealized_high':(3.5,550.)}[climate]
    context=np.r_[np.array([n==name for n in REGIONS],float),np.sin(angle),np.cos(angle),
                   delta,co2/550.,soil_context(str(root),name)]
    observed=np.array([state[k] for k in ['dvs','lai','sm','n_fert_cum','n_uptake','stage']])
    return np.r_[observed,climate_vector,context]
