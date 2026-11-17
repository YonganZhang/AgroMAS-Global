"""Frozen causal P2 inputs with full branch probabilities and stratified residuals."""
from pathlib import Path
import json,hashlib
import numpy as np,joblib,torch
from datetime import date
from pcse_gym.agromas_v8.joint_model import FrozenJointWorldModel
from pcse_gym.agromas_v8.tree_weather import TreeClimateForecastAgent
from pcse_gym.agromas_v8.online_features import history_from_provider
from pcse_gym.agromas.season import regional_weather
R=Path(__file__).resolve().parents[1];D=R/'cache/phase8-p2-adapter-inputs';O=R/'cache/phase8d-p2-adapter-inputs';P=R/'reports/phase8'
if __name__=='__main__':
 if O.exists():raise FileExistsError('Preserve prepared input version')
 O.mkdir();torch.set_num_threads(2);device='cuda' if torch.cuda.is_available() else 'cpu';x=np.load(D/'x.npy');y=np.load(D/'y.npy');meta=joblib.load(D/'metadata.joblib');assert len(set(meta['world']))==44;np.save(O/'x.npy',x);np.save(O/'y.npy',y);joblib.dump(meta,O/'metadata.joblib',compress=3);forecaster=TreeClimateForecastAgent(R);descriptors=[];weights=np.empty((len(x),15))
 for group in meta['groups']:
  h=history_from_provider(regional_weather(str(R),group['region'],'v2'),group['region'],date.fromisoformat(group['day']));desc,w,*_=forecaster.tree(group['region'],group['day'],observed_history=h);descriptors.append(desc);weights[group['start']:group['end']]=w
 np.save(O/'weights.npy',weights)
 for family in ['MLP','Weather','Linear','ExtraTrees']:
  model=FrozenJointWorldModel(R,'Sensorless',family,device=device,calibration='uncalibrated');points=np.empty((len(x),15,3));banks=np.empty((len(x),32,3))
  for group,desc in zip(meta['groups'],descriptors):
   i,j=group['start'],group['end'];expanded=np.repeat(x[i:j,None,:],15,axis=1);expanded[:,:,-9:]=desc[None];points[i:j]=model.point(expanded.reshape(-1,36)).reshape(j-i,15,3)
   for n in range(i,j):banks[n]=model.residual_banks[(group['region'],int(round(x[n,5])))]
  np.save(O/f'{family}-points.npy',points);np.save(O/f'{family}-banks.npy',banks);print('Prepared',family,flush=True)
 (P/'phase8d-P2-input-freeze.json').write_text(json.dumps(dict(site_years=44,rows=len(x),full_product_members=480,outer_labels_not_used_for_preparation=True,files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in O.iterdir() if p.is_file()}),indent=2))
