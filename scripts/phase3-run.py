"""Phase 3 matched budget runner, train-only, no held-out reads."""
import pathlib,sys,json,time,argparse,hashlib
import importlib.metadata,subprocess,platform
import numpy as np
import torch
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
base=SourceFileLoader('phase2_runner',str(R/'scripts/phase2-run.py')).load_module()
from pcse_gym.envs.phase3 import Phase3History,MaskedCostPolicy,LastObservableExtractor
from pcse_gym.envs.constraints import AgronomicShield,corrected_fertilization_action_constraint
from pcse_gym.envs.observable import OBSERVABLE_CROP,CausalGRUExtractor
from pcse_gym.initialize_envs import initialize_env
from pcse_gym.agent.ppo_mod import LagrangianPPO,CostActorCriticPolicy
from stable_baselines3.common.vec_env import VecNormalize,SubprocVecEnv
class Diagnostics(base.SplitAudit):
    def __init__(self):
        super().__init__();self.step_diagnostics=[];self.seasons=[];self.nitrogen=None
    def _on_step(self):
        super()._on_step()
        infos=self.locals['infos'];dones=self.locals['dones']
        if self.nitrogen is None:self.nitrogen=np.zeros(len(infos))
        for i,(done,info) in enumerate(zip(dones,infos)):
            self.nitrogen[i]+=10*info['executed_action']
            self.step_diagnostics.append(dict(valid=info.get('valid_mask_action_count'),delta_dvs=info['application_dvs']-info['proposal_dvs'],intercept=info['shield_triggered']))
            if done:
                nue=float(list(info['NUE'].values())[-1]);surplus=float(list(info['Nsurplus'].values())[-1])
                self.seasons.append(dict(N=self.nitrogen[i],NUE=nue,surplus=surplus,joint=.5<=nue<=.9 and 0<=surplus<=40));self.nitrogen[i]=0
        if self.n_calls%128==0 and hasattr(self,'output'):
            with torch.no_grad():entropy=float(self.model.policy.get_distribution(self.locals['obs_tensor']).entropy().mean())
            self.output.write_text(json.dumps(dict(steps=self.model.num_timesteps,completed_seasons=len(self.seasons),mean_N=float(np.mean([x['N'] for x in self.seasons])) if self.seasons else None,entropy=entropy)))
        return True

MODELS=['raw','corrected','reward','masked','guided','full','full2']
def make_env(model,seed,rank,years=None,soil=None,training=True):
    import logging;logging.disable(logging.CRITICAL)
    years=list(range(3002,5000)) if years is None else years
    if training and not all(3002<=y<=4999 for y in years):raise ValueError('Train firewall')
    if not training and not all(5000<=y<=5499 for y in years):raise ValueError('Held-out remains locked')
    if model in ('raw','corrected'):return base.make_env(model,seed,rank,years,soil,training)
    if model in ('full','full2') and training:soil=['default','fast','slow'][rank%3]
    env=initialize_env(pcse_env=2,crop_features=list(OBSERVABLE_CROP),action_features=[],years=years,locations=[(52.57,5.63)],random_weather=True,random_init=training,reward='NUE',seed=seed+rank,soil='slo' if soil=='slow' else None if soil=='default' else soil,start_type='sowing')
    env=AgronomicShield(env,enabled=model!='reward',n_budget=195)
    return Phase3History(env,history=4 if model in ('guided','full','full2') else 1,aligned=True,guided=model in ('guided','full','full2'),envelope_version=2 if model=='full2' else 1)
