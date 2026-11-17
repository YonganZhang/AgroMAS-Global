"""Train-only end-to-end test: frozen-book policy replay matches real weekly engine."""
from pathlib import Path
import json,numpy as np,logging
from pcse_gym.agromas.replay import replay_book
from pcse_gym.agromas.runtime import RegionalWeeklyEnv
R=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 logging.disable(logging.CRITICAL)
 beta=json.loads((R/'reports/phase5/policy-train-freeze-v2.json').read_text())['selected_beta'];results=[]
 for name in ('netherlands_lelystad','china_ncp_luancheng','australia_wa_perth'):
  path=R/f'data/phase5-teachers-v2/{name}-2000-Historical.jsonl'
  book={tuple(r['plan']):r for r in map(json.loads,path.read_text().splitlines())}
  expected=replay_book(str(R),book,year=2000,climate='Historical',zone='standard_40',price_multiplier=1.,subsidy=0.,beta=beta)
  e=RegionalWeeklyEnv(str(R),beta=beta,role='Train',evaluation=dict(region_id=name,year=2000,climate='Historical',zone='standard_40',price_multiplier=1.,subsidy=0.))
  e.reset(seed=4);done=False
  while not done:_,_,done,_,info=e.step(e.coordinated_action())
  error=float(np.max(np.abs(np.array(expected['outcome'])-info['outcome'])))
  assert error<1e-8,(name,error)
  results.append(dict(region_id=name,max_outcome_absolute_difference=error,plan=expected['plan'],events=info['stage_events'],
   soil_N_mass_balance_residual_kg_ha=info['stock_diagnostics']['soil_N_mass_balance_residual_kg_ha']))
 p=R/'reports/phase5/TRAIN-replay-real-engine-equivalence-v2.json'
 with p.open('x') as f:json.dump(dict(status='passed',scope='3TRAINseasons;frozenbookreplaymatchesrealsharedweeklycontroller,notHeld-Outefficacy',results=results),f,indent=2)
 p.chmod(0o444);print(json.dumps(results),flush=True)
