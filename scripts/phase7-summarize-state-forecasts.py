"""Retain selected-trajectory surplus forecast errors; never rescore a controller."""
from pathlib import Path
import json,numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];P=R/'reports/phase7';M=R/'manuscript/phase7/supplement'
if __name__=='__main__':
 results=json.loads((P/'bridge-policy-results-v7.json').read_text());sources=pd.read_csv(P/'physical-targets-v7.csv').set_index(['region','year']).source.to_dict();cache={};flat=[]
 for r in results:
  key=(r['region'],r['year'])
  if key not in cache:cache[key]={tuple(x['plan']):x for x in map(json.loads,(R/sources[key]).read_text().splitlines())}
  physical=cache[key][tuple(r['plan'])];actual=physical['outcome'][2]
  for t in r['trace']:flat.append(dict(scheme=r['scheme'],regime=r['regime'],region=r['region'],year=r['year'],cohort=r['cohort'],stage=t['stage'],observed_terminal_surplus=float(actual),predicted_terminal_surplus=t['predicted_surplus']))
 d=pd.DataFrame(flat);d.to_csv(P/'stage-surplus-forecast-errors-v7.csv',index=False);rows=[]
 for (scheme,regime,stage),q in d[d.year.between(2018,2026)].groupby(['scheme','regime','stage']):
  y=q.observed_terminal_surplus.to_numpy();p=q.predicted_terminal_surplus.to_numpy();rows.append(dict(scheme=scheme,regime=regime,stage=int(stage),target='terminal_surplus_expectation',prefix_observations=len(y),site_year_window='prior2018_2026 n44; actual selected trajectories',RMSE=float(np.sqrt(np.mean((y-p)**2))),R2=float(1-((y-p)**2).sum()/((y-y.mean())**2).sum()),scope='Prediction under frozen continuation contrasted with adopted imputed-policy trajectory; combines state error and continuation-policy mismatch, not a measured contemporaneous soil state'))
 (P/'stage-surplus-forecast-summary-v7.json').write_text(json.dumps(rows,indent=2));base=json.loads((P/'state-reconstruction-v7.json').read_text());pd.DataFrame(base+rows).to_csv(M/'state-reconstruction.csv',index=False);print('Added',len(rows),'surplus expectation summaries without inference or model fitting')
