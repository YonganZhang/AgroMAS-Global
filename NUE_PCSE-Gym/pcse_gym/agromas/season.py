"""Explicit registered regional physical seasons; evaluation roles remain locked."""
from pathlib import Path
from functools import lru_cache
from datetime import date,timedelta
import copy,json,shutil
import numpy as np
from pcse.base import ParameterProvider
from pcse_gym.envs.sb3 import get_wofost_kwargs
from pcse_gym.envs.common_env import Engine
from .regions import REGIONS,load_split_manifest,authorize_year
from .weather import VerifiedNASAWeather
from .physiology import configure_co2,ScenarioWeather,assert_co2_physiology
from .scheduler import ThreeStageScheduler
from .weekly import advance_week
from .contracts import FieldState
from .initialization import water_initialization


@lru_cache(maxsize=4)
def _template(project_root):
    root=Path(project_root)
    config=root/'cache/phase5-regional-config'
    if not config.exists():
        shutil.copytree(root/'NUE_PCSE-Gym/pcse_gym/envs/configs',config,
                        ignore=shutil.ignore_patterns('*.pkl','__pycache__'))
    return get_wofost_kwargs(config_dir=str(config))


@lru_cache(maxsize=10)
def regional_weather(project_root,region_id,version="v1"):
    root=Path(project_root)
    path=root/'data/global_regions'/region_id/'nasa-power-19840101-20261101.json'
    receipt=json.loads(path.with_suffix('.receipt.json').read_text())
    extra={}
    if version=='v2':
        mean=path.parent/'nasa-t2m-19840101-20261101-v2.json'
        extra=dict(mean_temperature_path=mean,mean_temperature_sha256=json.loads(mean.with_suffix('.receipt.json').read_text())['sha256'])
    elif version!='v1':raise ValueError('Unknown regional control version')
    return VerifiedNASAWeather(path,receipt['sha256'],region_id,**extra)


