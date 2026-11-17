"""Matched fixed-budget sensorless structured PPO, no evaluation-label access."""
from pathlib import Path
import argparse,csv,hashlib,json,pickle,time
import numpy as np,torch,joblib
from stable_baselines3.common.vec_env import DummyVecEnv,VecNormalize
from stable_baselines3.common.callbacks import BaseCallback
from sb3_contrib import MaskablePPO
from pcse_gym.agromas_v8.book_policy import TrainSensorlessBookEnv
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8'
class Curve(BaseCallback):
 def __init__(self,path):
  super().__init__();self.file=path.open('x');self.w=csv.writer(self.file);self.w.writerow(['step','region','year','joint','profit','plan_index','cap','price','subsidy']);self.episodes=0;self.actions={s:set() for s in [1,2,3]}
 def _on_step(self):
  for done,info in zip(self.locals['dones'],self.locals['infos']):
   if done:
    self.episodes+=1;self.w.writerow([self.num_timesteps,info['region'],info['year'],int(info['joint']),info['partial_profit'],info['plan_index'],info['cap'],info['price'],info['subsidy']])
    for s,a in info['actions']:self.actions[s].add(a)
  return True
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--seed',type=int,choices=[4,17,29],required=True);args=a.parse_args();torch.set_num_threads(1)
 freeze=json.loads((P/'phase8b-PPO-inputs-freeze.json').read_text());path=R/freeze['cache_path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==freeze['cache_sha256'];data,tables=joblib.load(path)
 out=R/f'models/phase8-controls/PPO-Sensorless-seed{args.seed}';out.mkdir(exist_ok=False)
 env=VecNormalize(DummyVecEnv([lambda:TrainSensorlessBookEnv(data,tables) for _ in range(8)]),norm_obs=True,norm_reward=True,clip_obs=1e6,clip_reward=10,gamma=1.)
 model=MaskablePPO('MlpPolicy',env,seed=args.seed,device='cpu',policy_kwargs=dict(net_arch=dict(pi=[64,64],vf=[64,64])),n_steps=256,batch_size=256,n_epochs=10,gamma=1.,gae_lambda=1.,ent_coef=.01,learning_rate=3e-4,target_kl=.03,verbose=0)
 before=np.concatenate([p.detach().numpy().ravel() for p in model.policy.parameters()]);curve=Curve(out/'episodes.csv');tick=time.monotonic();model.learn(total_timesteps=151552,callback=curve);elapsed=time.monotonic()-tick;curve.file.close();after=np.concatenate([p.detach().numpy().ravel() for p in model.policy.parameters()]);assert np.isfinite(after).all() and np.linalg.norm(after-before)>0
 model.save(out/'model.zip');env.training=False;env.norm_reward=False;env.save(out/'vecnormalize.pkl');rec={'status':'completed','seed':args.seed,'decision_steps':model.num_timesteps,'episodes':curve.episodes,'elapsed_seconds':elapsed,'weight_change_L2':float(np.linalg.norm(after-before)),'action_indices':{s:sorted(v) for s,v in curve.actions.items()},'observation_dim':91,'native_physics_calls':0,'TRAIN_only_rewards':True,'tool_calibration':'samefrozenDevcalibrationasallnewpolicyvariants','checkpoint':'finalfixedbudgetnotselectedbyDevorevaluation','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()}}
 (out/'receipt.json').write_text(json.dumps(rec,indent=2));[p.chmod(0o444) for p in out.iterdir()];print(json.dumps(rec))
