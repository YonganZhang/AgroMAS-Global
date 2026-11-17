"""One TRAIN-only real-engine calendar proof; no parameter fitting or heldout access."""
import pathlib,json,sys,hashlib,torch
from importlib.machinery import SourceFileLoader
from datetime import date
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'));run=SourceFileLoader('spacing_train_env',str(R/'scripts/phase4-ppo-run.py')).load_module();controller=SourceFileLoader('spacing_controller',str(R/'scripts/phase4-controller.py')).load_module()
from pcse_gym.envs.moisture4 import UtilityScorer
if __name__=='__main__':
 e=run.make_env('full4',4,0,years=[3002],soil='default',training=True)
 policy=controller.FrozenCUOController(UtilityScorer(run.calibration()));events=[];step=0
 try:
  obs,_=e.reset(seed=4);done=False
  while not done:
   decision=e.unwrapped.date;a=policy.act(obs);obs,r,t,tr,info=e.step(a);done=t or tr
   if info['executed_action']>0:events.append(dict(step=step,decision_date=str(decision),application_date=info['application_date'],dose=10*info['executed_action']))
   step+=1
 finally:e.close()
 offsets=[(date.fromisoformat(x['application_date'])-date.fromisoformat(x['decision_date'])).days for x in events];gaps=[(date.fromisoformat(b['application_date'])-date.fromisoformat(a['application_date'])).days for a,b in zip(events,events[1:])];countergaps=[7*(b['step']-a['step']) for a,b in zip(events,events[1:])]
 assert len(set(offsets))==1 and gaps==countergaps and all(g>=14 for g in gaps)
 out=R/'reports/phase4-calendar-spacing-proof.json';assert not out.exists();out.write_text(json.dumps(dict(training_only=True,year=3002,events=events,execution_offsets_days=offsets,actual_gaps_days=gaps,counter_gaps_days=countergaps,all_minimum14=True,scope='Fixed native weekly timestep: every positive application executes at same interval-last offset; no variable-step guarantee',extra_verification_seasons=1),indent=2));print(offsets,gaps,countergaps)
