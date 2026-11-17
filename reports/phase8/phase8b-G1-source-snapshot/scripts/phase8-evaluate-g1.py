"""Single Dev access for frozen G1 models. Never executes G2/G3 or opens Held-Out.

Conformal Dev coverage is calibration-set empirical coverage, not independent
coverage validation. Frozen choices and raw scores are retained without tuning.
"""
from pathlib import Path
import hashlib,json
import numpy as np,torch,joblib
from pcse_gym.agromas_v8.data import load_dev_once,parity_features
from pcse_gym.agromas_v8.models import WorldModel
from pcse_gym.agromas_v8.climate import ClimateForecastAgent
from pcse_gym.agromas_v8.scoring import project_executed_members,brier,bss,conformal_radius,ranking_regret,utility
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';D=R/'cache/phase8-train-arrays';M=R/'models/phase8-v8';O=R/'data/phase8-g1-predictions'
SEEDS=[20261115,20261116,20261117];CAPS=[25.,35.,40.,50.]

class Predictor:
 def __init__(self,track,arch,device='cuda'):
  self.device=device;self.track=track;self.arch=arch;self.models=[]
  if arch=='ExtraTrees':self.models=[joblib.load(M/f'{track}-ExtraTrees-fold-1.joblib')]
  else:
   for seed in SEEDS:
    c=torch.load(M/f'{track}-{arch}-fold-1-seed{seed}/model.pt',weights_only=False);model=WorldModel(architecture=arch);model.load_state_dict(c['state_dict'],strict=True);self.models.append((model.to(self.device).eval(),c))
 def predict(self,x,seed_index=None):
  x=parity_features(x,self.track)
  if self.arch=='ExtraTrees':return self.models[0].predict(x)
  if seed_index is None:return np.mean([self.predict(x,i) for i in range(len(self.models))],axis=0)
  model,c=self.models[seed_index];z=np.where(c['x_active'],np.clip((x-c['x_mean'])/c['x_std'],-8,8),0).astype('float32')
  with torch.no_grad():return model(torch.from_numpy(z).to(self.device)).cpu().numpy()*c['y_std']+c['y_mean']

def residuals(track,arch,y,meta):
 years=np.array([m['year'] for m in meta]);pred=np.zeros_like(y)
 for fold in range(5):
  ids=(years-1995)%5==fold
  if arch=='ExtraTrees':p=np.load(D/f'{track}-ExtraTrees-fold{fold}-pred.npy')
  else:p=np.mean([np.load(D/f'{track}-{arch}-fold{fold}-seed{s}-pred.npy') for s in SEEDS],axis=0)
  if p.shape!=y[ids].shape:raise ValueError('Outer TRAIN OOF alignment')
  pred[ids]=p
 return y-pred,pred

def marginal_members(x,meta,predictor,residual):
 agent=ClimateForecastAgent(R);rng=np.random.default_rng(20261115);rid=rng.integers(len(residual),size=32)
 out=np.zeros((len(x),32,6));groups={}
 for i,m in enumerate(meta):groups.setdefault((m['region'],m['as_of'],m['climate']),[]).append(i)
 for (region,issue,climate),ids in groups.items():
  weather,weight,years=agent.branches(region,issue,climate);branches=np.searchsorted(np.cumsum(weight),(np.arange(32)+.5)/32);branches=np.minimum(branches,len(weather)-1)
  ids=np.asarray(ids);raw=np.zeros((len(ids),32,3))
  branch_prediction={}
  for k in range(32):
   candidate=np.array(x[ids],copy=True);candidate[:,-9:]=weather[branches[k]]
   branch_id=int(branches[k])
   if branch_id not in branch_prediction:branch_prediction[branch_id]=predictor.predict(candidate)
   raw[:,k]=branch_prediction[branch_id]+residual[rid[k]]
  out[ids]=project_executed_members(raw,x[ids])
 return out

def defined_skill(candidate,reference):
 # A perfect reference has zero denominator: report undefined and fail the
 # strict-improvement gate rather than creating NaN or inventing skill.
 return None if reference<=0 else bss(candidate,reference)

