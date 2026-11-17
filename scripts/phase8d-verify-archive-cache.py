"""TRAIN-only exact archive bootstrap and fresh-policy cache equivalence."""
from pathlib import Path
import json,hashlib,torch
from pcse_gym.agromas_v8.trajectory_cache import NativeWorldCache
from pcse_gym.agromas_v8.joint_model import FrozenJointWorldModel
from pcse_gym.agromas_v8.controller import FiveSpecialistTeam
from pcse_gym.agromas_v8.policies import TreePolicy
R=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 torch.set_num_threads(2);team=FiveSpecialistTeam(R,FrozenJointWorldModel(R,'Sensorless',device='cuda'));checks=[]
 for climate in ('Historical','idealized_mid','idealized_high'):
  path=R/f'data/phase8d-train-native-preflight/{climate}.json';original=json.loads(path.read_text());c=original['case'];world=(c['region'],c['year'],climate,c['source']);cache=NativeWorldCache(R,world,None)
  assert cache.seed_archive(path,hashlib.sha256(path.read_bytes()).hexdigest());assert not cache.nodes
  first=cache.run(c,TreePolicy(team,mode='soft'));second=cache.run(c,TreePolicy(team,mode='soft'))
  a={k:v for k,v in first.items() if k!='native_cache'};b={k:v for k,v in second.items() if k!='native_cache'}
  assert a==b==original;assert cache.native_simulations==1 and second['native_cache']['trajectory_replayed']
  checks.append(dict(climate=climate,exact_full_result_equal=True,public_prefix_recovered_natively=True,old_policy_decisions_reused=False,receipt=cache.receipt()))
 (R/'reports/phase8/phase8d-native-cache-equivalence.json').write_text(json.dumps(dict(TRAIN_only=True,full_result_exact_equality=True,checks=checks),indent=2));print('PASS: archive bootstrap and native prefix recovery agree exactly in all3 climates')
