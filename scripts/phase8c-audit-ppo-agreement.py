"""Once-frozen reconstruction agreement; no selection,refit or duplicate physics."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8'
def key(c):return tuple(c.get(k) for k in ('region','year','source','seed','cap','price_multiplier','subsidy','tax'))
if __name__=='__main__':
 design=json.loads((P/'phase8c-frozen-cases-v3.json').read_text());new={key(c):c for c in design['cases'] if c['policy']=='SensorlessPPO' and c['climate']=='Historical' and 'P1' in c['phase8c_groups']};assert len(new)==198
 oldcases=[c for c in json.loads((P/'phase8b-locked-campaign-cases.json').read_text())['cases'] if c['policy']=='SensorlessPPO'];assert len(oldcases)==198;records=[]
 for c in oldcases:
  a=json.loads((R/'data/phase8-combined-evaluation'/c['episode_id']/'result.json').read_text());cc=new[key(c)];b=json.loads((R/'data/phase8c-supplemental-evaluation'/cc['episode_id']/'result.json').read_text());fields=('stage','as_of','dose','deferred','tier','applicable');ta=[{k:t.get(k) for k in fields} for t in a['trace']];tb=[{k:t.get(k) for k in fields} for t in b['trace']]
  records.append(dict(region=c['region'],year=c['year'],source=c['source'],seed=c['seed'],archived_episode=c['episode_id'],new_episode=cc['episode_id'],decision_action_sequence_exact_match=ta==tb,archived_decisions=len(ta),new_decisions=len(tb),outcome_bit_equal=bool(np.array_equal(a['outcome'],b['outcome'])),max_abs_outcome_difference=float(np.max(np.abs(np.asarray(a['outcome'])-b['outcome'])))))
 audit=json.loads((P/'phase8c-ppo-reconstruction-audit.json').read_text());audit['decision_action_agreement']=dict(status='complete',episodes=198,matching_episodes=sum(r['decision_action_sequence_exact_match'] for r in records),all_decision_action_sequences_exact_match=all(r['decision_action_sequence_exact_match'] for r in records),outcome_bit_equal_episodes=sum(r['outcome_bit_equal'] for r in records),max_abs_outcome_difference=max(r['max_abs_outcome_difference'] for r in records),records=records,source='once-executed matching main-campaign cases;checkpoints frozen before execution',no_extra_physics=True,no_selection_or_refitting_based_on_agreement=True)
 (P/'phase8c-ppo-reconstruction-audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps({k:v for k,v in audit['decision_action_agreement'].items() if k!='records'}))
