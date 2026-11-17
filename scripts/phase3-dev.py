"""Dev-only evaluator. Held-out harvest years rejected before environment creation."""
import pathlib,sys,json,time,argparse,concurrent.futures,statistics,hashlib
import numpy as np
import torch
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
run=SourceFileLoader('phase3_runner',str(R/'scripts/phase3-run.py')).load_module()
b=SourceFileLoader('baseline_eval',str(R/'scripts/evaluate-baselines.py')).load_module()
from pcse_gym.envs.phase3 import prior_action
from pcse_gym.agent.ppo_mod import LagrangianPPO

def verify_candidate_environment(folder, model_name):
    """Refuse replay of an old full2 checkpoint under a different stage-mask implementation."""
    if model_name!='full2':return None
    receipt=json.loads((folder/'receipt.json').read_text())
    path='NUE_PCSE-Gym/pcse_gym/envs/phase3.py'
    expected=receipt.get('source_sha256',{}).get(path)
    actual=hashlib.sha256((R/path).read_bytes()).hexdigest()
    if expected!=actual:raise RuntimeError('Checkpoint/environment version mismatch; preserve original snapshot')
    return actual

def evaluate(task):
    name,seed,soil,years,tag=task
    assert all(5000<=y<=5499 for y in years),'Dev firewall'
    torch.set_num_threads(1)
    import logging;logging.disable(logging.CRITICAL)
    learned=name in run.MODELS
    env=run.make_env(name if learned else 'guided' if name=='prior' else 'masked' if name.startswith('prior') else 'raw',seed,0,years=[years[0]],soil=soil,training=False)
    env.unwrapped.sb3_env._phase2_fast_info=True
    model=None;sha=None
    if learned:
        ck=R/'reports/phase3-runs'/f'{tag}-{name}-seed{seed}'/'model.zip';verify_candidate_environment(ck.parent,name);sha=hashlib.sha256(ck.read_bytes()).hexdigest();model=LagrangianPPO.load(ck,device='cpu')
    rows=[];attributions=[]
    try:
        for year in years:
            env.unwrapped.overwrite_year(year);obs,_=env.reset(seed=seed);merged={};done=False;actual=0;steps=0;masked=intercept=0
            while not done:
                if model is not None:action=int(model.predict(obs,deterministic=True)[0])
                elif name.startswith('prior'):
                    f=obs[-1,:10]
                    if name=='prior':action=prior_action(f)
                    else:
                        target=int(name[5:]);dvs=float(f[0]);used=float(f[5])*400
                        cumulative=50 if .10<=dvs<.32 else 110 if .32<=dvs<.62 else target if .62<=dvs<=.88 else used
                        action=int(np.clip(np.ceil((cumulative-used-1e-4)/10),0,8))
                    action=action if obs[-1,10+action] else max([i for i in range(action+1) if obs[-1,10+i]])
                elif name=='zero':action=0
                else:
                    from datetime import date,timedelta
                    from pcse_gym.utils.nitrogen_helpers import get_standard_practices
                    dates,doses=get_standard_practices(name+'-PA',year)
                    current=env.unwrapped.date;action=sum(dose//10 for d,dose in zip(dates,doses) if d<current<=d+timedelta(days=7))
                before=obs.copy()
                obs,rew,term,trunc,info=env.step(action);done=term or trunc;steps+=1;actual+=info['executed_action']*10;intercept+=int(info['shield_triggered'])
                if year==5000 and seed==4 and soil=='default':
                    attributions.append(dict(DVS=float(before[-1,0]),LAI=float(before[-1,1])*10,past_week_rain_scaled=float(before[-1,4]),cumulative_N=float(before[-1,5])*400,remaining_budget=float(before[-1,9])*400,proposed=int(action),executed=info['executed_action'],reasons=info['shield_reason']))
                for k,v in info.items():
                    if isinstance(v,dict):merged.setdefault(k,{}).update(v)
            row=b.extract(merged,year,name);native_input=row['grain_N_kg_ha']/row['NUE'] if row['NUE']>0 else 0
            nue=row['grain_N_kg_ha']/(native_input-row['fertilization_kg_ha']+actual) if native_input else 0
            surplus=row['N_surplus_kg_ha']-row['fertilization_kg_ha']+actual
            row.update(soil=soil,seed=seed,actual_N=actual,NUE_actual=nue,surplus_actual=surplus,joint_actual=.5<=nue<=.9 and 0<=surplus<=40,proposed_violation_rate=info['proposed_violation_rate'],executed_violation_rate=info['executed_violation_rate'],guard_interception_rate=intercept/steps,mask_active_rate=info.get('mask_active_rate',0))
            rows.append(row)
        if model is not None:assert hashlib.sha256(ck.read_bytes()).hexdigest()==sha
        return dict(model=name,seed=seed,soil=soil,checkpoint_sha256=sha,episodes=rows,attributions=attributions)
    finally:env.close()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seeds',nargs='+',type=int,default=[4,17,29]);p.add_argument('--models',nargs='+',default=['full','prior','N2']);p.add_argument('--years',type=int,default=500);p.add_argument('--tag',default='v1');p.add_argument('--workers',type=int,default=45);p.add_argument('--output',required=True);a=p.parse_args()
    out=R/a.output
    if out.exists():raise RuntimeError('Evidence overwrite rejected')
    years=list(range(5000,5000+a.years));assert len(years)>0 and max(years)<=5499
    tasks=[(m,s,soil,years[i:i+50],a.tag) for m in a.models for s in (a.seeds if m in run.MODELS else [4]) for soil in ['default','fast','slow'] for i in range(0,len(years),50)]
    records=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as ex:
        for x in ex.map(evaluate,tasks):
            records.append(x);out.with_suffix('.progress.json').write_text(json.dumps(records));print(json.dumps({k:v for k,v in x.items() if k!='episodes'}),flush=True)
    out.write_text(json.dumps(dict(status='completed',split='dev',years=years,records=records)))
