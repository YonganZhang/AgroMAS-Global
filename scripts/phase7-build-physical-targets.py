"""Read immutable historical books into site-year endpoints and prefix-only features."""
from pathlib import Path
import json,hashlib,numpy as np,pandas as pd
from pcse_gym.agromas.features import shared_features
R=Path(__file__).resolve().parents[1];P=R/'reports/phase7';D=R/'data/phase7-alphaearth-v1'
if __name__=='__main__':
 rows=[];source=[]
 for f in sorted((R/'data/phase5-final-evaluation-books-v4').glob('*-Historical-*.jsonl')):
  source.append(dict(path=str(f.relative_to(R)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()));book=[json.loads(x) for x in f.read_text().splitlines()];assert len(book)==343
  first=next(x for x in book if x['plan']==[0,0,0]);n2=next(x for x in book if x['plan']==[60,80,80]);m=np.array([x['outcome'] for x in book]);ok=(m[:,3]>=.5)&(m[:,3]<=.9)&(m[:,2]>=0)&(m[:,2]<=40);profit=200*m[:,0]-1.5*m[:,4];best=min(range(343),key=lambda i:(-profit[i],m[i,4],tuple(book[i]['plan'])));fert=m[ok,4];slopes=[]
  for i in range(343):
   for j in range(i+1,343):
    delta=np.asarray(book[j]['plan'])-book[i]['plan']
    if np.count_nonzero(delta)==1 and delta.sum()>0 and m[j,4]>m[i,4] and all((delta[k]==0 or next((g for g in [0,10,20,40,60,80,100] if g>book[i]['plan'][k]),None)==book[j]['plan'][k]) for k in range(3)):slopes.append((profit[j]-profit[i])/(m[j,4]-m[i,4]))
  state=first['states'].get('1');assert state is not None;base=shared_features(str(R),state);stock=first['stock_diagnostics'];latlon={'netherlands_lelystad':(52.57,5.63),'france_paris_beauce':(48.44,1.49),'usa_kansas_wichita':(37.69,-97.34),'china_ncp_luancheng':(37.89,114.69),'australia_wa_perth':(-31.95,115.86)}
  row=dict(region=first['region_id'],year=int(first['harvest_year']),cohort='Former-Held-Out' if first['role']=='Held-Out' else 'Public-Reused',mineralization=stock['native_net_mineralization_N_kg_ha'],zeroN_grainN=first['outcome'][1],upper_export=stock['upper_boundary_export_not_in_published_loss_kg_ha'],NLOSSCUM=n2['stock_diagnostics']['native_published_leaching_plus_denitrification_kg_ha'],feasible_fraction=float(ok.mean()),corridor_width=float(fert.max()-fert.min()) if len(fert) else 0.,optimal_total_N=float(m[best,4]),harvest_grain_DM=float(n2['outcome'][0])*1000,harvest_grain_N=float(n2['outcome'][1]),marginal_profit_sensitivity=max(0.,max(slopes)),external_nonfert_N=float(first['outcome'][5]),crop_N_uptake=stock['native_soil_crop_uptake_N_kg_ha'],latitude=latlon[first['region_id']][0],longitude=latlon[first['region_id']][1],source=str(f.relative_to(R)))
  for j in range(4):row[f'prefix_weather_{j}']=float(base[6+j])
  row['doy_sin']=float(base[15]);row['doy_cos']=float(base[16]);rows.append(row)
 df=pd.DataFrame(rows);assert len(df)==59 and sum(df.cohort=='Former-Held-Out')==52
 df.to_csv(P/'physical-targets-v7.csv',index=False);(P/'physical-target-provenance-v7.json').write_text(json.dumps({'books':source,'new_native_rollouts':0,'definitions':'ANALYSIS_PROTOCOL_V7.json','n_site_years':59},indent=2));print(df.groupby('cohort').size().to_dict())
