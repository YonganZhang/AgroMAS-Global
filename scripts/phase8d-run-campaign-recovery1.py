"""Append-only authorized Phase8C native campaign; halt on any failure.

No automatic retries. No new labels are inspected for selection or tuning.
A reused record is referenced by verified config/content hash, never rewritten.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import OrderedDict
import argparse,hashlib,json,os,subprocess,sys
import numpy as np,joblib,torch
from pcse_gym.agromas_v8.joint_model import FrozenJointWorldModel
from pcse_gym.agromas_v8.controller import FiveSpecialistTeam
from pcse_gym.agromas_v8.policies import TreePolicy,SensorlessPPOPolicy,LegacyV6Policy,FixedDosePolicy
from pcse_gym.agromas_v8.referee import run_episode,prepare_daily_outputs
from pcse_gym.agromas_v8.trajectory_cache import NativeWorldCache
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';D=R/'data/phase8d-evaluation';PERMIT=P/'phase8d-evaluation-permit-recovery1.json';DESIGN=P/'phase8d-frozen-cases-v4.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 permit=json.loads(PERMIT.read_text());assert sha(PERMIT)==PERMIT.with_suffix('.sha256').read_text().strip()
 from pcse_gym.agromas.regions import frozen_asset_sha
 for path,digest in permit['files'].items():assert frozen_asset_sha(R/path)==digest,path
 for path,digest in json.loads((P/'phase8d-readonly-dependencies.json').read_text()).items():assert frozen_asset_sha(R/path)==digest,path
 assert subprocess.check_output(['git','-C',str(R/'pcse'),'rev-parse','HEAD'],text=True).strip()=='d1fe6d29de828033b850ec51d994988d8d6d406f'
 assert not subprocess.check_output(['git','-C',str(R/'pcse'),'status','--porcelain'],text=True).strip()
 return permit
class PriorPolicy(TreePolicy):
 def choose(self,state,history,case):
  self.adapter_context={'prior_id':f"{case['region']}:{case['year']-1}",'as_of':state['as_of']}
  return super().choose(state,history,case)
def worker(index,count):
 torch.set_num_threads(2);verify();cases=json.loads(DESIGN.read_text())['cases'];teams=OrderedDict();legacy={};ppos={}
 def team(track,family,case=None):
  tag=None if case is None else (case['scheme'],f"{case['region']}-{case['year']}" if case['scheme']=='LOYO' else case['fold'],case['policy'][3:]);key=(track,family,tag)
  if key not in teams:
   m=FrozenJointWorldModel(R,track,family,device='cuda:0')
   if tag:
    scheme,fold,variant=tag;m._adapter=joblib.load(R/f'models/phase8d-controls/p2-adapters/{scheme}-{fold}/{variant}.joblib');m.adapter_tag=':'.join(tag)
   teams[key]=FiveSpecialistTeam(R,m)
   while len(teams)>12:teams.popitem(last=False)
  teams.move_to_end(key);return teams[key]
 groups={}
 for c in cases:
  if 'reuse' not in c:groups.setdefault((c['region'],c['year'],c['climate'],c['source']),[]).append(c)
 assert len(groups)==170
 for world_index,world in enumerate(sorted(groups)):
  if world_index%count!=index:continue
  cache=NativeWorldCache(R,world,PERMIT)
  for ref in json.loads(DESIGN.read_text())['physical_archive_index']:
   if tuple(ref['world'])==world:cache.seed_archive(R/ref['path'],ref['sha256'])
  recovery=json.loads((P/'phase8d-manual-recovery1.json').read_text())
  for c in groups[world]:
   if c['episode_id'] in recovery['completed_result_sha256']:cache.seed_archive(D/c['episode_id']/'result.json',recovery['completed_result_sha256'][c['episode_id']])
  for c in groups[world]:
   if (D/c['episode_id']/'result.json').exists():continue
   if (D/'STOP').exists():raise RuntimeError('Another worker halted the campaign; no automatic retry')
   folder=D/c['episode_id'];folder.mkdir();(folder/'claim.json').write_text(json.dumps(dict(case=c,worker=index,started=datetime.now(timezone.utc).isoformat())))
   try:
    name=c['policy'];track=c['track'];mode=c['mode']
    if name.startswith('P2-'):
     family={'Full64':'MLP','Static3':'MLP','Weather':'Weather','Linear64':'Linear','ExtraTrees64':'ExtraTrees'}[name[3:]];policy=PriorPolicy(team('Sensorless',family,c),mode=mode)
    elif name in ('LegacyV6Full','LegacyV6PPO'):
     seed=c.get('seed') if name=='LegacyV6PPO' else None
     if seed not in legacy:legacy[seed]=LegacyV6Policy(R,seed)
     policy=legacy[seed]
    elif name=='SensorlessPPO':
     seed=c['seed']
     if seed not in ppos:ppos[seed]=SensorlessPPOPolicy(R,team('Sensorless','MLP'),seed,model_dir=R/f'models/phase8c-controls/ppo-sensorless-reconstructed-seed{seed}')
     policy=ppos[seed]
    elif name=='DVS-N2':policy=FixedDosePolicy(team(track,'MLP'))
    else:
     family={'TreeMLP':'MLP','TreeWeather':'Weather','TreeExtraTrees':'ExtraTrees','TreeLinear':'Linear'}.get(name,'MLP')
     policy=TreePolicy(team(track,family),mode=mode,remove=name[7:] if name.startswith('remove-') else None)
    result=cache.run(c,policy)
    with (folder/'result.json').open('x') as f:json.dump(result,f,indent=2,default=str,allow_nan=False)
    assert result['mass_audit']['passed'],'Strict native conservation failed'
    assert len(result['mass_audit']['daily_records'])==result['mass_audit']['daily_rows']
    for file in (folder/'result.json',):file.chmod(0o444)
    (folder/'sha256').write_text(sha(folder/'result.json')+'\n');(folder/'sha256').chmod(0o444)
    print(json.dumps(dict(worker=index,world_index=world_index,episode_id=c['episode_id'],completed=True)),flush=True)
   except BaseException as e:
    (folder/'error.json').write_text(json.dumps(dict(error=repr(e),no_retry=True)));(D/'STOP').touch();raise
  world_id=hashlib.sha256(json.dumps(world).encode()).hexdigest()[:20]
  (P/'phase8d-world-receipts'/f'{world_id}.json').write_text(json.dumps(cache.receipt()|dict(worker=index,cases=len(groups[world])),indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--execute',action='store_true');a.add_argument('--resume-verified',action='store_true');a.add_argument('--worker',type=int);a.add_argument('--workers',type=int,default=16);args=a.parse_args()
 if args.worker is not None:
  assert args.execute;worker(args.worker,args.workers);raise SystemExit(0)
 design=json.loads(DESIGN.read_text())
 if not args.execute:print(json.dumps(dict(dry_run=True,total=design['total'],new=design['new_native'],reuse=design['reused'])));raise SystemExit(0)
 assert args.resume_verified,'Recovery requires an explicit manual flag';verify()
 recovery=json.loads((P/'phase8d-manual-recovery1.json').read_text())
 for episode,digest in recovery['completed_result_sha256'].items():assert sha(D/episode/'result.json')==digest
 assert not (D/'STOP').exists(),'STOP must be archived by the manual recovery audit'
 assert json.loads((P/'phase8d-root-cause-verification.json').read_text())['status']=='PRE_CAMPAIGN_PASS'
 (P/'phase8d-world-receipts').mkdir(exist_ok=True)
 prepare_daily_outputs(R);D.mkdir(exist_ok=True);(D/'claim.json').write_text(json.dumps(dict(started=datetime.now(timezone.utc).isoformat(),permit_sha256=sha(PERMIT),new=design['new_native'],reuse=design['reused'],no_automatic_retry=True)))
 for c in design['cases']:
  if 'reuse' not in c:continue
  ref=c['reuse'];source=R/ref['path'];assert sha(source)==ref['sha256'];folder=D/c['episode_id'];folder.mkdir();(folder/'reuse.json').write_text(json.dumps(ref,indent=2));(folder/'result.json').symlink_to(source);(folder/'sha256').write_text(ref['sha256']+'\n')
 processes=[]
 for i in range(args.workers):
  env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=str((0,1,5,7)[i%4]);log=(P/f'phase8d-native-recovery1-worker{i}.log').open('x');proc=subprocess.Popen([sys.executable,__file__,'--execute','--worker',str(i),'--workers',str(args.workers)],env=env,stdout=log,stderr=subprocess.STDOUT);processes.append((proc,log))
 (P/'phase8d-running-processes-recovery1.json').write_text(json.dumps(dict(parent_pid=os.getpid(),workers=[p.pid for p,_ in processes],devices=[0,1,5,7],new_native=design['new_native'],reused=design['reused']),indent=2))
 exits=[]
 for proc,log in processes:exits.append(proc.wait());log.close()
 world_receipts=[json.loads(p.read_text()) for p in (P/'phase8d-world-receipts').glob('*.json')]
 old_world_receipts=[json.loads(p.read_text()) for p in (P/'phase8d-world-receipts-attempt1').glob('*.json')]
 all_world_receipts=old_world_receipts+world_receipts
 simulated=set();actual_native=0
 for c in design['cases']:
  result=json.loads((D/c['episode_id']/'result.json').read_text())
  if not result['native_cache']['trajectory_replayed']:actual_native+=1;simulated.add((tuple(result['native_cache']['world']),tuple(result['native_cache']['executed_doses'])))
 receipt=dict(total_cases=design['total'],new_cases=design['new_native'],reused_cases=design['reused'],worlds_completed=len(world_receipts),unique_native_trajectories_simulated=len(simulated),native_simulations_including_repeated_executed_triples=actual_native,trajectory_cache_hits=design['total']-actual_native,world_receipts=world_receipts,prior_attempt_world_receipts=old_world_receipts,infrastructure_recovery=True,completed_from_prior_attempt=len(recovery['completed_result_sha256']),exit_codes=exits,expected=design['total'],new_expected=design['new_native'],reused=design['reused'],results=len(list(D.glob('*/result.json'))),no_automatic_retry=True)
 (P/'phase8d-campaign-receipt.json').write_text(json.dumps(receipt,indent=2));assert not any(exits) and receipt['results']==receipt['expected'];print(json.dumps(receipt))
