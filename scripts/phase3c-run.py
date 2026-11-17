"""Version4 native PPO, frozen train calibration, complete launch source snapshot."""
import pathlib,sys,json,time,argparse,hashlib,subprocess,platform,importlib.metadata
import numpy as np
import torch
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
base=SourceFileLoader('phase3b_base',str(R/'scripts/phase3-run.py')).load_module()
from pcse_gym.envs.moisture import VisibleFrameExtractor,StripWaterMask
from pcse_gym.envs.moisture4 import Moisture4History,AdaptiveMoisturePolicy
from pcse_gym.envs.phase3 import LastObservableExtractor
from pcse_gym.envs.constraints import AgronomicShield,upper_surplus_constraint,corrected_fertilization_action_constraint
from pcse_gym.envs.observable import OBSERVABLE_CROP,CausalGRUExtractor
from pcse_gym.initialize_envs import initialize_env
from pcse_gym.agent.ppo_mod import LagrangianPPO,CostActorCriticPolicy
from stable_baselines3.common.vec_env import VecNormalize,SubprocVecEnv
MODELS=['raw','corrected','masked','guided','full4']
CAL=R/'reports/phase3c-frozen-utility-v1.json'
def calibration():
    x=json.loads(CAL.read_text());assert all(3002<=y<=4999 for y in x['train_years']);return x

def make_env(model,seed,rank,years=None,soil=None,training=True,audit=False):
    import logging;logging.disable(logging.CRITICAL)
    years=list(range(3002,5000)) if years is None else list(years)
    if training and not all(3002<=y<=4999 for y in years):raise ValueError('Train firewall')
    if not training and not all(5000<=y<=5499 for y in years):
        unlock=R/'reports/phase3b-heldout-unlock.json'
        if not audit or not unlock.exists():raise ValueError('Heldout locked')
        u=json.loads(unlock.read_text());assert u['dev_gate_passed'] and u['all_checkpoints_frozen']
        assert all(y in set(range(1983,2022))|set(range(5500,5999)) for y in years)
        assert hashlib.sha256(CAL.read_bytes()).hexdigest()==u['calibration_sha256']
    if model=='full4' and training:soil=['default','fast','slow'][rank%3]
    c=calibration();v3=model not in ['raw','corrected']
    env=initialize_env(pcse_env=2,crop_features=list(OBSERVABLE_CROP),action_features=[],years=years,locations=[(52.57,5.63)],random_weather=True,random_init=training,reward='NUE',seed=seed+rank,soil='slo' if soil=='slow' else None if soil=='default' else soil,start_type='sowing')
    h=Moisture4History(AgronomicShield(env,enabled=v3,n_budget=210 if v3 else 0,max_applications=3 if model in ['guided','full4'] else 4),history=4 if model in ['guided','full4'] else 1,guided=model in ['guided','full4'],calibration=c,stages=c['stages'],joint_bonus=c['joint_bonus'],aligned=v3,budget=v3)
    return h if v3 else StripWaterMask(h)

def snapshot(out):
    hashes={};source=out/'source';source.mkdir()
    paths=[pathlib.Path(__file__).resolve(),R/'scripts/phase3-run.py',R/'scripts/phase2-run.py',R/'scripts/env.sh',R/'scripts/phase3c-dev.py',R/'scripts/phase3c-gate.py',R/'scripts/phase3c-calibrate.py',R/'scripts/phase3c-fit.py',R/'NUE_PCSE-Gym/tests/target/test_phase2.py',R/'NUE_PCSE-Gym/tests/target/test_phase3.py',R/'NUE_PCSE-Gym/tests/target/test_phase4.py',R/'reports/phase3c-training-utility-grid.json',CAL]
    for repo,package in [('NUE_PCSE-Gym','pcse_gym'),('pcse','pcse')]:
        paths += [p for p in (R/repo/package).rglob('*') if p.is_file() and p.suffix in ['.py','.yaml','.yml','.conf']]
    for p in sorted(set(paths)):
        rel=p.relative_to(R);dst=source/rel;dst.parent.mkdir(parents=True,exist_ok=True);data=p.read_bytes();dst.write_bytes(data);hashes[str(rel)]=hashlib.sha256(data).hexdigest()
    return hashes

