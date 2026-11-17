"""Native-weekly Gym wrapper shared by PPO and modular controller evaluation.

Factories/encoders are explicit dependencies. They must be frozen before fitting;
this wrapper never requests future physical weather to construct observations.
"""
from dataclasses import dataclass
import hashlib,json
from datetime import timedelta
import numpy as np
import gymnasium as gym
from .scheduler import ThreeStageScheduler
from .weekly import advance_week
from .contracts import CandidateTable,compliance


@dataclass(frozen=True)
class SharedControlConfig:
    dose_grid: tuple
    budget: float
    initial_base_n: float
    observation_names: tuple
    information_mode: str
    source_config_id: str
    beta: float=0.
    eta: float=0.
    regional_base_n: tuple=()

    def __post_init__(self):
        if self.information_mode not in ('raw-shared','structured-shared') or not self.source_config_id:
            raise ValueError('Explicit information/provenance contract required')
        if not self.observation_names or len(set(self.observation_names))!=len(self.observation_names):
            raise ValueError('Unique observation names required')
        if self.budget<self.initial_base_n or self.initial_base_n<0 or min(self.beta,self.eta)<0:
            raise ValueError('Invalid budget or utility bounds')
        if not self.dose_grid or self.dose_grid[0]!=0 or tuple(sorted(set(self.dose_grid)))!=self.dose_grid:
            raise ValueError('Sorted unique dose grid starting at zero required')
        if not np.isfinite([*self.dose_grid,self.budget,self.initial_base_n,self.beta,self.eta]).all():
            raise ValueError('Non-finite control configuration')
        if self.eta!=0:
            raise ValueError('Nonzero CVaR reward requires a validated shared conditional tail estimator')

        regional=dict(self.regional_base_n)
        if len(regional)!=len(self.regional_base_n) or any(
                not np.isfinite(v) or not 0<=v<=self.budget for v in regional.values()):
            raise ValueError('Explicit unique bounded regional basal configuration required')

    @property
    def schema_hash(self):
        return hashlib.sha256(json.dumps(self.__dict__,sort_keys=True).encode()).hexdigest()


