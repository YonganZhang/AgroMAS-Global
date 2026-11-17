"""Backward teacher selection must never rank held-year realized future yields."""
from itertools import product
import numpy as np
import pytest
from pcse_gym.agromas.continuation import GRID,dataset,project_members


class ObservableOnlyModel:
    def predict(self,x):
        d=x[:,-1];fert=x[:,3]+d
        return np.array([5-.001*(d-20)**2,.7*(fert+3.5),fert,np.full(len(x),3.5)]).T


def test_future_teacher_uses_fitted_observables_not_realized_yield_oracle():
    book={}
    for plan in product(GRID,repeat=3):
        features={}
        for stage in (1,2,3):
            base=np.zeros(22);base[3]=sum(plan[:stage-1]);base[5]=stage
            features[str(stage)]=base.tolist()
        # Giant realized future yield must NOT control the continuation decision.
        y=1000. if plan[1]==100 else 2.
        n=sum(plan)
        book[plan]=dict(features=features,outcome=[y, .7*(n+3.5),.3*(n+3.5),.7,n,3.5])
    x,y,years,keys=dataset({('synthetic',2000,'Historical'):book},1,
                           {2:ObservableOnlyModel(),3:ObservableOnlyModel()})
    zero=next(i for i,k in enumerate(keys) if k[-1]==(0.,))
    assert y[zero,0]==2.
    assert y[zero,2]==40.  # teacher20+20, not oracle100+anything
    assert set(years)=={2000}


def test_explicit_known_n_floor_keeps_yield_and_soil_stock_driven_nue():
    x=np.zeros((1,23));x[0,3]=70.;x[0,-1]=20.
    p=project_members(np.array([[[5.,200.,0.,999.]]]),x)
    assert p[0,0,0]==5.
    assert p[0,0,4]==90.
    assert p[0,0,5]==3.5
    assert p[0,0,3]>1  # Never manufacture compliance by clippingNUE.
    x[0,-1]=200.
    with pytest.raises(ValueError,match='budget'):project_members(np.ones((1,1,4)),x)


def test_fitted_feature_mask_does_not_change_known_committed_n():
    from pcse_gym.agromas.continuation import predict_physical
    class MaskSpy:
        agromas_feature_mask=(6,7,8,9)
        def predict(self,x):
            assert np.all(x[:,6:10]==0)
            assert x[0,3]==70 and x[0,-1]==20
            return np.ones((len(x),4))
    x=np.ones((1,23));x[0,3]=70;x[0,-1]=20
    assert predict_physical(MaskSpy(),x).shape==(1,4)
    assert np.all(x[:,6:10]==1)  # no caller-state mutation
