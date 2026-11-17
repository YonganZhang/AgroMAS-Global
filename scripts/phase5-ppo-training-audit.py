"""Summarize actual training and convergence evidence without checkpoint selection."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5'
if __name__=='__main__':
 rows=[]
 for mode in ('structured-shared','raw-shared'):
  for seed in (4,17,29):
   d=R/f'models/phase5/ppo-{mode}-seed{seed}-v4';receipt=json.loads((d/'receipt.json').read_text());curve=list(map(json.loads,(d/'training-curves.jsonl').read_text().splitlines()))
   assert receipt['parameters_finite'] and receipt['parameters_L2_change']>0 and receipt['actual_native_weekly_steps']==401408
   # Descriptive fixed final-quarter comparison, never selects checkpoints or extends after test outcomes.
   n=max(1,len(curve)//4);early=curve[-2*n:-n];late=curve[-n:]
   metrics={}
   for key in ('recent_partial_profit','recent_joint','conditional_choice_entropy'):
    if early and key in late[-1]:metrics[key]=dict(penultimate_quarter_mean=float(np.mean([x[key] for x in early])),final_quarter_mean=float(np.mean([x[key] for x in late])))
   rows.append(dict(mode=mode,seed=seed,actual_native_weekly_steps=receipt['actual_native_weekly_steps'],train_seasons=receipt['train_seasons'],
    parameter_count=receipt['parameter_count'],parameters_L2_change=receipt['parameters_L2_change'],elapsed_seconds=receipt['elapsed_seconds'],
    actual_training_steps_per_second=receipt['actual_training_steps_per_second'],conditional_entropy=receipt['conditional_entropy'],
    final_stage_action_histogram=receipt['stage_action_histogram'],quarter_diagnostics=metrics,selected_checkpoint='fixed_final',convergence_certified=False))
 p=P/'PPO-training-audit-v4.json'
 with p.open('x') as f:json.dump(dict(status='completed',runs=rows,total_native_weekly_steps=sum(x['actual_native_weekly_steps'] for x in rows),
  training_budget_rationale='Measuredfullwrappercostpreregistered401408nativeweeklystepsperseed;not67kpartialstagehandicap',
  convergence_scope='Nooptimizationconvergenceprooforoutcome-adaptedextension. Learningcurvesandseedvariationmustremainvisible;fullcontrolleradvantageoverthisfinitePPOimplementationisnotuniversalRLsuperiority.',test_selected_checkpoint=False),f,indent=2)
 print(json.dumps(rows))
