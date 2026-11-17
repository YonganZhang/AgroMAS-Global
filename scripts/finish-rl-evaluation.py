import pathlib,time,json,sys,subprocess
R=pathlib.Path(__file__).resolve().parents[1];receipt=R/'reports/rl-training-receipt.json';deadline=time.monotonic()+900
while not receipt.exists():
 if time.monotonic()>deadline:raise TimeoutError('Training receipt not ready within bounded 15-minute wait')
 time.sleep(2)
j=json.loads(receipt.read_text())
if j['status']!='completed':raise RuntimeError(j)
d=pathlib.Path(j['checkpoint_dir']);subprocess.run([sys.executable,str(R/'scripts/evaluate-rl.py'),str(d/'latest-model.zip'),str(d/'latest-env.pkl'),str(R/'reports/rl-final-evaluation.json')],cwd=R,check=True)
