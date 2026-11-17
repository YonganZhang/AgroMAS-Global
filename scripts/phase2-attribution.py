"""Read-only illustration of the frozen shield-only policy on the pre-defined dry case."""
import pathlib,sys,json,hashlib,importlib.util,numpy as np,torch
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
spec=importlib.util.spec_from_file_location('runner',R/'scripts/phase2-run.py');runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
from pcse_gym.agent.ppo_mod import LagrangianPPO
from pcse_gym.utils.attribution import explain_decision
model_name='shield';seed=4;year=1996;soil='default';torch.set_num_threads(1)
ckpt=R/'reports/phase2-runs/matched-v2-shield-seed4-env16/model.zip';frozen=json.loads((R/'reports/phase2-frozen-checkpoints.json').read_text());assert hashlib.sha256(ckpt.read_bytes()).hexdigest()==frozen[ckpt.parent.name]
m=LagrangianPPO.load(str(ckpt),device='cpu');env=runner.make_env(model_name,seed,0,years=[year],soil=soil,training=False);env.unwrapped.sb3_env._phase2_fast_info=True
obs,_=env.reset(seed=seed);done=False;events=[];total=0.
try:
 while not done:
  before=obs.copy();date=env.unwrapped.date.isoformat();action=int(np.asarray(m.predict(obs,deterministic=True)[0]).item())
  with torch.no_grad():latent=m.policy.extract_features(torch.as_tensor(before[None],device=m.device)).cpu().numpy()[0].tolist()
  obs,_,term,trunc,info=env.step(action);done=term or trunc;total+=info['executed_action']*10
  record=explain_decision(before.tolist(),latent,action,info['executed_action'],info['shield_reason'])
  record.update(date=date,application_date=info['application_date'],proposal_DVS=info['proposal_dvs'],application_DVS=info['application_dvs']);events.append(record)
 original=json.loads((R/'reports/phase2-evaluations-v3/shield-seed4-default.json').read_text());row=next(x for x in original['episodes'] if x['year']==year)
 assert total==row['actual_executed_fertilization_kg_ha'] and abs(list(info['WSO'].values())[-1]/1000-row['yield_t_ha'])<1e-12
 out={'model':'shield-only ablation, NOT Full','year':year,'seed':seed,'soil':soil,'checkpoint_sha256':frozen[ckpt.parent.name],'selection':'Fixed precipitation-defined historical dry case, seed4; illustration only, all outcomes remain in tables','replay_matches_canonical_metrics':True,'events':events}
 (R/'reports/phase2-shield-attribution-example.json').write_text(json.dumps(out,indent=2));print('Frozen shield-only attribution replay matches the canonical evaluation.')
finally:env.close()
assert hashlib.sha256(ckpt.read_bytes()).hexdigest()==frozen[ckpt.parent.name]
