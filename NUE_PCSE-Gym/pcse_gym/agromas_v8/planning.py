"""Non-anticipative backward DP on explicitly coarsened observable information.

Only future7-day rainfall/temperature bins may be revealed to later decisions.
The root action is common to all weather paths; no path-specific wait-and-see
maximum. Every actual next stage re-plans; native daily guards remain external.
"""
from dataclasses import dataclass,replace
from itertools import product
from .agents import UrbanEcoSafetyAgent,SocioEconomicPolicyAgent
import numpy as np
GRID=np.array([0.,10.,20.,40.,60.,80.,100.])

def weighted_quantile(values,weights,q):
 v=np.asarray(values,float).ravel();w=np.asarray(weights,float).ravel()
 if v.shape!=w.shape or not np.isfinite(v).all() or np.any(w<0) or w.sum()<=0:raise ValueError('Weighted distribution contract')
 order=np.argsort(v,kind='stable');s=np.cumsum(w[order]);idx=min(np.searchsorted(s,q*s[-1],side='left'),len(v)-1)
 return float(v[order[idx]])

def upper_cvar(values,weights,epsilon=.1):
 v=np.asarray(values,float).ravel();w=np.asarray(weights,float).ravel();w=w/w.sum();order=np.argsort(-v,kind='stable');before=np.r_[0.,np.cumsum(w[order])[:-1]];take=np.minimum(w[order],np.maximum(epsilon-before,0.))
 return float(np.sum(take*v[order])/epsilon)

@dataclass(frozen=True)
class Regime:
 cap:float=40.
 price_multiplier:float=1.
 subsidy:float=0.
 tax:float=0.
 eco:bool=True
 econ:bool=True
 soft:bool=False
 epsilon:float=.1
 radius:float=0.
 bare_tier2:bool=False

def distribution_metrics(members,branch_weights,regime):
 m=np.asarray(members,float);prob=np.asarray(branch_weights,float);prob=prob/prob.sum()
 # Integrate every residual member for every conditional weather branch.
 if m.ndim!=3 or m.shape[0]!=len(prob) or m.shape[2]!=6 or not np.isfinite(prob).all() or np.any(prob<0):raise ValueError('Branch product distribution contract')
 flat=m.reshape(-1,6);w=np.repeat(prob,m.shape[1])/m.shape[1]
 if not np.isfinite(flat).all():raise ValueError('Non-finite world-model response')
 mean=np.sum(flat*w[:,None],axis=0);s=flat[:,2];nue=flat[:,3];joint=(s>=0)&(s<=regime.cap)&(nue>=.5)&(nue<=.9)
 q90=weighted_quantile(s,w,.9);upper95=weighted_quantile(s,w,.95)+regime.radius;cvar=upper_cvar(s,w,regime.epsilon)+max(regime.radius,0.)
 eco_safe=mean[2]>=0 and max(q90,upper95)<=regime.cap and cvar<=regime.cap
 # The agronomic corridor is imposed on the weighted forecast mean, matching
 # the declared v6 point-corridor comparator. Actual seasonal NUE is audited.
 econ_safe=.5<=mean[3]<=.9
 price=1.5*regime.price_multiplier if regime.econ else 1.5;subsidy=regime.subsidy if regime.econ else 0.;tax=regime.tax if regime.econ else 0.
 partial=float(np.sum(w*(200*flat[:,0]-price*flat[:,4]+subsidy*joint-tax*np.maximum(s,0))))
 eco_ok=((s>=0)&(s<=regime.cap)) if regime.eco else np.ones_like(s,dtype=bool)
 econ_ok=((nue>=.5)&(nue<=.9)) if regime.econ else np.ones_like(nue,dtype=bool)
 active_joint=eco_ok&econ_ok
 econ_dist=(max(.5-mean[3],0)+1.5*max(mean[3]-.9,0)) if regime.econ else 0.
 eco_dist=((max(mean[2]-(regime.cap-2.),0)+max(mean[2]-regime.cap,0)+max(-mean[2],0))/regime.cap) if regime.eco else 0.
 distance=econ_dist+eco_dist
 active_probability=float(np.sum(w*active_joint))
 composite_score=partial+(250*active_probability-300*distance if (regime.eco or regime.econ) else 0.)
 score=partial if (regime.bare_tier2 and not regime.soft) else composite_score
 return dict(mean=mean,probability=float(np.sum(w*joint)),q90=q90,conformal_upper95=float(upper95),CVaR=cvar,eco_safe=bool(eco_safe),NUE_safe=bool(econ_safe),partial_profit=partial,score=float(score),distance=float(distance),active_probability=active_probability,composite_score=float(composite_score))

def choose_tier(metrics,doses,regime,*,modular=True):
 if not metrics:raise ValueError('No structurally legal candidates')
 if regime.soft:
  first=np.ones(len(metrics),bool)
 elif modular:
  eco=UrbanEcoSafetyAgent(regime.cap);econ=SocioEconomicPolicyAgent(price_n=1.5*regime.price_multiplier,subsidy=regime.subsidy,surplus_tax=regime.tax);first=np.array([eco.allowed_metrics(m,regime) and econ.allowed_metrics(m,regime) for m in metrics])
 else:first=np.array([(not regime.eco or m['eco_safe']) and (not regime.econ or m['NUE_safe']) for m in metrics])
 second_corridor=np.array([(not regime.eco or 0.<=m['mean'][2]<=regime.cap) and (not regime.econ or m['NUE_safe']) for m in metrics])
 # Archived bare ranking retains its original relaxation comparator.
 if regime.bare_tier2:second_corridor[:]=False
 second=np.array([not regime.eco or m['mean'][2]<=regime.cap for m in metrics])
 if first.any():allowed=first;tier=1
 elif second_corridor.any():allowed=second_corridor;tier=2
 elif second.any():allowed=second;tier=2
 else:
  zero=np.flatnonzero(np.asarray(doses)==0)
  if not len(zero):raise ValueError('Operational zero absent')
  return int(zero[0]),3
 scores=np.array([m['score'] for m in metrics]);return int(np.argmax(np.where(allowed,scores,-np.inf))),tier

