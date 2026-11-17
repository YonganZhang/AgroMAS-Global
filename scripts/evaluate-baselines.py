import sys,pathlib,json,time,contextlib,statistics,datetime
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'NUE_PCSE-Gym'))
from pcse_gym.initialize_envs import initialize_env
from evaluate_agent import evaluate_treatment
from pcse_gym.utils.nitrogen_helpers import get_standard_practices, get_surplus_n
from pcse_gym.envs.rewards import calculate_nue

def summarize(rows):
 keys=['yield_t_ha','NUE','N_surplus_kg_ha','fertilization_kg_ha','N_loss_kg_ha','profit_kEUR_ha','NUE_annual_deposition','N_surplus_annual_deposition_kg_ha']
 d={'n':len(rows),'mean':{k:statistics.mean(x[k] for x in rows) for k in keys},'median':{k:statistics.median(x[k] for x in rows) for k in keys}}
 for k in ['NUE_satisfied','surplus_satisfied','joint_satisfied','action_frequency_satisfied','spacing_satisfied','phenology_satisfied','action_domain_satisfied']:
  d[k+'_rate']=statistics.mean(x[k] for x in rows);d[k.replace('_satisfied','_violation')+'_rate']=1-d[k+'_rate']
 return d

def extract(info,year,policy):
 last=lambda k:float(list(info[k].values())[-1]); acts=[(d,float(v)) for d,v in info['action'].items() if float(v)>0];nue=last('NUE');surplus=last('Nsurplus');dvs=info['DVS'];freq=len(acts)<=4;spacing=all((b[0]-a[0]).days>=14 for a,b in zip(acts,acts[1:]));pheno=all(.01<=float(dvs.get(d,float('nan')))<=1 for d,v in acts)
 return {'year':year,'policy':policy,'yield_t_ha':last('WSO')/1000,'NUE':nue,'N_surplus_kg_ha':surplus,'fertilization_kg_ha':sum(float(v) for v in info['fertilizer'].values()),'N_loss_kg_ha':last('NLOSSCUM'),'grain_N_kg_ha':last('NamountSO'),'NUE_annual_deposition':float(calculate_nue(sum(float(v) for v in info['fertilizer'].values()),last('NamountSO'),year=year)),'N_surplus_annual_deposition_kg_ha':float(get_surplus_n(sum(float(v) for v in info['fertilizer'].values()),last('NamountSO'),year=year)),'profit_kEUR_ha':last('profit')/1000,'NUE_satisfied':.5<=nue<=.9,'surplus_satisfied':0<=surplus<=40,'joint_satisfied':.5<=nue<=.9 and 0<=surplus<=40,'action_frequency_satisfied':freq,'spacing_satisfied':spacing,'phenology_satisfied':pheno,'action_domain_satisfied':all(0<=v<=8 and float(v).is_integer() for d,v in acts),'actions':[(d.isoformat(),v) for d,v in acts]}

def zero_episode(env):
 history=[];done=False
 while not done:
  _,_,term,trunc,info=env.step(0);history.append(info);done=term or trunc
 merged={k:{} for k in history[0]}
 for h in history:
  for k,v in h.items():merged[k].update(v)
 return merged

if __name__=='__main__':
 out={'protocol':{'years':list(range(1983,2022)),'location':[52.57,5.63],'weather':'official Zenodo CSV historic rows 1982-2021; random_weather=True selects file provider, NOT synthetic-year relabeling','random_init':False,'seed':4,'reward':'NUE','environment':2,'start_type':'sowing','soil':'arminda_soil.yaml','action_frequency_limit':4,'min_spacing_days':14,'DVS_range':[.01,1],'surplus_inclusive_lower_bound':0},'policies':{}}
 start=time.monotonic()
 with open(ROOT/'logs/deterministic-details.log','w') as log,contextlib.redirect_stdout(log):
  env=initialize_env(pcse_env=2,years=[1983],locations=[(52.57,5.63)],random_weather=True,random_init=False,reward='NUE',start_type='sowing',seed=4)
  out['observation_space']=str(env.observation_space);out['action_space']=str(env.action_space)
  for policy in ['N1-PA','N2-PA','N3-PA','Zero-N']:
   rows=[]
   for year in range(1983,2022):
    env.overwrite_year(year);env.reset(seed=4)
    info=zero_episode(env) if policy=='Zero-N' else evaluate_treatment(policy,env)[1][0]
    rows.append(extract(info,year,policy))
    (ROOT/'reports/deterministic-progress.json').write_text(json.dumps({'policy':policy,'last_year':year,'elapsed_seconds':time.monotonic()-start}))
   out['policies'][policy]={'summary':summarize(rows),'episodes':rows}
   (ROOT/'reports/deterministic-baselines.json').write_text(json.dumps(out,indent=2))
 out['wall_clock_seconds']=time.monotonic()-start
 (ROOT/'reports/deterministic-baselines.json').write_text(json.dumps(out,indent=2));print({k:v['summary'] for k,v in out['policies'].items()})
