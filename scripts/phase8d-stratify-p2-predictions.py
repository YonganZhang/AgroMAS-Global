"""Descriptive cohort separation of frozen OOF predictions; no fitting/selection."""
from pathlib import Path
import json,hashlib,csv
import numpy as np,joblib
R=Path(__file__).resolve().parents[1];D=R/'cache/phase8d-p2-adapter-inputs';O=R/'models/phase8d-controls/p2-adapters';P=R/'reports/phase8'
if __name__=='__main__':
 m=joblib.load(D/'metadata.joblib');y=np.load(D/'y.npy');world=np.asarray(m['world']);lookup={f"{c['region']}:{c['year']}":c['cohort'] for c in m['cohort']};cohort=np.array([lookup[w] for w in world]);weights=np.array([1/np.sum(world==w) for w in world]);rows=[];sources={}
 for f in (D/'metadata.joblib',D/'y.npy'):sources[str(f.relative_to(R))]=hashlib.sha256(f.read_bytes()).hexdigest()
 for scheme in ('LOYO','LORO'):
  for variant in ('Full64','Static3','Weather','Linear64','ExtraTrees64'):
   f=O/f'{scheme}-{variant}-OOF.npz';sources[str(f.relative_to(R))]=hashlib.sha256(f.read_bytes()).hexdigest();a=np.load(f);error=(a['prediction'][:,1]-y[:,1])**2
   for label in ('Former-Held-Out','Public-Reused'):
    mask=cohort==label;w=weights[mask];acc=a['prior_accepted'][mask];row=dict(scheme=scheme,variant=variant,cohort=label,source='NASA',site_years=len(set(world[mask])),prediction_rows=int(mask.sum()),Grain_N_MSE_row_pooled=float(error[mask].mean()),Grain_N_MSE_world_equal=float(np.average(error[mask],weights=w)),prior_acceptance_rows=float(acc.mean()),prior_acceptance_world_equal=float(np.average(acc,weights=w)));rows.append(row)
 old=json.loads((P/'phase8d-P2-adapter-training-freeze.json').read_text())['results']
 for scheme in ('LOYO','LORO'):
  for variant in ('Full64','Static3','Weather','Linear64','ExtraTrees64'):
   parts=[v for v in rows if v['scheme']==scheme and v['variant']==variant];assert sorted(v['site_years'] for v in parts)==[4,40]
   for newkey,oldkey,weight in [('Grain_N_MSE_row_pooled','Grain_N_MSE_pooled','prediction_rows'),('Grain_N_MSE_world_equal','Grain_N_MSE_world_equal','site_years'),('prior_acceptance_rows','prior_acceptance_rows','prediction_rows'),('prior_acceptance_world_equal','prior_acceptance_world_equal','site_years')]:assert np.isclose(np.average([v[newkey] for v in parts],weights=[v[weight] for v in parts]),old[scheme+'-'+variant][oldkey],rtol=0.,atol=1e-9)
 result=dict(original_aggregate_reconstruction_passed=True,results=rows,source_sha256=sources,no_fitting=True,no_parameter_selection=True,original_first_pass_freeze_unchanged=True,scope='Cohorts and schemes separate; row-pooled/world-equal are within each named cohort only. Original all44 aggregate retained as archival diagnostic, not primary unpooled evidence.')
 (P/'phase8d-P2-predictive-cohort-strata.json').write_text(json.dumps(result,indent=2))
 with (P/'phase8d-P2-predictive-cohort-strata.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 print('Wrote20 cohort-separated predictive summaries from unchanged OOF arrays')
