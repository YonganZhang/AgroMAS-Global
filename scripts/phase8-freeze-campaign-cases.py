"""Pre-enumerate limited orthogonal campaigns, never90-cell cross-products."""
from pathlib import Path
import json,hashlib
import numpy as np
from pcse_gym.agromas.season import regional_weather
from pcse_gym.agromas.regions import REGIONS
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8'
if __name__=='__main__':
 path=P/'phase8b-locked-campaign-cases.json'
 if path.exists():raise ValueError('Campaign enumeration already frozen')
 split=json.loads((R/'reports/phase5/global-date-split-manifest.json').read_text());base=[];quantiles={};extremes=[]
 def rain(region,year):
  start,end=REGIONS[region].crop_dates(year);provider=regional_weather(str(R),region,'v2');return float(provider.history(start,end,as_of=end).values[:,3].sum())
 for region,info in split['regions'].items():
  values=[rain(region,y) for y in range(1995,2010)];lo,hi=np.quantile(values,[.2,.8]);quantiles[region]=dict(q20=float(lo),q80=float(hi),TRAIN_years=list(range(1995,2010)),definition='full_crop_calendar_total_rain_mm;offline_cohort_selection_only')
  for role in ('Held-Out','Public-Reused-Benchmark'):
   for year in info['roles'][role]:
    if year<2015:continue
    b=dict(region=region,year=year,role=role,source='NASA',cohort='Former-Held-Out' if role=='Held-Out' else 'Public-Reused',cap=40.,price_multiplier=1.,subsidy=0.,tax=0.,benchmark='P1');base.append(b)
    value=rain(region,year)
    if value<=lo or value>=hi:extremes.append(dict(region=region,year=year,total_rain=value,extreme='dry' if value<=lo else 'wet'))
 assert len(base)==59;cases=[]
 def add(b,policy,track='Sensorless',**kwargs):
  c=b|dict(policy=policy,track=track)|kwargs;c['episode_id']=hashlib.sha256(json.dumps(c,sort_keys=True).encode()).hexdigest()[:20];cases.append(c)
 for b in base:
  for track in ('Full-Telemetry','Sensorless'):add(b,'TreeMLP',track)
  add(b,'LegacyV6Full','Full-Telemetry');add(b,'DVS-N2','Full-Telemetry')
  for seed in (4,17,29):add(b,'LegacyV6PPO','Full-Telemetry',seed=seed);add(b,'SensorlessPPO',seed=seed)
  for policy in ('TreeWeather','TreeExtraTrees','TreeLinear','soft','open-loop','greedy-frozen'):add(b,policy)
  for cap in (25.,35.):
   for policy in ('TreeMLP','remove-eco'):add(b|dict(cap=cap),policy)
  green=json.loads((P/'phase8b-green-stress-TRAIN-freeze.json').read_text())['selected_subsidy']
  for change in [dict(price_multiplier=2.)]+([dict(subsidy=float(green))] if green is not None else []):
   for policy in ('TreeMLP','remove-econ'):add(b|change,policy)
  if any(v['region']==b['region'] and v['year']==b['year'] for v in extremes):
   # Baseline TreeMLP already evaluated above, reuse it for paired contrast.
   add(b,'remove-climate')
  if b['region']=='netherlands_lelystad':
   for policy in ('N2-PA-matched','N2-PA-calendar','Phase4-Forest-transfer'):add(b,policy,'Full-Telemetry')
 for year in range(2015,2022):
  b=dict(region='netherlands_lelystad',year=year,role='Public-Reused-Benchmark',source='WUR',cohort='Public-Reused-WUR',cap=40.,price_multiplier=1.,subsidy=0.,tax=0.,benchmark='P1-WUR')
  for track in ('Full-Telemetry','Sensorless'):add(b,'TreeMLP',track)
  for policy in ('LegacyV6Full','DVS-N2','N2-PA-matched','N2-PA-calendar','Phase4-Forest-transfer'):add(b,policy,'Full-Telemetry')
  for seed in (4,17,29):add(b,'LegacyV6PPO','Full-Telemetry',seed=seed);add(b,'SensorlessPPO',seed=seed)
 cohort=json.loads((P/'phase8b-P2-metadata-cohort.json').read_text())['rows']
 for scheme in ('LOYO','LORO'):
  for row in cohort:
   b=dict(region=row['region'],year=row['year'],role='Public-Reused-Benchmark' if row['cohort']=='Public-Reused' else 'Held-Out',source='NASA',cohort=row['cohort'],cap=40.,price_multiplier=1.,subsidy=0.,tax=0.,benchmark='P2',scheme=scheme,fold=str(row['year'] if scheme=='LOYO' else row['region']))
   for variant in ('Full64','Static3','Weather','Linear64','ExtraTrees64'):add(b,'P2-'+variant)
 assert len({c['episode_id'] for c in cases})==len(cases)
 with path.open('x') as out:json.dump(dict(cases=cases,total_native_episodes=len(cases),P1_worlds=59,P2_worlds_per_scheme=44,P2_schemes_not_pooled=True,WUR_worlds=7,TRAIN_rain_quantiles=quantiles,extreme_cohort=extremes,monolithic='bit_identical_alias_of_TreeMLP_no_duplicate_physics',StaticSoilDL_P1='TreeMLP_Sensorless_alias_no_duplicate_physics',no_90_cell_surface=True),out,indent=2)
 path.chmod(0o444);print('Frozen native episodes',len(cases),flush=True)
