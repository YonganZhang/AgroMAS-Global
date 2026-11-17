"""Frozen registered v2 candidates: TRAIN selection, separately invoked Dev check#2.

Never runs Held-Out. Outputs use exclusive creation; completed evidence is immutable.
"""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import date
import argparse,hashlib,json,logging,multiprocessing
import numpy as np
from pcse_gym.agromas.regions import REGIONS,load_split_manifest
from pcse_gym.agromas.season import run_fixed_plan,regional_weather,_template
R=Path(__file__).resolve().parents[1]
P=R/'reports/phase5'


def run(job):
    name,year,cultivar,scale,role=job
    try:
        return dict(status='completed',**run_fixed_plan(str(R),name,year,[60,80,80],
                     role=role,thermal_scale=scale,cultivar=cultivar,version='v2'))
    except Exception as e:
        return dict(status='failed',region_id=name,harvest_year=year,cultivar=cultivar,
                    thermal_scale=scale,role=role,error=repr(e))


def execute(jobs,path,workers):
    rows=[]
    with path.open('x') as f:
        with ProcessPoolExecutor(max_workers=workers,mp_context=multiprocessing.get_context('fork')) as pool:
            for future in as_completed([pool.submit(run,j) for j in jobs]):
                row=future.result();rows.append(row);f.write(json.dumps(row)+'\n');f.flush()
    path.chmod(0o444)
    return rows


def write(path,data):
    with path.open('x') as f:json.dump(data,f,indent=2)
    path.chmod(0o444)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=['train','dev'],required=True)
    parser.add_argument('--workers',type=int,default=8)
    args=parser.parse_args()
    if not 1<=args.workers<=12:parser.error('workers must be1..12')
    logging.disable(logging.CRITICAL)
    protocol=json.loads((P/'phenology-calibration-protocol-v2.json').read_text())
    manifest=load_split_manifest(P/'global-date-split-manifest.json')
    sources=[P/'phenology-calibration-protocol-v2.json',P/'regional-controls-v2.json',P/'global-date-split-manifest.json',
             Path(__file__),R/'NUE_PCSE-Gym/pcse_gym/agromas/season.py',
             R/'NUE_PCSE-Gym/pcse_gym/agromas/initialization.py',R/'NUE_PCSE-Gym/pcse_gym/agromas/scheduler.py',
             R/'NUE_PCSE-Gym/pcse_gym/agromas/weather.py',R/'NUE_PCSE-Gym/pcse_gym/agromas/weekly.py',
             R/'NUE_PCSE-Gym/pcse_gym/envs/configs/crop/winterwheat.yaml',
             R/'NUE_PCSE-Gym/pcse_gym/envs/configs/soil/arminda_soil.yaml',
             R/'NUE_PCSE-Gym/pcse_gym/envs/configs/site/arminda_site.yaml']
    hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    for name in REGIONS:regional_weather(str(R),name,'v2')
    _template(str(R))
    freeze_path=P/'regional-phenology-train-freeze-v2.json'
    if args.stage=='train':
        write(P/'regional-calibration-source-snapshot-v2.json',hashes)
        jobs=[(name,year,cultivar,scale,'Train') for name in REGIONS
              for year in manifest['regions'][name]['roles']['Train']
              for cultivar in protocol['cultivar_candidates'] for scale in protocol['candidates']]
        rows=execute(jobs,P/'regional-train-phenology-v2.jsonl',args.workers)
        selected={};summary={}
        for name in REGIONS:
            candidates=[]
            for cultivar in protocol['cultivar_candidates']:
                for scale in protocol['candidates']:
                    records=[r for r in rows if (r['region_id'],r['cultivar'],r['thermal_scale'])==(name,cultivar,scale)]
                    valid=[r for r in records if r['status']=='completed' and np.isfinite(r['outcome']).all() and r['outcome'][0]>=0]
                    mature=[r for r in valid if r['dvs_end']>=1.99 and r['maturity'] not in ('None','null')]
                    month,day=protocol['target_maturity_month_day'][name]
                    offsets=[(date.fromisoformat(r['maturity'])-date(r['harvest_year'],month,day)).days for r in mature]
                    candidates.append(dict(cultivar=cultivar,thermal_scale=scale,total=len(records),completed=len(valid),mature=len(mature),
                        eligible=len(valid)==len(records) and len(mature)>=.9*len(records),
                        median_maturity_offset_days=float(np.median(offsets)) if offsets else None,
                        mean_yield_dm_t_ha=float(np.mean([r['outcome'][0] for r in valid])) if valid else None))
            eligible=[r for r in candidates if r['eligible']]
            best=min(eligible,key=lambda x:abs(x['median_maturity_offset_days'])) if eligible else None
            if best:selected[name]=dict(cultivar=best['cultivar'],thermal_scale=best['thermal_scale'])
            summary[name]=dict(selected=best,candidates=candidates)
        assert hashes=={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'Source changed during campaign'
        write(freeze_path,dict(selected=selected,summary=summary,source_hashes=hashes,dev_seen=False,heldout_unlocked=False,
                              selection='Frozen TRAIN maturity-date rule; no yield/profit optimization'))
        print(json.dumps(dict(stage='Train',seasons=len(rows),failed=sum(r['status']!='completed' for r in rows),selected=selected)),flush=True)
        if len(selected)!=5:raise RuntimeError('Engineering gate failed; do not open Dev')
    else:
        freeze=json.loads(freeze_path.read_text())
        assert freeze['source_hashes']==hashes,'Source differs from TRAIN freeze'
        assert len(freeze['selected'])==5,'Incomplete TRAIN selection'
        jobs=[(name,year,freeze['selected'][name]['cultivar'],freeze['selected'][name]['thermal_scale'],'Dev')
              for name in REGIONS for year in manifest['regions'][name]['roles']['Dev']]
        rows=execute(jobs,P/'regional-dev-frozen-check-v2.jsonl',args.workers)
        write(P/'regional-dev-check-v2-receipt.json',dict(cumulative_dev_check_number=2,seasons=len(rows),
            failed=sum(r['status']!='completed' for r in rows),reselection=False,heldout_unlocked=False,source_hashes=hashes))
        print(json.dumps(dict(stage='Dev',cumulative_check=2,seasons=len(rows))),flush=True)
