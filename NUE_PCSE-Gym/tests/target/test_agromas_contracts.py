"""Synthetic arithmetic/interface fixtures, never regional weather or efficacy evidence."""
from datetime import date,timedelta
import numpy as np
import pytest
from pcse_gym.agromas import (CandidateTable,FieldState,ThreeStageScheduler,ClimateForecastAgent,
    WeatherHistory,UrbanEcoSafetyAgent,EconomicPolicy,SocioEconomicPolicyAgent,
    CoreAgronomicAgent,AgroMASGlobalCoordinator,upper_cvar)
from pcse_gym.agromas.core_agronomic_agent import select_objective


def table(doses=(0,20,40),grain=((60,60),(80,80),(100,100)),fert=((80,80),(100,100),(120,120))):
    grain=np.array(grain,dtype=float);fert=np.array(fert,dtype=float)
    nonfert=np.full_like(fert,10)
    y=np.full_like(fert,5)
    return CandidateTable(np.array(doses),np.stack([y,grain,fert+nonfert-grain,
        grain/(fert+nonfert),fert,nonfert],-1),date(2001,3,1),'fixture','train-continued',np.zeros(4),'train-model')


def test_member_accounting_full_season_not_current_dose():
    t=table();p=SocioEconomicPolicyAgent(EconomicPolicy(2,.2,100,3,.14)).price(t,40)
    assert p['member_profit'][1,0]==pytest.approx(1000*.2*5/.86-2*100+100)
    with pytest.raises(ValueError,match='mass balance'):
        m=t.members.copy();m[:,:,4]+=1
        CandidateTable(t.doses,m,t.as_of,t.region_id,t.continuation_policy_id,t.climate_vector,t.model_id)
    with pytest.raises(ValueError):t.members[0,0,0]=999


def test_nonlinear_subsidy_applied_per_member_not_at_mean():
    # Both have mean NUE .6, but first mixed member has only50% compliance.
    t=table((0,10),((40,80),(60,60)),((90,90),(90,90)))
    out=SocioEconomicPolicyAgent(EconomicPolicy(0,0,100)).price(t,100)
    assert np.array_equal(out['expected_profit'],[50,100])


def test_upper_tail_fractional_discrete_mass():
    assert upper_cvar([0,10,20,30],.3)==pytest.approx((30+.2*20)/1.2)
    assert upper_cvar([0,10,100],.1)==100
    assert upper_cvar([0,10,20],1)==10


def test_eco_noncontiguous_filter_and_honest_empty_fallback():
    t=table(grain=((80,80),(40,40),(110,110)))
    eco=UrbanEcoSafetyAgent()
    safe=eco.filter(t,50,50)
    assert safe.safe_doses==(0.,40.)
    out=AgroMASGlobalCoordinator(eco,SocioEconomicPolicyAgent(EconomicPolicy(1,.2))).choose(t,50,50)
    assert out.dose in (0,40)
    t=table(grain=((0,0),(0,0),(0,0)))
    assert AgroMASGlobalCoordinator(eco,SocioEconomicPolicyAgent(EconomicPolicy(1,.2))).choose(t,50,50).predicted_infeasible


def test_shared_objective_matches_modular_and_price_changes_dose():
    t=table();eco=UrbanEcoSafetyAgent();agent=SocioEconomicPolicyAgent(EconomicPolicy(1,.2))
    s=eco.filter(t,50,50).table
    modular=AgroMASGlobalCoordinator(eco,agent,beta=50,eta=2).choose(t,50,50)
    assert modular==select_objective(s,agent.price(s,eco.cap),eco.cap,50,2)
    # An actual arithmetic fixture responds to marginal grain price, without claiming field effect.
    m=t.members.copy();m[:,:,0]=[[4,4],[5,5],[6,6]]
    t=CandidateTable(t.doses,m,t.as_of,t.region_id,t.continuation_policy_id,t.climate_vector,t.model_id)
    a=AgroMASGlobalCoordinator(eco,SocioEconomicPolicyAgent(EconomicPolicy(100,.1))).choose(t,50,50)
    b=AgroMASGlobalCoordinator(eco,SocioEconomicPolicyAgent(EconomicPolicy(.1,1))).choose(t,50,50)
    assert a.dose==0 and b.dose==40


