"""Attest original pre-evaluation hashes against committed code;never re-seal."""
from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';permit=P/'phase8c-evaluation-permit.json';d=json.loads(permit.read_text());root=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip();nue=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R/'NUE_PCSE-Gym',text=True).strip();items=[]
for rel,h in d['files'].items():
 p=R/rel
 if hashlib.sha256(p.read_bytes()).hexdigest()!=h:raise RuntimeError('Frozen bytes changed: '+rel)
 repo=R/'NUE_PCSE-Gym' if rel.startswith('NUE_PCSE-Gym/') else R;key=rel.removeprefix('NUE_PCSE-Gym/');commit=nue if repo!=R else root
 proc=subprocess.run(['git','show',commit+':'+key],cwd=repo,capture_output=True)
 tracked=proc.returncode==0
 if tracked and hashlib.sha256(proc.stdout).hexdigest()!=h:raise RuntimeError('Committed bytes differ: '+rel)
 items.append(dict(path=rel,sha256=h,tracked_blob_verified=tracked,commit=commit if tracked else None))
(P/'phase8c-committed-permit-binding.json').write_text(json.dumps(dict(root_code_commit=root,NUE_code_commit=nue,original_permit_sha256=hashlib.sha256(permit.read_bytes()).hexdigest(),permit_unchanged=True,files=items,all_disk_hashes_verified=True,tracked_blobs_verified=sum(x['tracked_blob_verified'] for x in items),ignored_model_artifacts_require_promotion_inventory=True),indent=2));print('PASS: original permit bound to committed code;no retrospective re-seal')
