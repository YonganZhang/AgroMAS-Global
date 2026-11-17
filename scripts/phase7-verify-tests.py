"""Run real local pytest with byte-exact restoration of generated crop caches."""
from pathlib import Path
import os,sys,json,hashlib,subprocess
R=Path(__file__).resolve().parents[1];P=R/'reports/phase7'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
 label=sys.argv[1]
 branches={name:subprocess.check_output(['git','-C',str(path),'branch','--show-current'],text=True).strip() for name,path in [('root',R),('NUE',R/'NUE_PCSE-Gym')]}
 if label=='postmerge':assert branches=={'root':'master','NUE':'main'},branches
 out=P/f'{label}-full-pytest-v7.txt';assert not out.exists()
 caches=[R/'cache/phase5-regional-config/crop/YAMLCropDataProvider.pkl',R/'NUE_PCSE-Gym/pcse_gym/envs/configs/crop/YAMLCropDataProvider.pkl'];saved={p:(p.read_bytes(),p.stat().st_mode&0o777) for p in caches if p.exists()}
 env=os.environ.copy();env['PYTHONPATH']=os.pathsep.join(map(str,(R/'NUE_PCSE-Gym',R/'pcse',R/'scripts')))
 env.update(PHASE7_TEST_ROOT=str(R),PHASE7_TEST_LABEL=label);env['PYTEST_PLUGINS']=','.join(filter(None,(env.get('PYTEST_PLUGINS',''),'phase7_pytest_import_guard')))
 sys.path[:0]=env['PYTHONPATH'].split(os.pathsep)
 import pcse_gym.agromas_v6.core as core,pcse
 assert Path(core.__file__).resolve().is_relative_to((R/'NUE_PCSE-Gym').resolve());assert Path(pcse.__file__).resolve().is_relative_to((R/'pcse').resolve())
 try:
  for p in saved:p.chmod(0o644)
  with out.open('x') as f:rc=subprocess.run([str(R/'.venv/bin/python'),'-m','pytest','-q'],cwd=R/'NUE_PCSE-Gym',env=env,stdout=f,stderr=subprocess.STDOUT).returncode
 finally:
  for p,(data,mode) in saved.items():
   p.chmod(0o644);p.write_bytes(data);p.chmod(mode);assert p.read_bytes()==data
 baseline=json.loads((P/'preservation-baseline-v7.json').read_text());primary=Path(baseline['primary_root']);changed=[r['path'] for r in baseline['files'] if sha(primary/r['path'])!=r['sha256']];assert not changed
 child=json.loads((P/f'{label}-pytest-import-finish-v7.json').read_text());assert child['pytest_exitstatus']==rc and child['skips']==0
 result=dict(branches=branches,pytest_exit=rc,actual_pytest_child_provenance=child,source_root=str(R),core_source=str(Path(core.__file__).resolve()),PCSE_source=str(Path(pcse.__file__).resolve()),phase5_preserved=len(baseline['files']),caches_restored=True,log=str(out.relative_to(R)))
 (P/f'{label}-test-verification-v7.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));raise SystemExit(rc)
