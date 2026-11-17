"""TRAIN-only green-stress magnitude, distinct from old formal subsidy thresholds.

Select firstpositive50/100/150/200EUR/ha changing at least oneTRAIN policy plan
relative to0, across the two frozen parity tracks atcap40. No success criterion
is fitted on evaluation labels, and no all-years-compliance claim is made.
"""
from pathlib import Path
import json,hashlib,torch
from pcse_gym.agromas_v8.controller import FiveSpecialistTeam
from pcse_gym.agromas_v8.joint_model import FrozenJointWorldModel
from pcse_gym.agromas_v8.online_features import history_from_provider
from pcse_gym.agromas.season import regional_weather
from datetime import date
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8'
if __name__=='__main__':
 torch.set_num_threads(2);registry=json.loads((R/'reports/phase5/teacher-book-receipt-v2.json').read_text());entries=[e for e in registry['files'] if '-Historical.' in e['path']];assert len(entries)==75;records=[]
 protocol={'scope':'TRAIN-selected experimental economic stress,NOTformalminimumsubsidyproposal','grid':[0,50,100,150,200],'cap':40,'price_multiplier':1,'criterion':'firstpositivechangingatleastonefullthree-stageTRAINplanrelativeto0acrossfixedFull/Sensorlesscontrollers','if_no_change':'null;donotinventsuccessfulsubsidy','old_v6_strict_thresholds':'untouched,mostlynull;thisnewstresschoiceisnotthatcriterion','no_final_outcomes_accessed':True};(P/'phase8b-green-stress-selection-protocol.json').write_text(json.dumps(protocol,indent=2))
 for track in ['Full-Telemetry','Sensorless']:
  model=FrozenJointWorldModel(R,track,'MLP',device='cuda')
  for ent in entries:
   path=R/ent['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==ent['sha256'];rows={tuple(v['plan']):v for v in map(json.loads,path.read_text().splitlines())};first=rows[(0,0,0)];year=first['harvest_year'];region=first['region_id'];assert first['role']=='Train' and 1995<=year<=2009
   team=FiveSpecialistTeam(R,model,train_analog_years=tuple(y for y in range(1995,2010) if y!=year));provider=regional_weather(str(R),region,'v2')
   for sigma in [0,50,100,150,200]:
    plan=[0.,0.,0.];row=first;trace=[]
    for stage in [1,2,3]:
     state=row['states'].get(str(stage))
     if state:
      state=dict(state);day=date.fromisoformat(state['as_of']);past=[date.fromisoformat(e['date']) for e in row['events'] if e['dose']>0 and e['date']<=state['as_of']];state['days_since_last_fert']=min(60,(day-max(past)).days) if past else 60
      h=history_from_provider(provider,region,day);d=team.choose(state,h,subsidy=sigma);plan[stage-1]=d['dose'];trace.append({'stage':stage,'tier':d['tier']})
     row=rows[tuple(plan)]
    m=row['outcome'];records.append({'track':track,'region':region,'year':year,'subsidy':sigma,'plan':plan,'actual_TRAIN_outcome':m,'joint':bool(.5<=m[3]<=.9 and 0<=m[2]<=40),'trace':trace})
   print(json.dumps({'track':track,'region':region,'year':year,'records':len(records)}),flush=True)
 baseline={(x['track'],x['region'],x['year']):x['plan'] for x in records if x['subsidy']==0};changes={s:sum(x['plan']!=baseline[(x['track'],x['region'],x['year'])] for x in records if x['subsidy']==s) for s in [50,100,150,200]};selected=next((s for s in [50,100,150,200] if changes[s]>0),None)
 (P/'phase8b-green-stress-TRAIN-freeze.json').write_text(json.dumps({'selected_subsidy':selected,'changes':changes,'criterion':protocol,'records':records,'no_formal_success_claim':True},indent=2));print(json.dumps({'selected_subsidy':selected,'changes':changes}),flush=True)
