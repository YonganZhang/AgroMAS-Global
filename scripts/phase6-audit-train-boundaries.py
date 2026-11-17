"""Reproducible all-TRAIN reconstruction and outcome-label boundary audit."""
from pathlib import Path
import importlib.util,json,hashlib,joblib,numpy as np,sys
from pcse_gym.agromas_v6.core import Policy,select_objective
from pcse_gym.agromas_v6.books import FACTORS,PLANS
from pcse_gym.agromas_v6.book_env import TrainBookEnv
from pcse_gym.agromas_v6.training import replay
R=Path(__file__).resolve().parents[1];P=R/'reports/phase6'
if __name__=='__main__':
 source_sha=hashlib.sha256((R/'scripts/phase6-score-final.py').read_bytes()).hexdigest();spec=importlib.util.spec_from_file_location('score',R/'scripts/phase6-score-final.py');score=importlib.util.module_from_spec(spec);spec.loader.exec_module(score);active=json.loads((P/'ACTIVE_TRAIN_RUN_V6.json').read_text());p=R/active['reports'];selected=json.loads((p/'policy-train-selection-v6.json').read_text())['selected'];policy=Policy(selected['beta'],selected['penalty']);data,tables,legal=joblib.load(R/'cache/phase6'/active['run']/'train-book-ppo-inputs-v6.joblib');models={s:joblib.load(R/active['models']/'Full'/f'stage-{s}.joblib') for s in (1,2,3)};records=[]
 for path in sorted((R/'data/phase5-teachers-v2').glob('*.jsonl')):
  rows,rebuilt,first=score.load_book(path);maximum=0
  for i,plan in enumerate(PLANS):
   for stage,base in rows[tuple(plan)]['features'].items():maximum=max(maximum,float(np.max(np.abs(rebuilt.features[0,int(stage)-1,i]-base))))
  assert maximum<1e-10;records.append(dict(path=str(path.relative_to(R)),max_feature_difference=maximum,prefix_check='passed',feature_shape=list(rebuilt.features.shape)))
 assert len(records)==225
 env=TrainBookEnv(data,tables,legal,policy);original=data.outcomes.copy()
 for seed in range(30):
  data.outcomes[:]=original;obs,_=env.reset(seed=seed);seen=[];ended=False
  while not ended:
   mask=env.action_masks();action=int(np.flatnonzero(mask)[0]);seen.append((obs.copy(),mask.copy()));obs,_,ended,_,_=env.step(action)
  data.outcomes[:]=original;data.outcomes[:,:,0]+=123;obs,_=env.reset(seed=seed);ended=False;i=0
  while not ended:
   mask=env.action_masks();assert np.array_equal(obs,seen[i][0]) and np.array_equal(mask,seen[i][1]);obs,_,ended,_,_=env.step(int(np.flatnonzero(mask)[0]));i+=1
 data.outcomes[:]=original
 for seed in range(20):
  obs,_=env.reset(seed=100+seed);world=env.world;cap=env.cap;price=env.price;subsidy=env.subsidy;ended=False
  while not ended:
   s=env.stage;prefix=env.index//(7**(4-s));action,_=select_objective(tables[s][world,prefix][None],legal[s][world,prefix][None],cap,price,subsidy,policy);obs,_,ended,_,info=env.step(int(action[0]))
  actual=replay(data,[world],models,policy,cap=cap,price=price,subsidy=subsidy)[0];assert actual['plan']==info['plan'] and abs(actual['partial_profit']-info['partial_profit'])<1e-10
 assert source_sha==hashlib.sha256((R/'scripts/phase6-score-final.py').read_bytes()).hexdigest(),'Loadersourcechangedduringaudit'
 result=dict(status='passed',scope='All225TRAINbooks1995to2009;nofinalstatesoroutcomesopened',reconstruction=records,label_perturbation_cases=30,direct_vs_cached_replay_cases=20,loader_source_sha256=hashlib.sha256((R/'scripts/phase6-score-final.py').read_bytes()).hexdigest(),generator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 with (p/(sys.argv[1] if len(sys.argv)>1 else 'TRAIN-boundaries-reconstruction-full-v6.json')).open('x') as f:json.dump(result,f,indent=2)
 print(json.dumps(dict(status='passed',books=len(records),perturbation_cases=30,replay_cases=20)))
