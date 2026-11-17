"""Forecast-tool invariance only; full online-action invariance is a G2 gate."""
from datetime import date,timedelta
import numpy as np
import pytest
from pcse_gym.agromas.climate_agent import WeatherHistory
from pcse_gym.agromas_v8 import climate

class FakeWeather:
 def __init__(self):
  self.parameters={p:{} for p in ['T2M_MIN','T2M_MAX','PRECTOTCORR','ALLSKY_SFC_SW_DWN']}
  for y in list(range(1994,2010))+[2011,2012]:
   for i in range(366):
    d=date(y,1,1)+timedelta(days=i);key=d.strftime('%Y%m%d')
    for p,v in zip(self.parameters,[8.+y%3,17.+y%4,2.+y%5,12.+y%6]):self.parameters[p][key]=v
 def history(self,start,end,*,as_of):
  assert end<=as_of
  days=tuple(start+timedelta(days=i) for i in range((end-start).days+1));a=[]
  for d in days:
   key=d.strftime('%Y%m%d');p=self.parameters;a.append([p['T2M_MIN'][key],p['T2M_MAX'][key],p['ALLSKY_SFC_SW_DWN'][key],p['PRECTOTCORR'][key],60.,3.])
  return WeatherHistory(days,np.array(a),'netherlands_lelystad','synthetic-train-contract')

@pytest.mark.parametrize('perturbation',range(30))
def test_conditional_analog_tool_ignores_future_target_weather(monkeypatch,perturbation):
 w=FakeWeather();monkeypatch.setattr(climate,'regional_weather',lambda *args:w)
 as_of=date(2012,4,1);a=climate.ClimateForecastAgent('unused');before=a.branches('netherlands_lelystad',as_of)
 for p,vals in w.parameters.items():
  for k in vals:
   if '20120401'<k<'20130101':vals[k]+=1000*(perturbation+1)
 b=climate.ClimateForecastAgent('unused');after=b.branches('netherlands_lelystad',as_of)
 assert np.array_equal(before[0],after[0]) and np.array_equal(before[1],after[1]) and before[2]==after[2]
 with pytest.raises(ValueError):a.offline_train_descriptor('netherlands_lelystad',2012,as_of)
