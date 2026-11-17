"""Snapshot Phase6 delivery assets before transfer; never replace Phase5 manifests."""
from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[1];P=R/'reports/phase6';out=P/'phase6-final-transfer-manifest-v6.json'
assert not out.exists()
paths=set()
for folder in ['reports/phase6','reports/figures/phase6','models/phase6']:
 for f in (R/folder).rglob('*'):
  if f.is_file() and f.name!='FINAL_CLOSEOUT_V6.md':paths.add(f)
paths.update((R/'scripts').glob('phase6*.py'))
for folder in ['NUE_PCSE-Gym/pcse_gym/agromas_v6']:
 paths.update(f for f in (R/folder).glob('*.py'))
for n in ['NUE_PCSE-Gym/tests/target/test_phase6.py','_codemap.md','_meta/_data_sources.md','_wiki-methodology/_wiki/method.md','_wiki-methodology/_wiki/socratic-logic-and-evolution.md']:paths.add(R/n)
rows=[dict(path=str(f.relative_to(R)),sha256=hashlib.sha256(f.read_bytes()).hexdigest(),bytes=f.stat().st_size) for f in sorted(paths)]
out.write_text(json.dumps(dict(scope='Premerge delivery snapshot; final closeout, later test logs and plan records are appended separately',files=rows),indent=2));print(len(rows))
