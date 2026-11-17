"""Bounded orchestration of three fixed TRAIN-only PPO runs."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,sys,time
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8'
if __name__=='__main__':
 deadline=time.monotonic()+3600
 while not (P/'phase8b-PPO-inputs-freeze.json').exists():
  if time.monotonic()>deadline:raise TimeoutError('PPO table preparation timeout')
  time.sleep(5)
 (P/'phase8b-PPO-training-protocol.json').write_text(json.dumps({'seeds':[4,17,29],'decision_steps':151552,'source':'TRAIN1995–2009only','hyperparameters':'matchedv6defaults;noevalbasedextension','policy_inputs':'sensorlesscurrentprefix+frozencausalsurrogatestats;91D;nohiddenLAI/SM/uptake','new_NN_architecture_search':False},indent=2))
 def run(seed):
  with (P/f'phase8b-PPO-seed{seed}.log').open('x') as f:rc=subprocess.run([sys.executable,str(R/'scripts/phase8-train-sensorless-ppo.py'),'--seed',str(seed)],cwd=R,stdout=f,stderr=subprocess.STDOUT).returncode
  if rc:raise RuntimeError(f'PPOseed{seed}failed')
 with ThreadPoolExecutor(max_workers=3) as pool:list(pool.map(run,[4,17,29]))
 (P/'phase8b-PPO-training-complete.json').write_text(json.dumps({'status':'completed','seeds':[4,17,29],'all_final_fixed_budget':True},indent=2));print('All sensorless PPO runs complete',flush=True)
