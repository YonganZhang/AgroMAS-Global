"""Frozen TRAIN/Dev sample contracts: full schedules at reachable prefixes."""
from pathlib import Path
from datetime import date
import hashlib,json,gzip
import numpy as np
from .climate import ClimateForecastAgent
from pcse_gym.agromas.regions import REGIONS

INPUT_DIM=36

def row_samples(root,row,climate_agent,*,actual_train_weather):
 if row['status']!='completed':raise ValueError('Failed physical row')
 plan=np.array(row['plan'],float);basal=row['initial_base_n']
 # Budget legality is identical across both tracks and all model families.
 if plan.sum()+basal>220+1e-8:return
 for stage in (1,2,3):
  state=row['states'].get(str(stage))
  if state is None:continue
  if any(str(s) not in row['states'] and plan[s-1]!=0 for s in range(1,stage)):continue
  base=np.array(row['features'][str(stage)],float)
  if base[3]+plan[stage-1:].sum()>220+1e-8:continue
  issue=date.fromisoformat(str(state['as_of']))
  past=[e for e in row['events'] if e['date']<=issue.isoformat() and e['dose']>0]
  spacing=min(60,(issue-date.fromisoformat(max(e['date'] for e in past))).days) if past else 60
  remaining=plan.copy();remaining[:stage-1]=0
  end=REGIONS[row['region_id']].crop_dates(row['harvest_year'])[1]
  # Region ID is not a hidden static-soil surrogate in the weather-only control.
  base[10:15]=0.
  descriptor=climate_agent.offline_train_descriptor(row['region_id'],row['harvest_year'],issue,row['climate']) if actual_train_weather else np.zeros(9)
  x=np.r_[base,remaining,spacing,(end-issue).days,descriptor]
  if x.shape!=(INPUT_DIM,) or not np.isfinite(x).all():raise ValueError('Input shape/finite contract')
  y=np.array(row['outcome'])[[0,1,4]]
  prefix=(row['region_id'],row['harvest_year'],row['climate'],stage,issue.isoformat(),tuple((e['stage'],e['date'],e['dose']) for e in row['events'] if e['date']<=issue.isoformat()))
  yield x,y,dict(region=row['region_id'],year=row['harvest_year'],climate=row['climate'],stage=stage,as_of=issue.isoformat(),prefix=repr(prefix),plan=row['plan'])

def load_train(root):
 root=Path(root);registry=json.loads((root/'reports/phase5/teacher-book-receipt-v2.json').read_text());agent=ClimateForecastAgent(root)
 xs=[];ys=[];meta=[]
 for ent in sorted(registry['files'],key=lambda e:e['path']):
  path=root/ent['path']
  if hashlib.sha256(path.read_bytes()).hexdigest()!=ent['sha256']:raise ValueError('Immutable TRAIN hash drift')
  with path.open() as f:
   for line in f:
    row=json.loads(line)
    if row['role']!='Train' or not 1995<=row['harvest_year']<=2009:raise ValueError('TRAIN-only input required')
    for x,y,m in row_samples(root,row,agent,actual_train_weather=True):xs.append(x);ys.append(y);meta.append(m)
 return np.asarray(xs),np.asarray(ys),meta

def validate_dev_books(root):
 root=Path(root);receipt_path=root/'reports/phase8/phase8b-physical-receipt.json'
 if not receipt_path.exists():raise ValueError('Physical campaign incomplete; do not claim Dev access')
 receipt=json.loads(receipt_path.read_text())
 if receipt['status']!='completed' or len(receipt['files'])!=250 or any(e['failed'] for e in receipt['files']):raise ValueError('Physical campaign not complete and clean')
 train=[e for e in receipt['files'] if e['role']=='Train']
 expected_train={(r,y,c) for r in REGIONS for y in range(1995,2010) for c in ['Historical','idealized_mid','idealized_high']}
 if len(train)!=225 or {(e['region_id'],e['year'],e['climate']) for e in train}!=expected_train:raise ValueError('Incomplete TRAIN diagnostic cohort')
 entries=[e for e in receipt['files'] if e['role']=='Dev']
 expected={(r,y) for r in REGIONS for y in range(2010,2015)}
 if {(e['region_id'],e['year']) for e in entries}!=expected or len(entries)!=25:raise ValueError('Incomplete Dev cohort')
 for ent in entries:
  path=root/ent['path']
  if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=ent['sha256']:raise ValueError('Sealed Dev file missing or changed')
 return receipt

def load_dev_once(root,freeze_digest):
 root=Path(root);receipt=validate_dev_books(root);claim=root/'reports/phase8/phase8b-dev-access-claim.json'
 with claim.open('x') as f:json.dump({'frozen_train_models_sha256':freeze_digest,'purpose':'one-shot marginalized conformal and pre-registered gates; no optimization'},f)
 agent=ClimateForecastAgent(root);xs=[];ys=[];meta=[]
 for ent in sorted(receipt['files'],key=lambda e:e['path']):
  if ent['role']!='Dev':continue
  path=root/ent['path']
  if ent['failed'] or hashlib.sha256(path.read_bytes()).hexdigest()!=ent['sha256']:raise ValueError('Sealed Dev integrity failed')
  with gzip.open(path,'rt') as f:
   for line in f:
    row=json.loads(line)
    if row['role']!='Dev' or not 2010<=row['harvest_year']<=2014:raise ValueError('Dev-only input required')
    for x,y,m in row_samples(root,row,agent,actual_train_weather=False):xs.append(x);ys.append(y);meta.append(m)
 return np.asarray(xs),np.asarray(ys),meta

def parity_features(x,track):
 out=np.array(x,copy=True)
 if track=='Sensorless':out[:,[1,2,4]]=0.
 elif track!='Full-Telemetry':raise ValueError('Unknown parity track')
 return out
