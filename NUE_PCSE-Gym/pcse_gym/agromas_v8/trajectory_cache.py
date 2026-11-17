"""Exact per-world native trajectory reuse with case-local policy decisions.

Only public decision prefixes recorded by a real run_episode are replayed.
Unknown action paths invoke the unchanged external native referee. A replay
never substitutes a policy trace: each policy independently chooses every dose.
Full requested-action paths include timestamps/defer flags; this also retains
case-specific scheduler events when a proposed dose misses a native window.
"""
import hashlib,json
import numpy as np
from pcse_gym.agromas.climate_agent import WeatherHistory
from .referee import run_episode,decision_trace


def _state_equal(a,b):
 return json.dumps(a,sort_keys=True,default=str)==json.dumps(b,sort_keys=True,default=str)

def _history_equal(a,b):
 return a.dates==b.dates and a.region_id==b.region_id and a.source_id==b.source_id and np.array_equal(a.values,b.values)

def _action(fields,decision):
 defer=bool(decision.get('defer',False));dose=0. if defer else float(decision['dose'])
 if dose not in (0,10,20,40,60,80,100) or dose>220-fields['n_fert_cum']+1e-8:raise ValueError('Policy structural action violation')
 return (int(fields['stage']),str(fields['as_of']),dose,defer)

def _trace(fields,decision):return decision_trace(fields,decision,_action(fields,decision)[2])