def test_scheduler_skips_jumps_and_checks_actual_dates_and_positive_cooldown():
    s=ThreeStageScheduler(210,10);d=date(2001,3,1)
    assert s.eligible(d,.92)==3
    assert s.completed=={0,1}
    assert s.execute(d,.92,30)==30
    assert s.cumulative==40
    assert s.execute(d+timedelta(days=1),.95,30)==0
    s.reset()
    assert s.execute(d,.4,0)==0
    assert s.eligible(d+timedelta(days=1),.7)==2  # zero does not trigger cooling
    assert s.execute(d+timedelta(days=1),.7,30)==30
    assert s.eligible(d+timedelta(days=7),.95) is None
    assert s.eligible(d+timedelta(days=15),1.01) is None
    assert 2 in s.completed
    assert s.cumulative==40
    with pytest.raises(ValueError):s.execute(d,.3,0)


def test_scheduler_all_three_doses_free_and_base_once():
    s=ThreeStageScheduler(195,15);d=date(2001,3,1)
    for i,(dvs,dose) in enumerate([(.4,20),(.7,50),(.95,70)]):
        assert s.execute(d+timedelta(days=14*i),dvs,dose)==dose
    assert s.cumulative==155
    assert [e['dose'] for e in s.events]==[20,50,70]
    s.reset()
    with pytest.raises(ValueError,match='budget'):s.execute(d,.4,190)


@pytest.fixture(scope='module')
def weather_fixture():
    n=365*4+1;dates=tuple(date(2000,1,1)+timedelta(days=i) for i in range(n))
    t=np.arange(n);rng=np.random.default_rng(17)
    temp=10+8*np.sin(t/365*2*np.pi)+rng.normal(0,1,n)
    v=np.column_stack([temp-3,temp+3,10+3*np.sin(t/365*2*np.pi),rng.exponential(2,n),
                       np.full(n,60),np.full(n,3)])
    h=WeatherHistory(dates,v,'unit-fixture','synthetic-test-only')
    train=h.through(date(2002,12,31))
    return h,ClimateForecastAgent(16).fit(train,train.dates)


def test_causal_forecast_future_truth_invariance_and_bounds(weather_fixture):
    history,agent=weather_fixture;as_of=date(2003,3,1)
    a=agent.forecast(history,as_of,seed=4)
    v=history.values.copy();v[np.array([d>as_of for d in history.dates]),:2]+=100
    changed=WeatherHistory(history.dates,v,history.region_id,history.source_id)
    b=agent.forecast(changed,as_of,seed=4)
    assert np.array_equal(a.members,b.members)
    assert a.members.shape==(16,14,6) and a.vector.shape==(4,)
    assert a.issued_at==as_of and min(a.valid_dates)>as_of
    assert ((a.vector[[0,1,3]]>=0)&(a.vector[[0,1,3]]<=1)).all()
    with pytest.raises(ValueError,match='Future'):history.observed(as_of+timedelta(days=1),as_of)
    with pytest.raises(ValueError,match='forbidden'):agent.forecast(history,as_of,oracle_truth=history)
    oracle=agent.forecast(history,as_of,mode='perfect',oracle_truth=history)
    assert np.array_equal(oracle.members[0],history.values[history.dates.index(as_of)+1:history.dates.index(as_of)+15])


def test_fit_rejects_dev_and_nontrain_rows(weather_fixture):
    h,_=weather_fixture
    with pytest.raises(ValueError,match='Train'):ClimateForecastAgent().fit(h,h.dates,role='Dev')
    with pytest.raises(ValueError,match='Non-Train'):ClimateForecastAgent().fit(h,h.dates[:-1])


def test_core_only_passes_explicit_observable_vector():
    expected=table();seen=[]
    def predictor(rows):
        seen.append(rows.copy());return expected.members
    core=CoreAgronomicAgent(predictor,'train-model','train-continued')
    state=FieldState(date(2001,3,1),'fixture',.4,2,.3,20,10,1)
    actual=core.candidates(state,expected.doses,np.zeros(4),[1,2])
    assert actual.members.shape==(3,2,6)
    assert seen[0].shape==(3,13)
    assert np.array_equal(seen[0][:,-1],expected.doses)


