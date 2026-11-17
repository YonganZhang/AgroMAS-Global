"""Fixed G2 controls using the same registered MLP and TRAIN-only recipe.

No new architecture families, Dev-based selection, or physical simulations.
Pure-Weather removes all three soil channels; Linear keeps matched information.
"""
from pathlib import Path
import argparse,importlib.util,json,os,subprocess,sys,hashlib
import numpy as np,joblib
from sklearn.linear_model import Ridge
R=Path(__file__).resolve().parents[1];D=R/'cache/phase8-train-arrays';P=R/'reports/phase8';WD=R/'cache/phase8-weather-control-arrays';M=R/'models/phase8-controls'

def worker(fold,seed):
 spec=importlib.util.spec_from_file_location('g1_fixed_recipe',R/'scripts/phase8-fit-world-model.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.D=WD;m.M=M/'pure-weather';m.fit('Sensorless','mlp',fold,seed)

if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--worker',action='store_true');a.add_argument('--fold',type=int);a.add_argument('--seed',type=int);args=a.parse_args()
 if args.worker:worker(args.fold,args.seed);raise SystemExit(0)
 assert json.loads((P/'phase8b-G1-verdict.json').read_text())['status']=='G1_PASS'
 M.mkdir(exist_ok=False);(M/'pure-weather').mkdir();WD.mkdir(exist_ok=False)
 x=np.load(D/'x.npy');x[:,19:22]=0;np.save(WD/'x.npy',x)
 for n in ['y.npy','meta.json']:(WD/n).symlink_to(D/n)
 protocol={'registered_before_P1_or_P2_evaluation':True,'selected_backbone':'first registered mlp; G1passbothtracks','pureweather':'same36DMLP/13155params; zero3soilchannelsand3hiddenchannels; no regionID','epochs':80,'seeds':[20261115,20261116,20261117],'folds':list(range(5))+[-1],'Linear':'Ridgealpha10,sameparityfeatures/split/targets','no_Dev_model_selection':True,'no_new_NN_architecture':True}
 (P/'phase8b-G2-control-training-protocol.json').write_text(json.dumps(protocol,indent=2))
 from concurrent.futures import ThreadPoolExecutor,as_completed
 import queue
 gpu=queue.Queue()
 for i in [0,1,5,7]:gpu.put(str(i))
 def run(job):
  fold,seed=job;device=gpu.get();key=f'pure-weather-fold{fold}-seed{seed}'
  try:
   with (P/(key+'.log')).open('x') as f:rc=subprocess.run([sys.executable,__file__,'--worker','--fold',str(fold),'--seed',str(seed)],env=dict(os.environ,CUDA_VISIBLE_DEVICES=device,CUBLAS_WORKSPACE_CONFIG=':4096:8'),stdout=f,stderr=subprocess.STDOUT).returncode
   if rc:raise RuntimeError(key+' failed')
   return key
  finally:gpu.put(device)
 with ThreadPoolExecutor(max_workers=4) as pool:
  for f in as_completed([pool.submit(run,(fold,seed)) for fold in [0,1,2,3,4,-1] for seed in [20261115,20261116,20261117]]):print(f.result(),flush=True)
 from pcse_gym.agromas_v8.data import parity_features
 y=np.load(D/'y.npy');meta=json.loads((D/'meta.json').read_text());years=np.array([m['year'] for m in meta]);base=np.load(D/'x.npy')
 for track in ['Full-Telemetry','Sensorless']:
  z=parity_features(base,track)
  for fold in [0,1,2,3,4,-1]:
   valid=(years-1995)%5==fold if fold>=0 else np.ones(len(years),bool);fit=~valid if fold>=0 else valid
   mean=z[fit].mean(0);sd=z[fit].std(0);active=sd>1e-8;sd=np.where(active,sd,1);features=np.where(active,(z-mean)/sd,0);model=Ridge(alpha=10.).fit(features[fit],y[fit]);path=M/f'{track}-Linear-fold{fold}.joblib';joblib.dump({'model':model,'mean':mean,'sd':sd,'active':active},path);np.save(WD/f'{track}-Linear-fold{fold}-pred.npy',model.predict(features[valid]))
 files={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in M.rglob('*') if p.is_file() and p.suffix in ['.pt','.joblib']}
 for rel in files:(R/rel).chmod(0o444)
 (P/'phase8b-G2-control-freeze.json').write_text(json.dumps({'files':files,'TRAIN_only':True,'same_registered_architecture':True,'no_eval_access':True},indent=2));print('G2 control fits complete',flush=True)
