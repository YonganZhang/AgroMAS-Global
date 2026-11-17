"""Register final local evidence and all12immutable checkpoints. Read-only scientific audit."""
import pathlib,json,hashlib,subprocess
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
runs=[]
for parent,tag in [('phase3b-runs','v3'),('phase3b-runs','v3-long'),('phase3b2-runs','v3-c8'),('phase3b3-runs','v3-sm')]:
 for seed in [4,17,29]:
  f=R/f'reports/{parent}/{tag}-full3-seed{seed}';x=json.loads((f/'receipt.json').read_text());assert x['status']=='completed' and x['parameters_changed'] and x['finite_parameters']
  assert sha(f/'model.zip')==x['checkpoint_sha256']
  for rel,h in x['source_sha256'].items():assert sha(R/rel)==h and sha(f/'source'/rel)==h,rel
  runs.append(dict(tag=tag,seed=seed,steps=x['actual_steps'],checkpoint=str((f/'model.zip').relative_to(R)),checkpoint_sha256=x['checkpoint_sha256'],receipt_sha256=sha(f/'receipt.json'),frozen_source_files=len(x['source_sha256'])))
assert len(runs)==12 and sum(r['steps'] for r in runs)==1002240
paths=sorted(set([p for p in (R/'reports').glob('phase3b*') if p.is_file() and '.progress.' not in p.name and p.name!='phase3b-artifact-registry.json']+list((R/'scripts').glob('phase3b*.py'))+[R/'reports/PHASE3_BREAKTHROUGH_RESULTS.md',R/'reports/phase3_metrics.json',R/'reports/phase3-metrics-summary.json',R/'tasks/TASK_PHASE3B_190_CORRIDOR_AND_FINAL_UNLOCK.md']+list((R/'figures/phase3-breakthrough').glob('*'))+list((R/'figures/phase3b-breakthrough-final').glob('*'))))
registry=dict(runs=runs,total_formal_PPO_steps=1002240,dev_gate_passed=False,historical_started=False,stress_started=False,remaining_tiers_trained=False,package_head=subprocess.check_output(['git','-C',str(R/'NUE_PCSE-Gym'),'rev-parse','HEAD'],text=True).strip(),pcse_head=subprocess.check_output(['git','-C',str(R/'pcse'),'rev-parse','HEAD'],text=True).strip(),files={str(p.relative_to(R)):sha(p) for p in paths if p.is_file()})
(R/'reports/phase3b-artifact-registry.json').write_text(json.dumps(registry,indent=2));print(json.dumps(dict(runs=12,steps=1002240,files=len(registry['files']))))
