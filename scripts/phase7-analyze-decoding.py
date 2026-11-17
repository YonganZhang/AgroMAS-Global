"""Nested group-CV physical probes with complete5000-draw permutation refits."""
from pathlib import Path
import json,hashlib,itertools,time,sys
import numpy as np,pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr
from pcse_gym.agromas_v7.validation import nested_maps,predict_nested,permutations,r2
R=Path(__file__).resolve().parents[1];P=R/'reports/phase7';D=R/'data/phase7-alphaearth-v1';M=R/'models/phase7';SEED=20261115
TARGETS=['mineralization','zeroN_grainN','upper_export','NLOSSCUM','feasible_fraction','corridor_width','optimal_total_N','harvest_grain_DM','harvest_grain_N','marginal_profit_sensitivity']
BASE=['latitude','longitude']+[f'prefix_weather_{j}' for j in range(4)]+['doy_sin','doy_cos']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def embeddings():
 rows=[]
 for meta in sorted(D.glob('*-20??.json')):
  d=json.loads(meta.read_text());a=np.load(D/d['npz_file']);v=a['station_embedding'][a['station_valid']].astype(float);x=v.mean(0)
  rows.append(dict(region=d['site'],embedding_year=int(d['year']),**{f'A{j:02}':x[j] for j in range(64)}))
 df=pd.DataFrame(rows);assert len(df)==45;return df

def model_inputs(df,aef,mode):
 x=df[BASE].to_numpy();axes=[f'A{j:02}' for j in range(64)];v=[]
 if mode=='Climate_coordinates':return x
 for row in df.itertuples():
  a=aef[aef.region==row.region].sort_values('embedding_year')
  if mode=='Persistent_retrospective':z=a[axes].mean().to_numpy()
  elif mode=='Same_year_retrospective':z=a.loc[a.embedding_year==row.year,axes].to_numpy()[0]
  elif mode=='Prior_year':z=a.loc[a.embedding_year==row.year-1,axes].to_numpy()[0]
  elif mode=='Prior_anomaly':
   last=a.loc[a.embedding_year==row.year-1,axes].to_numpy()[0];earlier=a.loc[a.embedding_year<row.year-1,axes];z=last-earlier.mean().to_numpy() if len(earlier) else np.zeros(64)
  else:raise ValueError(mode)
  v.append(z)
 return np.c_[x,v]

def holm(p):
 p=np.asarray(p);order=np.argsort(p);adjusted=np.maximum.accumulate((len(p)-np.arange(len(p)))*p[order]);out=np.empty(len(p));out[order]=np.minimum(1,adjusted);return out

def run_window(df,aef,name,modes,balanced):
 Y=df[TARGETS].to_numpy();reg=df.region.to_numpy();years=df.year.to_numpy();records=[];predictions=[]
 nulls={'within_region':permutations(reg,years,5000,SEED,'within_region')}
 if balanced:nulls['region_blocks']=permutations(reg,years,5000,SEED,'region_blocks')
 for mode in modes:
  X=model_inputs(df,aef,mode)
  for scheme,groups in [('LOYO',years),('LORO',reg)]:
   start=time.perf_counter();maps=nested_maps(X,groups);pred,chosen=predict_nested(maps,Y);observed=r2(Y,pred);tests={}
   for null,indices in nulls.items():
    exact_indices=None
    if null=='region_blocks':
     rr=np.unique(reg);exact_indices=np.array([[int(np.flatnonzero((reg==dict(zip(rr,donor))[reg[i]])&(years==years[i]))[0]) for i in range(len(df))] for donor in itertools.permutations(rr)]).T;assert exact_indices.shape==(len(df),120)
    # Refit every nested alpha selector for every target and permuted draw.
    all_y=np.concatenate([Y[:,None,:],Y[indices]]+([Y[exact_indices]] if exact_indices is not None else []),axis=1).reshape(len(df),-1);all_p,_=predict_nested(maps,all_y);null_r2=r2(all_y,all_p).reshape(5121 if exact_indices is not None else 5001,len(TARGETS));np.testing.assert_allclose(null_r2[0],observed,rtol=1e-10,atol=1e-10,equal_nan=True)
    mc=(1+(null_r2[1:5001]>=observed[None,:]-1e-12).sum(axis=0))/5001;mc=np.where(np.isfinite(observed),mc,1.);unique=np.unique(indices.T,axis=0);exact=np.where(np.isfinite(observed),(null_r2[5001:]>=observed[None,:]-1e-12).mean(axis=0),1.) if exact_indices is not None else None;p=exact if exact is not None else mc;tests[null]=dict(p=p,mc=mc,holm=holm(p),exact=exact,unique_permutations=int(len(unique)),null_r2_quantiles=np.nanquantile(null_r2[1:5001],[.025,.5,.975],axis=0))
   for j,target in enumerate(TARGETS):
    y=Y[:,j];pr=pred[:,j];center_y=y.copy();center_p=pr.copy()
    for rr in np.unique(reg):ix=reg==rr;center_y[ix]-=y[ix].mean();center_p[ix]-=pr[ix].mean()
    correlation=float(pearsonr(y,pr).statistic) if np.std(y)>1e-12 and np.std(pr)>1e-12 else None
    result=dict(window=name,model=mode,scheme=scheme,target=target,n=len(df),former_held_out=int((df.cohort=='Former-Held-Out').sum()),public_reused=int((df.cohort=='Public-Reused').sum()),R2=float(observed[j]) if np.isfinite(observed[j]) else None,RMSE=float(np.sqrt(np.mean((y-pr)**2))),r=correlation,within_region_R2=float(r2(center_y,center_p)) if np.std(center_y)>1e-10 else None,between_region_variance_fraction=float(np.var([y[reg==rr].mean() for rr in np.unique(reg)])/np.var(y)) if np.var(y)>1e-12 else None,selected_alpha_by_outer_fold=[float((.1,1,10,100,1000)[k[j]]) for k in chosen],permutations={null:dict(p=float(v['p'][j]),Holm_p=float(v['holm'][j]),draws=5000,Monte_Carlo_p=float(v['mc'][j]),exact_block_p=float(v['exact'][j]) if v['exact'] is not None else None,unique_draws=v['unique_permutations'],null_R2_quantiles=[float(z) if np.isfinite(z) else None for z in v['null_r2_quantiles'][:,j]]) for null,v in tests.items()});result['stratum_metrics']={cohort:dict(n=int((df.cohort==cohort).sum()),R2=float(r2(y[df.cohort==cohort],pr[df.cohort==cohort])) if np.std(y[df.cohort==cohort])>1e-10 else None,RMSE=float(np.sqrt(np.mean((y[df.cohort==cohort]-pr[df.cohort==cohort])**2)))) for cohort in df.cohort.unique()};result['fold_metrics']=[dict(held_group=str(group),n=int((groups==group).sum()),RMSE=float(np.sqrt(np.mean((y[groups==group]-pr[groups==group])**2)))) for group in np.unique(groups)];records.append(result)
    for i,row in df.reset_index(drop=True).iterrows():predictions.append(dict(window=name,model=mode,scheme=scheme,target=target,region=row.region,year=int(row.year),cohort=row.cohort,observed=float(y[i]),predicted=float(pr[i])))
   print(name,mode,scheme,'seconds',time.perf_counter()-start,flush=True)
 return records,predictions
