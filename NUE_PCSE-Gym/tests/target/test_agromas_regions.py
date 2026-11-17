"""Date-only split and actual cached source verification; never simulate Held-Out."""
from pathlib import Path
from datetime import date
import json
import numpy as np
import pytest
from pcse_gym.agromas.regions import REGIONS,sha256,load_split_manifest,authorize_year,metadata_partition
from pcse_gym.agromas.weather import VerifiedNASAWeather
R=Path(__file__).resolve().parents[3]


def metadata(name):
    receipt=next((R/'data/global_regions'/name).glob('*.receipt.json'))
    meta=json.loads(receipt.read_text())
    raw=receipt.with_name(receipt.name.replace('.receipt.json','.json'))
    return raw,meta


def test_real_five_region_cache_sha_units_and_train_weather():
    manifest=load_split_manifest(R/'reports/phase5/global-date-split-manifest.json')
    for name,region in REGIONS.items():
        raw,meta=metadata(name)
        assert sha256(raw)==meta['sha256']
        assert not raw.stat().st_mode&0o222
        w=VerifiedNASAWeather(raw,meta['sha256'],name)
        day=date(2000,6,1)  # TRAIN for every region, including SH
        assert np.isfinite([w(day).IRRAD,w(day).ET0,w(day).RAIN]).all()
        assert w(day).IRRAD==pytest.approx(w.parameters['ALLSKY_SFC_SW_DWN']['20000601']*1e6)
        assert w(day).RAIN==pytest.approx(w.parameters['PRECTOTCORR']['20000601']/10)
        assert metadata_partition(region,meta)==manifest['regions'][name]
        with pytest.raises(ValueError,match='Future'):w.history(day,date(2000,6,2),as_of=day)


def test_temporal_roles_are_disjoint_and_nl_confirmatory_is_post2021():
    m=load_split_manifest(R/'reports/phase5/global-date-split-manifest.json')
    for name,v in m['regions'].items():
        roles=[set(y) for y in v['roles'].values()]
        assert sum(map(len,roles))==len(set.union(*roles))
        assert max(v['roles']['Train'])<min(v['roles']['Dev'])
        assert max(v['roles']['Dev'])<min(v['roles']['Held-Out'])
        authorize_year(m,name,2000,'Train')
        with pytest.raises(ValueError,match='requested role'):authorize_year(m,name,2000,'Dev')
        with pytest.raises(ValueError,match='locked'):authorize_year(m,name,v['roles']['Held-Out'][0],'Held-Out')
    assert m['regions']['netherlands_lelystad']['roles']['Held-Out']==[2022,2023,2024,2025,2026]
    assert REGIONS['australia_wa_perth'].crop_dates(2000)[0].year==2000
    assert REGIONS['china_ncp_luancheng'].crop_dates(2000)[0].year==1999


def test_single_invalid_kansas_date_never_imputed():
    raw,meta=metadata('usa_kansas_wichita')
    assert meta['validation']['invalid_dates']==['20260907']
    w=VerifiedNASAWeather(raw,meta['sha256'],'usa_kansas_wichita')
    with pytest.raises(ValueError,match='Missing verified'):w(date(2026,9,7))


def test_published_soil_transfer_units_curves_and_provenance():
    from pcse_gym.agromas.soil import derive_soil,published_ptf
    ptf=published_ptf(1.3,20,40,40,1,7,20,True)
    assert ptf['theta_saturated']==pytest.approx(.8308-.28217*1.3+.0002728*20+.000187*40)
    assert ptf['ksat_cm_day']==pytest.approx(10**(.4022+.26122*7+.44565-.02329*20-.01265*40-.01038*20))
    for name in REGIONS:
        raw=R/'data/global_regions'/name/'soilgrids-ptf-source.json'
        rec=json.loads(raw.with_suffix('.receipt.json').read_text())
        soil,provenance=derive_soil(raw,rec['sha256'])
        assert provenance['source_sha256']==sha256(raw)
        assert sum(x['Thickness'] for x in soil['SoilProfileDescription']['SoilLayers'])==125
        assert len(provenance['layers'])==7
        for layer in soil['SoilProfileDescription']['SoilLayers']:
            theta=np.array(layer['SMfromPF'])[1::2]
            assert ((theta>0)&(theta<1)).all() and (np.diff(theta)<0).all()


