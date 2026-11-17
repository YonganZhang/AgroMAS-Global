"""Verify actual primary against the completed worktree before deleting it."""
from pathlib import Path
import json,hashlib,subprocess,shutil
R=Path(__file__).resolve().parents[1];W=Path('/mnt/data/yongan-admin-2/projects/worktrees/agromas-phase8d');P=R/'reports/phase8'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
if __name__=='__main__':
 assert R==Path('/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体') and W.is_dir()
 runtime=json.loads((P/'phase8d-runtime-promotion-sha256.json').read_text())['files']
 for rel,h in runtime.items():assert sha(R/rel)==h,rel
 tracked={};base='adc38b3';head=subprocess.check_output(['git','-C',str(W),'rev-parse','HEAD'],text=True).strip()
 for rel in subprocess.check_output(['git','-C',str(W),'diff','--name-only',base,head],text=True).splitlines():
  f=W/rel
  if not f.is_file():continue
  h=sha(f);assert sha(R/rel)==h,rel;tracked[rel]=h
 for permit_name in ('phase8d-evaluation-permit.json','phase8d-evaluation-permit-recovery1.json'):
  p=P/permit_name;assert sha(p)==p.with_suffix('.sha256').read_text().strip()
  for rel,h in json.loads(p.read_text())['files'].items():assert sha(R/rel)==h,rel
 for rel,h in json.loads((P/'phase8d-readonly-dependencies.json').read_text()).items():assert sha(R/rel)==h,rel
 archived=json.loads((P/'phase8d-preservation-baseline.json').read_text())['files']
 for rel,h in archived.items():assert sha(R/rel)==h,rel
 neurons=json.loads((P/'phase8d-frozen-neural72-preservation.json').read_text())['files']
 for rel,h in neurons.items():assert sha(R/rel)==h,rel
 for name in ('phase8d-NUE-merge.log','phase8d-root-merge.log'):shutil.copy2(W/'reports/phase8'/name,P/name)
 assert subprocess.check_output(['git','-C',str(R/'pcse'),'rev-parse','HEAD'],text=True).strip()=='d1fe6d29de828033b850ec51d994988d8d6d406f'
 assert not subprocess.check_output(['git','-C',str(R/'pcse'),'status','--porcelain'],text=True).strip()
 for repo,branch in ((R,'master'),(R/'NUE_PCSE-Gym','main')):
  assert subprocess.check_output(['git','-C',str(repo),'branch','--show-current'],text=True).strip()==branch
  subprocess.run(['git','-C',str(repo),'merge-base','--is-ancestor','feat/phase8d-root-cause-optimization',branch],check=True)
 v=json.loads((P/'phase8d-primary-verification.json').read_text());assert v['canonical_passed']>=232 and v['future_weather_invariance_passed']==120
 pub=json.loads((P/'phase8d-publication-integrity.json').read_text());assert pub['passed']
 for f in pub['files']:assert sha(R/f['path'])==f['sha256'],f['path']
 out=dict(all_primary_hashes_verified=True,runtime_files=len(runtime),tracked_promoted_files=len(tracked),tracked_sha256=tracked,archived_files_unchanged=len(archived),neural_checkpoints_unchanged=len(neurons),both_permits_and_readonly_dependencies_verified=True,actual_primary_verification=v,both_feature_branches_merged=True,pcse_unchanged=True,worktree_commit=head)
 (P/'phase8d-final-primary-sha256-verification.json').write_text(json.dumps(out,indent=2));print('PASS:',len(runtime),'runtime files,',len(tracked),'tracked artifacts, both sealed permits, original dependencies,392 archives and72 neural weights')
