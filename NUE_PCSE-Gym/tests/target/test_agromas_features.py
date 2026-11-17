"""Shared encoder uses actual earlyTRAIN-fitted climate models, never future truth."""
from pathlib import Path
from datetime import date
import numpy as np
import pytest
from pcse_gym.agromas.features import shared_features,forecast_model
from pcse_gym.agromas.regions import REGIONS
R=Path(__file__).resolve().parents[3]


def test_actual_frozen_forecasts_and_shared_numeric_schema():
    for name in REGIONS:
        state=dict(as_of=date(2000,6,1),region_id=name,dvs=.6,lai=3.,sm=.3,n_fert_cum=20.,n_uptake=30.,stage=2)
        x=shared_features(str(R),state)
        assert x.shape==(22,)
        assert np.isfinite(x).all()
        assert sum(x[10:15])==1.
        assert np.array_equal(x[:6],[.6,3.,.3,20.,30.,2.])
        model=forecast_model(str(R),name)
        assert model.fitted and model.region_id==name
        with pytest.raises(ValueError,match='causal'):
            shared_features(str(R),state,forecast_mode='perfect')
