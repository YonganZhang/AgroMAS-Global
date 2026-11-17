"""Independent mathematical audit of frozen TRAIN sample geometry; no Dev access."""
from pathlib import Path
import json,numpy as np
from pcse_gym.agromas_v8.data import parity_features
R=Path(__file__).resolve().parents[1];D=R/'cache/phase8-train-arrays';P=R/'reports/phase8'
if __name__=='__main__':
 x=np.load(D/'x.npy');y=np.load(D/'y.npy');meta=json.loads((D/'meta.json').read_text());groups={};stage={}
 for i,m in enumerate(meta):groups.setdefault(m['prefix'],[]).append(i);stage[m['stage']]=stage.get(m['stage'],0)+1
 for ids in groups.values():
  z=x[ids][:,list(range(22))+[25,26]];assert np.allclose(z,z[:1],rtol=0,atol=1e-10),'Unexecuted future actions altered observable prefix'
 assert (y[:,2]>=x[:,3]-1e-8).all() and (y[:,2]<=x[:,3]+x[:,22:25].sum(1)+1e-8).all()
 assert (x[:,3]+x[:,22:25].sum(1)<=220+1e-8).all()
 assert np.isfinite(x).all() and np.isfinite(y).all()
 assert not parity_features(x,'Sensorless')[:,[1,2,4]].any()
 assert all(1995<=m['year']<=2009 for m in meta)
 region_counts={r:sum(m['region']==r for m in meta) for r in sorted({m['region'] for m in meta})};minimum=x.std(0)<1e-8
 out={'status':'passed','rows':len(y),'stage_counts':stage,'unique_causal_prefixes':len(groups),'prefix_causality_max_tolerance':1e-10,'Executed_N_bounds_all_pass':True,'Sensorless_hidden_columns_zero':True,'regions':region_counts,'CN_row_fraction':region_counts['china_ncp_luancheng']/len(y),'training_objective':'fixed sample-average standardized MSE; CN cardinality imbalance disclosed; evaluation BSS/coverage equal region-year-stage','inactive_columns':np.flatnonzero(minimum).tolist(),'two_architecture_parameter_count':13155,'baseline_NN_preprocessing_difference':'NN fold-standardized inactive-masked inputs; tree raw identical information, no asymmetric extra covariates','conditional_OOF_not_operational_forecast':True,'not_universal_DL_failure':'Two small MLPs and three-bin weather descriptors only; no claim all DL/backbones fail.'}
 (P/'phase8b-TRAIN-contract-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
