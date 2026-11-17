"""Training-only grouped diagnostic; soil-label oracle is NOT a deployable actor."""
import pathlib,json,numpy as np
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.model_selection import GroupKFold
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1]
import sys;sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
from pcse_gym.envs.corridor import terminal_compliance
raw=json.loads((R/'reports/phase3b-training-calibration-v1.json').read_text());c=raw['calibration'];rows=[r for r in raw['episodes'] if r['stages']==[70,130]]
assert all(3002<=r['year']<=4999 and r['actual_N']==r['requested_N'] for r in rows)
y=np.array([r['yield_t_ha']-.002*r['actual_N']+terminal_compliance(r['NUE'],r['surplus'],c['joint_bonus']) for r in rows]);groups=np.array([r['year'] for r in rows]);results={}
for oracle in [False,True]:
 X=np.array([[r['features']['LAI'],r['features']['LAI_delta'],r['features']['RAIN_scaled'],r['actual_N']]+([int(r['soil']==s) for s in ['default','fast','slow']] if oracle else []) for r in rows])
 choices=[]
 for fold,(fit,test) in enumerate(GroupKFold(5).split(X,y,groups)):
  model=ExtraTreesRegressor(n_estimators=128,min_samples_leaf=3,n_jobs=2,random_state=4);model.fit(X[fit],y[fit]);pred=model.predict(X[test]);cases={}
  for idx,score in zip(test,pred):cases.setdefault((rows[idx]['year'],rows[idx]['soil']),[]).append((float(score),idx))
  for case,items in cases.items():
   idx=max(items)[1];r=rows[idx];choices.append(dict(year=r['year'],soil=r['soil'],N=r['actual_N'],joint=.5<=r['NUE']<=.9 and 0<=r['surplus']<=40,yield_t_ha=r['yield_t_ha'],fold=fold))
 results['unavailable_soil_label_oracle' if oracle else 'observable_response_model']=dict(n=len(choices),joint=float(np.mean([q['joint'] for q in choices])),N=float(np.mean([q['N'] for q in choices])),yield_t_ha=float(np.mean([q['yield_t_ha'] for q in choices])),choices=choices)
fixed=[r for r in rows if r['actual_N']==190]
result=dict(training_only=True,grouped_validation='5-fold held-out training years, never Dev',fixed190_joint=float(np.mean([.5<=r['NUE']<=.9 and 0<=r['surplus']<=40 for r in fixed])),results=results,warning='Small calibration-set diagnostic, not proof of information-theoretic impossibility; soil labels used only for a diagnostic upper-information comparison and never actor inputs.')
out=R/'reports/phase3b-training-response-probe.json';assert not out.exists();out.write_text(json.dumps(result,indent=2));print({k:{x:v for x,v in z.items() if x!='choices'} for k,z in results.items()})
