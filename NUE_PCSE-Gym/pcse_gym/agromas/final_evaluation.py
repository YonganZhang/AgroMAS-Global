"""Frozen-policy replay on once-unlocked final physical intervention books.

Current-state engine objects expose no terminal outcome/book to the controller.
MLP evaluation is deterministic with frozen normalization; skipping no-decision
weeks cannot change hidden state because these PPO actors are feedforward.
"""
from pathlib import Path
from types import SimpleNamespace
from functools import lru_cache
import json,pickle,hashlib
import numpy as np
from sb3_contrib import MaskablePPO
from .runtime import RegionalWeeklyEnv,UrbanEcoSafetyAgent,BudgetOnlyEco,GRID,SoilHydraulicContext,soil_context
from .replay import ObservableReplayEngine
from .socio_econ_agent import SocioEconomicPolicyAgent,EconomicPolicy
from .regions import load_split_manifest,authorize_year


@lru_cache(maxsize=6)
def ppo_assets(root,mode,seed):
    d=Path(root)/f'models/phase5/ppo-{mode}-seed{seed}-v4'
    receipt=json.loads((d/'receipt.json').read_text())
    if receipt['status']!='completed':raise ValueError('PPOnotfrozen')
    for name in ('model.zip','vecnormalize.pkl'):
        if hashlib.sha256((d/name).read_bytes()).hexdigest()!=receipt['files'][name]:raise ValueError('PPOassetdrift:'+name)
    model=MaskablePPO.load(d/'model.zip',device='cpu');model.policy.set_training_mode(False)
    with (d/'vecnormalize.pkl').open('rb') as f:normalizer=pickle.load(f)
    normalizer.training=False;normalizer.norm_reward=False
    return model,normalizer


def decision_context(root,state,meta,*,zone,price_multiplier,subsidy,beta,variant,mode,permit_path):
    e=RegionalWeeklyEnv.__new__(RegionalWeeklyEnv)
    e.root=str(Path(root).resolve());e.name=state['region_id'];e.role=meta['role'];e.variant=variant
    e.climate=meta['climate'];e.information_mode=mode;e.evaluation={'permit_path':permit_path}
    e.episode_metadata=meta;e.config=SimpleNamespace(beta=beta,budget=220.,dose_grid=GRID,source_config_id=hashlib.sha256((Path(e.root)/'reports/phase5/regional-controls-v2.json').read_bytes()).hexdigest())
    stage=int(state['stage']);e.scheduler=SimpleNamespace(cumulative=float(state['n_fert_cum']),preview=lambda *args:stage)
    e.engine=ObservableReplayEngine(state)
    cls=BudgetOnlyEco if variant in ('A0','A1','A2','A2-oracle','LOAO-eco','DVS-N2') else UrbanEcoSafetyAgent
    fc,wp,logk=soil_context(e.root,e.name)
    profile=SoilHydraulicContext('v2-'+e.name,e.name,e.config.source_config_id,'medium',float(fc),float(wp),float(10**logk))
    e.eco=cls(zone,epsilon=.1,dual=0.,dual_rate=0.,soil_profile=profile);e.economics=SocioEconomicPolicyAgent(EconomicPolicy(1.5*price_multiplier,.2,subsidy=subsidy))
    e.context=e._encode(e.engine,e.scheduler)
    return e


