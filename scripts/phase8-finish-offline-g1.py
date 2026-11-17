"""Wait boundedly for once-only physics, then run independent offline audits only."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import json,subprocess,sys,time
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8'
if __name__=='__main__':
 deadline=time.monotonic()+3600
 while not (P/'phase8b-physical-receipt.json').exists():
  if time.monotonic()>deadline:raise TimeoutError('Physical completion timeout; no Dev scoring')
  time.sleep(5)
 receipt=json.loads((P/'phase8b-physical-receipt.json').read_text());assert receipt['status']=='completed' and len(receipt['files'])==250
 def run(name):
  with (P/(name+'.log')).open('x') as f:rc=subprocess.run([sys.executable,str(R/'scripts'/(name+'.py'))],cwd=R,stdout=f,stderr=subprocess.STDOUT).returncode
  if rc:raise RuntimeError(name+' failed: '+str(rc))
 with ThreadPoolExecutor(max_workers=2) as pool:
  futures=[pool.submit(run,name) for name in ['phase8-audit-native-endpoints','phase8-audit-physical-decoding']]
  for f in futures:f.result()
 while not (P/'phase8b-daily-ledger-audit.json').exists():
  if time.monotonic()>deadline:raise TimeoutError('Daily ledger audit completion timeout; no Dev scoring')
  time.sleep(5)
 daily=json.loads((P/'phase8b-daily-ledger-audit.json').read_text());native=json.loads((P/'phase8b-native-endpoint-audit.json').read_text());assert daily['status']=='passed' and native['status']=='passed'
 assert not (P/'phase8b-dev-access-claim.json').exists()
 (P/'phase8b-offline-readiness.json').write_text(json.dumps({'status':'ready_for_frozen_G1_Dev_scoring','physical_books':250,'TRAIN_books':225,'Dev_books':25,'physical_calls':receipt['physics_calls'],'daily_audit':daily['status'],'native_endpoint_audit':native['status'],'TRAIN_decoding_complete':(P/'phase8b-TRAIN-physical-decoding.json').exists(),'Dev_scoring_started':False,'G2_G3_started':False},indent=2));print('Offline checks complete; Dev scoring remains unstarted',flush=True)
