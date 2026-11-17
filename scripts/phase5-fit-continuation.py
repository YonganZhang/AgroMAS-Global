"""Outer-year-isolated backward continuation fitting; no Dev/Held-Out data."""
from pathlib import Path
import hashlib,json,logging
import numpy as np
import joblib
from sklearn.model_selection import GroupKFold
from pcse_gym.agromas.continuation import dataset,fit_pipeline,FrozenStageOutcome,choose,predict_physical
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5'
if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    receipt=P/'teacher-book-receipt-v2.json'
    registry=json.loads(receipt.read_text())
    if registry['failed']:raise RuntimeError('Physical teacher failures must be resolved/retained before fitting')
    books={}
    for entry in registry['files']:
        p=R/entry['path']
        if hashlib.sha256(p.read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('Teacher book drift')
        records=[json.loads(line) for line in p.read_text().splitlines()]
        first=records[0];key=(first['region_id'],first['harvest_year'],first['climate'])
        assert first['role']=='Train' and 1995<=key[1]<=2009
        books[key]={tuple(r['plan']):r for r in records}
        assert len(books[key])==343
    years=np.array(sorted({k[1] for k in books}));residual={s:[] for s in (1,2,3)};folds=[]
    calibration={s:[] for s in (1,2,3)}
    policy_protocol=json.loads((P/'policy-selection-protocol-v2.json').read_text())
    policy_rows=[]
    for fold,(fit,valid) in enumerate(GroupKFold(n_splits=5).split(years,groups=years)):
        fit_years=set(years[fit].tolist());valid_years=set(years[valid].tolist())
        assert not fit_years&valid_years
        fitbook={k:v for k,v in books.items() if k[1] in fit_years}
        validbook={k:v for k,v in books.items() if k[1] in valid_years}
        models=fit_pipeline(fitbook)
        for stage in (1,2,3):
            x,y,groups,keys=dataset(validbook,stage,models)
            pred=predict_physical(models[stage],x)
            residual[stage].append(y-pred)
            calibration[stage].append(dict(fold=fold,n=len(x),physical_target_RMSE=np.sqrt(np.mean((y-pred)**2,axis=0)).tolist(),
                zero_fertilizer_underprediction_fraction=float(np.mean(pred[:,2]<x[:,3]+x[:,-1]))))
        for key,book in validbook.items():
            for beta in policy_protocol['beta_candidates_EUR_ha']:
                plan=[0.,0.,0.];row=book[tuple(plan)]
                for stage in (1,2,3):
                    plan[stage-1]=choose(models[stage],row,stage,beta=beta)
                    row=book[tuple(plan)]
                m=np.asarray(row['outcome']);joint=bool(.5<=m[3]<=.9 and m[2]<=40)
                policy_rows.append(dict(fold=fold,region_id=key[0],year=key[1],climate=key[2],beta=beta,
                    joint=joint,partial_profit=float(200*m[0]-1.5*m[4]),plan=plan))
        folds.append(dict(fold=fold,fit_years=sorted(fit_years),validation_years=sorted(valid_years),
            continuation_teachers_refit_only_on_outer_fit_years=True))
        print(json.dumps(folds[-1]),flush=True)
    policy_summary=[]
    for beta in policy_protocol['beta_candidates_EUR_ha']:
        v=[r for r in policy_rows if r['beta']==beta]
        policy_summary.append(dict(beta=beta,mean_joint=float(np.mean([r['joint'] for r in v])),
              mean_partial_profit=float(np.mean([r['partial_profit'] for r in v]))))
    selected_beta=max(policy_summary,key=lambda r:(r['mean_joint'],r['mean_partial_profit'],-r['beta']))['beta']
    selection=dict(selected_beta=selected_beta,eta=0.,summary=policy_summary,OOF_replay=policy_rows,
        protocol_sha256=hashlib.sha256((P/'policy-selection-protocol-v2.json').read_bytes()).hexdigest(),dev_used=False,heldout_used=False)
    policy_path=P/'policy-train-freeze-v2.json'
    with policy_path.open('x') as f:json.dump(selection,f,indent=2)
    policy_path.chmod(0o444)
    models=fit_pipeline(books)
    out=R/'models/phase5/continuation-v2';out.mkdir(parents=True,exist_ok=False)
    records=[]
    for stage in (1,2,3):
        errors=np.concatenate(residual[stage])
        model_id=hashlib.sha256(receipt.read_bytes()+errors.tobytes()+str(stage).encode()).hexdigest()
        model=FrozenStageOutcome(models[stage],errors,model_id)
        path=out/f'stage-{stage}.joblib';joblib.dump(model,path,compress=3);path.chmod(0o444)
        records.append(dict(stage=stage,model_id=model_id,path=str(path.relative_to(R)),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),outer_pipeline_residual_rows=len(errors),
                calibration=calibration[stage]))
    result=dict(status='Train_only_frozen',models=records,folds=folds,dev_used=False,heldout_used=False,
        residual_scope='Full backward pipeline outer-year residuals; final allTRAIN teacher differs from outer teachers, no conditional coverage guarantee',
        teacher_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),
        reference_continuation='Frozen cap40,subsidy0,grain0.20,N1.5,beta200,eta0 reference, not reoptimized for allscenariofuturepolicies')
    path=P/'outcome-train-freeze-v2.json'
    with path.open('x') as f:json.dump(result,f,indent=2)
    path.chmod(0o444)
