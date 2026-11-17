"""One real-regional weekly environment for trained PPO and deterministic policies.

All arms use the same frozen outcome/forecast tables, ecological filter, observed
state, prices and physical execution guard. This module never loads teacher books.
"""
from pathlib import Path
from functools import lru_cache
from datetime import timedelta
import hashlib,json
import joblib,numpy as np
from .baseline import WofostWeeklyEnv,SharedControlConfig
from .season import build_season,observe,terminal,regional_weather
from .features import shared_features,soil_context
from .contracts import CandidateTable,compliance
from .core_agronomic_agent import CoreAgronomicAgent,AgroMASGlobalCoordinator,select_objective
from .urban_eco_agent import UrbanEcoSafetyAgent,SoilHydraulicContext,EcoResult
from .socio_econ_agent import SocioEconomicPolicyAgent,EconomicPolicy
from .regions import REGIONS
GRID=(0.,10.,20.,40.,60.,80.,100.)
CLIMATES=('Historical','idealized_mid','idealized_high')
ZONES=('strict_25','buffer_35','outer_50')
TRAIN_ZONES=ZONES+('standard_40',)  # Include the main40cap, not just interpolation at evaluation.
SUBSIDIES=(0.,50.,100.,150.,200.)
OBS_NAMES=tuple([f'causal_{i}' for i in range(22)]+['cap','N_price','grain_price','subsidy','beta']+
                [f'action_{i}_{j}' for i in range(7) for j in ('dose','yield','grain_N','surplus_upper','NUE','Nfert','profit','joint_probability')]+
                [f'legal_{i}' for i in range(7)])


@lru_cache(maxsize=3)
def outcome_model(root,stage):
    return joblib.load(Path(root)/'models/phase5/continuation-v2'/f'stage-{stage}.joblib')


@lru_cache(maxsize=24)
def variant_model(root,stage,family):
    return joblib.load(Path(root)/f'models/phase5/continuation-{family}-v2'/f'stage-{stage}.joblib')


class BudgetOnlyEco(UrbanEcoSafetyAgent):
    """Ablation: remove surplus risk filter, retain identical physical dose budget."""
    def filter(self,table,remaining_budget,agronomic_upper):
        diagnostic=super().filter(table,remaining_budget,agronomic_upper)
        mask=table.doses<=min(remaining_budget,agronomic_upper)
        doses=tuple(float(x) for x in table.doses[mask])
        return EcoResult(table.subset(mask) if doses else None,doses,max(doses,default=0.),
                         diagnostic.violation_probability,0.,not bool(doses))


