"""Reproduce Phase5 point-vs-global-residual TRAIN diagnostics without new physics."""
from pathlib import Path
import json,hashlib
import numpy as np,joblib
from pcse_gym.agromas.continuation import project_members
from pcse_gym.agromas_v6.books import load_train,FACTORS,PLANS
from pcse_gym.agromas_v6.core import GRID
R=Path(__file__).resolve().parents[1];P=R/'reports/phase6'
if __name__=='__main__':
 data=load_train(R);models={s:joblib.load(R/f'models/phase5/continuation-v2/stage-{s}.joblib') for s in (1,2,3)};results=[];spread=[]
 for mode in ['point','global-residual']:
  w=np.arange(len(data.keys));ix=np.zeros(len(w),int)
  for stage in (1,2,3):
   x,legal=data.candidate_inputs(w,ix,stage);flat=x.reshape(-1,23);ok=legal.ravel();members=np.zeros((len(flat),32 if mode=='global-residual' else 1,6));fert=flat[:,3]+flat[:,-1];members[:,:,4]=fert[:,None];members[:,:,5]=3.5;members[:,:,2]=fert[:,None]+3.5
   model=models[stage]
   if mode=='point':members[ok]=project_members(model.model.predict(flat[ok])[:,None,:],flat[ok])
   else:members[ok]=model(flat[ok])
   members=members.reshape(len(w),7,members.shape[1],6);s=members[...,2];nue=members[...,3];joint=(nue>=.5)&(nue<=.9)&(s<=40)&(s>=0)
   q=np.quantile(s,.9,axis=-1,method='higher');allowed=legal&(q<=40);value=(200*members[...,0]-1.5*members[...,4]).mean(-1)+200*joint.mean(-1);value=np.where(allowed,value,-np.inf)
   chosen=np.argmax(value,-1);chosen=np.where(allowed.any(-1),chosen,0);ix+=chosen*FACTORS[stage-1]
   if mode=='global-residual':
    point=project_members(model.model.predict(flat[ok])[:,None,:],flat[ok])[:,0];res=members.reshape(-1,32,6)[ok];compliant=(point[:,3]>=.5)&(point[:,3]<=.9)&(point[:,2]<=40)
    spread.append(dict(stage=stage,n_legal=int(ok.sum()),mean_member_Nfert_sd=float(res[...,4].std(-1).mean()),point_compliant_candidates=int(compliant.sum()),mean_q90_surplus_inflation_on_point_compliant=float(np.mean(np.quantile(res[compliant,:,2],.9,axis=-1,method='higher')-point[compliant,2])) if compliant.any() else None))
  rows=[]
  for k,i in enumerate(ix):
   m=data.outcomes[k,i];rows.append(dict(region_id=data.keys[k][0],year=data.keys[k][1],climate=data.keys[k][2],joint=bool(.5<=m[3]<=.9 and 0<=m[2]<=40),outcome=m.tolist(),plan=PLANS[i].tolist()))
  summary={name:float(np.mean([r['joint'] for r in rows if r['region_id']==name and r['climate']=='Historical'])) for name in sorted({r['region_id'] for r in rows})}
  results.append(dict(mode=mode,Historical_region_joint=summary,Historical_macro_joint=float(np.mean(list(summary.values()))),rows=rows))
 out=dict(scope='TRAIN1995–2009resubstitutiondiagnosticusingunchangedv4weights;notOOFandnotfinalbenchmark',results=results,conditional_spread=spread,new_physical_rollouts=0)
 with (P/'phase5-TRAIN-root-cause-reproduction-v6.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps([{k:v for k,v in d.items() if k!='rows'} for d in results]));print(json.dumps(spread))
