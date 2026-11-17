"""Predeclared Dev-only gate; negative outcome leaves heldout physically locked."""
import pathlib,json,argparse,hashlib,statistics
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1]
stats=SourceFileLoader('c_stats',str(R/'scripts/phase3-report.py')).load_module()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--tag',default='v4-sm-final');p.add_argument('--input',default='reports/phase3c-dev-full4-v4-sm.json');p.add_argument('--output',default='reports/phase3c-dev-gate-v4-sm.json');a=p.parse_args();out=R/a.output;assert not out.exists();src=R/a.input;data=json.loads(src.read_text());rows=[e for rec in data['records'] for e in rec['episodes']]
 assert len(rows)==4500 and len({(r['seed'],r['soil'],r['year']) for r in rows})==4500 and all(5000<=r['year']<=5499 for r in rows)
 refsdata=json.loads((R/'reports/phase3b-dev-controls-v3.json').read_text())['records'];refs={n:[e for rec in refsdata if rec['model']==n for e in rec['episodes']] for n in ['N2-PA','prior160','prior190']}
 fresh=json.loads((R/'reports/phase3c-dev-utilityprior-v4-sm.json').read_text())['records'];refs['utilityprior']=[e for rec in fresh if rec['model']=='utilityprior' for e in rec['episodes']];assert len(refs['utilityprior'])==1500
 oldSM=json.loads((R/'reports/phase3b3-dev-moisture-controls-audited-v3-sm.json').read_text())['records'];refs['old_SM-adaptiveprior']=[e for rec in oldSM if rec['model']=='adaptiveprior' for e in rec['episodes']]
 comparisons={n:stats.comparison(rows,r) for n,r in refs.items()};pooled=stats.summarize(rows);byseed={str(s):stats.summarize([r for r in rows if r['seed']==s]) for s in [4,17,29]};prior=stats.summarize(refs['prior190'])
 dose={};adapt={}
 for seed in [4,17,29]:
  rr=[r for r in rows if r['seed']==seed];counts={str(int(n)):sum(r['actual_N']==n for r in rr) for n in sorted(set(r['actual_N'] for r in rr))};soils={soil:[r['actual_N'] for r in rr if r['soil']==soil] for soil in ['default','fast','slow']};dose[str(seed)]=counts;adapt[str(seed)]=dict(unique_doses=len(counts),by_soil_mean={s:statistics.mean(v) for s,v in soils.items()},by_soil_std={s:statistics.pstdev(v) for s,v in soils.items()})
 checks=dict(noncollapse=all(150<=x['N_kg_ha']<=210 for x in byseed.values()),executed_safe=all(r['executed_violation_rate']==0 for r in rows),genuine_adaptation=all(z['unique_doses']>=2 and max(z['by_soil_std'].values())>0 and max(z['by_soil_mean'].values())>min(z['by_soil_mean'].values()) for z in adapt.values()),competitive_yield=pooled['yield_t_ha']>=prior['yield_t_ha'] or (pooled['yield_t_ha']>=prior['yield_t_ha']-.1 and (pooled['surplus_kg_ha']<=prior['surplus_kg_ha']-5 or pooled['cvar10_surplus']<=prior['cvar10_surplus']-5)),environmental_improvement=pooled['surplus_kg_ha']<prior['surplus_kg_ha'] or pooled['cvar10_surplus']<prior['cvar10_surplus'])
 for n in ['N2-PA','prior160','prior190','utilityprior']:
  c=comparisons[n]['joint_actual'];checks['beats_'+n]=c['ci95'][0]>0 and c['wilcoxon_year_mean_p']<.05
 receipts=[]
 for seed in [4,17,29]:
  f=R/f'reports/phase3c-runs/{a.tag}-full4-seed{seed}';x=json.loads((f/'receipt.json').read_text());assert x['status']=='completed' and x['actual_steps']==67200 and x['zero_step_prior_agreement']==1
  assert hashlib.sha256((f/'model.zip').read_bytes()).hexdigest()==x['checkpoint_sha256'];receipts.append(dict(seed=seed,checkpoint=x['checkpoint_sha256'],source_hashes=x['source_sha256'],active_stats=x['last_training_logger']))
 result=dict(dev_gate_passed=all(checks.values()),checks=checks,stats=pooled,by_seed=byseed,by_soil={s:stats.summarize([r for r in rows if r['soil']==s]) for s in ['default','fast','slow']},dose_counts=dose,adaptation=adapt,comparisons=comparisons,training_receipts=receipts,evaluator_sha256=data['evaluator_sha256'],calibration_sha256=data['calibration_sha256'],input_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),heldout_started=False)
 out.write_text(json.dumps(result,indent=2));print(json.dumps(dict(dev_gate_passed=result['dev_gate_passed'],checks=checks,stats=pooled)))
