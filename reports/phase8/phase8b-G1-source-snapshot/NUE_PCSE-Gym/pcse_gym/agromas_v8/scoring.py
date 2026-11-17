"""Executed-N projection and transparent, fail-closed G1 statistics."""
import numpy as np
from pcse_gym.agromas.continuation import project_members

def project_executed_members(raw,features):
 raw=np.asarray(raw,float);features=np.asarray(features,float)
 if raw.ndim!=3 or raw.shape[-1]!=3:raise ValueError('Joint Yield/GrainN/ExecutedN required')
 if not np.isfinite(raw).all():raise ValueError('Non-finite prediction')
 if len(features)!=len(raw):raise ValueError('Batch mismatch')
 # Projection API has a candidate-dose lower bound. Actual execution is uncertain:
 # a separate bound copy encodes committed N only, NOT a nominal future dose.
 committed_n_projection_bound=np.zeros((len(features),5));committed_n_projection_bound[:,3]=features[:,3]
 raw=np.array(raw,copy=True)
 nominal_remaining_sum=features[:,22:25].sum(axis=1)
 if np.any(nominal_remaining_sum<0) or np.any(features[:,3]+nominal_remaining_sum>220+1e-8):raise ValueError("Illegal nominal remaining schedule")
 raw[...,2]=np.minimum(raw[...,2],np.minimum(220.,features[:,3]+nominal_remaining_sum)[:,None])
 prediction=np.concatenate([raw,np.full(raw.shape[:-1]+(1,),3.5)],axis=-1)
 return project_members(prediction,committed_n_projection_bound,budget=220.)

def brier(probability,truth):
 p=np.asarray(probability,float);y=np.asarray(truth,float)
 if p.shape!=y.shape or not np.isfinite(p).all() or np.any((p<0)|(p>1)):raise ValueError('Probability contract')
 return float(np.mean((p-y)**2))

def bss(candidate,reference):
 if not np.isfinite([candidate,reference]).all() or reference<=0:raise ValueError('Undefined Brier skill')
 return float(1-candidate/reference)

def conformal_radius(scores,alpha=.1):
 scores=np.asarray(scores,float)
 if scores.ndim!=1 or len(scores)==0 or not np.isfinite(scores).all():raise ValueError('Conformal scores contract')
 if not 0<alpha<1:raise ValueError('Invalid conformal alpha')
 rank=int(np.ceil((len(scores)+1)*(1-alpha)))
 return float(np.sort(scores)[rank-1]) if rank<=len(scores) else float('inf')

def ranking_regret(meta,predicted_value,real_value,*,macro=False):
 groups={}
 for i,m in enumerate(meta):groups.setdefault(m['prefix'],[]).append(i)
 regrets=[];world_stage={}
 for ids in groups.values():
  if len(ids)<2:continue
  ix=np.asarray(ids);choice=ix[np.argmax(np.asarray(predicted_value)[ix])]
  regret=float(np.max(np.asarray(real_value)[ix])-real_value[choice]);regrets.append(regret)
  if macro:
   m=meta[ids[0]];world_stage.setdefault((m["region"],m["year"],m["stage"]),[]).append(regret)
 if not regrets:raise ValueError('No rankable candidate prefixes')
 value=np.mean([np.mean(v) for v in world_stage.values()]) if macro else np.mean(regrets)
 return float(value),len(regrets)

def utility(members):return (200*members[...,0]-1.5*members[...,4]).mean(axis=-1)
