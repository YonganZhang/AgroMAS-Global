"""Selected-policy TRAIN OOF proxy calibration, not an uncertainty guarantee."""
from pathlib import Path
import json
import numpy as np
from sklearn.model_selection import GroupKFold
from pcse_gym.agromas_v6.books import load_train,FACTORS
from pcse_gym.agromas_v6.core import Policy,select_objective
from pcse_gym.agromas_v6.training import fit_pipeline,table
R=Path(__file__).resolve().parents[1];P=R/'reports/phase6'
if __name__=='__main__':
 active=json.loads((P/'ACTIVE_TRAIN_RUN_V6.json').read_text());p=R/active['reports'];selected=json.loads((p/'policy-train-selection-v6.json').read_text())['selected'];policy=Policy(selected['beta'],selected['penalty']);data=load_train(R);years=np.arange(1995,2010);records=[]
 for fold,(train,val) in enumerate(GroupKFold(5).split(years,groups=years)):
  fit=np.array([i for i,k in enumerate(data.keys) if k[1] in years[train]]);valid=np.array([i for i,k in enumerate(data.keys) if k[1] in years[val]]);models,cache=fit_pipeline(data,fit,policy);ix=np.zeros(len(valid),int);predictions=[]
  for stage in (1,2,3):
   stats,legal=table(data,valid,ix,stage,models[stage],cache);action,diag=select_objective(stats,legal,40.,1.,0.,policy);x,_=data.candidate_inputs(valid,ix,stage);seen=data.available[valid,stage-1,ix];pred=np.zeros((len(valid),32,6));pred[seen]=models[stage](x[np.arange(len(valid)),action][seen]);predictions.append((pred,seen,stats[np.arange(len(valid)),action,8]));ix+=action*FACTORS[stage-1]
  true=data.outcomes[valid,ix];actual_joint=(true[:,3]>=.5)&(true[:,3]<=.9)&(true[:,2]>=0)&(true[:,2]<=40)
  for stage,(pred,seen,prob) in enumerate(predictions,1):
   for i in np.flatnonzero(seen):
    lo,hi=np.quantile(pred[i],[.05,.95],axis=0);records.append(dict(fold=fold,region_id=data.keys[valid[i]][0],year=data.keys[valid[i]][1],climate=data.keys[valid[i]][2],stage=stage,predicted_mean=pred[i].mean(0).tolist(),actual_outcome=true[i].tolist(),proxy_interval_coverage=((true[i]>=lo)&(true[i]<=hi)).tolist(),proxy_interval_width=(hi-lo).tolist(),proxy_joint_fraction=float(prob[i]),actual_joint=bool(actual_joint[i])))
  print(json.dumps(dict(fold=fold,completed=True)),flush=True)
 summary=[]
 for stage in (1,2,3):
  rows=[r for r in records if r['stage']==stage];errors=np.array([r['predicted_mean'] for r in rows])-np.array([r['actual_outcome'] for r in rows]);summary.append(dict(stage=stage,n_policy_contexts=len(rows),RMSE=np.sqrt((errors**2).mean(0)).tolist(),proxy90_interval_coverage=np.mean([r['proxy_interval_coverage'] for r in rows],0).tolist(),mean_proxy90_width=np.mean([r['proxy_interval_width'] for r in rows],0).tolist(),joint_fraction_Brier=float(np.mean([(r['proxy_joint_fraction']-r['actual_joint'])**2 for r in rows]))))
 with (p/'selected-policy-TRAIN-OOF-calibration-v6.json').open('x') as f:json.dump(dict(status='completed',scope='SelectedparameterTRAINselectionCVdiagnostic;notindependentvalidation;pairedtreeproxydoesnotincludefullaleatoricweatheruncertainty',metrics_order=['yield_tDM','grainN','surplus','NUE','fertN','nonfertN'],summary=summary,rows=records),f,indent=2)
