"""Atomic, no-overwrite artifact promotion; retain source until primary verification."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,tempfile,time
A=argparse.ArgumentParser();A.add_argument('--source',type=Path,required=True);A.add_argument('--target',type=Path,required=True);A.add_argument('--apply',action='store_true');a=A.parse_args();src=a.source.resolve();dst=a.target.resolve()
if src==dst:raise RuntimeError('Source and destination must differ')
private=dst/'cache/phase8c-raw-external-reviews';inventory=dst/'cache/phase8c-promotion-inventory.json';receipt=dst/'reports/phase8/phase8c-promotion-receipt.json'
def require(ok,message):
 if not ok:raise RuntimeError(message)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def destination(path):
 rel=path.relative_to(src)
 return private/rel.relative_to('_reports') if rel.parts[0]=='_reports' else dst/rel
def relocated_link(path,out):
 raw=os.readlink(path);target=Path(raw) if os.path.isabs(raw) else path.parent/raw;target=Path(os.path.normpath(str(target)))
 try:new=destination(target)
 except ValueError:return raw
 return str(new) if os.path.isabs(raw) else os.path.relpath(new,out.parent)
def parents(out):
 cur=out.parent
 while cur!=dst.parent:
  require(not cur.is_symlink(),'Refusing destination ancestor symlink: '+str(cur))
  if cur==dst:break
  cur=cur.parent
 out.parent.mkdir(parents=True,exist_ok=True)
 if out.is_relative_to(private):
  cur=out.parent
  while cur!=private.parent:cur.chmod(0o700);cur=cur.parent
roots=list((src/'data').glob('phase8c*'))+list((src/'cache').glob('phase8c*'))+[src/'models/phase8c-controls',src/'reports/phase8',src/'manuscript/phase8',src/'_reports']
if (src/'figures').exists():roots.append(src/'figures')
require((src/'models/phase8c-controls').is_dir() and (src/'reports/phase8').is_dir() and any((src/'data').glob('phase8c*')),'Missing expected Phase8C roots')
items=[];directory_links=[];seen=set()
for root in roots:
 if not root.exists():continue
 for p in ([root] if root.is_file() else sorted(root.rglob('*'))):
  if p in seen:continue
  seen.add(p)
  if p.is_symlink() and p.is_dir():directory_links.append(dict(target=str(destination(p).relative_to(dst)),link=relocated_link(p,destination(p))));continue
  if not p.is_file():continue
  out=destination(p);x=dict(source=str(p.relative_to(src)),target=str(out.relative_to(dst)),sha256=sha(p),bytes=p.stat().st_size,symlink=p.is_symlink())
  if x['symlink']:x['link']=relocated_link(p,out)
  if os.path.lexists(out):
   require(out.is_symlink()==x['symlink'],'Refusing existing target type mismatch: '+str(out))
   if x['symlink']:require(os.readlink(out)==x['link'],'Refusing different existing target link: '+str(out))
   if out.exists():require(sha(out)==x['sha256'],'Refusing different existing target: '+str(out))
   else:require(x['symlink'],'Refusing dangling regular-file destination')
  items.append(x)
require(bool(items),'No artifact files discovered')
if not a.apply:print(json.dumps(dict(mode='dry-run',files=len(items),directory_symlinks=len(directory_links),bytes=sum(x['bytes'] for x in items))));raise SystemExit
for x in items:
 p=src/x['source'];out=dst/x['target'];parents(out)
 if not os.path.lexists(out):
  if x['symlink']:out.symlink_to(x['link'])
  else:
   fd,tmp=tempfile.mkstemp(prefix='.phase8c-copy-',dir=out.parent)
   try:
    with os.fdopen(fd,'wb') as f,p.open('rb') as origin:shutil.copyfileobj(origin,f,4*1024*1024);f.flush();os.fsync(f.fileno())
    shutil.copystat(p,tmp);require(sha(Path(tmp))==x['sha256'],'Temporary copy checksum mismatch');os.link(tmp,out)
   finally:
    if os.path.exists(tmp):os.unlink(tmp)
 if not out.is_symlink() and out.is_relative_to(private):out.chmod(0o600)
for x in directory_links:
 out=dst/x['target'];parents(out)
 if os.path.lexists(out):require(out.is_symlink() and os.readlink(out)==x['link'],'Directory link mismatch: '+str(out))
 else:out.symlink_to(x['link'],target_is_directory=True)
def verify():
 for x in items:
  out=dst/x['target'];require(out.exists() and sha(out)==x['sha256'],'Final checksum mismatch: '+str(out))
  require(out.is_symlink()==x['symlink'],'Final type mismatch')
  if x['symlink']:require(os.readlink(out)==x['link'],'Final symlink mismatch')
 for x in directory_links:require(os.readlink(dst/x['target'])==x['link'],'Final directory link mismatch')
verify();inventory.parent.mkdir(exist_ok=True);inventory.write_text(json.dumps(dict(source=str(src),target=str(dst),files=items,directory_symlinks=directory_links),indent=2));inventory.chmod(0o600);verify()
r=dict(status='passed',files=len(items),directory_symlinks=len(directory_links),bytes=sum(x['bytes'] for x in items),all_sha256_verified=True,all_link_targets_verified=True,inventory=str(inventory),inventory_sha256=sha(inventory),raw_reviews_mode='0700 directories;0600 files',source_retained_until_postmerge_verification=True,roots=[str(p.relative_to(src)) for p in roots],completed_at=time.strftime('%Y-%m-%dT%H:%M:%S%z'));receipt.write_text(json.dumps(r,indent=2));print(json.dumps(r))
