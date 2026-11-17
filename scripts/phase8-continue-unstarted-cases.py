"""Continue only incomplete/unstarted IDs after pre-integral WUR type repair.

Epoch28 still authorizes original2incomplete restarts; recovery1's four WUR
failures occurred in Engine trait validation before any physical integration.
All1460completed seasons stay immutable. Default is dry-run.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,hashlib,subprocess,os,sys,importlib.util,shutil
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';OUT=P/'recovery2';DATA=R/'data/phase8-locked-recovery2';PERMIT=OUT/'phase8b-recovery-permit.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def worker(index):
 sp=importlib.util.spec_from_file_location('lockedworker',R/'scripts/phase8-run-locked-campaign.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);m.P=OUT;m.D=DATA;m.PERMIT=PERMIT;m.execute_worker(index,8)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--execute',action='store_true');parser.add_argument('--approval-file',type=Path);parser.add_argument('--worker',type=int);a=parser.parse_args()
 if a.worker is not None:assert a.execute;worker(a.worker);raise SystemExit(0)
 completed={}
 for folder in ('phase8-locked-evaluation','phase8-locked-recovery1'):
  for file in (R/'data'/folder).glob('*/result.json'):
   assert file.parent.name not in completed;completed[file.parent.name]=dict(path=str(file.relative_to(R)),sha256=sha(file))
 cases=json.loads((P/'phase8b-locked-campaign-cases.json').read_text())['cases'];missing=[c for c in cases if c['episode_id'] not in completed];assert len(completed)==1460 and len(missing)==557
 failures=list((R/'data/phase8-locked-recovery1').glob('*/error.json'));assert len(failures)==4 and all('weatherdataprovider' in json.loads(p.read_text())['error'] for p in failures)
 if not a.execute:print(json.dumps(dict(dry_run=True,completed_preserved=1460,missing=557,WUR_preintegration_type_failures=4,additional_native_prefix_replays=0)));raise SystemExit(0)
 assert a.approval_file and a.approval_file.is_file();assert not OUT.exists() and not DATA.exists()
 base=json.loads((P/'recovery1/phase8b-recovery-permit.json').read_text());changed=[p for p,h in base['files'].items() if sha(R/p)!=h];assert changed==['NUE_PCSE-Gym/pcse_gym/agromas_v8/referee.py']
 for p,h in json.loads((P/'phase8b-external-inference-dependency-freeze.json').read_text()).items():assert sha(R/p)==h
 for device in (0,1,5,7):
  env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=str(device);subprocess.run([sys.executable,'-c','import torch; assert torch.ones(1,device="cuda").item()==1'],env=env,check=True,stdout=subprocess.DEVNULL)
 OUT.mkdir();casefile=OUT/'phase8b-locked-campaign-cases.json';casefile.write_text(json.dumps(dict(cases=missing),indent=2));shutil.copy2(P/'phase8b-external-inference-dependency-freeze.json',OUT/'phase8b-external-inference-dependency-freeze.json');base['files']=dict(base['files']);base['files'][changed[0]]=sha(R/changed[0]);base['files'][str(Path(__file__).resolve().relative_to(R))]=sha(Path(__file__));base['files'][str(casefile.relative_to(R))]=sha(casefile);base.update(recovery2_UTC=datetime.now(timezone.utc).isoformat(),same_epoch28_approval_sha256=sha(a.approval_file),preserved_completed=completed,WUR_error_before_native_integration=True,no_additional_native_prefix_replays=True)
 PERMIT.write_text(json.dumps(base,indent=2));PERMIT.with_suffix('.sha256').write_text(sha(PERMIT)+'\n');PERMIT.chmod(0o444);PERMIT.with_suffix('.sha256').chmod(0o444);casefile.chmod(0o444)
 from pcse_gym.agromas.regions import authorize_year,load_split_manifest
 c=missing[0];authorize_year(load_split_manifest(R/'reports/phase5/global-date-split-manifest.json'),c['region'],c['year'],c['role'],permit_path=PERMIT,project_root=R)
 from pcse_gym.agromas_v8.referee import prepare_daily_outputs
 prepare_daily_outputs(R);DATA.mkdir();(DATA/'claim.json').write_text(json.dumps(dict(missing=557,preserved=1460,new_native_prefix_replays=0)));workers=[]
 for index in range(8):
  env=os.environ.copy();env['CUDA_VISIBLE_DEVICES']=str((0,1,5,7)[index%4]);log=(OUT/f'worker{index}.log').open('x');proc=subprocess.Popen([sys.executable,__file__,'--execute','--worker',str(index)],env=env,stdout=log,stderr=subprocess.STDOUT);workers.append((proc,log))
 exits=[]
 for proc,log in workers:exits.append(proc.wait());log.close()
 receipt=dict(exit_codes=exits,expected=557,results=len(list(DATA.glob('*/result.json'))),completed1460_unchanged=all(sha(R/r['path'])==r['sha256'] for r in completed.values()),no_extra_native_prefix_replays=True,epoch28_authorization=True)
 (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2));assert not any(exits) and receipt['results']==557;print(json.dumps(receipt),flush=True)
