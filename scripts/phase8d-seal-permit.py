"""Seal the authorized first-pass Phase8D workflow; no model selection here."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
if __name__=='__main__':
 dest=P/'phase8d-evaluation-permit.json';assert not dest.exists()
 v=json.loads((P/'phase8d-root-cause-verification.json').read_text());assert v['status']=='PRE_CAMPAIGN_PASS' and v['canonical_tests']['passed']>=232
 for name in ('online-action-invariance','positive-action-invariance','online-action-invariance-tree','positive-action-invariance-tree'):assert json.loads((P/f'phase8d-{name}.json').read_text())['passed']==30
 assert json.loads((P/'phase8d-native-cache-equivalence.json').read_text())['full_result_exact_equality']
 original=json.loads((P/'phase8c-evaluation-permit.json').read_text());frozen={}
 for rel,digest in original['files'].items():
  if not rel.startswith('models/'):continue
  file=R/rel;assert sha(file)==digest,rel;assert file.resolve().is_relative_to(R);frozen[rel]=digest
 for rel,digest in json.loads((P/'phase8d-readonly-dependencies.json').read_text()).items():assert sha(R/rel)==digest,rel
 files=list((R/'NUE_PCSE-Gym/pcse_gym/agromas_v8').glob('*.py'))+list((R/'models/phase8d-controls/p2-adapters').rglob('*.joblib'))
 files += [R/'scripts/phase8d-run-campaign.py']+[P/n for n in ('phase8d-frozen-cases-v4.json','phase8d-root-cause-verification.json','phase8d-G1-verdict.json','phase8d-G2-control-calibration.json','phase8d-P2-adapter-training-freeze.json','phase8d-protocol-amendment-first-pass-boundaries.json','phase8d-G1-width-protocol-amendment.json','phase8d-readonly-dependencies.json')]
 files += [R/'reports/phase5'/n for n in ('regional-controls-v2.json','regional-phenology-train-freeze-v2.json')]
 files += [f for f in (R/'cache/phase5-regional-config').rglob('*') if f.is_file() and f.suffix in ('.yaml','.conf')]
 for file in files:assert file.resolve().is_relative_to(R),file;frozen[str(file.relative_to(R))]=sha(file)
 baseline=json.loads((P/'phase8d-preservation-baseline.json').read_text())
 for rel,digest in baseline['files'].items():assert sha(R/rel)==digest,rel
 assert subprocess.check_output(['git','-C',str(R/'pcse'),'rev-parse','HEAD'],text=True).strip()=='d1fe6d29de828033b850ec51d994988d8d6d406f'
 assert not subprocess.check_output(['git','-C',str(R/'pcse'),'status','--porcelain'],text=True).strip()
 permit=dict(all_models_frozen=True,dev_verified=True,subsidy_train_frozen=True,split_manifest_sha256=sha(R/'reports/phase5/global-date-split-manifest.json'),files=frozen,registered_UTC=datetime.now(timezone.utc).isoformat(),authorization='continue-8c00f528d36f805c.md attempt37',external_PCSE_commit='d1fe6d29de828033b850ec51d994988d8d6d406f',protocol='Adaptive benchmark reuse, not a new prospective blind test; first-pass Dev/P2 boundaries retained, no post-outcome tuning',G1='Explicit CQR width amendment; original signed-offset failure archived',P2='First-pass outer fits frozen; LORO MSE degradation disclosed',Dev='First-pass soft targets improved; hard AU zero-compliance retained',physical_decoding='TRAIN-only nested three-seed prediction readout; zero neural fits',ledger_limits=dict(N=1e-10,C=1e-9),stress_cells=180,continuity_subset_cells=90,primary_mode='soft',sensitivity_mode='tree',new_native=18268,reused=0,decision_reuse=0,physical_archive_reuse='Only exact verified dated-action paths; real native public-prefix recovery required; every policy decision recomputed')
 with dest.open('x') as f:json.dump(permit,f,indent=2)
 dest.with_suffix('.sha256').write_text(sha(dest)+'\n');print(json.dumps(dict(frozen_files=len(frozen),preserved_archival_files=len(baseline['files']),permit_sha256=sha(dest))))
