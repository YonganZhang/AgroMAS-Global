"""Verify immutable legacy evidence and explicit versioned Phase7 asset inventory."""
from pathlib import Path
import json,hashlib,sys
R=Path(__file__).resolve().parents[1];P=R/'reports/phase7'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
 baseline=json.loads((P/'preservation-baseline-v7.json').read_text());primary=Path(baseline['primary_root']);assert all(sha(primary/x['path'])==x['sha256'] for x in baseline['files'])
 inventory=P/'delivery-assets-manifest-v7.json'
 if '--create' in sys.argv:
  assert not inventory.exists(),'Never silently replace a sealed delivery inventory'
  paths=[]
  for folder in ['models/phase7','reports/figures/phase7','manuscript/phase7','data/phase7-alphaearth-v1']:
   paths.extend(x for x in (R/folder).rglob('*') if x.is_file() and not any(y in x.parts for y in ['build','http-cache','__pycache__']) and x.suffix not in ['.tmp'])
  # Binary HTTP range caches are rebuildable; scientific arrays and metadata are sealed.
  paths=[x for x in paths if 'cache' not in x.relative_to(R).parts]
  inventory.write_text(json.dumps(dict(scope='New scientific assets; excludes regenerable HTTP caches/build files and future closeout logs',assets=[dict(path=str(x.relative_to(R)),sha256=sha(x),bytes=x.stat().st_size) for x in sorted(set(paths))]),indent=2))
 assets=json.loads(inventory.read_text())['assets'];changed=[x['path'] for x in assets if not (R/x['path']).is_file() or sha(R/x['path'])!=x['sha256']];assert not changed,changed
 label=next((x.split('=',1)[1] for x in sys.argv if x.startswith('--label=')),'verification');(P/f'{label}-delivery-verification-v7.json').write_text(json.dumps(dict(status='passed',source_root=str(R),legacy_files_bit_exact=len(baseline['files']),new_assets_verified=len(assets),manifest_sha256=sha(inventory)),indent=2));print('Legacy',len(baseline['files']),'new assets',len(assets),'byte-exact')