def test_scheduler_pending_stage_cannot_apply_in_different_window():
    s=ThreeStageScheduler(210);d=date(2001,3,1)
    assert s.execute(d,.7,20,expected_stage=1)==0
    assert s.cumulative==0 and 1 not in s.completed
    assert s.execute(d,.7,20,expected_stage=2)==20
    assert s.eligible(d+timedelta(days=14),-.1) is None


def test_actual_wofost81_co2_and_recomputed_evapotranspiration():
    import importlib.util
    from pathlib import Path
    from pcse_gym.agromas.physiology import ScenarioWeather
    root=Path(__file__).resolve().parents[3]
    spec=importlib.util.spec_from_file_location('phase5_co2_test',root/'scripts/phase5-co2-probe.py')
    probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
    low=probe.run(380);high=probe.run(550)
    assert low['et_module']==high['et_module']=='EvapotranspirationCO2Layered'
    assert high['TAGP']!=pytest.approx(low['TAGP'],abs=1e-3)
    assert high['CTRAT']!=pytest.approx(low['CTRAT'],abs=1e-5)
    source=probe.get_random_weather_provider((52.57,5.63));day=date(3002,5,1)
    base=source(day)
    shifted=ScenarioWeather(source,3.5,1.,1.1,angstrom=(.18,.55))(day)
    assert shifted.TMAX==pytest.approx(base.TMAX+3.5)
    assert shifted.IRRAD==pytest.approx(base.IRRAD*1.1)
    assert shifted.ET0!=pytest.approx(base.ET0,abs=1e-8)
    assert source(day).TMAX==base.TMAX  # raw weather immutable


def test_weekly_wrapper_actual_guard_shared_masks_terminal_units():
    from pcse_gym.agromas.baseline import WofostWeeklyEnv,SharedControlConfig
    class EngineFixture:
        # Synthetic engine test double, not a physical/crop trajectory claim.
        def __init__(self):self.day=date(2001,3,1);self.dvs=.4;self.terminated=False
        def get_variable(self,name):return self.dvs
        def run(self,days,action):
            self.day+=timedelta(days=days)
            self._guard_executed_action=self._action_guard(action,self.dvs,self.day)
            self.dvs+=.3*days/7
            self.terminated=self.dvs>1.1
    def factory(rng,options):return EngineFixture(),dict(split='Train',fixture=True)
    def encode(e,s):
        t=table();t=CandidateTable(t.doses,t.members,e.day,t.region_id,t.continuation_policy_id,t.climate_vector,t.model_id)
        return dict(observation=[e.dvs,s.cumulative],candidate_table=t,agronomic_upper=50)
    def terminal(e,s):
        f=s.cumulative;n=10.;g=.7*(f+n)
        return [5,g,f+n-g,.7,f,n]
    config=SharedControlConfig((0,20,40),210,0,('DVS','Nfert'),'structured-shared','fixture')
    env=WofostWeeklyEnv(factory,encode,terminal,UrbanEcoSafetyAgent(),
                        SocioEconomicPolicyAgent(EconomicPolicy(1,.2)),config)
    obs,info=env.reset(seed=4)
    assert env.action_masks().tolist()==[True,True,True]
    _,reward,done,_,_=env.step(1)
    assert reward==0 and not done and env.scheduler.cumulative==20
    assert env.action_masks().tolist()==[True,False,False]  # positive-dose cooling
    env.step(0)
    _,reward,done,_,info=env.step(2)
    assert done and info['weekly_steps']==3 and np.isfinite(reward)
    assert info['schema_hash']==config.schema_hash
    with pytest.raises(RuntimeError):env.step(0)
    with pytest.raises(ValueError,match='tail estimator'):
        SharedControlConfig((0,20),210,0,('DVS',),'raw-shared','fixture',eta=1)


