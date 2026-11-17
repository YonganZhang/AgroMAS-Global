import pathlib,time,json,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[1];deadline=time.monotonic()+5400
while time.monotonic()<deadline:
 p=R/'reports/phase2-training-processes-v2.json'
 if p.exists():
  try:s=json.loads(p.read_text())
  except json.JSONDecodeError:s={}
  if s.get('status')=='failed':raise RuntimeError('Training failed; audit remains locked')
  if s.get('status')=='completed':break
 time.sleep(5)
else:raise TimeoutError('Training deadline; do not unlock audit')
subprocess.run([sys.executable,str(R/'scripts/phase2-evaluate.py')],check=True,cwd=R)
print('All evaluation tasks completed',flush=True)
