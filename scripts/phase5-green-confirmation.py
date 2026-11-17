"""Confirm TRAIN-chosen subsidy levels without any final-set reselection."""
from pathlib import Path
import json,hashlib
from pcse_gym.agromas.final_evaluation import validate_external_dependency
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5'
if __name__=='__main__':
 permit=P/'final-evaluation-permit-v4.json';validate_external_dependency(R,permit)
 receipt=json.loads((P/'final-policy-evaluation-receipt-v4.json').read_text());assert receipt['permit_sha256']==hashlib.sha256(permit.read_bytes()).hexdigest()
 d=pd.read_csv(P/'final-annual-seed-averaged-metrics-v4.csv');train=json.loads((P/'green-subsidy-TRAIN-freeze-v3.json').read_text());rows=[]
 for group in train['groups']:
  for role in ('Held-Out','Public-Reused-Benchmark'):
   q=d[(d.region_id==group['region_id'])&(d.climate==group['climate'])&(d.zone==group['zone'])&(d.price_multiplier==group['price_multiplier'])&(d.role==role)]
   if q.empty:continue
   sigma=group['confirmation_subsidy'];a=q[(q.arm=='A4')&(q.subsidy==sigma)].sort_values('harvest_year');reference='N2-PA-calendar' if group['region_id']=='netherlands_lelystad' else 'DVS-N2';b=q[(q.arm==reference)&(q.subsidy==0)].sort_values('harvest_year')
   assert np.array_equal(a.harvest_year.values,b.harvest_year.values)
   delta=a.partial_profit.to_numpy()-b.partial_profit.to_numpy();ix=np.random.default_rng(20261115).integers(0,len(a),size=(5000,len(a)))
   confirmed=bool(delta.mean()>=0 and (a.joint==1).all())
   rows.append(dict(region_id=group['region_id'],climate=group['climate'],zone=group['zone'],price_multiplier=group['price_multiplier'],role=role,
    selected_subsidy=group['selected_subsidy'],evaluated_subsidy=sigma,train_status=group['status'],confirmatory=group['selected_subsidy'] is not None,
    independent_years=len(a),paired_mean_partial_profit_difference=float(delta.mean()),CI95=np.quantile(delta[ix].mean(1),[.025,.975]).tolist(),
    actual_surplus_violation_years=int((a.surplus_upper_compliant<1).sum()),joint_violation_years=int((a.joint<1).sum()),reference_policy=reference,mean_joint=float(a.joint.mean()),
    final_criterion_met=confirmed if group['selected_subsidy'] is not None else None,
    interpretation='TRAIN-frozen discrete bracket confirmation' if group['selected_subsidy'] is not None else 'TRAIN no-solution retained; sigma0 descriptive fallback only'))
 p=P/'final-green-subsidy-confirmation-v4.json'
 with p.open('x') as f:json.dump(dict(status='completed',final_selection=False,rows=rows),f,indent=2)
 p.chmod(0o444);validate_external_dependency(R,permit)
 print(json.dumps(dict(confirmatory_groups=sum(x['confirmatory'] and x['role']=='Held-Out' for x in rows),confirmed_groups=sum(x['final_criterion_met'] is True and x['role']=='Held-Out' for x in rows))))