def main():
    p=argparse.ArgumentParser();p.add_argument('--model',choices=MODELS,required=True);p.add_argument('--seed',type=int,default=4);p.add_argument('--steps',type=int,default=65536);p.add_argument('--nenvs',type=int,default=15);p.add_argument('--tag',default='v1');a=p.parse_args()
    out=R/'reports/phase3-runs'/f'{a.tag}-{a.model}-seed{a.seed}';out.mkdir(parents=True,exist_ok=False)
    torch.set_num_threads(1);start=time.monotonic();vec=None;receipt=vars(a)|dict(status='started',train_years=[3002,4999])
    snapshot=out/'source';snapshot.mkdir()
    paths=[pathlib.Path(__file__).resolve(),R/'NUE_PCSE-Gym/pcse_gym/envs/phase3.py',R/'NUE_PCSE-Gym/pcse_gym/envs/constraints.py',R/'NUE_PCSE-Gym/pcse_gym/agent/ppo_mod.py',R/'NUE_PCSE-Gym/pcse_gym/envs/observable.py']
    receipt['source_sha256']={}
    for file in paths:
        data=file.read_bytes();receipt['source_sha256'][str(file.relative_to(R))]=hashlib.sha256(data).hexdigest();(snapshot/file.name).write_bytes(data)
    receipt['python']=platform.python_version();receipt['packages']={p:importlib.metadata.version(p) for p in ['torch','stable-baselines3','gymnasium','numpy']}
    receipt['source_head']=subprocess.check_output(['git','-C',str(R/'NUE_PCSE-Gym'),'rev-parse','HEAD'],text=True).strip()
    receipt['env_seeds_and_soils']=[dict(seed=a.seed+i,soil=['default','fast','slow'][i%3] if a.model in ('full','full2') else 'default') for i in range(a.nenvs)]
    try:
        vec=VecNormalize(SubprocVecEnv([lambda rank=i:make_env(a.model,a.seed,rank) for i in range(a.nenvs)],start_method='fork'),norm_obs=False,norm_reward=True,gamma=1.)
        kw=dict(net_arch=dict(pi=[32,32],vf=[32,32]))
        if a.model in ('reward','masked'):kw.update(features_extractor_class=LastObservableExtractor)
        if a.model in ('guided','full','full2'):kw.update(features_extractor_class=CausalGRUExtractor,features_extractor_kwargs=dict(features_dim=7),prior_strength=.5 if a.model=='full2' else 1.,prior_final=170. if a.model=='full2' else 160.)
        policy=CostActorCriticPolicy if a.model in ('raw','corrected','reward') else MaskedCostPolicy
        model=LagrangianPPO(policy,vec,seed=a.seed,learning_rate=.0003,n_steps=128,batch_size=240,n_epochs=10,gamma=1.,gae_lambda=.95,clip_range=.2,ent_coef=.01,constraint_fn=__import__('pcse_gym.agent.ppo_mod',fromlist=['fertilization_action_constraint']).fertilization_action_constraint if a.model=='raw' else corrected_fertilization_action_constraint,constraint_mode='raw' if a.model=='raw' else 'corrected',cvar_alpha=.1 if a.model in ('full','full2') else None,dual_update_once=a.model=='full2',policy_kwargs=kw,device='cpu',verbose=0)
        before=base.hash_policy(model);cb=Diagnostics();cb.output=out/'progress.json';model.learn(total_timesteps=a.steps,callback=cb)
        model.save(str(out/'model.zip'));vec.save(str(out/'normalizer.pkl'))
        receipt.update(status='completed',actual_steps=model.num_timesteps,parameters_changed=base.hash_policy(model)!=before,finite_parameters=all(bool(torch.isfinite(x).all()) for x in model.policy.parameters()),parameter_count=sum(x.numel() for x in model.policy.parameters()),observed_training_years=sorted(cb.years),episode_outcomes=model.episode_outcomes,diagnostic_seasons=cb.seasons,step_diagnostics=cb.step_diagnostics,last_training_logger={k:float(v) for k,v in model.logger.name_to_value.items() if np.isscalar(v)},checkpoint_sha256=hashlib.sha256((out/'model.zip').read_bytes()).hexdigest())
    except BaseException as e:receipt.update(status='failed',error=repr(e));raise
    finally:
        if vec is not None:vec.close()
        receipt['seconds']=time.monotonic()-start;(out/'receipt.json').write_text(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
