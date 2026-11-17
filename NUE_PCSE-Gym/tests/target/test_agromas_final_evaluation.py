"""Final evaluator boundary checks independent of expensive final campaign."""
import json
from pathlib import Path
from types import SimpleNamespace
import importlib.util
import numpy as np
import pytest
from pcse_gym.agromas import final_evaluation as f


def test_current_state_engine_rejects_terminal_labels():
    from pcse_gym.agromas.replay import ObservableReplayEngine
    engine=ObservableReplayEngine(dict(as_of='2000-04-01',dvs=.4,lai=2,sm=.3,n_uptake=25))
    assert engine.get_variable('DVS')==.4
    with pytest.raises(ValueError,match='non-observable'):engine.get_variable('TWSO')


def test_final_replay_never_opens_dev_policy_campaign():
    row=dict(region_id='netherlands_lelystad',harvest_year=2010,climate='Historical',role='Dev')
    with pytest.raises(ValueError,match='Dev'):
        f.replay_final_book('.',{(0.,0.,0.):row},zone='standard_40',price_multiplier=1,subsidy=0,beta=200,policy='A4',permit_path=None)


def test_final_replay_fixes_action_before_next_trajectory(monkeypatch):
    monkeypatch.setattr(f,'load_split_manifest',lambda _: {})
    monkeypatch.setattr(f,'authorize_year',lambda *a,**k:None)
    calls=[]
    state=dict(stage=1,n_fert_cum=0)
    def context(root,observed,meta,**kwargs):
        assert observed is state
        assert 'outcome' not in observed
        calls.append('decision')
        safe=SimpleNamespace(predicted_infeasible=False)
        return SimpleNamespace(coordinated_action=lambda:1,eco=SimpleNamespace(filter=lambda *a:safe),
            context=dict(candidate_table=SimpleNamespace(model_id='frozen')),scheduler=SimpleNamespace(cumulative=0),engine=SimpleNamespace(day='current'))
    monkeypatch.setattr(f,'decision_context',context)
    class Book(dict):
        def __getitem__(self,key):
            if key==(10.,0.,0.):assert calls==['decision']
            return super().__getitem__(key)
    base=dict(region_id='netherlands_lelystad',harvest_year=2000,climate='Historical',role='Train',states={},outcome=[1.,20.,-6.5,1.48,10.,3.5],events=[],stock_diagnostics={},native_weekly_steps=40)
    zero=dict(base,states={'1':state});selected=dict(base)
    result=f.replay_final_book('.',Book({(0.,0.,0.):zero,(10.,0.,0.):selected}),zone='standard_40',price_multiplier=1,subsidy=100,beta=200,policy='A4',permit_path=None)
    assert result['plan']==[10.,0.,0.]
    assert result['joint'] is False
    assert result['partial_profit']==185.


def test_fractional_tail_and_exact_small_sample_inference():
    # Root script is a statistical artifact with no side effects on import.
    root=Path(__file__).resolve().parents[3]
    spec=importlib.util.spec_from_file_location('phase5_stats',root/'scripts/phase5-final-statistics.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module.upper_cvar([0,1,2,3,4])==4
    assert module.upper_cvar(np.arange(15))==pytest.approx((14+.5*13)/1.5)
    assert module.signflip_p([1]*5)==.0625
    assert module.signflip_p([0,0,0])==1


@pytest.mark.parametrize('dissimilation,residual',[(.012,0.),(.011,10.)])
def test_native_carbon_flux_units_and_closure(monkeypatch,dissimilation,residual):
    from pcse_gym.agromas import stock_diagnostics as stock
    monkeypatch.setattr(stock,'stock_diagnostics',lambda *a:dict(initial_soil_C_kg_ha=1000.,final_soil_C_kg_ha=900.))
    engine=SimpleNamespace(get_variable=lambda name:{'RCORGAMTT':.002,'RCORGDISTT':dissimilation}[name])
    if residual:
        with pytest.raises(ValueError,match='organicCmassbalance'):f.final_stock_diagnostics(engine,{},[])
    else:
        result=f.final_stock_diagnostics(engine,{},[])
        assert result['native_organic_C_applied_kg_ha']==20.
        assert result['native_organic_C_dissimilation_kg_ha']==120.
        assert result['soil_C_mass_balance_residual_kg_ha']==0.


def test_external_validation_rejects_permit_drift_before_git(tmp_path,monkeypatch):
    path=tmp_path/'permit.json';path.write_text('{}');path.with_suffix('.sha256').write_text('wrong')
    import subprocess
    monkeypatch.setattr(subprocess,'check_output',lambda *a,**k:pytest.fail('Externalcheckbeforepermitintegrity'))
    with pytest.raises(ValueError,match='Finalpermitdrift'):f.validate_external_dependency(tmp_path,path)
