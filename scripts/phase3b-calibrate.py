"""Train-only paired dose/split calibration. No Dev or held-out environments permitted."""
import pathlib,sys,json,concurrent.futures,time
import numpy as np
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
from pcse_gym.initialize_envs import initialize_env
from pcse_gym.envs.observable import OBSERVABLE_CROP
from pcse_gym.envs.constraints import AgronomicShield
from pcse_gym.envs.corridor import CorridorHistory,target,terminal_compliance

def evaluate(task):
    soil,stages,dose,years=task
    assert all(3002<=y<=4999 for y in years)
    import logging;logging.disable(logging.CRITICAL)
    env=initialize_env(pcse_env=2,crop_features=list(OBSERVABLE_CROP),action_features=[],years=[years[0]],locations=[(52.57,5.63)],random_weather=True,random_init=False,reward='NUE',seed=4,soil='slo' if soil=='slow' else None if soil=='default' else soil,start_type='sowing')
    env=CorridorHistory(AgronomicShield(env,n_budget=210),stages=stages)
    env.unwrapped.sb3_env._phase2_fast_info=True;rows=[]
    try:
        for year in years:
            env.unwrapped.overwrite_year(year);obs,_=env.reset(seed=year);done=False;total=0;features=None
            while not done:
                f=obs[-1,:10];desired=float(target(f[0],total,dose,stages));a=int(np.clip(np.ceil((desired-total-1e-4)/10),0,8))
                a=max(i for i in range(a+1) if obs[-1,10+i])
                if .62<=f[0]<=.88 and features is None:features=dict(LAI=float(f[1])*10,RAIN_scaled=float(f[4]),LAI_delta=float(obs[-1,1]-obs[-2,1])*10)
                obs,rew,t,tr,info=env.step(a);done=t or tr;total+=10*info['executed_action']
            last=lambda k:float(list(info[k].values())[-1])
            rows.append(dict(year=year,soil=soil,stages=stages,requested_N=dose,actual_N=total,yield_t_ha=last('WSO')/1000,NUE=last('NUE'),surplus=last('Nsurplus'),features=features,executed_violation_rate=info['executed_violation_rate']))
        return rows
    finally:env.close()
if __name__=='__main__':
    out=R/'reports/phase3b-training-calibration-v1.json';assert not out.exists()
    years=np.linspace(3002,4999,50,dtype=int).tolist();tasks=[(soil,stages,dose,years[i:i+5]) for soil in ['default','fast','slow'] for stages in [(50,110),(70,130)] for dose in [160,170,180,190,200,210] for i in range(0,50,5)]
    rows=[];start=time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(max_workers=45) as ex:
        for part in ex.map(evaluate,tasks):rows+=part
    assert len(rows)==1800
    groups={}
    for r in rows:groups.setdefault((r['year'],r['soil'],tuple(r['stages'])),[]).append(r)
    # Freeze reward scale using only within-scenario training yield ranges.
    max_range=max(max(r['yield_t_ha'] for r in g)-min(r['yield_t_ha'] for r in g) for g in groups.values())
    bonus=float(np.clip(np.ceil(2*max_range*2)/2,1,4))
    for group in groups.values():
        feature_values=[r['features']['LAI'] for r in group];assert max(feature_values)-min(feature_values)<1e-6,'Unpaired early trajectory'
    chosen=[]
    for k,g in groups.items():
        if k[2]!=(70,130):continue
        chosen.append(max(g,key=lambda r:r['yield_t_ha']-.002*r['actual_N']+terminal_compliance(r['NUE'],r['surplus'],bonus)))
    xx=np.array([r['features']['LAI'] for r in chosen]);yy=np.array([r['actual_N'] for r in chosen]);b=max(0.,float(np.cov(xx,yy,ddof=0)[0,1]/np.var(xx)));a=float(np.mean(yy-b*xx));error=yy-(a+b*xx);headroom=float(np.clip(np.ceil(max(0,float(np.quantile(error,.75)))/10)*10,10,20))
    calibration=dict(intercept=a,LAI_coefficient=b,headroom=headroom,joint_bonus=bonus,stages=[70,130],train_years=years,fit_n=len(chosen),max_paired_yield_range=max_range,RMSE=float(np.sqrt(np.mean(error**2))),selected_N_histogram={str(n):int(sum(yy==n)) for n in sorted(set(yy))},source='train-only terminal labels, fixed initial soil; LAI measured before Stage3; no soil label at inference')
    out.write_text(json.dumps(dict(calibration=calibration,seconds=time.monotonic()-start,episodes=rows),indent=2))
    (R/'reports/phase3b-frozen-calibration-v1.json').write_text(json.dumps(calibration,indent=2));print(json.dumps(calibration),flush=True)
