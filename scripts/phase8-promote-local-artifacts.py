"""Move task-local scientific artifacts to primary after verified merges.

Default dry-run; never overwrite an existing artifact. Retarget only absolute
worktree symlinks, preserving referenced bytes and immutable result hashes.
"""
from pathlib import Path
import argparse,json,subprocess,shutil,hashlib
R=Path(__file__).resolve().parents[1];PRIMARY=Path('/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体')
def git(path,*args):return subprocess.check_output(['git','-C',str(path),*args],text=True).strip()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--execute',action='store_true');a=p.parse_args();moves=[]
 for folder in [v for v in (R/'data').glob('phase8*') if v.is_dir() and not v.is_symlink()]:moves.append((folder,PRIMARY/'data'/folder.name))
 for folder in [v for v in (R/'cache').glob('phase8*') if v.is_dir() and not v.is_symlink()]:moves.append((folder,PRIMARY/'cache'/folder.name))
 for file in (R/'cache').glob('phase8*.joblib'):moves.append((file,PRIMARY/'cache'/file.name))
 for file in (R/'models/phase8-v8').glob('*ExtraTrees-fold*.joblib'):moves.append((file,PRIMARY/'models/phase8-v8'/file.name))
 if (R/'cache/phase5-regional-config').is_dir():moves.append((R/'cache/phase5-regional-config',PRIMARY/'cache/phase8b-native-runtime-config'))
 if (R/'_reports').is_dir():moves.append((R/'_reports',PRIMARY/'cache/phase8b-raw-external-reviews'))
 for source,target in moves:
  if target.exists() or target.is_symlink():raise ValueError('Refuse overwrite:'+str(target))
 if not a.execute:print(json.dumps(dict(dry_run=True,moves=[dict(source=str(s),target=str(t)) for s,t in moves]),indent=2));raise SystemExit(0)
 for project in ('.','NUE_PCSE-Gym'):
  subprocess.run(['git','-C',str(PRIMARY/project),'merge-base','--is-ancestor',git(R/project,'rev-parse','HEAD'),'HEAD'],check=True)
 for source,target in moves:
  target.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(source),str(target))
  if target.name in ('phase8b-private','phase8b-raw-external-reviews'):target.chmod(0o700)
 links=[]
 for source,target in moves:
  if not target.is_dir():continue
  for link in target.rglob('*'):
   if not link.is_symlink():continue
   old=link.readlink()
   if old.is_absolute() and old.is_relative_to(R):
    new=PRIMARY/old.relative_to(R);assert new.exists();link.unlink();link.symlink_to(new,target_is_directory=new.is_dir());links.append(dict(path=str(link),old=str(old),new=str(new)))
 manifest=json.loads((PRIMARY/'reports/phase8/phase8b-ExtraTrees-local-artifact-manifest.json').read_text())
 for row in manifest['files']:assert hashlib.sha256((PRIMARY/row['path']).read_bytes()).hexdigest()==row['sha256']
 frozen=json.loads((PRIMARY/'reports/phase8/phase8b-proposed-recovery-manifest.json').read_text())
 for row in frozen['completed']:assert hashlib.sha256((PRIMARY/'data/phase8-locked-evaluation'/row['episode_id']/'result.json').read_bytes()).hexdigest()==row['result_sha256']
 (PRIMARY/'reports/phase8/phase8b-local-artifact-promotion.json').write_text(json.dumps(dict(moves=[dict(source=str(s),target=str(t)) for s,t in moves],retargeted_symlinks=links,ExtraTrees_all_hashes_pass=True,original6_result_hashes_pass=True),indent=2));print('Scientific artifacts promoted; hashes verified')
