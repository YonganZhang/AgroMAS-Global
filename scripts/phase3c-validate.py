"""Read-only scientific/source/Dev consistency audit, no heldout evaluation."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET,subprocess
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 tests=0
 for file in ['phase3c-tests.xml','phase3c-integration-tests.xml']:
  root=ET.parse(R/'reports'/file).getroot()
  for s in root.iter('testsuite'):
   assert all(int(s.get(k,'0'))==0 for k in ['failures','errors','skipped']);tests+=int(s.get('tests','0'))
 assert tests==60
 runs=[]
 for seed in [4,17,29]:
  f=R/f'reports/phase3c-runs/v4-sm-final-full4-seed{seed}';x=json.loads((f/'receipt.json').read_text())
  assert x['status']=='completed' and x['actual_steps']==67200 and x['parameters_changed'] and x['finite_parameters'] and x['zero_step_prior_agreement']==1 and x['actor_head_L2_change']>0
  assert x['candidate_config']['active_step_grad'] and x['candidate_config']['gae_lambda']==1 and not x['candidate_config']['norm_reward']
  assert all(3002<=y<=4999 for y in x['observed_training_years'])
  for p,h in x['source_sha256'].items():assert sha(R/p)==h and sha(f/'source'/p)==h,p
  assert sha(f/'model.zip')==x['checkpoint_sha256']
  runs.append(dict(seed=seed,checkpoint_sha256=x['checkpoint_sha256'],parameters=x['parameter_count'],frozen_buffer_elements=x['frozen_buffer_elements'],actor_head_L2_change=x['actor_head_L2_change'],actual_steps=x['actual_steps'],source_files=len(x['source_sha256'])))
 e=R/'reports/phase3c-dev-full4-v4-sm.json';data=json.loads(e.read_text());assert data['evaluator_sha256']==sha(R/'scripts/phase3c-dev.py')
 keys=[(r['seed'],r['soil'],z['year']) for r in data['records'] for z in r['episodes']];assert len(keys)==len(set(keys))==4500 and all(5000<=k[2]<=5499 for k in keys)
 gate=json.loads((R/'reports/phase3c-dev-gate-v4-sm.json').read_text());assert gate['input_sha256']==sha(e) and gate['dev_gate_passed']==all(gate['checks'].values())
 if not gate['dev_gate_passed']:assert not (R/'reports/phase3b-heldout-unlock.json').exists()
 old=json.loads((R/'reports/phase3b-final/archive-index.json').read_text())
 for entry in old:assert sha(R/entry['archive'])==entry['sha256']
 cal=R/'reports/phase3c-frozen-utility-v1.json';grid=R/'reports/phase3c-training-utility-grid.json';c=json.loads(cal.read_text());assert c['table_sha256']==sha(grid) and len(c['train_years'])==120 and all(3002<=y<=4999 for y in c['train_years'])
 assert sha(R/'data/52.57-5.63_random_weather.csv')=='16c5e563093da55b65b0f57cb19bbe0b51d537385371bb9c38b9da8cca611a72'
 evidence=dict(tests_passed=tests,runs=runs,gate_checks=gate['checks'],dev_gate_passed=gate['dev_gate_passed'],unique_dev_cases=4500,previous_archive_files_unchanged=len(old),calibration_sha256=sha(cal),utility_table_sha256=sha(grid),evaluator_sha256=sha(R/'scripts/phase3c-dev.py'),test_sha256={str(p.relative_to(R)):sha(p) for p in (R/'NUE_PCSE-Gym/tests/target').glob('test_phase*.py')},weather_sha256=sha(R/'data/52.57-5.63_random_weather.csv'),heldout_started=False)
 (R/'reports/phase3c-validation.json').write_text(json.dumps(evidence,indent=2));print(json.dumps(evidence))
if __name__=='__main__':main()
