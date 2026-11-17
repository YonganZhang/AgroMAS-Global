"""Dev-only bug diagnostic: compare learned action with exact prior on the SAME observation."""
import pathlib,sys,json,torch,numpy as np
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
run=SourceFileLoader('decision_probe_runner',str(R/'scripts/phase3b2-run.py')).load_module()
from pcse_gym.agent.ppo_mod import LagrangianPPO
from pcse_gym.envs.corridor import target
out=[];torch.set_num_threads(1)
for seed in [4,17,29]:
 env=run.make_env('full3',seed,0,years=[5000],soil='default',training=False);env.unwrapped.sb3_env._phase2_fast_info=True
 model=LagrangianPPO.load(R/f'reports/phase3b2-runs/v3-c8-full3-seed{seed}/model.zip',device='cpu')
 try:
  obs,_=env.reset(seed=seed);done=False;events=[]
  while not done:
   a=int(model.predict(obs,deterministic=True)[0]);f=obs[-1,:10];prior=int(np.clip(np.ceil((float(target(f[0],f[5]*400,190))-f[5]*400-1e-4)/10),0,8));masked_prior=max(i for i in range(prior+1) if obs[-1,10+i])
   if a>0 or masked_prior>0:
    with torch.no_grad():pi=model.policy.mlp_extractor.forward_actor(model.policy.extract_features(torch.tensor(obs[None])));logits=model.policy.action_net(pi)[0].numpy().tolist()
    events.append(dict(DVS=float(f[0]),LAI=float(f[1])*10,cumulative=float(f[5])*400,remaining=float(f[9])*400,action=a,prior=prior,masked_prior=masked_prior,raw_logits=logits,mask=obs[-1,10:].tolist()))
   obs,r,t,tr,info=env.step(a);done=t or tr
  out.append(dict(seed=seed,events=events))
 finally:env.close()
p=R/'reports/phase3b-decision-path-probe.json';assert not p.exists();p.write_text(json.dumps(out,indent=2));print([{k:v for k,v in row.items() if k!='events'}|{'events':[{k:v for k,v in e.items() if k not in ['raw_logits','mask']} for e in row['events']]} for row in out])
