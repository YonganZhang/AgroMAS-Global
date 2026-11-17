"""TRAIN-only full Cartesian intervention book; online controllers never read it."""
from pathlib import Path
from itertools import product
from concurrent.futures import ProcessPoolExecutor,as_completed
import hashlib,json,logging,multiprocessing
from pcse_gym.agromas.regions import REGIONS,load_split_manifest
from pcse_gym.agromas.season import run_fixed_plan,regional_weather,_template
from pcse_gym.agromas.features import shared_features,forecast_model
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5';O=R/'data/phase5-teachers-v2'
GRID=(0,10,20,40,60,80,100)
def run(job):
    name,year,climate,selection=job
    path=O/f'{name}-{year}-{climate}.jsonl'
    rows=0;failed=0;feature_cache={}
    with path.open('x') as f:
        for plan in product(GRID,repeat=3):
            try:
                row=run_fixed_plan(str(R),name,year,plan,version='v2',climate=climate,record_states=True,**selection)
                features={}
                for stage,state in row['states'].items():
                    key=tuple((k,str(v)) for k,v in state.items())
                    if key not in feature_cache:feature_cache[key]=shared_features(str(R),state,climate).tolist()
                    features[stage]=feature_cache[key]
                row=dict(status='completed',plan=list(plan),features=features,**row)
            except Exception as e:
                row=dict(status='failed',region_id=name,harvest_year=year,climate=climate,plan=list(plan),error=repr(e));failed+=1
            f.write(json.dumps(row,default=str)+'\n');f.flush();rows+=1
    path.chmod(0o444)
    return dict(path=str(path.relative_to(R)),rows=rows,failed=failed,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    freeze=json.loads((P/'regional-phenology-train-freeze-v2.json').read_text())
    m=load_split_manifest(P/'global-date-split-manifest.json')
    protocol=dict(status='registered_before_teacher_simulations',years=list(range(1995,2010)),dose_grid=list(GRID),
        climates=['Historical','idealized_mid','idealized_high'],stage_order=[3,2,1],
        forecast_training='First10TRAIN season envelopes, coefficients/residuals frozen before all teacher issue dates',
        labels='Physical full-seasonY_DM,grainN,totalfert,nonfert; retain action-guard skips and clipping, no optimizer future truth online',
        continuation='Backward fixed reference-context policy: cap40,subsidy0,grain0.20EUR/kg,N1.5EUR/kg,beta200EUR/ha,eta0; outer year-grouped5fold teacher pipelines',
        projection='At inference, known committed fertilizer gives a nonnegative lower bound; future fertilizer clipped to budget; nonfert fixed to known seed/deposition control; raw prediction calibration retained',
        economics='Explicit experimental EUR prices, not observed regional farmer receipts; no field-income claim',
        split_sha256=hashlib.sha256((P/'global-date-split-manifest.json').read_bytes()).hexdigest())
    with (P/'outcome-teacher-protocol-v2.json').open('x') as f:json.dump(protocol,f,indent=2)
    (P/'outcome-teacher-protocol-v2.json').chmod(0o444)
    O.mkdir(parents=True,exist_ok=False)
    jobs=[]
    for name in REGIONS:
        regional_weather(str(R),name,'v2');forecast_model(str(R),name)
        for year in protocol['years']:
            assert year in m['regions'][name]['roles']['Train']
            for climate in protocol['climates']:jobs.append((name,year,climate,freeze['selected'][name]))
    _template(str(R))
    receipts=[]
    with (P/'teacher-generation-progress-v2.jsonl').open('x') as log:
        with ProcessPoolExecutor(max_workers=8,mp_context=multiprocessing.get_context('fork')) as pool:
            for future in as_completed([pool.submit(run,j) for j in jobs]):
                r=future.result();receipts.append(r);log.write(json.dumps(r)+'\n');log.flush();print(json.dumps(r),flush=True)
    with (P/'teacher-book-receipt-v2.json').open('x') as f:json.dump(dict(files=receipts,total_rows=sum(r['rows'] for r in receipts),failed=sum(r['failed'] for r in receipts),heldout_used=False,dev_used=False),f,indent=2)
