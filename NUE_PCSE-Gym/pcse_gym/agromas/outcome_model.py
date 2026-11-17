"""TRAIN-only joint outcome regression, calibrated with year-grouped residuals.

This is a statistical teacher surrogate, not an online simulator rollout. Callers
must record how each terminal label was generated under a fixed continuation.
"""
import hashlib,json
import numpy as np
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.model_selection import GroupKFold
from .contracts import finite_array


class TrainOutcomeModel:
    def __init__(self, ensemble_size=32, n_estimators=64, min_samples_leaf=4, seed=4):
        if ensemble_size<2 or n_estimators<2 or min_samples_leaf<2:
            raise ValueError('Invalid preregistered outcome model')
        self.ensemble_size=ensemble_size;self.n_estimators=n_estimators
        self.min_samples_leaf=min_samples_leaf;self.seed=seed
        self.fitted=False

    def _model(self):
        return ExtraTreesRegressor(n_estimators=self.n_estimators,min_samples_leaf=self.min_samples_leaf,
                                   random_state=self.seed,n_jobs=1)

    def fit(self,x,joint_targets,years,allowed_train_years,*,role,continuation_policy_id,label_source_id):
        if role!='Train':raise ValueError('Outcome fitting requires Train')
        x=finite_array(x);y=finite_array(joint_targets);years=np.asarray(years)
        if x.ndim!=2 or y.shape!=(len(x),4) or years.shape!=(len(x),):
            raise ValueError('Expected Y_DM,grain_N,full_Nfert,nonfert_N targets')
        if set(years)-set(allowed_train_years):raise ValueError('Non-Train target years')
        if len(set(years))<3 or not continuation_policy_id or not label_source_id:
            raise ValueError('Three TRAIN years and fixed-label provenance required')
        if np.any(y<0) or np.any(y[:,2]+y[:,3]<=0):raise ValueError('Invalid physical targets')
        residual=np.zeros_like(y)
        self.cv_folds=[]
        for fit,valid in GroupKFold(n_splits=min(5,len(set(years)))).split(x,y,years):
            model=self._model().fit(x[fit],y[fit])
            residual[valid]=y[valid]-model.predict(x[valid])
            self.cv_folds.append(dict(fit_years=sorted(set(years[fit].tolist())),
                                      validation_years=sorted(set(years[valid].tolist()))))
        self.model=self._model().fit(x,y)
        self.residual=finite_array(residual)
        self.continuation_policy_id=continuation_policy_id
        self.label_source_id=label_source_id
        self.train_years=tuple(sorted(set(years.tolist())))
        self.model_id=hashlib.sha256(x.tobytes()+y.tobytes()+json.dumps(dict(seed=self.seed,n_estimators=self.n_estimators,min_samples_leaf=self.min_samples_leaf,ensemble_size=self.ensemble_size,continuation=continuation_policy_id,label_source=label_source_id,train_years=self.train_years),sort_keys=True).encode()).hexdigest()
        self.fitted=True
        return self

    def __call__(self, rows):
        if not self.fitted:raise ValueError('TRAIN model not fitted')
        rows=finite_array(rows)
        mean=self.model.predict(rows)
        # Reproducible common residual members across candidate actions reduce MC comparison noise.
        rng=np.random.default_rng(self.seed)
        idx=rng.integers(len(self.residual),size=self.ensemble_size)
        physical=np.maximum(mean[:,None,:]+self.residual[idx][None,:,:],0)
        if np.any(physical[:,:,2]+physical[:,:,3]<=0):
            raise ValueError('Uncalibrated zero-N prediction; reject, do not manufacture NUE')
        y,grain,fert,nonfert=np.moveaxis(physical,-1,0)
        return np.stack([y,grain,fert+nonfert-grain,grain/(fert+nonfert),fert,nonfert],-1)