if __name__=='__main__':
 protocol=P/'ANALYSIS_PROTOCOL_V7.json';aef=embeddings();aef.to_csv(P/'station-mean-64d-v7.csv',index=False);physical=pd.read_csv(P/'physical-targets-v7.csv');records=[];preds=[]
 windows=[('overlap2017_2021',physical[physical.year.between(2017,2021)],['Climate_coordinates','Persistent_retrospective','Same_year_retrospective'],True),('overlap2017_2025',physical[physical.year.between(2017,2025)],['Climate_coordinates','Persistent_retrospective','Same_year_retrospective'],True),('prior2018_2021',physical[physical.year.between(2018,2021)],['Climate_coordinates','Prior_year'],True),('prior2018_2026',physical[physical.year.between(2018,2026)],['Climate_coordinates','Prior_year'],False)]
 windows += [('prior_anomaly2019_2021',physical[physical.year.between(2019,2021)],['Climate_coordinates','Prior_anomaly'],True),('prior_anomaly2019_2026',physical[physical.year.between(2019,2026)],['Climate_coordinates','Prior_anomaly'],False),('prior_balanced2018_2025',physical[physical.year.between(2018,2025)],['Climate_coordinates','Prior_year'],True)]
 if '--postprocess-only' not in sys.argv:
  for name,df,modes,balanced in windows:
   a,b=run_window(df.reset_index(drop=True),aef,name,modes,balanced);records+=a;preds+=b
  pd.DataFrame(preds).to_csv(P/'decoding-OOF-predictions-v7.csv',index=False);(P/'decoding-nested-statistics-v7.json').write_text(json.dumps(dict(seed=SEED,draws=5000,protocol_sha256=sha(protocol),results=records,scope='Adaptive-Reused cross-fitted associations. Prior-year inputs do not make retrospective label fitting prospective.'),indent=2,allow_nan=False))
  # Full-data descriptive loadings are not OOF scores and cannot select a target/window.
  df=physical[physical.year.between(2017,2025)].reset_index(drop=True);X=model_inputs(df,aef,'Same_year_retrospective');sc=StandardScaler().fit(X);ys=df[TARGETS].to_numpy();ym=ys.mean(0);ystd=ys.std(0);ystd[ystd<1e-12]=1;fit=Ridge(alpha=100).fit(sc.transform(X),(ys-ym)/ystd)
  np.savez_compressed(M/'descriptive-linear-probes-v7.npz',Xmean=sc.mean_,Xscale=sc.scale_,coef=fit.coef_,intercept=fit.intercept_,Ymean=ym,Yscale=ystd)
  load=[]
  for i,target in enumerate(TARGETS):
   for j in range(64):load.append(dict(target=target,channel=f'A{j:02}',standardized_loading=float(fit.coef_[i,len(BASE)+j]),interpretation='Basis-dependent association, not channel physical identity or causal attribution'))
  pd.DataFrame(load).to_csv(P/'descriptive-channel-loadings-v7.csv',index=False)
 else:records=json.loads((P/'decoding-nested-statistics-v7.json').read_text())['results']
 matrices=[]
 for region in sorted(aef.region.unique()):
  v=aef[aef.region==region][[f'A{j:02}' for j in range(64)]].to_numpy(copy=True);v/=np.linalg.norm(v,axis=1,keepdims=True);dots=v@v.T;matrices.append(dict(region=region,within_site_interannual_cosine=float(dots[np.triu_indices(9,1)].mean())))
 (P/'cosine-stability-v7.json').write_text(json.dumps(matrices,indent=2));print('Completed',len(records),'target model/window/scheme results',flush=True)
