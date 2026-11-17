"""Read-only independent physical-trajectory denominator verification."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];seen={};new=hits=0
for p in (R/'data/phase8c-supplemental-evaluation').glob('*/result.json'):
 if p.is_symlink():continue
 d=json.loads(p.read_text());c=d['native_cache'];k=tuple(c['world'])+(c['physical_sha256'],);m=d['mass_audit'];new+=1;hits+=c['trajectory_replayed'];assert m['passed'];v=dict(world=c['world'],physical_sha256=c['physical_sha256'],executed_doses=c['executed_doses'],daily_rows=m['daily_rows'],max_N=m['max_abs_N_residual_kg_ha'],max_C=m['max_abs_C_residual_kg_ha'],representative=str(p.relative_to(R)))
 if k in seen:
  assert all(seen[k][x]==v[x] for x in ['daily_rows','max_N','max_C','executed_doses'])
 else:seen[k]=v
assert new==17747 and hits==15830 and len(seen)==1917,(new,hits,len(seen))
out=dict(unique_native_trajectories=len(seen),new_scored_configurations=new,trajectory_cache_hits=hits,unique_physical_daily_rows=sum(x['daily_rows'] for x in seen.values()),all_mass_passed=True,trajectories=list(seen.values()));(R/'reports/phase8/phase8c-unique-physical-trajectories.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='trajectories'}))
