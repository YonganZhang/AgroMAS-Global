"""One fixed calibration per new comparator; never re-score/retune G1 candidates.

Uses the already-exposed2010–2014 Dev labels only to fit fixed-alpha intervals,
not to select model hyperparameters/checkpoints. Primary G1 artifacts unchanged.
"""
from pathlib import Path
import gzip,hashlib,json,numpy as np,joblib,torch
from pcse_gym.agromas_v8.data import validate_dev_books,row_samples
from pcse_gym.agromas_v8.climate import ClimateForecastAgent
from pcse_gym.agromas_v8.tree_weather import TreeClimateForecastAgent
from pcse_gym.agromas_v8.joint_model import FrozenJointWorldModel
from pcse_gym.agromas_v8.ood import ApplicabilityDomain
from pcse_gym.agromas_v8.scoring import conformal_radius
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';M=R/'models/phase8-controls'
if __name__=='__main__':
 torch.set_num_threads(2);freeze=json.loads((P/'phase8b-G2-control-freeze.json').read_text());assert freeze['TRAIN_only']
 for rel,h in freeze['files'].items():assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==h
 xtrain=np.load(R/'cache/phase8-weather-control-arrays/x.npy');ood=ApplicabilityDomain('Sensorless').fit(xtrain);op=M/'PureWeather-ood.joblib';assert not op.exists();joblib.dump(ood,op);op.chmod(0o444);freeze['files'][str(op.relative_to(R))]=hashlib.sha256(op.read_bytes()).hexdigest();(P/'phase8b-G2-control-freeze.json').write_text(json.dumps(freeze,indent=2))
 receipt=validate_dev_books(R);claim=P/'phase8b-G2-control-calibration-claim.json'
 with claim.open('x') as f:json.dump({'fixed_controls':['Full-Telemetry-ExtraTrees','Sensorless-ExtraTrees','Full-Telemetry-Linear','Sensorless-Linear','Sensorless-Weather'],'freeze_sha256':hashlib.sha256((P/'phase8b-G2-control-freeze.json').read_bytes()).hexdigest(),'scope':'fixed-alpha calibration of predetermined controls only; reusedDev,notanewvalidation;noG1refit'},f,indent=2)
 xs=[];ys=[];meta=[];agent=ClimateForecastAgent(R)
 for ent in sorted(receipt['files'],key=lambda e:e['path']):
  if ent['role']!='Dev':continue
  with gzip.open(R/ent['path'],'rt') as f:
   for line in f:
    for x,y,m in row_samples(R,json.loads(line),agent,actual_train_weather=False):xs.append(x);ys.append(y);meta.append(m)
 x=np.array(xs);y=np.array(ys);assert np.array_equal(y,np.load(R/'data/phase8-g1-predictions/actual.npy'));truth=y[:,2]+3.5-y[:,1]
 # Public-prefix statistics can be reused by predeclared baselines. These are
 # not new primary-model validation data or a second primary G1 pass.
 np.save(R/'cache/phase8-weather-control-arrays/Dev-x.npy',x);np.save(R/'cache/phase8-weather-control-arrays/Dev-y.npy',y);(R/'cache/phase8-weather-control-arrays/Dev-meta.json').write_text(json.dumps(meta))
 groups={}
 for i,m in enumerate(meta):groups.setdefault((m['region'],m['as_of'],m['climate']),[]).append(i)
 results={};forecaster=TreeClimateForecastAgent(R)
 for track,family in [('Full-Telemetry','ExtraTrees'),('Sensorless','ExtraTrees'),('Full-Telemetry','Linear'),('Sensorless','Linear'),('Sensorless','Weather')]:
  if family=='ExtraTrees':members=np.load(R/f'data/phase8-g1-predictions/{track}-ExtraTrees-members.npy')
  else:
   model=FrozenJointWorldModel(R,track,family,device='cuda');members=np.zeros((len(x),32,6))
   for (region,day,climate),ids in groups.items():
    desc,weights,_,_,_=forecaster.tree(region,day,climate);response=model.response_tensor(x[ids],desc);branch=np.minimum(np.searchsorted(np.cumsum(weights),(np.arange(32)+.5)/32),len(weights)-1);members[ids]=response[:,branch,np.arange(32)]
  low=np.quantile(members[...,2],.05,axis=1,method='lower');up=np.quantile(members[...,2],.95,axis=1,method='higher');radius=conformal_radius(np.maximum(low-truth,truth-up));coverage=float(((truth>=low-radius)&(truth<=up+radius)).mean());results[track+'-'+family]={'radius':radius,'alpha':.1,'calibration_set_coverage':coverage,'no_independent_validation_claim':True,'samples':len(y)};print(json.dumps({'control':track+'-'+family,**results[track+'-'+family]}),flush=True)
 (P/'phase8b-G2-control-calibration.json').write_text(json.dumps({'scope':'fixed comparator calibration on already-exposedDev,oncepercontrol;G1notrerun;nohyperparameterselection','results':results},indent=2));print('All comparator calibrators frozen',flush=True)
