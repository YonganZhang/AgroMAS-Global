"""Training-year only model initialization probe; no ablation training or Dev tuning."""
import pathlib,sys,json,torch,numpy as np
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1]
r=SourceFileLoader('sm_contract_runner',str(R/'scripts/phase3b3-run.py')).load_module()
rows=[];torch.set_num_threads(1)
for model in r.MODELS:
 e=r.make_env(model,4,0,years=[3002],soil='default',training=True)
 try:
  obs,info=e.reset(seed=4);assert obs.shape[-1] in [11,20];assert 0<=float(obs[-1,10])<=1
  kw=dict(net_arch=dict(pi=[32,32],vf=[32,32]));v3=model not in ['raw','corrected'];guided=model in ['guided','full3']
  if guided:kw.update(features_extractor_class=r.CausalGRUExtractor,features_extractor_kwargs=dict(features_dim=7),prior_strength=.3,prior_final=190,stages=[70,130])
  elif v3:kw.update(features_extractor_class=r.VisibleFrameExtractor,prior_strength=0)
  policy=(r.MoisturePolicy if v3 else r.CostActorCriticPolicy)(e.observation_space,e.action_space,lambda _:0.0003,**kw)
  batch=torch.as_tensor(obs[None]);a,_,_,lp=policy(batch);_,_,lp2,_=policy.evaluate_actions(batch,a);assert torch.allclose(lp,lp2)
  nxt,reward,t,tr,inf=e.step(int(a[0]));assert np.isfinite(nxt).all()
  rows.append(dict(model=model,observation_shape=list(obs.shape),SM=float(obs[-1,10]),parameter_count=sum(p.numel() for p in policy.parameters()),matching_log_prob=True,step_finite=True))
 finally:e.close()
out=R/'reports/phase3b3-tier-contract-probe.json';assert not out.exists();out.write_text(json.dumps(dict(training_only=True,initialization_only=True,no_ablation_training=True,models=rows),indent=2));print(json.dumps(rows))
