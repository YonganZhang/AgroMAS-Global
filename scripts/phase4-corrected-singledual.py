import pathlib,subprocess,sys,json,concurrent.futures,time
R=pathlib.Path(__file__).resolve().parents[1]
def train(seed):
 cmd=[sys.executable,str(R/'scripts/phase4-ppo-run-singledual.py'),'--model','corrected','--seed',str(seed),'--tag','phase4-singledual'];start=time.monotonic()
 with (R/f'logs/phase4-corrected-singledual-{seed}.log').open('w') as f:code=subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT).returncode
 return dict(seed=seed,returncode=code,seconds=time.monotonic()-start,command=cmd)
if __name__=='__main__':
 out=R/'reports/phase4-corrected-singledual-processes.json';assert not out.exists()
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(train,[4,17,29]))
 out.write_text(json.dumps(rows,indent=2));assert all(r['returncode']==0 for r in rows)