def legal_schedules(stage,committed):
 plans=[]
 for suffix in product(GRID,repeat=4-stage):
  p=np.r_[np.zeros(stage-1),suffix]
  if committed+p.sum()<=220+1e-8:plans.append(p)
 return np.asarray(plans,float)

def frozen_continuation_indices(plans,stage):
 plans=np.asarray(plans,float);selected=[];doses=[];available=float(plans.sum(1).max())
 for dose in sorted(set(plans[:,stage-1])):
  target=np.zeros(3);target[stage-1]=dose;remaining=available-dose
  for future in range(stage,3):
   target[future]=max(v for v in GRID if v<=min(80.,remaining)+1e-8);remaining-=target[future]
  match=np.flatnonzero(np.all(plans==target,axis=1))
  if len(match)!=1:raise ValueError('Fixed80/80 continuation absent from legal schedule set')
  selected.append(int(match[0]));doses.append(float(dose))
 return selected,doses

class CoreAgronomicAgent:
 def __init__(self,regime=Regime(),*,monolithic=False):self.regime=regime;self.monolithic=monolithic
 def choose(self,stage,plans,responses,weights,rain_bins,temp_bins,*,applicable=True,mode='tree'):
  if mode in ('soft','hard-bare-tier2','tier2-composite'):
   regime=replace(self.regime,soft=mode=='soft',bare_tier2=mode=='hard-bare-tier2')
   return CoreAgronomicAgent(regime,monolithic=self.monolithic).choose(stage,plans,responses,weights,rain_bins,temp_bins,applicable=applicable,mode='tree')
  plans=np.asarray(plans,float);responses=np.asarray(responses,float);weights=np.asarray(weights,float)
  if responses.shape!=(len(plans),len(weights),32,6):raise ValueError('Plan/branch/K32 shape contract')
  if stage not in (1,2,3) or mode not in ('tree','open-loop','greedy-frozen'):raise ValueError('Unknown planning contract')
  if not applicable:
   zero=int(np.flatnonzero(np.all(plans==0,axis=1))[0]);return dict(dose=0.,tier=3,reason='OOD_operational_zero_not_compliance',branch_plan_indices=np.full(len(weights),zero,int),metrics=None,nonanticipative=True)
  rain=np.asarray(rain_bins,int);temp=np.asarray(temp_bins,int)
  if rain.shape!=weights.shape or temp.shape!=weights.shape:raise ValueError('Information partition shape')
  root_branches=np.arange(len(weights));cache={}
  def describe(mapping,branches):return distribution_metrics(np.stack([responses[mapping[b],b] for b in branches]),weights[branches],self.regime)
  def solve(depth,eligible,branches):
   key=(depth,tuple(eligible),tuple(branches))
   if key in cache:return cache[key]
   doses=sorted(set(plans[eligible,depth]));options=[];metrics=[]
   for dose in doses:
    ix=eligible[plans[eligible,depth]==dose];mapping={}
    if depth==2:
     assert len(ix)==1
     mapping={int(b):int(ix[0]) for b in branches}
    else:
     # F2 reveals rainfall only; F3 adds temperature from the same first7days.
     # Both are available by the earliest later weekly observation; withholding
     # part of known information is conservative, never anticipative.
     labels=rain if depth==0 else rain*2+temp
     for label in sorted(set(labels[branches])):
      bs=branches[labels[branches]==label];child=solve(depth+1,ix,bs);mapping.update(child['mapping'])
    options.append(mapping);metrics.append(describe(mapping,branches))
   chosen,tier=choose_tier(metrics,doses,self.regime,modular=not self.monolithic)
   result={'mapping':options[chosen],'dose':float(doses[chosen]),'tier':tier,'metrics':metrics[chosen]};cache[key]=result;return result
  if mode=='tree':result=solve(stage-1,np.arange(len(plans)),root_branches)
  elif mode=='open-loop':
   options=[{int(b):i for b in root_branches} for i in range(len(plans))];metrics=[describe(v,root_branches) for v in options]
   # Tier fallback must offer the all-zero schedule as the operational zero.
   first=np.array([int(np.any(p)) for p in plans]);indices,tier=choose_tier(metrics,first,self.regime,modular=not self.monolithic)
   result={'mapping':options[indices],'dose':float(plans[indices,stage-1]),'tier':tier,'metrics':metrics[indices]}
  else:
   # Greedy evaluates current dose with a deterministic budget-clipped80/80
   # future continuation, not a path-specific future optimum.
   selected,doses=frozen_continuation_indices(plans,stage)
   options=[{int(b):i for b in root_branches} for i in selected];metrics=[describe(v,root_branches) for v in options];chosen,tier=choose_tier(metrics,doses,self.regime,modular=not self.monolithic);result={'mapping':options[chosen],'dose':float(doses[chosen]),'tier':tier,'metrics':metrics[chosen]}
  mapping=np.array([result['mapping'][int(b)] for b in root_branches]);return dict(dose=result['dose'],tier=result['tier'],reason='active_constraints' if result['tier']==1 else 'relaxed_upper_surplus_only' if result['tier']==2 else 'operational_zero_not_compliance',branch_plan_indices=mapping,metrics=result['metrics'],nonanticipative=True)