class NativeWorldCache:
 """One serial worker owns each world; no engine object ever enters a policy."""
 def __init__(self,root,world,permit):
  self.root=root;self.world=tuple(world);self.permit=permit;self.nodes={};self.terminals={};self.physical_digests={};self.executed={};self.role=None;self.native_simulations=0;self.replayed_cases=0;self.prefix_decisions_replayed=0;self.archived_records=0;self.archive_paths=0;self.simulated_doses=set()
 def seed_archive(self,path,expected_sha256):
  """Import verified terminal physics, never old policy decisions or telemetry.

  Public prefix nodes remain empty until recovered by a real native run. A
  terminal is usable only after the new policy independently reaches its exact
  dated requested-action path through those native public prefix nodes.
  """
  raw=path.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=expected_sha256:raise ValueError('Archive content hash mismatch')
  result=json.loads(raw);self._check_world(result['case']);audit=result['mass_audit']
  if not audit['passed']:raise ValueError('Archive mass audit failed')
  daily=audit.get('daily_records')
  if not daily or len(daily)!=audit['daily_rows']:return False
  if any(not np.isfinite([d['N_residual_kg_ha'],d['C_residual_kg_ha']]).all() or abs(d['N_residual_kg_ha'])>=1e-10 or abs(d['C_residual_kg_ha'])>=1e-9 for d in daily):raise ValueError('Archive daily conservation failed')
  prefix=tuple((int(t['stage']),str(t['as_of']),float(t['dose']),bool(t.get('deferred',False))) for t in result['trace'])
  if not prefix:return False
  physical={k:v for k,v in result.items() if k not in ('case','trace','joint','partial_profit','NUE_compliant','surplus_compliant','native_cache')}
  fingerprint=hashlib.sha256(json.dumps({k:v for k,v in physical.items() if k!='events'},sort_keys=True,default=str,allow_nan=False).encode()).hexdigest()
  if 'native_cache' in result and result['native_cache']['physical_sha256']!=fingerprint:raise ValueError('Archive physical digest mismatch')
  if prefix in self.physical_digests and self.physical_digests[prefix]!=fingerprint:raise ValueError('Archive dated-path physics mismatch')
  doses=tuple(sum(e['dose'] for e in result['events'] if e['stage']==stage) for stage in (1,2,3))
  if doses in self.executed and self.executed[doses]!=fingerprint:raise ValueError('Archive dose triple physics mismatch')
  self.executed[doses]=fingerprint;self.archived_records+=1
  if prefix not in self.terminals:self.terminals[prefix]=physical;self.physical_digests[prefix]=fingerprint;self.archive_paths+=1
  return True
 def _check_world(self,case):
  actual=(case['region'],case['year'],case.get('climate','Historical'),case.get('source','NASA'))
  if actual!=self.world:raise ValueError('Cross-world physical cache access')
  if self.role is None:self.role=case.get('role')
  elif self.role!=case.get('role'):raise ValueError('Cross-role physical cache access')
 def run(self,case,policy):
  self._check_world(case);prefix=();prepared=[];trace=[]
  # Decisions are recomputed using this case's own price/cap/mode/seed/track.
  # A stateful open-loop policy thus advances exactly once at each query.
  while prefix not in self.terminals and prefix in self.nodes:
   fields,history=self.nodes[prefix];decision=policy.choose(dict(fields),history,case);action=_action(fields,decision);prepared.append(decision);trace.append(_trace(fields,decision));prefix+=action,
  if prefix in self.terminals:
   self.replayed_cases+=1;self.prefix_decisions_replayed+=len(prepared)
   return self._compose(self.terminals[prefix],case,trace,True,prefix)
  cache=self
  class Recorder:
   def __init__(self):self.prefix=();self.index=0
   def choose(self,fields,history,c):
    if self.prefix in cache.nodes:
     saved_fields,saved_history=cache.nodes[self.prefix]
     if not _state_equal(saved_fields,fields) or not _history_equal(saved_history,history):raise ValueError('Native public-prefix replay mismatch')
    else:
     values=history.values.copy();values.setflags(write=False)
     cache.nodes[self.prefix]=(dict(fields),WeatherHistory(history.dates,values,history.region_id,history.source_id))
    if self.index<len(prepared):decision=prepared[self.index]
    else:decision=policy.choose(fields,history,c)
    self.index+=1;self.prefix+=_action(fields,decision),
    return decision
  recorder=Recorder();result=run_episode(self.root,case,recorder,self.permit);self.native_simulations+=1
  if not result['mass_audit']['passed']:raise ValueError('Native conservation failed before cache insertion')
  physical={k:v for k,v in result.items() if k not in ('case','trace','joint','partial_profit','NUE_compliant','surplus_compliant')}
  self.terminals[recorder.prefix]=physical
  # Native physics is checked on repeated executed-dose triples. Scheduler
  # event reason/date metadata is intentionally kept per requested-action path.
  doses=tuple(sum(e['dose'] for e in result['events'] if e['stage']==stage) for stage in (1,2,3))
  fingerprint=hashlib.sha256(json.dumps({k:v for k,v in physical.items() if k!='events'},sort_keys=True,default=str,allow_nan=False).encode()).hexdigest()
  if doses in self.executed and self.executed[doses]!=fingerprint:raise ValueError('Executed dose triple has nonidentical native physics; enlarge cache key')
  self.executed[doses]=fingerprint;self.simulated_doses.add(doses)
  self.physical_digests[recorder.prefix]=fingerprint
  self.prefix_decisions_replayed+=len(prepared)
  return self._compose(physical,case,result['trace'],False,recorder.prefix)
 def _compose(self,physical,case,trace,reused,prefix):
  outcome=physical['outcome'];cap=case.get('cap',40.);joint=bool(.5<=outcome[3]<=.9 and 0<=outcome[2]<=cap)
  result=dict(physical,case=case,trace=trace,joint=joint,NUE_compliant=bool(.5<=outcome[3]<=.9),surplus_compliant=bool(0<=outcome[2]<=cap),partial_profit=float(200*outcome[0]-1.5*case.get('price_multiplier',1)*outcome[4]+case.get('subsidy',0)*joint-case.get('tax',0)*max(outcome[2],0)))
  result['native_cache']=dict(trajectory_replayed=reused,executed_doses=[sum(e['dose'] for e in physical['events'] if e['stage']==stage) for stage in (1,2,3)],physical_sha256=self.physical_digests[prefix],world=list(self.world),requested_action_path_sha256=hashlib.sha256(json.dumps(prefix,sort_keys=True).encode()).hexdigest(),source='realWOFOST81-SNOMIN',every_case_policy_decision_recomputed=True)
  return result
 def receipt(self):
  return dict(world=list(self.world),native_simulations=self.native_simulations,unique_native_executed_trajectories=len(self.simulated_doses),unique_executed_trajectories=len(self.executed),executed_trajectory_sha256=[dict(doses=list(k),sha256=v) for k,v in self.executed.items()],complete_requested_paths=len(self.terminals),cases_replayed=self.replayed_cases,public_prefix_nodes=len(self.nodes),prefix_decisions_replayed=self.prefix_decisions_replayed,archived_records_verified=self.archived_records,archived_requested_paths=self.archive_paths)
