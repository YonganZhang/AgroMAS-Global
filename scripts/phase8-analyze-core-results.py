"""Locked-case descriptive metrics and paired case-level inference, no tuning."""
from pathlib import Path
import json,hashlib
import numpy as np,pandas as pd
from scipy.stats import binomtest,rankdata
from itertools import product
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';B=5000;SEED=20261115

def paired(a,b,metric):
 keys=['region','year'];z=a[keys+[metric]].merge(b[keys+[metric]],on=keys,suffixes=('_a','_b'),validate='one_to_one');delta=(z[metric+'_a']-z[metric+'_b']).to_numpy(float).copy();tolerance=1e-12 if metric in ('joint','NUE_gt_090') else 1e-9;delta[np.abs(delta)<=tolerance]=0.;n=len(delta)
 if not n:return None
 rng=np.random.default_rng(SEED);boot=delta[rng.integers(n,size=(B,n))].mean(1);nonzero=delta[delta!=0];sign=float(binomtest(int((nonzero>0).sum()),len(nonzero),.5).pvalue) if len(nonzero) else 1.;
 if len(nonzero):
  ranks=rankdata(np.abs(nonzero),method='average');observed=float(ranks[nonzero>0].sum());center=float(ranks.sum()/2);null=np.array(list(product((0.,1.),repeat=len(nonzero))))@ranks;wp=float(np.mean(np.abs(null-center)>=abs(observed-center)-1e-12))
 else:wp=1.
 return dict(n=n,n_eff_nonzero=len(nonzero),ties=int(n-len(nonzero)),mean_difference=float(delta.mean()),CI95=np.quantile(boot,[.025,.975]).tolist(),exact_two_sided_sign_p=sign,Wilcoxon_two_sided_p=wp,Wilcoxon_method='exact enumeration of2^n_eff signed-rank allocations; average tied ranks, zero differences removed',tie_absolute_tolerance=tolerance,bootstrap_draws=B,bootstrap_seed=SEED,NL_n5_minimum_exact_sign_p=.0625)

