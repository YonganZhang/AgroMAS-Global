"""Rebuild the chosen TRAIN-only sklearn scorer and compare deployed frozen buffers."""
import pathlib,json,sys,numpy as np
from sklearn.ensemble import ExtraTreesRegressor
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
from pcse_gym.envs.moisture4 import utility_features,utility_scores
from pcse_gym.envs.corridor import terminal_compliance
c=json.loads((R/'reports/phase3c-frozen-utility-v1.json').read_text());assert c['selection']=='forest'
rows=json.loads((R/'reports/phase3c-training-utility-grid.json').read_text())['records'];frames=np.array([r['observation'][-1][:11] for r in rows]);X=utility_features(frames);E=[sorted(r['episodes'],key=lambda e:e['actual_N']) for r in rows];Y=np.array([[e['yield_t_ha']-.002*e['actual_N']+terminal_compliance(e['NUE'],e['surplus'],8)-max(0,(e['surplus']-40)/20) for e in es] for es in E]);z=np.clip((X-np.array(c['mean']))/np.array(c['scale']),-5,5)
m=ExtraTreesRegressor(n_estimators=64,max_depth=5,min_samples_leaf=4,n_jobs=2,random_state=4).fit(z,Y);sk=m.predict(z);deployed=utility_scores(frames,c);err=float(np.max(np.abs(sk-deployed)));agree=float(np.mean(sk.argmax(1)==deployed.argmax(1)));assert err<1e-5 and agree==1
out=R/'reports/phase3c-scorer-parity.json';assert not out.exists();out.write_text(json.dumps(dict(training_only=True,scenarios=360,max_utility_error=err,argmax_agreement=agree,sklearn_version=__import__('sklearn').__version__),indent=2));print(err,agree)
