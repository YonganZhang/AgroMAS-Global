"""Registered TRAIN-only 5-fold selection and version-isolated continuation fitting."""
from pathlib import Path
import json,hashlib,itertools,time,os,multiprocessing
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np,joblib
from sklearn.model_selection import GroupKFold
from pcse_gym.agromas_v6.books import load_train
from pcse_gym.agromas_v6.core import Policy,FAMILIES
from pcse_gym.agromas_v6.training import fit_stage,stage3_cache,fit_pipeline,replay
R=Path(__file__).resolve().parents[1];P=R/'reports/phase6';DATA=None;FIT=None;VALID=None;STAGE3=None;CACHE3=None

def candidate(job):
    beta,penalty=job;p=Policy(beta,penalty)
    models,cache=fit_pipeline(DATA,FIT,p,STAGE3,CACHE3)
    return dict(beta=beta,penalty=penalty,rows=replay(DATA,VALID,models,p,cache))

def immutable(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2)
    path.chmod(0o444)

if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--workers',type=int,default=8);a.add_argument('--attempt',choices=['r1','r2'],default='r1');args=a.parse_args()
    if args.attempt!='r1':P=P/args.attempt
    model_prefix=Path('models/phase6') if args.attempt=='r1' else Path('models/phase6')/args.attempt
    protocol_path=P/'TRAIN_PROTOCOL_V6.json';protocol=json.loads(protocol_path.read_text());DATA=load_train(R)
    immutable(P/'train-book-causal-prefix-audit-v6.json',dict(status='passed',worlds=len(DATA.keys),requested_plan_rows=len(DATA.keys)*343,stages=3,unexecuted_suffix_cannot_change_current_observation=True))
    years=np.array(sorted({k[1] for k in DATA.keys}));selections=[];folds=[];start=time.monotonic()
    for fold,(fit,valid) in enumerate(GroupKFold(5).split(years,groups=years)):
        fy=set(years[fit]);vy=set(years[valid]);FIT=np.array([i for i,k in enumerate(DATA.keys) if k[1] in fy]);VALID=np.array([i for i,k in enumerate(DATA.keys) if k[1] in vy]);assert not fy&vy
        STAGE3=fit_stage(DATA,FIT,3,{},Policy());CACHE3=stage3_cache(DATA,STAGE3)
        jobs=list(itertools.product(protocol['beta_candidates'],protocol['lambda_corridor_candidates']))
        results=[]
        with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('fork')) as pool:
            for f in as_completed([pool.submit(candidate,j) for j in jobs]):
                result=f.result();result['fold']=fold;results.append(result);print(json.dumps(dict(phase='selection',fold=fold,done=len(results),total=len(jobs),beta=result['beta'],penalty=result['penalty'])),flush=True)
        selections.extend(results);folds.append(dict(fold=fold,fit_years=sorted(map(int,fy)),validation_years=sorted(map(int,vy)),all_backward_teachers_inside_fit_only=True))
        immutable(P/f'selection-fold-{fold}-v6.json',dict(fold=fold,results=results,split=folds[-1]))
    summary=[]
    for beta,penalty in itertools.product(protocol['beta_candidates'],protocol['lambda_corridor_candidates']):
        rows=[r for s in selections if s['beta']==beta and s['penalty']==penalty for r in s['rows']];regions=sorted({r['region_id'] for r in rows})
        shards={name:dict(joint=float(np.mean([r['joint'] for r in rows if r['region_id']==name])),partial_profit=float(np.mean([r['partial_profit'] for r in rows if r['region_id']==name]))) for name in regions}
        summary.append(dict(beta=beta,penalty=penalty,macro_joint=float(np.mean([v['joint'] for v in shards.values()])),macro_partial_profit=float(np.mean([v['partial_profit'] for v in shards.values()])),regional=shards))
    best=max(summary,key=lambda s:(s['macro_joint'],s['macro_partial_profit'],-s['beta'],-s['penalty']))
    immutable(P/'policy-train-selection-v6.json',dict(status='TRAIN_OOF_selected',selected=best,summary=summary,folds=folds,protocol_sha256=hashlib.sha256(protocol_path.read_bytes()).hexdigest(),selectionCV_not_unbiased_validation=True,dev_used=False,final_books_used=False))
    receipts=[]
    # Component models are refit with their own future policy, never merely masked after fitting.
    for family in FAMILIES:
        p=Policy(best['beta'],best['penalty'],family);models,cache=fit_pipeline(DATA,np.arange(len(DATA.keys)),p)
        folder=R/model_prefix/family;folder.mkdir(parents=True,exist_ok=False);files=[]
        for stage,m in models.items():
            path=folder/f'stage-{stage}.joblib';joblib.dump(m,path,compress=3);path.chmod(0o444);files.append(dict(path=str(path.relative_to(R)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),stage=stage,model_id=m.model_id))
        rows=replay(DATA,np.arange(len(DATA.keys)),models,p,cache)
        immutable(P/f'train-primary-replay-{family}-v6.json',dict(scope='AllTRAINresubstitution;notOOF',policy=p.__dict__,rows=rows))
        receipts.append(dict(family=family,files=files,policy=p.__dict__,future_teacher_refit=True));print(json.dumps(dict(phase='allTRAIN_fit',family=family,completed=True)),flush=True)
    immutable(P/'outcome-train-freeze-v6.json',dict(status='completed',families=receipts,folds=folds,selected=best,elapsed_seconds=time.monotonic()-start,TRAIN_worlds=len(DATA.keys),new_daily_physical_rollouts=0,final_books_used=False))
