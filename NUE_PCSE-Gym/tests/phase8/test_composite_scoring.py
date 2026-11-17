"""Behavioral scoring contracts for the approved Phase8C repair."""
import numpy as np
import pytest
from pcse_gym.agromas_v8.planning import Regime,distribution_metrics,choose_tier,CoreAgronomicAgent


def members(s=20.,nue=.7):
 m=np.zeros((1,32,6));m[...,0]=5.;m[...,2]=s;m[...,3]=nue;m[...,4]=100.
 return m

@pytest.mark.parametrize('soft,bare',[(False,False),(True,False),(True,True)])
def test_composite_reward_and_mean_distance(soft,bare):
 m=members();m[0,16:,2]=60.;m[0,16:,3]=1.2
 d=distribution_metrics(m,[1.],Regime(soft=soft,bare_tier2=bare))
 # mean surplus40, mean NUE .95; half the paired members jointly comply.
 assert d['probability']==.5
 assert d['score']==pytest.approx(d['partial_profit']+125.-37.5)
 assert d['composite_score']==d['score']


def test_archived_bare_profit_and_tier2_action_collapse():
 # Both candidates fail hard tail safety; both satisfy Tier2 mean surplus.
 a=members(nue=1.2);a[...,0]=5.1;a[0,-1,2]=100.
 b=members();b[0,-1,2]=100.
 metrics=[distribution_metrics(x,[1.],Regime(bare_tier2=True)) for x in (a,b)]
 assert all(m['score']==m['partial_profit'] for m in metrics)
 assert choose_tier(metrics,[0.,60.],Regime(bare_tier2=True))==(0,2)
 fixed=[distribution_metrics(x,[1.],Regime()) for x in (a,b)]
 assert choose_tier(fixed,[0.,60.],Regime())==(1,2)

@pytest.mark.parametrize('eco,econ,s,nue,prob,distance',[
 (False,True,100.,.7,1.,0.),(True,False,20.,1.2,1.,0.),
 (False,True,-100.,1.2,0.,.45),(True,False,80.,-1.,0.,2.05),
 (False,False,100.,1.2,1.,0.)])
def test_removed_specialist_terms_are_disabled(eco,econ,s,nue,prob,distance):
 d=distribution_metrics(members(s,nue),[1.],Regime(eco=eco,econ=econ))
 assert d['probability']==0. # Physical audit remains active regardless of removal.
 assert d['active_probability']==prob
 assert d['distance']==pytest.approx(distance)
 assert d['score']==pytest.approx(d['partial_profit']+(250*prob-300*distance if eco or econ else 0))

@pytest.mark.parametrize('mode,regime',[('hard-bare-tier2',Regime(bare_tier2=True)),('tier2-composite',Regime()),('soft',Regime(soft=True))])
def test_direct_core_mode_aliases_match_explicit_regimes(mode,regime):
 plans=np.array([[0.,0.,0.],[0.,0.,60.]])
 tensor=np.stack([members(nue=1.2),members()]);args=(3,plans,tensor,[1.],[0],[0])
 a=CoreAgronomicAgent().choose(*args,mode=mode);b=CoreAgronomicAgent(regime).choose(*args)
 assert a['dose']==b['dose'] and a['tier']==b['tier']
 np.testing.assert_array_equal(a['branch_plan_indices'],b['branch_plan_indices'])
