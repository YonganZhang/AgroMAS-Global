"""TRAIN intervention-book replay with an observable-only controller boundary.

The controller receives a current state, not terminal labels or the book. The
outer replay retrieves the next physical trajectory only AFTER an action is fixed.
"""
from datetime import date
from types import SimpleNamespace
from pathlib import Path
import hashlib,json
from .runtime import RegionalWeeklyEnv,UrbanEcoSafetyAgent,BudgetOnlyEco,GRID
from .socio_econ_agent import SocioEconomicPolicyAgent,EconomicPolicy


class ObservableReplayEngine:
    def __init__(self,state):
        self.day=date.fromisoformat(state['as_of']) if isinstance(state['as_of'],str) else state['as_of']
        self.current={'DVS':state['dvs'],'LAI':state['lai'],'SM':state['sm'],'NuptakeTotal':state['n_uptake']}
    def get_variable(self,name):
        if name not in self.current:raise ValueError('Replay controller requested non-observable:'+name)
        return self.current[name]


def action_for_state(root,state,*,year,climate,zone,price_multiplier,subsidy,beta,variant='A4'):
    # __new__ bypasses physical season construction, not the shared controller.
    e=RegionalWeeklyEnv.__new__(RegionalWeeklyEnv)
    e.root=str(Path(root).resolve());e.name=state['region_id'];e.role='Train';e.variant=variant
    e.climate=climate;e.information_mode='structured-shared';e.evaluation={}
    e.episode_metadata=dict(harvest_year=year)
    e.config=SimpleNamespace(beta=beta)
    stage=int(state['stage'])
    e.scheduler=SimpleNamespace(cumulative=float(state['n_fert_cum']),preview=lambda *args:stage)
    e.engine=ObservableReplayEngine(state)
    cls=BudgetOnlyEco if variant in ('A0','A1','A2','A2-oracle','LOAO-eco','DVS-N2') else UrbanEcoSafetyAgent
    e.eco=cls(zone);e.economics=SocioEconomicPolicyAgent(EconomicPolicy(1.5*price_multiplier,.2,subsidy=subsidy))
    e.context=e._encode(e.engine,e.scheduler)
    index=e.coordinated_action()
    return GRID[index],dict(predicted_infeasible=e.eco.filter(e.context['candidate_table'],220-e.scheduler.cumulative,100.).predicted_infeasible,
                           observed_day=str(e.engine.day),model_id=e.context['candidate_table'].model_id)


def replay_book(root,book,*,year,climate,zone,price_multiplier,subsidy,beta,variant='A4'):
    plan=[0.,0.,0.];row=book[tuple(plan)];trace=[]
    if row['role']!='Train':raise ValueError('Intervention book replay is TRAIN only')
    for stage in (1,2,3):
        state=row['states'].get(str(stage))
        if state is not None:
            dose,diagnostic=action_for_state(root,state,year=year,climate=climate,zone=zone,
                price_multiplier=price_multiplier,subsidy=subsidy,beta=beta,variant=variant)
            plan[stage-1]=dose;trace.append(dict(stage=stage,dose=dose,**diagnostic))
        row=book[tuple(plan)]
    m=row['outcome'];cap={'strict_25':25.,'buffer_35':35.,'standard_40':40.,'outer_50':50.}[zone]
    joint=.5<=m[3]<=.9 and m[2]<=cap
    profit=200*m[0]-1.5*price_multiplier*m[4]+subsidy*joint
    return dict(region_id=row['region_id'],year=year,climate=climate,role='Train',variant=variant,zone=zone,cap=cap,
       price_multiplier=price_multiplier,subsidy=subsidy,beta=beta,plan=plan,events=row['events'],outcome=m,
       joint=bool(joint),partial_profit=float(profit),trace=trace,simulation_source='FrozenTRAINinterventionbook;observableonlydecisions')
