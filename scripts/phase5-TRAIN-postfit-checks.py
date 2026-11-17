"""After six formal receipts exist, run TRAIN-only audit and replay checks."""
from pathlib import Path
import time,subprocess,sys,json
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5'
if __name__=='__main__':
 deadline=time.monotonic()+10800
 receipts=[R/f'models/phase5/ppo-{m}-seed{s}-v4/receipt.json' for m in ('structured-shared','raw-shared') for s in (4,17,29)]
 while not(all(p.exists() for p in receipts) and (P/'PPO-training-campaign-v4.json').exists()):
  if time.monotonic()>deadline:raise TimeoutError('FormalTRAINreceiptsnotcomplete')
  time.sleep(30)
 for name in ('phase5-ppo-training-audit.py','phase5-check-final-PPO-replay.py'):
  print(json.dumps(dict(starting=name,role='Trainonly')),flush=True)
  subprocess.run([sys.executable,str(R/'scripts'/name)],cwd=R,check=True)
 print('AllpostfitTRAINcheckscompleted;finalsetsremainlocked.',flush=True)
