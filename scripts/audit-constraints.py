import numpy as np,json,pathlib
from pcse_gym.agent.ppo_mod import fertilization_action_constraint
case=dict(actions=np.array([1.]),episodic_step=np.array([10]),non_zero_action_counter=np.array([1]),last_non_zero_action_step=np.array([9]),dvs=np.array([.5]),nitrogen_efficiency=np.array([.7]),nitrogen_surplus=np.array([20.]),end_of_episode_mask=np.array([True]))
valid=fertilization_action_constraint(**case)
case['end_of_episode_mask']=np.array([False]);spacing=fertilization_action_constraint(**case)
out={'valid_terminal_case':{'NUE':.7,'surplus':20,'expected_endpoint_costs':[0,0],'observed_endpoint_costs':[float(np.asarray(c).sum()) for c in valid[3:]],'contract_passed':all(float(np.asarray(c).sum())==0 for c in valid[3:])},'one_week_spacing_case':{'expected_spacing_violation':True,'observed_spacing_cost':float(np.asarray(spacing[2]).sum()),'contract_passed':float(np.asarray(spacing[2]).sum())>0},'scope':'Diagnostics on unchanged published scientific cost function. No fix applied.'}
pathlib.Path('reports/constraint-audit.json').write_text(json.dumps(out,indent=2));print(out)
