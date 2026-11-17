"""Seal repaired inference source, unchanged models and authorized case design."""
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
 dest=P/'phase8c-evaluation-permit.json';assert not dest.exists()
 assert json.loads((P/'phase8c-canonical-test-receipt.json').read_text())['exit_code']==0
 assert json.loads((P/'phase8c-online-action-invariance.json').read_text())['passed']==30
 assert json.loads((P/'phase8c-positive-action-invariance.json').read_text())['passed']==30
 assert len(json.loads((P/'phase8c-native-preflight.json').read_text())['records'])==3
 original=json.loads((P/'recovery2/phase8b-recovery-permit.json').read_text());unchanged_models={}
 for relative,digest in original['files'].items():
  if relative.startswith('models/'):
   file=R/relative
   if not file.exists():
    assert relative.endswith('/model.zip') and 'PPO-Sensorless-seed' in relative
    continue
   assert sha(file)==digest,relative;unchanged_models[relative]=digest
 assert len(unchanged_models)==95
 for seed in (4,17,29):
  for name in ('model.zip','vecnormalize.pkl','receipt.json'):
   file=R/f'models/phase8c-controls/ppo-sensorless-reconstructed-seed{seed}/{name}';unchanged_models[str(file.relative_to(R))]=sha(file)
 olddeps=json.loads((P/'phase8b-external-inference-dependency-freeze.json').read_text())
 for relative,digest in olddeps.items():assert sha(R/relative)==digest,relative
 dep=P/'phase8c-readonly-dependencies.json';encoded=json.dumps(olddeps,indent=2)
 if dep.exists():assert dep.read_text()==encoded
 else:dep.write_text(encoded)
 frozen={}
 sources=list((R/'NUE_PCSE-Gym/pcse_gym/agromas_v8').glob('*.py'))+[R/'scripts'/n for n in ('phase8c-run-campaign.py','phase8c-freeze-cases.py')]+[P/n for n in ('phase8c-frozen-cases-v3.json','phase8c-authorized-scope.md','phase8c-readonly-dependencies.json','phase8c-ppo-reconstruction-recipe.json','phase8c-ppo-reconstruction-authority.md','phase8c-native-cache-contract.md','phase8b-G1-verdict.json','phase8b-G2-control-calibration.json')]+[R/'reports/phase5'/n for n in ('regional-controls-v2.json','regional-phenology-train-freeze-v2.json')]+[f for f in (R/'cache/phase5-regional-config').rglob('*') if f.is_file() and f.suffix in ('.yaml','.conf')]
 for file in sources:
  assert file.resolve().is_relative_to(R);frozen[str(file.relative_to(R))]=sha(file);file.chmod(file.stat().st_mode&~0o222)
 for relative,digest in unchanged_models.items():
  file=R/relative;assert file.resolve().is_relative_to(R);frozen[relative]=digest;file.chmod(file.stat().st_mode&~0o222)
 preserved={}
 receipt=json.loads((P/'phase8b-combined-campaign-receipt.json').read_text())
 for episode,record in receipt['files'].items():
  file=R/'data/phase8-combined-evaluation'/episode/'result.json';assert sha(file)==record['sha256'];preserved[episode]=record['sha256']
 assert len(preserved)==2017
 (P/'phase8c-archived2017-preservation.json').write_text(json.dumps(dict(episode_count=2017,result_sha256=preserved,archived_report_sha256=sha(P/'PHASE8B_CORE_EXPERIMENTS_G1_G2_G3_REPORT.md'),root_baseline='e773fcb4501d5445a38ad86014c9202bfcd0b9b5',nue_baseline='b97976055f2699cc2d04acf1c16a02f33cdf24d6',immutable=True),indent=2))
 design=json.loads((P/'phase8c-frozen-cases-v3.json').read_text())
 permit=dict(all_models_frozen=True,dev_verified=True,subsidy_train_frozen=True,split_manifest_sha256=sha(R/'reports/phase5/global-date-split-manifest.json'),files=frozen,registered_UTC=datetime.now(timezone.utc).isoformat(),authorization='continue-5fb468a2b721d5f3.md attempt32OptionA;prior180cellscope retained',architecture='36D13155parameter PyTorch backbone plus private64D PCA/Ridge adapter<=4D',external_PCSE_commit='d1fe6d29de828033b850ec51d994988d8d6d406f',P1='adaptive-reused',P2='retrospective nested;unchanged outer-fold adapters',original_surviving_model_files=95,missing_original_PPO_ZIPs=3,versioned_TRAIN_only_PPO_reconstructions=3,all_other_model_fits=0,ledger_limits=dict(N=1e-10,C=1e-9),stress_cells=180,continuity_subset_cells=90,original2017_immutable=True,primary_mode='soft',sensitivity_mode='tree',new_native=design['new_native'],reused=design['reused'])
 with dest.open('x') as f:json.dump(permit,f,indent=2)
 dest.with_suffix('.sha256').write_text(sha(dest)+'\n');dest.chmod(0o444);dest.with_suffix('.sha256').chmod(0o444)
 print(json.dumps(dict(frozen=len(frozen),unchanged_models=len(unchanged_models),external_dependencies=len(olddeps),archived2017_unchanged=True)))
