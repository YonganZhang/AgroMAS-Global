"""Run unchanged frozen scoring main after an identical cache-write redirection."""
from pathlib import Path
import importlib.util,sys,json,hashlib,runpy
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5'
if __name__=='__main__':
 from pcse_gym.agromas.final_evaluation import validate_external_dependency
 validate_external_dependency(R,P/'final-evaluation-permit-v4.json')
 spec=importlib.util.spec_from_file_location('cache_recovery_v4_r1',R/'scripts/phase5-final-cache-recovery-v4-r1.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 source_sha=module.sha(Path(__file__));cache=module.preload('score')
 original=P/'final-evaluation-recovery-addendum-v4-r1.json';assert json.loads(original.read_text())['source_sha256']==module.sha(R/'scripts/phase5-final-cache-recovery-v4-r1.py')
 module.immutable(P/'final-policy-cache-addendum-v4-r1.json',dict(status='cache_only_scoring_launch',permit_sha256=module.sha(P/'final-evaluation-permit-v4.json'),physical_recovery_addendum_sha256=module.sha(original),
  source_sha256=source_sha,source=str(Path(__file__).relative_to(R)),review_sha256=module.sha(P/'final-cache-recovery-review-v4-r1.md'),cache=cache,policy_changes=False,parameters_changed=False))
 sys.argv=[str(R/'scripts/phase5-score-final-books.py'),'--workers','32'];runpy.run_path(sys.argv[0],run_name='__main__')
 validate_external_dependency(R,P/'final-evaluation-permit-v4.json');assert module.sha(Path(__file__))==source_sha
