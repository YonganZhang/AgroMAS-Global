"""One-year Dev controller parity, never a fitting or heldout run."""
import pathlib,json,concurrent.futures,hashlib,argparse
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1];m=SourceFileLoader('parity_frozen_eval',str(R/'scripts/phase4-frozen-eval.py')).load_module()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',default='reports/phase4-controller-parity.json');a=p.parse_args()
 sources={};oldcf=json.loads((R/'reports/phase4-dev-counterfactual.json').read_text())['records'];full=json.loads((R/'reports/phase3c-dev-full4-v4-sm.json').read_text())['records'];sm=json.loads((R/'reports/phase3b3-dev-moisture-controls-audited-v3-sm.json').read_text())['records']
 for name,records,original in [('cf-gru',oldcf,'cf-gru'),('utilityprior',oldcf,'utilityprior'),('full4',full,'full4'),('old_SM-adaptiveprior',sm,'adaptiveprior')]:
  for rec in records:
   if rec['model']!=original:continue
   for e in rec['episodes']:
    if e['year']==5000:sources[(name,rec['seed'],rec['soil'])]=e
 tasks=[(n,s,soil,[5000],False) for n in ['cf-gru','utilityprior','full4','old_SM-adaptiveprior'] for s in ([4,17,29] if n in ['cf-gru','full4'] else [4]) for soil in ['default','fast','slow']]
 results=[]
 with concurrent.futures.ProcessPoolExecutor(max_workers=24) as pool:
  for r in pool.map(m.evaluate,tasks):
   e=r['episodes'][0];ref=sources[(r['model'],r['seed'],r['soil'])]
   for k in ['actual_N','yield_t_ha','NUE_actual','surplus_actual','joint_actual','proposed_violation_rate','executed_violation_rate']:assert e[k]==ref[k],(r['model'],k,e[k],ref[k])
   results.append(dict(model=r['model'],seed=r['seed'],soil=r['soil'],actual_N=e['actual_N'],minimum_actual_spacing_days=e['minimum_actual_spacing_days']))
 out=R/a.output;assert not out.exists();out.write_text(json.dumps(dict(dev_only=True,year=5000,verification_seasons=len(results),all_physical_metrics_exactly_equal=True,results=results,evaluator_sha256=hashlib.sha256((R/'scripts/phase4-frozen-eval.py').read_bytes()).hexdigest(),environment_sha256=hashlib.sha256((R/'scripts/phase4-env.py').read_bytes()).hexdigest(),controller_sha256=hashlib.sha256((R/'scripts/phase4-controller.py').read_bytes()).hexdigest(),verification_script_sha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()),indent=2));print('All24Devcasecontrollerparities exact')