def test_joint_outcome_model_train_year_firewall_and_correlated_members():
    from pcse_gym.agromas.outcome_model import TrainOutcomeModel
    rng=np.random.default_rng(4);x=rng.normal(size=(90,4));years=np.repeat([2000,2001,2002],30)
    y=np.c_[5+x[:,0]*.1,70+x[:,1],100+x[:,2],np.full(90,10)]
    m=TrainOutcomeModel(8,8,4).fit(x,y,years,[2000,2001,2002],role='Train',
                                 continuation_policy_id='fixed-rule-no-fit',label_source_id='synthetic-fixture')
    members=m(x[:2]);assert members.shape==(2,8,6)
    assert np.allclose(members[:,:,2],members[:,:,4]+members[:,:,5]-members[:,:,1])
    assert all(not set(f['fit_years'])&set(f['validation_years']) for f in m.cv_folds)
    with pytest.raises(ValueError,match='Non-Train'):
        m.fit(x,y,years,[2000],role='Train',continuation_policy_id='x',label_source_id='fixture')


def test_research_zone_and_dual_signals_change_without_double_pricing():
    t=table()
    strict=UrbanEcoSafetyAgent('strict_25',dual=2,dual_rate=.1).filter(t,50,50)
    outer=UrbanEcoSafetyAgent('outer_50',dual=2,dual_rate=.1).filter(t,50,50)
    assert strict.predicted_infeasible and not outer.predicted_infeasible
    assert strict.shadow_penalty>outer.shadow_penalty>=0
    economics=SocioEconomicPolicyAgent(EconomicPolicy(1,.2))
    # Dual signal remains diagnostic: identical hard cap/objective still identical decisions.
    a=AgroMASGlobalCoordinator(UrbanEcoSafetyAgent(dual=0),economics).choose(t,50,50)
    b=AgroMASGlobalCoordinator(UrbanEcoSafetyAgent(dual=100),economics).choose(t,50,50)
    assert a==b


def test_hydraulic_source_mismatch_fails_closed():
    from pcse_gym.agromas.urban_eco_agent import SoilHydraulicContext
    profile=SoilHydraulicContext('unit-soil','fixture','synthetic-test-only','medium',.3,.1,5)
    t=table();eco=UrbanEcoSafetyAgent(soil_profile=profile)
    with pytest.raises(ValueError,match='profile mismatch'):eco.filter(t,50,50)
    t=CandidateTable(t.doses,t.members,t.as_of,t.region_id,t.continuation_policy_id,t.climate_vector,t.model_id,'unit-soil')
    assert eco.filter(t,50,50).table.soil_profile_id=='unit-soil'


def test_weekly_wrapper_full_physical_season_with_explicit_stub_predictor():
    # This is a wrapper/units integration test; its stub predictions are NOT a fitted controller.
    import importlib.util
    from pathlib import Path
    from pcse_gym.agromas.baseline import WofostWeeklyEnv,SharedControlConfig
    root=Path(__file__).resolve().parents[3]
    spec=importlib.util.spec_from_file_location('physical_wrapper_probe',root/'scripts/phase5-co2-probe.py')
    probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
    def factory(rng,options):return probe.make_engine(380,3002),{'split':'legacy_Train','fixture_predictor':True}
    def encode(e,s):
        t=table((0,),((60,60),),((80,80),))
        t=CandidateTable(t.doses,t.members,e.day,'fixture',t.continuation_policy_id,t.climate_vector,t.model_id)
        return dict(observation=[float(e.get_variable('DVS') or 0),s.cumulative],candidate_table=t,agronomic_upper=0)
    def terminal(e,s):
        summary=e.get_summary_output()[-1];out=e.get_output()[-1]
        nonfert=3.5+1e4*(out['RNO3DEPOSTT']+out['RNH4DEPOSTT'])
        grain=summary['NamountSO'];inputs=s.cumulative+nonfert
        return [summary['TWSO']/1000,grain,inputs-grain,grain/inputs,s.cumulative,nonfert]
    cfg=SharedControlConfig((0,),210,0,('DVS','Nfert'),'raw-shared','explicit-unit-stub')
    e=WofostWeeklyEnv(factory,encode,terminal,UrbanEcoSafetyAgent(),SocioEconomicPolicyAgent(EconomicPolicy(1,.2)),cfg)
    e.reset(seed=4);steps=0;done=False
    while not done and steps<60:
        obs,reward,done,_,info=e.step(0);steps+=1
    assert done and 20<steps<60 and len(info['outcome'])==6
    assert info['outcome'][4]==0 and np.isfinite(info['outcome']).all()
    assert info['weekly_steps']==steps


