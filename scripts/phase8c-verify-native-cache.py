"""Real TRAIN native-vs-cache equivalence; no tuning or final-outcome access."""
from pathlib import Path
import json,torch
from pcse_gym.agromas_v8.joint_model import FrozenJointWorldModel
from pcse_gym.agromas_v8.controller import FiveSpecialistTeam
from pcse_gym.agromas_v8.policies import TreePolicy,SensorlessPPOPolicy,LegacyV6Policy,FixedDosePolicy
from pcse_gym.agromas_v8.referee import prepare_daily_outputs,run_episode
from pcse_gym.agromas_v8.trajectory_cache import NativeWorldCache
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';D=R/'data/phase8c-train-cache-equivalence'
if __name__=='__main__':
 assert not D.exists();D.mkdir();torch.set_num_threads(2);prepare_daily_outputs(R);teams={track:FiveSpecialistTeam(R,FrozenJointWorldModel(R,track,'MLP',device='cuda')) for track in ('Sensorless','Full-Telemetry')};records=[];worlds=[]
 specs=[('tree','Sensorless',40.,1.,0.,None),('soft','Sensorless',40.,1.,0.,None),('soft','Sensorless',40.,2.,0.,None),('soft','Sensorless',40.,1.,50.,None),('tree','Full-Telemetry',40.,1.,0.,None),('open-loop','Sensorless',40.,1.,0.,None),('greedy-frozen','Sensorless',40.,1.,0.,None),('soft','Sensorless',25.,1.,0.,'eco'),('tree','Sensorless',40.,2.,0.,'econ'),('soft','Sensorless',40.,1.,0.,'climate'),('PPO','Sensorless',40.,1.,0.,None),('DVS','Full-Telemetry',40.,1.,0.,None),('legacy','Full-Telemetry',40.,1.,0.,None)]
 for region,year,climate in [('netherlands_lelystad',2005,'Historical'),('australia_wa_perth',2003,'idealized_mid'),('china_ncp_luancheng',2001,'idealized_high')]:
  world=(region,year,climate,'NASA');cache=NativeWorldCache(R,world,None)
  for i,(mode,track,cap,price,sub,remove) in enumerate(specs):
   case=dict(region=region,year=year,climate=climate,source='NASA',role='Train',cap=cap,price_multiplier=price,subsidy=sub,tax=0.,mode=mode,track=track,scope='TRAIN integration equivalence only;no selection')
   def factory():
    if mode=='PPO':return SensorlessPPOPolicy(R,teams['Sensorless'],4,model_dir=R/'models/phase8c-controls/ppo-sensorless-reconstructed-seed4')
    if mode=='DVS':return FixedDosePolicy(teams[track])
    if mode=='legacy':return LegacyV6Policy(R)
    return TreePolicy(teams[track],mode=mode,remove=remove)
   cached=cache.run(case,factory());native=run_episode(R,case,factory(),None);a={k:v for k,v in cached.items() if k!='native_cache'}
   assert json.dumps(a,sort_keys=True,default=str,allow_nan=False)==json.dumps(native,sort_keys=True,default=str,allow_nan=False),'Exact native/cache mismatch'
   assert cached['mass_audit']['passed']
   (D/f'{region}-{climate}-{i}.json').write_text(json.dumps(dict(cached=cached,reference=native),indent=2,default=str,allow_nan=False))
   records.append(dict(world=list(world),configuration=i,mode=mode,track=track,remove=remove,exact_full_result_equal=True,cache_replayed=cached['native_cache']['trajectory_replayed'],N=cached['mass_audit']['max_abs_N_residual_kg_ha'],C=cached['mass_audit']['max_abs_C_residual_kg_ha']));print(json.dumps(records[-1]),flush=True)
  worlds.append(cache.receipt())
 assert len(records)==39 and sum(w['cases_replayed'] for w in worlds)>0
 (P/'phase8c-native-cache-equivalence.json').write_text(json.dumps(dict(tests=records,passed=len(records),failed=0,full_result_exact_equality=True,TRAIN_only=True,no_fitting_or_selection=True,world_receipts=worlds,reference_native_simulations=len(records),cached_native_simulations=sum(w['native_simulations'] for w in worlds),all_daily_mass_passed=True),indent=2))
