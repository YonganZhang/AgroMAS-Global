import pathlib,subprocess,sys,json,time,argparse
R=pathlib.Path(__file__).resolve().parents[1]
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--model',default='full');ap.add_argument('--tag',default='v1');a=ap.parse_args()
    records=[];active=[]
    for seed in [4,17,29]:
        log=open(R/f'logs/phase3-{a.tag}-{a.model}-seed{seed}.log','w')
        cmd=[sys.executable,str(R/'scripts/phase3-run.py'),'--model',a.model,'--seed',str(seed),'--steps','65536','--tag',a.tag]
        p=subprocess.Popen(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT)
        active.append((seed,p,log,time.monotonic(),cmd))
    for seed,p,log,start,cmd in active:
        code=p.wait();log.close();records.append(dict(seed=seed,returncode=code,seconds=time.monotonic()-start,command=cmd))
        (R/f'reports/phase3-{a.tag}-processes.json').write_text(json.dumps(records,indent=2))
    sys.exit(int(any(r['returncode'] for r in records)))
