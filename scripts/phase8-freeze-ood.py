"""Fit and seal observable applicability domains using TRAIN only."""
from pathlib import Path
import hashlib,json,numpy as np,joblib
from pcse_gym.agromas_v8.ood import ApplicabilityDomain
R=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 x=np.load(R/'cache/phase8-train-arrays/x.npy');files={}
 for track in ['Full-Telemetry','Sensorless']:
  model=ApplicabilityDomain(track).fit(x);p=R/f'models/phase8-v8/{track}-observable-ood.joblib';joblib.dump(model,p);files[str(p.relative_to(R))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'threshold':model.threshold}
 (R/'reports/phase8/phase8b-ood-freeze.json').write_text(json.dumps({'TRAIN_only':True,'percentile':.99,'scope':'observed context only; not a calibrated safety guarantee','files':files},indent=2));print(json.dumps(files))
