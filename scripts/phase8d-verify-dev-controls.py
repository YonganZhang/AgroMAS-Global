"""Fixed Dev-only closed-loop checks,never a controller-selection loop."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import json,hashlib
import numpy as np
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';O=R/'data/phase8d-dev-controls'
def worker(world):
 import torch
 from pcse_gym.agromas_v8.joint_model import FrozenJointWorldModel
 from pcse_gym.agromas_v8.controller import FiveSpecialistTeam
 from pcse_gym.agromas_v8.policies import TreePolicy
 from pcse_gym.agromas_v8.trajectory_cache import NativeWorldCache
 torch.set_num_threads(1);region,year=world;cache=NativeWorldCache(R,(region,year,'Historical','NASA'),None);models={t:FiveSpecialistTeam(R,FrozenJointWorldModel(R,t,'MLP',device='cuda' if torch.cuda.is_available() else 'cpu')) for t in ['Full-Telemetry','Sensorless']};records=[]
 for track in models:
  for mode in ['soft','tree']:
   for cap in [25.,35.,40.]:
    case=dict(region=region,year=year,role='Dev',source='NASA',climate='Historical',track=track,policy='TreeMLP',mode=mode,cap=cap,price_multiplier=1.,subsidy=0.,tax=0.);result=cache.run(case,TreePolicy(models[track],mode=mode));key=hashlib.sha256(json.dumps(case,sort_keys=True).encode()).hexdigest()[:20];f=O/(key+'.json');f.write_text(json.dumps(result));records.append(dict(region=region,year=year,track=track,mode=mode,cap=cap,joint=result['joint'],Executed_N=result['outcome'][4],NUE=result['outcome'][3],mass_passed=result['mass_audit']['passed'],path=str(f.relative_to(R)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
 return records,cache.receipt()
if __name__=='__main__':
 from pcse_gym.agromas.regions import REGIONS
 from pcse_gym.agromas_v8.referee import prepare_daily_outputs
 if O.exists():raise FileExistsError('Preserve Dev diagnostic')
 O.mkdir();prepare_daily_outputs(R);records=[];receipts=[]
 with ProcessPoolExecutor(max_workers=4) as pool:
  for future in as_completed([pool.submit(worker,(r,y)) for r in REGIONS for y in range(2010,2015)]):
   a,b=future.result();records.extend(a);receipts.append(b);print(json.dumps(dict(world=b['world'],native=b['native_simulations'])),flush=True)
 summary=[]
 for region in REGIONS:
  for track in ['Full-Telemetry','Sensorless']:
   for mode in ['soft','tree']:
    for cap in [25.,35.,40.]:
     v=[x for x in records if (x['region'],x['track'],x['mode'],x['cap'])==(region,track,mode,cap)];summary.append(dict(region=region,track=track,mode=mode,cap=cap,n=len(v),joint=float(np.mean([x['joint'] for x in v])),Executed_N=float(np.mean([x['Executed_N'] for x in v]))))
 def cell(r,t,m,c):return next(x for x in summary if (x['region'],x['track'],x['mode'],x['cap'])==(r,t,m,c))
 gates={}
 for mode in ['soft','tree']:
  for track in ['Full-Telemetry','Sensorless']:
   gates[track+'-'+mode+'-AU_cap25_nonzero']=cell('australia_wa_perth',track,mode,25.)['joint']>0
   gates[track+'-'+mode+'-NL_tight_caps_lower_N']=all(cell('netherlands_lelystad',track,mode,c)['Executed_N']<cell('netherlands_lelystad',track,mode,40.)['Executed_N'] for c in [25.,35.])
  full=np.mean([cell(r,'Full-Telemetry',mode,40.)['joint'] for r in REGIONS]);sl=np.mean([cell(r,'Sensorless',mode,40.)['joint'] for r in REGIONS]);gates[mode+'-Full_strictly_higher_joint']=bool(full>sl)
 (P/'phase8d-Dev-control-verification.json').write_text(json.dumps(dict(scope='25 Historical Dev farm-years;fixed predeclared policies,no retuning',records=records,summary=summary,gates=gates,passed=all(gates.values()),all_mass_passed=all(x['mass_passed'] for x in records),world_receipts=receipts),indent=2));print(json.dumps(gates),flush=True)
