"""Fixed-budget TRAIN-book PPO; no physical rollouts, no final-book access."""
from pathlib import Path
import argparse,json,hashlib,time,pickle,csv
import numpy as np,torch,joblib
from stable_baselines3.common.vec_env import DummyVecEnv,VecNormalize
from stable_baselines3.common.callbacks import BaseCallback
from sb3_contrib import MaskablePPO
from pcse_gym.agromas_v6.books import DenseBooks
from pcse_gym.agromas_v6.core import Policy
from pcse_gym.agromas_v6.book_env import TrainBookEnv
R=Path(__file__).resolve().parents[1];P=R/'reports/phase6'
class Curve(BaseCallback):
 def __init__(self,path):super().__init__();self.file=path.open('x');self.writer=csv.writer(self.file);self.writer.writerow(['step','region','year','joint','partial_profit','plan']);self.episodes=0;self.actions={s:set() for s in (1,2,3)}
 def _on_step(self):
  for done,info in zip(self.locals['dones'],self.locals['infos']):
   if done:
    self.episodes+=1;self.writer.writerow([self.num_timesteps,info['region_id'],info['year'],int(info['joint']),info['partial_profit'],json.dumps(info['plan'])])
    for s,a in info['actions']:self.actions[s].add(a)
  return True
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--seed',type=int,choices=[4,17,29],required=True);args=a.parse_args();torch.set_num_threads(1)
 active=json.loads((P/'ACTIVE_TRAIN_RUN_V6.json').read_text());P=R/active['reports'];protocol=json.loads((P/'PPO_TRAIN_PROTOCOL_V6.json').read_text());cache=R/'cache/phase6'/active['run']/'train-book-ppo-inputs-v6.joblib'
 assert hashlib.sha256(cache.read_bytes()).hexdigest()==protocol['cache_sha256'];data,tables,legal=joblib.load(cache)
 selected=json.loads((P/'policy-train-selection-v6.json').read_text())['selected'];policy=Policy(selected['beta'],selected['penalty'])
 out=R/active['models']/f'PPO-structured-seed{args.seed}';out.mkdir(parents=True,exist_ok=False)
 env=VecNormalize(DummyVecEnv([lambda:TrainBookEnv(data,tables,legal,policy) for _ in range(8)]),norm_obs=True,norm_reward=True,clip_obs=1e6,clip_reward=10.,gamma=1.)
 model=MaskablePPO('MlpPolicy',env,seed=args.seed,device='cpu',policy_kwargs=dict(net_arch=dict(pi=[64,64],vf=[64,64])),n_steps=256,batch_size=256,n_epochs=10,gamma=1.,gae_lambda=1.,ent_coef=.01,learning_rate=3e-4,target_kl=.03,verbose=0)
 before=np.concatenate([p.detach().cpu().numpy().ravel() for p in model.policy.parameters()]);callback=Curve(out/'episodes.csv');start=time.monotonic();model.learn(total_timesteps=protocol['decision_steps_per_seed'],callback=callback);elapsed=time.monotonic()-start;callback.file.close()
 after=np.concatenate([p.detach().cpu().numpy().ravel() for p in model.policy.parameters()]);assert np.isfinite(after).all() and np.linalg.norm(after-before)>0
 model.save(out/'model.zip');env.training=False;env.norm_reward=False;env.save(out/'vecnormalize.pkl')
 result=dict(status='completed',seed=args.seed,actual_decision_steps=model.num_timesteps,completed_TRAIN_seasons=callback.episodes,elapsed_seconds=elapsed,parameter_L2_change=float(np.linalg.norm(after-before)),stage_action_indices={s:sorted(v) for s,v in callback.actions.items()},native_daily_rollouts=0,observables=91,normalization_clip=1e6,normalization_frozen=True,checkpoint='Finalfixedbudget;notconvergencecertified',files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()})
 with (out/'receipt.json').open('x') as f:json.dump(result,f,indent=2)
 for p in out.iterdir():p.chmod(0o444)
 print(json.dumps(result),flush=True)
