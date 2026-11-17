"""Two prespecified subsidy rules; TRAIN only and no vacuous feasibility success."""
from pathlib import Path
import json,joblib
import numpy as np
from pcse_gym.agromas_v6.books import load_train,PLANS,FACTORS
from pcse_gym.agromas_v6.core import Policy,select_objective
from pcse_gym.agromas_v6.book_env import build_tables
R=Path(__file__).resolve().parents[1];P=R/'reports/phase6'
if __name__=='__main__':
 active=json.loads((P/'ACTIVE_TRAIN_RUN_V6.json').read_text());p=R/active['reports'];data,tables,legal=joblib.load(R/'cache/phase6'/active['run']/'train-book-ppo-inputs-v6.joblib');selected=json.loads((p/'policy-train-selection-v6.json').read_text())['selected'];policy=Policy(selected['beta'],selected['penalty'])
 refs=json.loads((R/'reports/phase5/green-subsidy-TRAIN-freeze-v3.json').read_text())['reference_rows'];reference={(r['region_id'],r['harvest_year'],r['climate']):r['outcome'] for r in refs};reachable=np.ones((len(data.keys),343),bool)
 for stage in (1,2,3):
  seen=data.available[:,stage-1];dose=PLANS[:,stage-1][None,:];committed=data.features[:,stage-1,:,3];reachable&=(seen&(committed+dose<=220+1e-8))|((~seen)&(dose==0))
 groups=[];allrows=[]
 for cap in (25.,35.,50.):
  m=data.outcomes;feasible=(reachable&(m[:,:,3]>=.5)&(m[:,:,3]<=.9)&(m[:,:,2]>=0)&(m[:,:,2]<=cap)).any(1)
  for price in (1.,2.):
   gridrows=[]
   for sigma in (0.,50.,100.,150.,200.):
    ix=np.zeros(len(data.keys),int);worlds=np.arange(len(data.keys))
    for stage in (1,2,3):
     prefix=ix//(7**(4-stage));stats=tables[stage][worlds,prefix];allowed=legal[stage][worlds,prefix];choice,_=select_objective(stats,allowed,cap,price,sigma,policy);ix+=choice*FACTORS[stage-1]
    for k,i in enumerate(ix):
     outcome=data.outcomes[k,i];key=data.keys[k];j=bool(.5<=outcome[3]<=.9 and 0<=outcome[2]<=cap);ref=reference[key];profit=200*outcome[0]-1.5*price*outcome[4]+sigma*j
     gridrows.append(dict(region_id=key[0],year=key[1],climate=key[2],cap=cap,price_multiplier=price,subsidy=sigma,physically_feasible_in_grid=bool(feasible[k]),joint=j,partial_profit=float(profit),paired_profit_difference=float(profit-(200*ref[0]-1.5*price*ref[4])),plan=PLANS[i].tolist(),outcome=outcome.tolist()))
   allrows.extend(gridrows)
   for region,climate in sorted({(k[0],k[2]) for k in data.keys}):
    candidates=[]
    for sigma in (0.,50.,100.,150.,200.):
     rows=[x for x in gridrows if x['region_id']==region and x['climate']==climate and x['subsidy']==sigma];assert len(rows)==15
     feasible_rows=[x for x in rows if x['physically_feasible_in_grid']];profit=float(np.mean([x['paired_profit_difference'] for x in rows]));candidates.append(dict(subsidy=sigma,n_years=15,n_feasible=len(feasible_rows),n_joint=sum(x['joint'] for x in rows),n_feasible_violations=sum(not x['joint'] for x in feasible_rows),mean_paired_partial_profit=profit,strict_qualifies=all(x['joint'] for x in rows) and profit>=0,feasible_qualifies=bool(feasible_rows) and all(x['joint'] for x in feasible_rows) and profit>=0))
    groups.append(dict(region_id=region,climate=climate,cap=cap,price_multiplier=price,strict_selected_subsidy=next((x['subsidy'] for x in candidates if x['strict_qualifies']),None),feasible_selected_subsidy=next((x['subsidy'] for x in candidates if x['feasible_qualifies']),None),grid=candidates,zero_feasible_not_success=True))
 out=dict(status='TRAIN_frozen',groups=groups,rows=allrows,profit_rule='MeanpairedpartialprofitoverALL15TRAINyearsversuszero-subsidyN2;NLnativecalendarreference,othersgridDVSN2',feasibility='Expostreachablefinitegridexistenceonly;notcausalachievabilityorcontinuousfieldfeasibility',final_books_used=False,new_daily_rollouts=0)
 with (p/'green-subsidy-TRAIN-freeze-v6.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(dict(groups=len(groups),strict_selected=sum(g['strict_selected_subsidy'] is not None for g in groups),feasible_selected=sum(g['feasible_selected_subsidy'] is not None for g in groups),zero_feasible_groups=sum(g['grid'][0]['n_feasible']==0 for g in groups))))
