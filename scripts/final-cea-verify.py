"""Independent complete-case reconciliation; reads frozen episodes, never constructs an env."""
import pathlib,json,hashlib,sys,datetime,statistics
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
from pcse_gym.utils.frozen_audit import sha,exclusive_json
records=SourceFileLoader('final_receipts',str(R/'scripts/phase4-records.py')).load_module();protocol=SourceFileLoader('final_protocol',str(R/'scripts/phase4-protocol.py')).load_module()
def main():
 manifest=protocol.validate_domain_manifest(R,True);claim=json.loads((R/'reports/heldout-audit-claim.json').read_text());assert claim['manifest_sha256']==sha(R/'reports/heldout-unlock-manifest.json');claim_sha=sha(R/'reports/heldout-audit-claim.json')
 expected={(m,seed,soil,y) for m,seed,soil,years,audit in claim['tasks'] for y in years};assert len(expected)==38736 and all(t[-1] for t in claim['tasks'])
 raw=json.loads((R/'reports/phase4-heldout-final.json').read_text());assert raw['status']=='completed';assert raw['evaluator_sha256']==sha(R/'scripts/phase4-frozen-eval.py') and raw['environment_sha256']==sha(R/'scripts/phase4-env.py')
 seen=set();index={};violations={};summary={};history=stress=0
 for rec in raw['records']:
  eventmap={}
  for e in rec['events']:eventmap.setdefault(e['year'],[]).append(e)
  for row in rec['episodes']:
   key=(rec['model'],rec['seed'],rec['soil'],row['year']);assert key not in seen and key in expected;seen.add(key)
   p=R/f'reports/phase4-heldout-episodes/{key[0]}/{key[1]}/{key[2]}/{key[3]}.json';receipt=records.read_episode(p);assert receipt['episode']==row and receipt['events']==eventmap.get(row['year'],[])
   assert receipt['manifest_sha256']==claim['manifest_sha256'] and receipt['checkpoint_sha256']==rec['checkpoint_sha256'] and receipt['task_claim_sha256']==claim_sha
   assert receipt['evaluator_sha256']==raw['evaluator_sha256'] and receipt['environment_sha256']==raw['environment_sha256'] and receipt['calibration_sha256']==raw['calibration_sha256']
   assert row['joint_actual']==(.5<=row['NUE_actual']<=.9 and 0<=row['surplus_actual']<=40)
   dates=[datetime.date.fromisoformat(d) for d in row['actual_application_dates']];gaps=[(b-a).days for a,b in zip(dates,dates[1:])];bad=sum(g<14 for g in gaps);assert bad==row['actual_spacing_violations'];assert row['minimum_actual_spacing_days']==(min(gaps) if gaps else None)
   if key[0] not in ['raw','corrected','N2-PA']:assert bad==0
   violations[key[0]]=violations.get(key[0],0)+bad
   for alias in ['native_NUE','native_surplus_kg_ha','native_joint_satisfied']:assert alias in row
   actual=sum(e['executed']*10 for e in receipt['events']);assert actual==row['actual_N'];assert row['actual_N']>=0
   index[str(p.relative_to(R))]=sha(p);summary.setdefault(key[0],[]).append(row);history+=1983<=row['year']<=2021;stress+=5500<=row['year']<=5998
 assert seen==expected and history==2808 and stress==35928
 physical_files=list((R/'reports/phase4-heldout-episodes').rglob('*.json'));assert len(physical_files)==38736
 output=R/'reports/phase4-episode-sha-index.json';exclusive_json(output,dict(manifest_sha256=claim['manifest_sha256'],episode_count=len(index),files=index))
 report=dict(status='completed',episodes=len(seen),expected_episodes=len(expected),duplicates=0,missing=0,unexpected=0,historical_episodes=history,stress_episodes=stress,sealed_episode_files=len(physical_files),all_receipt_seals_valid=True,all_raw_and_sealed_rows_and_events_equal=True,all_provenance_hashes_match=True,native_metric_aliases_preserved=True,actual_spacing_violations_by_method=violations,manifest_sha256=claim['manifest_sha256'],episode_index_sha256=sha(output),raw_sha256=sha(R/'reports/phase4-heldout-final.json'),method_counts={k:len(v) for k,v in summary.items()},completed_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
 exclusive_json(R/'reports/phase4-final-integrity.json',report);print(json.dumps(report))
if __name__=='__main__':main()
