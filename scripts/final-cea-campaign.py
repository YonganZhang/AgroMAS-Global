"""Wait for the single completed audit, then run only read-only posthoc transformations."""
import pathlib,json,time,subprocess,sys,os
R=pathlib.Path(__file__).resolve().parents[1];start=time.monotonic();raw=R/'reports/phase4-heldout-final.json'
while True:
 if raw.exists():
  try:
   x=json.loads(raw.read_text());assert x['status']=='completed';assert sum(len(r['episodes']) for r in x['records'])==38736;break
  except (json.JSONDecodeError,AssertionError):pass
 if time.monotonic()-start>5400:raise TimeoutError('Single frozen audit did not complete; do not rerun policies automatically')
 time.sleep(15)
for args in [['scripts/phase4-summarize.py','--heldout'],['scripts/final-cea-analysis.py'],['scripts/final-cea-verify.py'],['scripts/final-cea-figure.py'],['scripts/final-cea-report.py']]:
 print('START',args,flush=True);subprocess.run([sys.executable,*args],cwd=R,check=True);print('DONE',args,flush=True)
print('POSTHOC COMPLETE',flush=True)
