"""Wait for the authorized missing PPO tiers, then Dev only. Never opens heldout."""
import pathlib,json,time,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[1];start=time.monotonic()
while True:
 p=R/'reports/phase4-ppo-processes.json'
 if p.exists():
  x=json.loads(p.read_text())
  if len(x)==12:
   assert all(r['returncode']==0 for r in x);break
 if time.monotonic()-start>10800:raise TimeoutError('Bounded3hourcampaign wait')
 time.sleep(10)
subprocess.run([sys.executable,str(R/'scripts/phase4-eval.py'),'--models','raw','corrected','masked','guided','--output','reports/phase4-dev-ppo-matrix.json'],cwd=R,check=True)
