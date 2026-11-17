"""Refit functional ablations and their continuation teachers entirely insideTRAINfolds."""
from pathlib import Path
import json,hashlib,logging,copy
import numpy as np
import joblib
from sklearn.model_selection import GroupKFold
from pcse_gym.agromas.continuation import dataset,fit_pipeline,FrozenStageOutcome,predict_physical,choose,GRID
from pcse_gym.agromas.oracle import oracle_vector
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5'


def load_books():
    reg=json.loads((P/'teacher-book-receipt-v2.json').read_text());assert reg['failed']==0
    books={}
    for record in reg['files']:
        path=R/record['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256']
        rows=[json.loads(line) for line in path.read_text().splitlines()]
        row=rows[0];key=(row['region_id'],row['harvest_year'],row['climate'])
        assert row['role']=='Train' and 1995<=key[1]<=2009
        books[key]={tuple(r['plan']):r for r in rows}
    return books


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--family',required=True)
    args=parser.parse_args();logging.disable(logging.CRITICAL)
    protocol_path=P/'ablation-training-protocol-v2.json';protocol=json.loads(protocol_path.read_text())
    if args.family=='A2-oracle':config=dict(objective='yield',ecological=False,mask=[])
    elif args.family in protocol['families']:config=protocol['families'][args.family]
    else:parser.error('Unregistered family')
    books=load_books()
    if args.family=='A2-oracle':
        cache={}
        for (name,year,climate),book in books.items():
            for row in book.values():
                for stage,features in row['features'].items():
                    day=row['states'][stage]['as_of'];key=(name,year,climate,day)
                    if key not in cache:cache[key]=oracle_vector(str(R),name,day,climate,role='Train',harvest_year=year).tolist()
                    features[6:10]=cache[key]
    years=np.array(sorted({k[1] for k in books}));errors={s:[] for s in (1,2,3)};folds=[];metrics=[]
    for i,(fit,valid) in enumerate(GroupKFold(n_splits=5).split(years,groups=years)):
        fy=set(years[fit].tolist());vy=set(years[valid].tolist());assert not fy&vy
        train={k:v for k,v in books.items() if k[1] in fy};validation={k:v for k,v in books.items() if k[1] in vy}
        models=fit_pipeline(train,**config)
        for stage in (1,2,3):
            x,y,_,_=dataset(validation,stage,models,**config)
            pred=predict_physical(models[stage],x);errors[stage].append(y-pred)
            metrics.append(dict(fold=i,stage=stage,n=len(x),RMSE=np.sqrt(np.mean((y-pred)**2,0)).tolist()))
        folds.append(dict(fold=i,fit_years=sorted(fy),validation_years=sorted(vy),teachers_refit_inside_outerfit=True))
        print(json.dumps(dict(family=args.family,fold=i,completed=True)),flush=True)
    models=fit_pipeline(books,**config)
    out=R/f'models/phase5/continuation-{args.family}-v2';out.mkdir(parents=True,exist_ok=False)
    receipts=[]
    for stage in (1,2,3):
        residual=np.concatenate(errors[stage]);model_id=hashlib.sha256(residual.tobytes()+args.family.encode()+str(stage).encode()+protocol_path.read_bytes()).hexdigest()
        model=FrozenStageOutcome(models[stage],residual,model_id)
        path=out/f'stage-{stage}.joblib';joblib.dump(model,path,compress=3);path.chmod(0o444)
        receipts.append(dict(stage=stage,path=str(path.relative_to(R)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),model_id=model_id))
    result=dict(family=args.family,config=config,folds=folds,metrics=metrics,models=receipts,dev_used=False,heldout_used=False,
        scope=protocol['interpretation'],protocol_sha256=hashlib.sha256(protocol_path.read_bytes()).hexdigest())
    if args.family=='A1':
        basal=json.loads((P/'regional-controls-v2.json').read_text())['regional_basal_n_kg_ha'];fixed={}
        for name in sorted({k[0] for k in books}):
            group={k:b for k,b in books.items() if k[0]==name and k[2]=='Historical'};candidates=[]
            for a in GRID:
                for b in GRID:
                    if a+b>220-basal.get(name,0):continue
                    vals=[];fert=[]
                    for key,book in group.items():
                        plan=[a,b,0.];row=book[tuple(plan)]
                        plan[2]=choose(models[3],row,3,objective='yield',ecological=False);row=book[tuple(plan)]
                        vals.append(row['outcome'][0]);fert.append(row['outcome'][4])
                    candidates.append((float(np.mean(vals)),-float(np.mean(fert)),-a,-b,a,b))
            best=max(candidates);fixed[name]=[best[-2],best[-1]]
        fixed_path=P/'A0-fixed-first-two-train-freeze-v2.json'
        with fixed_path.open('x') as f:json.dump(dict(selected=fixed,scope=protocol['A0'],dev_used=False,heldout_used=False),f,indent=2)
        fixed_path.chmod(0o444)
    receipt=P/f'outcome-{args.family}-train-freeze-v2.json'
    with receipt.open('x') as f:json.dump(result,f,indent=2)
    receipt.chmod(0o444)
