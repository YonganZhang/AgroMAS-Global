"""Frozen dev-only explanation replay; never alters the policy or executes generated text."""
import argparse,pathlib,json,hashlib,sys
import numpy as np
import torch
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
run=SourceFileLoader('phase3_runner',str(R/'scripts/phase3-run.py')).load_module()
from pcse_gym.agent.ppo_mod import LagrangianPPO
from pcse_gym.utils.attribution import explain_decision
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--model',default='full');p.add_argument('--tag',default='v1');a=p.parse_args();out=R/f'reports/phase3-attribution-{a.tag}.json';assert not out.exists()
 torch.set_num_threads(1);env=run.make_env(a.model,4,0,years=[5000],soil='default',training=False);env.unwrapped.sb3_env._phase2_fast_info=True
 ck=R/f'reports/phase3-runs/{a.tag}-{a.model}-seed4/model.zip';sha=hashlib.sha256(ck.read_bytes()).hexdigest();model=LagrangianPPO.load(ck,device='cpu');events=[]
 try:
  obs,_=env.reset(seed=4);done=False;total=0
  while not done:
   before=obs.copy();action=int(model.predict(obs,deterministic=True)[0]);obs,r,t,tr,info=env.step(action);done=t or tr;total+=10*info['executed_action']
   with torch.no_grad():latent=model.policy.extract_features(torch.tensor(before[None])).cpu().numpy()[0]
   event=explain_decision(before.tolist(),latent.tolist(),action,info['executed_action'],info['shield_reason'])
   event.update(DVS=float(before[-1,0]),LAI=float(before[-1,1])*10,past_week_rain_normalized=float(before[-1,4]),applied_N=float(before[-1,5])*400,remaining_budget=float(before[-1,9])*400,application_DVS=info['application_dvs'],application_date=info['application_date'])
   event['observable_explanation']=(f"Decision DVS={event['DVS']:.3f}, LAI={event['LAI']:.2f}, past rain index={event['past_week_rain_normalized']:.4f}, applied N={event['applied_N']:.1f}, remaining seasonal budget={event['remaining_budget']:.1f}; masked valid actions={int(before[-1,10:].sum())}; proposed/executed dose={action*10}/{info['executed_action']*10} kg/ha. This is a state/constraint explanation, not a causal feature-importance claim.")
   events.append(event)
  canonical=json.loads((R/f'reports/phase3-dev-full-{a.tag}.json').read_text())
  expected=[e for rec in canonical['records'] if rec['seed']==4 and rec['soil']=='default' for e in rec['episodes'] if e['year']==5000][0]
  assert total==expected['actual_N'];assert abs(float(list(info['WSO'].values())[-1])/1000-expected['yield_t_ha'])<1e-9
  assert hashlib.sha256(ck.read_bytes()).hexdigest()==sha
  out.write_text(json.dumps(dict(checkpoint_sha256=sha,year=5000,soil='default',seed=4,replay_matches_canonical=True,events=events),indent=2))
 finally:env.close()
