"""Cross-fitted observable-only imputation with unchanged frozen Phase6 action selector."""
from pathlib import Path
import json,hashlib,time,resource
import numpy as np,pandas as pd,joblib,yaml
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from pcse_gym.agromas.features import shared_features
from pcse_gym.agromas_v6.core import Policy,GRID,statistics,select_objective
from pcse_gym.agromas_v6.books import PLANS,FACTORS
from pcse_gym.agromas_v6.training import predict_stats
from pcse_gym.agromas_v7.bridge import features,reconstruct,prior_year,HIDDEN
R=Path(__file__).resolve().parents[1];P=R/'reports/phase7';M=R/'models/phase7';D=R/'data/phase7-alphaearth-v1';REGIMES=['Weather_only','Static_soil','Satellite_bridge']
def static_prior(region):
 if region=='netherlands_lelystad':s=yaml.safe_load((R/'NUE_PCSE-Gym/pcse_gym/envs/configs/soil/arminda_soil.yaml').read_text())
 else:s=json.loads((R/f'reports/phase5/regional-model-inputs/{region}/soil-v1.json').read_text())
 return float(s['SoilProfileDescription']['SoilLayers'][0]['FSOMI'])
def worlds():
 out=[]
 for folder,role in [('data/phase5-teachers-v2','Train'),('data/phase5-final-evaluation-books-v4','Evaluation')]:
  for f in sorted((R/folder).glob('*-Historical*.jsonl')):
   rows=[json.loads(x) for x in f.read_text().splitlines()];first=rows[0];book={tuple(x['plan']):x for x in rows};key=(first['region_id'],int(first['harvest_year']));prefix=[]
   for stage in (1,2,3):
    for ix in range(0,343,7**(4-stage)):
     row=book[tuple(PLANS[ix])]
     if str(stage) not in row['states']:continue
     state=row['states'][str(stage)];base=np.array(row['features'][str(stage)]) if 'features' in row else shared_features(str(R),state)
     prefix.append((stage,ix,base))
   out.append(dict(region=key[0],year=key[1],train=role=='Train',source_role=first['role'],book=book,prefix=prefix,prior_SOM=static_prior(key[0])))
 return out

def fit_models(ws,aef,scheme,group):
 train=[w for w in ws if (w['year'] if scheme=='LOYO' else w['region'])!=group];assert train
 fitted={}
 for regime in REGIMES:
  X=[];Y=[];weights=[]
  for w in train:
   sat=prior_year(aef,w['region'],w['year']) if not w['train'] and w['year']>=2018 else None
   for stage,ix,base in w['prefix']:
    prior=np.r_[base[19:22],w['prior_SOM']];X.append(features(base,regime,prior,sat));Y.append(base[list(HIDDEN)]);weights.append(1/len(w['prefix']))
  X=np.array(X);Y=np.array(Y);weight=np.array(weights);scale=StandardScaler().fit(X,sample_weight=weight);model=Ridge(alpha=100).fit(scale.transform(X),Y,sample_weight=weight);fitted[regime]=(scale,model)
 return fitted,[(w['region'],w['year']) for w in train]

def episode(w,regime,fitted,aef,models):
 index=0;trace=[];errors=[];sat=prior_year(aef,w['region'],w['year']);lookup={(stage,ix):base for stage,ix,base in w['prefix']};policy=Policy();timing=[]
 for stage in (1,2,3):
  if (stage,index) not in lookup:continue
  full=lookup[(stage,index)];effective='Static_soil' if regime=='Satellite_bridge' and sat is None else regime;start=time.perf_counter_ns();prior=np.r_[full[19:22],w['prior_SOM']];x=features(full,effective,prior,sat);scale,reg=fitted[effective];hidden=reg.predict(scale.transform(x[None]))[0];base=reconstruct(full,hidden);legal=full[3]+GRID<=220+1e-8
  inputs=np.c_[np.repeat(base[None],7,axis=0),GRID];stats=predict_stats(models[stage],inputs,legal);choice,diag=select_objective(stats,legal,40.,1.,0.,policy);choice=int(choice);timing.append((time.perf_counter_ns()-start)/1e6)
  # Counterfactual masking audit: inaccessible labels cannot change runtime features.
  changed=full.copy();changed[list(HIDDEN)]+=1234;changed[10:15]+=567;np.testing.assert_array_equal(x,features(changed,effective,prior,sat));np.testing.assert_array_equal(base,reconstruct(changed,hidden))
  errors.append(dict(stage=stage,observed=full[list(HIDDEN)].tolist(),predicted=hidden.tolist()));trace.append(dict(stage=stage,chosen=float(GRID[choice]),predicted_surplus=float(stats[choice,2]),tier=int(diag['tier']),allowed=diag['allowed'].tolist(),satellite_input_year=w['year']-1 if sat is not None else None,missing_satellite=sat is None,effective_regime=effective));index+=choice*FACTORS[stage-1]
 physical=w['book'][tuple(PLANS[index])];m=physical['outcome'];ok=bool(.5<=m[3]<=.9 and 0<=m[2]<=40);stock=physical.get('stock_diagnostics',{});assert abs(stock['soil_N_mass_balance_residual_kg_ha'])<1e-10 and abs(stock['soil_C_mass_balance_residual_kg_ha'])<1e-9
 return dict(region=w['region'],year=w['year'],cohort='Former-Held-Out' if w['source_role']=='Held-Out' else 'Public-Reused',regime=regime,has_prior_year_satellite=sat is not None,joint=float(ok),partial_profit=float(200*m[0]-1.5*m[4]),applied_N=float(m[4]),plan=PLANS[index].tolist(),trace=trace,state_errors=errors,decision_latency_ms=timing,native_daily_rollouts=0)

