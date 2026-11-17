import numpy as np
from pcse_gym.agromas_v8.prior_adapter import LowRankPriorAdapter

def fixture():
 rng=np.random.default_rng(8);x=rng.normal(size=(120,36));x[:,3]=0;x[:,22:25]=20;x[:,5]=np.tile([1,2,3],40);y=rng.normal(size=(120,3));w=np.ones(120)/12
 priors={str(k):(rng.normal(size=64),'2017-12-31') for k in range(10)};context=[(str(i//12),'2018-03-01') for i in range(120)]
 return x,y,w,priors,context

def test_outer_labels_do_not_change_fold_transform_or_predictions():
 x,y,w,p,c=fixture();train=np.arange(96);test=np.arange(96,120)
 def fit(labels):return LowRankPriorAdapter(legacy=True).fit(x[train],labels[train],w[train],[c[i] for i in train],priors=p)
 a=fit(y);corrupted=y.copy();corrupted[test]=1e12;b=fit(corrupted)
 np.testing.assert_array_equal(a.axes,b.axes);np.testing.assert_array_equal(a.predict(x[test],[c[i] for i in test]),b.predict(x[test],[c[i] for i in test]));assert a.axes.shape[1]<=4

def test_prior_annual_end_must_precede_issue_and_rejection_is_base_fallback():
 x,y,w,p,c=fixture();a=LowRankPriorAdapter(legacy=True).fit(x,y,w,c,priors=p)
 future=[(key,'2017-12-31') for key,_ in c];delta,accepted=a.correction(x,future);assert not accepted.any();assert not delta.any()

def test_static_and_weather_prior_dimensions_are_bounded():
 x,y,w,p,c=fixture()
 for kind,limit in [('Static3',3),('Weather',4)]:
  a=LowRankPriorAdapter(kind).fit(x,y,w,c);assert a.axes.shape[1]<=limit

def test_ood_threshold_gives_sparse_site_year_equal_weight():
 # Nine dense worlds and one sparse basal-limited world. A row percentile
 # would reject the sparse world despite its10%site-year probability mass.
 x=np.zeros((109,36));x[:,5]=1;x[:,22]=20;x[-1,19]=100
 y=np.zeros((109,3));context=[(str(i//12),'2018-03-01') for i in range(108)]+[('sparse','2018-03-01')]
 adapter=LowRankPriorAdapter('Static3').fit(x,y,np.ones(109),context)
 assert adapter.correction(x,context)[1].all()
