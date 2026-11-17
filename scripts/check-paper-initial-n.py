import pathlib,importlib.machinery,json,time,yaml,contextlib
R=pathlib.Path(__file__).resolve().parents[1];m=importlib.machinery.SourceFileLoader('baseline_eval',str(R/'scripts/evaluate-baselines.py')).load_module()
site=yaml.safe_load((R/'NUE_PCSE-Gym/pcse_gym/envs/configs/site/arminda_site.yaml').read_text());options={'NO3I':[x*70/sum(site['NO3I']) for x in site['NO3I']],'NH4I':[0.]*7};rows=[];start=time.monotonic()
with open(R/'logs/paper-initial-n-details.log','w') as log,contextlib.redirect_stdout(log):
 env=m.initialize_env(pcse_env=2,years=[1983],locations=[(52.57,5.63)],random_weather=True,random_init=False,reward='NUE',start_type='sowing',seed=4)
 for year in range(1983,2022):
  env.overwrite_year(year);env.reset(options=options);info=m.evaluate_treatment('N2-PA',env)[1][0];rows.append(m.extract(info,year,'N2-PA-paper-total-N-sensitivity'))
result={'protocol':'Sensitivity only: paper total nitrate 70, ammonium 0; released per-layer NO3 proportions rescaled. Not claimed identical paper per-layer initialization. All other released settings unchanged. No hyperparameter selection.','initial_NO3I':options['NO3I'],'initial_NH4I':options['NH4I'],'summary':m.summarize(rows),'episodes':rows,'wall_clock_seconds':time.monotonic()-start}
(R/'reports/paper-initial-n-sensitivity.json').write_text(json.dumps(result,indent=2));print(result['summary'])
