"""Read-only evidence consistency checks for Phase3B3 Dev screening."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
R=pathlib.Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 evidence={}
 tests=ET.parse(R/'reports/phase3b3-tests-sm.xml').getroot();suites=list(tests.iter('testsuite'))
 assert sum(int(s.get('tests','0')) for s in suites)==52
 assert all(int(s.get(k,'0'))==0 for s in suites for k in ['failures','errors','skipped'])
 evidence['tests']=dict(passed=52,failed=0,skipped=0)
 c=R/'reports/phase3b3-frozen-calibration-sm-v1.json';cal=json.loads(c.read_text())
 assert len(cal['train_years'])==50 and all(3002<=y<=4999 for y in cal['train_years'])
 runs={}
 for seed in [4,17,29]:
  f=R/f'reports/phase3b3-runs/v3-sm-full3-seed{seed}';x=json.loads((f/'receipt.json').read_text())
  assert x['status']=='completed' and x['actual_steps']==67200 and x['parameters_changed'] and x['finite_parameters'] and x['parameter_count']==4908
  assert all(3002<=y<=4999 for y in x['observed_training_years'])
  assert digest(f/'model.zip')==x['checkpoint_sha256']
  for p,h in x['source_sha256'].items():assert digest(R/p)==h and digest(f/'source'/p)==h,p
  runs[str(seed)]={k:x[k] for k in ['actual_steps','parameter_count','checkpoint_sha256','parameters_changed','finite_parameters']}
 evidence['runs']=runs
 data=R/'reports/phase3b3-dev-full3-v3-sm.json';x=json.loads(data.read_text());assert x['status']=='completed'
 assert digest(R/'reports/phase3b3-evaluation-source/phase3b3-dev.py')==x['evaluator_sha256']
 keys=[(r['seed'],r['soil'],e['year']) for r in x['records'] for e in r['episodes']]
 assert len(keys)==len(set(keys))==4500 and all(5000<=k[2]<=5499 for k in keys)
 for r in x['records']:assert r['checkpoint_sha256']==runs[str(r['seed'])]['checkpoint_sha256']
 gate=json.loads((R/'reports/phase3b-full3-dev-gate-v3-sm.json').read_text());assert gate['input_sha256']==digest(data)
 assert gate['dev_gate_passed']==all(gate['checks'].values())
 evidence.update(dev_unique_cases=4500,gate=gate['checks'],dev_gate_passed=gate['dev_gate_passed'],calibration_sha256=digest(c))
 if not gate['dev_gate_passed']:
  assert not (R/'reports/phase3b-heldout-unlock.json').exists()
  assert not any((R/'reports').glob('phase3b3-audit-*.json'))
  evidence['heldout_locked']=True
 assert digest(R/'data/52.57-5.63_random_weather.csv')=='16c5e563093da55b65b0f57cb19bbe0b51d537385371bb9c38b9da8cca611a72'
 out=R/'reports/phase3b3-validation.json';out.write_text(json.dumps(evidence,indent=2));print(json.dumps(evidence))
if __name__=='__main__':main()
