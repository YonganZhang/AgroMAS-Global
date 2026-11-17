import pathlib,subprocess,sys,json,time,os,concurrent.futures
R=pathlib.Path(__file__).resolve().parents[1]
models=['raw','corrected','shield','recurrent','full'];seeds=[4,17,29]
status={'started_unix':time.time(),'budget':32768,'seeds':seeds,'runs':[]}
def run(item):
    model,seed=item
    folder=R/'reports/phase2-runs'/f'matched-v2-{model}-seed{seed}-env16'
    if model in ('raw','corrected') and (folder/'receipt.json').exists():
        previous=json.loads((R/'reports/phase2-training-processes-v2-before-terminal-guard.json').read_text())['runs']
        row=next(x for x in previous if x['model']==model and x['seed']==seed)
        assert row['exit_code']==0
        row['reused_completed_same_protocol']=True
        return row
    if folder.exists():
        folder.rename(folder.with_name('preterminal-'+folder.name))
        oldlog=R/'logs'/f'phase2-matched-v2-{model}-{seed}.log'
        if oldlog.exists():oldlog.rename(oldlog.with_name('preterminal-'+oldlog.name))
    cmd=[sys.executable,str(R/'scripts/phase2-run.py'),'--model',model,'--seed',str(seed),'--steps','32768','--nenvs','16','--tag','matched-v2']
    log=R/'logs'/f'phase2-matched-v2-{model}-{seed}.log'
    start=time.monotonic()
    with log.open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,cwd=R)
    row=dict(model=model,seed=seed,command=cmd,exit_code=p.returncode,wall_seconds=time.monotonic()-start,log=str(log))
    return row
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
    # Interleave seeds within a model; no audit evaluation is run until all models freeze.
    for row in ex.map(run,[(m,s) for m in models for s in seeds]):
        status['runs'].append(row)
        (R/'reports/phase2-training-processes-v2.json').write_text(json.dumps(status,indent=2))
        print(json.dumps(row),flush=True)
status['completed_unix']=time.time();status['status']='completed' if all(x['exit_code']==0 for x in status['runs']) else 'failed'
(R/'reports/phase2-training-processes-v2.json').write_text(json.dumps(status,indent=2))
if status['status']!='completed':sys.exit(1)
