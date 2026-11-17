"""TRAIN-only observable-domain score; an applicability flag, not a safety promise."""
import numpy as np
from sklearn.covariance import LedoitWolf
from pcse_gym.agromas_v8.data import parity_features

class ApplicabilityDomain:
 def __init__(self,track='Sensorless'):self.track=track
 def _observed(self,x):
  # Exclude nominal actions and future scenario descriptors; OOD refers to known
  # field/weather/phenology context, never target future weather or hidden states.
  z=parity_features(x,self.track)
  return np.c_[z[:,:22],z[:,25:27]]
 def fit(self,x):
  z=self._observed(x);self.mean=z.mean(0);sd=z.std(0);self.active=sd>=1e-8;self.sd=np.where(self.active,sd,1.)
  normalized=((z-self.mean)/self.sd)[:,self.active]
  if not normalized.shape[1]:raise ValueError('Empty applicability domain')
  self.cov=LedoitWolf().fit(normalized);score=self.cov.mahalanobis(normalized);self.threshold=float(np.quantile(score,.99,method='higher'));return self
 def score(self,x):
  z=self._observed(x);normalized=((z-self.mean)/self.sd)[:,self.active];score=self.cov.mahalanobis(normalized)
  return score,score<=self.threshold