def build_season(project_root,region_id,year,*,role='Train',thermal_scale=1.,climate='Historical',permit_path=None,version='v1',cultivar='Arminda',root_depth_cm=125.):
    root=Path(project_root)
    manifest=load_split_manifest(root/'reports/phase5/global-date-split-manifest.json')
    authorize_year(manifest,region_id,year,role,permit_path=permit_path,project_root=root)
    if version not in ('v1','v2'):raise ValueError('Unknown regional control version')
    controls=json.loads((root/f'reports/phase5/regional-controls-{version}.json').read_text())
    if version=='v1' and (cultivar!='Arminda' or root_depth_cm!=125.):raise ValueError('v1 source configuration is immutable')
    if version=='v2' and (cultivar not in controls['cultivar_candidates'] or root_depth_cm not in controls['root_depth_sensitivity_cm']):
        raise ValueError('Unregistered v2 cultivar/root-depth hypothesis')
    if thermal_scale not in controls['phenology_candidates']:raise ValueError('Unregistered thermal candidate')
    # Exact task temperature/CO2 controls; do not call them actual GCM projections.
    scenarios={'Historical':(0.,380.),'idealized_mid':(1.8,450.),'idealized_high':(3.5,550.)}
    if climate not in scenarios:raise ValueError('Unknown climate sensitivity')
    delta,co2=scenarios[climate]
    kw=copy.deepcopy(_template(str(root)))
    soil=json.loads((root/'reports/phase5/regional-model-inputs'/region_id/'soil-v1.json').read_text())
    if version=='v2' and region_id=='netherlands_lelystad':
        # Explicit approved native arable prior; never pretend this is measured SoilGrids.
        soil=copy.deepcopy(kw['soil_parameters'])
    elif version=='v2':
        native=kw['soil_parameters']['SoilProfileDescription']['SoilLayers']
        for layer,reference in zip(soil['SoilProfileDescription']['SoilLayers'],native,strict=True):
            layer['CNRatioSOMI']=reference['CNRatioSOMI']
    crop=kw['crop_parameters'];crop.set_active_crop('winterwheat',cultivar)
    site=kw['site_parameters']
    site['NH4ConcR']=controls['wet_deposition_nh4_mg_l'];site['NO3ConcR']=controls['wet_deposition_no3_mg_l']
    layers=soil['SoilProfileDescription']['SoilLayers']
    site['WAV']=.7*sum(np.interp(2.,np.array(x['SMfromPF'])[::2],np.array(x['SMfromPF'])[1::2])*x['Thickness'] for x in layers)
    site['SMLIM']=float(np.interp(2.,np.array(layers[0]['SMfromPF'])[::2],np.array(layers[0]['SMfromPF'])[1::2]))
    if version=='v2':
        init=water_initialization(soil,target='field_capacity')
        site['WAV']=init['WAV_cm'];site['SMLIM']=init['SMLIM']
        site['SSMAX']=controls['surface_storage_cm']
        site['A0SOM']=controls['native_SOM_apparent_age_years']
    parameters=ParameterProvider(cropdata=crop,sitedata=site,soildata=soil)
    if version=='v2':parameters.set_override('RDMCR',root_depth_cm)
    configure_co2(parameters,co2)
    parameters.set_override('TSUM1',float(parameters['TSUM1'])*thermal_scale)
    parameters.set_override('TSUM2',float(parameters['TSUM2'])*thermal_scale)
    if region_id=='australia_wa_perth':parameters.set_override('IDSL',1)
    region=REGIONS[region_id];start,end=region.crop_dates(year);campaign,_=region.weather_envelope(year)
    events=None
    if region_id=='china_ncp_luancheng':
        irr=controls['irrigation'][region_id]
        events=[dict(event_signal='irrigate',event_state='DVS',zero_condition='rising',name='common_source_based_irrigation',
                     comment='Fixed experimental management shared by all policies',events_table=[
                         {d:dict(amount=irr['amount_cm_per_event'],efficiency=irr['efficiency'])} for d in irr['DVS_events']])]
    basal=controls.get('regional_basal_n_kg_ha',{}).get(region_id,0.)
    timed=None
    if basal:
        timed=[dict(event_signal='apply_n_snomin',name='source_based_basal',comment='Shared source-based basal, included in seasonal budget',
                    events_table=[{start:dict(amount=basal,application_depth=10.,cnratio=0.,f_orgmat=0.,f_NH4N=.5,f_NO3N=.5,initial_age=0.)}])]
    agro=[{campaign:dict(CropCalendar=dict(crop_name='winterwheat',variety_name=cultivar,crop_start_date=start,
                        crop_start_type='sowing',crop_end_date=end,crop_end_type='harvest',max_duration=365),
                        TimedEvents=timed,StateEvents=events)}]
    if events is not None:agro.append({end+timedelta(days=1):None})
    source=regional_weather(str(root),region_id,version)
    weather=source if delta==0 else ScenarioWeather(source,delta)
    stock_om=np.array([x['RHOD']*x['Thickness']*x['FSOMI']*1e5 for x in layers])
    stock_c=.58*stock_om
    stock_n=stock_c/np.array([x['CNRatioSOMI'] for x in layers])
    stock_ledger=dict(organic_matter_kg_ha=stock_om.tolist(),organic_C_kg_ha=stock_c.tolist(),
                      organic_N_kg_ha=stock_n.tolist(),initial_NO3_kg_ha=list(site['NO3I']),initial_NH4_kg_ha=list(site['NH4I']),
                      apparent_age_years=float(site['A0SOM']),native_total_SOM=True,
                      NUE_denominator='fertilizer+seed+wet_deposition; excludes initial soil stocks')
    engine=Engine(parameters,weather,agro,config=kw['model_config'])
    warm_days=(start-engine.day).days
    if warm_days>0:engine.run(days=warm_days,action=0)
    if engine.crop is None:raise ValueError('Crop did not initialize at registered sow date')
    assert_co2_physiology(engine)
    return engine,dict(region_id=region_id,harvest_year=year,role=role,climate=climate,
                       thermal_scale=thermal_scale,cultivar=cultivar,root_depth_cm=root_depth_cm,initial_base_n=basal,
                       version=version,initial_stock_ledger=stock_ledger,weather_source_id=source.source_id,warmup_physical_days=warm_days,background='controlled-regional-'+version,
                       field_validation=False)


