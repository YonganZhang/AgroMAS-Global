"""Train-only first-Stage3 decision readout. Does not modify/save any checkpoint."""
import pathlib,sys,json,numpy as np,torch
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
import pcse.input
from pcse_gym.agent.ppo_mod import LagrangianPPO
windows=json.loads((R/'reports/phase3b-training-observation-windows.json').read_text())['observations'];raw=json.loads((R/'reports/phase3b-training-calibration-v1.json').read_text())['episodes'];lookup={(r['year'],r['soil'],r['actual_N']):r for r in raw if r['stages']==[70,130]};obs=np.array([r['observation'] for r in windows],dtype=np.float32);torch.set_num_threads(1);out={}
for strength in [.05,.1,.2,.3,.5,1.]:
 byseed={}
 for seed in [4,17,29]:
  m=LagrangianPPO.load(R/f'reports/phase3b2-runs/v3-c8-full3-seed{seed}/model.zip',device='cpu');m.policy.prior_strength=strength;actions=m.predict(obs,deterministic=True)[0];selected=[];unknown=0
  for r,a in zip(windows,actions):
   n=130+10*int(a);sample=lookup.get((r['year'],r['soil'],n))
   if sample is None:unknown+=1
   else:selected.append(sample)
  byseed[str(seed)]=dict(coverage=len(selected)/150,unmeasured_action_count=unknown,mean_first_stage3_N=float(np.mean(130+10*actions)),joint_one_shot=float(np.mean([.5<=e['NUE']<=.9 and 0<=e['surplus']<=40 for e in selected])) if selected else None)
 out[str(strength)]=byseed
fixed=[r for r in raw if r['stages']==[70,130] and r['actual_N']==190];result=dict(training_only=True,checkpoints_unchanged=True,first_stage3_only=True,not_a_deployed_policy_or_full_trajectory_evaluation=True,fixed190_joint=float(np.mean([.5<=r['NUE']<=.9 and 0<=r['surplus']<=40 for r in fixed])),results=out)
p=R/'reports/phase3b-training-prior-strength-probe.json';assert not p.exists();p.write_text(json.dumps(result,indent=2));print(json.dumps(result))
