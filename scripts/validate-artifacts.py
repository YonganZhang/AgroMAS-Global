import pathlib,json,hashlib,math
R=pathlib.Path(__file__).resolve().parents[1]
a=json.loads((R/'reports/asset-receipt.json').read_text());checks={}
for name in ['weather_csv','paper_pdf']:
 p=pathlib.Path(a[name+'_path']);checks[name+'_sha256']=hashlib.sha256(p.read_bytes()).hexdigest()==a[name+'_sha256']
checks['weather_bytes']=a['weather_csv_bytes']==63774426
checks['weather_md5']=hashlib.md5(pathlib.Path(a['weather_csv_path']).read_bytes()).hexdigest()=='fd7e5421842e0870812a2e26546c73f0'
d=json.loads((R/'reports/deterministic-baselines.json').read_text())
for name,expected in [('N1-PA',80),('N2-PA',220),('N3-PA',240),('Zero-N',0)]:
 rows=d['policies'][name]['episodes'];checks[name+'_39_years']=[x['year'] for x in rows]==list(range(1983,2022));checks[name+'_applied_total']=all(x['fertilization_kg_ha']==expected for x in rows);checks[name+'_finite']=all(math.isfinite(x[k]) for x in rows for k in ['yield_t_ha','NUE','N_surplus_kg_ha','profit_kEUR_ha']);checks[name+'_fractions']=all(0<=v<=1 for k,v in d['policies'][name]['summary'].items() if k.endswith('_rate'))
if (R/'reports/rl-final-evaluation.json').exists():
 e=json.loads((R/'reports/rl-final-evaluation.json').read_text());checks['RL_eval_39_years']=[x['year'] for x in e['episodes']]==list(range(1983,2022));t=json.loads((R/'reports/rl-training-receipt.json').read_text());checks['RL_parameters_changed']=t['parameters_changed'];checks['RL_minimum_100k']=t['steps_run']>=100000;checks['RL_checkpoint_exists']=pathlib.Path(e['checkpoint_path']).is_file()
checks['all_passed']=all(checks.values());(R/'reports/artifact-validation.json').write_text(json.dumps(checks,indent=2));print(checks)
assert checks['all_passed']
