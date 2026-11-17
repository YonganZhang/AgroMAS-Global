"""Fixed-alpha reused Dev calibration of predetermined control models only."""
from pathlib import Path
import json
import numpy as np,torch
from pcse_gym.agromas_v8.joint_model import FrozenJointWorldModel
from pcse_gym.agromas_v8.offline_verification import predict_summary
from pcse_gym.agromas_v8.scoring import conformal_radius
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';D=R/'cache/phase8-weather-control-arrays';O=R/'data/phase8d-control-calibration'
if __name__=='__main__':
 if O.exists():raise FileExistsError('Preserve fixed control calibration')
 O.mkdir();torch.set_num_threads(2);device='cuda' if torch.cuda.is_available() else 'cpu';x=np.load(D/'Dev-x.npy');y=np.load(D/'Dev-y.npy');meta=json.loads((D/'Dev-meta.json').read_text());truth=y[:,2]+3.5-y[:,1];results={}
 for track,family in [('Full-Telemetry','ExtraTrees'),('Sensorless','ExtraTrees'),('Full-Telemetry','Linear'),('Sensorless','Linear'),('Sensorless','Weather')]:
  if family=='ExtraTrees':summary=dict(np.load(R/f'data/phase8d-g1-predictions/{track}-ExtraTrees.npz'))
  else:summary=predict_summary(R,x,meta,FrozenJointWorldModel(R,track,family,device=device,calibration='uncalibrated'))
  scores=np.maximum(summary['low']-truth,truth-summary['upper']);radius=conformal_radius(scores);results[track+'-'+family]=dict(radius=radius,alpha=.1,samples=len(y),calibration_set_coverage=float(np.mean((truth>=summary['low']-radius)&(truth<=summary['upper']+radius))),full_branch_product=True);np.savez_compressed(O/(track+'-'+family+'.npz'),**summary);print(json.dumps(dict(control=track+'-'+family,**results[track+'-'+family])),flush=True)
 (P/'phase8d-G2-control-calibration.json').write_text(json.dumps(dict(results=results,fixed_models=True,hyperparameter_selection=False,reused_Dev=True),indent=2))
