"""Restore original strict subsidy criterion; retain v2 evidence unchanged."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import json,hashlib,logging,multiprocessing
import numpy as np
from pcse_gym.agromas.replay import replay_book
from pcse_gym.agromas.legacy_comparators import run_nl_reference
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5'

def reference(path):
 rows=list(map(json.loads,path.read_text().splitlines()));r=rows[0];name=r['region_id'];year=r['harvest_year'];climate=r['climate']
 if name=='netherlands_lelystad':
  result=run_nl_reference(str(R),year,policy='N2-PA-calendar',role='Train',climate=climate)
 else:
  book={tuple(x['plan']):x for x in rows};result=replay_book(str(R),book,year=year,climate=climate,zone='standard_40',price_multiplier=1.,subsidy=0.,beta=0.,variant='DVS-N2')
 return dict(region_id=name,harvest_year=year,climate=climate,outcome=result['outcome'],events=result['events'],reference='N2-PA-calendar' if name=='netherlands_lelystad' else 'DVS-N2-grid-transfer')

if __name__=='__main__':
 logging.disable(logging.CRITICAL)
 protocol=dict(status='correction_registered_before_final_unlock',supersedes_for_formal_confirmation='green-subsidy-selection-protocol-v2.json',
  reason='v2deviatedfromoriginalmethod:surplusonlyinsteadofalljoint;noecoreferenceinsteadofN2. Preservev2assecondarydescriptiveanalysis,restorestrictoriginalcontract.',
  criterion='First0/50/100/150/200withALL15TRAINyearsjointcompliantANDmeanpairedpartialprofitdifference>=0versuszero-subsidyN2reference',
  joint='0.5<=NUE<=0.9 AND0<=S<=cap;positiveinputsandNUE<=0.9alreadyimplyS>=0',
  reference='NLnativecalendarN2-PA;otherregionscommon-gridDVS-N2transfer;allv2physicalbackground;zero subsidy',
  selection_role='Trainonly',no_solution='nullselectedsubsidy;zeroonlydescriptivefallback;noHeldreselection',grid=[0,50,100,150,200],
  reuse='FullTRAINcontrolleroutcomesfromunchangedv2replay;noFullpolicyrefit;N2referencescomputedTrainonly')
 pp=P/'green-subsidy-selection-protocol-v3.json'
 with pp.open('x') as f:json.dump(protocol,f,indent=2)
 pp.chmod(0o444)
 registry=json.loads((P/'teacher-book-receipt-v2.json').read_text());paths=[]
 for x in registry['files']:
  p=R/x['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256'];paths.append(p)
 refs=[]
 with ProcessPoolExecutor(max_workers=8,mp_context=multiprocessing.get_context('fork')) as pool:
  for future in as_completed([pool.submit(reference,p) for p in paths]):refs.append(future.result())
 lookup={(x['region_id'],x['harvest_year'],x['climate']):x for x in refs};rows=[]
 original=P/'green-subsidy-TRAIN-replay-v2.jsonl';expected=json.loads((P/'green-subsidy-TRAIN-freeze-v2.json').read_text())['replay_sha256'];assert hashlib.sha256(original.read_bytes()).hexdigest()==expected
 for row in map(json.loads,original.read_text().splitlines()):
  ref=lookup[(row['region_id'],row['year'],row['climate'])];m=ref['outcome'];row=dict(row)
  row['reference_policy']=ref['reference'];row['reference_partial_profit']=200*m[0]-1.5*row['price_multiplier']*m[4]
  row['paired_partial_profit_difference']=row['partial_profit']-row['reference_partial_profit'];rows.append(row)
 replay=P/'green-subsidy-TRAIN-replay-v3.jsonl'
 with replay.open('x') as f:
  for row in rows:f.write(json.dumps(row)+'\n')
 replay.chmod(0o444);thresholds=[]
 for key in sorted({(x['region_id'],x['climate'],x['zone'],x['price_multiplier']) for x in rows}):
  group=[x for x in rows if (x['region_id'],x['climate'],x['zone'],x['price_multiplier'])==key];grid=[]
  for sigma in protocol['grid']:
   v=[x for x in group if x['subsidy']==sigma];assert len(v)==15
   violations=sum(not(.5<=x['outcome'][3]<=.9 and 0<=x['outcome'][2]<=x['cap']) for x in v);diff=float(np.mean([x['paired_partial_profit_difference'] for x in v]))
   grid.append(dict(subsidy=sigma,paired_mean_profit_difference=diff,joint_violation_years=violations,mean_joint=float(np.mean([x['joint'] for x in v])),qualifies=violations==0 and diff>=0))
  eligible=[x['subsidy'] for x in grid if x['qualifies']];chosen=eligible[0] if eligible else None
  thresholds.append(dict(zip(('region_id','climate','zone','price_multiplier'),key),selected_subsidy=chosen,confirmation_subsidy=chosen if chosen is not None else 0,
   status='TRAIN_selected' if chosen is not None else 'No_solution_in_registered_grid',grid=grid,bracket=None if chosen is None else [0 if chosen==0 else protocol['grid'][protocol['grid'].index(chosen)-1],chosen]))
 out=P/'green-subsidy-TRAIN-freeze-v3.json'
 with out.open('x') as f:json.dump(dict(status='TRAIN_frozen',groups=thresholds,dev_used=False,heldout_used=False,protocol_sha256=hashlib.sha256(pp.read_bytes()).hexdigest(),replay_sha256=hashlib.sha256(replay.read_bytes()).hexdigest(),reference_rows=refs,original_v2_preserved=True),f,indent=2)
 out.chmod(0o444);print(json.dumps(dict(selected=sum(x['selected_subsidy'] is not None for x in thresholds),no_solution=sum(x['selected_subsidy'] is None for x in thresholds))))
