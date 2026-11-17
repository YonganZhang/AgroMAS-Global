"""Protocol-locked retrospective P2 outer-training inputs, never online labels."""
from pathlib import Path
from datetime import date
import json,hashlib,time
import numpy as np,joblib,pandas as pd,torch
from pcse_gym.agromas_v8.online_features import public_state,candidate_features,history_from_provider
from pcse_gym.agromas_v8.tree_weather import TreeClimateForecastAgent
from pcse_gym.agromas_v8.joint_model import FrozenJointWorldModel
from pcse_gym.agromas.season import regional_weather
R=Path(__file__).resolve().parents[1];O=R/'cache/phase8-p2-adapter-inputs';P=R/'reports/phase8'
if __name__=='__main__':
 if O.exists():raise ValueError('Exclusive preparation claim: preserve existing inputs')
 O.mkdir();torch.set_num_threads(2)
 protocol=P/'phase8b-g2-g3-implementation-contract.md';(O/'protocol.sha256').write_text(hashlib.sha256(protocol.read_bytes()).hexdigest())
 cohort=json.loads((P/'phase8b-P2-metadata-cohort.json').read_text())['rows'];keys={(v['region'],v['year']) for v in cohort};X=[];Y=[];C=[];world=[];groups=[];offset=0
 a=pd.read_csv(R/'reports/phase7/station-mean-64d-v7.csv');priors={}
 for row in a.itertuples():priors[f'{row.region}:{int(row.embedding_year)}']=(np.array([getattr(row,f'A{j:02}') for j in range(64)]),f'{int(row.embedding_year)}-12-31')
 for file in sorted((R/'data/phase5-final-evaluation-books-v4').glob('*-Historical*.jsonl')):
  rows=[json.loads(line) for line in file.open()];first=rows[0];key=first['region_id'],int(first['harvest_year'])
  if key not in keys:continue
  prefixgroups={}
  for row in rows:
   if sum(row['plan'])>220:continue
   for stage in (1,2,3):
    if str(stage) not in row['states']:continue
    state=row['states'][str(stage)].copy()
    if state['n_fert_cum']+sum(row['plan'][stage-1:])>220+1e-8:continue
    day=date.fromisoformat(state['as_of']);past=[date.fromisoformat(e['date']) for e in row['events'] if e['dose']>0 and date.fromisoformat(e['date'])<=day];state['days_since_last_fert']=min(60,(day-max(past)).days) if past else 60
    prefix=tuple(row['plan'][:stage-1]);prefixgroups.setdefault((stage,prefix,state['as_of']),[]).append((state,row))
  for (stage,prefix,day),items in prefixgroups.items():
   provider=regional_weather(str(R),key[0],'v2');history=history_from_provider(provider,key[0],date.fromisoformat(day));states=[public_state(s,'Sensorless') for s,r in items];plans=np.array([np.r_[np.zeros(stage-1),r['plan'][stage-1:]] for s,r in items]);xx=candidate_features(R,states[0],plans,history=history)
   assert not xx[:,[1,2,4]].any() and not xx[:,10:15].any()
   X.extend(xx);Y.extend([np.array(r['outcome'])[[0,1,4]] for s,r in items]);C.extend([(f'{key[0]}:{key[1]-1}',day)]*len(items));world.extend([f'{key[0]}:{key[1]}']*len(items));groups.append(dict(start=offset,end=offset+len(items),region=key[0],year=key[1],day=day));offset+=len(items)
  print(json.dumps(dict(world=key,rows=offset)),flush=True)
 assert len(set(world))==44
 np.save(O/'x.npy',np.array(X));np.save(O/'y.npy',np.array(Y));joblib.dump(dict(context=C,world=world,groups=groups,priors=priors,cohort=cohort),O/'metadata.joblib',compress=3)
 for family in ('MLP','Weather','Linear','ExtraTrees'):
  model=FrozenJointWorldModel(R,'Sensorless',family,device='cuda');raw=np.empty((len(X),32,3));climate=TreeClimateForecastAgent(R);xx=np.asarray(X)
  for group in groups:
   i,j=group['start'],group['end'];provider=regional_weather(str(R),group['region'],'v2');history=history_from_provider(provider,group['region'],date.fromisoformat(group['day']));desc,w,_,_,_=climate.tree(group['region'],group['day'],observed_history=history);branch=np.minimum(np.searchsorted(np.cumsum(w),(np.arange(32)+.5)/32),len(w)-1)
   expanded=np.repeat(xx[i:j,None,:],32,axis=1);expanded[:,:,-9:]=desc[branch][None];raw[i:j]=model.point(expanded.reshape(-1,36)).reshape(j-i,32,3)+model.residual[None]
  np.save(O/f'{family}-raw.npy',raw);print(f'{family} completed',flush=True)
 receipt={'site_years':44,'rows':len(X),'protocol_sha256':(O/'protocol.sha256').read_text(),'raw_prior_public':False,'purpose':'retrospective nested outer-fold fitting only; no online label access','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in O.iterdir() if p.is_file()}}
 (P/'phase8b-P2-adapter-inputs-freeze.json').write_text(json.dumps(receipt,indent=2))
