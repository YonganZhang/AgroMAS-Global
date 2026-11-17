"""Matched from-scratch native LagrangianPPO experiment. No evaluation in learn()."""
import argparse, pathlib, sys, json, time, hashlib, os
import numpy as np
import torch
R=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
from pcse_gym.initialize_envs import initialize_env
from pcse_gym.envs.constraints import AgronomicShield, fertilization_action_constraint
from pcse_gym.envs.observable import ObservableHistory,CausalGRUExtractor,OBSERVABLE_CROP
from pcse_gym.agent.ppo_mod import LagrangianPPO,CostActorCriticPolicy
from stable_baselines3.common.vec_env import SubprocVecEnv,VecNormalize
from stable_baselines3.common.callbacks import BaseCallback

MODELS=['raw','corrected','shield','recurrent','full']
def make_env(model,seed,rank,years=None,soil=None,training=True):
    import logging;logging.disable(logging.CRITICAL)
    years=list(range(3002,5000)) if years is None else years
    if training and not set(years).issubset(set(range(3002,5000))): raise ValueError('Training split violation')
    env=initialize_env(pcse_env=2,crop_features=list(OBSERVABLE_CROP),action_features=[],
        years=years,locations=[(52.57,5.63)],random_weather=True,random_init=training,
        reward='NUE',seed=seed+rank,soil='slo' if soil=='slow' else soil,start_type='sowing')
    env=AgronomicShield(env,enabled=model in ('shield','recurrent','full'))
    return ObservableHistory(env,history=4 if model in ('recurrent','full') else 1)

class SplitAudit(BaseCallback):
    def __init__(self):super().__init__();self.years=set();self.episode_count=0
    def _on_step(self):
        for done,info in zip(self.locals['dones'],self.locals['infos']):
            if done:
                dates=list(info['DVS']);year=dates[-1].year
                assert 3002<=year<=4999, year
                self.years.add(year);self.episode_count+=1
        return True

def hash_policy(m):return hashlib.sha256(b''.join(x.detach().cpu().numpy().tobytes() for x in m.policy.parameters())).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--model',choices=MODELS,required=True);ap.add_argument('--seed',type=int,default=4);ap.add_argument('--steps',type=int,default=32768);ap.add_argument('--nenvs',type=int,default=16);ap.add_argument('--tag',default='matched-v2');a=ap.parse_args()
    torch.set_num_threads(1)
    out=R/'reports/phase2-runs'/f'{a.tag}-{a.model}-seed{a.seed}-env{a.nenvs}';out.mkdir(parents=True,exist_ok=True)
    if (out/'receipt.json').exists():raise RuntimeError('Refuse overwrite of existing run evidence')
    vec=None;start=time.monotonic();receipt=vars(a)|{'status':'started','train_years':[3002,4999],'initialized_from_scratch':True,'phase1_weights_used':False}
    try:
        vec=VecNormalize(SubprocVecEnv([lambda rank=i:make_env(a.model,a.seed,rank) for i in range(a.nenvs)],start_method='fork'),norm_obs=False,norm_reward=True,gamma=1.)
        policy_kwargs=dict(net_arch=dict(pi=[32,32],vf=[32,32]))
        if a.model in ('recurrent','full'):policy_kwargs.update(features_extractor_class=CausalGRUExtractor,features_extractor_kwargs={'features_dim':8})
        model=LagrangianPPO(CostActorCriticPolicy,vec,seed=a.seed,learning_rate=.001,n_steps=128,batch_size=256,n_epochs=10,gamma=1.,gae_lambda=.95,clip_range=.2,ent_coef=0.,
            constraint_fn=__import__('pcse_gym.agent.ppo_mod',fromlist=['fertilization_action_constraint']).fertilization_action_constraint if a.model=='raw' else __import__('pcse_gym.envs.constraints',fromlist=['corrected_fertilization_action_constraint']).corrected_fertilization_action_constraint,
            constraint_mode='raw' if a.model=='raw' else 'corrected',cvar_alpha=.25 if a.model=='full' else None,
            policy_kwargs=policy_kwargs,device='cpu',verbose=0,tensorboard_log=str(out/'tensorboard'))
        count=sum(p.numel() for p in model.policy.parameters())
        assert count in (4587,4875), count
        before=hash_policy(model);cb=SplitAudit();learn_start=time.monotonic()
        model.learn(total_timesteps=a.steps,callback=cb)
        learn_seconds=time.monotonic()-learn_start
        model.save(str(out/'model.zip'));vec.save(str(out/'normalizer.pkl'))
        receipt.update(status='completed',actual_steps=model.num_timesteps,learn_seconds=learn_seconds,steps_per_second=model.num_timesteps/learn_seconds,
            initial_policy_sha256=before,final_policy_sha256=hash_policy(model),parameters_changed=before!=hash_policy(model),
            parameter_count=sum(p.numel() for p in model.policy.parameters()),observed_training_years=sorted(cb.years),completed_training_episodes=cb.episode_count,
            episode_outcomes=model.episode_outcomes,finite_parameters=all(bool(torch.isfinite(p).all()) for p in model.policy.parameters()))
    except BaseException as e:
        receipt.update(status='failed',error=repr(e));raise
    finally:
        if vec is not None:vec.close()
        receipt.update(total_seconds=time.monotonic()-start,vec_env_closed=True)
        (out/'receipt.json').write_text(json.dumps(receipt,indent=2))
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['episode_outcomes','observed_training_years']}))
if __name__=='__main__':main()