def test_native_entropy_ppo_constructor_has_no_dose_prior():
    import gymnasium as gym
    from pcse_gym.agromas.baseline import make_entropy_ppo
    class E(gym.Env):
        observation_space=gym.spaces.Box(-1,1,(2,),dtype=np.float32)
        action_space=gym.spaces.Discrete(3)
        def reset(self,seed=None,options=None):return np.zeros(2,np.float32),{}
        def step(self,a):raise AssertionError('Constructor must not start training')
        def action_masks(self):return np.array([True,False,True])
    m=make_entropy_ppo(E(),4)
    assert m.ent_coef==.01 and m.num_timesteps==0
    assert m.policy.action_net.out_features==3
    assert not hasattr(m.policy,'prior_strength')


def test_weekly_clock_executes_next_day_not_an_extra_week_later():
    from pcse_gym.agromas.weekly import advance_week
    class DailyEngine:
        def __init__(self):
            self.day=date(2000,5,1);self.dvs=.92;self.terminated=False;self.applied=[]
        def run(self,days,action):
            self._guard_executed_action=0
            for i in range(days):
                self.day+=timedelta(days=1);self.dvs+=.02
                if i==days-1:
                    dose=self._action_guard(action,self.dvs,self.day)
                    self._guard_executed_action=dose
                    if dose:self.applied.append((self.day,dose))
    e=DailyEngine();s=ThreeStageScheduler(220);s.completed={0,1}
    e._action_guard=lambda a,dvs,day:s.execute(day,dvs,a,expected_stage=3)
    execution=advance_week(e,80)
    assert execution=='2000-05-02' and e.day==date(2000,5,8)
    assert e.applied==[(date(2000,5,2),80)] and e._guard_executed_action==80
    assert s.cumulative==80


def test_nextday_spacing_preview_is_pure_and_does_not_add_a_week():
    s=ThreeStageScheduler(220);t=date(2000,3,1)
    assert s.execute(t+timedelta(days=1),.4,40)==40
    decision=t+timedelta(days=14)
    original=(s.last_check,set(s.completed),list(s.events))
    assert s.preview(decision,.7) is None  # only13days since execution
    assert s.preview(decision+timedelta(days=1),.7)==2
    assert (s.last_check,s.completed,s.events)==original
    assert s.execute(decision+timedelta(days=1),.7,40)==40
    assert (date.fromisoformat(s.events[1]['date'])-date.fromisoformat(s.events[0]['date'])).days==14
    assert s.min_days==14

def test_v2_windows_keep_registered_probe_semantics():
    for dvs,stage in ((.4,1),(.7,2),(.92,3),(.95,3)):
        s=ThreeStageScheduler(220)
        assert s.eligible(date(2000,3,1),dvs)==stage


def test_regional_basal_schema_prevents_budget_omission_at_reset():
    from pcse_gym.agromas.baseline import WofostWeeklyEnv,SharedControlConfig
    class Fixture:
        day=date(2001,3,1)
    def factory(rng,options):return Fixture(),dict(region_id='china',initial_base_n=171.)
    def encode(e,s):
        t=table();t=CandidateTable(t.doses,t.members,e.day,t.region_id,t.continuation_policy_id,t.climate_vector,t.model_id)
        return dict(observation=[s.cumulative],candidate_table=t,agronomic_upper=100)
    config=SharedControlConfig((0,20,40),220,0,('Nfert',),'structured-shared','fixture',regional_base_n=(('china',171.),))
    env=WofostWeeklyEnv(factory,encode,None,UrbanEcoSafetyAgent(),None,config)
    obs,_=env.reset()
    assert obs[0]==171. and env.scheduler.budget-env.scheduler.cumulative==49.
    wrong=SharedControlConfig((0,20,40),220,0,('Nfert',),'structured-shared','fixture')
    env=WofostWeeklyEnv(factory,encode,None,UrbanEcoSafetyAgent(),None,wrong)
    with pytest.raises(ValueError,match='basal'):env.reset()
