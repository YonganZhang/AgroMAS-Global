"""Frozen Full3 Dev screening. No held-out rows accepted, no calibration changes."""
import pathlib,json,hashlib,argparse,statistics
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1]
old=SourceFileLoader('phase3b_statistics',str(R/'scripts/phase3-report.py')).load_module()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',default='reports/phase3b-dev-full3-v3.json');p.add_argument('--output',default='reports/phase3b-full3-dev-gate-v3.json');a=p.parse_args();out=R/a.output;assert not out.exists()
 file=R/a.input;records=json.loads(file.read_text())['records'];rows=[e for r in records for e in r['episodes']];assert len(rows)==4500
 keys=[(r['seed'],r['soil'],r['year']) for r in rows];assert len(set(keys))==4500 and all(5000<=r['year']<=5499 for r in rows)
 inventory={}
 for parent in ['phase3b-runs','phase3b2-runs','phase3b3-runs']:
  for receipt_file in (R/'reports'/parent).glob('*/receipt.json'):
   receipt=json.loads(receipt_file.read_text())
   if receipt.get('status')=='completed':inventory[receipt['checkpoint_sha256']]=receipt
 shas={rec['checkpoint_sha256'] for rec in records};assert len(shas)==3
 assert all(s in inventory and inventory[s]['actual_steps']>=65536 for s in shas)
 trained_steps={inventory[s]['actual_steps'] for s in shas};assert len(trained_steps)==1
 baseline=json.loads((R/'reports/phase3a-final/phase3_metrics.json').read_text())['episodes'];refs={'N2-PA':baseline['N2'],'prior160':baseline['prior'],'prior190':baseline['prior190']}
 fresh=R/'reports/phase3b-dev-controls-v3.json';provenance='Frozen Phase3A controls, unchanged native physics; fresh control reproduction pending'
 if fresh.exists():
  x=json.loads(fresh.read_text())['records'];refs={n:[e for r in x if r['model']==n for e in r['episodes']] for n in refs};assert all(len(v)==1500 for v in refs.values());provenance='Fresh Phase3B controls'
 stats=old.summarize(rows);seeds={str(s):old.summarize([r for r in rows if r['seed']==s]) for s in [4,17,29]};comparisons={n:old.comparison(rows,rs) for n,rs in refs.items()}
 prior=old.summarize(refs['prior190']);competitive=(stats['yield_t_ha']>=prior['yield_t_ha'] or (stats['yield_t_ha']>=prior['yield_t_ha']-.1 and (stats['surplus_kg_ha']<=prior['surplus_kg_ha']-5 or stats['cvar10_surplus']<=prior['cvar10_surplus']-5)))
 checks=dict(noncollapse=all(150<=v['N_kg_ha']<=210 for v in seeds.values()),executed_safe=all(r['executed_violation_rate']==0 for r in rows),competitive_yield_or_environmental_tradeoff=competitive)
 for n,c in comparisons.items():checks['beats_'+n]=c['joint_actual']['ci95'][0]>0 and c['joint_actual']['wilcoxon_year_mean_p']<.05
 candidate_provenance=[dict(tag=inventory[s]['tag'],model=inventory[s]['model'],seed=inventory[s]['seed'],joint_bonus=inventory[s]['candidate_config']['calibration']['joint_bonus'],constraint_mode='raw' if inventory[s]['model']=='raw' else 'corrected',endpoint_cost_mode=inventory[s]['candidate_config']['endpoint_cost_mode'],calibration_sources=[p for p in inventory[s]['source_sha256'] if 'frozen-calibration-' in p]) for s in sorted(shas)]
 result=dict(candidate_provenance=candidate_provenance,actual_training_steps_per_seed=next(iter(trained_steps)),checkpoint_sha256=sorted(shas),dev_gate_passed=all(checks.values()),checks=checks,stats=stats,by_seed=seeds,by_soil={s:old.summarize([r for r in rows if r['soil']==s]) for s in ['default','fast','slow']},comparisons=comparisons,control_provenance=provenance,input_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),heldout_started=False,all_checkpoints_frozen=False)
 out.write_text(json.dumps(result,indent=2));print(json.dumps(result))
