"""Post-review sensitivity only: independent region-wise paired-year bootstrap."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5';B=5000
if __name__=='__main__':
 source=P/'final-annual-seed-averaged-metrics-v4.csv';a=pd.read_csv(source)
 a=a[(a.role=='Held-Out')&(a.climate=='Historical')&(a.zone=='standard_40')&(a.price_multiplier==1)&(a.subsidy==0)]
 metrics=['joint','partial_profit','yield_tDM_ha','N_applied_kg_ha'];rows=[]
 for control in ['DVS-N2','PPO-structured-shared']:
  rng=np.random.default_rng(20261115);boots=[];points=[];support={}
  for region in sorted(a.region_id.unique()):
   x=a[a.region_id==region];full=x[x.arm=='A4'].set_index('harvest_year')[metrics].sort_index();ref=x[x.arm==control].set_index('harvest_year')[metrics].sort_index();assert full.index.equals(ref.index)
   delta=(full-ref).to_numpy();n=len(delta);support[region]=full.index.tolist();ix=rng.integers(0,n,size=(B,n));boots.append(delta[ix].mean(axis=1));points.append(delta.mean(axis=0))
  bootstrap=np.mean(boots,axis=0);point=np.mean(points,axis=0);ci=np.quantile(bootstrap,[.025,.975],axis=0)
  rows.append(dict(control=control,region_year_support=support,metrics={m:dict(difference=float(point[i]),CI95=ci[:,i].tolist()) for i,m in enumerate(metrics)}))
 out=dict(status='completed',scope='Post-hoc external-review-requested sensitivity; not a new primary analysis, no policy fitting/inference/selection',bootstrap_replicates=B,seed=20261115,weighting='equal-regionmacro',resampling='Paired harvest years sampled independently within each region with original regional n preserved; cross-region synchronous-year dependence is NOT preserved, unlike frozen primary analysis',primary_unchanged='final-global-macro-statistics-v4.json',source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),contrasts=rows)
 path=P/'final-region-stratified-macro-sensitivity-v4-r1.json'
 with path.open('x') as f:json.dump(out,f,indent=2)
 path.chmod(0o444);print(json.dumps(rows))
