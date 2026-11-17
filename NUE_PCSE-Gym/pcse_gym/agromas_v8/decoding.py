"""Region-aware TRAIN-only physical decoding;not an online observation channel."""
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

def fit_region_heads(features,targets,regions,weights,train,test,alpha=10.):
 pred=np.empty((int(np.sum(test)),targets.shape[1]));test_ids=np.flatnonzero(test)
 for region in sorted(set(regions[test])):
  fit=train&(regions==region);ids=test_ids[regions[test_ids]==region]
  if fit.sum()<2:raise ValueError('Missing outer-training support in a region')
  w=np.asarray(weights[fit],float)
  # Each original world contributes total weight one; preserve world units.
  scale=StandardScaler().fit(features[fit],sample_weight=w);mean=np.average(targets[fit],axis=0,weights=w);sd=np.sqrt(np.maximum(np.average((targets[fit]-mean)**2,axis=0,weights=w),1e-12));head=Ridge(alpha=alpha).fit(scale.transform(features[fit]),(targets[fit]-mean)/sd,sample_weight=w)
  values=np.asarray(head.predict(scale.transform(features[ids]))).reshape(len(ids),targets.shape[1])*sd+mean;pred[np.searchsorted(test_ids,ids)]=values
 return pred


def nested_region_heads(features,targets,regions,years,weights,train,test,
                        alphas=(10.,25.,50.,100.,200.,500.)):
 """Select only readout regularization inside outer TRAIN years.

 Frozen neural features are conditional inputs, not refitted inner-fold models.
 All normalizers and stock targets used for selection exclude outer test rows.
 """
 pred=np.empty((int(np.sum(test)),targets.shape[1]));test_ids=np.flatnonzero(test);audit=[]
 for region in sorted(set(regions[test])):
  fit=train&(regions==region);score=np.zeros(len(alphas));den=0.
  for year in sorted(set(years[fit])):
   inner=fit&(years!=year);val=fit&(years==year)
   w=np.asarray(weights[inner],float);v=np.asarray(weights[val],float)
   scale=StandardScaler().fit(features[inner],sample_weight=w)
   mean=np.average(targets[inner],axis=0,weights=w)
   sd=np.sqrt(np.maximum(np.average((targets[inner]-mean)**2,axis=0,weights=w),1e-12))
   a=scale.transform(features[inner]);b=(targets[inner]-mean)/sd
   # Shared eigensystem exactly solves weighted Ridge for every registered alpha.
   gram=a.T@(w[:,None]*a);rhs=a.T@(w[:,None]*b)
   eig,vec=np.linalg.eigh(gram);eig=np.maximum(eig,0.)
   left=scale.transform(features[val])@vec;right=vec.T@rhs
   truth=(targets[val]-mean)/sd
   for i,alpha in enumerate(alphas):
    diff=left@(right/(eig[:,None]+alpha))-truth
    score[i]+=np.sum(v[:,None]*diff**2)
   den+=v.sum()*targets.shape[1]
  selected=min(range(len(alphas)),key=lambda i:(score[i]/den,-alphas[i]))
  ids=test_ids[regions[test_ids]==region]
  local_test=np.zeros(len(test),bool);local_test[ids]=True
  pred[np.searchsorted(test_ids,ids)]=fit_region_heads(features,targets,regions,weights,fit,local_test,alphas[selected])
  audit.append(dict(region=region,alpha=alphas[selected],inner_years=[int(y) for y in sorted(set(years[fit]))],world_weight_sum=float(weights[fit].sum()),inner_standardized_MSE=(score/den).tolist()))
 return pred,audit
