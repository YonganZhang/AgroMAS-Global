"""External read-only WOFOST referee, never given to a decision specialist."""
from pathlib import Path
from contextlib import contextmanager
from datetime import date,timedelta
import hashlib,json
import numpy as np
from pcse.input import CSVWeatherDataProvider
from pcse_gym.agromas import season
from pcse_gym.agromas.scheduler import ThreeStageScheduler
from pcse_gym.agromas.weekly import advance_week
from pcse_gym.agromas.final_evaluation import final_stock_diagnostics
from pcse_gym.agromas.climate_agent import WeatherHistory
from .online_features import history_from_provider

class WURHistoricalWeather:
 def __init__(self,root):
  p=Path(root)/'data/52.57-5.63_random_weather.csv';self.base=CSVWeatherDataProvider(str(p));self.source_id=hashlib.sha256(p.read_bytes()).hexdigest()
 def __getattr__(self,name):return getattr(self.base,name)
 def __call__(self,day,member_id=0):
  if member_id:raise ValueError('Historic deterministic source')
  if not 1982<=day.year<=2021:raise ValueError('WUR historic-year rows only; synthetic-year rows forbidden')
  return self.base(day)
 def history(self,start,end,*,as_of):
  if end>as_of:raise ValueError('Future WUR weather denied')
  days=tuple(start+timedelta(days=i) for i in range((end-start).days+1));values=[]
  for d in days:
   w=self(d);t=(w.TMIN+w.TMAX)/2;sat=.6108*np.exp(17.27*t/(t+237.3));rh=np.clip(w.VAP/10/sat*100,0,100);values.append([w.TMIN,w.TMAX,w.IRRAD/1e6,w.RAIN*10,rh,w.WIND])
  return WeatherHistory(days,np.array(values),'netherlands_lelystad',self.source_id)

@contextmanager
def weather_source(root,source):
 # Each evaluation worker owns one serial native engine. The old source file is
 # untouched; only construction resolves the requested external weather driver.
 old=season.regional_weather
 if source=='WUR':
  wur=WURHistoricalWeather(root)
  season.regional_weather=lambda project,name,version='v2':wur if name=='netherlands_lelystad' else old(project,name,version)
 try:yield
 finally:season.regional_weather=old

def prepare_daily_outputs(root):
 from pcse_gym.agromas_v8.ledger import DAILY
 season._template(str(root));conf=Path(root)/'cache/phase5-regional-config/Wofost81_NWLP_MLWB_SNOMIN.conf'
 text=conf.read_text()
 if '# Phase8 evaluation output-only extension' not in text:
  conf.write_text(text+'\n# Phase8 evaluation output-only extension\nOUTPUT_VARS=list(dict.fromkeys(OUTPUT_VARS+'+repr(list(DAILY))+'))\n')
 season._template.cache_clear()