def metrics(members,y,meta,baseline,train_y,train_meta):
 truth_surplus=y[:,2]+3.5-y[:,1];profit=200*y[:,0]-1.5*y[:,2]
 groups={}
 for i,m in enumerate(meta):groups.setdefault((m['region'],m['year'],m['stage']),[]).append(i)
 weight=np.zeros(len(meta))
 for ids in groups.values():weight[ids]=1/len(ids)
 weight/=weight.sum()
 def weighted_brier(p,t):return float(np.sum(weight*(np.asarray(p)-np.asarray(t))**2))
 lower=np.quantile(members[...,2],.05,axis=1,method='lower');upper=np.quantile(members[...,2],.95,axis=1,method='higher')
 scores=np.maximum(lower-truth_surplus,truth_surplus-upper);radius=conformal_radius(scores)
 coverage=(truth_surplus>=lower-radius)&(truth_surplus<=upper+radius)
 # Leave-one-Dev-year-out calibration avoids using each scored year to fit
 # its radius. No predictor or alpha is refit; this is the pre-registered coverage gate.
 years=np.array([m['year'] for m in meta]);cross=np.zeros(len(y),bool)
 for year in sorted(set(years)):
  ix=years==year;r=conformal_radius(scores[~ix]);cross[ix]=(truth_surplus[ix]>=lower[ix]-r)&(truth_surplus[ix]<=upper[ix]+r)
 bycap={};train_s=train_y[:,2]+3.5-train_y[:,1]
 for cap in CAPS:
  truth=truth_surplus<=cap;pred=(members[...,2]<=cap).mean(1);ref=(baseline[...,2]<=cap).mean(1)
  clim={}
  for region in sorted({m['region'] for m in train_meta}):
   for stage in (1,2,3):
    mask=np.array([m['region']==region and m['stage']==stage and m['climate']=='Historical' for m in train_meta]);clim[(region,stage)]=float((train_s[mask]<=cap).mean())
  prob=np.array([clim[(m['region'],m['stage'])] for m in meta]);candidate=weighted_brier(pred,truth);tree=weighted_brier(ref,truth);climatology=weighted_brier(prob,truth)
  bycap[str(int(cap))]=dict(brier=candidate,tree_brier=tree,climatology_brier=climatology,BSS_vs_ExtraTrees=defined_skill(candidate,tree),BSS_vs_region_stage_climatology=defined_skill(candidate,climatology))
  event_diagnostics={}
  train_nue=train_y[:,1]/(train_y[:,2]+3.5);dev_nue=y[:,1]/(y[:,2]+3.5)
  for event in ['surplus_corridor','joint_surplus_and_NUE']:
   tz=(train_s>=0)&(train_s<=cap);dz=(truth_surplus>=0)&(truth_surplus<=cap)
   pz=(members[...,2]>=0)&(members[...,2]<=cap);bz=(baseline[...,2]>=0)&(baseline[...,2]<=cap)
   if event=='joint_surplus_and_NUE':
    tz&=(train_nue>=.5)&(train_nue<=.9);dz&=(dev_nue>=.5)&(dev_nue<=.9)
    pz&=(members[...,3]>=.5)&(members[...,3]<=.9);bz&=(baseline[...,3]>=.5)&(baseline[...,3]<=.9)
   climate_probability={}
   for region in sorted({m['region'] for m in train_meta}):
    for stage in (1,2,3):
     mask=np.array([m['region']==region and m['stage']==stage and m['climate']=='Historical' for m in train_meta]);climate_probability[(region,stage)]=float(tz[mask].mean())
   cp=np.array([climate_probability[(m['region'],m['stage'])] for m in meta]);bs=weighted_brier(pz.mean(1),dz);bt=weighted_brier(bz.mean(1),dz);bc=weighted_brier(cp,dz)
   event_diagnostics[event]={'brier':bs,'BSS_vs_ExtraTrees':defined_skill(bs,bt),'BSS_vs_climatology':defined_skill(bs,bc),'TRAIN_all_climates_legal_base_rate':float(tz.mean()),'Dev_macro_base_rate':float(np.sum(weight*dz)),'diagnostic_not_gate':True}
  bycap[str(int(cap))]['additional_events']=event_diagnostics
  bycap[str(int(cap))]['primary_event']='S_N <= cap only, as literally specified; distinct from corridor and full joint compliance'
  bycap[str(int(cap))]['TRAIN_all_climates_upper_surplus_base_rate']=float((train_s<=cap).mean())

 regret,groups=ranking_regret(meta,utility(members),profit,macro=True);tree_regret,_=ranking_regret(meta,utility(baseline),profit,macro=True)
 pooled_regret,_=ranking_regret(meta,utility(members),profit);pooled_tree_regret,_=ranking_regret(meta,utility(baseline),profit)
 byregion={}
 for region in sorted({m['region'] for m in meta}):
  ix=np.array([m['region']==region for m in meta]);byregion[region]=dict(samples=int(ix.sum()),coverage=float(coverage[ix].mean()),crossyear_coverage=float(cross[ix].mean()),joint_raw_point_RMSE=np.sqrt(np.mean((members[ix][:,:,[0,1,4]].mean(1)-y[ix])**2,axis=0)).tolist())
 gates=dict(BSS_positive_both_references_all_caps=all(v['BSS_vs_ExtraTrees'] is not None and v['BSS_vs_region_stage_climatology'] is not None and v['BSS_vs_ExtraTrees']>0 and v['BSS_vs_region_stage_climatology']>0 for v in bycap.values()),coverage_85_to_95=.85<=float(np.sum(weight*cross))<=.95,ranking_regret_strictly_lower_than_ExtraTrees=regret<tree_regret)
 return dict(samples=len(y),unique_prefix_groups=groups,caps=bycap,conformal_alpha=.1,conformal_radius_kg_ha=radius,uncalibrated_90pct_coverage=float(((truth_surplus>=lower)&(truth_surplus<=upper)).mean()),Dev_calibration_set_90pct_coverage=float(coverage.mean()),Dev_crossyear_diagnostic_90pct_coverage=float(cross.mean()),Dev_crossyear_macro_90pct_coverage=float(np.sum(weight*cross)),metric_weighting='equal region-year-stage; pooled coverage separately reported',partial_profit_ranking_regret_EUR_ha=regret,ExtraTrees_regret_EUR_ha=tree_regret,pooled_prefix_regret_EUR_ha=pooled_regret,pooled_ExtraTrees_regret_EUR_ha=pooled_tree_regret,regret_weighting="equal region-year-stage means of unique-prefix regrets",by_region=byregion,gates=gates,passed=all(gates.values()),coverage_scope='G1 coverage uses leave-one-Dev-year-out conformal radii, frozen predictors, equal region-year-stage weights. Final pooled Dev calibration-set coverage is secondary only; correlated candidate prefixes are not independent farms. This is retrospective cross-conformal verification, not prospective validation.'),scores

