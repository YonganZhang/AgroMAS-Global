"""Once-sealed final physicalbook campaign, never a training/selection datasource."""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ProcessPoolExecutor,as_completed
import argparse,json,hashlib,logging,multiprocessing
import numpy as np
from pcse_gym.agromas.season import build_season,observe,terminal,regional_weather,_template
from pcse_gym.agromas.scheduler import ThreeStageScheduler
from pcse_gym.agromas.weekly import advance_week
from pcse_gym.agromas.final_evaluation import final_stock_diagnostics as stock_diagnostics
from pcse_gym.agromas.regions import load_split_manifest,authorize_year,REGIONS
from pcse_gym.agromas.runtime import GRID
from itertools import product
from pcse_gym.agromas.final_evaluation import validate_external_dependency
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5';O=R/'data/phase5-final-evaluation-books-v4'
PERMIT=P/'final-evaluation-permit-v4.json'


def physical_plan(name,year,climate,role,selection,plan,permit):
    e,meta=build_season(str(R),name,year,role=role,climate=climate,version='v2',permit_path=permit,**selection)
    scheduler=ThreeStageScheduler(220.,initial_base_n=meta['initial_base_n']);requested=None;states={};steps=0
    def guard(dose,dvs,day):
        if dvs is None:return 0.
        scheduler.eligible(day,float(dvs))
        return scheduler.execute(day,float(dvs),dose,expected_stage=requested) if requested is not None else 0.
    e._action_guard=guard
    while not e.terminated and steps<60:
        state=observe(e,scheduler,name);requested=state.stage or None
        if requested:
            states[requested]=state.__dict__;dose=min(float(plan[requested-1]),220-scheduler.cumulative)
        else:dose=0.
        advance_week(e,dose);steps+=1
    if not e.terminated:raise ValueError('Finalphysicalhorizon')
    m=terminal(e,scheduler);diagnostic=stock_diagnostics(e,meta,m)
    if not np.isfinite(m).all() or abs(diagnostic['soil_N_mass_balance_residual_kg_ha'])>1e-4 or abs(diagnostic['native_fertilizer_N_kg_ha']-m[4])>1e-6:raise ValueError('Finalphysicalmassbalance')
    return dict(status='completed',**meta,plan=list(plan),outcome=m.tolist(),events=scheduler.events,states=states,
       stock_diagnostics=diagnostic,native_weekly_steps=steps,physical_crop_end_day=str(e.day),crop_control_integrated_days=(e.day-REGIONS[name].crop_dates(year)[0]).days,total_integrated_physical_days=meta['warmup_physical_days']+(e.day-REGIONS[name].crop_dates(year)[0]).days)


def run(job):
    name,year,climate,role,selection=job;path=O/f'{name}-{year}-{climate}-{role}.jsonl';failures=0;steps=0;days=0;event_sequences=set()
    with path.open('x') as f:
        for plan in product(GRID,repeat=3):
            try:
                row=physical_plan(name,year,climate,role,selection,plan,str(PERMIT));steps+=row['native_weekly_steps'];days+=row['total_integrated_physical_days'];event_sequences.add(json.dumps(row['events'],sort_keys=True))
            except Exception as error:
                row=dict(status='failed',region_id=name,harvest_year=year,climate=climate,role=role,plan=plan,error=repr(error));failures+=1
            f.write(json.dumps(row,default=str)+'\n');f.flush()
    path.chmod(0o444)
    return dict(path=str(path.relative_to(R)),rows=343,failed=failures,distinct_executed_event_sequences=len(event_sequences),physical_native_weekly_steps=steps,total_integrated_physical_days=days,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--workers',type=int,choices=[32,48],default=48)
    args=parser.parse_args();logging.disable(logging.CRITICAL)
    permit=json.loads(PERMIT.read_text());assert permit['all_models_frozen'] and permit['subsidy_train_frozen']
    assert hashlib.sha256(PERMIT.read_bytes()).hexdigest()==PERMIT.with_suffix('.sha256').read_text().strip()
    validate_external_dependency(R,PERMIT)
    # One campaign claim; failure recovery must be a separately audited missing-only pass.
    claim=P/'final-evaluation-campaign-claim-v4.json'
    with claim.open('x') as f:json.dump(dict(status='claimed_once',started_UTC=datetime.now(timezone.utc).isoformat(),
        permit_sha256=hashlib.sha256(PERMIT.read_bytes()).hexdigest(),no_model_selection=True),f,indent=2)
    claim.chmod(0o444)
    m=load_split_manifest(P/'global-date-split-manifest.json');selection=json.loads((P/'regional-phenology-train-freeze-v2.json').read_text())['selected']
    O.mkdir(parents=True,exist_ok=False);jobs=[]
    for name in m['regions']:
        regional_weather(str(R),name,'v2')
        for role in ('Held-Out','Public-Reused-Benchmark'):
            for year in m['regions'][name]['roles'][role]:
                authorize_year(m,name,year,role,permit_path=PERMIT,project_root=R)
                for climate in ('Historical','idealized_mid','idealized_high'):jobs.append((name,year,climate,role,selection[name]))
    assert len(jobs)==177;_template(str(R));receipts=[]
    with (P/'final-physical-book-progress-v4.jsonl').open('x') as log:
        with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('fork')) as pool:
            for future in as_completed([pool.submit(run,j) for j in jobs]):
                r=future.result();receipts.append(r);log.write(json.dumps(r)+'\n');log.flush();print(json.dumps(dict(completed=len(receipts),total=177,failed=r['failed'])),flush=True)
    validate_external_dependency(R,PERMIT)
    out=P/'final-physical-book-receipt-v4.json'
    with out.open('x') as f:json.dump(dict(status='completed' if all(r['failed']==0 for r in receipts) else 'failures_retained',
        files=receipts,physical_simulation_invocations=sum(r['rows'] for r in receipts),distinct_requested_plan_world_keys=sum(r['rows'] for r in receipts),distinct_executed_event_sequences=sum(r['distinct_executed_event_sequences'] for r in receipts),total_integrated_physical_days=sum(r['total_integrated_physical_days'] for r in receipts),failures=sum(r['failed'] for r in receipts),
        independent_weather_seasons=52,public_reused_weather_seasons=7,climate_sensitivities=3,intervention_plans=343,
        permit_sha256=hashlib.sha256(PERMIT.read_bytes()).hexdigest(),training_or_selection_use=False),f,indent=2)
    out.chmod(0o444)
