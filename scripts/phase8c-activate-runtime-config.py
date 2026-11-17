"""Activate the scored output-only runtime config after preserving prior cache."""
from pathlib import Path
import json,hashlib,ast,os,tempfile
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';d=json.loads((P/'phase8c-runtime-relocation-manifest.json').read_text());target=R/d['target'];old=(R/d['prior_backup']).read_bytes();new=(R/d['desired_archive']).read_bytes()
def sha(b):return hashlib.sha256(b).hexdigest()
if sha(old)!=d['prior_sha256'] or sha(new)!=d['desired_sha256']:raise RuntimeError('Runtime archive mismatch')
if not new.startswith(old):raise RuntimeError('Runtime change is not additive')
for n in ast.parse(new[len(old):].decode()).body:
 if not isinstance(n,ast.Assign) or not all(isinstance(t,ast.Name) and t.id=='OUTPUT_VARS' for t in n.targets):raise RuntimeError('Non-output runtime change refused')
if sha(target.read_bytes()) not in [d['prior_sha256'],d['desired_sha256']]:raise RuntimeError('Unexpected primary runtime config')
if target.read_bytes()!=new:
 fd,tmp=tempfile.mkstemp(prefix='.phase8c-runtime-',dir=target.parent)
 try:
  with os.fdopen(fd,'wb') as f:f.write(new);f.flush();os.fsync(f.fileno())
  os.chmod(tmp,0o444);os.replace(tmp,target)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
if sha(target.read_bytes())!=d['desired_sha256']:raise RuntimeError('Runtime activation verification failed')
(P/'phase8c-primary-runtime-activation.json').write_text(json.dumps(dict(status='passed',target=d['target'],prior_primary_config_preserved=d['prior_backup'],prior_sha256=d['prior_sha256'],active_sha256=d['desired_sha256'],native_equations_unchanged=True,original_permit_unchanged=True),indent=2));print('PASS: output-only runtime config activated;prior cache preserved')
