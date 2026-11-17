"""Independent numerical and group-isolation checks for small-sample satellite probes."""
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from pcse_gym.agromas_v7.validation import ridge_map,nested_maps,predict_nested,permutations

def test_ridge_linear_map_matches_independent_sklearn_with_intercept():
    rng=np.random.default_rng(73);x=rng.normal(size=(25,64));x[:,3]=5;y=rng.normal(size=(25,3));train=np.arange(20);test=np.arange(20,25)
    scale=StandardScaler().fit(x[train]);actual=Ridge(alpha=10).fit(scale.transform(x[train]),y[train]).predict(scale.transform(x[test]));expected=ridge_map(x,train,test,10)@y[train]
    np.testing.assert_allclose(actual,expected,rtol=1e-10,atol=1e-10)

def test_nested_selection_matches_independent_full_refits_and_fold_isolation():
    rng=np.random.default_rng(9);x=rng.normal(size=(25,8));y=rng.normal(size=(25,2));groups=np.repeat(np.arange(5),5);alphas=(.1,1,10);maps=nested_maps(x,groups,alphas);actual,_=predict_nested(maps,y);expected=np.empty_like(y)
    for group in np.unique(groups):
        train=np.flatnonzero(groups!=group);test=np.flatnonzero(groups==group);errors=np.zeros((3,2))
        for inner in np.unique(groups[train]):
            fit=train[groups[train]!=inner];valid=train[groups[train]==inner];sc=StandardScaler().fit(x[fit])
            for j,a in enumerate(alphas):errors[j]+=np.mean((Ridge(alpha=a).fit(sc.transform(x[fit]),y[fit]).predict(sc.transform(x[valid]))-y[valid])**2,axis=0)/4
        sc=StandardScaler().fit(x[train])
        for k in range(2):expected[test,k]=Ridge(alpha=alphas[np.argmin(errors[:,k])]).fit(sc.transform(x[train]),y[train,k]).predict(sc.transform(x[test]))
        # Held target changes must never alter its own outer predictions.
        changed=y.copy();changed[test]+=1000;pred,_=predict_nested(maps,changed);np.testing.assert_array_equal(pred[test],actual[test])
    np.testing.assert_allclose(actual,expected,rtol=1e-10,atol=1e-10)

def test_permutation_nulls_keep_the_registered_exchangeability_blocks():
    region=np.repeat(np.arange(5),5);year=np.tile(np.arange(2017,2022),5)
    within=permutations(region,year,100,4,'within_region');assert np.all(region[within]==region[:,None])
    blocks=permutations(region,year,100,4,'region_blocks');assert np.all(year[blocks]==year[:,None])
    for j in range(100):
        assert len(np.unique(blocks[:,j]))==25
        for r in range(5):assert len(np.unique(region[blocks[region==r,j]]))==1

def test_bridge_observables_are_invariant_to_hidden_and_region_telemetry():
    from pcse_gym.agromas_v7.bridge import features,reconstruct,HIDDEN
    a=np.arange(22,dtype=float);b=a.copy();b[list(HIDDEN)]+=1000;b[10:15]+=999
    for regime in ['Weather_only','Static_soil','Satellite_bridge']:
        np.testing.assert_array_equal(features(a,regime,np.ones(4),np.ones(64)),features(b,regime,np.ones(4),np.ones(64)))
    x=reconstruct(a,np.ones(6));y=reconstruct(b,np.ones(6));np.testing.assert_array_equal(x,y)

def test_satellite_lookup_cannot_substitute_current_year_for_missing_prior():
    from pcse_gym.agromas_v7.bridge import prior_year
    import pytest
    a={('site',2017):np.ones(64),('site',2018):np.full(64,2)}
    assert prior_year(a,'site',2017) is None
    np.testing.assert_array_equal(prior_year(a,'site',2018),np.ones(64))
    with pytest.raises(ValueError):prior_year(a,'site',2020)

def test_index_range_reader_keeps_complete_boundary_rows(tmp_path,monkeypatch):
    import importlib.util
    from pathlib import Path
    root=Path(__file__).resolve().parents[3]
    spec=importlib.util.spec_from_file_location('phase7extract',root/'scripts/phase7-extract-alphaearth.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    header=','.join(module.FIELDS)+'\n';row='POINT(0 0),EPSG:32631,s3://x,2020,31N,0,0,81920,81920,0,0,1,1\n';raw=(header+row+row).encode();module.INDEX_SIZE=len(raw)
    monkeypatch.setattr(module,'fetch',lambda url,a,b:raw[a:b+1])
    at=len(header.encode());found=module.lines_at(at,len(row.encode()));assert len(found)==1 and found[0][0]==at
    found=module.lines_at(at+3,len(raw)-at-3);assert len(found)==1 and found[0][0]==at+len(row.encode())
