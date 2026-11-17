"""Descriptive adaptive benchmark, paired-year and stratified uncertainty."""
from pathlib import Path
import json,hashlib,itertools,argparse,numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];P=R/'reports/phase6'
ACTIVE=json.loads((P/'ACTIVE_TRAIN_RUN_V6.json').read_text());PROTOCOL=json.loads((R/ACTIVE['reports']/'TRAIN_PROTOCOL_V6.json').read_text());BOOTSTRAP_SEED=int(PROTOCOL['bootstrap_seed'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read_records():
 result=[]
 for version in (4,6):
  base=R/f'reports/phase{5 if version==4 else 6}';receipt=json.loads((base/f'final-policy-evaluation-receipt-v{version}.json').read_text());assert receipt['status']=='completed'
  for entry in receipt['files']:
   path=R/entry['path'];assert sha(path)==entry['sha256']
   for row in map(json.loads,path.read_text().splitlines()):
    policy=row['policy']
    if version==4:
     if policy=='PPO':policy='PPO-v4-'+row['information_mode']
     elif policy not in ('DVS-N2','N2-PA-calendar','Phase4-Forest-transfer'):policy='Phase5-'+policy
    role=row.get('source_role',row['role']);m=row['outcome'];s=row.get('stock_diagnostics',{});events=row.get('events',[])
    item=dict(region_id=row['region_id'],year=int(row['harvest_year']),climate=row['climate'],cohort='Former-Held-Out' if role=='Held-Out' else 'Public-Reused',policy=policy,cap=row['cap'],price_multiplier=row['price_multiplier'],subsidy=row['subsidy'],seed=row.get('seed'),physically_feasible_in_grid=float(row.get('physically_feasible_in_grid',float('nan'))),joint=float(.5<=m[3]<=.9 and 0<=m[2]<=row['cap']),partial_profit=float(200*m[0]-1.5*row['price_multiplier']*m[4]+row['subsidy']*bool(.5<=m[3]<=.9 and 0<=m[2]<=row['cap'])),source_partial_profit=row['partial_profit'],source_joint_definition_difference=float(bool(row['joint'])!=bool(.5<=m[3]<=.9 and 0<=m[2]<=row['cap'])),yield_tDM=m[0],grainN=m[1],surplus=m[2],NUE=m[3],fertN=m[4],nonfertN=m[5],**{f'dose{s}':sum(e['dose'] for e in events if e.get('stage')==s) for s in (1,2,3)})
    for k,v in s.items():
     if isinstance(v,(int,float)):item['stock_'+k]=v
    result.append(item)
 return pd.DataFrame(result)
KEYS=['region_id','year','climate','cohort','policy','cap','price_multiplier','subsidy']
def annualize(frame):return frame.groupby(KEYS,as_index=False).mean(numeric_only=True).drop(columns=['seed'],errors='ignore')
def main_primary(d):return d[(d.climate=='Historical')&(d.cap==40)&(d.price_multiplier==1)&(d.subsidy==0)&(d.cohort=='Former-Held-Out')]
def contrast(d,reference,metric,draws=5000):
 a=d[d.policy=='Phase6-Full'];b=d[d.policy==reference];v=a.merge(b,on=['region_id','year'],suffixes=('_a','_b'));v['delta']=v[metric+'_a']-v[metric+'_b'];regions=sorted(v.region_id.unique());rng=np.random.default_rng(BOOTSTRAP_SEED);details=[]
 for region in regions:
  x=v.loc[v.region_id==region,'delta'].to_numpy();boot=x[rng.integers(len(x),size=(draws,len(x)))].mean(1);signs=np.array(list(itertools.product((-1,1),repeat=len(x))));p=float(np.mean(np.abs((signs*x).mean(1))>=abs(x.mean())-1e-12));details.append(dict(region_id=region,n=len(x),mean=float(x.mean()),CI95=np.quantile(boot,[.025,.975]).tolist(),paired_signflip_p=p))
 point=float(v.groupby('region_id').delta.mean().mean());years=sorted(v.year.unique());matrix=v.pivot(index='year',columns='region_id',values='delta').reindex(index=years,columns=regions).to_numpy();boot=[];rejected=0
 while len(boot)<draws:
  sample=matrix[rng.integers(len(years),size=len(years))]
  if np.any(np.all(np.isnan(sample),axis=0)):rejected+=1;continue
  boot.append(float(np.nanmean(sample,axis=0).mean()))
 strat=[]
 arrays=[v.loc[v.region_id==r,'delta'].to_numpy() for r in regions]
 for _ in range(draws):strat.append(float(np.mean([x[rng.integers(len(x),size=len(x))].mean() for x in arrays])))
 return dict(reference=reference,metric=metric,scope='Adaptive-Reused Temporal Benchmark',regions=details,macro_equal_region_mean=point,year_cluster_CI95=np.quantile(boot,[.025,.975]).tolist(),year_cluster_union_years=len(years),rejected_empty_region_draws=rejected,region_stratified_CI95=np.quantile(strat,[.025,.975]).tolist(),region_stratified_assumes_independent_regions=True,draws=draws)
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--statistics-only',action='store_true',help='Recompute descriptive intervals from frozen annual aggregation; no policy inference');args=parser.parse_args()
 if args.statistics_only:d=pd.read_csv(P/'annual-policy-metrics-v6.csv',float_precision='round_trip')
 else:d=annualize(read_records());d.to_csv(P/'annual-policy-metrics-v6.csv',index=False)
 primary=main_primary(d);summary=[]
 for (policy,region),g in primary.groupby(['policy','region_id']):summary.append(dict(policy=policy,region_id=region,n_years=len(g),**{m:float(g[m].mean()) for m in ('joint','partial_profit','fertN','yield_tDM','surplus','NUE')}))
 contrasts=[]
 for ref in ('DVS-N2','Phase5-A4','PPO-v4-structured-shared','PPO-v6-structured-book')+tuple('Phase6-'+s for s in ('LOAO-climate','LOAO-surplus-filter','LOAO-soil-mining-guard','LOAO-core-state','LOAO-economics')):
  for metric in ('joint','partial_profit'):contrasts.append(contrast(primary,ref,metric))
 active=json.loads((P/'ACTIVE_TRAIN_RUN_V6.json').read_text());frozen=json.loads((R/active['reports']/'green-subsidy-TRAIN-freeze-v6.json').read_text());subsidy=[]
 for group in frozen['groups']:
  for rule,key in (('strict','strict_selected_subsidy'),('feasible','feasible_selected_subsidy')):
   sigma=group[key];base={k:group[k] for k in ('region_id','climate','cap','price_multiplier')}
   if sigma is None:subsidy.append(dict(**base,rule=rule,TRAIN_selected_subsidy=None,status='NoTRAINsolution;notreselected'));continue
   q=d[(d.policy=='Phase6-Full')&(d.cohort=='Former-Held-Out')&(d.subsidy==sigma)]
   for k,v in base.items():q=q[q[k]==v]
   reference='N2-PA-calendar' if 'netherlands' in base['region_id'] else 'DVS-N2';b=d[(d.policy==reference)&(d.cohort=='Former-Held-Out')&(d.subsidy==0)]
   for k,v in base.items():b=b[b[k]==v]
   pair=q.merge(b,on=['region_id','year'],suffixes=('_a','_b'));feas=pair[pair.physically_feasible_in_grid_a==1];dp=float((pair.partial_profit_a-pair.partial_profit_b).mean());violations=int((1-feas.joint_a).sum());qualifies=(bool(len(feas)) and violations==0 if rule=='feasible' else bool((pair.joint_a==1).all())) and dp>=0
   subsidy.append(dict(**base,rule=rule,TRAIN_selected_subsidy=sigma,n_years=len(pair),n_joint=int(pair.joint_a.sum()),n_feasible=len(feas),n_feasible_violations=violations,mean_paired_partial_profit=dp,reused_rule_satisfied=bool(qualifies),status='FrozenTRAINruleprojectedwithoutreselection'))
 with (P/'subsidy-frozen-rule-reused-diagnostics-v6.json').open('x') as f:json.dump(dict(scope='Adaptivereuse;finitegridfeasibilityisexpostdiagnosticnotcausaloracle',groups=subsidy),f,indent=2)
 # Descriptive adaptive family includes three primary regional comparisons, 15 tests.
 family=[]
 for c in contrasts:
  if c['metric']=='joint' and c['reference'] in ('DVS-N2','PPO-v4-structured-shared','PPO-v6-structured-book'):
   for v in c['regions']:family.append(dict(reference=c['reference'],region_id=v['region_id'],p=v['paired_signflip_p']))
 ordered=sorted(range(len(family)),key=lambda i:family[i]['p']);previous=0.
 for rank,i in enumerate(ordered):previous=max(previous,min(1.,family[i]['p']*(len(family)-rank)));family[i]['Holm_adjusted_p']=previous
 output=dict(bootstrap_seed=BOOTSTRAP_SEED,bootstrap_draws=5000,postprocessing_revision='r3registeredseed;nocampaignrepeat',scope='Adaptive-Reused Temporal Benchmark;allexploratorypostPhase5',summary=summary,contrasts=contrasts,Holm_family=family,primary_family='15regionaljointcomparisonsFullvsN2v4PPOv6PPO;seedsaveragedwithinyear',climate='IdealizedwarmingandCO2;notCMIP6',profit='ExperimentalEURpartialNbudget;notwholefarmprofit',organization='Matchedmonolithicidentity;noorganizationalcausaleffect',annual_rows=len(d))
 with (P/'benchmark-statistics-v6.json').open('x') as f:json.dump(output,f,indent=2)
 print(json.dumps(dict(annual_rows=len(d),macro_primary=primary.groupby('policy').apply(lambda g:g.groupby('region_id').joint.mean().mean()).to_dict()),indent=2))