def replay_final_book(root,book,*,zone,price_multiplier,subsidy,beta,policy,permit_path,seed=None,mode='structured-shared'):
    row=book[(0.,0.,0.)];meta={k:row[k] for k in ('region_id','harvest_year','climate','role')}
    if meta['role'] not in ('Held-Out','Public-Reused-Benchmark','Train'):raise ValueError('NorepeatedDevpolicycampaign')
    authorize_year(load_split_manifest(Path(root)/'reports/phase5/global-date-split-manifest.json'),meta['region_id'],meta['harvest_year'],
                   meta['role'],permit_path=permit_path,project_root=root)
    variant='A4' if policy=='PPO' else policy
    plan=[0.,0.,0.];trace=[]
    for stage in (1,2,3):
        state=row['states'].get(str(stage))
        if state is not None:
            clipping={}
            e=decision_context(root,state,meta,zone=zone,price_multiplier=price_multiplier,subsidy=subsidy,beta=beta,
                variant=variant,mode=mode,permit_path=permit_path)
            if policy=='PPO':
                model,normalizer=ppo_assets(str(root),mode,seed)
                raw=np.asarray(e.context['observation'],np.float32)[None]
                if normalizer.norm_obs:
                    z=(raw-normalizer.obs_rms.mean)/np.sqrt(normalizer.obs_rms.var+normalizer.epsilon)
                    indices=np.flatnonzero(np.abs(z[0])>normalizer.clip_obs).tolist()
                    critical=[i for i in indices if 22<=i<27 or (mode=='structured-shared' and (i>=83 or 27<=i<83 and (i-27)%8 in (6,7))) or (mode=='raw-shared' and i>=69)]
                    clipping=dict(clipped_observation_indices=indices,clipped_objective_or_mask_indices=critical,normalizer_frozen=True,clip_obs=normalizer.clip_obs)
                observation=normalizer.normalize_obs(raw)
                masks=e.action_masks();action=int(np.asarray(model.predict(observation,deterministic=True,action_masks=masks)[0]).ravel()[0])
                if not masks[action]:raise ValueError('PPOselectedmaskedaction')
            else:action=e.coordinated_action()
            plan[stage-1]=GRID[action]
            safe=e.eco.filter(e.context['candidate_table'],220-e.scheduler.cumulative,100.)
            trace.append(dict(stage=stage,dose=GRID[action],observed_day=str(e.engine.day),
                predicted_infeasible=safe.predicted_infeasible,model_id=e.context['candidate_table'].model_id,**clipping))
        row=book[tuple(plan)]
    m=row['outcome'];cap={'strict_25':25.,'buffer_35':35.,'standard_40':40.,'outer_50':50.}[zone]
    joint=.5<=m[3]<=.9 and m[2]<=cap
    return dict(**meta,zone=zone,cap=cap,price_multiplier=price_multiplier,subsidy=subsidy,policy=policy,
        seed=seed,information_mode=mode if policy=='PPO' else 'deterministic-specialists',beta=beta,
        outcome=m,plan=plan,events=row['events'],partial_profit=float(200*m[0]-1.5*price_multiplier*m[4]+subsidy*joint),
        joint=bool(joint),NUE_compliant=bool(.5<=m[3]<=.9),surplus_upper_compliant=bool(m[2]<=cap),
        surplus_corridor_compliant=bool(0<=m[2]<=cap),stock_diagnostics=row['stock_diagnostics'],
        native_weekly_steps=row['native_weekly_steps'],trace=trace,
        physical_source_id=f"{meta['region_id']}:{meta['harvest_year']}:{meta['climate']}:{','.join(map(str,plan))}")


def validate_external_dependency(root,permit_path):
    """Verify external read-only PCSE once before/after each final campaign."""
    import hashlib,subprocess
    root=Path(root).resolve();pcse=(root/'pcse').resolve();path=Path(permit_path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=path.with_suffix('.sha256').read_text().strip():raise ValueError('Finalpermitdrift')
    permit=json.loads(path.read_text());expected=permit['external_dependency']
    from importlib.metadata import version
    for name,expected_version in permit.get('runtime_versions',{}).items():
        if version(name)!=expected_version:raise ValueError('Runtimeversiondrift:'+name)
    from .regions import frozen_asset_sha
    for relative,digest in permit['files'].items():
        target=(root/relative).resolve()
        if not target.is_relative_to(root) or frozen_asset_sha(target)!=digest:raise ValueError('Finalassetdrift:'+relative)
    actual=subprocess.check_output(['git','-C',str(pcse),'rev-parse','HEAD'],text=True).strip()
    if actual!=expected['commit']:raise ValueError('PCSEcommitdrift')
    if subprocess.check_output(['git','-C',str(pcse),'status','--porcelain'],text=True).strip():raise ValueError('PCSEdirty')
    for relative,digest in expected['files'].items():
        if hashlib.sha256((pcse/relative).read_bytes()).hexdigest()!=digest:raise ValueError('PCSEsourcedrift:'+relative)


def final_stock_diagnostics(engine,metadata,outcome):
    """Add native integrated organic-C flux closure to frozen N/stock outputs."""
    from .stock_diagnostics import stock_diagnostics
    result=stock_diagnostics(engine,metadata,outcome)
    def total(name):
        value=engine.get_variable(name)
        if value is None:raise ValueError('Missingnativecarbonflux:'+name)
        return 1e4*float(np.asarray(value).sum())
    applied=total('RCORGAMTT');dissimilation=total('RCORGDISTT')
    residual=result['initial_soil_C_kg_ha']+applied-result['final_soil_C_kg_ha']-dissimilation
    if abs(residual)>1e-4:raise ValueError('NativeorganicCmassbalance')
    result.update(native_organic_C_applied_kg_ha=applied,native_organic_C_dissimilation_kg_ha=dissimilation,soil_C_mass_balance_residual_kg_ha=residual)
    return result
