"""Fixed task criteria; no policy/alpha selection on Dev."""
import pathlib,json,hashlib,statistics,math
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1];s=SourceFileLoader('p4_stats',str(R/'scripts/phase3b-report.py')).load_module();stat=SourceFileLoader('p4_tests',str(R/'scripts/phase3-report.py')).load_module()
if __name__=='__main__':
 src=R/'reports/phase4-dev-counterfactual.json';data=json.loads(src.read_text());assert data['status']=='completed';groups={name:[e for r in data['records'] if r['model']==name for e in r['episodes']] for name in ['cf-gru','utilityprior','prior170']};assert len(groups['cf-gru'])==4500 and len(groups['utilityprior'])==1500
 old=json.loads((R/'reports/phase3b-dev-controls-v3.json').read_text())['records'];refs={n:[e for r in old if r['model']==n for e in r['episodes']] for n in ['N2-PA','prior190']};refs['full4']=[e for r in json.loads((R/'reports/phase3c-dev-full4-v4-sm.json').read_text())['records'] for e in r['episodes']]
 original=[e for r in json.loads((R/'reports/phase3c-dev-utilityprior-v4-sm.json').read_text())['records'] if r['model']=='utilityprior' for e in r['episodes']];key=lambda r:(r['year'],r['soil']);original={key(e):e for e in original}
 assert all(all(e[k]==original[key(e)][k] for k in ['actual_N','yield_t_ha','NUE_actual','surplus_actual']) for e in groups['utilityprior'])
 result={}
 for name in ['cf-gru','utilityprior']:
  rows=groups[name];summary=s.summary(rows);comparison={n:stat.comparison(rows,rr) for n,rr in refs.items()};comparison['utilityprior']=stat.comparison(rows,groups['utilityprior']);checks=dict(joint_at_least59_40=summary['joint']>=.594-1e-12,CVaR_at_most55_5=summary['cvar10_surplus']<=55.5,proposed_safe=all(e['proposed_violation_rate']==0 for e in rows),executed_safe=all(e['executed_violation_rate']==0 for e in rows))
  for n,limit in [('prior190',.001),('full4',.001),('N2-PA',1e-50)]:checks['p_vs_'+n]=comparison[n]['joint_actual']['wilcoxon_year_mean_p']<limit
  result[name]=dict(stats=summary,by_seed={str(seed):s.summary([e for e in rows if e['seed']==seed]) for seed in sorted(set(e['seed'] for e in rows))},checks=checks,passed=all(checks.values()),comparisons=comparison)
 out=R/'reports/phase4-counterfactual-dev-gate.json';assert not out.exists();out.write_text(json.dumps(dict(results=result,all_task_targets_passed=all(r['passed'] for r in result.values()),teacher_physical_parity_Phase3C=True,input_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),policies_unchanged=True,heldout_started=False),indent=2));print(json.dumps({n:dict(stats=z['stats'],checks=z['checks']) for n,z in result.items()}))