def main():
    p=argparse.ArgumentParser();p.add_argument('--model',choices=MODELS,required=True);p.add_argument('--seed',type=int,default=4);p.add_argument('--steps',type=int,default=65536);p.add_argument('--nenvs',type=int,default=15);p.add_argument('--tag',default='v4-sm');a=p.parse_args()
    out=R/f'reports/phase3c-runs/{a.tag}-{a.model}-seed{a.seed}';out.mkdir(parents=True,exist_ok=False)
    torch.set_num_threads(1);start=time.monotonic();vec=None;receipt=vars(a)|dict(status='started',train_harvest_years=[3002,4999])
    try:
        c=calibration();receipt['candidate_config']=dict(calibration=c,prior_final='state_adaptive_utility_argmax',prior_strength=.1 if a.model in ['guided','full4'] else 0,active_step_grad=True,gae_lambda=1.,norm_reward=False,stage_exact=True,endpoint_cost_mode='upper_surplus' if a.model not in ['raw','corrected'] else 'joint',cvar_alpha=.1 if a.model=='full4' else None)
        receipt['env_seeds_and_soils']=[dict(seed=a.seed+i,soil=['default','fast','slow'][i%3] if a.model=='full4' else 'default') for i in range(a.nenvs)]
        receipt['source_sha256']=snapshot(out);receipt['repositories']={s:dict(head=subprocess.check_output(['git','-C',str(R/s),'rev-parse','HEAD'],text=True).strip(),status=subprocess.check_output(['git','-C',str(R/s),'status','--porcelain'],text=True)) for s in ['.','NUE_PCSE-Gym','pcse']}
        receipt['packages']={p:importlib.metadata.version(p) for p in ['torch','numpy','gymnasium','stable-baselines3']};receipt['python']=platform.python_version()
        vec=VecNormalize(SubprocVecEnv([lambda rank=i:make_env(a.model,a.seed,rank) for i in range(a.nenvs)],start_method='fork'),norm_obs=False,norm_reward=False,gamma=1.)
        kw=dict(net_arch=dict(pi=[32,32],vf=[32,32]));guided=a.model in ['guided','full4'];v3=a.model not in ['raw','corrected']
        if guided:kw.update(features_extractor_class=CausalGRUExtractor,features_extractor_kwargs=dict(features_dim=7),prior_strength=.1,prior_final=190,stages=c['stages'],utility_calibration=c)
        elif v3:kw.update(features_extractor_class=VisibleFrameExtractor,prior_strength=0,utility_calibration=c)
        fn=__import__('pcse_gym.agent.ppo_mod',fromlist=['fertilization_action_constraint']).fertilization_action_constraint if a.model=='raw' else upper_surplus_constraint if v3 else corrected_fertilization_action_constraint
        m=LagrangianPPO(AdaptiveMoisturePolicy if v3 else CostActorCriticPolicy,vec,seed=a.seed,learning_rate=.0003,n_steps=128,batch_size=240,n_epochs=10,gamma=1,gae_lambda=1.,clip_range=.2,ent_coef=.01,constraint_fn=fn,constraint_mode='raw' if a.model=='raw' else 'corrected',endpoint_cost_mode='upper_surplus' if v3 else 'joint',cvar_alpha=.1 if a.model=='full4' else None,dual_update_once=v3,active_step_grad=True,active_mask_offset=11 if v3 else None,target_kl=.03,policy_kwargs=kw,device='cpu',verbose=0)
        before=base.base.hash_policy(m);head_before=m.policy.action_net.weight.detach().clone()
        if guided:
            windows=json.loads((R/'reports/phase3c-training-utility-grid.json').read_text())['records'];batch=torch.tensor([w['observation'] for w in windows],dtype=torch.float32)
            from pcse_gym.envs.moisture4 import adaptive_total
            requested=(adaptive_total(batch[:,-1,:11],c)-130)//10
            predicted=torch.as_tensor(m.predict(batch.numpy(),deterministic=True)[0])
            assert torch.equal(predicted,requested),'Initialization degrades frozen prior'
            receipt['zero_step_prior_agreement']=float((predicted==requested).float().mean())
        cb=base.Diagnostics();cb.output=out/'progress.json';m.learn(total_timesteps=a.steps,callback=cb)
        for path,digest in receipt['source_sha256'].items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==digest,'Source drift during train: '+path
        m.save(out/'model.zip');vec.save(out/'normalizer.pkl')
        receipt.update(status='completed',actual_steps=m.num_timesteps,parameters_changed=base.base.hash_policy(m)!=before,finite_parameters=all(bool(torch.isfinite(x).all()) for x in m.policy.parameters()),parameter_count=sum(x.numel() for x in m.policy.parameters()),frozen_buffer_elements=sum(x.numel() for x in m.policy.buffers()),actor_head_L2_change=float(torch.linalg.vector_norm(m.policy.action_net.weight.detach()-head_before)),observed_training_years=sorted(cb.years),diagnostic_seasons=cb.seasons,episode_outcomes=m.episode_outcomes,step_diagnostics=cb.step_diagnostics,last_training_logger={k:float(v) for k,v in m.logger.name_to_value.items() if np.isscalar(v)},checkpoint_sha256=hashlib.sha256((out/'model.zip').read_bytes()).hexdigest())
    except BaseException as e:receipt.update(status='failed',error=repr(e));raise
    finally:
        if vec is not None:vec.close()
        receipt['seconds']=time.monotonic()-start;(out/'receipt.json').write_text(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
