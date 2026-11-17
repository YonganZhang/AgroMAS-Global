"""Full legal TRAIN intervention decoder, complementing225 zero-dose backgrounds.

No Dev/P1/P2 labels or fitting. Fixed Ridgealpha10, first registered neural seed,
backbone and decoder both held-year-out. Offline association, not causal proof.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import gzip,hashlib,json
import numpy as np,torch
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
from pcse_gym.agromas_v8.models import WorldModel
from pcse_gym.agromas_v8.data import parity_features
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';D=R/'cache/phase8-train-arrays';O=R/'data/phase8-physical-decoding';TARGETS=['final_organic_N_kg_ha','final_mineral_N_kg_ha','native_Nloss_kg_ha','final_soil_C_kg_ha','native_net_mineralization_N_kg_ha']
def read_book(ent):
 p=R/ent['path'];assert not p.stat().st_mode&0o222;targets={}
 # SHA already independently verified by the completed native endpoint audit.
 with gzip.open(p,'rt') as f:
  for line in f:
   row=json.loads(line);assert row['role']=='Train' and 1995<=row['harvest_year']<=2009 and row['status']=='completed'
   targets[tuple(row['plan'])]=[row['stock_diagnostics'][k] for k in TARGETS]
 assert len(targets)==343
 return (ent['region_id'],ent['year'],ent['climate']),targets
if __name__=='__main__':
 torch.set_num_threads(2);assert json.loads((P/'phase8b-native-endpoint-audit.json').read_text())['status']=='passed'
 receipt=json.loads((P/'phase8b-physical-receipt.json').read_text());entries=[e for e in receipt['files'] if e['role']=='Train'];assert len(entries)==225
 books={}
 with ProcessPoolExecutor(max_workers=8) as pool:
  for f in as_completed([pool.submit(read_book,e) for e in entries]):key,values=f.result();books[key]=values
 x=np.load(D/'x.npy');meta=json.loads((D/'meta.json').read_text());y=np.array([books[(m['region'],m['year'],m['climate'])][tuple(m['plan'])] for m in meta]);assert len(y)==177930 and np.isfinite(y).all();years=np.array([m['year'] for m in meta]);results={}
 for track in ['Full-Telemetry','Sensorless']:
  raw=parity_features(x,track)
  for arch in ['mlp','residual-mlp']:
   pred=np.zeros_like(y);direct_pred=np.zeros_like(y)
   for fold in range(5):
    test=(years-1995)%5==fold;fit=~test;c=torch.load(R/f'models/phase8-v8/{track}-{arch}-fold{fold}-seed20261115/model.pt',weights_only=False);model=WorldModel(architecture=arch);model.load_state_dict(c['state_dict'],strict=True);model.eval();z=np.where(c['x_active'],np.clip((raw-c['x_mean'])/c['x_std'],-8,8),0).astype('float32')
    with torch.no_grad():latent=np.concatenate([model.latent(torch.from_numpy(z[i:i+8192])).numpy() for i in range(0,len(z),8192)])
    scale=StandardScaler().fit(latent[fit]);decoder=Ridge(alpha=10.).fit(scale.transform(latent[fit]),y[fit]);pred[test]=decoder.predict(scale.transform(latent[test]))
    ds=StandardScaler().fit(raw[fit]);direct=Ridge(alpha=10.).fit(ds.transform(raw[fit]),y[fit]);direct_pred[test]=direct.predict(ds.transform(raw[test]))
   metrics={t:{'latent_OOF_R2':float(r2_score(y[:,j],pred[:,j])),'raw_OOF_R2':float(r2_score(y[:,j],direct_pred[:,j])),'latent_RMSE':float(np.sqrt(np.mean((pred[:,j]-y[:,j])**2)))} for j,t in enumerate(TARGETS)}
   regions={r:{t:float(r2_score(y[np.array([m['region']==r for m in meta]),j],pred[np.array([m['region']==r for m in meta]),j])) for j,t in enumerate(TARGETS)} for r in sorted({m['region'] for m in meta})}
   stages={str(s):{t:float(r2_score(y[np.array([m['stage']==s for m in meta]),j],pred[np.array([m['stage']==s for m in meta]),j])) for j,t in enumerate(TARGETS)} for s in [1,2,3]}
   out=O/f'full-TRAIN-{track}-{arch}.npz';assert not out.exists();np.savez_compressed(out,truth=y,decoded=pred,raw_decoded=direct_pred)
   results[track+'-'+arch]={'targets':metrics,'by_region':regions,'by_stage':stages,'prediction_path':str(out.relative_to(R)),'prediction_sha256':hashlib.sha256(out.read_bytes()).hexdigest()};print(json.dumps({'completed':track+'-'+arch,'targets':metrics}),flush=True)
 (P/'phase8b-full-TRAIN-physical-decoding.json').write_text(json.dumps({'scope':'59310legalTRAINplansx3causalstages=177930rows;225worlds;5outeryearfolds;backboneandprobeexcludedscoredyear;fixedalpha10','no_Dev_or_evaluation_labels':True,'no_extra_neural_architectures':True,'not_causal_physical_identification':True,'targets':TARGETS,'results':results},indent=2))
