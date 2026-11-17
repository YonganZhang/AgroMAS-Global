"""Measured CPU component latency and explicit storage/parameter accounting."""
from pathlib import Path
import json,time,pickle,platform,os,numpy as np,joblib,torch
from threadpoolctl import threadpool_limits,threadpool_info
from sb3_contrib import MaskablePPO
from pcse_gym.agromas_v6.core import Policy,GRID,select_objective
from pcse_gym.agromas_v6.training import predict_stats
from pcse_gym.agromas_v6.book_env import encode
from pcse_gym.agromas_v7.bridge import features,reconstruct
R=Path(__file__).resolve().parents[1];P=R/'reports/phase7'
def timing(fn):
 for _ in range(100):fn()
 times=[]
 for _ in range(1000):
  start=time.perf_counter_ns();fn();times.append((time.perf_counter_ns()-start)/1e6)
 return dict(median_ms=float(np.median(times)),p95_ms=float(np.quantile(times,.95)),warmup=100,repeats=1000)
if __name__=='__main__':
 torch.set_num_threads(1);file=R/'models/phase6/r2/Full/stage-1.joblib';forest=joblib.load(file);a=np.load(R/'models/phase7/descriptive-linear-probes-v7.npz');site=__import__('pandas').read_csv(P/'station-mean-64d-v7.csv').iloc[0];z=site[[f'A{j:02}' for j in range(64)]].to_numpy(float);imputers=joblib.load(R/'models/phase7/bridge-imputers-LOYO-2018.joblib');scale,model=imputers['Satellite_bridge'];base=np.array([.2,2,.3,0,50,1,.2,0,-.2,.3,0,0,0,1,0,.2,.9,0,.69,.3,.1,10.]);prior=np.r_[base[19:22],.03];policy=Policy();legal=np.ones(7,bool)
 def sat_lookup():return z.copy()
 def impute():
  x=features(base,'Satellite_bridge',prior,sat_lookup());return reconstruct(base,model.predict(scale.transform(x[None]))[0])
 def full_decision():
  b=impute();stats=predict_stats(forest,np.c_[np.repeat(b[None],7,axis=0),GRID],legal);return select_objective(stats,legal,40.,1.,0.,policy)[0]
 stats=predict_stats(forest,np.c_[np.repeat(base[None],7,axis=0),GRID],legal);obs,mask,_=encode(base,stats,legal,40.,1.,0.,policy);folder=R/'models/phase6/r2/PPO-structured-seed4';ppo=MaskablePPO.load(folder/'model.zip',device='cpu');ppo.policy.set_training_mode(False)
 with (folder/'vecnormalize.pkl').open('rb') as f:norm=pickle.load(f)
 norm.training=False;norm.norm_reward=False
 def ppo_only():return ppo.predict(norm.normalize_obs(obs[None]),deterministic=True,action_masks=mask)[0]
 def ppo_pipeline():
  s=predict_stats(forest,np.c_[np.repeat(base[None],7,axis=0),GRID],legal);o,m,_=encode(base,s,legal,40.,1.,0.,policy);return ppo.predict(norm.normalize_obs(o[None]),deterministic=True,action_masks=m)[0]
 with threadpool_limits(limits=1):times=dict(cached64D_lookup=timing(sat_lookup),satellite_ridge_imputation=timing(impute),satellite_plus_frozen_proxy_decision=timing(full_decision),PPO_network_normalization_only=timing(ppo_only),PPO_shared_proxy_plus_network=timing(ppo_pipeline))
 tree_nodes=sum(t.tree_.node_count for stage in (1,2,3) for t in joblib.load(R/f'models/phase6/r2/Full/stage-{stage}.joblib').model.estimators_);node_bytes=sum(sum(getattr(t.tree_,field).nbytes for field in ['children_left','children_right','feature','threshold','value','impurity','n_node_samples','weighted_n_node_samples']) for stage in (1,2,3) for t in joblib.load(R/f'models/phase6/r2/Full/stage-{stage}.joblib').model.estimators_)
 report=dict(timing=times,hardware=dict(platform=platform.platform(),CPU=next((s.split(':',1)[1].strip() for s in Path('/proc/cpuinfo').read_text().splitlines() if s.startswith('model name')),platform.processor()),logical_cpus=os.cpu_count(),torch_threads=torch.get_num_threads(),threadpools=threadpool_info()),ridge_imputer_trainable_scalars=int(model.coef_.size+model.intercept_.size),PPO_trainable_parameters=sum(p.numel() for p in ppo.policy.parameters()),frozen_proxy_total_nodes=tree_nodes,frozen_proxy_tree_array_bytes=node_bytes,frozen_proxy_serialized_bytes=sum((R/f'models/phase6/r2/Full/stage-{s}.joblib').stat().st_size for s in (1,2,3)),PPO_zip_bytes=(folder/'model.zip').stat().st_size,AEF_lookup_vector_bytes=64*8,process_peak_RSS_KiB=__import__('resource').getrusage(__import__('resource').RUSAGE_SELF).ru_maxrss,physical_grid_scope='Native343-plan books expose physical integration step counts, not directly comparable wall-time measurements; no numerical native wall-time speedup claimed.',scope='Warm batch1 synthetic fixed-input CPU timing, includes cached lookup and frozen proxy where named; excludes network extraction and model loading. Tree nodes, bytes and neural trainable parameters are distinct capacity measures.')
 (P/'inference-footprint-v7.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
