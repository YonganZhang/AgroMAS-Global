"""Validate final Phase3 evidence without modifying scientific outputs."""
import pathlib,json,math,hashlib,xml.etree.ElementTree as E,subprocess
import psutil
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def finite(x):
 if isinstance(x,float):assert math.isfinite(x)
 elif isinstance(x,dict):
  for v in x.values():finite(v)
 elif isinstance(x,list):
  for v in x:finite(v)
if __name__=='__main__':
 x=json.loads((R/'reports/phase3_metrics.json').read_text());finite(x);checks={}
 assert x['heldout_phase3_started'] is False
 for name,rows in x['episodes'].items():
  learned=name.startswith('full-');seeds=[4,17,29] if learned else [4]
  keys=[(r['seed'],r['soil'],r['year']) for r in rows]
  expected={(s,soil,y) for s in seeds for soil in ['default','fast','slow'] for y in range(5000,5500)}
  assert len(keys)==len(set(keys)) and set(keys)==expected,(name,len(keys))
  if learned:assert all(r['executed_violation_rate']==0 for r in rows)
 checks['complete_unique_dev_scenarios']={n:len(rs) for n,rs in x['episodes'].items()}
 runs=[]
 for tag,model in [('v1','full'),('v2b','full2')]:
  processes=json.loads((R/f'reports/phase3-{tag}-processes.json').read_text());assert len(processes)==3 and all(p['returncode']==0 for p in processes)
  for seed in [4,17,29]:
   folder=R/f'reports/phase3-runs/{tag}-{model}-seed{seed}';r=json.loads((folder/'receipt.json').read_text());finite(r)
   assert r['status']=='completed' and r['actual_steps']==67200 and r['finite_parameters'] and r['parameters_changed']
   assert r['checkpoint_sha256']==sha(folder/'model.zip');assert all(3002<=y<=4999 for y in r['observed_training_years'])
   if tag=='v2b':
    assert len(r['diagnostic_seasons'])>1000
    for p,digest in r['source_sha256'].items():assert sha(folder/'source'/pathlib.Path(p).name)==digest
   runs.append(dict(run=folder.name,steps=r['actual_steps'],checkpoint_sha256=r['checkpoint_sha256']))
 checks['training_receipts']=runs
 tests=E.parse(R/'reports/phase3-tests-final.xml').getroot()
 suites=[tests] if tests.tag=='testsuite' else list(tests)
 assert all(int(s.attrib.get(k,0))==0 for s in suites for k in ['failures','errors','skipped'])
 checks['tests_passed']=sum(int(s.attrib['tests']) for s in suites)
 evidence=json.loads((R/'reports/phase3-test-evidence.json').read_text())
 assert sha(R/'reports/phase3-tests-final.xml')==evidence['junit_sha256']
 for path,digest in evidence['source_sha256'].items():assert sha(R/path)==digest
 checks['test_source_hashes_match']=True
 assert not subprocess.check_output(['git','-C',str(R/'NUE_PCSE-Gym'),'diff','70265fb','--','pcse_gym/envs/common_env.py'])
 checks['weekly_engine_unchanged_from_phase2']=True
 for g in x['gates'].values():assert not g['final_unlock_pass'],'Passing final gate requires a different held-out delivery workflow'
 checks['gate_failed_and_heldout_locked']=True
 active=[]
 for process in psutil.process_iter(['pid','cmdline']):
  args=process.info['cmdline'] or []
  if len(args)>1 and pathlib.Path(args[1]).name in ['phase3-run.py','phase3-campaign.py','phase3-dev.py','phase3-calibrate.py','phase3-attribution.py']:
   active.append(dict(pid=process.info['pid'],script=pathlib.Path(args[1]).name))
 assert not active,active
 checks['active_phase3_processes']=active
 figure=R/'figures/phase3-breakthrough'
 manifest=json.loads((figure/'manifest.json').read_text())
 for path,digest in manifest['artifacts'].items():assert sha(figure/path)==digest
 for src in [manifest['spec']]+manifest['sources']:assert sha(R/src['path'])==src['sha256']
 qa=json.loads((R/'reports/phase3-figure-review.json').read_text())
 assert qa['verdict']=='PASS' and qa['completion']=='COMPLETE' and qa['reviewed_png_sha256']==sha(figure/'diagram.png')
 checks['figure_hash_and_review_verified']=True
 assets=set((R/'reports/phase3-runs').rglob('*'))|set((R/'reports').glob('phase3-*'))|set((R/'figures/phase3-breakthrough').glob('*'))|set((R/'scripts').glob('phase3-*'))|{R/'reports/phase3_metrics.json',R/'reports/PHASE3_BREAKTHROUGH_RESULTS.md'}
 assets-={R/'reports/phase3-artifact-registry.json',R/'reports/phase3-delivery-validation.json'}
 assets={p for p in assets if p.is_file()}
 registry=dict(assets=[dict(path=str(p.relative_to(R)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(assets)])
 (R/'reports/phase3-artifact-registry.json').write_text(json.dumps(registry,indent=2))
 checks.update(registered_assets=len(assets),source_HEAD=subprocess.check_output(['git','-C',str(R/'NUE_PCSE-Gym'),'rev-parse','HEAD'],text=True).strip(),pcse_HEAD=subprocess.check_output(['git','-C',str(R/'pcse'),'rev-parse','HEAD'],text=True).strip(),registry_sha256=sha(R/'reports/phase3-artifact-registry.json'))
 (R/'reports/phase3-delivery-validation.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks))
