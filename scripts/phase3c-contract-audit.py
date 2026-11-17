"""Independent frozen contract/provenance audit. Does not change models or base gate."""
import pathlib,json,hashlib,sys,pickle,subprocess
import torch
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
SourceFileLoader('contract_runner',str(R/'scripts/phase3c-run.py')).load_module()
from pcse_gym.agent.ppo_mod import LagrangianPPO
from pcse_gym.envs.moisture4 import UtilityScorer
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
 torch.set_num_threads(1);c=json.loads((R/'reports/phase3c-frozen-utility-v1.json').read_text());gate=json.loads((R/'reports/phase3c-dev-gate-v4-sm.json').read_text());data=json.loads((R/'reports/phase3c-dev-full4-v4-sm.json').read_text());prior=json.loads((R/'reports/phase3c-dev-utilityprior-v4-sm.json').read_text());rows=[e for rec in data['records'] for e in rec['episodes']];runs=[]
 assert data['evaluator_sha256']==prior['evaluator_sha256']==sha(R/'scripts/phase3c-dev.py')
 assert data['runner_sha256']==prior['runner_sha256']==sha(R/'scripts/phase3c-run.py')
 assert data['calibration_sha256']==prior['calibration_sha256']==sha(R/'reports/phase3c-frozen-utility-v1.json')
 for seed in [4,17,29]:
  f=R/f'reports/phase3c-runs/v4-sm-final-full4-seed{seed}';receipt=json.loads((f/'receipt.json').read_text());m=LagrangianPPO.load(f/'model.zip',device='cpu');normal=pickle.loads((f/'normalizer.pkl').read_bytes())
  expected=dict(gamma=1.,gae_lambda=1.,learning_rate=.0003,n_steps=128,batch_size=240,n_epochs=10,ent_coef=.01,target_kl=.03,active_step_grad=True,active_mask_offset=11,cvar_alpha=.1,dual_update_once=True,endpoint_cost_mode='upper_surplus')
  for key,value in expected.items():assert getattr(m,key)==value,(key,getattr(m,key),value)
  assert not normal.norm_reward and not normal.norm_obs and normal.gamma==1
  assert m.policy.prior_strength==.1 and m.policy.utility_calibration==c
  assert sum(x.numel() for x in m.policy.parameters())==4908 and sum(x.numel() for x in m.policy.buffers())==37772
  assert all(torch.isfinite(x).all() for x in m.policy.parameters())
  for key,value in UtilityScorer(c).state_dict().items():assert torch.equal(m.policy.utility_model.state_dict()[key],value)
  assert sha(f/'model.zip')==receipt['checkpoint_sha256']
  for path,h in receipt['source_sha256'].items():assert sha(R/path)==h and sha(f/'source'/path)==h
  runs.append(dict(seed=seed,frozen_contract_matches=True,actual_steps=receipt['actual_steps'],parameter_count=4908,frozen_buffer_elements=37772))
 helpers={}
 for rel in ['scripts/phase3-report.py','scripts/evaluate-baselines.py']:
  before=subprocess.check_output(['git','show','6e16aba42adcfa5fcbf5adacb78ba91199cf20b5:'+rel]);assert hashlib.sha256(before).hexdigest()==sha(R/rel);helpers[rel]=dict(sha256=sha(R/rel),unchanged_since_pre_v4_commit='6e16aba42adcfa5fcbf5adacb78ba91199cf20b5')
 refs={str(p.relative_to(R)):sha(p) for p in [R/'reports/phase3b-dev-controls-v3.json',R/'reports/phase3b3-dev-moisture-controls-audited-v3-sm.json',R/'reports/phase3c-dev-utilityprior-v4-sm.json']}
 grid=json.loads((R/'reports/phase3c-training-utility-grid.json').read_text());assert len(grid['records'])==360 and all(3002<=rec['year']<=4999 for rec in grid['records'])
 assert c['table_sha256']==sha(R/'reports/phase3c-training-utility-grid.json')
 checks=dict(frozen_models_and_prior_match=True,metrics_helpers_unchanged=True,reference_hashes_registered=True,evaluator_calibration_equal=True,proposed_safe=all(e['proposed_violation_rate']==0 for e in rows),all_seasons_N_in_150_210=all(150<=e['actual_N']<=210 for e in rows),all_soils_vary_each_seed=all(all(z>0 for z in a['by_soil_std'].values()) for a in gate['adaptation'].values()))
 output=dict(audit_checks=checks,effective_gate_passed=gate['dev_gate_passed'] and all(checks.values()),base_gate_passed=gate['dev_gate_passed'],runs=runs,evaluator_helpers=helpers,reference_sha256=refs,test_sources={str(p.relative_to(R)):sha(p) for p in (R/'NUE_PCSE-Gym/tests/target').glob('test_phase*.py')},test_results={f:sha(R/'reports'/f) for f in ['phase3c-tests.xml','phase3c-integration-tests.xml']},weather_sha256=sha(R/'data/52.57-5.63_random_weather.csv'),meaning='Supplemental contract audit; no base statistical threshold changed; extra coverage checks cannot turn a failed base gate into success')
 out=R/'reports/phase3c-contract-audit.json';out.write_text(json.dumps(output,indent=2));print(json.dumps(dict(checks=checks,effective_gate_passed=output['effective_gate_passed'])))
