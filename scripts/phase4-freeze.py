"""Build a reviewed19-asset candidate; --seal only after clean commits and pre-heldout review."""
import pathlib,json,hashlib,sys,subprocess,argparse,pickle,xml.etree.ElementTree as ET
import torch
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
evalmod=SourceFileLoader('freeze_eval',str(R/'scripts/phase4-frozen-eval.py')).load_module();protocol=SourceFileLoader('freeze_protocol',str(R/'scripts/phase4-protocol.py')).load_module()
from pcse_gym.utils.frozen_audit import sha,seal_manifest
from pcse_gym.agent.ppo_mod import LagrangianPPO
from pcse_gym.agent.counterfactual import CounterfactualGRU
CAL=R/'reports/phase3c-frozen-utility-v1.json'
METHODS=['N2-PA','prior160','prior170','prior190','old_SM-adaptiveprior','raw','corrected','masked','guided','full4','utilityprior','cf-gru']

def build():
 torch.set_num_threads(1);amend=json.loads((R/'reports/phase4-protocol-amendment.json').read_text());assert amend['approved'] and amend['option']=='A';gate=json.loads((R/'reports/phase4-counterfactual-dev-gate.json').read_text());assert gate['results']['utilityprior']['passed'] and not gate['results']['cf-gru']['checks']['joint_at_least59_40'];assert gate['input_sha256']==sha(R/'reports/phase4-dev-counterfactual.json');assert sha(R/'reports/phase4-counterfactual-dev-gate.json')==amend['pre_amendment_gate_sha256']
 parity=json.loads((R/'reports/phase4-controller-parity-final.json').read_text());assert parity['all_physical_metrics_exactly_equal'] and parity['verification_seasons']==24
 for key,rel in [('evaluator_sha256','scripts/phase4-frozen-eval.py'),('environment_sha256','scripts/phase4-env.py'),('controller_sha256','scripts/phase4-controller.py'),('verification_script_sha256','scripts/phase4-parity-check.py')]:assert parity[key]==sha(R/rel),rel
 tables=SourceFileLoader('freeze_tables',str(R/'scripts/phase4-summarize.py')).load_module();groups=tables.dev_groups();assert set(groups)==set(METHODS)
 for method,rows in groups.items():
  seeds=[4,17,29] if method in ['raw','corrected','masked','guided','full4','cf-gru'] else [4];assert len(rows)==1500*len(seeds)
  assert len({(r['year'],r['soil'],r['seed']) for r in rows})==len(rows) and all(5000<=r['year']<=5499 for r in rows)
 root=ET.parse(R/'reports/phase4-all-tests.xml').getroot();suites=list(root.iter('testsuite'));assert sum(int(s.get('tests','0')) for s in suites)==71 and all(int(s.get(k,'0'))==0 for s in suites for k in ['failures','errors','skipped'])
 files={};models=[]
 def register(p):
  p=pathlib.Path(p);files[str(p.relative_to(R))]=sha(p)
 for method in ['raw','corrected','masked','guided','full4','cf-gru']:
  for seed in [4,17,29]:
   ck=evalmod.model_asset(method,seed);rec=json.loads((ck.parent/'receipt.json').read_text());assert rec['status']=='completed' and sha(ck)==rec['checkpoint_sha256']
   for rel,h in rec['source_sha256'].items():
    assert sha(R/rel)==h,rel
    snapshot=ck.parent/'source'/rel
    if snapshot.exists():assert sha(snapshot)==h
   if method=='cf-gru':
    m=CounterfactualGRU.load(ck,device='cpu');alpha=rec['selection']['alpha'];assert sha(ck)==amend['original_CF_models'][str(seed)]['checkpoint_sha256'] and alpha==amend['original_CF_models'][str(seed)]['alpha'];params=4908
   else:
    m=LagrangianPPO.load(ck,device='cpu');alpha=None;params=4908 if method=='full4' else 4683;assert rec['actual_steps']==67200 and rec['finite_parameters']
    expected_dual=method!='raw';assert m.dual_update_once==expected_dual
    assert m.gamma==1 and m.gae_lambda==1 and m.active_step_grad and m.learning_rate==.0003 and m.n_epochs==10
    normal=pickle.loads((ck.parent/'normalizer.pkl').read_bytes());assert not normal.norm_obs and not normal.norm_reward;register(ck.parent/'normalizer.pkl')
   assert sum(p.numel() for p in m.parameters())==params if method=='cf-gru' else sum(p.numel() for p in m.policy.parameters())==params
   net=m if method=='cf-gru' else m.policy;assert all(torch.isfinite(p).all() for p in net.parameters());register(ck);register(ck.parent/'receipt.json')
   models.append(dict(model=method,seed=seed,path=str(ck.relative_to(R)),sha256=sha(ck),class_name=type(net).__name__,trainable_parameters=params,frozen_buffer_elements=sum(b.numel() for b in net.buffers()),alpha=alpha,inference_entrypoint='FrozenCUOController' if method=='cf-gru' else 'LagrangianPPO.predict',training_receipt=str((ck.parent/'receipt.json').relative_to(R))))
 register(CAL);assert sha(CAL)==amend['forest_sha256'];models.append(dict(model='utilityprior',seed=None,path=str(CAL.relative_to(R)),sha256=sha(CAL),class_name='UtilityScorer/FrozenCUOController',trainable_neural_parameters=0,tree_count=64,frozen_buffer_elements=37772,inference_entrypoint='FrozenCUOController',seed_aliases=[4,17,29],aliases_are_not_independent_fits=True))
 for repo,package in [('NUE_PCSE-Gym','pcse_gym'),('pcse','pcse')]:
  for p in (R/repo/package).rglob('*'):
   if p.is_file() and p.suffix.lower() in ['.py','.yaml','.yml','.conf','.cab','.crop','.site','.soil']:register(p)
 for p in (R/'NUE_PCSE-Gym/tests/target').glob('test_phase*.py'):register(p)
 for p in (R/'scripts').glob('phase4*.py'):register(p)
 for rel in ['scripts/env.sh','scripts/phase3-run.py','scripts/phase2-run.py','scripts/phase3-report.py','scripts/evaluate-baselines.py','reports/phase4-protocol-amendment.json','reports/phase4-counterfactual-dev-gate.json','reports/phase4-dev-counterfactual.json','reports/phase4-dev-ppo-matrix.json','reports/phase4-dev-metrics-summary.json','reports/phase4-controller-parity.json','reports/phase4-controller-parity-final.json','reports/phase4-calendar-spacing-proof.json','reports/phase4-training-weather-thresholds.json','reports/phase4-all-tests.xml','reports/phase4-cf-extra-provenance.json','reports/phase3c-training-utility-grid.json','reports/phase3b3-frozen-calibration-sm-v1.json','tasks/TASK_PHASE4_PROTOCOL_AMENDMENT_OPTION_A.md','data/52.57-5.63_random_weather.csv','docs/compag2025rl.pdf']:
  register(R/rel)
 for rel in ['reports/phase3b-dev-controls-v3.json','reports/phase3b3-dev-moisture-controls-audited-v3-sm.json','reports/phase3c-dev-full4-v4-sm.json','reports/phase4-contract.md','reports/phase4-ppo-processes.json','reports/phase4-corrected-singledual-processes.json','tasks/TASK_PHASE4_CUO_GRU_FINAL_EVAL.md','scripts/phase3b-report.py']:
  register(R/rel)
 for p in (R/'reports/phase4-eval-source').glob('*.py'):register(p)
 commits={d:subprocess.check_output(['git','-C',str(R/d),'rev-parse','HEAD'],text=True).strip() for d in ['.','NUE_PCSE-Gym','pcse']}
 result=dict(schema_version=1,dev_verified=True,all_checkpoints_frozen=True,cf_point_target_passed=False,primary_policy='utilityprior',exploratory_policy='cf-gru',protocol_amendment='reports/phase4-protocol-amendment.json',models=models,files=files,git_commits=commits,calibration_sha256=sha(CAL),evaluation_methods=METHODS,historical_harvest_years=list(range(1983,2022)),stress_harvest_years=list(range(5500,5999)),expected_unique_scenarios=dict(historical=117,stress=1497,historical_default=39),expected_total_method_seed_soil_episodes=38736,tests_passed=71,one_shot=True,prior_Phase2_audits_preexisted=True,scope='One final frozen-series evaluation; not a claim the legacy benchmark has never been evaluated by the project')
 protocol.check_catalog(result,R);return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seal',action='store_true');a=p.parse_args();payload=build()
 if not a.seal:
  (R/'reports/phase4-freeze-candidate.json').write_text(json.dumps(payload,indent=2));print('Candidate ready:19assets,71tests; heldout stilllocked')
 else:
  for d in ['.','NUE_PCSE-Gym','pcse']:assert not subprocess.check_output(['git','-C',str(R/d),'status','--porcelain'],text=True).strip(),d
  review=R/'reports/phase4-review-final.md';assert review.exists() and 'COMPLETE' in review.read_text() and 'ERROR_CLASS: NONE' in review.read_text()
  digest=seal_manifest(R,payload);print('Sealed one-shot manifest',digest)
