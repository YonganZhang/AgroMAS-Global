"""Frozen PPO TRAIN diagnostics without learning or checkpoint selection."""
from pathlib import Path
import hashlib,json,joblib,numpy as np,torch
from stable_baselines3.common.vec_env import DummyVecEnv,VecNormalize
from sb3_contrib import MaskablePPO
from pcse_gym.agromas_v6.core import Policy
from pcse_gym.agromas_v6.book_env import TrainBookEnv
R=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 torch.set_num_threads(1);active=json.loads((R/'reports/phase6/ACTIVE_TRAIN_RUN_V6.json').read_text());p=R/active['reports'];selected=json.loads((p/'policy-train-selection-v6.json').read_text())['selected'];policy=Policy(selected['beta'],selected['penalty'])
 data,tables,legal=joblib.load(R/'cache/phase6'/active['run']/'train-book-ppo-inputs-v6.joblib');records=[]
 for seed in (4,17,29):
  folder=R/active['models']/f'PPO-structured-seed{seed}';before={q.name:hashlib.sha256(q.read_bytes()).hexdigest() for q in folder.iterdir()};env=TrainBookEnv(data,tables,legal,policy);norm=VecNormalize.load(folder/'vecnormalize.pkl',DummyVecEnv([lambda:env]));norm.training=False;norm.norm_reward=False;model=MaskablePPO.load(folder/'model.zip',device='cpu');count=0;clipped=np.zeros(91,int);maxima=np.zeros(91);joints=[]
  for episode in range(225):
   obs,_=env.reset(seed=seed*1000+episode);ended=False
   while not ended:
    z=(obs-norm.obs_rms.mean)/np.sqrt(norm.obs_rms.var+norm.epsilon);clipped+=np.abs(z)>norm.clip_obs;maxima=np.maximum(maxima,np.abs(z));mask=env.action_masks();action,_=model.predict(norm.normalize_obs(obs[None]),deterministic=True,action_masks=mask[None]);assert mask[int(action[0])];obs,reward,ended,_,info=env.step(int(action[0]));count+=1
   joints.append(info['joint'])
  assert before=={q.name:hashlib.sha256(q.read_bytes()).hexdigest() for q in folder.iterdir()}
  records.append(dict(seed=seed,episodes=225,decisions=count,clipped_counts_by_feature=clipped.tolist(),max_abs_standardized_by_feature=maxima.tolist(),joint_resampled_TRAIN=float(np.mean(joints)),all_actions_mask_valid=True,weights_and_normalizer_unchanged=True))
 with (p/'PPO-frozen-TRAIN-diagnostic-v6.json').open('x') as f:json.dump(dict(scope='TRAINdescriptivefrozencheckpointdiagnostic;notselection;notconvergence',training_reward_transform=dict(normalized=True,clip=10,gamma=1),evaluation_reward_normalization=False,records=records),f,indent=2)
