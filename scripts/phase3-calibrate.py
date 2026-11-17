"""Training-only phenology margin diagnostic, not an all-weather proof."""
import pathlib,sys,json
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1]
run=SourceFileLoader('phase3_runner',str(R/'scripts/phase3-run.py')).load_module()
from pcse_gym.envs.phase3 import prior_action
rows=[]
for soil in ['default','fast','slow']:
    env=run.make_env('guided',4,0,years=list(range(3002,3022)),soil=soil,training=True)
    env.unwrapped.sb3_env._phase2_fast_info=True
    try:
        for year in range(3002,3022):
            env.unwrapped.overwrite_year(year);obs,_=env.reset(seed=year);done=False
            while not done:
                a=prior_action(obs[-1,:10]);a=a if obs[-1,10+a] else 0
                obs,r,t,tr,info=env.step(a);done=t or tr
                if .01<=info['proposal_dvs']<=1:rows.append(dict(year=year,soil=soil,proposal_DVS=info['proposal_dvs'],delta_DVS=info['application_dvs']-info['proposal_dvs'],guard_interception=info['shield_triggered']))
    finally:env.close()
out=R/'reports/phase3-training-margin-diagnostic.json';assert not out.exists()
out.write_text(json.dumps(dict(years=[3002,3021],training_only=True,random_initial_conditions=True,margin=.12,max_observed_delta=max(x['delta_DVS'] for x in rows),universal_bound_claim=False,rows=rows)))
