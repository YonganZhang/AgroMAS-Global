"""120train years x3soils x6real doses; observable utility labels, no Dev reads."""
import pathlib,json,sys,hashlib,concurrent.futures
import numpy as np
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
from pcse_gym.initialize_envs import initialize_env
from pcse_gym.envs.observable import OBSERVABLE_CROP
from pcse_gym.envs.constraints import AgronomicShield
from pcse_gym.envs.moisture4 import Moisture4History
from pcse_gym.envs.corridor import target,terminal_compliance
OLD=R/'reports/phase3b-training-calibration-v1.json';WINDOWS=R/'reports/phase3b3-training-sm-windows.json'
def collect(task):
 year,soil=task;assert 3002<=year<=4999
 import logging;logging.disable(logging.CRITICAL)
 rows=[];window=None
 for dose in range(160,211,10):
  native=initialize_env(pcse_env=2,crop_features=list(OBSERVABLE_CROP),action_features=[],years=[year],locations=[(52.57,5.63)],random_weather=True,random_init=False,reward='NUE',seed=4,soil='slo' if soil=='slow' else None if soil=='default' else soil,start_type='sowing')
  e=Moisture4History(AgronomicShield(native,n_budget=210),guided=True,calibration=None,stages=(70,130),joint_bonus=8);e.unwrapped.sb3_env._phase2_fast_info=True
  try:
   obs,_=e.reset(seed=year);done=False;used=0
   while not done:
    if window is None and obs[-1,0]>=.62:window=obs.tolist()
    desired=float(target(obs[-1,0],used,dose,(70,130)));a=int(np.clip(np.round((desired-used)/10),0,8));a=max(i for i in range(a+1) if obs[-1,11+i])
    obs,r,t,tr,info=e.step(a);used+=10*info['executed_action'];done=t or tr
   assert used==dose
   last=lambda k:float(list(info[k].values())[-1])
   rows.append(dict(year=year,soil=soil,actual_N=used,yield_t_ha=last('WSO')/1000,NUE=last('NUE'),surplus=last('Nsurplus'),stages=[70,130],source='new_fixed_init_simulation'))
  finally:e.close()
 return dict(year=year,soil=soil,observation=window,episodes=rows)
if __name__=='__main__':
 out=R/'reports/phase3c-training-utility-grid.json';assert not out.exists()
 old=json.loads(OLD.read_text());oldyears=old['calibration']['train_years'];candidates=[int(y) for y in np.linspace(3002,4999,200) if int(y) not in oldyears];extra=[candidates[i] for i in np.linspace(0,len(candidates)-1,70).round().astype(int)];years=sorted(set(oldyears+extra));assert len(years)==120
 observations=json.loads(WINDOWS.read_text())['observations'];records=[]
 for w in observations:
  es=[dict(r,source='immutable_Phase3B_training_grid_reuse') for r in old['episodes'] if r['stages']==[70,130] and r['year']==w['year'] and r['soil']==w['soil']];assert len(es)==6
  records.append(dict(w,episodes=es))
 with concurrent.futures.ProcessPoolExecutor(max_workers=35) as pool:
  for rec in pool.map(collect,[(y,s) for y in extra for s in ['default','fast','slow']]):
   records.append(rec);out.with_suffix('.progress.json').write_text(json.dumps(dict(training_only=True,records=records)))
 assert len(records)==360
 out.write_text(json.dumps(dict(training_only=True,years=years,fixed_initial_soil=True,records=records,reused_source_sha256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [OLD,WINDOWS]})))
 print('Completed360training scenarios,2160dose outcomes')