def test_native_water_capacity_units_and_clipped_layer_allocation():
    from pcse_gym.agromas.initialization import water_initialization
    for name in REGIONS:
        soil=json.loads((R/'reports/phase5/regional-model-inputs'/name/'soil-v1.json').read_text())
        init=water_initialization(soil,target='field_capacity',fraction=1.)
        dz=np.array([x['Thickness'] for x in soil['SoilProfileDescription']['SoilLayers']])
        wp=np.array(init['wilting_point']);fc=np.array(init['field_capacity']);sm=np.array(init['predicted_initial_SM'])
        assert init['WAV_cm']==pytest.approx(np.dot(fc-wp,dz))
        assert np.dot(sm-wp,dz)==pytest.approx(init['WAV_cm'])
        saturated=water_initialization(soil,target='native_available_capacity',fraction=1.)
        assert saturated['LOWRED']==1.
        assert np.all(np.array(saturated['predicted_initial_SM'])<=np.array(saturated['saturation'])+1e-12)
    with pytest.raises(ValueError):water_initialization(soil,fraction=1.1)


def test_v2_actual_nasa_mean_temperature_is_used_with_separate_provenance():
    for name in REGIONS:
        raw,meta=metadata(name)
        extra=R/'data/global_regions'/name/'nasa-t2m-19840101-20261101-v2.json'
        extra_meta=json.loads(extra.with_suffix('.receipt.json').read_text())
        w=VerifiedNASAWeather(raw,meta['sha256'],name,mean_temperature_path=extra,
                              mean_temperature_sha256=extra_meta['sha256'])
        value=json.loads(extra.read_text())['properties']['parameter']['T2M']['20000601']
        assert w(date(2000,6,1)).TEMP==value
        assert w.source_id!=meta['sha256']
        assert not extra.stat().st_mode&0o222


def test_v2_native_total_som_basal_budget_and_roles():
    from pcse_gym.agromas.season import build_season,run_fixed_plan
    from pcse_gym.agromas.scheduler import ThreeStageScheduler
    import yaml
    native=yaml.safe_load((R/'NUE_PCSE-Gym/pcse_gym/envs/configs/soil/arminda_soil.yaml').read_text())
    engine,meta=build_season(str(R),'netherlands_lelystad',2000,version='v2')
    layers=engine.parameterprovider['SoilProfileDescription']['SoilLayers']
    assert [x['FSOMI'] for x in layers]==[x['FSOMI'] for x in native['SoilProfileDescription']['SoilLayers']]
    assert engine.parameterprovider['A0SOM']==24.
    assert engine.parameterprovider['SSMAX']==5.
    assert meta['version']=='v2'
    row=run_fixed_plan(str(R),'china_ncp_luancheng',2000,[0,0,0],version='v2')
    assert row['initial_base_n']==171.
    assert row['outcome'][4]==171.
    assert row['outcome'][0]>=0
    e,meta=build_season(str(R),'china_ncp_luancheng',2000,version='v2')
    # Physical basal application and ledger must agree, not just metadata.
    e.run(days=1,action=0)  # Integrate the sow-day basal rates.
    assert e.get_variable('RNH4AMTT')+e.get_variable('RNO3AMTT')==pytest.approx(.0171)
    for name,region in REGIONS.items():
        with pytest.raises(ValueError,match='locked'):
            build_season(str(R),name,2025,role='Held-Out',version='v2')
    with pytest.raises(ValueError,match='Unregistered'):
        build_season(str(R),'netherlands_lelystad',2000,version='v2',cultivar='invented')


def test_frozen_asset_digest_invalidates_even_when_mtime_is_restored(tmp_path):
    import os
    from pcse_gym.agromas.regions import frozen_asset_sha
    p=tmp_path/'weight.bin';p.write_bytes(b'aaa');before=p.stat()
    first=frozen_asset_sha(p)
    p.write_bytes(b'bbb');os.utime(p,ns=(before.st_atime_ns,before.st_mtime_ns))
    assert frozen_asset_sha(p)==sha256(p) and frozen_asset_sha(p)!=first


def test_explicit_oracle_cannot_open_locked_or_wrong_role_year():
    from pcse_gym.agromas.oracle import oracle_vector
    with pytest.raises(ValueError,match='locked'):
        oracle_vector(str(R),'netherlands_lelystad',date(2025,4,1),'Historical',role='Held-Out',harvest_year=2025)
    with pytest.raises(ValueError,match='requested role'):
        oracle_vector(str(R),'netherlands_lelystad',date(2015,4,1),'Historical',role='Train',harvest_year=2015)


def test_native_evaporative_transport_probe_is_not_published_bottom_leaching():
    from types import SimpleNamespace
    from pcse.soil.snomin import SNOMIN
    layers=[SimpleNamespace(Thickness_m=.2) for _ in range(7)]
    flow=np.zeros(8);flow[0]=-.001;nitrate=np.zeros(7);nitrate[0]=.01
    incoming,outgoing=SNOMIN.SoilInorganicNModel.SoilNNitrateModel().calculate_NO3_flow_rates(layers,flow,nitrate,np.full(7,.3))
    assert (outgoing-incoming).sum()*1e4==pytest.approx(5/3)
    assert outgoing[-1]==0
