"""TRAIN-only numerical contract checks;never evaluates a season or future truth."""
from pathlib import Path
import json
from datetime import date
import numpy as np
from pcse_gym.agromas.season import regional_weather
from pcse_gym.agromas.physiology import ScenarioWeather
from pcse_gym.agromas_v8.online_features import history_from_provider,feature_base
from pcse_gym.agromas_v8.tree_weather import TreeClimateForecastAgent
R=Path(__file__).resolve().parents[1];D=R/'cache/phase8-train-arrays';meta=json.loads((D/'meta.json').read_text());x=np.load(D/'x.npy',mmap_mode='r');agent=TreeClimateForecastAgent(R);seen=set();rows=[]
for i,m in enumerate(meta):
 key=(m['region'],m['stage'],m['climate'])
 if m['climate']=='Historical' or key in seen:continue
 seen.add(key);v=x[i];state=dict(zip(['dvs','lai','sm','n_fert_cum','n_uptake','stage'],v[:6]));state.update(region_id=m['region'],as_of=m['as_of'],days_since_last_fert=float(v[25]));day=date.fromisoformat(m['as_of']);source=regional_weather(str(R),m['region'],'v2');delta={'idealized_mid':1.8,'idealized_high':3.5}[m['climate']]
 # Angstrom constants are unused by history();this is not a physical season.
 provider=ScenarioWeather(source,delta_temperature=delta,angstrom=(.25,.5));h=history_from_provider(provider,m['region'],day);base=feature_base(R,state,m['climate'],h);err=float(np.max(np.abs(base-v[:22])))
 a=agent.tree(m['region'],day,'Historical');b=agent.tree(m['region'],day,m['climate'],observed_history=h);weight_err=float(np.max(np.abs(a[1]-b[1])));shift=np.zeros(9);shift[[0,3,6]]=delta;desc_err=float(np.max(abs((b[0]-a[0])-shift)))
 rows.append(dict(region=m['region'],stage=m['stage'],climate=m['climate'],TRAIN_year=m['year'],feature_error=err,weight_error=weight_err,descriptor_shift_error=desc_err,passed=max(err,weight_err,desc_err)<1e-6))
assert len(rows)==30 and all(v['passed'] for v in rows),rows
(R/'reports/phase8/phase8d-warming-alignment.json').write_text(json.dumps(dict(status='passed',checks=rows,max_feature_error=max(v['feature_error'] for v in rows),max_weight_error=max(v['weight_error'] for v in rows),TRAIN_only=True,native_evaluation_seasons=0),indent=2));print('PASS:30 TRAIN region-stage-warming contracts')
