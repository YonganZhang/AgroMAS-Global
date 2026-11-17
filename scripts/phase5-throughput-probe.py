"""Eight-process TRAIN physical-kernel throughput ceiling, not PPO learning evidence."""
import importlib.util,json,time
from pathlib import Path
import numpy as np
import gymnasium as gym
from stable_baselines3.common.vec_env import SubprocVecEnv
R=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('co2_throughput',R/'scripts/phase5-co2-probe.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)

class PhysicalBenchmark(gym.Env):
    observation_space=gym.spaces.Box(-np.inf,np.inf,(1,),dtype=np.float32)
    action_space=gym.spaces.Discrete(1)
    def __init__(self,rank):self.rank=rank
    def reset(self,seed=None,options=None):
        super().reset(seed=seed)
        self.engine=probe.make_engine(380,3002+self.rank%3)
        self.steps=0
        return np.zeros(1,np.float32),{}
    def step(self,action):
        self.engine.run(days=7,action=0);self.steps+=1
        ended=self.engine.terminated
        return np.zeros(1,np.float32),0.,ended,False,dict(season_steps=self.steps)

if __name__=='__main__':
    # Warm one immutable weather cache before fork; do not multiply CSV ingestion.
    probe.get_random_weather_provider((52.57,5.63))
    probe.make_engine()
    vec=None;start=time.monotonic();episodes=0
    try:
        vec=SubprocVecEnv([lambda rank=i:PhysicalBenchmark(rank) for i in range(8)],start_method='fork')
        vec.reset();startup=time.monotonic()-start;tick=time.monotonic()
        for _ in range(256):
            _,_,done,_=vec.step(np.zeros(8,dtype=int));episodes+=int(done.sum())
        elapsed=time.monotonic()-tick
        result=dict(status='completed',n_envs=8,native_weekly_steps=2048,completed_seasons=episodes,
                    timing_seconds=elapsed,startup_seconds=startup,weekly_steps_per_second=2048/elapsed,
                    train_years=[3002,3003,3004],scope='Physical zero-N kernel ceiling; forecast/scorer/PPO overhead excluded',
                    final_ppo_budget_frozen=False,claim='No learning, action diversity, convergence or fairness result')
        out=R/'reports/phase5/eight-process-physical-throughput.json'
        if out.exists():raise FileExistsError('Preserve throughput evidence')
        out.write_text(json.dumps(result,indent=2));print(json.dumps(result))
    finally:
        if vec is not None:vec.close()
