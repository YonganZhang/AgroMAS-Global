"""Pre-registered TRAIN-only CUDA Lightning fits; never opens Dev/evaluation books."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
import numpy as np
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';D=R/'cache/phase8-train-arrays';M=R/'models/phase8-v8'

def prepare():
 from pcse_gym.agromas_v8.data import load_train
 D.mkdir(exist_ok=False);M.mkdir(exist_ok=False)
 x,y,meta=load_train(R);np.save(D/'x.npy',x);np.save(D/'y.npy',y);(D/'meta.json').write_text(json.dumps(meta))
 manifest={'samples':len(y),'input_shape':list(x.shape),'target_shape':list(y.shape),'years':sorted({m['year'] for m in meta}),'regions':sorted({m['region'] for m in meta}),'stages':{str(s):sum(m['stage']==s for m in meta) for s in (1,2,3)},'Dev_accessed':False,'files':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in ['x.npy','y.npy','meta.json']}}
 (P/'phase8b-train-sample-contract.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest),flush=True)

def fit(track,architecture,fold,seed):
 import torch,lightning as L
 from torch.utils.data import IterableDataset,DataLoader
 from pcse_gym.agromas_v8.models import WorldModel
 from pcse_gym.agromas_v8.lightning_container import StructuredAutoResearchModule
 from pcse_gym.agromas_v8.data import parity_features
 torch.set_num_threads(2);L.seed_everything(seed,workers=True)
 if not torch.cuda.is_available():raise RuntimeError('CUDA required; CPU fit cannot be training evidence')
 x=parity_features(np.load(D/'x.npy'),track);y=np.load(D/'y.npy');meta=json.loads((D/'meta.json').read_text());years=np.array([m['year'] for m in meta]);regions=sorted({m['region'] for m in meta})
 valid=(years-1995)%5==fold if fold>=0 else np.ones(len(years),bool);training=~valid if fold>=0 else valid
 mean=x[training].mean(0);sd=x[training].std(0);active=sd>=1e-8;sd=np.where(active,sd,1.);ym=y[training].mean(0);ys=np.maximum(y[training].std(0),1.)
 z=np.where(active,np.clip((x-mean)/sd,-8,8),0).astype('float32');t=((y-ym)/ys).astype('float32')
 class Samples(IterableDataset):
  def __init__(self,ids,batch,shuffle):
   self.ids=torch.as_tensor(np.flatnonzero(ids),device='cuda');self.batch=batch;self.shuffle=shuffle
   self.z=torch.as_tensor(z,device='cuda');self.t=torch.as_tensor(t,device='cuda')
   self.regions={r:torch.as_tensor(np.array([m['region']==r for m in meta])[:,None],device='cuda') for r in regions}
  def __len__(self):return (len(self.ids)+self.batch-1)//self.batch
  def __iter__(self):
   ids=self.ids[torch.randperm(len(self.ids),device='cuda')] if self.shuffle else self.ids
   for j in range(0,len(ids),self.batch):
    ix=ids[j:j+self.batch];yield {'x':self.z[ix],'y':self.t[ix],'slice_masks':{r:v[ix] for r,v in self.regions.items()}}
 train=DataLoader(Samples(training,2048,True),batch_size=None,num_workers=0);val=DataLoader(Samples(valid,4096,False),batch_size=None,num_workers=0)
 key=f'{track}-{architecture}-fold{fold}-seed{seed}';out=M/key;out.mkdir(exist_ok=False)
 module=StructuredAutoResearchModule(WorldModel(architecture=architecture),torch.nn.MSELoss(),slice_names=tuple(regions),lr=.001,weight_decay=.001,scheduler={'name':'cosine'})
 logger=L.pytorch.loggers.CSVLogger(str(out),name='training')
 trainer=L.Trainer(accelerator='gpu',devices=1,max_epochs=80,precision='32-true',logger=logger,enable_progress_bar=False,enable_checkpointing=False,deterministic=True,check_val_every_n_epoch=10,num_sanity_val_steps=0,enable_model_summary=False)
 tick=time.monotonic();trainer.fit(module,train,val);model=module.model.cpu().eval()
 state={'state_dict':model.state_dict(),'architecture':architecture,'track':track,'seed':seed,'fold':fold,'x_mean':mean,'x_std':sd,'x_active':active,'y_mean':ym,'y_std':ys}
 torch.save(state,out/'model.pt')
 with torch.no_grad():
  predictions=np.concatenate([model(torch.from_numpy(z[valid][i:i+8192])).numpy()*ys+ym for i in range(0,int(valid.sum()),8192)])
 # Strict saved-state reload, same checkpoint predictions.
 reloaded=WorldModel(architecture=architecture);reloaded.load_state_dict(torch.load(out/'model.pt',weights_only=False)['state_dict'],strict=True);reloaded.eval()
 with torch.no_grad():assert torch.equal(model(torch.from_numpy(z[:8])),reloaded(torch.from_numpy(z[:8])))
 predpath=D/(key+'-pred.npy');np.save(predpath,predictions)
 rec=dict(key=key,track=track,architecture=architecture,fold=fold,seed=seed,n_fit=int(training.sum()),n_validation=int(valid.sum()),parameters=sum(p.numel() for p in model.parameters()),epochs=80,global_steps=trainer.global_step,elapsed_seconds=time.monotonic()-tick,cuda_device=torch.cuda.get_device_name(),torch=torch.__version__,lightning=L.__version__,weight_path=str((out/'model.pt').relative_to(R)),weight_sha256=hashlib.sha256((out/'model.pt').read_bytes()).hexdigest(),prediction_path=str(predpath.relative_to(R)),validation_role='outer_TRAIN_OOF' if fold>=0 else 'TRAIN_resubstitution_not_selection',Dev_used=False)
 (out/'receipt.json').write_text(json.dumps(rec,indent=2));print(json.dumps(rec),flush=True)

def campaign():
 from concurrent.futures import ThreadPoolExecutor,as_completed
 import queue
 invariants=(P/'phase8b-cpu-invariants.log').read_text()
 if '5 passed' not in invariants:raise ValueError('Non-empty invariant gate not passed')
 manifest=P/'phase8b-train-campaign-claim.json'
 with manifest.open('x') as f:json.dump({'started':time.time(),'architectures':['mlp','residual-mlp'],'epochs':80,'seeds':[20261115,20261116,20261117],'Dev_accessed':False},f,indent=2)
 gpu=queue.Queue()
 for i in [0,1,5,7]:gpu.put(str(i))
 jobs=[(track,arch,fold,seed) for track in ['Full-Telemetry','Sensorless'] for arch in ['mlp','residual-mlp'] for fold in [0,1,2,3,4,-1] for seed in [20261115,20261116,20261117]]
 def run(job):
  device=gpu.get();track,arch,fold,seed=job;key=f'{track}-{arch}-fold{fold}-seed{seed}';env=dict(os.environ,CUDA_VISIBLE_DEVICES=device,CUBLAS_WORKSPACE_CONFIG=':4096:8')
  try:
   with (P/(key+'.log')).open('x') as f:
    rc=subprocess.run([sys.executable,__file__,'fit','--track',track,'--architecture',arch,'--fold',str(fold),'--seed',str(seed)],env=env,stdout=f,stderr=subprocess.STDOUT).returncode
   if rc:raise RuntimeError(f'TRAIN fit failed {key}: exit{rc}; no Dev access permitted')
   return key
  finally:gpu.put(device)
 with (P/'phase8b-train-progress.jsonl').open('x') as log:
  with ThreadPoolExecutor(max_workers=4) as pool:
   for f in as_completed([pool.submit(run,j) for j in jobs]):
    key=f.result();log.write(json.dumps({'completed':key})+'\n');log.flush();print(key,flush=True)
 files={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(M.glob('*/model.pt'))}
 assert len(files)==72
 (P/'phase8b-train-model-freeze.json').write_text(json.dumps({'files':files,'no_Dev_selection':True,'all_models_frozen':True},indent=2))

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['prepare','fit','campaign']);ap.add_argument('--track');ap.add_argument('--architecture');ap.add_argument('--fold',type=int);ap.add_argument('--seed',type=int);a=ap.parse_args()
 if a.mode=='prepare':prepare()
 elif a.mode=='fit':fit(a.track,a.architecture,a.fold,a.seed)
 else:campaign()
