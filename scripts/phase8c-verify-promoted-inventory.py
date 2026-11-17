"""Independent read-only verification of promoted bytes and removal-safe links."""
from pathlib import Path
import json,hashlib,os,subprocess
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';receipt=json.loads((P/'phase8c-promotion-receipt.json').read_text());inventory=Path(receipt['inventory'])
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
if sha(inventory)!=receipt['inventory_sha256']:raise RuntimeError('Inventory hash mismatch')
d=json.loads(inventory.read_text());old=d['source'];links=0
for x in d['files']:
 p=R/x['target']
 if sha(p)!=x['sha256']:raise RuntimeError('Promoted file changed: '+str(p))
 if p.is_symlink()!=x['symlink']:raise RuntimeError('Type mismatch')
 if x['symlink']:
  if os.readlink(p)!=x['link'] or str(p.resolve()).startswith(old+'/'):raise RuntimeError('Old worktree link remains: '+str(p))
  if x['target'].startswith('data/phase8c-supplemental-evaluation/') and p.name=='result.json':links+=1
for x in d['directory_symlinks']:
 if os.readlink(R/x['target'])!=x['link']:raise RuntimeError('Directory link changed')
if links!=521:raise RuntimeError('Archived result link denominator mismatch')
archive=json.loads((P/'phase8c-frozen-runtime-archive.json').read_text())['files'];permit=json.loads((P/'phase8c-evaluation-permit.json').read_text())
for rel,h in permit['files'].items():
 q=R/(archive[rel]['archived_path'] if rel in archive else rel)
 if sha(q)!=h or sha(R/rel)!=h:raise RuntimeError('Frozen dependency unavailable at registered runtime path: '+rel)
binding=json.loads((P/'phase8c-committed-permit-binding.json').read_text())
for repo,key in [(R,'root_code_commit'),(R/'NUE_PCSE-Gym','NUE_code_commit')]:subprocess.run(['git','merge-base','--is-ancestor',binding[key],'HEAD'],cwd=repo,check=True)
private=R/'cache/phase8c-raw-external-reviews'
for p in [private]+list(private.rglob('*')):
 if p.is_symlink():continue
 if p.stat().st_mode&0o777!=(0o700 if p.is_dir() else 0o600):raise RuntimeError('Private permissions incorrect: '+str(p))
out=dict(status='passed',files_verified=len(d['files']),inventory_sha256=sha(inventory),all_file_SHA256_match=True,all_link_targets_match=True,archived_result_links_verified=links,no_link_points_to_removed_source=True,committed_code_ancestry_verified=True,private_permissions_verified=True,frozen_dependencies_verified=len(permit['files']),frozen_cache_files_archived_separately=len(archive))
(P/'phase8c-postmerge-promotion-verification.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
