"""Fixed region-balanced Ridge stock heads,with neural and head outer years purged."""
from pathlib import Path
import json,hashlib
import numpy as np,torch
from sklearn.metrics import r2_score
from pcse_gym.agromas_v8.data import parity_features
from pcse_gym.agromas_v8.models import WorldModel
from pcse_gym.agromas_v8.decoding import fit_region_heads
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';D=R/'cache/phase8-train-arrays';O=R/'data/phase8d-physical-decoding-v2';TARGETS=['final_organic_N_kg_ha','final_mineral_N_kg_ha','native_Nloss_kg_ha','final_soil_C_kg_ha','native_net_mineralization_N_kg_ha']
if __name__=='__main__':
 if O.exists():raise FileExistsError('Preserve diagnostic output')
 O.mkdir();torch.set_num_threads(2);device='cuda' if torch.cuda.is_available() else 'cpu';meta=json.loads((D/'meta.json').read_text());x=np.load(D/'x.npy');years=np.array([m['year'] for m in meta]);regions=np.array([m['region'] for m in meta]);world=[(m['region'],m['year'],m['climate']) for m in meta];assert years.min()>=1995 and years.max()<=2009
 unique={v:0 for v in world}
 for v in world:unique[v]+=1
 weights=np.array([1/unique[v] for v in world]);old=json.loads((P/'phase8b-full-TRAIN-physical-decoding.json').read_text());source=R/old['results']['Full-Telemetry-mlp']['prediction_path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==old['results']['Full-Telemetry-mlp']['prediction_sha256'];y=np.load(source)['truth'];assert y.shape==(len(x),5);results={}
 for track in ['Full-Telemetry','Sensorless']:
  raw=parity_features(x,track);pred=np.zeros_like(y);direct=np.zeros_like(y)
  for fold in range(5):
   test=(years-1995)%5==fold;train=~test;c=torch.load(R/f'models/phase8-v8/{track}-mlp-fold{fold}-seed20261115/model.pt',weights_only=False);model=WorldModel();model.load_state_dict(c['state_dict'],strict=True);model.to(device).eval();z=np.where(c['x_active'],np.clip((raw-c['x_mean'])/c['x_std'],-8,8),0).astype('float32')
   with torch.no_grad():latent=np.concatenate([model.latent(torch.from_numpy(z[i:i+8192]).to(device)).cpu().numpy() for i in range(0,len(z),8192)])
   pred[test]=fit_region_heads(latent,y,regions,weights,train,test);direct[test]=fit_region_heads(raw,y,regions,weights,train,test)
  metrics={t:dict(latent_OOF_R2=float(r2_score(y[:,j],pred[:,j])),raw_OOF_R2=float(r2_score(y[:,j],direct[:,j]))) for j,t in enumerate(TARGETS)}
  by_region={r:{t:dict(latent_OOF_R2=float(r2_score(y[regions==r,j],pred[regions==r,j])),raw_OOF_R2=float(r2_score(y[regions==r,j],direct[regions==r,j])),RMSE=float(np.sqrt(np.mean((pred[regions==r,j]-y[regions==r,j])**2)))) for j,t in enumerate(TARGETS)} for r in sorted(set(regions))}
  out=O/(track+'.npz');np.savez_compressed(out,truth=y,decoded=pred,raw_decoded=direct);results[track+'-mlp']=dict(targets=metrics,by_region=by_region,auxiliary_stock_head='TRAIN-only standardized Ridge readout of frozen latent,not a retrained backbone',prediction_path=str(out.relative_to(R)),prediction_sha256=hashlib.sha256(out.read_bytes()).hexdigest());print(json.dumps(dict(track=track,by_region=by_region)),flush=True)
 required=[TARGETS[i] for i in [0,3,4]];passed=all(values[t]['latent_OOF_R2']>0 for v in results.values() for values in v['by_region'].values() for t in required)
 (P/'phase8d-full-TRAIN-physical-decoding-v2.json').write_text(json.dumps(dict(status='passed' if passed else 'gate_failed',TRAIN_only=True,backbone_unchanged=True,head_alpha=10.,world_equal_weights=True,weight_mean_one_preserves_alpha_units=True,region_specific_heads=True,outer_year_exclusion=True,not_causal_physical_identification=True,required_positive_targets=required,results=results),indent=2));print('Physical decoding gate:',passed,flush=True)
