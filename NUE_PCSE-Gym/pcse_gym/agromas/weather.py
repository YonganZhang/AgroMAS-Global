"""Verified real NASA weather drives physics; causal histories are a separate interface."""
from datetime import date,timedelta
from pathlib import Path
import json,hashlib
import numpy as np
from pcse.base.weather import WeatherDataProvider,WeatherDataContainer
from pcse.util import reference_ET
from pcse.input.nasapower import tdew_to_hpa
from .climate_agent import WeatherHistory
from .regions import sha256,validate_daily_payload


class VerifiedNASAWeather(WeatherDataProvider):
    # PCSE NASA default constants, fixed independently of any validation/test weather.
    angstA=.29
    angstB=.49

    def __init__(self,raw_path,expected_sha256,region_id,*,mean_temperature_path=None,mean_temperature_sha256=None):
        super().__init__()
        path=Path(raw_path)
        if sha256(path)!=expected_sha256:raise ValueError('Raw NASA weather hash mismatch')
        self.payload=json.loads(path.read_text())
        self.validation=validate_daily_payload(self.payload)
        self.valid_dates=set(self.validation['complete_dates'])
        self.region_id=region_id
        self.source_id=expected_sha256
        self.mean_temperature=None
        if mean_temperature_path is not None:
            if not mean_temperature_sha256 or sha256(mean_temperature_path)!=mean_temperature_sha256:
                raise ValueError('Daily mean-temperature source hash mismatch')
            extra=json.loads(Path(mean_temperature_path).read_text())
            if extra['parameters']['T2M']['units']!='C' or extra['geometry']['coordinates'][:2]!=self.payload['geometry']['coordinates'][:2]:
                raise ValueError('Mean-temperature units or location mismatch')
            self.mean_temperature=extra['properties']['parameter']['T2M']
            self.mean_temperature_fill=extra['header'].get('fill_value',-999)
            self.source_id=hashlib.sha256((expected_sha256+mean_temperature_sha256).encode()).hexdigest()
        lon,lat,elevation=self.payload['geometry']['coordinates']
        self.latitude=lat;self.longitude=lon;self.elevation=elevation
        self.parameters=self.payload['properties']['parameter']
        self.description=['NASA POWER gridded historical daily weather; '+expected_sha256]
        self._memo={}

    def __call__(self,day,member_id=0):
        if member_id!=0:raise ValueError('Deterministic historical physical weather only')
        if not isinstance(day,date):raise ValueError('Explicit date required')
        key=day.strftime('%Y%m%d')
        if key not in self.valid_dates:raise ValueError('Missing verified real weather date: '+key)
        if day not in self._memo:
            p=self.parameters
            mean=(p['T2M_MIN'][key]+p['T2M_MAX'][key])/2
            if self.mean_temperature is not None:
                mean=self.mean_temperature.get(key,self.mean_temperature_fill)
                if not np.isfinite(mean) or mean==self.mean_temperature_fill:
                    raise ValueError('Missing real daily mean temperature; no midpoint substitution')
            tmin=p['T2M_MIN'][key];tmax=p['T2M_MAX'][key]
            irrad=p['ALLSKY_SFC_SW_DWN'][key]*1e6
            rain=p['PRECTOTCORR'][key]/10.
            vap=tdew_to_hpa(p['T2MDEW'][key]);wind=p['WS2M'][key]
            e0,es0,et0=reference_ET(day,self.latitude,self.elevation,tmin,tmax,irrad,vap,wind,self.angstA,self.angstB)
            self._memo[day]=WeatherDataContainer(DAY=day,LAT=self.latitude,LON=self.longitude,ELEV=self.elevation,
                TMIN=tmin,TMAX=tmax,TEMP=mean,IRRAD=irrad,VAP=vap,WIND=wind,RAIN=rain,
                E0=e0/10.,ES0=es0/10.,ET0=et0/10.)
        # Never expose mutable original model driver instances to observers.
        import copy
        return copy.deepcopy(self._memo[day])

    def history(self,start,end,*,as_of):
        if end>as_of:raise ValueError('Future truth denied to forecast history')
        dates=tuple(start+timedelta(days=i) for i in range((end-start).days+1))
        rows=[]
        for day in dates:
            key=day.strftime('%Y%m%d')
            if key not in self.valid_dates:raise ValueError('Missing historical date; no imputation')
            p=self.parameters
            rows.append([p[x][key] for x in ('T2M_MIN','T2M_MAX','ALLSKY_SFC_SW_DWN','PRECTOTCORR','RH2M','WS2M')])
        return WeatherHistory(dates,np.asarray(rows),self.region_id,self.source_id)