if __name__=='__main__':
 receipt=json.loads((P/'phase8b-native-campaign-receipt.json').read_text());assert not any(receipt['exit_codes']) and receipt['result_count']==receipt['expected'];rows=[];audits=[]
 for file in sorted((R/'data/phase8-locked-evaluation').glob('*/result.json')):
  r=json.loads(file.read_text());c=r['case'];m=r['outcome'];tiers=[v['tier'] for v in r['trace'] if v.get('tier') is not None and not v.get('deferred',False)];audits.append(r['mass_audit']);rows.append(c|dict(joint=float(r['joint']),partial_profit=r['partial_profit'],Yield=m[0],Grain_N=m[1],S_N=m[2],NUE=m[3],Executed_N=m[4],Native_N_loss=r['Native_N_loss'],NUE_gt_090=float(m[3]>.9),NUE_lt_050=float(m[3]<.5),surplus_compliant=float(r['surplus_compliant']),Tier1=sum(t==1 for t in tiers),Tier2=sum(t==2 for t in tiers),Tier3=sum(t==3 for t in tiers),decisions=len(tiers),episode_sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
 assert all(a['passed'] for a in audits)
 prior_usage=[]
 for file in sorted((R/'data/phase8-locked-evaluation').glob('*/result.json')):
  result=json.loads(file.read_text());case=result['case']
  if case['benchmark']!='P2':continue
  decisions=[t for t in result['trace'] if t.get('prior_accepted') is not None];prior_usage.append({k:case[k] for k in ('scheme','policy','cohort','region','year')}|dict(decisions=len(decisions),prior_accepted=sum(t['prior_accepted'] for t in decisions),prior_timing_admissible=sum(t['prior_timing_admissible'] for t in decisions),prior_ood=sum(t['prior_ood'] for t in decisions),effective_radii=[t['radius'] for t in decisions]))
 frame=pd.DataFrame(rows);frame['scheme']=frame.get('scheme',pd.Series(index=frame.index,dtype=str)).fillna('none');frame['fold']=frame.get('fold',pd.Series(index=frame.index,dtype=str)).fillna('none');frame.to_csv(P/'phase8b-native-episode-metrics.csv',index=False)
 group=['benchmark','source','cohort','scheme','region','year','policy','track','cap','price_multiplier','subsidy','tax'];metrics=['joint','partial_profit','Yield','Grain_N','S_N','NUE','Executed_N','Native_N_loss','NUE_gt_090','NUE_lt_050','surplus_compliant','Tier1','Tier2','Tier3','decisions']
 # All three fixed PPO seeds receive equal weight within the same site-year.
 annual=frame.groupby(group,dropna=False)[metrics].mean().reset_index();annual.to_csv(P/'phase8b-case-metrics-seed-averaged.csv',index=False)
 extremes={(v['region'],v['year']) for v in json.loads((P/'phase8b-locked-campaign-cases.json').read_text())['extreme_cohort']};subset=annual[(annual.benchmark=='P1')&(annual.policy=='TreeMLP')&(annual.track=='Sensorless')&(annual.cap==40)&(annual.price_multiplier==1)&(annual.subsidy==0)&annual.apply(lambda row:(row.region,row.year) in extremes,axis=1)].copy();subset['policy']='TreeMLP-extreme-subset';annual=pd.concat([annual,subset],ignore_index=True)
 summary=[];keys=[k for k in group if k not in ('region','year')]
 for key,g in annual.groupby(keys,dropna=False):
  regional=g.groupby('region')[metrics].mean();summary.append(dict(zip(keys,key))|dict(site_years=len(g),regions=len(regional),pooled=g[metrics].mean().to_dict(),region_equal=regional.mean().to_dict(),by_region={name:dict(n=len(g[g.region==name]))|row.to_dict() for name,row in regional.iterrows()},fallback_decision_weighted={f'Tier{i}':float(g[f'Tier{i}'].sum()/g.decisions.sum()) if g.decisions.sum() else None for i in (1,2,3)}))
 contrasts=[]
 for benchmark in annual.benchmark.unique():
  q=annual[annual.benchmark==benchmark]
  contextkeys=['source','cohort','scheme','cap','price_multiplier','subsidy','tax','track']
  for context,g in q.groupby(contextkeys,dropna=False):
   policies=set(g.policy);primary='P2-Full64' if benchmark=='P2' else 'TreeMLP'
   if primary not in policies:continue
   for reference in sorted(policies-{primary,'TreeMLP-extreme-subset'}):
    for region in ('netherlands_lelystad','usa_kansas_wichita','australia_wa_perth'):
     a=g[(g.policy==primary)&(g.region==region)];b=g[(g.policy==reference)&(g.region==region)]
     for metric in ('joint','partial_profit','Native_N_loss','NUE_gt_090'):
      result=paired(a,b,metric)
      if result:contrasts.append(dict(zip(contextkeys,context))|dict(benchmark=benchmark,region=region,primary=primary,reference=reference,metric=metric)|result)
 # Explicit Holm adjustment across the entire reported exploratory family.
 if contrasts:
  pvals=np.array([c['exact_two_sided_sign_p'] for c in contrasts]);order=np.argsort(pvals);adjusted=np.minimum(1,np.maximum.accumulate((len(order)-np.arange(len(order)))*pvals[order]))
  for i,value in zip(order,adjusted):contrasts[int(i)]['Holm_sign_p_full_exploratory_family']=float(value)
 result=dict(summary=summary,contrasts=contrasts,prior_usage=prior_usage,matched_climate_extreme_baseline='TreeMLP-extreme-subset is an alias restricted to exactly the34TRAIN-quantile extreme site-years; no extra physical runs',bootstrap=dict(B=B,seed=SEED,unit='site-year after within-case PPO seed averaging'),statistical_scope='exploratory adaptive-reused P1; retrospective nested P2; NASA/WUR and Former/Public and LOYO/LORO never pooled',mass=dict(native_runs=len(audits),daily_records=sum(a['daily_rows'] for a in audits),all_passed=True,max_N=max(a['max_abs_N_residual_kg_ha'] for a in audits),max_C=max(a['max_abs_C_residual_kg_ha'] for a in audits)),physical_grid_ceilings=dict(AU='11/11',US='12/12',NL='4/5 NASA',FR='1/12',CN='0/12;basal171'),ceiling_scope='old finite GRID enumeration under specified physics; not continuous field oracle',monolithic='exact pytest identity; no claimed organization effect')
 (P/'phase8b-core-statistics.json').write_text(json.dumps(result,indent=2,allow_nan=False));print(json.dumps(result['mass']),flush=True)
