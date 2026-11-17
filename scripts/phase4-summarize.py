"""Pure frozen-result statistics for Dev and once-authorized heldout cohorts."""
import pathlib,json,statistics,math,numpy as np
from scipy.stats import wilcoxon
R=pathlib.Path(__file__).resolve().parents[1]
SOILS=['default','fast','slow']
def summary(rows):
 if not rows:return dict(n_episodes=0,n_years=0,mean=None)
 avg=lambda key:statistics.mean(float(r[key]) for r in rows)
 return dict(n_episodes=len(rows),n_years=len({r['year'] for r in rows}),yield_t_ha=avg('yield_t_ha'),N_kg_ha=avg('actual_N'),NUE=avg('NUE_actual'),surplus_kg_ha=avg('surplus_actual'),joint=avg('joint_actual'),cvar10_surplus=statistics.mean(sorted([r['surplus_actual'] for r in rows],reverse=True)[:max(1,math.ceil(.1*len(rows)))]),proposed_violation_rate=avg('proposed_violation_rate'),executed_violation_rate=avg('executed_violation_rate'),guard_interception_rate=avg('guard_interception_rate'))
def pair_comparison(a,b,n_boot=3000):
 metrics=['joint_actual','yield_t_ha','actual_N','NUE_actual','surplus_actual','proposed_violation_rate','executed_violation_rate'];result={}
 for metric in metrics:
  def aggregate(rows):
   cells={}
   for r in rows:cells.setdefault((r['year'],r['soil']),[]).append(float(r[metric]))
   return {k:statistics.mean(v) for k,v in cells.items()}
  aa,bb=aggregate(a),aggregate(b);keys=sorted(set(aa)&set(bb));years=sorted({k[0] for k in keys})
  if not keys:result[metric]=dict(n_years=0,mean_difference=None,ci95=None,wilcoxon_p=None);continue
  peryear=np.array([statistics.mean(aa[k]-bb[k] for k in keys if k[0]==y) for y in years]);rng=np.random.default_rng(4);bs=peryear[rng.integers(0,len(years),size=(n_boot,len(years)))].mean(1);p=1. if np.all(peryear==0) else float(wilcoxon(peryear,zero_method='wilcox').pvalue)
  result[metric]=dict(n_years=len(years),paired_scenarios=len(keys),mean_difference=float(peryear.mean()),ci95=np.quantile(bs,[.025,.975]).tolist(),wilcoxon_p=p,small_n_caution=len(years)<10,n_boot=n_boot)
 # CVaR is a non-additive pooled tail functional: bootstrap whole year clusters,
 # not a fabricated Wilcoxon test on per-season "CVaR" observations.
 years=sorted(set(r['year'] for r in a)&set(r['year'] for r in b))
 def tail(values):
  x=np.asarray(values,float);n=max(1,math.ceil(.1*len(x)));return float(np.partition(x,len(x)-n)[-n:].mean())
 if years:
  av={y:[r['surplus_actual'] for r in a if r['year']==y] for y in years};bv={y:[r['surplus_actual'] for r in b if r['year']==y] for y in years};rng=np.random.default_rng(4);differences=[]
  for _ in range(n_boot):
   sampled=rng.choice(years,len(years),replace=True);differences.append(tail([v for y in sampled for v in av[y]])-tail([v for y in sampled for v in bv[y]]))
  result['cvar10_surplus']=dict(n_years=len(years),mean_difference=tail([r['surplus_actual'] for r in a])-tail([r['surplus_actual'] for r in b]),ci95=np.quantile(differences,[.025,.975]).tolist(),wilcoxon_p=None,reason='Nonadditive tail functional; paired-year bootstrap only',small_n_caution=len(years)<10,n_boot=n_boot)
 else:result['cvar10_surplus']=dict(n_years=0,mean_difference=None,ci95=None,wilcoxon_p=None)
 return result

