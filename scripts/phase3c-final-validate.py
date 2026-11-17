"""Check canonical negative hand-in, archives and final visual/source certificates."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
R=pathlib.Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
 tests=ET.parse(R/'reports/phase3c-all-tests.xml').getroot();suites=list(tests.iter('testsuite'));assert sum(int(s.get('tests','0')) for s in suites)==60 and all(int(s.get(k,'0'))==0 for s in suites for k in ['errors','failures','skipped'])
 preserved=0
 for entry in json.loads((R/'reports/phase3b-final/archive-index.json').read_text()):assert sha(R/entry['archive'])==entry['sha256'];preserved+=1
 for entry in json.loads((R/'reports/phase3a-final/archive-index.json').read_text())['files']:assert sha(R/entry['archive'])==entry['sha256'];preserved+=1
 for entry in json.loads((R/'reports/phase3a-final/phase3-artifact-registry.json').read_text())['assets']:
  if entry['path'].startswith('figures/phase3-breakthrough/'):assert sha(R/'reports/phase3a-final/figure'/pathlib.Path(entry['path']).name)==entry['sha256'];preserved+=1
 assert preserved==19
 for folder in ['figures/phase3c-breakthrough-final','figures/phase3-breakthrough']:
  f=R/folder;m=json.loads((f/'manifest.json').read_text())
  for rel,h in m['artifacts'].items():assert sha(f/rel)==h
  for src in m['sources']:assert sha(R/src['path'])==src['sha256']
  assert sha(R/m['spec']['path'])==m['spec']['sha256']
  assert m['visual_review']['verdict']=='PASS' and sha(f/'diagram.png')==m['visual_review']['reviewed_png_sha256']
 for f in ['diagram.png','diagram.drawio','diagram.svg','manifest.json']:assert sha(R/'figures/phase3c-breakthrough-final'/f)==sha(R/'figures/phase3-breakthrough'/f)
 assert sha(R/'reports/phase3_metrics.json')==sha(R/'reports/phase3c_metrics.json')
 assert sha(R/'reports/phase3-metrics-summary.json')==sha(R/'reports/phase3c-metrics-summary.json')
 g=json.loads((R/'reports/phase3c-dev-gate-v4-sm.json').read_text());a=json.loads((R/'reports/phase3c-contract-audit.json').read_text());assert not g['dev_gate_passed'] and not a['effective_gate_passed']
 assert not (R/'reports/phase3b-heldout-unlock.json').exists()
 output=dict(tests_passed=60,canonical_data_and_figures_match=True,final_visual_review='Gemini Carbon medium PASS',preserved_prior_stage_archived_files=19,all_archive_hashes_match=True,base_dev_gate_passed=False,effective_dev_gate_passed=False,historical_locked=True,stress_locked=True,matched_remaining_tiers_run=False,negative_honesty_fallback=True,all_tests_xml_sha256=sha(R/'reports/phase3c-all-tests.xml'))
 (R/'reports/phase3c-final-validation.json').write_text(json.dumps(output,indent=2));print(json.dumps(output))
