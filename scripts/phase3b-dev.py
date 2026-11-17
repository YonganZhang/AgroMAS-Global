"""New v3 receipts; Dev first, audit only under a frozen explicit unlock manifest."""
import pathlib,sys,json,argparse,hashlib,concurrent.futures,time
import numpy as np
import torch
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
run=SourceFileLoader('phase3b_runner',str(R/'scripts/phase3b-run.py')).load_module()
b=SourceFileLoader('phase3b_baseline',str(R/'scripts/evaluate-baselines.py')).load_module()
from pcse_gym.envs.corridor import target
from pcse_gym.envs.phase3 import Phase3History
from pcse_gym.envs.constraints import AgronomicShield
from pcse_gym.envs.observable import OBSERVABLE_CROP
from pcse_gym.initialize_envs import initialize_env
from pcse_gym.agent.ppo_mod import LagrangianPPO

def validate_years(years,audit):
    if all(5000<=y<=5499 for y in years):return
    if not audit:raise ValueError('Heldout locked')
    u=json.loads((R/'reports/phase3b-heldout-unlock.json').read_text())
    assert u['dev_gate_passed'] and u['all_checkpoints_frozen']
    assert all(y in set(range(1983,2022))|set(range(5500,5999)) for y in years)

def evaluate(task):
    name,seed,soil,years,tag,audit=task;validate_years(years,audit);torch.set_num_threads(1)
    import logging;logging.disable(logging.CRITICAL)
    learned=name in run.MODELS;c=run.calibration()
    if learned or name in ['corridorprior','adaptiveprior']:
        env=run.make_env(name if learned else 'guided',seed,0,years=[years[0]],soil=soil,training=False,audit=audit)
    else:
        prior=name in ['prior160','prior190']
        if prior:
            native=initialize_env(pcse_env=2,crop_features=list(OBSERVABLE_CROP),action_features=[],years=[years[0]],locations=[(52.57,5.63)],random_weather=True,random_init=False,reward='NUE',seed=seed,soil='slo' if soil=='slow' else None if soil=='default' else soil,start_type='sowing')
            env=Phase3History(AgronomicShield(native,enabled=True,n_budget=195),history=1,aligned=False,guided=name=='prior160')
        else:env=run.base.base.make_env('raw',seed,0,years=[years[0]],soil=soil,training=False)
    env.unwrapped.sb3_env._phase2_fast_info=True;model=None;sha=None;rows=[];events=[]
    try:
        if learned:
            folder=R/f'reports/phase3b-runs/{tag}-{name}-seed{seed}';receipt=json.loads((folder/'receipt.json').read_text());ck=folder/'model.zip'
            assert receipt['status']=='completed';sha=hashlib.sha256(ck.read_bytes()).hexdigest();assert sha==receipt['checkpoint_sha256']
            for path in receipt['source_sha256']:
                assert hashlib.sha256((R/path).read_bytes()).hexdigest()==receipt['source_sha256'][path],'Candidate environment drift'
            model=LagrangianPPO.load(ck,device='cpu')
            if audit:assert json.loads((R/'reports/phase3b-heldout-unlock.json').read_text())['checkpoint_sha256'][folder.name]==sha
        for year in years:
            env.unwrapped.overwrite_year(year);obs,_=env.reset(seed=seed);done=False;actual=0;steps=0;intercepts=0;merged={};adapt=None
            while not done:
                before=obs.copy()
                if model is not None:a=int(model.predict(obs,deterministic=True)[0])
                elif name in ['prior160','prior190','corridorprior','adaptiveprior']:
                    f=obs[-1,:10]
                    if name=='adaptiveprior' and adapt is None and f[0]>=.62:
                        adapt=float(np.clip(np.round((c['intercept']+c['LAI_coefficient']*f[1]*10)/10)*10,160,210))
                    final=160 if name=='prior160' else adapt if name=='adaptiveprior' and adapt is not None else 190
                    stages=(50,110) if name in ['prior160','prior190'] else c['stages']
                    wanted=(50 if .10<=float(f[0])<.32 else 110 if .32<=float(f[0])<.62 else final if .62<=float(f[0])<=.88 else actual) if name in ['prior160','prior190'] else float(target(f[0],actual,final,stages));a=int(np.clip(np.ceil((wanted-actual-1e-4)/10),0,8));a=max(i for i in range(a+1) if obs[-1,10+i])
                elif name=='Zero-N':a=0
                else:
                    from pcse_gym.utils.nitrogen_helpers import get_standard_practices
                    from datetime import timedelta
                    dates,doses=get_standard_practices(name,year);date=env.unwrapped.date;a=sum(n//10 for d,n in zip(dates,doses) if d<date<=d+timedelta(days=7))
                obs,r,t,tr,info=env.step(a);done=t or tr;actual+=10*info['executed_action'];steps+=1;intercepts+=int(info['shield_triggered'])
                for k,v in info.items():
                    if isinstance(v,dict):merged.setdefault(k,{}).update(v)
                if seed==4 and soil=='default' and year==years[0] and year in [5000,1983,5500]:events.append(dict(year=year,DVS=float(before[-1,0]),LAI=float(before[-1,1])*10,past_rain=float(before[-1,4]),cumulative_N=float(before[-1,5])*400,seasonal_remaining=None if before[-1,9]<0 else float(before[-1,9])*400,proposed=int(a),executed=info['executed_action'],reasons=info['shield_reason']))
            row=b.extract(merged,year,name);native_input=row['grain_N_kg_ha']/row['NUE'] if row['NUE']>0 else 0
            nue=row['grain_N_kg_ha']/(native_input-row['fertilization_kg_ha']+actual) if native_input else 0.;surplus=row['N_surplus_kg_ha']-row['fertilization_kg_ha']+actual
            row.update(seed=seed,soil=soil,actual_N=actual,NUE_actual=nue,surplus_actual=surplus,joint_actual=.5<=nue<=.9 and 0<=surplus<=40,proposed_violation_rate=info['proposed_violation_rate'],executed_violation_rate=info['executed_violation_rate'],guard_interception_rate=intercepts/steps,mask_active_rate=info.get('mask_active_rate',0))
            row.update(native_NUE=row['NUE'],native_surplus_kg_ha=row['N_surplus_kg_ha'],native_joint_satisfied=row['joint_satisfied'])
            row.update(NUE=nue,N_surplus_kg_ha=surplus,NUE_satisfied=.5<=nue<=.9,surplus_satisfied=0<=surplus<=40,joint_satisfied=row['joint_actual'])
            rows.append(row)
        if model is not None:assert hashlib.sha256(ck.read_bytes()).hexdigest()==sha
        return dict(model=name,seed=seed,soil=soil,checkpoint_sha256=sha,episodes=rows,events=events)
    finally:env.close()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--models',nargs='+',default=['full3']);p.add_argument('--tag',default='v3');p.add_argument('--workers',type=int,default=45);p.add_argument('--years',type=int,default=500);p.add_argument('--audit',action='store_true');p.add_argument('--output',required=True);a=p.parse_args();out=R/a.output;assert not out.exists()
    years=list(range(1983,2022))+list(range(5500,5999)) if a.audit else list(range(5000,5000+a.years));validate_years(years,a.audit)
    tasks=[(m,s,soil,years[i:i+50],a.tag,a.audit) for m in a.models for s in ([4,17,29] if m in run.MODELS else [4]) for soil in ['default','fast','slow'] for i in range(0,len(years),50)]
    rows=[];start=time.monotonic()
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as ex:
        for r in ex.map(evaluate,tasks):
            rows.append(r);out.with_suffix('.progress.json').write_text(json.dumps(dict(seconds=time.monotonic()-start,records=rows)));print(json.dumps({k:v for k,v in r.items() if k not in ['episodes','events']}),flush=True)
    out.write_text(json.dumps(dict(status='completed',split='audit' if a.audit else 'dev',years=years,seconds=time.monotonic()-start,records=rows)))
