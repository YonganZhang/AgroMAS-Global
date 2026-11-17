"""Post-hoc Dev-only dry/fast and wet/default case records; no new simulations."""
import pathlib,json,csv,collections,hashlib
R=pathlib.Path(__file__).resolve().parents[1]
p=R/'reports/phase3b3-dev-full3-v3-sm.json';x=json.loads(p.read_text());assert x['split']=='dev'
rain=collections.defaultdict(float)
with (R/'data/52.57-5.63_random_weather.csv').open() as f:
 for line in f:
  if line.startswith('DAY,'):break
 reader=csv.DictReader(f,fieldnames=line.strip().split(','))
 for row in reader:
  date=row['DAY'];y=int(date[:4]);month=int(date[4:6]);harvest=y+1 if month>=10 else y
  if 5000<=harvest<=5499 and (month>=10 or month<=7):rain[harvest]+=float(row['RAIN'])
assert len(rain)==500
cases=[('dry_fast',min(rain,key=rain.get),'fast'),('wet_default',max(rain,key=rain.get),'default')]
controls=json.loads((R/'reports/phase3b-dev-controls-v3.json').read_text())['records'];out=[]
for label,year,soil in cases:
 rows=[]
 for seed in [4,17,29]:
  record=next(r for r in x['records'] if r['seed']==seed and r['soil']==soil and any(e['year']==year for e in r['episodes']))
  e=next(e for e in record['episodes'] if e['year']==year)
  rows.append(dict(seed=seed,checkpoint_sha256=record['checkpoint_sha256'],outcome=e,application_states=[z for z in record['events'] if z['year']==year and z['proposed']>0]))
 refs={n:next(e for r in controls if r['model']==n and r['soil']==soil for e in r['episodes'] if e['year']==year) for n in ['prior190','N2-PA']}
 out.append(dict(case=label,year=year,soil=soil,seasonal_rain_mm=rain[year],policy_cases=rows,static_controls=refs))
file=R/'reports/phase3b3-dev-attribution.json';assert not file.exists();file.write_text(json.dumps(dict(dev_only=True,no_new_simulation=True,selection='minimum/maximum Oct-July rainfall within Dev only; post-hoc explanation, never actor input',causal_feature_importance_claim=False,input_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),cases=out),indent=2));print([(a,y,s,round(rain[y],2)) for a,y,s in cases])
