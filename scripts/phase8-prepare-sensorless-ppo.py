"""TRAIN-only causal model-assisted PPO tables, no evaluation books or physics."""
from pathlib import Path
from datetime import date
import hashlib,json,time
import numpy as np,joblib,torch
from pcse_gym.agromas_v6.books import load_train
from pcse_gym.agromas_v8.joint_model import FrozenJointWorldModel
from pcse_gym.agromas_v8.tree_weather import TreeClimateForecastAgent
from pcse_gym.agromas_v8.book_policy import stats_from_members
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';D=R/'cache/phase8-train-arrays';O=R/'cache/phase8-ppo-inputs.joblib'
if __name__=='__main__':
 assert not O.exists();torch.set_num_threads(2);data=load_train(R);x=np.load(D/'x.npy');meta=json.loads((D/'meta.json').read_text());world={k:i for i,k in enumerate(data.keys)};unique={}
 for i,m in enumerate(meta):unique.setdefault((m['region'],m['year'],m['climate'],m['stage'],tuple(m['plan'][:m['stage']-1])),i)
 groups={}
 for key,i in unique.items():
  m=meta[i];groups.setdefault((m['region'],m['year'],m['climate'],m['as_of']),[]).append((key,i))
 model=FrozenJointWorldModel(R,'Sensorless','MLP',device='cuda');tables={};tick=time.monotonic()
 for (region,year,climate,day),items in groups.items():
  # Training a policy may not exploit its own archived future-weather block.
  forecaster=TreeClimateForecastAgent(R,tuple(y for y in range(1995,2010) if y!=year));desc,w,_,_,_=forecaster.tree(region,day,climate);branch=np.minimum(np.searchsorted(np.cumsum(w),(np.arange(32)+.5)/32),len(w)-1)
  batch=[];records=[]
  for key,i in items:
   m=meta[i];stage=m['stage'];base=x[i].copy();base[[1,2,4]]=0;base[10:15]=0;legal=base[3]+np.array([0,10,20,40,60,80,100])<=220+1e-8;indices=[]
   for a,dose in enumerate([0,10,20,40,60,80,100]):
    if not legal[a]:continue
    z=base.copy();z[22:25]=0;z[22+stage-1]=dose;remaining=220-base[3]-dose
    for s in range(stage,3):
     future=max(v for v in [0,10,20,40,60,80] if v<=remaining+1e-8);z[22+s]=future;remaining-=future
    indices.append((a,len(batch)));batch.append(z)
   score,applicable=model.applicability(base[None]);records.append((key,i,legal,indices,applicable,base))
  responses=model.response_tensor(np.asarray(batch),desc);marginal=responses[:,branch,np.arange(32)];statistics=stats_from_members(marginal,model.radius)
  for key,i,legal,indices,applicable,base in records:
   region,year,climate,stage,prefix=key;index=sum([int(np.flatnonzero(np.array([0,10,20,40,60,80,100])==v)[0])*factor for v,factor in zip(prefix,[49,7])]);stats=np.zeros((7,12))
   for a,j in indices:stats[a]=statistics[j]
   tables[(world[(region,year,climate)],stage,index//(7**(4-stage)))]=dict(base=base[:22],stats=stats,legal=legal,applicable=applicable)
  print(json.dumps({'groups_done':len({k[0] for k in tables}),'tables':len(tables),'region':region,'year':year}),flush=True)
 assert len(tables)==10980
 assert all(not v['base'][[1,2,4]].any() for v in tables.values())
 joblib.dump((data,tables),O,compress=3);O.chmod(0o444)
 (P/'phase8b-PPO-inputs-freeze.json').write_text(json.dumps({'source':'TRAIN1995-2009physicalbooks,currentprefixonly,forecastanalogsexcludeepisodeyear','tables':len(tables),'observation_dim':91,'hidden_telemetry_zero':True,'elapsed_seconds':time.monotonic()-tick,'cache_path':str(O.relative_to(R)),'cache_sha256':hashlib.sha256(O.read_bytes()).hexdigest(),'tool_calibration':'frozenG1Devcalibration;rewardsandpolicyfitlabelsTRAINonly','policy_hyperparameters':'samev6:151552decisionstepsperseed,seeds4/17/29,8env,64x64,finalfixedbudget'},indent=2))
