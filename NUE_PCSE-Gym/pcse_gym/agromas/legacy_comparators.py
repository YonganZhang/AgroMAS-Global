"""Frozen NL calendar/Phase4 references transferred to the registered v2 physics.

These are descriptive reference policies, not information/action-matched PPO arms.
No frozen Phase4 results, source, weights, or old audit roles are rewritten.
"""
from pathlib import Path
from datetime import date,timedelta
from functools import lru_cache
import json,hashlib
import numpy as np
import torch
from .season import build_season,terminal
from .weekly import advance_week
from .final_evaluation import final_stock_diagnostics as stock_diagnostics
from pcse_gym.envs.moisture4 import UtilityScorer
from pcse_gym.envs.corridor import target


class ReferenceLedger:
    def __init__(self,budget):self.budget=budget;self.cumulative=0.;self.events=[];self.last_positive=None


@lru_cache(maxsize=1)
def frozen_phase4_scorer(root):
    p=Path(root)/'reports/phase3c-frozen-utility-v1.json'
    return UtilityScorer(json.loads(p.read_text())),hashlib.sha256(p.read_bytes()).hexdigest()


def outcome_row(engine,meta,ledger,steps,policy):
    m=terminal(engine,ledger);physical=1e4*(engine.get_variable('RNH4AMTT')+engine.get_variable('RNO3AMTT'))
    if not np.isclose(physical,m[4],atol=1e-6):raise ValueError('Referencephysicalfertilizerledgerdrift')
    summary=engine.get_summary_output()[-1]
    return dict(**meta,policy=policy,outcome=m.tolist(),events=ledger.events,native_weekly_steps=steps,
      stock_diagnostics=stock_diagnostics(engine,meta,m),maturity=str(summary.get('DOM')),dvs_end=summary['DVS'],
      comparator_scope='Frozenreferencepolicytransfertoregionalv2physics;notreproductionofoldPhase4weather/background/clockresults')


def run_nl_reference(root,year,*,policy,role,climate,permit_path=None):
    if policy not in ('N2-PA-calendar','Phase4-Forest-transfer'):raise ValueError('UnknownNLreference')
    freeze=json.loads((Path(root)/'reports/phase5/regional-phenology-train-freeze-v2.json').read_text())
    engine,meta=build_season(root,'netherlands_lelystad',year,role=role,climate=climate,version='v2',
        permit_path=permit_path,**freeze['selected']['netherlands_lelystad'])
    if meta['initial_base_n']!=0:raise ValueError('NLreferencebasalmismatch')
    ledger=ReferenceLedger(220. if policy=='N2-PA-calendar' else 210.)
    if policy=='N2-PA-calendar':
        # Native CEA N2-PA calendar/doses; no extra DVS staging constraint imposed.
        scheduled={date(year,2,17):60.,date(year,5,11):80.,date(year,6,21):80.}
        def guard(amount,dvs,day):
            if amount<=0 or dvs is None or engine.flag_terminate:return 0.
            if ledger.last_positive is not None and (day-ledger.last_positive).days<14:raise ValueError('Calendarspacing')
            dose=min(amount,ledger.budget-ledger.cumulative)
            ledger.cumulative+=dose;ledger.last_positive=day
            ledger.events.append(dict(stage=len(ledger.events)+1,date=str(day),dose=dose,reason='fixed_native_N2_PA_calendar',actual_dvs=float(dvs)))
            return dose
        engine._action_guard=guard;days=0
        while not engine.terminated and days<420:
            dose=scheduled.get(engine.day+timedelta(days=1),0.)
            engine.run(days=1,action=dose);days+=1
        if not engine.terminated:raise ValueError('NLreferencehorizon')
        return outcome_row(engine,meta,ledger,(days+6)//7,policy)
    scorer,asset_sha=frozen_phase4_scorer(str(root));torch.set_num_threads(1)
    def guard(amount,dvs,day):
        if amount<=0 or dvs is None or engine.flag_terminate:return 0.
        legal=(dvs is not None and .01<=float(dvs)<=1. and len(ledger.events)<3 and
               (ledger.last_positive is None or (day-ledger.last_positive).days>=14))
        if not legal:return 0.
        dose=min(amount,10*np.floor((ledger.budget-ledger.cumulative)/10))
        if dose>0:
            ledger.cumulative+=dose;ledger.last_positive=day
            ledger.events.append(dict(stage=len(ledger.events)+1,date=str(day),dose=float(dose),reason='frozenPhase4foresttransfer',actual_dvs=float(dvs)))
        return float(dose)
    engine._action_guard=guard;steps=0
    while not engine.terminated and steps<60:
        dvs=float(engine.get_variable('DVS') or 0.);lai=float(engine.get_variable('LAI') or 0.)
        sm=float(np.asarray(engine.get_variable('SM')).ravel()[0])
        observed=[engine.weatherdataprovider(engine.day-timedelta(days=i)) for i in range(6,-1,-1)]
        since=365 if ledger.last_positive is None else (engine.day+timedelta(days=1)-ledger.last_positive).days
        frame=np.array([dvs,lai/10,np.mean([w.IRRAD for w in observed])/1e7,
          np.mean([w.TMIN for w in observed])/30,np.mean([w.RAIN for w in observed])/10,
          ledger.cumulative/400,min(since,365)/365,0.,len(ledger.events)/4,(210-ledger.cumulative)/400,sm],np.float32)
        with torch.no_grad():final=160+10*int(scorer(torch.as_tensor(frame)).argmax()) if .62<=dvs<=.88 else 190
        desired=float(target(dvs,ledger.cumulative,final,(70,130)))
        action=int(np.clip(np.round((desired-ledger.cumulative)/10),0,8));mask=np.zeros(9,bool);mask[0]=True
        remaining=max(0.,210-ledger.cumulative)
        if .10<=dvs<.62:
            needed=int(round((desired-ledger.cumulative)/10));mask[1:]=[i==needed and 10*i<=remaining for i in range(1,9)]
        elif .01<=dvs<=.88:mask[1:]=np.arange(1,9)*10<=remaining
        if since<14 or len(ledger.events)>=3:mask[1:]=False
        action=max(i for i in range(action+1) if mask[i])
        advance_week(engine,10*action);steps+=1
    if not engine.terminated:raise ValueError('NLreferencehorizon')
    row=outcome_row(engine,meta,ledger,steps,policy);row['phase4_frozen_asset_sha256']=asset_sha
    row['reference_budget_kg_ha']=210.;return row
