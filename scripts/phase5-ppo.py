"""Full-wrapper8process benchmark, then sufficient native weekly SB3 PPO training."""
from pathlib import Path
from functools import partial
import argparse,hashlib,json,logging,math,time,fcntl
import numpy as np
import torch
from stable_baselines3.common.vec_env import SubprocVecEnv,VecNormalize
from stable_baselines3.common.callbacks import BaseCallback
from sb3_contrib.common.maskable.utils import get_action_masks
from pcse_gym.agromas.runtime import RegionalWeeklyEnv,outcome_model
from pcse_gym.agromas.features import forecast_model
from pcse_gym.agromas.season import regional_weather,_template
from pcse_gym.agromas.regions import REGIONS
from pcse_gym.agromas.baseline import make_entropy_ppo
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5'


def write(path,data):
    with path.open('x') as f:json.dump(data,f,indent=2)
    path.chmod(0o444)


def preload():
    start=time.monotonic()
    for stage in (1,2,3):outcome_model(str(R),stage)
    for name in REGIONS:forecast_model(str(R),name);regional_weather(str(R),name,'v2')
    with (R/'cache/phase5-template-init.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        _template(str(R))
        fcntl.flock(lock,fcntl.LOCK_UN)
    import pcse_gym.agromas.runtime as actual_runtime
    assert Path(actual_runtime.__file__).resolve().is_relative_to((R/'NUE_PCSE-Gym').resolve()),'Wrongsourceworktree'
    return time.monotonic()-start


def vector(mode,beta,seed):
    v=SubprocVecEnv([partial(RegionalWeeklyEnv,str(R),beta=beta,information_mode=mode) for _ in range(8)],start_method='fork')
    v.seed(seed)
    return v


class AuditCallback(BaseCallback):
    def __init__(self,path):
        super().__init__();self.path=path;self.episodes=[];self.entropy_sum=0.;self.entropy_n=0
        self.action_hist={str(s):{str(i):0 for i in range(7)} for s in (1,2,3)}
        self.decision_count=0;self.infeasible=0;self.started=time.monotonic()
    def _on_training_start(self):self.log=self.path.open('x')
    def _on_step(self):
        infos=self.locals['infos'];actions=np.asarray(self.locals['actions']).reshape(-1)
        for i,info in enumerate(infos):
            stage=info.get('decision_stage')
            if stage:
                self.decision_count+=1;self.infeasible+=bool(info['predicted_infeasible'])
                self.action_hist[str(stage)][str(int(actions[i]))]+=1
            if 'outcome' in info:
                m=info['outcome'];cap=info['cap'];joint=.5<=m[3]<=.9 and m[2]<=cap
                profit=200*m[0]-1.5*info['price_multiplier']*m[4]+info['subsidy']*joint
                self.episodes.append(dict(region_id=info['region_id'],year=info['harvest_year'],climate=info['climate'],
                     cap=cap,joint=bool(joint),outcome=m,partial_profit=profit,events=info['stage_events'],
                     actual_surplus_violation=bool(m[2]>cap),stock_diagnostics=info['stock_diagnostics']))
        masks=self.locals.get('action_masks');obs=self.locals.get('obs_tensor')
        if masks is not None and obs is not None:
            active=np.asarray(masks).sum(1)>1
            if active.any():
                with torch.no_grad():ent=self.model.policy.get_distribution(obs,action_masks=masks).entropy().cpu().numpy()
                self.entropy_sum+=float(ent[active].sum());self.entropy_n+=int(active.sum())
        return True
    def _on_rollout_end(self):
        recent=self.episodes[-200:]
        row=dict(native_weekly_steps=self.num_timesteps,elapsed_seconds=time.monotonic()-self.started,
            complete_train_seasons=len(self.episodes),conditional_choice_entropy=self.entropy_sum/max(1,self.entropy_n),
            entropy_choice_count=self.entropy_n,decision_count=self.decision_count,predicted_infeasible=self.infeasible,
            stage_action_histogram=self.action_hist,dual=0.,eta=0.,
            recent_joint=float(np.mean([x['joint'] for x in recent])) if recent else None,
            actual_surplus_violation_count=sum(x['actual_surplus_violation'] for x in self.episodes),
            recent_surplus_violation_rate=float(np.mean([x['actual_surplus_violation'] for x in recent])) if recent else None,
            recent_partial_profit=float(np.mean([x['partial_profit'] for x in recent])) if recent else None,
            optimizer={k:float(v) for k,v in self.model.logger.name_to_value.items() if k.startswith('train/') and np.isscalar(v)})
        self.log.write(json.dumps(row)+'\n');self.log.flush()
    def _on_training_end(self):self.log.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=['benchmark','train'],required=True)
    parser.add_argument('--mode',choices=['raw-shared','structured-shared'],default='structured-shared')
    parser.add_argument('--seed',type=int,choices=[4,17,29])
    parser.add_argument('--protocol-version',choices=['v2','v3','v4'],default='v4')
    args=parser.parse_args();version=args.protocol_version;logging.disable(logging.CRITICAL);torch.set_num_threads(1)
    if args.stage=='train' and args.seed is None:parser.error('--seed required for training')
    beta=json.loads((P/'policy-train-freeze-v2.json').read_text())['selected_beta']
    source_freeze_path=P/f'PPO-source-and-input-freeze-{version}.json'
    source_freeze=None
    if args.stage=='train':
        source_freeze=json.loads(source_freeze_path.read_text())
        for rel,digest in source_freeze['files'].items():
            assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==digest,'Pretraininginputdrift:'+rel
    load_seconds=preload()
    if args.stage=='benchmark':
        start=time.monotonic();v=vector('structured-shared',beta,4);obs=v.reset();startup=time.monotonic()-start
        rng=np.random.default_rng(4);start=time.monotonic();seasons=0;decisions=0
        for _ in range(256):
            masks=get_action_masks(v)
            actions=np.array([rng.choice(np.flatnonzero(mask)) for mask in masks])
            obs,rewards,dones,infos=v.step(actions)
            seasons+=int(np.sum(dones));decisions+=sum(bool(i.get('decision_stage')) for i in infos)
        elapsed=time.monotonic()-start;v.close();sps=2048/elapsed
        bench=dict(processes=8,native_weekly_steps=2048,complete_seasons=seasons,decision_steps=decisions,
          wall_seconds=elapsed,steps_per_second=sps,parent_model_and_source_load_seconds=load_seconds,
          process_start_reset_seconds=startup,includes=['realregionalPCSE','weeklyactualdayguard','causalforecast','64treeoutcomeensemble','ecofilter','economicpricing','90sharedobservables','IPC'],
          excludes=['PPOpolicyforward','SGDupdates'],not_physical_kernel_only=True)
        write(P/f'eight-process-full-wrapper-throughput-{version}.json',bench)
        steps=401408 if sps>=100 else 200704  # Measured-cost choice frozen before any PPO fit.
        budget=dict(status='frozen_after_actual_full_wrapper_throughput',protocol_version=version,train_caps=[25,35,40,50],seeds=[4,17,29],modes=['structured-shared','raw-shared'],
          native_weekly_steps_per_seed=steps,initial_requested_minimum=200000,budget_rule='401408if fullwrapperSPS>=100,else200704; no outcome-based selection',n_envs=8,n_steps=256,batch_size=256,n_epochs=10,
          gamma=1.,gae_lambda=1.,entropy_coefficient=.01,learning_rate=.0003,target_kl=.03,device='cpu',
          observation_and_reward_normalization='VecNormalize TRAIN only, clip_obs10, clip_reward10,gamma1; frozen for evaluation',
          main_comparison='structured-shared exact sufficient statistics: expectedprofit+probJoint+legalmask; raw-shared is transformation diagnostic',
          throughput_sha256=hashlib.sha256((P/f'eight-process-full-wrapper-throughput-{version}.json').read_bytes()).hexdigest(),
          convergence='Report fullcurves,stageactiondiversity,conditionalentropy,actualparams; insufficientconvergence prohibitsvictoryclaims; no Dev-driven budget extension',
          eta=0.,dual=0.,beta=beta)
        write(P/f'ppo-training-budget-{version}.json',budget);print(json.dumps(bench),flush=True)
    else:
        budget=json.loads((P/f'ppo-training-budget-{version}.json').read_text())
        out=R/f'models/phase5/ppo-{args.mode}-seed{args.seed}-{version}';out.mkdir(parents=True,exist_ok=False)
        v=VecNormalize(vector(args.mode,beta,args.seed),norm_obs=True,norm_reward=True,clip_obs=10.,clip_reward=10.,gamma=1.)
        model=make_entropy_ppo(v,args.seed)
        before=torch.cat([x.detach().cpu().flatten() for x in model.policy.parameters()]).numpy().copy()
        cb=AuditCallback(out/'training-curves.jsonl');start=time.monotonic()
        model.learn(total_timesteps=budget['native_weekly_steps_per_seed'],callback=cb)
        elapsed=time.monotonic()-start
        after=torch.cat([x.detach().cpu().flatten() for x in model.policy.parameters()]).numpy()
        model.save(out/'model.zip');v.save(out/'vecnormalize.pkl');v.close()
        with (out/'train-episodes.jsonl').open('x') as f:
            for row in cb.episodes:f.write(json.dumps(row)+'\n')
        for rel,digest in source_freeze['files'].items():
            assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==digest,'Source/inputchangedduringPPO:'+rel
        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.is_file()}
        receipt=dict(status='completed',seed=args.seed,mode=args.mode,actual_native_weekly_steps=model.num_timesteps,
          parameter_count=len(after),parameters_finite=bool(np.isfinite(after).all()),parameters_L2_change=float(np.linalg.norm(after-before)),
          elapsed_seconds=elapsed,actual_training_steps_per_second=model.num_timesteps/elapsed,parent_load_seconds=load_seconds,
          train_seasons=len(cb.episodes),train_decisions=cb.decision_count,conditional_entropy=cb.entropy_sum/max(1,cb.entropy_n),
          stage_action_histogram=cb.action_hist,predicted_infeasible=cb.infeasible,dual=0.,eta=0.,beta=beta,
          files=files,source_freeze_sha256=hashlib.sha256(source_freeze_path.read_bytes()).hexdigest(),budget_sha256=hashlib.sha256((P/f'ppo-training-budget-{version}.json').read_bytes()).hexdigest(),dev_used=False,heldout_used=False)
        write(out/'receipt.json',receipt)
        for p in out.iterdir():p.chmod(0o444)
        print(json.dumps(receipt),flush=True)
