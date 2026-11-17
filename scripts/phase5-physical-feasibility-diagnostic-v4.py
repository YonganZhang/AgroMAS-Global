"""Secondary finite-grid reachability counts; never chooses a test policy."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5'
if __name__=='__main__':
 from pcse_gym.agromas.final_evaluation import validate_external_dependency
 validate_external_dependency(R,P/'final-evaluation-permit-v4.json')
 receipt=json.loads((P/'final-physical-book-receipt-v4.json').read_text());assert receipt['status']=='completed' and receipt['failures']==0
 results=[]
 for file in receipt['files']:
  path=R/file['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==file['sha256'];rows=list(map(json.loads,path.read_text().splitlines()));reachable={}
  for row in rows:
   valid=True
   for stage,dose in enumerate(row['plan'],1):
    state=row['states'].get(str(stage))
    if state is None:
     if dose!=0:valid=False;break
    elif dose>220-state['n_fert_cum']+1e-8:valid=False;break
   if valid:reachable.setdefault(json.dumps(row['events'],sort_keys=True),row)
  first=rows[0];counts={str(cap):sum(.5<=r['outcome'][3]<=.9 and 0<=r['outcome'][2]<=cap for r in reachable.values()) for cap in (25,35,40,50)}
  results.append(dict(region_id=first['region_id'],harvest_year=first['harvest_year'],role=first['role'],climate=first['climate'],
   requested_plan_invocations=len(rows),reachable_distinct_executed_event_sequences=len(reachable),joint_feasible_sequence_counts=counts,
   no_feasible_sequence={cap:count==0 for cap,count in counts.items()}))
 out=P/'final-physical-feasibility-diagnostic-v4.json'
 with out.open('x') as f:json.dump(dict(status='completed',scope='secondarydescriptivefinitecommon-grid/sharedDVSclockonly;notcontinuous/fieldfeasibilityoradeployableoracle',
  no_best_test_policy_selected=True,no_training_or_tuning=True,excludes_unaffordable_requested_doses_and_nonzero_requests_in_absent_stages=True,
  excludes_calendar_N2_and_legacy_action_domains=True,source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),worlds=results),f,indent=2)
 out.chmod(0o444);print(json.dumps(dict(worlds=len(results),best_test_policy_selected=False)),flush=True)
