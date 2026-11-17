"""Same legacy TRAIN weather physiological probe; no new-region Held-Out access."""
from pathlib import Path
import copy,json,yaml,shutil
from datetime import date
from pcse.base import ParameterProvider
from pcse_gym.envs.sb3 import get_wofost_kwargs
from pcse_gym.envs.common_env import Engine,AgroManagementContainer,get_random_weather_provider
from pcse_gym.agromas.physiology import configure_co2,assert_co2_physiology,ScenarioWeather
from pcse_gym.agromas import ThreeStageScheduler
R=Path(__file__).resolve().parents[1]

def make_engine(co2=380, year=3002):
    config=R/'cache/phase5-co2-config'
    if not config.exists():
        shutil.copytree(R/'NUE_PCSE-Gym/pcse_gym/envs/configs',config,ignore=shutil.ignore_patterns('*.pkl','__pycache__'))
    kw=get_wofost_kwargs(config_dir=str(config))
    crop=kw['crop_parameters'];crop.set_active_crop('winterwheat','Arminda')
    site=copy.deepcopy(kw['site_parameters'])
    params=ParameterProvider(cropdata=crop,sitedata=site,soildata=kw['soil_parameters'])
    configure_co2(params,co2)
    agro=AgroManagementContainer(yaml.safe_load(Path(kw['agro_config']).read_text()))
    agro.get_start_type('sowing');agro.replace_years(year)
    weather=get_random_weather_provider((52.57,5.63))
    engine=Engine(params,weather,agro.structure,config=kw['model_config'])
    return engine

def run(co2):
    engine=make_engine(co2)
    scheduler=ThreeStageScheduler(210)
    def guard(action,dvs,day):
        return scheduler.execute(day,dvs,action,expected_stage=stage) if dvs is not None and stage is not None else 0.
    engine._action_guard=guard
    module=None;days=0
    while not engine.terminated and days<400:
        stage=scheduler.eligible(engine.day,float(engine.get_variable('DVS') or 0))
        engine.run(days=7,action=[70,60,60][stage-1] if stage else 0)
        days+=7
        if engine.crop is not None:module=assert_co2_physiology(engine)
    summaries=engine.get_summary_output()
    if not engine.terminated or not summaries:raise RuntimeError('Invalid seasonal trajectory')
    result=summaries[-1]
    return dict(co2=co2,et_module=module,TAGP=result['TAGP'],TWSO=result['TWSO'],CTRAT=result['CTRAT'],
                DVS=result['DVS'],events=scheduler.events,source='legacy TRAIN random weather year3002, not foreign historical observations')

if __name__=='__main__':
    low=run(380);high=run(550)
    assert abs(high['TAGP']-low['TAGP'])>1e-3,'CO2 assimilation no-op'
    assert abs(high['CTRAT']-low['CTRAT'])>1e-5,'CO2 transpiration no-op'
    out=R/'reports/phase5/co2-physiology-probe.json'
    if out.exists():raise FileExistsError('Preserve existing physiological evidence; select a new receipt version')
    out.write_text(json.dumps(dict(status='passed',low=low,high=high,claim='model physiology only; no regional efficacy'),indent=2))
    print(out)
