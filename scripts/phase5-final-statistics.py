"""Paired harvest-year inference; never treats seeds or interventions as replicates."""
from pathlib import Path
import json,hashlib,itertools
from functools import lru_cache
import numpy as np
import pandas as pd
from pcse_gym.agromas.final_evaluation import validate_external_dependency
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5';B=5000
METRICS=('joint','NUE_compliant','surplus_upper_compliant','surplus_corridor_compliant','yield_tDM_ha','partial_profit','N_applied_kg_ha','surplus_kg_ha','NUE','grain_N_kg_ha')
CONTEXT=['role','region_id','climate','zone','price_multiplier','subsidy'];KEY=CONTEXT+['arm']

def upper_cvar(values,alpha=.1):
 x=np.sort(np.asarray(values,float))[::-1];mass=len(x)*alpha;n=int(np.floor(mass));frac=mass-n
 return float((x[:n].sum()+(frac*x[n] if frac>1e-12 else 0.))/mass)

@lru_cache(maxsize=17)
def _signs(n):return np.array(list(itertools.product((-1.,1.),repeat=n)))

def signflip_p(d):
 d=np.asarray(d,float);d=d[np.abs(d)>1e-12]
 if len(d)==0:return 1.
 observed=abs(d.sum());n=len(d)
 if n<=16:
  null=abs(_signs(n)@d)
  return float(np.mean(null>=observed-1e-12))
 rng=np.random.default_rng(20261115);null=abs(rng.choice([-1.,1.],size=(100000,n))@d)
 return float((1+np.sum(null>=observed-1e-12))/100001)

def paired(a,b):
 # Same sorted year set and seed-averaged annual metric vectors.
 assert np.array_equal(a.harvest_year.values,b.harvest_year.values)
 rng=np.random.default_rng(20261115);n=len(a);ix=rng.integers(0,n,size=(B,n));result={}
 for metric in METRICS:
  d=a[metric].to_numpy(float)-b[metric].to_numpy(float);boot=d[ix].mean(1)
  result[metric]=dict(difference=float(d.mean()),CI95=np.quantile(boot,[.025,.975]).tolist(),p_unadjusted=signflip_p(d),n_years=n)
 return result

def immutable_json(path,value):
 with path.open('x') as f:json.dump(value,f,indent=2)
 path.chmod(0o444)