def run_episode(root,case,policy,permit):
 selected=json.loads((Path(root)/'reports/phase5/regional-phenology-train-freeze-v2.json').read_text())['selected'][case['region']]
 with weather_source(root,case.get('source','NASA')):
  engine,meta=season.build_season(str(root),case['region'],case['year'],role=case['role'],version='v2',climate='Historical',permit_path=str(permit),**selected)
 scheduler=ThreeStageScheduler(220,initial_base_n=meta['initial_base_n']);requested=None;trace=[];steps=0
 def guard(amount,dvs,day):
  if dvs is None:return 0.
  scheduler.eligible(day,float(dvs))
  return scheduler.execute(day,float(dvs),amount,expected_stage=requested) if requested is not None else 0.
 engine._action_guard=guard
 while not engine.terminated and steps<60:
  state=season.observe(engine,scheduler,case['region']);requested=state.stage or None;dose=0.
  if requested:
   fields=state.__dict__.copy();fields['as_of']=str(fields['as_of']);fields['days_since_last_fert']=min(60,(engine.day-scheduler.last_positive).days) if scheduler.last_positive else 60;fields['climate']='Historical'
   # Only the current weather history snapshot, never the engine, is passed.
   history=history_from_provider(engine.weatherdataprovider,case['region'],engine.day)
   decision=policy.choose(fields,history,case)
   if decision.get('defer',False):requested=None
   else:dose=float(decision['dose'])
   if dose not in (0,10,20,40,60,80,100) or dose>220-scheduler.cumulative+1e-8:raise ValueError('Policy structural action violation')
   trace.append({'stage':state.stage,'as_of':fields['as_of'],'dose':dose,'tier':decision.get('tier'),'deferred':decision.get('defer',False),'reason':decision.get('reason'),'applicable':decision.get('applicable'),'OOD_score':decision.get('OOD_score'),'request_hash':decision.get('request_hash'),'active_eco':decision.get('active_eco',True),'active_econ':decision.get('active_econ',True),'radius':decision.get('radius'),'prior_accepted':decision.get('prior_accepted'),'prior_timing_admissible':decision.get('prior_timing_admissible'),'prior_ood':decision.get('prior_ood'),'prior_kind':decision.get('prior_kind')})
  advance_week(engine,dose);steps+=1
 if not engine.terminated:raise ValueError('Native seasonal horizon exceeded')
 outcome=season.terminal(engine,scheduler);diag=final_stock_diagnostics(engine,meta,outcome)
 from .ledger import audit_native_engine
 audit=audit_native_engine(engine,meta,outcome)
 dates=[date.fromisoformat(e['date']) for e in scheduler.events if e['dose']>0];assert all((b-a).days>=14 for a,b in zip(dates,dates[1:]));assert outcome[4]<=220+1e-8
 cap=case.get('cap',40.);joint=bool(.5<=outcome[3]<=.9 and 0<=outcome[2]<=cap);profit=float(200*outcome[0]-1.5*case.get('price_multiplier',1)*outcome[4]+case.get('subsidy',0)*joint-case.get('tax',0)*max(outcome[2],0))
 return {'case':case,'outcome':outcome.tolist(),'joint':joint,'partial_profit':profit,'NUE_compliant':bool(.5<=outcome[3]<=.9),'surplus_compliant':bool(0<=outcome[2]<=cap),'Native_N_loss':diag['native_Nloss_kg_ha'],'stock_diagnostics':diag,'mass_audit':audit,'events':scheduler.events,'trace':trace,'native_weekly_steps':steps,'weather_source_id':meta['weather_source_id'],'physics_referee':'externalWOFOST81-SNOMIN','field_measurement':False}

def run_native_nl_reference(root,case,permit):
 """Separate descriptive native-clock references, with100%daily mass audit."""
 from pcse_gym.agromas import legacy_comparators as legacy
 from .ledger import audit_native_engine
 old=legacy.outcome_row
 def audited(engine,meta,ledger,steps,policy):
  row=old(engine,meta,ledger,steps,policy);row['mass_audit']=audit_native_engine(engine,meta,np.asarray(row['outcome']));return row
 legacy.outcome_row=audited
 try:
  with weather_source(root,case.get('source','NASA')):
   row=legacy.run_nl_reference(str(root),case['year'],policy=case['policy'],role=case['role'],climate='Historical',permit_path=str(permit))
 finally:legacy.outcome_row=old
 m=np.asarray(row['outcome']);cap=case.get('cap',40);joint=bool(.5<=m[3]<=.9 and 0<=m[2]<=cap)
 row.update(case=case,joint=joint,partial_profit=float(200*m[0]-1.5*case.get('price_multiplier',1)*m[4]+case.get('subsidy',0)*joint),NUE_compliant=bool(.5<=m[3]<=.9),surplus_compliant=bool(0<=m[2]<=cap),Native_N_loss=row['stock_diagnostics']['native_Nloss_kg_ha'],trace=[],physics_referee='externalWOFOST81-SNOMIN',field_measurement=False)
 return row
