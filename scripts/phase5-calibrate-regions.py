"""TRAIN-only engineering phenology selection, then exactly one frozen Dev check."""
from pathlib import Path
import json,multiprocessing,hashlib
from concurrent.futures import ProcessPoolExecutor,as_completed
from datetime import date
import numpy as np
from pcse_gym.agromas.regions import REGIONS,load_split_manifest
from pcse_gym.agromas.season import run_fixed_plan,regional_weather,_template
R=Path(__file__).resolve().parents[1]

def run(job):
    name,year,scale,role=job
    try:return dict(status='completed',**run_fixed_plan(str(R),name,year,[60,80,80],role=role,thermal_scale=scale))
    except Exception as e:return dict(status='failed',region_id=name,harvest_year=year,thermal_scale=scale,role=role,error=repr(e))

def execute(jobs,out):
    rows=[]
    with out.open('x') as log:
        with ProcessPoolExecutor(max_workers=12,mp_context=multiprocessing.get_context('fork')) as pool:
            for future in as_completed([pool.submit(run,j) for j in jobs]):
                row=future.result();rows.append(row);log.write(json.dumps(row)+'\n');log.flush()
    return rows

if __name__=='__main__':
    import logging;logging.disable(logging.CRITICAL)
    protocol=json.loads((R/'reports/phase5/phenology-calibration-protocol-v1.json').read_text())
    manifest=load_split_manifest(R/'reports/phase5/global-date-split-manifest.json')
    for name in REGIONS:regional_weather(str(R),name)
    _template(str(R))
    jobs=[(name,year,scale,'Train') for name in REGIONS for year in manifest['regions'][name]['roles']['Train'] for scale in protocol['candidates']]
    rows=execute(jobs,R/'reports/phase5/regional-train-phenology-v1.jsonl')
    selected={};summary={}
    for name in REGIONS:
        candidates=[]
        for scale in protocol['candidates']:
            records=[r for r in rows if r['region_id']==name and r['thermal_scale']==scale]
            valid=[r for r in records if r['status']=='completed' and np.isfinite(r['outcome']).all() and r['outcome'][0]>=0]
            mature=[r for r in valid if r['dvs_end']>=1.99 and r['maturity'] not in ('None','null')]
            offsets=[]
            for r in mature:
                month,day=protocol['target_maturity_month_day'][name]
                offsets.append((date.fromisoformat(r['maturity'])-date(r['harvest_year'],month,day)).days)
            eligible=len(valid)==len(records) and len(mature)/len(records)>=.9
            candidates.append(dict(thermal_scale=scale,total=len(records),completed=len(valid),mature=len(mature),
                eligible=eligible,median_maturity_offset_days=float(np.median(offsets)) if offsets else None,
                mean_yield_dm_t_ha=float(np.mean([r['outcome'][0] for r in valid])) if valid else None,
                third_positive_fraction=float(np.mean([any(e['stage']==3 and e['dose']>0 for e in r['events']) for r in valid])) if valid else None))
        eligible=[x for x in candidates if x['eligible']]
        if not eligible:
            summary[name]=dict(status='no_valid_preregistered_candidate',candidates=candidates);continue
        best=min(eligible,key=lambda x:abs(x['median_maturity_offset_days']))
        selected[name]=best['thermal_scale'];summary[name]=dict(status='TRAIN_selected',selected=best,candidates=candidates)
    freeze=dict(selected=selected,summary=summary,protocol_sha256=hashlib.sha256((R/'reports/phase5/phenology-calibration-protocol-v1.json').read_bytes()).hexdigest(),
                split_sha256=hashlib.sha256((R/'reports/phase5/global-date-split-manifest.json').read_bytes()).hexdigest(),scope='Engineering phenology calibration; not field-yield validation',dev_seen=False)
    out=R/'reports/phase5/regional-phenology-train-freeze-v1.json'
    with out.open('x') as f:json.dump(freeze,f,indent=2)
    out.chmod(0o444)
    print(json.dumps(summary),flush=True)
    # Do not unlock Dev if even one region has no valid TRAIN family.
    if len(selected)!=len(REGIONS):raise RuntimeError('TRAIN engineering gate failed; Dev remains unopened')
    devjobs=[(name,year,selected[name],'Dev') for name in REGIONS for year in manifest['regions'][name]['roles']['Dev']]
    dev=execute(devjobs,R/'reports/phase5/regional-dev-frozen-check-v1.jsonl')
    print(json.dumps(dict(dev_seasons=len(dev),dev_failed=sum(r['status']!='completed' for r in dev),heldout_unlocked=False)))
