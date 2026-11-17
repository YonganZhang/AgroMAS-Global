"""Collect full causal actor windows on calibration training years for a diagnostic."""
import pathlib,json,sys,concurrent.futures
import numpy as np
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
from pcse_gym.initialize_envs import initialize_env
from pcse_gym.envs.observable import OBSERVABLE_CROP
from pcse_gym.envs.constraints import AgronomicShield
from pcse_gym.envs.corridor import target
from pcse_gym.envs.moisture import MoistureHistory
C=json.loads((R/'reports/phase3b-frozen-calibration-v1.json').read_text())
def collect(task):
 year,soil=task;assert 3002<=year<=4999
 import logging;logging.disable(logging.CRITICAL)
 e=initialize_env(pcse_env=2,crop_features=list(OBSERVABLE_CROP),action_features=[],years=[year],locations=[(52.57,5.63)],random_weather=True,random_init=False,reward='NUE',seed=4,soil='slo' if soil=='slow' else None if soil=='default' else soil,start_type='sowing')
 e=MoistureHistory(AgronomicShield(e,n_budget=210),calibration=None,stages=C['stages'],joint_bonus=8);e.unwrapped.sb3_env._phase2_fast_info=True
 try:
  obs,_=e.reset(seed=year);done=False;used=0
  while not done:
   f=obs[-1,:10]
   if f[0]>=.62:return dict(year=year,soil=soil,observation=obs.tolist())
   desired=float(target(f[0],used,190,C['stages']));a=int(np.clip(np.ceil((desired-used-1e-4)/10),0,8));a=max(i for i in range(a+1) if obs[-1,11+i]);obs,r,t,tr,info=e.step(a);used+=10*info['executed_action'];done=t or tr
  raise RuntimeError('No pre-Stage3 observation')
 finally:e.close()
if __name__=='__main__':
 out=R/'reports/phase3b3-training-sm-windows.json';assert not out.exists()
 with concurrent.futures.ProcessPoolExecutor(max_workers=20) as p:rows=list(p.map(collect,[(y,s) for y in C['train_years'] for s in ['default','fast','slow']]))
 out.write_text(json.dumps(dict(training_only=True,observations=rows)))

 raw=json.loads((R/'reports/phase3b-training-calibration-v1.json').read_text())['episodes']
 pool={}
 for r in raw:
     if r['stages']==[70,130]:pool.setdefault((r['year'],r['soil']),[]).append(r)
 from pcse_gym.envs.corridor import terminal_compliance
 chosen=[max(pool[q['year'],q['soil']],key=lambda r:r['yield_t_ha']-.002*r['actual_N']+terminal_compliance(r['NUE'],r['surplus'],8)) for q in rows]
 observations=np.array([q['observation'] for q in rows]);previous=json.loads((R/'reports/phase3b-training-observation-windows.json').read_text())['observations'];old={(q['year'],q['soil']):np.array(q['observation']) for q in previous}
 assert max(float(np.max(np.abs(np.array(q['observation'])[:,:9]-old[q['year'],q['soil']][:,:9]))) for q in rows)<1e-6
 f=observations[:,-1,:11];X=np.column_stack([f[:,1]*10,f[:,10],f[:,10]**2,f[:,4]]);Y=np.array([q['actual_N'] for q in chosen]);mu=X.mean(0);scale=X.std(0);scale[scale<1e-8]=1;Z=(X-mu)/scale;coef=np.linalg.solve(Z.T@Z+np.eye(4),Z.T@(Y-Y.mean()));error=Y-(Y.mean()+Z@coef)
 cal=dict(intercept=float(Y.mean()),feature_mean=mu.tolist(),feature_scale=scale.tolist(),coefficients=coef.tolist(),headroom=float(np.clip(np.ceil(max(0,float(np.quantile(error,.75)))/10)*10,10,20)),joint_bonus=8,stages=[70,130],train_years=C['train_years'],fit_n=150,RMSE=float(np.sqrt(np.mean(error**2))),feature_names=['LAI','top20cm_SM','top20cm_SM_squared','past7d_RAIN_scaled'],observation_assumption='Idealized physically measurable top0-20cm volumetric water; no real sensor/noise robustness claim; no soil-N pool or soil-label input')
 dst=R/'reports/phase3b3-frozen-calibration-sm-v1.json';assert not dst.exists();dst.write_text(json.dumps(cal,indent=2));print(json.dumps(cal))
