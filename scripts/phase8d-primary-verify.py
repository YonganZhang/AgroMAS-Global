"""Post-merge verification on actual primary source, with new receipt names."""
from pathlib import Path
import hashlib,json,os,subprocess,sys,time,re
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';EXPECTED=Path('/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体')
if __name__=='__main__':
 assert R==EXPECTED,'Run only after merging into actual primary'
 import pcse_gym.agromas_v8.models as models
 assert Path(models.__file__).resolve().is_relative_to(R/'NUE_PCSE-Gym')
 assert subprocess.check_output(['git','-C',str(R/'NUE_PCSE-Gym'),'branch','--show-current'],text=True).strip()=='main'
 assert subprocess.check_output(['git','-C',str(R),'branch','--show-current'],text=True).strip()=='master'
 started=time.monotonic();canonical=[str(R/'NUE_PCSE-Gym/tests/target'),str(R/'NUE_PCSE-Gym/tests/phase8'),str(R/'NUE_PCSE-Gym/tests/phase8d')]+[str(p) for p in (R/'NUE_PCSE-Gym/tests').glob('test_phase8*.py')]
 with (P/'phase8d-primary-canonical-tests.log').open('x') as log:rc=subprocess.run([str(R/'.venv/bin/python'),'-m','pytest','-q',*canonical],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 assert rc==0,'Primary canonical suite failed; retain log'
 canonical_text=(P/'phase8d-primary-canonical-tests.log').read_text();passed=int(re.findall(r'(\d+) passed',canonical_text)[-1]);assert passed>=232
 assert not re.search(r'\d+ skipped',canonical_text)
 scripts=['phase8d-verify-online-invariance.py','phase8d-verify-positive-action-invariance.py','phase8d-final-hard-online.py','phase8d-final-hard-positive-action.py'];records=[]
 interpreter=R/'cache/phase8b-venv/bin/python'
 for name in scripts:
  path=R/'scripts'/name;source=path.read_text();command="from pathlib import Path; p=Path("+repr(str(path))+"); exec(compile(p.read_text().replace('/phase8d-', '/phase8d-primary-'),str(p),'exec'),{'__name__':'__main__','__file__':str(p)})"
  with (P/('phase8d-primary-'+name.removeprefix('phase8d-')+'.log')).open('x') as log:exit_code=subprocess.run([str(interpreter),'-c',command],cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
  assert exit_code==0,name;records.append(dict(script=name,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),exit_code=exit_code,only_transformation='write results to distinct phase8d-primary names'))
 for name in ('online-action-invariance','positive-action-invariance','online-action-invariance-tree','positive-action-invariance-tree'):assert json.loads((P/f'phase8d-primary-{name}.json').read_text())['passed']==30
 subprocess.run(['git','-C',str(R/'NUE_PCSE-Gym'),'restore','--','pcse_gym/envs/configs/crop/YAMLCropDataProvider.pkl'],check=True)
 receipt=dict(actual_primary_source=str(Path(models.__file__).resolve()),canonical_exit_code=rc,canonical_passed=passed,canonical_skipped=0,canonical_log_sha256=hashlib.sha256((P/'phase8d-primary-canonical-tests.log').read_bytes()).hexdigest(),future_weather_invariance_passed=120,scripts=records,elapsed_seconds=time.monotonic()-started,root_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),NUE_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R/'NUE_PCSE-Gym',text=True).strip())
 (P/'phase8d-primary-verification.json').write_text(json.dumps(receipt,indent=2));print('PASS: actual primary canonical suite and120 future-weather invariance checks')