class RegionalWeeklyEnv(WofostWeeklyEnv):
    def __init__(self,project_root,*,beta,role='Train',evaluation=None,information_mode='structured-shared',variant='A4'):
        self.root=str(Path(project_root).resolve());self.role=role;self.evaluation=evaluation
        if variant not in ('A0','A1','A2','A2-oracle','A3','A4','LOAO-climate','LOAO-eco','LOAO-core-state','LOAO-economics','monolithic','DVS-N2'):
            raise ValueError('Unregistered policy variant')
        self.variant=variant
        if information_mode not in ('raw-shared','structured-shared'):raise ValueError('Unknown information mode')
        self.information_mode=information_mode
        names=OBS_NAMES if information_mode=='structured-shared' else tuple(
            [f'causal_{i}' for i in range(22)]+['cap','N_price','grain_price','subsidy','beta']+
            [f'past_weather_{i}' for i in range(42)]+[f'legal_{i}' for i in range(7)])
        r=Path(self.root)
        self.freeze=json.loads((r/'reports/phase5/regional-phenology-train-freeze-v2.json').read_text())
        controls_path=r/'reports/phase5/regional-controls-v2.json'
        controls=json.loads(controls_path.read_text())
        config=SharedControlConfig(GRID,220.,0.,names,information_mode,hashlib.sha256(controls_path.read_bytes()).hexdigest(),
                beta=beta,eta=0.,regional_base_n=tuple(controls['regional_basal_n_kg_ha'].items()))
        super().__init__(self._factory,self._encode,self._terminal,UrbanEcoSafetyAgent(),
                         SocioEconomicPolicyAgent(EconomicPolicy(1.5,.2)),config)

    def _terminal(self,engine,scheduler):
        result=terminal(engine,scheduler)
        physical=1e4*(engine.get_variable('RNH4AMTT')+engine.get_variable('RNO3AMTT'))
        if not np.isclose(result[4],physical,atol=1e-6):
            raise ValueError('Runtime physical fertilizer and shared ledger disagree')
        return result

    def _factory(self,rng,options):
        if self.evaluation is None:
            if self.role!='Train':raise ValueError('Explicit frozen evaluation episode required')
            names=tuple(REGIONS);name=names[int(rng.integers(5))]
            year=int(rng.integers(1995,2010));climate=CLIMATES[int(rng.integers(3))]
            zone=TRAIN_ZONES[int(rng.integers(len(TRAIN_ZONES)))];price_mult=(1.,2.)[int(rng.integers(2))]
            subsidy=SUBSIDIES[int(rng.integers(5))];permit=None
        else:
            e=self.evaluation
            name=e['region_id'];year=e['year'];climate=e['climate'];zone=e['zone']
            price_mult=e['price_multiplier'];subsidy=e['subsidy'];permit=e.get('permit_path')
        self.name=name;self.climate=climate
        fc,wp,logk=soil_context(self.root,name)
        profile=SoilHydraulicContext('v2-'+name,name,self.config.source_config_id,'medium',float(fc),float(wp),float(10**logk))
        eco_class=BudgetOnlyEco if self.variant in ('A0','A1','A2','A2-oracle','LOAO-eco','DVS-N2') else UrbanEcoSafetyAgent
        self.eco=eco_class(zone,epsilon=.1,dual=0.,dual_rate=0.,soil_profile=profile)
        self.economics=SocioEconomicPolicyAgent(EconomicPolicy(1.5*price_mult,.20,subsidy=subsidy))
        engine,meta=build_season(self.root,name,year,role=self.role,climate=climate,version='v2',
                                 permit_path=permit,**self.freeze['selected'][name])
        meta.update(variant=self.variant,zone=zone,cap=self.eco.cap,price_multiplier=price_mult,subsidy=subsidy)
        return engine,meta

    def _model(self,stage):
        family={'A0':'A1','LOAO-economics':'A3','DVS-N2':'A1'}.get(self.variant,self.variant)
        return outcome_model(self.root,stage) if family in ('A4','monolithic') else variant_model(self.root,stage,family)

    def _encode(self,engine,scheduler):
        field=observe(engine,scheduler,self.name)
        base=shared_features(self.root,field.__dict__,self.climate)
        if self.variant in ('A0','A1','LOAO-climate'):base[6:10]=0.
        if self.variant=='LOAO-core-state':base[[0,1,2,4]]=0.
        if self.variant=='A2-oracle':
            from .oracle import oracle_vector
            base[6:10]=oracle_vector(self.root,self.name,engine.day,self.climate,role=self.role,
                harvest_year=self.episode_metadata['harvest_year'],
                permit_path=self.evaluation.get('permit_path') if self.evaluation else None)
        def predictor(rows):
            # Unaffordable grid entries are explicit placeholders, excluded by
            # the common budget mask. They are never queried from a fitted model.
            members=np.zeros((len(rows),32,6));fert=rows[:,3]+rows[:,-1]
            members[:,:,4]=fert[:,None];members[:,:,5]=3.5
            members[:,:,2]=fert[:,None]+3.5
            legal=fert<=220+1e-8
            if field.stage and np.any(legal):members[legal]=self._model(field.stage)(rows[legal])
            return members
        core=CoreAgronomicAgent(predictor,'no-stage-placeholder' if not field.stage else self._model(field.stage).model_id,
                                'backward-reference-cap40-no-subsidy-v2')
        table=core.candidates(field,np.array(GRID),base[6:10],base[10:],'v2-'+self.name)
        safe=self.eco.filter(table,220-scheduler.cumulative,100.) if field.stage else None
        mask=np.array([d in safe.safe_doses for d in GRID],float) if safe is not None else np.array([1.,0,0,0,0,0,0])
        if not np.any(mask):mask[0]=1.
        econ=self.economics.price(table,self.eco.cap)
        m=table.members
        action=np.c_[np.array(GRID)/100,m[:,:,0].mean(1)/12,m[:,:,1].mean(1)/200,
                np.quantile(m[:,:,2],.9,axis=1,method='higher')/200,m[:,:,3].mean(1)/2,
                m[:,:,4].mean(1)/220,econ['expected_profit']/3000,compliance(m,self.eco.cap).mean(1)]
        policy=self.economics.policy
        economic_context=[self.eco.cap/50,policy.nitrogen_price/3,policy.grain_price/.2,policy.subsidy/200,self.config.beta/200]
        if self.information_mode=='structured-shared':
            obs=np.r_[base,economic_context,action.ravel(),mask]
        else:
            history=regional_weather(self.root,self.name,'v2').history(
                engine.day-timedelta(days=6),engine.day,as_of=engine.day)
            obs=np.r_[base,economic_context,history.values.ravel(),mask]
        return dict(observation=obs,candidate_table=table,agronomic_upper=100.)

    def step(self,action):
        obs,reward,ended,truncated,info=super().step(action)
        if ended:
            from .stock_diagnostics import stock_diagnostics
            info['stock_diagnostics']=stock_diagnostics(self.engine,self.episode_metadata,info['outcome'])
        return obs,reward,ended,truncated,info

    def coordinated_action(self,*,beta=None):
        stage=self.scheduler.preview(self.engine.day+timedelta(days=1),float(self.engine.get_variable('DVS') or 0))
        if not stage:return 0
        remaining=220-self.scheduler.cumulative
        if self.variant=='DVS-N2' or self.variant=='A0' and stage<3:
            if self.variant=='DVS-N2':target=(60.,80.,80.)[stage-1]
            else:
                selected=json.loads((Path(self.root)/'reports/phase5/A0-fixed-first-two-train-freeze-v2.json').read_text())['selected']
                target=selected[self.name][stage-1]
            return GRID.index(max(d for d in GRID if d<=min(target,remaining)))
        table=self.context['candidate_table'];safe=self.eco.filter(table,remaining,100.)
        if safe.predicted_infeasible:return 0
        if self.variant in ('A0','A1','A2','A2-oracle','A3','LOAO-economics'):
            means=safe.table.members[:,:,0].mean(1)
            dose=float(safe.table.doses[np.lexsort((safe.table.doses,-means))[0]])
            return GRID.index(dose)
        weight=self.config.beta if beta is None else beta
        coordinator=AgroMASGlobalCoordinator(self.eco,self.economics,weight,0.)
        decision=coordinator.choose(table,remaining,100.)
        reference=select_objective(safe.table,self.economics.price(safe.table,self.eco.cap),self.eco.cap,weight,0.)
        if decision.dose!=reference.dose:raise AssertionError('Matched monolithic/table identity failed')
        return GRID.index(reference.dose if self.variant=='monolithic' else decision.dose)
