import numpy as np
import pytest
from pcse_gym.agromas_v6.core import Policy,PairedStageOutcome,statistics,select_objective,AgroMASGlobalCoordinator
from pcse_gym.agromas_v6.books import DenseBooks

class Tree:
 def __init__(self,i):self.i=i
 def predict(self,x):return np.tile([5.,100.+self.i/10,30.+self.i,3.5],(len(x),1))
class Forest:estimators_=[Tree(i) for i in range(64)]

def members(nue=.7,surplus=20):
 m=np.zeros((1,7,32,6));m[...,0]=5;m[...,3]=nue;m[...,2]=surplus;m[...,4]=100;m[...,5]=3.5;m[...,1]=72.45
 return m

def test_pairs_and_projected_mass():
 x=np.zeros((7,23));x[:,3]=100;x[:,-1]=[0,10,20,40,60,80,100]
 m=PairedStageOutcome(Forest(),'test')(x)
 assert m.shape==(7,32,6)
 assert np.all(m[...,4]>=x[:,3,None]+x[:,-1,None])
 assert np.all(m[...,4]<=220)
 assert np.allclose(m[...,2],m[...,4]+m[...,5]-m[...,1])
 assert np.allclose(m[...,3],m[...,1]/(m[...,4]+m[...,5]))

def test_64_trees_required():
 f=Forest();f.estimators_=f.estimators_[:2]
 with pytest.raises(ValueError):PairedStageOutcome(f,'x')

def test_tier1_and_identity():
 s=statistics(members());legal=np.ones((1,7),bool);p=Policy(800,200)
 a,d=select_objective(s,legal,40.,1.,0.,p);b,e=AgroMASGlobalCoordinator(p).choose(s,legal)
 assert np.array_equal(a,b) and d['tier'][0]==1 and a[0]==0

def test_tier2_penalty_and_unilateral_removal():
 s=statistics(members(nue=1.4,surplus=-20));s[0,:,3]=[1.4,1.3,1.2,1.1,1.05,1.01,1.0];s[0,:,0]=[5,4.99,4.98,4.97,4.96,4.95,4.94]
 a,d=select_objective(s,np.ones((1,7),bool),40,1,0,Policy(0,800));assert a[0]==6 and d['tier'][0]==2
 a,d=select_objective(s,np.ones((1,7),bool),40,1,0,Policy(0,800,'LOAO-soil-mining-guard'));assert a[0]==0 and d['tier'][0]==1

def test_tier3_explicit_zero():
 s=statistics(members(nue=.3,surplus=80));a,d=select_objective(s,np.ones((1,7),bool),40,1,0,Policy());assert a[0]==0 and d['predicted_infeasible'][0] and d['tier'][0]==3

def test_budget_and_removed_cap():
 s=statistics(members(nue=.7,surplus=80));legal=np.zeros((1,7),bool);legal[:,0]=True
 a,d=select_objective(s,legal,40,1,0,Policy(family='LOAO-surplus-filter'));assert a[0]==0 and d['tier'][0]==1

def test_causal_prefix_rejects_unexecuted_future():
 f=np.zeros((1,3,343,22));available=np.ones((1,3,343),bool);out=np.zeros((1,343,6));f[0,0,1,0]=1
 with pytest.raises(ValueError,match='prefix'):DenseBooks([('x',2000,'Historical')],f,available,out)

def test_invalid_policy():
 with pytest.raises(ValueError):Policy(-1,0)


def test_terminal_fertilizer_is_known_not_forest_uncertainty():
 x=np.zeros((7,23));x[:,3]=0;x[:,5]=3;x[:,-1]=[0,10,20,40,60,80,100]
 m=PairedStageOutcome(Forest(),'terminal')(x)
 assert np.array_equal(m[:,:,4],np.broadcast_to((x[:,3]+x[:,-1])[:,None],(7,32)))
 old=PairedStageOutcome(Forest(),'legacy');del old.terminal_fertilizer_known
 assert np.any(old(x)[:,:,4]!=m[:,:,4])

def test_book_environment_labels_cannot_change_observation_or_mask():
 from pcse_gym.agromas_v6.book_env import TrainBookEnv
 features=np.zeros((1,3,343,22));available=np.ones((1,3,343),bool);outcomes=np.zeros((1,343,6));outcomes[...,0]=5;outcomes[...,3]=.7
 data=DenseBooks([('fixture',2000,'Historical')],features,available,outcomes)
 stats=statistics(members())[0];tables={s:np.broadcast_to(stats,(1,7**(s-1),7,10)).copy() for s in (1,2,3)};legal={s:np.ones((1,7**(s-1),7),bool) for s in (1,2,3)}
 env=TrainBookEnv(data,tables,legal,Policy());before,_=env.reset(seed=4);mask=env.action_masks();data.outcomes[...,0]+=100;after,_=env.reset(seed=4)
 assert before.shape==(91,) and np.array_equal(before,after) and np.array_equal(mask,env.action_masks())
 for _ in range(3):obs,reward,done,_,info=env.step(int(np.flatnonzero(env.action_masks())[0]))
 assert done and info['partial_profit']>20000
 with pytest.raises(ValueError,match='TRAINonly'):TrainBookEnv(DenseBooks([('x',2010,'Historical')],features,available,outcomes),tables,legal,Policy())

def test_backward_pipeline_never_fits_validation_year_labels():
 from pcse_gym.agromas_v6.training import fit_pipeline
 from pcse_gym.agromas_v6.books import PLANS
 features=np.zeros((4,3,343,22));features[:,:,:,5]=np.arange(1,4)[None,:,None];available=np.ones((4,3,343),bool);outcomes=np.zeros((4,343,6));outcomes[:,:,0]=5+PLANS.sum(1)*.001;outcomes[:,:,4]=PLANS.sum(1);outcomes[:,:,5]=3.5;outcomes[:,:,1]=.7*(outcomes[:,:,4]+3.5);outcomes[:,:,2]=.3*(outcomes[:,:,4]+3.5);outcomes[:,:,3]=.7
 data=DenseBooks([('fixture',y,'Historical') for y in (1995,1996,1997,1998)],features,available,outcomes);first,_=fit_pipeline(data,np.array([0,1,2]),Policy())
 data.outcomes[3]*=100000;second,_=fit_pipeline(data,np.array([0,1,2]),Policy())
 assert all(first[s].model_id==second[s].model_id for s in (1,2,3))