def summary(results):
 flat=pd.DataFrame([{k:x[k] for k in ['scheme','region','year','cohort','regime','has_prior_year_satellite','joint','partial_profit','applied_N']} for x in results]);old=pd.read_csv(R/'reports/phase6/annual-policy-metrics-v6.csv');old=old[(old.climate=='Historical')&(old.cap==40)&(old.price_multiplier==1)&(old.subsidy==0)&old.policy.isin(['Phase6-Full','PPO-v6-structured-book'])]
 for scheme in ('LOYO','LORO'):
  for policy,label in [('Phase6-Full','Full_telemetry_reference'),('PPO-v6-structured-book','PPO_telemetry_reference')]:
   q=old[old.policy==policy][['region_id','year','cohort','joint','partial_profit','fertN']].rename(columns={'region_id':'region','fertN':'applied_N'});q['scheme']=scheme;q['regime']=label;q['has_prior_year_satellite']=q.year>=2018;flat=pd.concat([flat,q],ignore_index=True)
 flat.to_csv(P/'bridge-annual-metrics-v7.csv',index=False)
 records=[];contrasts=[]
 for window,mask in [('mixed2017_2021',flat.year.between(2017,2021)),('prior2018_2021',flat.year.between(2018,2021)),('prior2018_2026',flat.year.between(2018,2026)),('mixed_full59',flat.year.between(2015,2026))]:
  for (scheme,regime,stratum),g in flat[mask].groupby(['scheme','regime','cohort']):
   records.append(dict(window=window,scheme=scheme,regime=regime,stratum=stratum,n=len(g),regions=g.region.nunique(),**{v:float(g.groupby('region')[v].mean().mean()) for v in ['joint','partial_profit','applied_N']}))
  for (scheme,regime),g in flat[mask].groupby(['scheme','regime']):records.append(dict(window=window,scheme=scheme,regime=regime,stratum='Explicit_combined_regions',n=len(g),regions=g.region.nunique(),**{v:float(g.groupby('region')[v].mean().mean()) for v in ['joint','partial_profit','applied_N']}))
  # Pair by exact region/year, retaining equal-region macro weights and synchronous-year draws.
  for scheme in ('LOYO','LORO'):
   subset=flat[mask&(flat.scheme==scheme)]
   for regime in REGIMES+['PPO_telemetry_reference']:
    ref=subset[subset.regime=='Full_telemetry_reference'];q=subset[subset.regime==regime].merge(ref,on=['region','year','cohort'],suffixes=('_a','_b'));regions=sorted(q.region.unique());years=np.sort(q.year.unique());rng=np.random.default_rng(20261115);values=q[[v+'_a' for v in ['joint','partial_profit','applied_N']]].to_numpy()-q[[v+'_b' for v in ['joint','partial_profit','applied_N']]].to_numpy();draws=[]
    while len(draws)<5000:
     picked=rng.choice(years,len(years),replace=True);weights=np.array([(picked==y).sum() for y in q.year]);means=[]
     for region in regions:
      ix=q.region.to_numpy()==region
      if not weights[ix].sum():break
      means.append(np.average(values[ix],axis=0,weights=weights[ix]))
     if len(means)==len(regions):draws.append(np.mean(means,axis=0))
    point=np.mean([values[q.region.to_numpy()==r].mean(0) for r in regions],axis=0);ci=np.quantile(draws,[.025,.975],axis=0);contrasts.append(dict(window=window,scheme=scheme,regime=regime,reference='Full_telemetry_reference',n=len(q),seed=20261115,draws=5000,metrics={v:dict(difference=float(point[j]),CI95=ci[:,j].tolist()) for j,v in enumerate(['joint','partial_profit','applied_N'])}))
 (P/'bridge-comparison-statistics-v7.json').write_text(json.dumps(dict(summary=records,paired_contrasts=contrasts,scope='Retrospective OOF diagnostic; input-timestamp prior-year causality only, not historical model/product availability; both restricted state and region-ID telemetry removed; fixed frozen controller was trained with those coordinates, so distribution shift remains'),indent=2))
if __name__=='__main__':
 a=pd.read_csv(P/'station-mean-64d-v7.csv');aef={(x.region,int(x.embedding_year)):np.array([getattr(x,f'A{j:02}') for j in range(64)]) for x in a.itertuples()};ws=worlds();assert sum(not w['train'] for w in ws)==59;models={s:joblib.load(R/f'models/phase6/r2/Full/stage-{s}.joblib') for s in (1,2,3)};results=[];fits=[]
 for scheme in ('LOYO','LORO'):
  groups=sorted({w['year'] if scheme=='LOYO' else w['region'] for w in ws if not w['train']})
  for group in groups:
   fitted,keys=fit_models(ws,aef,scheme,group);test=[w for w in ws if not w['train'] and (w['year'] if scheme=='LOYO' else w['region'])==group];assert all((year!=group if scheme=='LOYO' else region!=group) for region,year in keys);joblib.dump(fitted,M/f'bridge-imputers-{scheme}-{group}.joblib');fits.append(dict(scheme=scheme,held_group=group,fit_site_years=keys,test_site_years=[(w['region'],w['year']) for w in test],alpha=100))
   for w in test:
    for regime in REGIMES:row=episode(w,regime,fitted,aef,models);row['scheme']=scheme;results.append(row)
   print(scheme,group,'completed',len(results),flush=True)
 (P/'bridge-policy-results-v7.json').write_text(json.dumps(results,indent=2));(P/'bridge-crossfit-provenance-v7.json').write_text(json.dumps(fits,indent=2));summary(results)
