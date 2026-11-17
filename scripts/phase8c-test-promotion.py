"""Meaningful isolated safety checks for the artifact promotion boundary."""
from pathlib import Path
import tempfile,subprocess,json,sys
R=Path(__file__).resolve().parents[1];base=R/'cache/phase8c-promotion-fixture';base.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(dir=base) as td:
 t=Path(td);s=t/'source';d=t/'target'
 for rel,body in [('data/phase8c-demo/z-result','native-result'),('models/phase8c-controls/demo/model.zip','frozen-weight'),('cache/phase8c-demo/input','runtime'),('cache/phase8c-top.log','top-level-log'),('reports/phase8/report','report'),('_reports/review/result','private-review')]:
  p=s/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body)
 (s/'_reports/review/private-link').symlink_to(s/'_reports/review/result');(s/'_reports/review/report-link').symlink_to('../../reports/phase8/report')
 (s/'data/phase8c-demo/a-link').symlink_to(s/'data/phase8c-demo/z-result');(s/'cache/phase8c-demo/alias').symlink_to('input')
 cmd=[sys.executable,str(R/'scripts/phase8c-promote-local-artifacts.py'),'--source',str(s),'--target',str(d),'--apply'];r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr
 assert (d/'data/phase8c-demo/a-link').read_text()=='native-result';assert str(d) in str((d/'data/phase8c-demo/a-link').readlink())
 assert (d/'cache/phase8c-raw-external-reviews/review/private-link').read_text()=='private-review';assert (d/'cache/phase8c-raw-external-reviews/review/report-link').read_text()=='report'
 assert (d/'cache/phase8c-raw-external-reviews/review/result').stat().st_mode&0o777==0o600
 assert subprocess.run(cmd,capture_output=True).returncode==0
 assert (d/'cache/phase8c-top.log').read_text()=='top-level-log'
 link=d/'data/phase8c-demo/a-link';wanted=link.readlink();link.unlink();link.symlink_to(s/'data/phase8c-demo/z-result');assert subprocess.run(cmd,capture_output=True).returncode!=0;link.unlink();link.symlink_to(wanted)
 regular=d/'cache/phase8c-demo/input';regular.unlink();outside=t/'outside';regular.symlink_to(outside);assert subprocess.run(cmd,capture_output=True).returncode!=0;assert not outside.exists();regular.unlink();regular.write_text('runtime')
 (d/'models/phase8c-controls/demo/model.zip').write_text('do-not-overwrite');r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode!=0 and 'Refusing different existing target' in r.stderr
 assert (d/'models/phase8c-controls/demo/model.zip').read_text()=='do-not-overwrite'
# An interrupted copy publishes no partial file and a normal retry completes.
with tempfile.TemporaryDirectory(dir=base) as td:
 t=Path(td);source=t/'source';target=t/'target'
 for rel in ['data/phase8c-demo/result','models/phase8c-controls/weight','reports/phase8/report']:
  q=source/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_text('original-evidence')
 import runpy,unittest.mock
 old=sys.argv;sys.argv=['promotion','--source',str(source),'--target',str(target),'--apply']
 def interrupted(origin,dest,*args):dest.write(b'partial');raise OSError('injected copy interruption')
 try:
  with unittest.mock.patch('shutil.copyfileobj',interrupted):
   try:runpy.run_path(str(R/'scripts/phase8c-promote-local-artifacts.py'),run_name='__main__')
   except OSError as ex:assert 'injected' in str(ex)
   else:raise AssertionError('Interruption was not propagated')
 finally:sys.argv=old
 assert not (target/'data/phase8c-demo/result').exists();assert not list(target.rglob('.phase8c-copy-*'))
 cmd=[sys.executable,str(R/'scripts/phase8c-promote-local-artifacts.py'),'--source',str(source),'--target',str(target),'--apply'];r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr
(R/'reports/phase8/phase8c-promotion-isolated-tests.json').write_text(json.dumps(dict(passed=True,checks=['all file classes copied','absolute worktree symlink retargeted','relative symlink retained','private absolute and cross-root relative links retargeted','private permissions','top-level cache file retained','source-pointing link rejected','dangling target rejected without external write','interrupted copy never published and retry succeeded','idempotent retry','different destination rejected without overwrite']),indent=2));print('PASS: eleven isolated promotion safety checks')
