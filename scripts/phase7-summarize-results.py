"""Human-readable facts and state reconstruction summaries without any refitting."""
from pathlib import Path
import json,hashlib,numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];P=R/'reports/phase7'
if __name__=='__main__':
 d=pd.read_csv(R/'reports/phase6/annual-policy-metrics-v6.csv');base=d[(d.climate=='Historical')&(d.cap==40)&(d.price_multiplier==1)&(d.subsidy==0)&(d.cohort=='Former-Held-Out')];facts={'policy_primary':{}}
 for policy in ['Phase5-A4','Phase6-Full','PPO-v6-structured-book','DVS-N2','PPO-v4-structured-shared','Phase4-Forest-transfer','N2-PA-calendar']:
  x=base[base.policy==policy]
  if x.empty:continue
  facts['policy_primary'][policy]={v:float(x.groupby('region_id')[v].mean().mean()) for v in ['joint','partial_profit','fertN','stock_soil_N_stock_drawdown_kg_ha','stock_native_published_leaching_plus_denitrification_kg_ha','stock_upper_boundary_export_not_in_published_loss_kg_ha']}
 b=facts['policy_primary']['Phase6-Full'];fixed=facts['policy_primary']['DVS-N2'];facts['vs_fixed']={'profit_gain':b['partial_profit']-fixed['partial_profit'],'N_reduction_kg':fixed['fertN']-b['fertN'],'N_reduction_percent':100*(fixed['fertN']-b['fertN'])/fixed['fertN']}
 records=json.loads((P/'bridge-policy-results-v7.json').read_text());state=[]
 for scheme in ['LOYO','LORO']:
  for regime in ['Weather_only','Static_soil','Satellite_bridge']:
   for stage in [1,2,3]:
    rows=[err for x in records if x['scheme']==scheme and x['regime']==regime and 2018<=x['year']<=2026 for err in x['state_errors'] if err['stage']==stage];y=np.array([x['observed'][:3] for x in rows]);pr=np.array([x['predicted'][:3] for x in rows])
    for j,name in enumerate(['LAI','soil_moisture','crop_N_uptake']):state.append(dict(scheme=scheme,regime=regime,stage=stage,target=name,prefix_observations=len(y),site_year_window='prior2018_2026 n44; reachable chosen prefixes',RMSE=float(np.sqrt(np.mean((y[:,j]-pr[:,j])**2))),R2=float(1-np.sum((y[:,j]-pr[:,j])**2)/np.sum((y[:,j]-y[:,j].mean())**2))))
 (P/'state-reconstruction-v7.json').write_text(json.dumps(state,indent=2));facts['satellite_site_years']=45;facts['prior_full_n']=44;facts['prior_narrow_n']=20;facts['overlap_full_n']=45;facts['overlap_narrow_n']=25;facts['control_reference_former_held_out_n']=52;facts['public_reused_n']=7
 facts['decoding']={}
 for x in json.loads((P/'decoding-nested-statistics-v7.json').read_text())['results']:
  key=f"{x['window']}|{x['model']}|{x['scheme']}|{x['target']}";facts['decoding'][key]={v:x[v] for v in ['n','R2','RMSE','r','within_region_R2','between_region_variance_fraction','permutations']}
 facts['bridge']=json.loads((P/'bridge-comparison-statistics-v7.json').read_text());facts['footprint']=json.loads((P/'inference-footprint-v7.json').read_text());facts['cosine']=json.loads((P/'regional-fingerprint-and-cosine-v7.json').read_text());facts['extraction']=json.loads((P/'extraction-complete-verification-v7.json').read_text());facts['sources']={str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [R/'reports/phase6/annual-policy-metrics-v6.csv',P/'decoding-nested-statistics-v7.json',P/'bridge-comparison-statistics-v7.json',P/'inference-footprint-v7.json',P/'extraction-complete-verification-v7.json']}
 (P/'core-facts-v7.json').write_text(json.dumps(facts,indent=2));print(json.dumps({'policies':facts['policy_primary'],'vs_fixed':facts['vs_fixed']},indent=2))
