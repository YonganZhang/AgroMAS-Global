"""Actual regional weekly rollout with explicitly synthetic outcome predictor stub."""
from pathlib import Path
import numpy as np
import pytest
from pcse_gym.agromas import runtime
R=Path(__file__).resolve().parents[3]


class SyntheticOutcomeStub:
    model_id='synthetic-outcome-test-only'
    def __call__(self,x):
        f=x[:,3]+x[:,-1];g=.7*(f+3.5)
        m=np.c_[np.full(len(x),5.),g,f+3.5-g,np.full(len(x),.7),f,np.full(len(x),3.5)]
        return np.repeat(m[:,None,:],32,axis=1)


def test_actual_weekly_regional_adapter_and_basal_fullseason_ledger(monkeypatch):
    monkeypatch.setattr(runtime,'outcome_model',lambda root,stage:SyntheticOutcomeStub())
    e=runtime.RegionalWeeklyEnv(str(R),beta=200,role='Train',evaluation=dict(
        region_id='china_ncp_luancheng',year=2000,climate='Historical',zone='standard_40',
        price_multiplier=1.,subsidy=0.))
    obs,info=e.reset(seed=4)
    assert obs.shape==(90,) and np.isfinite(obs).all()
    assert info['initial_base_n']==171. and e.scheduler.cumulative==171.
    done=False
    for _ in range(60):
        action=e.coordinated_action()
        assert e.action_masks()[action]
        obs,reward,done,truncated,info=e.step(action)
        assert np.isfinite(obs).all()
        if done:break
    assert done and not truncated and np.isfinite(reward)
    assert 171<=info['outcome'][4]<=220
    diagnostic=info['stock_diagnostics']
    assert diagnostic['native_NUE']==info['outcome'][3]
    assert abs(diagnostic['soil_N_mass_balance_residual_kg_ha'])<1.
    assert diagnostic['native_fertilizer_N_kg_ha']==pytest.approx(info['outcome'][4])
    assert sum(x['dose'] for x in info['stage_events'])+171==pytest.approx(info['outcome'][4])


def test_raw_shared_encoder_retains_same_causal_controls_and_budget(monkeypatch):
    monkeypatch.setattr(runtime,'outcome_model',lambda root,stage:SyntheticOutcomeStub())
    e=runtime.RegionalWeeklyEnv(str(R),beta=200,role='Train',information_mode='raw-shared',evaluation=dict(
        region_id='netherlands_lelystad',year=2000,climate='Historical',zone='standard_40',
        price_multiplier=1.,subsidy=0.))
    obs,info=e.reset(seed=4)
    assert obs.shape==(76,) and np.isfinite(obs).all()
    assert e.config.dose_grid==runtime.GRID and e.config.budget==220
    assert e.action_masks().sum()==1  # No decision at sowing.


def test_structured_ppo_observes_exact_objective_joint_probabilities(monkeypatch):
    from pcse_gym.agromas.contracts import compliance
    class Heterogeneous(SyntheticOutcomeStub):
        def __call__(self,x):
            m=super().__call__(x)
            for i in range(len(x)):
                if x[i,-1]==10:
                    nue=np.tile([.4,1.0],16)  # same mean.7,zerojointprobability
                    inputs=m[i,:,4]+m[i,:,5]
                    m[i,:,1]=nue*inputs;m[i,:,3]=nue;m[i,:,2]=inputs-m[i,:,1]
            return m
    monkeypatch.setattr(runtime,'outcome_model',lambda root,stage:Heterogeneous())
    e=runtime.RegionalWeeklyEnv(str(R),beta=200,role='Train',evaluation=dict(
        region_id='netherlands_lelystad',year=2000,climate='Historical',zone='standard_40',
        price_multiplier=1.,subsidy=0.))
    obs,_=e.reset(seed=4)
    while e.context['candidate_table'].model_id=='no-stage-placeholder':
        obs,_,done,_,_=e.step(0)
        assert not done
    stats=obs[27:27+7*8].reshape(7,8)
    expected=compliance(e.context['candidate_table'].members,e.eco.cap).mean(1)
    assert np.allclose(stats[:,-1],expected)
    assert stats[0,-1]==1 and stats[1,-1]==0
    assert stats[0,4]==stats[1,4]  # meanNUEalonecannotrecoverprobJoint
