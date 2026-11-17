"""Frozen numerical response model; all raw priors/adapters remain private."""
from pathlib import Path
import json
import numpy as np,torch,joblib
from .models import WorldModel
from .data import parity_features
from .scoring import project_executed_members,build_stratified_residual_banks,build_global_zero_mean_bank

class FrozenJointWorldModel:
 def __init__(self,root,track='Sensorless',family='MLP',device='cpu',*,calibration='phase8d'):
  self.root=Path(root);self.track=track;self.family=family;self.device=device;self.models=[];self._adapter=None
  d=self.root/'cache/phase8-train-arrays';wd=self.root/'cache/phase8-weather-control-arrays';m=self.root/'models/phase8-v8';control=self.root/'models/phase8-controls';self.y=np.load(d/'y.npy');meta=json.loads((d/'meta.json').read_text());years=np.array([v['year'] for v in meta]);oof=np.zeros_like(self.y)
  if family in ['MLP','Weather']:
   parent=m if family=='MLP' else control/'pure-weather';source_track=track if family=='MLP' else 'Sensorless';predroot=d if family=='MLP' else wd
   for seed in [20261115,20261116,20261117]:
    c=torch.load(parent/f'{source_track}-mlp-fold-1-seed{seed}/model.pt',weights_only=False);model=WorldModel();model.load_state_dict(c['state_dict'],strict=True);self.models.append((model.to(device).eval(),c))
   for f in range(5):oof[(years-1995)%5==f]=np.mean([np.load(predroot/f'{source_track}-mlp-fold{f}-seed{s}-pred.npy') for s in [20261115,20261116,20261117]],axis=0)
  elif family=='ExtraTrees':
   self.models=[joblib.load(m/f'{track}-ExtraTrees-fold-1.joblib')]
   for f in range(5):oof[(years-1995)%5==f]=np.load(d/f'{track}-ExtraTrees-fold{f}-pred.npy')
  elif family=='Linear':
   self.models=[joblib.load(control/f'{track}-Linear-fold-1.joblib')]
   for f in range(5):oof[(years-1995)%5==f]=np.load(wd/f'{track}-Linear-fold{f}-pred.npy')
  else:raise ValueError('Unknown frozen numerical family')
  residual=self.y-oof;self.residual_banks=build_stratified_residual_banks(residual,meta);self.residual=build_global_zero_mean_bank(residual,meta)
  from pcse_gym.agromas.features import soil_context
  from pcse_gym.agromas.regions import REGIONS
  self.soil_to_region={tuple(np.round(soil_context(str(self.root),region),4)):region for region in REGIONS}
  if len(self.soil_to_region)!=5:raise ValueError('Calibrated soil keys are not unique')
  self.domain=joblib.load(control/'PureWeather-ood.joblib' if family=='Weather' else m/f'{track}-observable-ood.joblib')
  if calibration not in ('phase8d','legacy','uncalibrated'):raise ValueError('Explicit calibration version required')
  self.calibration=calibration
  if calibration=='uncalibrated':self.radius=0.
  else:
   prefix='phase8b' if calibration=='legacy' else 'phase8d'
   if family=='MLP':self.radius=json.loads((self.root/f'reports/phase8/{prefix}-G1-verdict.json').read_text())['results'][track+'-mlp']['conformal_radius_kg_ha']
   else:
    cal=self.root/f'reports/phase8/{prefix}-G2-control-calibration.json'
    self.radius=json.loads(cal.read_text())['results'][('Sensorless' if family=='Weather' else track)+'-'+family]['radius']
 def inputs(self,x):
  z=parity_features(x,self.track)
  if self.family=='Weather':z[:,[1,2,4,19,20,21]]=0.
  return z
 def point(self,x):
  x=self.inputs(x)
  if self.family=='ExtraTrees':return self.models[0].predict(x)
  if self.family=='Linear':
   c=self.models[0];return c['model'].predict(np.where(c['active'],(x-c['mean'])/c['sd'],0))
  outputs=[]
  with torch.no_grad():
   for model,c in self.models:
    z=np.where(c['x_active'],np.clip((x-c['x_mean'])/c['x_std'],-8,8),0).astype('float32');outputs.append(np.concatenate([model(torch.from_numpy(z[i:i+8192]).to(self.device)).cpu().numpy() for i in range(0,len(z),8192)])*c['y_std']+c['y_mean'])
  return np.mean(outputs,axis=0)
 def response_tensor(self,base_candidates,weather_descriptors,*,adapter_context=None):
  x=np.array(base_candidates,float);b=np.asarray(weather_descriptors,float);expanded=np.repeat(x[:,None,:],len(b),axis=1);expanded[:,:,-9:]=b[None];flat=expanded.reshape(-1,36);raw=self.point(flat)
  if self._adapter is not None:raw=raw+self._adapter.predict(flat,adapter_context)
  banks=[]
  for row in x:
   region=self.soil_to_region.get(tuple(np.round(row[19:22],4)))
   banks.append(self.residual if region is None else self.residual_banks[(region,int(round(row[5])))])
  bank=np.repeat(np.asarray(banks)[:,None,:,:],len(b),axis=1).reshape(-1,32,3)
  members=project_executed_members(raw[:,None,:]+bank,flat)
  return members.reshape(len(x),len(b),32,6)
 def prior_status(self,x,context=None):
  return dict(prior_accepted=None,prior_timing_admissible=None,prior_ood=None,prior_kind=None) if self._adapter is None else self._adapter.status(x,context)
 def calibration_radius(self,x,context=None):
  if self._adapter is None:return self.radius
  _,accepted=self._adapter.correction(x,context)
  return float(self._adapter.radius if np.all(accepted) else max(self.radius,self._adapter.radius))
 def applicability(self,x):
  score,allowed=self.domain.score(self.inputs(x));return float(score[0]),bool(allowed[0])
