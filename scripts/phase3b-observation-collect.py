"""Collect full causal actor windows on calibration training years for a diagnostic."""
import pathlib,json,sys,concurrent.futures
import numpy as np
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
from pcse_gym.initialize_envs import initialize_env
from pcse_gym.envs.observable import OBSERVABLE_CROP
from pcse_gym.envs.constraints import AgronomicShield
from pcse_gym.envs.corridor import CorridorHistory,target
C=json.loads((R/'reports/phase3b-frozen-calibration-v1.json').read_text())
def collect(task):
 year,soil=task;assert 3002<=year<=4999
 import logging;logging.disable(logging.CRITICAL)
 e=initialize_env(pcse_env=2,crop_features=list(OBSERVABLE_CROP),action_features=[],years=[year],locations=[(52.57,5.63)],random_weather=True,random_init=False,reward='NUE',seed=4,soil='slo' if soil=='slow' else None if soil=='default' else soil,start_type='sowing')
 e=CorridorHistory(AgronomicShield(e,n_budget=210),calibration=C,stages=C['stages'],joint_bonus=C['joint_bonus']);e.unwrapped.sb3_env._phase2_fast_info=True
 try:
  obs,_=e.reset(seed=year);done=False;used=0
  while not done:
   f=obs[-1,:10]
   if f[0]>=.62:return dict(year=year,soil=soil,observation=obs.tolist())
   desired=float(target(f[0],used,190,C['stages']));a=int(np.clip(np.ceil((desired-used-1e-4)/10),0,8));a=max(i for i in range(a+1) if obs[-1,10+i]);obs,r,t,tr,info=e.step(a);used+=10*info['executed_action'];done=t or tr
  raise RuntimeError('No pre-Stage3 observation')
 finally:e.close()
if __name__=='__main__':
 out=R/'reports/phase3b-training-observation-windows.json';assert not out.exists()
 with concurrent.futures.ProcessPoolExecutor(max_workers=20) as p:rows=list(p.map(collect,[(y,s) for y in C['train_years'] for s in ['default','fast','slow']]))
 out.write_text(json.dumps(dict(training_only=True,observations=rows)))
