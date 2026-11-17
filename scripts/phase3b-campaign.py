import pathlib,subprocess,sys,json,time,argparse
R=pathlib.Path(__file__).resolve().parents[1]
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--model',default='full3');p.add_argument('--tag',default='v3');p.add_argument('--steps',type=int,default=65536);a=p.parse_args();active=[];rows=[]
 receipt=R/f'reports/phase3b-{a.tag}-{a.model}-processes.json';assert not receipt.exists()
 for seed in [4,17,29]:
  log=open(R/f'logs/phase3b-{a.tag}-{a.model}-seed{seed}.log','w');cmd=[sys.executable,str(R/'scripts/phase3b-run.py'),'--model',a.model,'--seed',str(seed),'--tag',a.tag,'--steps',str(a.steps)]
  active.append((seed,subprocess.Popen(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT),log,time.monotonic(),cmd))
 for seed,proc,log,start,cmd in active:
  code=proc.wait();log.close();rows.append(dict(seed=seed,returncode=code,seconds=time.monotonic()-start,command=cmd));receipt.write_text(json.dumps(rows,indent=2))
 sys.exit(int(any(x['returncode'] for x in rows)))
