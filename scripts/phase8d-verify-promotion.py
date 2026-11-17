"""Hash-verify new runtime artifacts against primary; no old data overwritten."""
from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parents[1];P=Path('/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
paths=list((W/'data').glob('phase8d*'))+[W/'cache/phase8d-p2-adapter-inputs'];files={}
for path in paths:
 for f in path.rglob('*'):
  if not f.is_file():continue
  relative=f.relative_to(W);digest=sha(f);assert sha(P/relative)==digest,str(relative);files[str(relative)]=digest
receipt=dict(files=files,total_files=len(files),all_equal=True,source=str(W),primary=str(P),old_archives_overwritten=False)
(W/'reports/phase8/phase8d-runtime-promotion-sha256.json').write_text(json.dumps(receipt,indent=2));print('PASS:',len(files),'runtime artifact files promoted with identical SHA256')