def observe(engine,scheduler,region_id):
    def scalar(name):
        x=engine.get_variable(name)
        return 0. if x is None else float(np.asarray(x).ravel()[0])
    sm=scalar('SM')
    return FieldState(engine.day,region_id,scalar('DVS'),scalar('LAI'),sm,scheduler.cumulative,
                      scalar('NuptakeTotal'),scheduler.preview(engine.day+timedelta(days=1),scalar('DVS')) or 0,True)


def terminal(engine,scheduler,seed_n=3.5):
    summaries=engine.get_summary_output()
    if not summaries:raise ValueError('Missing seasonal crop output')
    summary=summaries[-1];last=engine.get_output()[-1]
    nonfert=seed_n+1e4*(last['RNO3DEPOSTT']+last['RNH4DEPOSTT'])
    fert=scheduler.cumulative;grain=summary['NamountSO'];inputs=fert+nonfert
    return np.array([summary['TWSO']/1000,grain,inputs-grain,grain/inputs,fert,nonfert])


def run_fixed_plan(project_root,region_id,year,plan,*,role='Train',thermal_scale=1.,climate='Historical',record_states=False,version='v1',cultivar='Arminda',root_depth_cm=125.):
    engine,metadata=build_season(project_root,region_id,year,role=role,thermal_scale=thermal_scale,climate=climate,
                                 version=version,cultivar=cultivar,root_depth_cm=root_depth_cm)
    controls=json.loads((Path(project_root)/f'reports/phase5/regional-controls-{version}.json').read_text())
    scheduler=ThreeStageScheduler(controls['seasonal_fertilizer_budget_kg_ha'],initial_base_n=metadata['initial_base_n'])
    if version=='v1':scheduler.windows=((.30,.65),(.65,.90),(.90,1.00))
    requested=None;states={};steps=0
    def guard(action,dvs,day):
        if dvs is None:return 0.
        scheduler.eligible(day,float(dvs))
        return scheduler.execute(day,float(dvs),action,expected_stage=requested) if requested is not None else 0.
    engine._action_guard=guard
    while not engine.terminated and steps<60:
        field=observe(engine,scheduler,region_id)
        requested=field.stage or None
        if requested:
            if record_states:states[requested]=field.__dict__
            dose=float(plan[requested-1])
            dose=min(dose,scheduler.budget-scheduler.cumulative)
        else:dose=0.
        advance_week(engine,dose);steps+=1
    if not engine.terminated:raise ValueError('Season exceeded registered physical horizon')
    outcome=terminal(engine,scheduler)
    physical_fertilizer=1e4*(engine.get_variable('RNH4AMTT')+engine.get_variable('RNO3AMTT'))
    if version=='v2' and not np.isclose(physical_fertilizer,scheduler.cumulative,atol=1e-6):
        raise ValueError('Physical fertilizer and full-season ledger disagree')
    if not np.isfinite(outcome).all():raise ValueError('Non-finite physical outcome')
    summary=engine.get_summary_output()[-1]
    return dict(**metadata,physical_fertilizer_kg_ha=float(physical_fertilizer),outcome=outcome.tolist(),native_weekly_steps=steps,events=scheduler.events,
                dvs_end=summary['DVS'],biomass_dm_kg_ha=summary['TAGP'],transpiration_cm=summary['CTRAT'],
                anthesis=str(summary.get('DOA')),maturity=str(summary.get('DOM')),states=states if record_states else None)
