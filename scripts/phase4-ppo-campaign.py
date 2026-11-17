"""Complete missing four tiers, matched budgets/seeds; no heldout read."""
import pathlib,subprocess,sys,json,concurrent.futures,time
R=pathlib.Path(__file__).resolve().parents[1]
def run(task):
 model,seed=task;cmd=[sys.executable,str(R/'scripts/phase4-ppo-run.py'),'--model',model,'--seed',str(seed),'--tag','phase4'];start=time.monotonic()
 with (R/f'logs/phase4-ppo-{model}-{seed}.log').open('w') as f:code=subprocess.run(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT).returncode
 return dict(model=model,seed=seed,returncode=code,seconds=time.monotonic()-start,command=cmd)
if __name__=='__main__':
 out=R/'reports/phase4-ppo-processes.json';assert not out.exists();rows=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for r in pool.map(run,[(m,s) for m in ['raw','corrected','masked','guided'] for s in [4,17,29]]):rows.append(r);out.write_text(json.dumps(rows,indent=2));print(json.dumps(r),flush=True)
 assert len(rows)==12 and all(r['returncode']==0 for r in rows)