def main():
 permit=P/'final-evaluation-permit-v4.json';validate_external_dependency(R,permit)
 receipt=json.loads((P/'final-policy-evaluation-receipt-v4.json').read_text());assert receipt['permit_sha256']==hashlib.sha256(permit.read_bytes()).hexdigest();rows=[]
 for info in receipt['files']:
  path=R/info['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==info['sha256']
  for row in map(json.loads,path.read_text().splitlines()):
   m=row['outcome'];row['arm']=('PPO-'+row['information_mode']) if row['policy']=='PPO' else row['policy']
   row.update(yield_tDM_ha=m[0],grain_N_kg_ha=m[1],surplus_kg_ha=m[2],NUE=m[3],N_applied_kg_ha=m[4])
   for stage in (1,2,3):row[f'stage{stage}_dose']=sum(e['dose'] for e in row['events'] if e.get('stage')==stage)
   rows.append(row)
 clipping=[]
 for role in ('Held-Out','Public-Reused-Benchmark'):
  for mode in ('structured-shared','raw-shared'):
   subset=[r for r in rows if r['role']==role and r['policy']=='PPO' and r['information_mode']==mode]
   traces=[t for r in subset for t in r['trace']]
   clipping.append(dict(role=role,mode=mode,policy_context_rows=len(subset),decision_events=len(traces),
    any_clipped_decision_events=sum(bool(t.get('clipped_observation_indices')) for t in traces),
    objective_or_mask_clipped_decision_events=sum(bool(t.get('clipped_objective_or_mask_indices')) for t in traces),
    interpretation='FrozenPPOpreprocessingdiagnostic;eventcountsarenotindependentstatisticalreplicates'))
 immutable_json(P/'final-PPO-normalization-diagnostics-v4.json',clipping)
 d=pd.DataFrame(rows);annual=d.groupby(KEY+['harvest_year'],dropna=False)[list(METRICS)+['stage1_dose','stage2_dose','stage3_dose']].mean().reset_index()
 annual.to_csv(P/'final-annual-seed-averaged-metrics-v4.csv',index=False,mode='x')
 d.groupby(KEY+['seed'],dropna=False)[list(METRICS)].mean().reset_index().to_csv(P/'final-seedwise-context-metrics-v4.csv',index=False,mode='x')
 summaries=[]
 for key,g in d.groupby(KEY,sort=True):
  a=annual
  for column,value in zip(KEY,key):a=a[a[column]==value]
  row=dict(zip(KEY,key));row.update({metric:float(a[metric].mean()) for metric in METRICS})
  row.update({f'stage{s}_dose':float(a[f'stage{s}_dose'].mean()) for s in (1,2,3)})
  seedgroups=list(g.groupby('seed',dropna=False));row['upper_CVaR10_surplus_kg_ha']=float(np.mean([upper_cvar(x.surplus_kg_ha) for _,x in seedgroups]))
  row['independent_year_count']=int(g.harvest_year.nunique());row['policy_seed_count']=len(seedgroups)
  row['maximum_abs_soil_N_balance_residual']=float(max(abs(x['soil_N_mass_balance_residual_kg_ha']) for x in g.stock_diagnostics))
  for metric in ('soil_N_stock_drawdown_kg_ha','upper_boundary_export_not_in_published_loss_kg_ha','native_published_leaching_plus_denitrification_kg_ha'):
   row['mean_'+metric]=float(np.mean([x[metric] for x in g.stock_diagnostics]))
  summaries.append(row)
 pd.DataFrame(summaries).to_csv(P/'final-context-summary-v4.csv',index=False,mode='x')
 contrasts=[]
 for key,g in annual.groupby(CONTEXT):
  arms={arm:x.sort_values('harvest_year') for arm,x in g.groupby('arm')};full=arms['A4']
  primary=key[2:] == ('Historical','standard_40',1.,0)
  controls=[a for a in arms if a!='A4'] if primary else ['DVS-N2','PPO-structured-shared']
  for arm in controls:
   contrasts.append(dict(zip(CONTEXT,key),control=arm,metrics=paired(full,arms[arm]),primary=primary))
 family=[x for x in contrasts if x['primary'] and x['role']=='Held-Out' and x['control'] in ('DVS-N2','PPO-structured-shared')]
 ordered=sorted(family,key=lambda x:x['metrics']['joint']['p_unadjusted']);adj=0.
 for rank,x in enumerate(ordered):
  adj=max(adj,min(1.,(len(ordered)-rank)*x['metrics']['joint']['p_unadjusted']));x['metrics']['joint']['p_Holm_primary_family']=adj
 # CVaR contrasts bootstrap paired years separately per seed, then average seed metrics.
 for x in contrasts:
  if not x['primary']:continue
  match=d
  for col in CONTEXT:match=match[match[col]==x[col]]
  aa=match[match.arm=='A4'];bb=match[match.arm==x['control']]
  years=np.sort(aa.harvest_year.unique());rng=np.random.default_rng(20261115);ix=rng.integers(0,len(years),size=(B,len(years)))
  va=aa.set_index('harvest_year').loc[years].surplus_kg_ha.to_numpy();vb=np.stack([v.set_index('harvest_year').loc[years].surplus_kg_ha.to_numpy() for _,v in bb.groupby('seed',dropna=False)])
  diff=upper_cvar(va)-float(np.mean([upper_cvar(v) for v in vb]))
  boot=[upper_cvar(va[i])-np.mean([upper_cvar(v[i]) for v in vb]) for i in ix]
  x['CVaR10_surplus_contrast']=dict(difference=diff,CI95=np.quantile(boot,[.025,.975]).tolist(),pvalue=None,scope='CIonly;nonlinearCVaRcontrastnotmeanannualsignflip')
 immutable_json(P/'final-paired-year-statistics-v4.json',dict(status='completed',bootstrap_replicates=B,bootstrap_seed=20261115,contrasts=contrasts,
  aliases={'LOAO-economics':'A3','matched-monolithic-optimizer':'A4'},public_reused_separate=True,seed_pseudoreplication=False))
 # Equal-region macro. Harvest year is sampled jointly across all five regions.
 main=annual[(annual.role=='Held-Out')&(annual.climate=='Historical')&(annual.zone=='standard_40')&(annual.price_multiplier==1)&(annual.subsidy==0)]
 regions=sorted(main.region_id.unique());years=np.sort(main.harvest_year.unique());rng=np.random.default_rng(20261115);globalrows=[]
 for control in ('DVS-N2','PPO-structured-shared'):
  vectors={}
  for reg in regions:
   g=main[main.region_id==reg];a=g[g.arm=='A4'].set_index('harvest_year');b=g[g.arm==control].set_index('harvest_year')
   vectors[reg]=(a[list(METRICS)]-b[list(METRICS)])
  boot=[];reject=0
  while len(boot)<B:
   sample=rng.choice(years,len(years),replace=True);vals=[]
   for reg in regions:
    idx=[y for y in sample if y in vectors[reg].index]
    if not idx:break
    vals.append(vectors[reg].loc[idx].mean().to_numpy())
   if len(vals)<len(regions):reject+=1;continue
   boot.append(np.mean(vals,axis=0))
  point=np.mean([v.mean().to_numpy() for v in vectors.values()],axis=0);ci=np.quantile(boot,[.025,.975],axis=0)
  globalrows.append(dict(control=control,weighting='equal-regionmacro',year_clusters=len(years),rejected_empty_region_draws=reject,
   metrics={m:dict(difference=float(point[i]),CI95=ci[:,i].tolist()) for i,m in enumerate(METRICS)}))
 immutable_json(P/'final-global-macro-statistics-v4.json',globalrows)
 for name in ('final-annual-seed-averaged-metrics-v4.csv','final-context-summary-v4.csv','final-seedwise-context-metrics-v4.csv'):(P/name).chmod(0o444)
 validate_external_dependency(R,permit)
 print(json.dumps(dict(rows=len(d),annual=len(annual),context_summaries=len(summaries),contrasts=len(contrasts))))

if __name__=='__main__':main()
