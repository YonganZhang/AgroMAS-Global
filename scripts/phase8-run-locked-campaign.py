"""One exclusive native campaign; no automatic retries or label-driven tuning."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,hashlib,subprocess,os,sys
import numpy as np,joblib,torch
from pcse_gym.agromas_v8.joint_model import FrozenJointWorldModel
from pcse_gym.agromas_v8.controller import FiveSpecialistTeam
from pcse_gym.agromas_v8.policies import TreePolicy,SensorlessPPOPolicy,LegacyV6Policy,FixedDosePolicy
from pcse_gym.agromas_v8.referee import prepare_daily_outputs,run_episode,run_native_nl_reference
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';D=R/'data/phase8-locked-evaluation';PERMIT=P/'phase8b-final-evaluation-permit.json'

def execute_worker(index,count):
 torch.set_num_threads(2)
 for relative,digest in json.loads((P/'phase8b-external-inference-dependency-freeze.json').read_text()).items():
  assert hashlib.sha256((R/relative).read_bytes()).hexdigest()==digest,'External dependency drift:'+relative
 cases=json.loads((P/'phase8b-locked-campaign-cases.json').read_text())['cases'];teams={};legacy={};ppos={}
 def team(track,family):
  key=track,family
  if key not in teams:teams[key]=FiveSpecialistTeam(R,FrozenJointWorldModel(R,track,family,device='cuda:0'))
  return teams[key]
 for i,case in enumerate(cases):
  if i%count!=index:continue
  if (D/'STOP').exists():raise RuntimeError('Campaign halted by another worker; never retry silently')
  folder=D/case['episode_id'];folder.mkdir();(folder/'claim.json').write_text(json.dumps(dict(case=case,started=datetime.now(timezone.utc).isoformat(),worker=index)))
  try:
   name=case['policy'];track=case['track']
   if name in ('N2-PA-calendar','Phase4-Forest-transfer'):result=run_native_nl_reference(R,case,PERMIT)
   else:
    if name.startswith('P2-'):
     variant=name[3:];family={'Full64':'MLP','Static3':'MLP','Weather':'Weather','Linear64':'Linear','ExtraTrees64':'ExtraTrees'}[variant]
     model=FrozenJointWorldModel(R,'Sensorless',family,device='cuda:0');model._adapter=joblib.load(R/f"models/phase8-controls/p2-adapters/{case['scheme']}-{case['fold']}/{variant}.joblib");model.adapter_tag=case['scheme']+':'+case['fold']+':'+variant;current=FiveSpecialistTeam(R,model)
     # Context contains only opaque prior ID/current timestamp. The private
     # encoder resolves numeric vectors; no specialist receives raw64 values.
     class PriorPolicy(TreePolicy):
      def choose(self,state,history,c):
       self.adapter_context={'prior_id':f"{c['region']}:{c['year']-1}",'as_of':state['as_of']};return super().choose(state,history,c)
     policy=PriorPolicy(current)
    elif name=='LegacyV6Full' or name=='LegacyV6PPO':
     key=case.get('seed') if name=='LegacyV6PPO' else None
     if key not in legacy:legacy[key]=LegacyV6Policy(R,key)
     policy=legacy[key]
    elif name=='SensorlessPPO':
     seed=case['seed']
     if seed not in ppos:ppos[seed]=SensorlessPPOPolicy(R,team('Sensorless','MLP'),seed)
     policy=ppos[seed]
    elif name in ('DVS-N2','N2-PA-matched'):policy=FixedDosePolicy(team(track,'MLP'),calendar=name=='N2-PA-matched')
    else:
     family={'TreeMLP':'MLP','TreeWeather':'Weather','TreeExtraTrees':'ExtraTrees','TreeLinear':'Linear'}.get(name,'MLP');policy=TreePolicy(team(track,family),mode=name if name in ('soft','open-loop','greedy-frozen') else 'tree',remove=name[7:] if name.startswith('remove-') else None)
    result=run_episode(R,case,policy,PERMIT)
   with (folder/'result.json').open('x') as stream:json.dump(result,stream,indent=2,default=str,allow_nan=False)
   if not result['mass_audit']['passed']:raise RuntimeError('Saved native result failed strict daily mass bounds')
   (folder/'sha256').write_text(hashlib.sha256((folder/'result.json').read_bytes()).hexdigest());print(json.dumps(dict(worker=index,index=i,id=case['episode_id'],completed=True)),flush=True)
  except BaseException as error:
   (folder/'error.json').write_text(json.dumps(dict(error=repr(error),no_retry=True)));(D/'STOP').touch();raise

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--worker',type=int);parser.add_argument('--workers',type=int,default=8);args=parser.parse_args()
 if args.worker is not None:execute_worker(args.worker,args.workers);raise SystemExit(0)
 if D.exists():raise ValueError('Exclusive campaign already claimed; preserve results and do not rescore')
 assert PERMIT.exists() and hashlib.sha256(PERMIT.read_bytes()).hexdigest()==PERMIT.with_suffix('.sha256').read_text().strip()
 from pcse_gym.agromas.regions import load_split_manifest,authorize_year
 frozen_cases=json.loads((P/'phase8b-locked-campaign-cases.json').read_text())['cases'];first=frozen_cases[0]
 authorize_year(load_split_manifest(R/'reports/phase5/global-date-split-manifest.json'),first['region'],first['year'],first['role'],permit_path=PERMIT,project_root=R)
 for relative,digest in json.loads((P/'phase8b-external-inference-dependency-freeze.json').read_text()).items():assert hashlib.sha256((R/relative).read_bytes()).hexdigest()==digest,'Preflight external dependency drift:'+relative
 for record in json.loads((P/'phase8b-P2-adapter-training-freeze.json').read_text())['fits']:
  path=R/f"models/phase8-controls/p2-adapters/{record['scheme']}-{record['held']}/{record['variant']}.joblib";assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256'];joblib.load(path)
 for device in (0,1,5,7):
  env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=str(device);subprocess.run([sys.executable,'-c','import torch; assert torch.cuda.is_available(); assert torch.ones(1,device="cuda").item()==1'],env=env,check=True,stdout=subprocess.DEVNULL)
 prepare_daily_outputs(R)
 (P/'phase8b-campaign-preflight.json').write_text(json.dumps(dict(passed=True,permit_hash_verified=True,all_source_models_and_external_hashes_verified=True,adapters_loaded=70,CUDA_devices=[0,1,5,7],native_physics_runs=0,claim_created_after_preflight=True),indent=2))
 D.mkdir();(D/'campaign-claim.json').write_text(json.dumps(dict(started=datetime.now(timezone.utc).isoformat(),permit_sha256=hashlib.sha256(PERMIT.read_bytes()).hexdigest(),single_pass=True)))
 workers=[];devices=[0,1,5,7]
 for index in range(args.workers):
  env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=str(devices[index%len(devices)]);log=(P/f'phase8b-native-worker{index}.log').open('x');proc=subprocess.Popen([sys.executable,__file__,'--worker',str(index),'--workers',str(args.workers)],env=env,stdout=log,stderr=subprocess.STDOUT);workers.append((proc,log))
 exits=[]
 for proc,log in workers:exits.append(proc.wait());log.close()
 results=list(D.glob('*/result.json'));receipt=dict(exit_codes=exits,result_count=len(results),expected=len(json.loads((P/'phase8b-locked-campaign-cases.json').read_text())['cases']),single_pass=True,no_automatic_retry=True)
 (P/'phase8b-native-campaign-receipt.json').write_text(json.dumps(receipt,indent=2));assert not any(exits) and receipt['result_count']==receipt['expected'];print(json.dumps(receipt),flush=True)
