"""Predefined descriptive and paired analysis; never tunes frozen inference.

All simultaneous claims use one Holm family covering every reported sign test.
PPOseeds are averaged within farm-year before any comparison. Spatial and
weather/cohort strata remain separate. CIs are marginal descriptive intervals.
"""
from pathlib import Path
import hashlib,importlib.util,json
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';D=R/'data/phase8d-evaluation'
sp=importlib.util.spec_from_file_location('paired_reference',R/'scripts/phase8-analyze-recovered-core-results.py');lib=importlib.util.module_from_spec(sp);sp.loader.exec_module(lib)
METRICS=['joint','partial_profit','Yield','Grain_N','S_N','NUE','Executed_N','Native_N_loss','NUE_gt_090','NUE_lt_050','surplus_compliant','Tier1','Tier2','Tier3','decisions','zero_dose_decisions','prior_decisions','prior_accepted','prior_ood']
CONTEXT=['source','cohort','scheme','climate','cap','price_multiplier','subsidy','tax']
if __name__=='__main__':
 design=json.loads((P/'phase8d-frozen-cases-v4.json').read_text());receipt=json.loads((P/'phase8d-campaign-receipt.json').read_text());assert not any(receipt['exit_codes']) and receipt['results']==design['total']
 rows=[];audits=[];newaudits=[]
 for c in design['cases']:
  file=D/c['episode_id']/'result.json';raw=file.read_bytes();assert hashlib.sha256(raw).hexdigest()==(file.parent/'sha256').read_text().strip();r=json.loads(raw);a=r['mass_audit'];assert a['passed'];m=np.asarray(r['outcome']);trace=[t for t in r['trace'] if t.get('tier') is not None and not t.get('deferred',False)];prior=[t for t in trace if t.get('prior_accepted') is not None]
  if 'reuse' not in c:
   assert len(a['daily_records'])==a['daily_rows']
   n=np.array([d['N_residual_kg_ha'] for d in a['daily_records']]);carbon=np.array([d['C_residual_kg_ha'] for d in a['daily_records']]);assert np.isfinite(n).all() and np.isfinite(carbon).all() and np.abs(n).max()<1e-10 and np.abs(carbon).max()<1e-9
   assert np.abs(n).max()==a['max_abs_N_residual_kg_ha'] and np.abs(carbon).max()==a['max_abs_C_residual_kg_ha'];newaudits.append({k:v for k,v in a.items() if k!='daily_records'})
  audits.append({k:v for k,v in a.items() if k!='daily_records'})
  rows.append({k:v for k,v in c.items() if k not in ('reuse','phase8d_groups')}|dict(scheme=c.get('scheme','none'),joint=float(r['joint']),partial_profit=r['partial_profit'],Yield=m[0],Grain_N=m[1],S_N=m[2],NUE=m[3],Executed_N=m[4],Native_N_loss=r['Native_N_loss'],NUE_gt_090=float(m[3]>.9),NUE_lt_050=float(m[3]<.5),surplus_compliant=float(r['surplus_compliant']),Tier1=sum(t['tier']==1 for t in trace),Tier2=sum(t['tier']==2 for t in trace),Tier3=sum(t['tier']==3 for t in trace),decisions=len(trace),zero_dose_decisions=sum(t['dose']==0 for t in trace),prior_decisions=len(prior),prior_accepted=sum(t['prior_accepted'] for t in prior),prior_ood=sum(t['prior_ood'] for t in prior),reused='reuse' in c,episode_sha256=hashlib.sha256(raw).hexdigest(),Q84='Q8.4' in c['phase8d_groups'],G3A='G3-A' in c['phase8d_groups'],G3B='G3-B' in c['phase8d_groups'],G3C=any(g.startswith('G3-C') for g in c['phase8d_groups']),subsidy_diagnostic='subsidy-diagnostic' in c['phase8d_groups']))
 frame=pd.DataFrame(rows);frame.to_csv(P/'phase8d-native-episode-metrics.csv',index=False)
 keys=CONTEXT+['benchmark','region','year','policy','track','mode'];annual=frame.groupby(keys,dropna=False)[METRICS].mean().reset_index();annual.to_csv(P/'phase8d-case-metrics-seed-averaged.csv',index=False)
 summary=[]
 for key,g in annual.groupby(CONTEXT+['benchmark','policy','track','mode'],dropna=False):
  regional=g.groupby('region')[METRICS].mean();summary.append(dict(zip(CONTEXT+['benchmark','policy','track','mode'],key))|dict(site_years=len(g),region_count=len(regional),pooled=g[METRICS].mean().to_dict(),region_equal=regional.mean().to_dict(),by_region={name:dict(n=int((g.region==name).sum()))|row.to_dict() for name,row in regional.iterrows()},Tier_fractions={str(i):float(g[f'Tier{i}'].sum()/g.decisions.sum()) if g.decisions.sum() else None for i in (1,2,3)},tier_semantics='soft mode Tier1 denotes unconstrained composite-score choice,not forecast or realized compliance' if key[-1]=='soft' else 'hard active specialist hierarchy; Tier2 corridor-preferred then upper-surplus fallback; Tier3 OOD or operational zero,not compliance'))
 contrasts=[];primary_ids=[('TreeMLP','Sensorless','soft'),('TreeMLP','Sensorless','tree'),('TreeMLP','Full-Telemetry','soft'),('TreeMLP','Full-Telemetry','tree'),('P2-Full64','Sensorless','soft'),('P2-Full64','Sensorless','tree')]
 for context,g in annual.groupby(CONTEXT+['benchmark'],dropna=False):
  groups={key:part for key,part in g.groupby(['policy','track','mode'])}
  for primary in primary_ids:
   if primary not in groups:continue
   a=groups[primary]
   for reference,b in groups.items():
    if reference==primary:continue
    if primary[1]!=reference[1] and reference[0] not in ('LegacyV6Full','DVS-N2'):continue
    if primary[0].startswith('P2-')!=reference[0].startswith('P2-'):continue
    for region in ('netherlands_lelystad','france_paris_beauce','usa_kansas_wichita','china_ncp_luancheng','australia_wa_perth','CORE_EQUAL3','GLOBAL_EQUAL5'):
     regions={'CORE_EQUAL3':('netherlands_lelystad','usa_kansas_wichita','australia_wa_perth'),'GLOBAL_EQUAL5':('netherlands_lelystad','france_paris_beauce','usa_kansas_wichita','china_ncp_luancheng','australia_wa_perth')}.get(region,(region,));aa=a[a.region.isin(regions)];bb=b[b.region.isin(regions)]
     for metric in ('joint','partial_profit','Native_N_loss','NUE_gt_090'):
      result=lib.paired(aa,bb,metric)
      if result is None:continue
      matched=aa[['region','year',metric]].merge(bb[['region','year',metric]],on=['region','year'],suffixes=('_a','_b'),validate='one_to_one')
      if set(matched.region)!=set(regions):continue
      if len(regions)>1:
       rng=np.random.default_rng(lib.SEED);draws=[];effects=[]
       for r in regions:
        part=matched[matched.region==r];delta=(part[metric+'_a']-part[metric+'_b']).to_numpy(float).copy();delta[np.abs(delta)<=result['tie_absolute_tolerance']]=0;effects.append(float(delta.mean()));draws.append(delta[rng.integers(len(delta),size=(lib.B,len(delta)))].mean(1))
       result.update(mean_difference=float(np.mean(effects)),CI95=np.quantile(np.mean(draws,axis=0),[.025,.975]).tolist(),bootstrap_weighting='paired years resampled within each region;equal regions',exact_test_weighting='pooled paired farm-year signs/ranks,not region-weighted ranks')
      contrasts.append(dict(zip(CONTEXT+['benchmark'],context))|dict(region=region,primary=list(primary),reference=list(reference),information_matched=primary[1]==reference[1],metric=metric)|result)
 if contrasts:
  pv=np.array([c['exact_two_sided_sign_p'] for c in contrasts]);order=np.argsort(pv);adj=np.minimum(1,np.maximum.accumulate((len(pv)-np.arange(len(pv)))*pv[order]))
  for i,v in zip(order,adj):contrasts[int(i)]['Holm_sign_p_full_family']=float(v)
 # The stress export is regional cells, with seed averaging at farm-year first.
 ids=set(frame.loc[frame.Q84,'episode_id']);stress=annual.merge(frame[frame.episode_id.isin(ids)][keys].drop_duplicates(),on=keys,validate='one_to_one');stresskeys=['region','climate','cap','price_multiplier','subsidy','policy','track','mode'];surface=stress.groupby(stresskeys)[METRICS].mean().reset_index();surface['n_years']=stress.groupby(stresskeys).size().to_numpy();surface.to_csv(P/'phase8d-180cell-stress-surface.csv',index=False)
 canonical=surface[(surface.cap.isin([25.,35.,50.]))&(surface.subsidy==0.)];assert len(canonical[['region','climate','cap','price_multiplier']].drop_duplicates())==90;canonical.to_csv(P/'phase8d-canonical90-stress-subset.csv',index=False)
 assert len(surface[['region','climate','cap','price_multiplier','subsidy']].drop_duplicates())==180
 def mass(aa):return dict(scored_case_configurations=len(aa),daily_records=sum(a['daily_rows'] for a in aa),all_passed=True,max_N=max(a['max_abs_N_residual_kg_ha'] for a in aa),max_C=max(a['max_abs_C_residual_kg_ha'] for a in aa))
 result=dict(summary=summary,contrasts=contrasts,mass_all_configurations=mass(audits),mass_new_native=mass(newaudits),actual_native_simulations=receipt['native_simulations_including_repeated_executed_triples'],unique_native_trajectories_simulated=receipt['unique_native_trajectories_simulated'],trajectory_cache_hits=receipt['trajectory_cache_hits'],reused=design['reused'],new_native=design['new_native'],bootstrap=dict(B=lib.B,seed=lib.SEED,unit='farm-year after within-case seed averaging'),statistical_scope='adaptive-reused evaluation;retrospective P2;NASA/WUR,Former/Public,LOYO/LORO unpooled',CIs='marginal descriptive,not simultaneous or prospective assurance',multiplicity=dict(family_size=len(contrasts),method='Holm across every reported exact two-sided sign test'),NL_n5_min_exact_p=.0625,monolithic='exact computational alias;no agent-count causal claim',physical_ceilings_scope='old finite GRID Historical cap40physics only;do not extrapolate to climate/cap changes',architecture='36D13155parameter neural backbone plus private64D PCA/Ridge adapter<=4D')
 (P/'phase8d-core-statistics.json').write_text(json.dumps(result,indent=2,allow_nan=False));print(json.dumps(dict(summary_groups=len(summary),contrasts=len(contrasts),mass=result['mass_new_native'])))
