"""Purged outer folds;anomaly alpha chosen by inner-year predictions only."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np,joblib
from pcse_gym.agromas_v8.prior_adapter import LowRankPriorAdapter
from pcse_gym.agromas_v8.scoring import project_executed_members
from pcse_gym.agromas_v8.planning import weighted_quantile
R=Path(__file__).resolve().parents[1];D=R/'cache/phase8d-p2-adapter-inputs';O=R/'models/phase8d-controls/p2-adapters';P=R/'reports/phase8';VARIANTS={'Full64':('MLP','AE64',4),'Static3':('MLP','Static3',3),'Weather':('Weather','Weather',4),'Linear64':('Linear','AE64',4),'ExtraTrees64':('ExtraTrees','AE64',4)};GRID=(10.,25.,50.,100.,200.)
if __name__=='__main__':
 if O.exists():raise FileExistsError('Preserve fitted adapter version')
 O.mkdir(parents=True);meta=joblib.load(D/'metadata.joblib');x=np.load(D/'x.npy');y=np.load(D/'y.npy');context=meta['context'];world=np.array(meta['world']);regions=np.array([v.rsplit(':',1)[0] for v in world]);years=np.array([int(v.rsplit(':',1)[1]) for v in world]);counts={v:int(np.sum(world==v)) for v in set(world)};weights=np.array([1/counts[v] for v in world]);bw=np.load(D/'weights.npy');fits=[];cache={};predictions={};acceptances={};family_data={}
 for family in set(v[0] for v in VARIANTS.values()):
  points=np.load(D/f'{family}-points.npy',mmap_mode='r');banks=np.load(D/f'{family}-banks.npy',mmap_mode='r');mean=np.sum(points*bw[:,:,None],axis=1);family_data[family]=(points,banks,mean)
 def fit(indices,kind,rank,alpha,family):
  target=y-family_data[family][2]
  return LowRankPriorAdapter(kind,rank,10.,anom_alpha=alpha).fit(x[indices],target[indices],weights[indices],[context[i] for i in indices],priors=meta['priors'])
 def calibrated_scores(adapter,ids,family):
  point,bank,_=family_data[family];delta=adapter.predict(x[ids],[context[i] for i in ids]);raw=(point[ids,:,None,:]+bank[ids,None,:,:]+delta[:,None,None,:]).reshape(len(ids),-1,3);features=np.repeat(x[ids,None,:],15,axis=1).reshape(-1,36);members=project_executed_members(raw.reshape(-1,32,3),features).reshape(len(ids),480,6);scores=[]
  for j,i in enumerate(ids):
   w=np.repeat(bw[i],32)/32;low=weighted_quantile(members[j,:,2],w,.05);up=weighted_quantile(members[j,:,2],w,.95);truth=y[i,2]+3.5-y[i,1];scores.append(max(low-truth,truth-up))
  return scores
 outer=[]
 for held in sorted(set(world)):
  year=int(held.rsplit(':',1)[1]);outer.append(('LOYO',held.replace(':','-'),np.flatnonzero(years!=year),np.flatnonzero(world==held)))
 for region in sorted(set(regions)):outer.append(('LORO',region,np.flatnonzero(regions!=region),np.flatnonzero(regions==region)))
 for scheme,held,train,test in outer:
  folder=O/(scheme+'-'+held);folder.mkdir();signature=tuple(sorted(set(world[train])))
  for variant,(family,kind,rank) in VARIANTS.items():
   key=(signature,variant)
   if key not in cache:
    candidates=GRID if kind=='AE64' else (10.,);trial={};calibration={}
    for alpha in candidates:
     error=total=0.;inner=[];scores=[];calw=[]
     for year in sorted(set(years[train])):
      itrain=train[years[train]!=year];ival=train[years[train]==year];assert not set(world[itrain])&set(world[ival]);adapter=fit(itrain,kind,rank,alpha,family);delta=adapter.predict(x[ival],[context[i] for i in ival]);prediction=family_data[family][2][ival]+delta;error+=float(np.sum(weights[ival]*(prediction[:,1]-y[ival,1])**2));total+=float(weights[ival].sum());inner.append(dict(held_year=int(year),train_worlds=sorted(set(world[itrain])),validation_worlds=sorted(set(world[ival]))))
     trial[alpha]=error/total
    selected=min(candidates,key=lambda a:(trial[a],-a));scores=[];calw=[]
    for year in sorted(set(years[train])):
     itrain=train[years[train]!=year];ival=train[years[train]==year];adapter=fit(itrain,kind,rank,selected,family);scores.extend(calibrated_scores(adapter,ival,family));calw.extend(weights[ival])
    radius=weighted_quantile(scores,calw,min(1.,.9+1/(len(signature)+1)));adapter=fit(train,kind,rank,selected,family);adapter.radius=radius;path=folder/(variant+'.joblib');joblib.dump(adapter,path,compress=3);path.chmod(0o444);cache[key]=(path,adapter,dict(selected_anomaly_alpha=selected,inner_Grain_N_MSE={str(k):v for k,v in trial.items()},inner=inner,radius=radius))
   original,adapter,details=cache[key];path=folder/(variant+'.joblib')
   if path!=original:shutil.copy2(original,path)
   delta,accepted=adapter.correction(x[test],[context[i] for i in test]);predictions.setdefault((scheme,variant),np.empty_like(y))[test]=family_data[family][2][test]+delta;acceptances.setdefault((scheme,variant),np.zeros(len(y),bool))[test]=accepted
   fits.append(dict(scheme=scheme,held=held,variant=variant,train_worlds=list(signature),test_worlds=sorted(set(world[test])),outer_labels_used_for_fit=False,backbone_updated=False,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),path=str(path.relative_to(R)),**details));print(json.dumps(dict(scheme=scheme,held=held,variant=variant,alpha=details['selected_anomaly_alpha'])),flush=True)
 results={}
 for (scheme,variant),pred in predictions.items():
  mse=(pred[:,1]-y[:,1])**2;acc=acceptances[(scheme,variant)];results[scheme+'-'+variant]=dict(Grain_N_MSE_pooled=float(mse.mean()),Grain_N_MSE_world_equal=float(np.average(mse,weights=weights)),prior_acceptance_rows=float(acc.mean()),prior_acceptance_world_equal=float(np.average(acc,weights=weights)));np.savez_compressed(O/(scheme+'-'+variant+'-OOF.npz'),prediction=pred,prior_accepted=acc)
 gate=dict(LOYO_Full64_MSE_lower_than_Static3=results['LOYO-Full64']['Grain_N_MSE_pooled']<results['LOYO-Static3']['Grain_N_MSE_pooled'],LORO_Full64_acceptance_over_50pct=results['LORO-Full64']['prior_acceptance_rows']>.5,LORO_Full64_MSE_not_degraded=results['LORO-Full64']['Grain_N_MSE_pooled']<=results['LORO-Static3']['Grain_N_MSE_pooled'])
 (P/'phase8d-P2-adapter-training-freeze.json').write_text(json.dumps(dict(fits=fits,logical_fold_count=49,logical_fits=len(fits),distinct_training_set_variant_fits=len(cache),outer_schemes_separate=True,LOYO_purges_entire_calendar_year=True,unlabelled_station_history_through_t_minus_1=True,no_outer_label_selection=True,prospective_blind_claim=False,results=results,gates=gate,passed=all(gate.values())),indent=2));print(json.dumps(dict(gates=gate,results=results)),flush=True)
