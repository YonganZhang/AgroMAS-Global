"""Train-only full-observation response probes; no diagnostic oracle enters a policy."""
import pathlib,json,sys,numpy as np
from sklearn.ensemble import ExtraTreesRegressor,HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
from pcse_gym.envs.corridor import terminal_compliance
raw=json.loads((R/'reports/phase3b-training-calibration-v1.json').read_text());rows=[r for r in raw['episodes'] if r['stages']==[70,130]];windows=json.loads((R/'reports/phase3b-training-observation-windows.json').read_text())['observations'];obs={(r['year'],r['soil']):np.array(r['observation']) for r in windows}
max_error=max(abs(obs[r['year'],r['soil']][-1,1]*10-r['features']['LAI']) for r in rows);assert max_error<1e-6
Y=np.array([r['yield_t_ha']-.002*r['actual_N']+terminal_compliance(r['NUE'],r['surplus'],raw['calibration']['joint_bonus']) for r in rows]);groups=np.array([r['year'] for r in rows]);results={}
for family in ['extra_trees','hist_gradient_boosting']:
 for oracle in [False,True]:
  X=np.array([obs[r['year'],r['soil']].flatten().tolist()+[r['actual_N']]+([int(r['soil']==s) for s in ['default','fast','slow']] if oracle else []) for r in rows]);choices=[]
  for fold,(fit,test) in enumerate(GroupKFold(5).split(X,Y,groups)):
   model=ExtraTreesRegressor(n_estimators=128,min_samples_leaf=3,n_jobs=2,random_state=4) if family=='extra_trees' else HistGradientBoostingRegressor(max_iter=150,max_leaf_nodes=7,l2_regularization=1,early_stopping=False,random_state=4)
   model.fit(X[fit],Y[fit]);pred=model.predict(X[test]);cases={}
   for idx,score in zip(test,pred):cases.setdefault((rows[idx]['year'],rows[idx]['soil']),[]).append((float(score),idx))
   for case,items in cases.items():
    r=rows[max(items)[1]];choices.append(dict(year=r['year'],soil=r['soil'],N=r['actual_N'],joint=.5<=r['NUE']<=.9 and 0<=r['surplus']<=40,yield_t_ha=r['yield_t_ha']))
  results[family+('_soil_label_oracle' if oracle else '_observable')]=dict(n=len(choices),joint=float(np.mean([c['joint'] for c in choices])),N=float(np.mean([c['N'] for c in choices])),yield_t_ha=float(np.mean([c['yield_t_ha'] for c in choices])),choices=choices)
out=R/'reports/phase3b-full-window-response-probe.json';assert not out.exists();out.write_text(json.dumps(dict(training_only=True,full_actor_window=True,year_grouped_cv=True,calibration_vs_current_observation_LAI_max_error=max_error,results=results,warning='150 training scenarios only, not an impossibility proof. Oracle soil labels are diagnostic metadata never available to actors.'),indent=2));print({k:{x:v for x,v in z.items() if x!='choices'} for k,z in results.items()})
