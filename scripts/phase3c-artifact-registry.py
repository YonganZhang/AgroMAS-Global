"""Register Phase3C local data/weights and compact committed evidence, without simulation."""
import pathlib,json,hashlib,subprocess
R=pathlib.Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
 runs=[]
 for seed in [4,17,29]:
  f=R/f'reports/phase3c-runs/v4-sm-final-full4-seed{seed}';x=json.loads((f/'receipt.json').read_text());assert x['status']=='completed' and x['actual_steps']==67200 and sha(f/'model.zip')==x['checkpoint_sha256']
  for rel,h in x['source_sha256'].items():assert sha(R/rel)==h and sha(f/'source'/rel)==h
  runs.append(dict(seed=seed,path=str(f.relative_to(R)),checkpoint_sha256=x['checkpoint_sha256'],receipt_sha256=sha(f/'receipt.json'),normalizer_sha256=sha(f/'normalizer.pkl'),steps=x['actual_steps'],source_files=len(x['source_sha256'])))
 paths=[p for p in (R/'reports').glob('phase3c*') if p.is_file() and '.progress.' not in p.name and p.name!='phase3c-artifact-registry.json']+list((R/'scripts').glob('phase3c*.py'))+list((R/'figures/phase3c-breakthrough-final').glob('*'))+list((R/'figures/phase3-breakthrough').glob('*'))+[R/'reports/PHASE3_BREAKTHROUGH_RESULTS.md',R/'reports/PHASE3C_DEV_RESULTS.md',R/'reports/phase3_metrics.json',R/'reports/phase3-metrics-summary.json',R/'reports/phase3b-final/archive-index.json',R/'tasks/TASK_PHASE3C_ACTIVE_STEP_PPO_AND_FINAL_EVAL.md']
 old=json.loads((R/'reports/phase3b-final/archive-index.json').read_text())
 for a in old:assert sha(R/a['archive'])==a['sha256']
 interrupted=[]
 for seed in [4,17,29]:
  f=R/f'reports/phase3c-runs/v4-sm-full4-seed{seed}';x=json.loads((f/'interruption.json').read_text());interrupted.append(dict(seed=seed,path=str(f.relative_to(R)),last_recorded_steps_lower_bound=x['last_recorded_steps_lower_bound'],metadata_sha256=sha(f/'interruption.json'),complete_receipt_exists=(f/'receipt.json').exists(),not_a_completed_trial=True))
 out=dict(formal_checkpoints=runs,total_formal_interactions=201600,interrupted_preDev_attempts=interrupted,preflight_smoke_steps=1920,dev_gate_passed=False,heldout_started=False,calibration_scenarios=360,calibration_outcomes=2160,calibration_new_outcomes=1260,calibration_reused_outcomes=900,package_commit=subprocess.check_output(['git','-C',str(R/'NUE_PCSE-Gym'),'rev-parse','HEAD'],text=True).strip(),pcse_commit=subprocess.check_output(['git','-C',str(R/'pcse'),'rev-parse','HEAD'],text=True).strip(),files={str(p.relative_to(R)):sha(p) for p in sorted(set(paths)) if p.is_file()})
 (R/'reports/phase3c-artifact-registry.json').write_text(json.dumps(out,indent=2));print(json.dumps(dict(formal_checkpoints=3,steps=201600,registered_files=len(out['files']))))
