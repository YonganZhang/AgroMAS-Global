"""Pin retained scientific evidence, including ignored large files and superseded development runs."""
import pathlib,json,hashlib,subprocess,datetime
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 manifest=json.loads((R/'reports/heldout-unlock-manifest.json').read_text());integrity=json.loads((R/'reports/phase4-final-integrity.json').read_text());assert integrity['episodes']==38736 and integrity['missing']==0
 files=dict(manifest['files'])
 def add(p):
  p=pathlib.Path(p);assert p.is_file(),str(p);files[str(p.relative_to(R))]=sha(p)
 for rel in ['reports/heldout-unlock-manifest.json','reports/heldout-unlock-manifest.sha256','reports/heldout-audit-claim.json','reports/phase4-heldout-final.json','reports/phase4-heldout-metrics-summary.json','reports/final_cea_metrics.json','reports/FINAL_CEA_EXPERIMENTAL_RESULTS.md','reports/phase4-final-integrity.json','reports/phase4-episode-sha-index.json','reports/phase4-review-final.md','reports/phase4-review-resolution.md','reports/phase4-figure-review.md','reports/phase4-paired-dataset.json','reports/phase4-budget-scope.json','reports/phase4-figure-review-round1.md','reports/phase4-final-report-initial.md','logs/phase4-posthoc-figure-refined.log','logs/phase4-posthoc-report-final.log','logs/phase4-drawio-validation.log','logs/phase4-heldout-final.log','logs/phase4-freeze-seal.log','logs/phase4-posthoc-campaign.log','logs/phase4-posthoc-analysis.log','logs/phase4-posthoc-integrity.log','logs/phase4-posthoc-figure.log','logs/phase4-posthoc-report.log']:
  add(R/rel)
 for p in (R/'scripts').glob('final-cea*.py'):add(p)
 for p in (R/'figures/phase4-final').rglob('*'):
  if p.is_file():add(p)
 for p in (R/'reports/phase4-ppo-runs').glob('phase4-corrected-seed*'):
  for name in ['model.zip','receipt.json','normalizer.pkl']:add(p/name)
 for m in manifest['models']:
  if m['model']=='utilityprior':continue
  folder=(R/m['path']).parent
  for p in (folder/'source').rglob('*'):
   if p.is_file():add(p)
  for name in ['versions.json','config.json']:
   if (folder/name).exists():add(folder/name)
 for rel,h in manifest['files'].items():assert sha(R/rel)==h,'Frozen source/asset drift: '+rel
 payload=dict(status='completed',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),frozen_git_commits=manifest['git_commits'],reporting_parent_commit_before_registry=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),files=files,sha_algorithm='SHA256',raw_episode_index='reports/phase4-episode-sha-index.json',raw_episode_count=38736,episode_index_sha256=sha(R/'reports/phase4-episode-sha-index.json'),immutability_scope='Write-once procedural seals and committed hash registry; no hostile-root immutability claim',git_policy='Bulky checkpoint/raw metrics/weather retained locally and addressed bySHA; finalOUTBOX records actual final commits; unchangedpcse has no artificialemptycommit',primary='utilityprior',exploratory='cf-gru',original_cf_dev_point_target_passed=False)
 p=R/'reports/phase4-final-artifact-registry.json';assert not p.exists();p.write_text(json.dumps(payload,indent=2));print('Registered',len(files),'retained artifacts')
if __name__=='__main__':main()
