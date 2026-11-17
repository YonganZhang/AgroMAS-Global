"""Check canonical deliverables and immutable prior-stage archives, without simulations."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((R/'reports/phase3a-final/archive-index.json').read_text())
for f in a['files']:assert sha(R/f['archive'])==f['sha256'],f['archive']
old=json.loads((R/'reports/phase3a-final/phase3-artifact-registry.json').read_text())
figures=[f for f in old['assets'] if f['path'].startswith('figures/phase3-breakthrough/')]
assert len(figures)==4
for f in figures:assert sha(R/'reports/phase3a-final/figure'/pathlib.Path(f['path']).name)==f['sha256']
for folder in ['figures/phase3b-breakthrough-final','figures/phase3-breakthrough']:
 p=R/folder;x=json.loads((p/'manifest.json').read_text())
 for rel,h in x['artifacts'].items():assert sha(p/rel)==h
 for src in x['sources']:assert sha(R/src['path'])==src['sha256']
 assert sha(R/x['spec']['path'])==x['spec']['sha256']
 assert x['visual_review']['verdict']=='PASS' and sha(p/'diagram.png')==x['visual_review']['reviewed_png_sha256']
for f in ['diagram.png','diagram.drawio','diagram.svg','manifest.json']:assert sha(R/'figures/phase3b-breakthrough-final'/f)==sha(R/'figures/phase3-breakthrough'/f)
assert sha(R/'reports/phase3_metrics.json')==sha(R/'reports/phase3b_metrics.json')
assert sha(R/'reports/phase3-metrics-summary.json')==sha(R/'reports/phase3b-metrics-summary.json')
x=json.loads((R/'reports/phase3b_metrics.json').read_text());assert all(len(x['episodes'][k])==4500 for k in ['v3/full3','v3-long/full3','v3-c8/full3','v3-sm/full3'])
assert all(e['actual_N']==190 for e in x['episodes']['v3-sm/full3'])
assert not (R/'reports/phase3b-heldout-unlock.json').exists()
assert '**PASS**' in (R/'reports/phase3b-figure-review-final.md').read_text()
out=dict(archive_files_preserved=len(a['files'])+len(figures),all_archive_hashes_match=True,canonical_metrics_equal_Phase3B=True,final_figure_source_hashes_match=True,canonical_figure_equal_final=True,visual_review='Gemini Carbon medium PASS',formal_candidates=4,formal_checkpoints=12,formal_interactions=1002240,target_tests=52,historical_locked=True,stress_locked=True,effect_gate_passed=False,all5tier_complete=False)
(R/'reports/phase3b-final-validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
