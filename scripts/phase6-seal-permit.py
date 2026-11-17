"""Freeze all v6 selection inputs and inference assets before adaptive scoring."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess
R=Path(__file__).resolve().parents[1];P=R/'reports/phase6'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
 active=json.loads((P/'ACTIVE_TRAIN_RUN_V6.json').read_text());run=R/active['reports'];primary=Path(json.loads((P/'phase5-preservation-baseline-v6.json').read_text())['primary_root']);files={}
 assert json.loads((P/'prefinal-fold-isolation-test-verification-v6.json').read_text())['pytest_exit']==0
 assert json.loads((run/'PPO-campaign-v6.json').read_text())['status']=='completed'
 for name in ('PPO-frozen-TRAIN-diagnostic-v6.json','PPO-env-causal-and-replay-audit-v6.json','final-loader-TRAIN-reconstruction-v6.json','green-subsidy-TRAIN-freeze-v6.json','selected-policy-TRAIN-OOF-calibration-v6.json'):assert (run/name).is_file()
 campaign=json.loads((run/'PPO-campaign-v6.json').read_text());assert sorted(x['seed'] for x in campaign['jobs'])==[4,17,29] and all(x['exit_code']==0 for x in campaign['jobs'])
 protocol=run/'PPO_TRAIN_PROTOCOL_V6.json';pretrain=json.loads((run/'PPO-source-freeze-v6.json').read_text());assert sha(protocol)==pretrain['protocol_sha256']
 for name,digest in pretrain['files'].items():assert sha(R/name)==digest
 cache=R/'cache/phase6'/active['run']/'train-book-ppo-inputs-v6.joblib';assert sha(cache)==json.loads(protocol.read_text())['cache_sha256']
 for seed in (4,17,29):
  folder=R/active['models']/f'PPO-structured-seed{seed}';receipt=json.loads((folder/'receipt.json').read_text());assert receipt['status']=='completed' and receipt['actual_decision_steps']==151552
  for name,digest in receipt['files'].items():assert sha(folder/name)==digest
 diagnostic=json.loads((run/'PPO-frozen-TRAIN-all-context-diagnostic-v6.json').read_text());assert sorted(r['seed'] for r in diagnostic['records'])==[4,17,29]
 for row in diagnostic['records']:assert row['episodes']==6825 and row['all_actions_mask_valid'] and row['weights_and_normalizer_unchanged'] and row['clip_obs']==1e6
 boundary=json.loads((run/'TRAIN-boundaries-reconstruction-full-r2-v6.json').read_text());assert boundary['status']=='passed' and len(boundary['reconstruction'])==225 and boundary['loader_source_sha256']==sha(R/'scripts/phase6-score-final.py')
 assert boundary['label_perturbation_cases']==30 and boundary['direct_vs_cached_replay_cases']==20 and all(r['max_feature_difference']<1e-10 and r['prefix_check']=='passed' for r in boundary['reconstruction'])
 book_receipt=json.loads((R/'reports/phase5/final-physical-book-receipt-v4.json').read_text());assert book_receipt['status']=='completed' and book_receipt['failures']==0 and len(book_receipt['files'])==177
 baseline=json.loads((P/'phase5-preservation-baseline-v6.json').read_text());expected={r['path']:r['sha256'] for r in baseline['files'] if r['path'].startswith('data/phase5-final-evaluation-books-v4/')};assert {r['path']:r['sha256'] for r in book_receipt['files']}==expected
 selected=json.loads((run/'policy-train-selection-v6.json').read_text());assert selected['selected']['beta']==200 and selected['selected']['penalty']==200
 subsidy=json.loads((run/'green-subsidy-TRAIN-freeze-v6.json').read_text());assert subsidy['status']=='TRAIN_frozen' and not subsidy['final_books_used'] and len(subsidy['groups'])==90
 from pcse_gym.agromas.final_evaluation import validate_external_dependency
 validate_external_dependency(R,R/'reports/phase5/final-evaluation-permit-v4.json')
 for row in json.loads((P/'phase5-preservation-baseline-v6.json').read_text())['files']:assert sha(primary/row['path'])==row['sha256']
 candidates=list((R/active['models']).rglob('*'))+list((R/'NUE_PCSE-Gym/pcse_gym/agromas_v6').glob('*.py'))+list((R/'NUE_PCSE-Gym/pcse_gym/agromas').glob('*.py'))+[R/'scripts'/name for name in ('phase6-score-final.py','phase6-seal-permit.py','phase6-fit.py','phase6-prepare-ppo.py','phase6-ppo.py','phase6-ppo-supervisor.py','phase6-green-subsidy.py','phase6-ppo-frozen-audit.py','phase6-ppo-context-audit.py','phase6-audit-train-boundaries.py')]
 candidates+=[P/'ACTIVE_TRAIN_RUN_V6.json',P/'phase5-preservation-baseline-v6.json',R/'reports/phase5/final-physical-book-receipt-v4.json',R/'reports/phase5/final-policy-evaluation-receipt-v4.json',R/'cache/phase6'/active['run']/'train-book-ppo-inputs-v6.joblib']
 candidates+=list(run.glob('*.json'))
 legacy=json.loads((R/'reports/phase5/final-evaluation-permit-v4.json').read_text());candidates+=[R/name for name in legacy['files']]
 candidates+=list((R/'data/global_regions').rglob('*'))+list((R/'models/phase5/climate-v2').glob('*.joblib'))+list((R/'reports/phase5/regional-model-inputs').rglob('*.json'))+[R/'NUE_PCSE-Gym/pcse_gym/envs/configs/soil/arminda_soil.yaml']
 for path in candidates:
  if path.is_file():files[str(path.relative_to(R))]=sha(path)
 pcse=R/'pcse';commit=subprocess.check_output(['git','-C',str(pcse),'rev-parse','HEAD'],text=True).strip();assert commit=='d1fe6d29de828033b850ec51d994988d8d6d406f';assert not subprocess.check_output(['git','-C',str(pcse),'status','--porcelain'],text=True).strip()
 permit=dict(status='sealed_before_v6_final_scoring',registered_UTC=datetime.now(timezone.utc).isoformat(),scope='Adaptive-Reused Temporal Benchmark',phase5_confirmatory_history_preserved=True,all_models_frozen=True,subsidy_train_frozen=True,train_years=list(range(1995,2010)),selection='5foldouteryearTRAINselectionCV;notunbiasedvalidation',TRAIN_replay_verified=True,Dev_scope='PreservedPhase5physicsreceiptonly;nonewv6Devpolicycampaign',primary_root=str(primary),active_run=active,contexts='90stresscombinationsplusHistoricalcap40price1subsidy0',external_PCSE_commit=commit,ledger_tolerance=dict(N=1e-10,C=1e-9),final_physical_books=book_receipt['files'],runtime_versions=legacy['runtime_versions'],files=files,no_new_native_daily_rollouts=True,no_fitting_after_unlock=True)
 path=P/'final-evaluation-permit-v6.json'
 with path.open('x') as f:json.dump(permit,f,indent=2)
 path.with_suffix('.sha256').write_text(sha(path)+'\n');path.chmod(0o444);path.with_suffix('.sha256').chmod(0o444);print(json.dumps(dict(permit_sha256=sha(path),files=len(files))))
