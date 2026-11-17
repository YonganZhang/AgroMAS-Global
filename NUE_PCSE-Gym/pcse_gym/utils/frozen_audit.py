"""Write-once heldout authorization, sealed assets and one-shot audit claim."""
import pathlib,json,hashlib,os

def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()

def exclusive_json(path,value):
    path=pathlib.Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    raw=json.dumps(value,sort_keys=True,indent=2).encode();fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o444)
    with os.fdopen(fd,'wb') as file:file.write(raw);file.flush();os.fsync(file.fileno())
    return hashlib.sha256(raw).hexdigest()

def seal_manifest(root,payload):
    root=pathlib.Path(root);path=root/'reports/heldout-unlock-manifest.json';seal=path.with_suffix('.sha256')
    if path.exists() or seal.exists():raise FileExistsError('Heldout manifest is write-once')
    if not payload.get('dev_verified') or not payload.get('all_checkpoints_frozen'):raise ValueError('Dev/freeze prerequisites missing')
    for rel,h in payload['files'].items():
        resolved=(root/rel).resolve()
        if not resolved.is_relative_to(root.resolve()) or sha(resolved)!=h:raise ValueError('Asset drift: '+rel)
    digest=exclusive_json(path,payload);fd=os.open(seal,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o444)
    with os.fdopen(fd,'w') as f:f.write(digest+'\n');f.flush();os.fsync(f.fileno())
    return digest

def validate_manifest(root,verify_files=True):
    root=pathlib.Path(root);p=root/'reports/heldout-unlock-manifest.json'
    if not p.exists() or not p.with_suffix('.sha256').exists():raise ValueError('Heldout locked')
    if sha(p)!=p.with_suffix('.sha256').read_text().strip():raise ValueError('Manifest seal mismatch')
    x=json.loads(p.read_text())
    if not x['dev_verified'] or not x['all_checkpoints_frozen']:raise ValueError('Invalid frozen contract')
    if verify_files:
        for rel,h in x['files'].items():
            resolved=(root/rel).resolve()
            if not resolved.is_relative_to(root.resolve()) or sha(resolved)!=h:raise ValueError('Frozen asset drift: '+rel)
    return x

def claim_audit(root,tasks):
    root=pathlib.Path(root);validate_manifest(root,True)
    return exclusive_json(root/'reports/heldout-audit-claim.json',dict(manifest_sha256=sha(root/'reports/heldout-unlock-manifest.json'),tasks=tasks,one_shot=True))