if __name__=='__main__':
 torch.set_num_threads(2)
 freezes=[P/'phase8b-train-model-freeze.json',P/'phase8b-ExtraTrees-freeze.json',P/'phase8b-ood-freeze.json']
 docs=[json.loads(p.read_text()) for p in freezes];assert docs[0]['all_models_frozen'] and len(docs[0]['files'])==72 and len(docs[1]['files'])==12 and len(docs[2]['files'])==2
 for path,digest in docs[0]['files'].items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==digest
 for ent in docs[1]['files']:assert hashlib.sha256((R/ent['path']).read_bytes()).hexdigest()==ent['sha256']
 for path,entry in docs[2]['files'].items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==entry['sha256']
 from pcse_gym.agromas_v8.data import validate_dev_books
 validate_dev_books(R)
 if not torch.cuda.is_available():raise RuntimeError('CUDA inference runtime unavailable')
 freeze_digest=hashlib.sha256(b''.join(p.read_bytes() for p in freezes)).hexdigest()
 if O.exists() or (P/'phase8b-dev-access-claim.json').exists():raise FileExistsError('Preserve prior Dev access/output; no repeated scoring')
 source_files=list((R/'NUE_PCSE-Gym/pcse_gym/agromas_v8').glob('*.py'))+list((R/'scripts').glob('phase8-*.py'))+[P/'phase8b-preregistered-protocol.json']
 source_digest={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
 with (P/'phase8b-G1-source-freeze.json').open('x') as f:json.dump(source_digest,f,indent=2)
 train_y=np.load(D/'y.npy');train_meta=json.loads((D/'meta.json').read_text());O.mkdir(exist_ok=False);x,y,meta=load_dev_once(R,freeze_digest);np.save(O/'actual.npy',y);(O/'meta.json').write_text(json.dumps(meta));results={}
 for track in ['Full-Telemetry','Sensorless']:
  ood=joblib.load(M/f'{track}-observable-ood.joblib');ood_score,applicable=ood.score(x)
  ood_summary={'samples':len(x),'applicable':int(applicable.sum()),'threshold':ood.threshold,'max_score':float(ood_score.max()),'no_exclusions_from_G1':True}
  (P/f'phase8b-Dev-{track}-OOD.json').write_text(json.dumps(ood_summary,indent=2))
  residual,oof=residuals(track,'ExtraTrees',train_y,train_meta);tree=marginal_members(x,meta,Predictor(track,'ExtraTrees'),residual);np.save(O/f'{track}-ExtraTrees-members.npy',tree)
  for arch in ['mlp','residual-mlp']:
   residual,oof=residuals(track,arch,train_y,train_meta);members=marginal_members(x,meta,Predictor(track,arch),residual);np.save(O/f'{track}-{arch}-members.npy',members)
   result,scores=metrics(members,y,meta,tree,train_y,train_meta);np.save(O/f'{track}-{arch}-conformal-scores.npy',scores);results[track+'-'+arch]=result;print(json.dumps({'track':track,'architecture':arch,**result}),flush=True)
 passed_arches=[a for a in ['mlp','residual-mlp'] if all(results[t+'-'+a]['passed'] for t in ['Full-Telemetry','Sensorless'])]
 verdict={'status':'G1_PASS' if passed_arches else 'G1_FAIL_HALT','passing_architectures':passed_arches,'results':results,'G2_executed':False,'G3_executed':False,'Dev_accesses':1,'no_Dev_hyperparameter_adjustment':True,'prediction_files':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in O.iterdir() if p.is_file()}}
 (P/'phase8b-G1-verdict.json').write_text(json.dumps(verdict,indent=2));print(verdict['status'],flush=True)
