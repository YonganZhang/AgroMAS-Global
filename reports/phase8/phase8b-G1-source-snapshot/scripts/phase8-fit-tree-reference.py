"""Identical-feature, identical-outer-year ExtraTrees reference fitted on TRAIN only."""
from pathlib import Path
import hashlib,json,time
import numpy as np,joblib
from sklearn.ensemble import ExtraTreesRegressor
from pcse_gym.agromas_v8.data import parity_features
R=Path(__file__).resolve().parents[1];D=R/'cache/phase8-train-arrays';M=R/'models/phase8-v8';P=R/'reports/phase8'
if __name__=='__main__':
 x=np.load(D/'x.npy');y=np.load(D/'y.npy');meta=json.loads((D/'meta.json').read_text());years=np.array([m['year'] for m in meta]);records=[]
 for track in ['Full-Telemetry','Sensorless']:
  z=parity_features(x,track)
  for fold in [0,1,2,3,4,-1]:
   valid=(years-1995)%5==fold if fold>=0 else np.ones(len(years),bool);fit=~valid if fold>=0 else valid
   tick=time.monotonic();tree=ExtraTreesRegressor(n_estimators=128,min_samples_leaf=4,max_features=1.,random_state=20261115,n_jobs=4).fit(z[fit],y[fit]);path=M/f'{track}-ExtraTrees-fold{fold}.joblib'
   if path.exists():raise FileExistsError('Preserve existing TRAIN reference weights')
   joblib.dump(tree,path,compress=3)
   np.save(D/f'{track}-ExtraTrees-fold{fold}-pred.npy',tree.predict(z[valid]));rec=dict(track=track,fold=fold,n_fit=int(fit.sum()),n_validation=int(valid.sum()),elapsed_seconds=time.monotonic()-tick,path=str(path.relative_to(R)),sha256=hashlib.sha256(path.read_bytes()).hexdigest());records.append(rec);print(json.dumps(rec),flush=True)
 (P/'phase8b-ExtraTrees-freeze.json').write_text(json.dumps({'files':records,'Dev_accessed':False},indent=2))