def flatten(path):
 x=json.loads(pathlib.Path(path).read_text());assert x['status']=='completed'
 groups={}
 for rec in x['records']:groups.setdefault(rec['model'],[]).extend(rec['episodes'])
 return groups

def dev_groups():
 groups=flatten(R/'reports/phase4-dev-ppo-matrix.json');groups.update(flatten(R/'reports/phase4-dev-counterfactual.json'))
 old=flatten(R/'reports/phase3b-dev-controls-v3.json')
 for n in ['N2-PA','prior160','prior190']:groups[n]=old[n]
 groups['old_SM-adaptiveprior']=flatten(R/'reports/phase3b3-dev-moisture-controls-audited-v3-sm.json')['adaptiveprior']
 groups['full4']=flatten(R/'reports/phase3c-dev-full4-v4-sm.json')['full4']
 return groups

def full_tables(groups):
 tables={}
 for name,rows in groups.items():
  byseed={str(seed):summary([r for r in rows if r['seed']==seed]) for seed in sorted({r['seed'] for r in rows})}
  tables[name]=dict(pooled=summary(rows),by_seed=byseed,by_soil={s:summary([r for r in rows if r['soil']==s]) for s in SOILS},seed_std={key:statistics.stdev(x[key] for x in byseed.values()) if len(byseed)>1 else None for key in ['yield_t_ha','N_kg_ha','joint','surplus_kg_ha','cvar10_surplus']})
 return tables
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--heldout',action='store_true');a=p.parse_args()
 if not a.heldout:
  groups=dev_groups();out=R/'reports/phase4-dev-metrics-summary.json';assert not out.exists();out.write_text(json.dumps(dict(tables=full_tables(groups),comparisons={n:{ref:pair_comparison(groups[n],groups[ref]) for ref in ['N2-PA','prior190','old_SM-adaptiveprior','full4']} for n in ['utilityprior','cf-gru']}),indent=2));print('Dev matrix summarized')
 else:
  from importlib.machinery import SourceFileLoader
  protocol=SourceFileLoader('summary_protocol',str(R/'scripts/phase4-protocol.py')).load_module();protocol.validate_domain_manifest(R,True)
  weather=SourceFileLoader('summary_weather',str(R/'scripts/phase4-weather-slices.py')).load_module();rain=weather.rain_totals(set(range(1983,2022))|set(range(5500,5999)));thresholds=json.loads((R/'reports/phase4-training-weather-thresholds.json').read_text());allrows=flatten(R/'reports/phase4-heldout-final.json');results={}
  filters={'historical':lambda r:1983<=r['year']<=2021,'historical_default_CEA2025':lambda r:1983<=r['year']<=2021 and r['soil']=='default','stress':lambda r:5500<=r['year']<=5998,'historical_q10':lambda r:1983<=r['year']<=2021 and rain[r['year']]<=thresholds['q10_mm'],'historical_q25':lambda r:1983<=r['year']<=2021 and rain[r['year']]<=thresholds['q25_mm'],'stress_q10':lambda r:5500<=r['year']<=5998 and rain[r['year']]<=thresholds['q10_mm'],'stress_q25':lambda r:5500<=r['year']<=5998 and rain[r['year']]<=thresholds['q25_mm']}
  for split,select in filters.items():
   cohort={n:[r for r in rows if select(r)] for n,rows in allrows.items()};results[split]=dict(tables=full_tables(cohort),years=sorted({r['year'] for rows in cohort.values() for r in rows}),comparisons={n:{ref:pair_comparison(cohort[n],cohort[ref]) for ref in ['N2-PA','prior190','old_SM-adaptiveprior','full4']} for n in ['utilityprior','cf-gru']})
  out=R/'reports/phase4-heldout-metrics-summary.json';assert not out.exists();out.write_text(json.dumps(dict(splits=results,thresholds=thresholds,rain_by_harvest_year=rain),indent=2));print('Frozen heldout summaries completed')
