"""Wait for this exact three-seed campaign, then screen Dev only. Never unlock heldout."""
import pathlib,time,json,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[1]
receipt=R/'reports/phase3b3-v3-sm-full3-processes.json'
start=time.monotonic()
while True:
 if receipt.exists():
  rows=json.loads(receipt.read_text())
  if len(rows)==3:
   assert all(r['returncode']==0 for r in rows);break
 if time.monotonic()-start>7200:raise TimeoutError('Bounded campaign wait exceeded2hours')
 time.sleep(10)
subprocess.run([sys.executable,str(R/'scripts/phase3b3-dev.py'),'--models','full3','--tag','v3-sm','--output','reports/phase3b3-dev-full3-v3-sm.json'],cwd=R,check=True)
subprocess.run([sys.executable,str(R/'scripts/phase3b-gate.py'),'--input','reports/phase3b3-dev-full3-v3-sm.json','--output','reports/phase3b-full3-dev-gate-v3-sm.json'],cwd=R,check=True)
