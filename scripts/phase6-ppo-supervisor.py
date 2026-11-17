"""Launch the three preregistered TRAIN PPO seeds and retain actual process exits."""
from pathlib import Path
import json,subprocess,time,sys,hashlib
R=Path(__file__).resolve().parents[1];P=R/'reports/phase6'
if __name__=='__main__':
 active=json.loads((P/'ACTIVE_TRAIN_RUN_V6.json').read_text());p=R/active['reports'];protocol=json.loads((p/'PPO_TRAIN_PROTOCOL_V6.json').read_text());jobs=[];start=time.monotonic()
 sources={str(x.relative_to(R)):hashlib.sha256(x.read_bytes()).hexdigest() for x in [R/'scripts/phase6-ppo.py',R/'NUE_PCSE-Gym/pcse_gym/agromas_v6/book_env.py',R/'NUE_PCSE-Gym/pcse_gym/agromas_v6/core.py']}
 with (p/'PPO-source-freeze-v6.json').open('x') as f:json.dump(dict(files=sources,protocol_sha256=hashlib.sha256((p/'PPO_TRAIN_PROTOCOL_V6.json').read_bytes()).hexdigest(),final_books_opened=False),f,indent=2)
 for seed in protocol['seeds']:
  command=[sys.executable,str(R/'scripts/phase6-ppo.py'),'--seed',str(seed)];log=(p/f'ppo-seed{seed}-v6.log').open('x');proc=subprocess.Popen(command,cwd=R,stdout=log,stderr=subprocess.STDOUT);jobs.append((seed,command,proc,log))
 results=[]
 for seed,command,proc,log in jobs:code=proc.wait();log.close();results.append(dict(seed=seed,command=command,exit_code=code))
 with (p/'PPO-campaign-v6.json').open('x') as f:json.dump(dict(status='completed' if all(x['exit_code']==0 for x in results) else 'failed',jobs=results,elapsed_seconds=time.monotonic()-start),f,indent=2)
 if any(x['exit_code'] for x in results):raise SystemExit(1)
