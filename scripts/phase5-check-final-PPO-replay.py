"""TRAIN-only actual frozen-PPO engine versus observable-book equivalence."""
from pathlib import Path
from itertools import product
import json,logging,numpy as np,torch
from pcse_gym.agromas.final_evaluation import ppo_assets,replay_final_book
from pcse_gym.agromas.runtime import RegionalWeeklyEnv
R=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 logging.disable(logging.CRITICAL);torch.set_num_threads(1);results=[]
 contexts=[('netherlands_lelystad',2000,'Historical','standard_40',1.,0),('china_ncp_luancheng',2000,'Historical','standard_40',1.,0),('australia_wa_perth',2000,'Historical','standard_40',1.,0),('australia_wa_perth',2001,'idealized_high','strict_25',2.,100),('netherlands_lelystad',2001,'idealized_high','strict_25',2.,200)]
 for (name,year,climate,zone,price,subsidy),mode,seed in product(contexts,('structured-shared','raw-shared'),(4,17,29)):
  model,norm=ppo_assets(str(R),mode,seed)
  e=RegionalWeeklyEnv(str(R),beta=200,role='Train',information_mode=mode,evaluation=dict(region_id=name,year=year,climate=climate,zone=zone,price_multiplier=price,subsidy=subsidy))
  obs,_=e.reset(seed=4);done=False;weekactions=[]
  while not done:
   action=int(np.asarray(model.predict(norm.normalize_obs(obs[None]),deterministic=True,action_masks=e.action_masks())[0]).ravel()[0])
   obs,_,done,_,info=e.step(action);weekactions.append(action)
  book={tuple(x['plan']):x for x in map(json.loads,(R/f'data/phase5-teachers-v2/{name}-{year}-{climate}.jsonl').read_text().splitlines())}
  # Earlier TRAIN books predate whole-profile diagnostics; these temporary output-only placeholders never enter decisions.
  for row in book.values():row['stock_diagnostics']={}
  expected=replay_final_book(str(R),book,zone=zone,price_multiplier=price,subsidy=subsidy,beta=200,policy='PPO',seed=seed,mode=mode,permit_path=None)
  error=float(np.max(np.abs(np.array(expected['outcome'])-info['outcome'])))
  assert error<1e-8,(name,mode,seed,error)
  assert expected['events']==info['stage_events'],(expected['events'],info['stage_events'])
  results.append(dict(region_id=name,year=year,climate=climate,zone=zone,price_multiplier=price,subsidy=subsidy,mode=mode,seed=seed,missed_window_events=sum(x.get('reason')=='missed_window' for x in expected['events']),predicted_infeasible_decisions=sum(x['predicted_infeasible'] for x in expected['trace']),outcome_max_abs_error=error,plan=expected['plan'],events=expected['events'],physical_weekly_steps=len(weekactions)))
 p=R/'reports/phase5/final-PPO-Train-replay-equivalence-v4.json'
 with p.open('x') as f:json.dump(dict(status='passed',role='Train',cases=results),f,indent=2)
 p.chmod(0o444);print(json.dumps(results),flush=True)
