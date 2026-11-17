"""Bounded wait then one frozen Dev screen; never unlocks any heldout split."""
import pathlib,time,json,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[1];start=time.monotonic()
while True:
 p=R/'reports/phase3c-v4-sm-final-full4-processes.json';c=R/'reports/phase3c-dev-utilityprior-v4-sm.json'
 if p.exists() and c.exists():
  rows=json.loads(p.read_text())
  if len(rows)==3:
   assert all(r['returncode']==0 for r in rows);break
 if time.monotonic()-start>7200:raise TimeoutError('Bounded wait2hours')
 time.sleep(10)
subprocess.run([sys.executable,str(R/'scripts/phase3c-dev.py'),'--models','full4','--tag','v4-sm-final','--output','reports/phase3c-dev-full4-v4-sm.json'],cwd=R,check=True)
subprocess.run([sys.executable,str(R/'scripts/phase3c-gate.py'),'--tag','v4-sm-final'],cwd=R,check=True)
