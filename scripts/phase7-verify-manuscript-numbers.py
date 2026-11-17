"""Independently reconcile manuscript claims with preserved raw metrics and group-CV outputs."""
from pathlib import Path
import json,re,hashlib,numpy as np,pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
R=Path(__file__).resolve().parents[1];P=R/'reports/phase7';O=R/'manuscript/phase7'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def macro(d,key):return float(d.groupby('region_id')[key].mean().mean())
def check_close(a,b):assert np.isclose(a,b,rtol=1e-10,atol=1e-9),(a,b)
if __name__=='__main__':
 import subprocess;subprocess.run(['python',str(R/'scripts/phase7-document-claim-guard.py')],check=True)
 facts=json.loads((P/'core-facts-v7.json').read_text());annual=pd.read_csv(R/'reports/phase6/annual-policy-metrics-v6.csv');primary=annual[(annual.climate=='Historical')&(annual.cap==40)&(annual.price_multiplier==1)&(annual.subsidy==0)&(annual.cohort=='Former-Held-Out')]
 for policy,metrics in facts['policy_primary'].items():
  for key,value in metrics.items():check_close(value,macro(primary[primary.policy==policy],key))
 for path,digest in facts['sources'].items():assert sha(R/path)==digest,path
 registry=json.loads((P/'manuscript-claim-registry-v7.json').read_text());documents={l:(O/f'MANUSCRIPT_{l}.md').read_text() for l in ['EN','ZH']};tex=(O/'main.tex').read_text();checks=[]
 for key,record in registry.items():
  value=json.loads((R/record['source']).read_text())
  for part in record['path']:value=value[part]
  display=f"{value*record['multiplier']:.{record['decimals']}f}";assert display==record['display']
  for lang,text in documents.items():assert display in text.replace('−','-'),(key,lang,display)
  assert display in tex.replace('−','-'),(key,'TeX',display);checks.append(dict(key=key,display=display,source_path=record['path']))
 # Audit all literal outcome numbers, including values initially written as prose.
 expected=[]
 def outcome(value,digits=2):expected.append(f'{value:.{digits}f}')
 full=primary[primary.policy=='Phase6-Full'];old=primary[primary.policy=='Phase5-A4'];ppo=primary[primary.policy=='PPO-v6-structured-book'];outcome(100*(macro(full,'joint')-macro(old,'joint')));outcome(100*(macro(full,'joint')-macro(ppo,'joint')));outcome(macro(full,'fertN')-macro(old,'fertN'));outcome(macro(old,'partial_profit')-macro(full,'partial_profit'))
 stat6=json.loads((R/'reports/phase6/benchmark-statistics-v6.json').read_text())
 for metric,mult in [('joint',100),('partial_profit',1)]:
  contrast=next(x for x in stat6['contrasts'] if x['reference']=='PPO-v6-structured-book' and x['metric']==metric)
  for value in contrast['year_cluster_CI95']:outcome(mult*value)
 select=json.loads((R/'reports/phase6/r2/policy-train-selection-v6.json').read_text());outcome(100*select['selected']['macro_joint'])
 for reg in ['netherlands_lelystad','australia_wa_perth','usa_kansas_wichita']:
  outcome(100*full[full.region_id==reg].joint.mean())
 nl=primary[primary.region_id=='netherlands_lelystad'];outcome(100*nl[nl.policy=='PPO-v6-structured-book'].joint.mean())
 for policy in ['Phase6-LOAO-economics','Phase6-LOAO-soil-mining-guard','Phase6-LOAO-surplus-filter']:outcome(100*macro(primary[primary.policy==policy],'joint'))
 for policy,col in [('Phase6-Full','stock_soil_N_stock_drawdown_kg_ha'),('Phase6-Full','stock_native_published_leaching_plus_denitrification_kg_ha'),('Phase6-Full','stock_upper_boundary_export_not_in_published_loss_kg_ha'),('Phase5-A4','stock_native_published_leaching_plus_denitrification_kg_ha'),('Phase5-A4','stock_upper_boundary_export_not_in_published_loss_kg_ha')]:outcome(macro(primary[primary.policy==policy],col))
 # Numeric table values are independently tied to actual raw policy metrics.
 for policy in ['Phase5-A4','PPO-v6-structured-book','Phase6-Full','DVS-N2']:
  for col,mult in [('joint',100),('partial_profit',1),('fertN',1)]:outcome(mult*macro(primary[primary.policy==policy],col))
 cosine=np.array(facts['cosine']['cosine_matrix']);off=cosine[~np.eye(5,dtype=bool)]
 for value in [np.diag(cosine).min(),np.diag(cosine).max(),off.min(),off.max()]:outcome(value)
 for x in expected:
  variants={x,x.rstrip('0').rstrip('.') if '.' in x else x};assert any(re.search(r'(?<![0-9.])'+re.escape(v)+r'(?![0-9]|\.[0-9])',documents['EN'].replace('−','-')) for v in variants),('Expected raw-derived claim absent from EN',x)
 # Independently recompute the newly disclosed state-reconstruction values from saved errors.
 records=json.loads((P/'bridge-policy-results-v7.json').read_text())
 state=json.loads((P/'state-reconstruction-v7.json').read_text())
 for r in state:
  errors=[e for q in records if q['scheme']==r['scheme'] and q['regime']==r['regime'] and 2018<=q['year']<=2026 for e in q['state_errors'] if e['stage']==r['stage']]
  j=['LAI','soil_moisture','crop_N_uptake'].index(r['target']);y=np.array([e['observed'][j] for e in errors]);pr=np.array([e['predicted'][j] for e in errors]);check_close(float(np.sqrt(np.mean((y-pr)**2))),r['RMSE']);check_close(float(1-np.sum((y-pr)**2)/np.sum((y-y.mean())**2)),r['R2'])
 # Complete OOF table must agree with all320 published point statistics.
 predictions=pd.read_csv(P/'decoding-OOF-predictions-v7.csv');stats=json.loads((P/'decoding-nested-statistics-v7.json').read_text())['results'];assert len(stats)==320
 for row in stats:
  q=predictions[(predictions.window==row['window'])&(predictions.model==row['model'])&(predictions.scheme==row['scheme'])&(predictions.target==row['target'])];assert len(q)==row['n'];y=q.observed.to_numpy();pr=q.predicted.to_numpy();den=((y-y.mean())**2).sum();check_close(np.sqrt(((y-pr)**2).mean()),row['RMSE'])
  if den>1e-14:check_close(1-((y-pr)**2).sum()/den,row['R2'])
  for mode,v in row['permutations'].items():
   assert v['draws']==5000 and 0<=v['p']<=v['Holm_p']<=1
   if mode=='region_blocks':assert v['p']>=1/120-1e-12 and abs(v['p']*120-round(v['p']*120))<1e-9 and v['p']==v['exact_block_p']
 # Independent sklearn refits for a real44-row prior-year mineralization assay.
 physical=pd.read_csv(P/'physical-targets-v7.csv');q=physical[physical.year.between(2018,2026)].reset_index(drop=True);aef=pd.read_csv(P/'station-mean-64d-v7.csv');base=['latitude','longitude']+[f'prefix_weather_{i}' for i in range(4)]+['doy_sin','doy_cos'];X=np.c_[q[base].to_numpy(),np.array([aef[(aef.region==r.region)&(aef.embedding_year==r.year-1)][[f'A{i:02}' for i in range(64)]].to_numpy()[0] for r in q.itertuples()])];Y=q.mineralization.to_numpy();groups=q.year.to_numpy();pred=np.empty(len(q));alphas=[.1,1,10,100,1000]
 for outer in np.unique(groups):
  train=np.flatnonzero(groups!=outer);test=np.flatnonzero(groups==outer);errors=[]
  for alpha in alphas:
   err=[]
   for inner in np.unique(groups[train]):
    fit=train[groups[train]!=inner];valid=train[groups[train]==inner];scale=StandardScaler().fit(X[fit]);model=Ridge(alpha=alpha).fit(scale.transform(X[fit]),Y[fit]);err.append(np.mean((model.predict(scale.transform(X[valid]))-Y[valid])**2))
   errors.append(np.mean(err))
  scale=StandardScaler().fit(X[train]);model=Ridge(alpha=alphas[int(np.argmin(errors))]).fit(scale.transform(X[train]),Y[train]);pred[test]=model.predict(scale.transform(X[test]))
 recorded=predictions[(predictions.window=='prior2018_2026')&(predictions.model=='Prior_year')&(predictions.scheme=='LOYO')&(predictions.target=='mineralization')];compare=q[['region','year']].merge(recorded,on=['region','year']);np.testing.assert_allclose(pred,compare.predicted,rtol=1e-9,atol=1e-8)
 # The full deployment assay has no duplicate site-year/policy keys.
 b=pd.read_csv(P/'bridge-annual-metrics-v7.csv');assert not b.duplicated(['scheme','region','year','cohort','regime']).any()
 for row in facts['bridge']['summary']:
  windows={'mixed2017_2021':(2017,2021),'prior2018_2021':(2018,2021),'prior2018_2026':(2018,2026),'mixed_full59':(2015,2026)};lo,hi=windows[row['window']];g=b[b.year.between(lo,hi)&(b.scheme==row['scheme'])&(b.regime==row['regime'])]
  if row['stratum']!='Explicit_combined_regions':g=g[g.cohort==row['stratum']]
  assert len(g)==row['n']
  for key in ['joint','partial_profit','applied_N']:check_close(g.groupby('region')[key].mean().mean(),row[key])
 # Structural literals are separately classified, never mistaken for model estimates.
 known=set(expected+[x['display'] for x in registry.values()]);known|={str(x) for x in range(0,301)}|{'320','343','486','500','640','1000','1024','2010','2014','2015','2016','2017','2018','2019','2020','2021','2022','2024','2025','2026','1995','2009','5000','151552','0.1','0.50','0.90','0.95','0.99','0.11','0.62','0.5','0.9','1.5','4.0','81.92'}
 known|={'-3.445','0.216','-2.614'};known|={v.lstrip('-') for v in known};unknown={}
 for lang,text in documents.items():
  text=re.sub(r'!\[[^\]]*\]\([^)]*\)\{[^}]*\}','',text);text=re.sub(r'\[@[^]]*\]','',text);text=re.sub(r'^#+.*$','',text,flags=re.M);text=text.replace('−','-');tokens=re.findall(r'(?<![A-Za-z0-9])[-+]?\d+(?:\.\d+)?(?:e-?\d+)?',text);unknown[lang]=sorted(set(x for x in tokens if x not in known and x.lstrip('-') not in known))
 assert not unknown['EN'] and not unknown['ZH'],unknown
 main_en=documents['EN'].split('## Supplementary information')[0];clean=re.sub(r'!\[[^]]*\]\([^)]*\)\{[^}]*\}','',main_en);assert not re.search(r'\bv[467]\b|phase[67]|32767|\.json|\.py|\bWe\b|\bOur\b',clean,re.I);assert '**' not in clean
 abstract=main_en.split('## Abstract\n\n')[1].split('\n\n## 1 ')[0];assert 160<=len(abstract.split())<=200;assert len(re.split(r'(?<!\d)\.(?=\s+[A-Z]|$)',abstract.strip()))-1==5
 (P/'manuscript-number-verification-v7.json').write_text(json.dumps(dict(status='passed',registered_claims=checks,all_literal_outcome_numbers_independently_recomputed=expected,unknown_numeric_literals=unknown,OOF_point_rows_verified=320,actual_sklearn_nested_refit_n=44,max_abs_nested_refit_difference=float(np.max(abs(pred-compare.predicted))),deployment_summary_rows_verified=len(facts['bridge']['summary']),abstract_words=len(abstract.split()),documents_sha256={str((O/f'MANUSCRIPT_{l}.md').relative_to(R)):sha(O/f'MANUSCRIPT_{l}.md') for l in ['EN','ZH']},TeX_sha256=sha(O/'main.tex')),indent=2));print('Verified registered source-derived values and OOF statistics; semantic claim binding is separately guarded by phase7-document-claim-guard.py')
