"""Explicit evaluation-only oracle weather counterfactual, isolated from causal features."""
from datetime import date,timedelta
import numpy as np
from .regions import REGIONS,load_split_manifest,authorize_year
from .season import regional_weather
from .features import forecast_model
from .climate_agent import WeatherHistory
from pathlib import Path


def oracle_vector(root,region_id,day,climate,*,role,harvest_year,permit_path=None):
    if isinstance(day,str):day=date.fromisoformat(day)
    root=Path(root)
    authorize_year(load_split_manifest(root/'reports/phase5/global-date-split-manifest.json'),
                   region_id,harvest_year,role,permit_path=permit_path,project_root=root)
    lo,hi=REGIONS[region_id].weather_envelope(harvest_year)
    if not lo<=day<=hi:raise ValueError('Oracle issue date outside registered season')
    weather=regional_weather(str(root),region_id,'v2')
    past=weather.history(day-timedelta(days=6),day,as_of=day)
    # This branch is intentionally ORACLE, never called by shared_features/PPO/full.
    truth=weather.history(day+timedelta(days=1),day+timedelta(days=14),as_of=day+timedelta(days=14))
    values=np.array(truth.values,copy=True)
    values[:,:2]+={'Historical':0.,'idealized_mid':1.8,'idealized_high':3.5}[climate]
    truth=WeatherHistory(truth.dates,values,region_id,truth.source_id+':explicit-oracle:'+climate)
    return forecast_model(str(root),region_id).forecast(past,day,mode='perfect',oracle_truth=truth).vector