class WofostWeeklyEnv(gym.Env):
    """Each step advances seven physical days; guard rechecks actual execution date.

    encode(engine,scheduler) -> {observation: finite 1D, candidate_table, agronomic_upper}
    It must use a causal observer. Candidate tables/eco filter are shared by all arms.
    terminal(engine,scheduler) -> one member [Y,grainN,S,NUE,Nfert,Nnonfert].
    """
    metadata={}

    def __init__(self, engine_factory, encode, terminal, eco, economics, config):
        self.engine_factory=engine_factory;self.encode=encode;self.terminal=terminal
        self.eco=eco;self.economics=economics;self.config=config
        self.action_space=gym.spaces.Discrete(len(config.dose_grid))
        self.observation_space=gym.spaces.Box(-np.inf,np.inf,(len(config.observation_names),),dtype=np.float32)
        self.engine=None

    def _observe(self):
        context=self.encode(self.engine,self.scheduler)
        obs=np.asarray(context['observation'],dtype=np.float32)
        if obs.shape!=self.observation_space.shape or not np.isfinite(obs).all():
            raise ValueError('Shared encoder shape/finite invariant')
        table=context['candidate_table']
        if table.as_of!=self.engine.day:
            raise ValueError('Stale/future candidate table')
        if not np.array_equal(table.doses,np.array(self.config.dose_grid)):
            raise ValueError('Shared candidate grid mismatch')
        self.context=context
        return obs

    def reset(self,seed=None,options=None):
        super().reset(seed=seed)
        self.engine,self.episode_metadata=self.engine_factory(self.np_random,options)
        base=dict(self.config.regional_base_n).get(self.episode_metadata.get('region_id'),self.config.initial_base_n)
        if not np.isclose(self.episode_metadata.get('initial_base_n',base),base):
            raise ValueError('Physical and configured regional basal fertilizer disagree')
        self.scheduler=ThreeStageScheduler(self.config.budget,base)
        self.weekly_steps=0;self.episode_active=True;self.requested_stage=None
        self.engine._action_guard=self._execution_guard
        return self._observe(),{'schema_hash':self.config.schema_hash,**self.episode_metadata}

    def _execution_guard(self,action,dvs,day):
        # `None` means no decision; a legitimate zero decision consumes its stage.
        if dvs is None:return 0.
        actual=self.scheduler.eligible(day,float(dvs))
        if self.requested_stage is None or actual!=self.requested_stage:
            return 0.
        return self.scheduler.execute(day,float(dvs),float(action),expected_stage=self.requested_stage)

    def action_masks(self):
        """Mask non-decisions and non-contiguous ecological exclusions identically."""
        stage=self.scheduler.preview(self.engine.day+timedelta(days=1),float(self.engine.get_variable('DVS') or 0))
        mask=np.zeros(len(self.config.dose_grid),dtype=bool)
        if stage is None:
            mask[0]=True
            return mask
        safe=self.eco.filter(self.context['candidate_table'],self.config.budget-self.scheduler.cumulative,
                             self.context['agronomic_upper'])
        if safe.predicted_infeasible:mask[0]=True
        else:mask=np.isin(self.config.dose_grid,safe.safe_doses)
        return mask

    def step(self,action):
        if not self.episode_active:raise RuntimeError('Reset required')
        if not self.action_space.contains(action):raise ValueError('Invalid discrete action')
        self.requested_stage=self.scheduler.preview(self.engine.day+timedelta(days=1),float(self.engine.get_variable('DVS') or 0))
        dose=float(self.config.dose_grid[int(action)])
        safe=None if self.requested_stage is None else self.eco.filter(
            self.context['candidate_table'],self.config.budget-self.scheduler.cumulative,self.context['agronomic_upper'])
        projected=0. if safe is None or dose not in safe.safe_doses else dose
        execution_date=advance_week(self.engine,projected)
        self.weekly_steps+=1
        ended=bool(self.engine.terminated)
        info={'requested_dose':dose,'projected_dose':projected,'predicted_infeasible':False if safe is None else safe.predicted_infeasible,
              'weekly_steps':self.weekly_steps,'decision_stage':self.requested_stage,'executed_dose':float(self.engine._guard_executed_action),
              'execution_date':execution_date,'schema_hash':self.config.schema_hash,**self.episode_metadata}
        reward=0.
        if ended:
            member=np.asarray(self.terminal(self.engine,self.scheduler),dtype=float).reshape(1,1,6)
            # Validate the same physical nitrogen accounting used in candidate pricing.
            table=CandidateTable(np.array([0.]),member,self.engine.day,'terminal',
                                 'realized',np.zeros(4),'physical-outcome')
            reward=float(self.economics.price(table,self.eco.cap)['expected_profit'][0]+
                         self.config.beta*compliance(member,self.eco.cap)[0,0])
            info.update(outcome=member[0,0].tolist(),stage_events=self.scheduler.events,
                        metric='partial_N_management_budget_plus_joint_utility')
            self.episode_active=False
            obs=np.zeros(self.observation_space.shape,dtype=np.float32)
        else:obs=self._observe()
        return obs,reward,ended,False,info


def make_entropy_ppo(env, seed, *, learning_rate=3e-4, ent_coef=.01):
    """Native SB3 entropy PPO; invalid actions masked without a hand-coded dose prior.

    Final step count is deliberately NOT a default here: callers must load the
    measured-throughput preregistration and pass it explicitly to `learn`.
    """
    from sb3_contrib import MaskablePPO
    return MaskablePPO('MlpPolicy',env,seed=seed,learning_rate=learning_rate,
                       n_steps=256,batch_size=256,n_epochs=10,gamma=1.,gae_lambda=1.,
                       ent_coef=ent_coef,clip_range=.2,target_kl=.03,
                       policy_kwargs=dict(net_arch=dict(pi=[64,64],vf=[64,64])),
                       device='cpu',verbose=0)
