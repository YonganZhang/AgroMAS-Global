"""Freeze the authorized adaptive-reused supplement and full180factorial.

This script enumerates configurations only. It never inspects new outcomes or
fits models. The archived2017seasons remain immutable; reuse is explicit.
"""
from pathlib import Path
from itertools import product
from collections import Counter
import hashlib,json
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(c):
 d={k:v for k,v in c.items() if k not in ('episode_id','benchmark','cohort','phase8c_groups','reuse')}
 d.setdefault('climate','Historical');d.setdefault('mode','tree')
 return d
if __name__=='__main__':
 dest=P/'phase8c-frozen-cases-v3.json';assert not dest.exists(),'Never overwrite frozen design'
 old=json.loads((P/'phase8b-locked-campaign-cases.json').read_text())['cases']
 worlds={}
 for c in old:
  if c['benchmark'] in ('P1','P1-WUR'):
   d={k:v for k,v in c.items() if k not in ('episode_id','policy','track','seed')};d.update(cap=40.,price_multiplier=1.,subsidy=0.,tax=0.);worlds[(c['region'],c['year'],c['source'])]=d
 assert len(worlds)==66
 assert all((b['cap'],b['price_multiplier'],b['subsidy'],b['tax'])==(40.,1.,0.,0.) for b in worlds.values())
 cases={}
 def add(base,policy='TreeMLP',track='Sensorless',mode='tree',group='P1',**extra):
  c=base|dict(policy=policy,track=track,mode=mode,climate='Historical')|extra
  if policy=='SensorlessPPO':c['ppo_checkpoint']='phase8c-train-reconstruction-v1'
  key=json.dumps(canonical(c),sort_keys=True)
  if key not in cases:
   c['episode_id']=hashlib.sha256(key.encode()).hexdigest()[:20];c['phase8c_groups']=[];cases[key]=c
  if group not in cases[key]['phase8c_groups']:cases[key]['phase8c_groups'].append(group)
 for b in worlds.values():
  for track,mode in product(('Sensorless','Full-Telemetry'),('soft','tree','hard-bare-tier2')):add(b,track=track,mode=mode)
  # All matched baseline seeds remain visible, never independent farm replicates.
  add(b,'LegacyV6Full','Full-Telemetry');add(b,'DVS-N2','Full-Telemetry')
  for seed in (4,17,29):add(b,'SensorlessPPO',seed=seed);add(b,'LegacyV6PPO','Full-Telemetry',seed=seed)
  if b['source']!='NASA':continue
  for track,mode in product(('Sensorless','Full-Telemetry'),('soft','tree')):
   for policy in ('TreeWeather','TreeExtraTrees','TreeLinear'):add(b,policy,track,mode,group='G3-A')
   for solver in ('open-loop','greedy-frozen'):add(b,track=track,mode=solver,group='G3-B')
   # Climate removal uses the already TRAIN-quantile-selected extreme subset.
   extreme=json.loads((P/'phase8b-locked-campaign-cases.json').read_text())['extreme_cohort']
   if any(e['region']==b['region'] and e['year']==b['year'] for e in extreme):add(b,'remove-climate',track,mode,group='G3-C-climate')
   for cap in (25.,35.,40.):
    add(b|dict(cap=cap),track=track,mode=mode,group='G3-C-eco-control')
    add(b|dict(cap=cap),'remove-eco',track,mode,group='G3-C-eco')
   for regime in (dict(price_multiplier=2.),dict(subsidy=50.)):
    add(b|regime,track=track,mode=mode,group='G3-C-econ-control');add(b|regime,'remove-econ',track,mode,group='G3-C-econ')
 # P2 is explicitly retrospective nested evaluation with unchanged outer adapters.
 p2={}
 for c in old:
  if c['benchmark']=='P2':p2[(c['region'],c['year'],c['scheme'],c['policy'])]={k:v for k,v in c.items() if k not in ('episode_id','policy','track')}
 for (_,_,_,policy),b in p2.items():
  for mode in ('soft','tree'):add(b,policy,mode=mode,group='P2')
 assert len(p2)==440
 stressworlds=[b for b in worlds.values() if b['source']=='NASA' and b['cohort']=='Former-Held-Out'];assert len(stressworlds)==52
 cells=set();subset=set()
 for b,climate,cap,policyregime in product(stressworlds,('Historical','idealized_mid','idealized_high'),(25.,35.,40.,50.),('standard','price2','sub50')):
  b=b|dict(cap=cap,price_multiplier=2. if policyregime=='price2' else 1.,subsidy=50. if policyregime=='sub50' else 0.)
  cell=(b['region'],climate,cap,policyregime);cells.add(cell)
  if cap in (25.,35.,50.) and policyregime!='sub50':subset.add(cell)
  for mode in ('soft','tree'):add(b,mode=mode,group='Q8.4',climate=climate)
  for policy,track in [('LegacyV6Full','Full-Telemetry'),('DVS-N2','Full-Telemetry')]:add(b,policy,track,group='Q8.4',climate=climate)
  for seed in (4,17,29):add(b,'SensorlessPPO',seed=seed,group='Q8.4',climate=climate)
 assert len(cells)==180 and len(subset)==90
 # Frozen TRAIN subsidy diagnostic grid: diagnostics, not new policy selection.
 # Full180already contains cap40/sub0and50 for everyclimate. Add100/150/200.
 for b,climate,sigma in product(stressworlds,('Historical','idealized_mid','idealized_high'),(0.,50.,100.,150.,200.)):
  for mode in ('soft','tree'):add(b|dict(subsidy=sigma),mode=mode,climate=climate,group='subsidy-diagnostic')
 # Explicit archived equivalence classes. No renamed score mode masquerades
 # as a new physical season. Read-only hash checks attach original source.
 archived={}
 for c in old:
  c=dict(c);name=c['policy']
  if name=='TreeMLP':c['mode']='hard-bare-tier2'
  elif name in ('soft','open-loop','greedy-frozen'):
   if name!='soft':continue # repaired initial composite search changes behavior
   c['policy']='TreeMLP';c['mode']=name
  elif name.startswith('P2-') or name.startswith('remove-') or name in ('TreeWeather','TreeExtraTrees','TreeLinear'):continue
  else:c['mode']='tree'
  archived[json.dumps(canonical(c),sort_keys=True)]=c
 preserved={}
 receipt=json.loads((P/'phase8b-combined-campaign-receipt.json').read_text())
 for key,c in cases.items():
  if key not in archived:continue
  oldcase=archived[key];file=R/'data/phase8-combined-evaluation'/oldcase['episode_id']/'result.json';digest=sha(file)
  prior=receipt['files'][oldcase['episode_id']];expected=prior['sha256']
  assert digest==expected
  c['reuse']=dict(archived_episode_id=oldcase['episode_id'],path=str(file.relative_to(R)),sha256=digest,configuration_sha256=hashlib.sha256(key.encode()).hexdigest(),equivalence='Historical inputs unchanged; soft composite unchanged with both specialists active; explicit bare mode restores archived score; matched baseline historical behavior unchanged')
  preserved[oldcase['episode_id']]=digest
 assert all((c['cap'],c['price_multiplier'],c['subsidy'],c['tax'])==(40.,1.,0.,0.) for c in cases.values() if 'P1' in c['phase8c_groups'])
 assert all(c['subsidy']==0. for c in cases.values() if c['price_multiplier']==2. and any(g.startswith('G3-') for g in c['phase8c_groups']))
 result=dict(design_version=3,supersedes='v1worldbasefixedinv2;v3versionsreconstructedPPOandremoves198archivedPPOreuse;no locked runs yet',cases=list(cases.values()),total=len(cases),new_native=sum('reuse' not in c for c in cases.values()),reused=sum('reuse' in c for c in cases.values()),factorial_cells=[list(c) for c in sorted(cells)],canonical90_cells=[list(c) for c in sorted(subset)],group_memberships=dict(Counter(g for c in cases.values() for g in c['phase8c_groups'])),stress_track='Sensorless primary;Full-Telemetry legacy/fixed comparators separately labelled',policy_seeds=[4,17,29],primary_mode='soft',sensitivity_mode='tree',scoring_repair='post-Phase8B-outcome-authorized adaptive-reused evaluation; no new blind-test claim',model_fits=0,subsidy_grid_TRAIN_frozen=[0,50,100,150,200],P2='retrospective nested;40Former/4Public;LOYO/LORO never pooled',no_success_assumed=True)
 with dest.open('x') as f:json.dump(result,f,indent=2)
 dest.chmod(0o444);print(json.dumps({k:v for k,v in result.items() if k not in ('cases','factorial_cells','canonical90_cells')}))
