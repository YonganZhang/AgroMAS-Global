"""Nested retrospective cross-fitting with frozen ranks/L2 and outer purging."""
from pathlib import Path
import json,hashlib
import numpy as np,joblib
from pcse_gym.agromas_v8.prior_adapter import LowRankPriorAdapter
from pcse_gym.agromas_v8.scoring import project_executed_members
R=Path(__file__).resolve().parents[1];D=R/'cache/phase8-p2-adapter-inputs';O=R/'models/phase8-controls/p2-adapters';P=R/'reports/phase8'
VARIANTS={'Full64':('MLP','AE64',4),'Static3':('MLP','Static3',3),'Weather':('Weather','Weather',4),'Linear64':('Linear','AE64',4),'ExtraTrees64':('ExtraTrees','AE64',4)}
def fit(x,y,raw,weights,context,priors,indices,kind,rank):
 return LowRankPriorAdapter(kind,rank,10.).fit(x[indices],y[indices]-raw[indices].mean(1),weights[indices],[context[i] for i in indices],priors=priors)
if __name__=='__main__':
 if O.exists():raise ValueError('Exclusive fit directory already exists')
 O.mkdir(parents=True);metadata=joblib.load(D/'metadata.joblib');x=np.load(D/'x.npy');y=np.load(D/'y.npy');context=metadata['context'];world=np.array(metadata['world']);unique,counts=np.unique(world,return_counts=True);weightmap=dict(zip(unique,1/counts));weights=np.array([weightmap[w] for w in world]);regions=np.array([w.rsplit(':',1)[0] for w in world]);years=np.array([int(w.rsplit(':',1)[1]) for w in world]);receipts=[]
 for scheme,labels in [('LOYO',years),('LORO',regions)]:
  for held in np.unique(labels):
   train=np.flatnonzero(labels!=held);test=np.flatnonzero(labels==held);assert not set(world[train])&set(world[test]);folder=O/f'{scheme}-{held}';folder.mkdir()
   for variant,(family,kind,rank) in VARIANTS.items():
    raw=np.load(D/f'{family}-raw.npy',mmap_mode='r');scores=[];calweights=[];inner=[]
    # Whole inner harvest years are excluded, even inside LORO. No in-sample
    # calibration and no outer held-out labels enter scores or transformations.
    for innerheld in np.unique(years[train]):
     itrain=train[years[train]!=innerheld];ival=train[years[train]==innerheld];assert not set(world[itrain])&set(world[ival]);adapter=fit(x,y,raw,weights,context,metadata['priors'],itrain,kind,rank);delta=adapter.predict(x[ival],[context[i] for i in ival]);members=project_executed_members(raw[ival]+delta[:,None,:],x[ival]);truth=y[ival,2]+3.5-y[ival,1];lo=np.quantile(members[:,:,2],.05,axis=1,method='lower');hi=np.quantile(members[:,:,2],.95,axis=1,method='higher');scores.extend(np.maximum(lo-truth,truth-hi));calweights.extend(weights[ival]);inner.append(dict(held_year=int(innerheld),train_worlds=sorted(set(world[itrain])),validation_worlds=sorted(set(world[ival]))))
    # Site-year-balanced finite-sample conservative weighted conformal score.
    scores=np.asarray(scores);cw=np.asarray(calweights);order=np.argsort(scores);cdf=np.cumsum(cw[order])/cw.sum();level=min(1.,.9+1/(len(set(world[train]))+1));radius=float(scores[order[min(np.searchsorted(cdf,level),len(order)-1)]])
    adapter=fit(x,y,raw,weights,context,metadata['priors'],train,kind,rank);adapter.radius=radius;path=folder/f'{variant}.joblib';joblib.dump(adapter,path,compress=3);path.chmod(0o444)
    receipts.append(dict(scheme=scheme,held=str(held),variant=variant,rank=rank,alpha=10,train_worlds=sorted(set(world[train])),test_worlds=sorted(set(world[test])),inner=inner,radius=radius,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),outer_labels_used=False,backbone_updated=False))
    print(json.dumps({k:receipts[-1][k] for k in ['scheme','held','variant','radius']}),flush=True)
 (P/'phase8b-P2-adapter-training-freeze.json').write_text(json.dumps(dict(fits=receipts,fit_count=len(receipts),outer_schemes_separate=True,prospective_blind_claim=False,hyperparameter_search=False),indent=2))
