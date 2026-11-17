"""Freeze utility prior using year-grouped TRAIN-only model selection."""
import pathlib,json,sys,hashlib
import numpy as np
from sklearn.model_selection import GroupKFold
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.linear_model import Ridge
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
from pcse_gym.envs.moisture4 import utility_features
from pcse_gym.envs.corridor import terminal_compliance
if __name__=='__main__':
 src=R/'reports/phase3c-training-utility-grid.json';records=json.loads(src.read_text())['records'];assert len(records)==360
 X=np.array([utility_features(np.array(r['observation'])[-1,:11]) for r in records]);groups=np.array([r['year'] for r in records]);E=[sorted(r['episodes'],key=lambda e:e['actual_N']) for r in records]
 assert all([e['actual_N'] for e in es]==list(range(160,211,10)) for es in E)
 U=np.array([[e['yield_t_ha']-.002*e['actual_N']+terminal_compliance(e['NUE'],e['surplus'],8)-max(0,(e['surplus']-40)/20) for e in es] for es in E])
 variants=['ridge.1','ridge1','ridge10','ridge100','forest'];scores={}
 def fit(name,x,y):return (ExtraTreesRegressor(n_estimators=64,max_depth=5,min_samples_leaf=4,n_jobs=2,random_state=4) if name=='forest' else Ridge(alpha=float(name[5:]))).fit(x,y)
 for name in variants:
  choices=np.zeros(360,dtype=int)
  for train,test in GroupKFold(5).split(X,U,groups):
   mu=X[train].mean(0);sd=X[train].std(0);sd[sd<1e-8]=1;m=fit(name,np.clip((X[train]-mu)/sd,-5,5),U[train]);choices[test]=m.predict(np.clip((X[test]-mu)/sd,-5,5)).argmax(1)
  chosen=[E[i][a] for i,a in enumerate(choices)];scores[name]=dict(joint=float(np.mean([.5<=e['NUE']<=.9 and 0<=e['surplus']<=40 for e in chosen])),utility=float(U[np.arange(360),choices].mean()),yield_t_ha=float(np.mean([e['yield_t_ha'] for e in chosen])),dose_counts={str(160+10*a):int(np.sum(choices==a)) for a in range(6)})
 best=max(variants,key=lambda n:(scores[n]['joint'],scores[n]['utility'],scores[n]['yield_t_ha']));mu=X.mean(0);sd=X.std(0);sd[sd<1e-8]=1;m=fit(best,np.clip((X-mu)/sd,-5,5),U)
 c=dict(model='forest' if best=='forest' else 'ridge',mean=mu.tolist(),scale=sd.tolist(),train_years=sorted(set(groups.tolist())),stages=[70,130],joint_bonus=8,prior_strength=.1,feature_names=['LAI','SM','SM_squared','past7dRAIN_scaled','IRRAD_scaled','TMIN_scaled'],selection=best,train_grouped_CV=scores,table_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),fit_scenarios=360,fixed_initial_soil=True)
 if best=='forest':
  trees=[e.tree_ for e in m.estimators_];size=max(t.node_count for t in trees);features=np.full((64,size),-2);threshold=np.zeros((64,size));left=np.zeros((64,size),int);right=left.copy();value=np.zeros((64,size,6))
  for i,t in enumerate(trees):
   n=t.node_count;features[i,:n]=t.feature;threshold[i,:n]=t.threshold;left[i,:n]=t.children_left;right[i,:n]=t.children_right;value[i,:n]=t.value[:,:,0]
  c.update(forest_features=features.tolist(),forest_thresholds=threshold.tolist(),forest_left=left.tolist(),forest_right=right.tolist(),forest_values=value.tolist(),forest_depth=5)
 else:c.update(coefficients=m.coef_.T.tolist(),intercepts=m.intercept_.tolist())
 out=R/'reports/phase3c-frozen-utility-v1.json';assert not out.exists();out.write_text(json.dumps(c));print(json.dumps(dict(selected=best,CV=scores)))
