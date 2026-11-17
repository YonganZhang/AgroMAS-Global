"""Once-only fixed Phase8D Dev scoring;never selects against Held-Out outcomes."""
from pathlib import Path
import json,hashlib
import numpy as np,torch
from pcse_gym.agromas_v8.joint_model import FrozenJointWorldModel
from pcse_gym.agromas_v8.offline_verification import predict_summary,evaluate_summary
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';D=R/'cache/phase8-weather-control-arrays';O=R/'data/phase8d-g1-predictions'
if __name__=='__main__':
 if O.exists() or (P/'phase8d-G1-verdict.json').exists():raise FileExistsError('Preserve Phase8D Dev access')
 protocol=P/'phase8d-preregistered-protocol.json';assert protocol.exists();O.mkdir();torch.set_num_threads(2);device='cuda' if torch.cuda.is_available() else 'cpu';x=np.load(D/'Dev-x.npy');y=np.load(D/'Dev-y.npy');meta=json.loads((D/'Dev-meta.json').read_text());assert all(2010<=m['year']<=2014 for m in meta);ty=np.load(R/'cache/phase8-train-arrays/y.npy');tm=json.loads((R/'cache/phase8-train-arrays/meta.json').read_text());results={}
 (O/'access.json').write_text(json.dumps(dict(protocol_sha256=hashlib.sha256(protocol.read_bytes()).hexdigest(),device=device,reused_Dev=True,no_hyperparameter_selection=True)))
 for track in ['Full-Telemetry','Sensorless']:
  et=predict_summary(R,x,meta,FrozenJointWorldModel(R,track,'ExtraTrees',device=device,calibration='uncalibrated'));np.savez_compressed(O/(track+'-ExtraTrees.npz'),**et)
  neural=predict_summary(R,x,meta,FrozenJointWorldModel(R,track,'MLP',device=device,calibration='uncalibrated'));np.savez_compressed(O/(track+'-mlp.npz'),**neural);result=evaluate_summary(neural,y,meta,et,ty,tm);results[track+'-mlp']=result;print(json.dumps(dict(track=track,**result)),flush=True)
 full=results['Full-Telemetry-mlp'];sl=results['Sensorless-mlp'];relative=dict(Full_radius_strictly_tighter=full['conformal_radius_kg_ha']<sl['conformal_radius_kg_ha'],Full_regret_strictly_lower=full['partial_profit_ranking_regret_EUR_ha']<sl['partial_profit_ranking_regret_EUR_ha']);passed=all(v['passed'] for v in results.values()) and all(relative.values());out=dict(status='G1_PASS' if passed else 'G1_FAIL_HALT',results=results,Full_vs_Sensorless=relative,Dev_accesses=1,no_Dev_hyperparameter_adjustment=True,source_files={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'NUE_PCSE-Gym/pcse_gym/agromas_v8').glob('*.py')});(P/'phase8d-G1-verdict.json').write_text(json.dumps(out,indent=2));print(out['status'],flush=True)
