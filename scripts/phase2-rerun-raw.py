"""Before audit unlock, preserve and replace raw pilot whose DVS path was inadvertently adapted."""
import pathlib,subprocess,sys,json,time,concurrent.futures
R=pathlib.Path(__file__).resolve().parents[1]
for seed in [4,17,29]:
 old=R/'reports/phase2-runs'/f'matched-raw-seed{seed}-env16'
 old.rename(old.with_name(f'preaudit-adapted-dvs-raw-seed{seed}-env16'))
 p=R/'logs'/f'phase2-matched-raw-{seed}.log'
 p.rename(p.with_name(f'phase2-preaudit-adapted-dvs-raw-{seed}.log'))
def run(seed):
 cmd=[sys.executable,str(R/'scripts/phase2-run.py'),'--model','raw','--seed',str(seed),'--steps','32768','--nenvs','16','--tag','matched'];start=time.monotonic()
 with (R/'logs'/f'phase2-matched-raw-{seed}.log').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,cwd=R)
 return dict(model='raw',seed=seed,command=cmd,exit_code=p.returncode,wall_seconds=time.monotonic()-start,reason='Preserve original raw post-transition DVS semantics; pilot retained; no audit had been evaluated')
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:results=list(ex.map(run,[4,17,29]))
(R/'reports/phase2-raw-rerun-processes.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results),flush=True)
if any(x['exit_code'] for x in results):sys.exit(1)
