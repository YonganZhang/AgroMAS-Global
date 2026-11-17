"""TRAIN-only N0/topdress0 and100cm rooting sensitivity; never select parameters."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import json,multiprocessing,logging
from pcse_gym.agromas.regions import load_split_manifest
from pcse_gym.agromas.season import run_fixed_plan,regional_weather,_template
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5'
def run(job):
    name,year,selection,kind=job
    try:return dict(status='completed',diagnostic=kind,**run_fixed_plan(str(R),name,year,
         [0,0,0] if kind=='zero_topdress' else [60,80,80],version='v2',
         root_depth_cm=100. if kind=='root100' else 125.,**selection))
    except Exception as e:return dict(status='failed',region_id=name,harvest_year=year,diagnostic=kind,error=repr(e))
if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    f=json.loads((P/'regional-phenology-train-freeze-v2.json').read_text())
    m=load_split_manifest(P/'global-date-split-manifest.json')
    for n in f['selected']:regional_weather(str(R),n,'v2')
    _template(str(R))
    jobs=[(n,y,s,k) for n,s in f['selected'].items() for y in m['regions'][n]['roles']['Train'] for k in ['zero_topdress','root100']]
    path=P/'regional-train-diagnostics-v2.jsonl'
    with path.open('x') as log:
        with ProcessPoolExecutor(max_workers=8,mp_context=multiprocessing.get_context('fork')) as pool:
            for future in as_completed([pool.submit(run,j) for j in jobs]):
                log.write(json.dumps(future.result())+'\n');log.flush()
    path.chmod(0o444)
