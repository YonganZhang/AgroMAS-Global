"""Explicitly approved append-only recovery; default is a non-mutating dry-run.

Keep all original6completed episodes and both failure records. A restarts only
2incomplete seasons and continues2009unstarted cases; C omits failed seasons.
Never infer approval from elapsed time or this script's existence.
"""
from pathlib import Path
import argparse,json,hashlib,importlib.util,subprocess,os,sys,shutil
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';OLD=R/'data/phase8-locked-evaluation'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def module():
 spec=importlib.util.spec_from_file_location('original_locked_worker',R/'scripts/phase8-run-locked-campaign.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--choice',choices=['A','C'],default='A');parser.add_argument('--execute',action='store_true');parser.add_argument('--approval-file',type=Path);parser.add_argument('--worker',type=int);args=parser.parse_args();plan=json.loads((P/'phase8b-proposed-recovery-manifest.json').read_text());out=P/'recovery1';data=R/'data/phase8-locked-recovery1';permit=out/'phase8b-recovery-permit.json'
 if args.worker is not None:
  assert args.execute and permit.is_file();m=module();m.P=out;m.D=data;m.PERMIT=permit;m.execute_worker(args.worker,8);raise SystemExit(0)
 todo=plan['unstarted']+([r['case'] for r in plan['failed']] if args.choice=='A' else []);ids={c['episode_id'] for c in todo};assert len(ids)==len(todo) and not ids&{r['episode_id'] for r in plan['completed']}
 for completed in plan['completed']:assert sha(OLD/completed['episode_id']/'result.json')==completed['result_sha256']
 if not args.execute:print(json.dumps(dict(dry_run=True,choice=args.choice,to_run=len(todo),preserved_completed=6,restarted_incomplete=2 if args.choice=='A' else 0,no_native_physics=True)));raise SystemExit(0)
 if args.approval_file is None or not args.approval_file.is_file():raise ValueError('Actual explicit user approval evidence is required')
 assert not out.exists() and not data.exists(),'Append-only recovery already claimed'
 # Verify old weights and every frozen file except the repaired wrapper.
 oldpermit=json.loads((P/'phase8b-final-evaluation-permit.json').read_text());changed=[relative for relative,digest in oldpermit['files'].items() if sha(R/relative)!=digest];assert changed==plan['changed_frozen_source'];assert sha(R/changed[0])==plan['repaired_source_sha256']
 for relative,digest in json.loads((P/'phase8b-external-inference-dependency-freeze.json').read_text()).items():assert sha(R/relative)==digest
 for device in (0,1,5,7):
  env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=str(device);subprocess.run([sys.executable,'-c','import torch; assert torch.ones(1,device="cuda").item()==1'],env=env,check=True,stdout=subprocess.DEVNULL)
 out.mkdir();cases=out/'phase8b-locked-campaign-cases.json';cases.write_text(json.dumps(dict(cases=todo,original2017caseIDs=True,choice=args.choice,never_repeat_completed=True),indent=2));shutil.copy2(P/'phase8b-external-inference-dependency-freeze.json',out/'phase8b-external-inference-dependency-freeze.json')
 new=oldpermit.copy();new['files']=dict(oldpermit['files']);new['files'][changed[0]]=sha(R/changed[0]);new['files'][str(Path(__file__).resolve().relative_to(R))]=sha(Path(__file__));new['files'][str(cases.relative_to(R))]=sha(cases);new.update(recovery_registered_UTC=datetime.now(timezone.utc).isoformat(),original_permit_sha256=sha(P/'phase8b-final-evaluation-permit.json'),user_approval_sha256=sha(args.approval_file),user_approval_source=str(args.approval_file),recovery_choice=args.choice,completed_episodes_immutable=plan['completed'],scope='only explicitly approved incomplete/unstarted case IDs; no refit or retuning')
 permit.write_text(json.dumps(new,indent=2));permit.with_suffix('.sha256').write_text(sha(permit)+'\n');permit.chmod(0o444);permit.with_suffix('.sha256').chmod(0o444);cases.chmod(0o444)
 from pcse_gym.agromas.regions import load_split_manifest,authorize_year
 first=todo[0];authorize_year(load_split_manifest(R/'reports/phase5/global-date-split-manifest.json'),first['region'],first['year'],first['role'],permit_path=permit,project_root=R)
 from pcse_gym.agromas_v8.referee import prepare_daily_outputs
 prepare_daily_outputs(R);data.mkdir();(data/'recovery-claim.json').write_text(json.dumps(dict(choice=args.choice,approval_sha256=sha(args.approval_file),expected=len(todo),original_completed_preserved=6)))
 workers=[]
 for index in range(8):
  env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=str((0,1,5,7)[index%4]);log=(out/f'worker{index}.log').open('x');proc=subprocess.Popen([sys.executable,__file__,'--execute','--worker',str(index)],env=env,stdout=log,stderr=subprocess.STDOUT);workers.append((proc,log))
 exits=[]
 for proc,log in workers:exits.append(proc.wait());log.close()
 receipt=dict(exit_codes=exits,expected=len(todo),results=len(list(data.glob('*/result.json'))),original_completed_untouched=all(sha(OLD/r['episode_id']/'result.json')==r['result_sha256'] for r in plan['completed']),no_automatic_retry=True,choice=args.choice)
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2));assert not any(exits) and receipt['expected']==receipt['results'];print(json.dumps(receipt),flush=True)
