"""Synthetic unit fixtures only, never scored scientific output."""
import numpy as np
import pytest
from pcse_gym.agromas_v8.scoring import build_stratified_residual_banks,build_global_zero_mean_bank
from pcse_gym.agromas_v8.planning import distribution_metrics,Regime,choose_tier
from pcse_gym.agromas_v8.prior_adapter import LowRankPriorAdapter

def test_all_fifteen_residual_strata_are_deterministic_centered_and_joint():
 rng=np.random.default_rng(1);meta=[dict(region='site'+str(r),stage=s,year=1995+i%15) for r in range(5) for s in (1,2,3) for i in range(64)];res=rng.normal(size=(len(meta),3))+np.arange(len(meta))[:,None]
 a=build_stratified_residual_banks(res,meta);b=build_stratified_residual_banks(res,meta);assert len(a)==15
 for key,v in a.items():assert v.shape==(32,3) and np.max(abs(v.mean(0)))<1e-10;np.testing.assert_array_equal(v,b[key])
 assert np.max(abs(build_global_zero_mean_bank(res,meta).mean(0)))<1e-10
 meta[0]['year']=2015
 with pytest.raises(ValueError):build_stratified_residual_banks(res,meta)

def test_each_weather_leaf_integrates_all_residuals():
 a=np.zeros((2,32,6));a[0,:,2]=np.arange(32);a[1,:,2]=100+np.arange(32);a[...,0]=1;a[...,3]=.7
 d=distribution_metrics(a,[.25,.75],Regime(eco=False,econ=False));assert d['mean'][2]==90.5
 leaf=distribution_metrics(a[:1],[1.],Regime(eco=False,econ=False));assert leaf['mean'][2]==15.5

def test_corridor_preferred_then_upper_surplus_then_operational_zero():
 def m(s,nue,score):return dict(mean=np.array([0,0,s,nue]),eco_safe=False,NUE_safe=.5<=nue<=.9,score=score)
 v=[m(20,1.2,1000),m(25,.7,0)]
 assert choose_tier(v,[0,20],Regime())==(1,2)
 assert choose_tier(v,[0,20],Regime(bare_tier2=True))==(0,2)
 assert choose_tier([m(20,1.2,1)],[0],Regime())==(0,2)
 assert choose_tier([m(100,.7,1)],[0],Regime())==(0,3)

def test_decomposed_adapter_ignores_future_satellite_and_outer_labels():
 rng=np.random.default_rng(11);priors={f'site{r}:{year}':(rng.normal(size=64)+r*10,f'{year}-12-31') for r in range(5) for year in range(2017,2023)}
 context=[(f'site{r}:{year}',f'{year+1}-04-01') for r in range(4) for year in range(2017,2022) for _ in range(6)];x=rng.normal(size=(len(context),36));x[:,5]=np.tile([1,2,3],len(x)//3);x[:,3]=0;x[:,22:25]=20;target=rng.normal(size=(len(x),3));a=LowRankPriorAdapter().fit(x,target,np.ones(len(x)),context,priors=priors)
 p=priors.copy();p['site0:2022']=(np.full(64,1e9),'2022-12-31');b=LowRankPriorAdapter().fit(x,target,np.ones(len(x)),context,priors=p)
 np.testing.assert_array_equal(a.axes,b.axes);np.testing.assert_array_equal(a.predict(x,context),b.predict(x,context))
 future=[(key,'2017-01-01') for key,_ in context];delta,accepted=a.correction(x,future);assert not accepted.any();np.testing.assert_allclose(delta,a.static.predict(x,future),atol=0,rtol=0)

def test_rare_weather_branch_tail_is_not_lost_to_systematic_pairing():
 m=np.zeros((2,32,6));m[...,0]=5;m[...,3]=.7;m[0,:,2]=1000
 d=distribution_metrics(m,[.01,.99],Regime());assert d['CVaR']==pytest.approx(100.);assert not d['eco_safe']

def test_region_stock_heads_exclude_scored_labels_and_keep_sparse_region_offsets():
 from pcse_gym.agromas_v8.decoding import fit_region_heads
 rng=np.random.default_rng(4);x=rng.normal(size=(100,3));regions=np.repeat(['dense','sparse'],[80,20]);y=(x[:,0]*2+(regions=='sparse')*10000)[:,None];train=np.arange(100)%4!=0;test=~train;w=np.where(regions=='dense',1/80,1/20)
 a=fit_region_heads(x,y,regions,w,train,test,alpha=.01);corrupt=y.copy();corrupt[test]=1e20;b=fit_region_heads(x,corrupt,regions,w,train,test,alpha=.01);np.testing.assert_array_equal(a,b);assert np.max(abs(a-y[test]))<.5

def test_full_residual_lookup_uses_known_soil_stage_and_synthetic_global_fallback():
 from pcse_gym.agromas_v8.joint_model import FrozenJointWorldModel
 a=FrozenJointWorldModel.__new__(FrozenJointWorldModel);a._adapter=None;a.point=lambda z:np.tile([5.,100.,100.],(len(z),1));a.residual=np.zeros((32,3));a.soil_to_region={(1.,2.,3.):'private-site'}
 bank=np.zeros((32,3));bank[:,1]=np.linspace(-3,3,32);a.residual_banks={('private-site',1):bank};x=np.zeros((2,36));x[:,5]=1;x[:,3]=50;x[:,22]=60;x[0,19:22]=[1,2,3];response=a.response_tensor(x,np.zeros((2,9)))
 assert response.shape==(2,2,32,6);assert np.std(response[0,0,:,1])>0;assert np.std(response[1,0,:,1])==0


def test_nested_stock_readout_ignores_outer_labels_and_preserves_world_weight_units():
 from pcse_gym.agromas_v8.decoding import nested_region_heads
 rng=np.random.default_rng(9);x=rng.normal(size=(120,4));years=np.repeat(np.arange(1995,2005),12);regions=np.repeat('site',120);y=x[:,:2]*2+3;w=np.full(120,1/12);train=years<2003;test=~train
 a,aa=nested_region_heads(x,y,regions,years,w,train,test,alphas=(.01,1.))
 altered=y.copy();altered[test]=1e20;b,bb=nested_region_heads(x,altered,regions,years,w,train,test,alphas=(.01,1.))
 np.testing.assert_array_equal(a,b);assert aa==bb;assert aa[0]['world_weight_sum']==pytest.approx(8.)
 assert aa[0]['inner_years']==list(range(1995,2003))
