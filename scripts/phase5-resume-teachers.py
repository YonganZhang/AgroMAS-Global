"""Scheduling-only resume of frozen343-plan TRAIN books, preserving all evidence."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import argparse,hashlib,importlib.util,json,logging,multiprocessing,sys,time
from pcse_gym.agromas.regions import REGIONS,load_split_manifest
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5';O=R/'data/phase5-teachers-v2'
spec=importlib.util.spec_from_file_location('phase5_teacher_generator',R/'scripts/phase5-generate-teachers.py')
generator=importlib.util.module_from_spec(spec);sys.modules[spec.name]=generator;spec.loader.exec_module(generator)


def verify(path,name,year,climate):
    if path.stat().st_mode&0o222:raise ValueError('Writable incomplete book must be archived before resume')
    data=path.read_bytes();rows=[json.loads(x) for x in data.splitlines()]
    if len(rows)!=343 or len({tuple(x['plan']) for x in rows})!=343:raise ValueError('Incomplete intervention grid')
    if any(x['status']!='completed' or x['role']!='Train' or x['region_id']!=name or x['harvest_year']!=year or x['climate']!=climate for x in rows):
        raise ValueError('Teacher identity/role/failure gate')
    return dict(path=str(path.relative_to(R)),rows=343,failed=0,sha256=hashlib.sha256(data).hexdigest())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--workers',type=int,choices=[32,48],default=32)
    args=parser.parse_args();logging.disable(logging.CRITICAL)
    transition=json.loads((P/'teacher-resume32-transition-v2.json').read_text())
    if transition['simulation_failures']:raise RuntimeError('Prior failures require explicit investigation')
    snapshot=json.loads((P/'teacher-generation-source-snapshot-v2.json').read_text())
    for rel,digest in snapshot['files'].items():
        if hashlib.sha256((R/rel).read_bytes()).hexdigest()!=digest:raise ValueError('Frozen functional source changed:'+rel)
    freeze=json.loads((P/'regional-phenology-train-freeze-v2.json').read_text())
    protocol=json.loads((P/'outcome-teacher-protocol-v2.json').read_text())
    manifest=load_split_manifest(P/'global-date-split-manifest.json')
    receipts=[];pending=[];jobs_by_path={}
    for name in REGIONS:
        generator.regional_weather(str(R),name,'v2');generator.forecast_model(str(R),name)
        for year in protocol['years']:
            assert year in manifest['regions'][name]['roles']['Train']
            for climate in protocol['climates']:
                path=O/f'{name}-{year}-{climate}.jsonl'
                job=(name,year,climate,freeze['selected'][name]);jobs_by_path[str(path.relative_to(R))]=job
                if path.exists():receipts.append(verify(path,name,year,climate))
                else:pending.append(job)
    prior={r['path']:r for r in transition['preserved_complete_files']}
    assert all(r['sha256']==prior[r['path']]['sha256'] for r in receipts)
    generator._template(str(R));start=time.monotonic()
    print(json.dumps(dict(skipped_verified=len(receipts),pending=len(pending),workers=args.workers)),flush=True)
    progress=P/'teacher-generation-resume32-progress-v2.jsonl'
    with progress.open('x') as log:
        with ProcessPoolExecutor(max_workers=args.workers,mp_context=multiprocessing.get_context('fork')) as pool:
            for future in as_completed([pool.submit(generator.run,j) for j in pending]):
                record=future.result();job=jobs_by_path[record['path']]
                checked=verify(R/record['path'],*job[:3]);assert checked==record
                receipts.append(checked);log.write(json.dumps(checked)+'\n');log.flush()
                print(json.dumps(dict(complete_files=len(receipts),total=225,elapsed_seconds=time.monotonic()-start)),flush=True)
    assert len(receipts)==225
    for rel,digest in snapshot['files'].items():
        assert hashlib.sha256((R/rel).read_bytes()).hexdigest()==digest,'Source changed during resume'
    result=dict(files=sorted(receipts,key=lambda r:r['path']),total_rows=sum(x['rows'] for x in receipts),failed=0,
      dev_used=False,heldout_used=False,resume_workers=args.workers,resume_elapsed_seconds=time.monotonic()-start,
      preserved_complete_files=len(prior),interrupted_additional_completed_rows=transition['interrupted_complete_row_count'],
      interrupted_physical_work_note='Additionalpartialpassrows preserved; unfinished currentseason simulations are not counted as completed episodes',
      scientific_protocol_sha256=hashlib.sha256((P/'outcome-teacher-protocol-v2.json').read_bytes()).hexdigest(),
      functional_source_snapshot_sha256=hashlib.sha256((P/'teacher-generation-source-snapshot-v2.json').read_bytes()).hexdigest())
    out=P/'teacher-book-receipt-v2.json'
    with out.open('x') as f:json.dump(result,f,indent=2)
    out.chmod(0o444);progress.chmod(0o444)
    print(json.dumps(dict(status='completed',files=225,unique_physical_seasons=result['total_rows'],failed=0)),flush=True)
