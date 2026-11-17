"""TRAIN-only year-isolated latent/physical associations, not causal understanding.

Zero-plan endpoints use all225 TRAIN site/year/climate worlds, never Dev or
P1/P2 evaluation labels. Each outer TRAIN-year decoder uses a backbone that also
excluded that year. Fixed Ridge alpha10; all four registered track/architectures.
"""
from pathlib import Path
import gzip,hashlib,json
import numpy as np,torch
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score,mean_squared_error
from pcse_gym.agromas_v8.data import row_samples,parity_features
from pcse_gym.agromas_v8.climate import ClimateForecastAgent
from pcse_gym.agromas_v8.models import WorldModel
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';M=R/'models/phase8-v8'
TARGETS=['final_organic_N_kg_ha','final_mineral_N_kg_ha','native_Nloss_kg_ha','final_soil_C_kg_ha','native_net_mineralization_N_kg_ha']
if __name__=='__main__':
 torch.set_num_threads(2);(R/'data/phase8-physical-decoding').mkdir(exist_ok=False);receipt=json.loads((P/'phase8b-physical-receipt.json').read_text());agent=ClimateForecastAgent(R);xs=[];ys=[];meta=[]
 for entry in sorted(receipt['files'],key=lambda e:e['path']):
  if entry['role']!='Train':continue
  path=R/entry['path'];assert entry['failed']==0 and hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
  # Cartesian book begins with zero plan; no need to decode remaining daily books.
  with gzip.open(path,'rt') as f:row=json.loads(next(f))
  assert row['plan']==[0,0,0] and row['role']=='Train' and 1995<=row['harvest_year']<=2009
  samples=list(row_samples(R,row,agent,actual_train_weather=True));x,y,m=next(v for v in samples if v[2]['stage']==1)
  xs.append(x);ys.append([row['stock_diagnostics'][k] for k in TARGETS]);meta.append(m)
 x=np.array(xs);y=np.array(ys);assert len(y)==225;years=np.array([m['year'] for m in meta]);result={}
 for track in ['Full-Telemetry','Sensorless']:
  for arch in ['mlp','residual-mlp']:
   decoded=np.zeros_like(y);raw_decoded=np.zeros_like(y)
   for fold in range(5):
    test=(years-1995)%5==fold;fit=~test;c=torch.load(M/f'{track}-{arch}-fold{fold}-seed20261115/model.pt',weights_only=False);model=WorldModel(architecture=arch);model.load_state_dict(c['state_dict'],strict=True);model.eval()
    raw=parity_features(x,track);z=np.where(c['x_active'],np.clip((raw-c['x_mean'])/c['x_std'],-8,8),0).astype('float32')
    with torch.no_grad():latent=model.latent(torch.from_numpy(z)).numpy()
    scale=StandardScaler().fit(latent[fit]);decoder=Ridge(alpha=10.).fit(scale.transform(latent[fit]),y[fit]);decoded[test]=decoder.predict(scale.transform(latent[test]))
    direct_scale=StandardScaler().fit(raw[fit]);direct=Ridge(alpha=10.).fit(direct_scale.transform(raw[fit]),y[fit]);raw_decoded[test]=direct.predict(direct_scale.transform(raw[test]))
   bytarget={k:{'latent_OOF_R2':float(r2_score(y[:,i],decoded[:,i])),'raw_feature_OOF_R2':float(r2_score(y[:,i],raw_decoded[:,i])),'latent_RMSE':float(np.sqrt(mean_squared_error(y[:,i],decoded[:,i])))} for i,k in enumerate(TARGETS)}
   result[track+'-'+arch]={'targets':bytarget,'regions':{r:{k:float(r2_score(y[np.array([m['region']==r for m in meta]),i],decoded[np.array([m['region']==r for m in meta]),i])) for i,k in enumerate(TARGETS)} for r in sorted({m['region'] for m in meta})}}
   np.savez_compressed(R/f'data/phase8-physical-decoding/{track}-{arch}-TRAIN-physical-decoding.npz',truth=y,decoded=decoded,raw_decoded=raw_decoded)
 out={'scope':'225 TRAIN zero-plan endpoints,5outeryearfolds;backboneanddecoderbothouteryearisolated;offlineassociationonly','targets':TARGETS,'results':result,'no_Dev_or_evaluation_labels':True,'not_online_inputs':True,'no_claim_agents_understand_raw_vectors':True};(P/'phase8b-TRAIN-physical-decoding.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
