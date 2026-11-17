"""TRAIN-only OOF raw conditional errors and model-ranking diagnostics, no Dev."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parents[1];D=R/'cache/phase8-train-arrays';P=R/'reports/phase8'
if __name__=='__main__':
 y=np.load(D/'y.npy');meta=json.loads((D/'meta.json').read_text());year=np.array([m['year'] for m in meta]);results={}
 for track in ['Full-Telemetry','Sensorless']:
  for arch in ['mlp','residual-mlp','ExtraTrees']:
   pred=np.zeros_like(y)
   for fold in range(5):
    pred[(year-1995)%5==fold]=np.load(D/f'{track}-ExtraTrees-fold{fold}-pred.npy') if arch=='ExtraTrees' else np.mean([np.load(D/f'{track}-{arch}-fold{fold}-seed{s}-pred.npy') for s in [20261115,20261116,20261117]],axis=0)
   rms=np.sqrt(np.mean((pred-y)**2,axis=0));byregion={r:np.sqrt(np.mean((pred[np.array([m['region']==r for m in meta])]-y[np.array([m['region']==r for m in meta])])**2,axis=0)).tolist() for r in sorted({m['region'] for m in meta})}
   results[track+'-'+arch]={'conditional_raw_OOF_RMSE_Y_GrainN_ExecutedN':rms.tolist(),'by_region':byregion}
 (P/'phase8b-TRAIN-CV-diagnostics.json').write_text(json.dumps({'scope':'TRAIN conditional actual-weather covariate prediction only; NOT operational forecast score; no Dev access','results':results},indent=2));print(json.dumps(results))
