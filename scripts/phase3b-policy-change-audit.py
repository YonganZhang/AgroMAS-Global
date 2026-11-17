"""Compare actually trained checkpoints across unsuccessful campaigns; no simulation."""
import pathlib,json,sys,hashlib
import numpy as np
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
SourceFileLoader('audit_runner',str(R/'scripts/phase3b2-run.py')).load_module()
from pcse_gym.agent.ppo_mod import LagrangianPPO
rows=[]
for seed in [4,17,29]:
 vectors={};heads={};items={}
 for tag,parent in [('v3','phase3b-runs'),('v3-long','phase3b-runs'),('v3-c8','phase3b2-runs')]:
  p=R/f'reports/{parent}/{tag}-full3-seed{seed}';receipt=json.loads((p/'receipt.json').read_text());m=LagrangianPPO.load(p/'model.zip',device='cpu')
  vectors[tag]=np.concatenate([v.detach().cpu().numpy().ravel() for v in m.policy.parameters()]);heads[tag]=m.policy.action_net.weight.detach().cpu().numpy().ravel()
  items[tag]=dict(actual_steps=receipt['actual_steps'],receipt_parameters_changed=receipt['parameters_changed'],head_sha256=hashlib.sha256(heads[tag].tobytes()).hexdigest(),optimizer_updates=m._n_updates)
 rows.append(dict(seed=seed,models=items,full_L2_from_short={k:float(np.linalg.norm(v-vectors['v3'])) for k,v in vectors.items() if k!='v3'},head_L2_from_short={k:float(np.linalg.norm(v-heads['v3'])) for k,v in heads.items() if k!='v3'}))
p=R/'reports/phase3b-policy-change-audit.json';assert not p.exists();p.write_text(json.dumps(dict(no_simulation=True,audit=rows,interpretation='Distinct trained parameters can yield identical deterministic actions. This rejects unchanged-weight explanation, not alternative implementation defects.'),indent=2))
