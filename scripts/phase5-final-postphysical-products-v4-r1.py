"""Supervised immutable Stage5D chain; no retry, overwrite, fitting or selection."""
from pathlib import Path
import subprocess,sys,time,json
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5'
if __name__=='__main__':
 deadline=time.monotonic()+14400;receipt=P/'final-physical-book-receipt-v4.json'
 while not receipt.exists():
  if time.monotonic()>deadline:raise TimeoutError('Finalphysicalreceiptnotready')
  time.sleep(30)
 physical=json.loads(receipt.read_text());assert physical['status']=='completed' and physical['failures']==0 and len(physical['files'])==177
 assert not (R/'cache/phase5-cache-recovery-v4-r1/native-score.pkl').exists(),'Orphanscorecachemustnotbeoverwritten'
 print('Physicalcampaigncomplete;runningunchangedfrozenpolicyscoring.',flush=True)
 with (P/'final-policy-campaign-v4-r1.log').open('x') as log:
  subprocess.run([sys.executable,str(R/'scripts/phase5-score-with-frozen-cache-v4-r1.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 print('Frozenpolicyscoringcomplete;runningregisteredstatisticsand9figurecandidates.',flush=True)
 with (P/'final-analysis-products-v4.log').open('x') as log:
  subprocess.run([sys.executable,str(R/'scripts/phase5-final-analysis-products.py')],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=True)
 print('Stage5Dmachineproductscomplete;requiresindependentnumeric/visualreviewanddualmerge.',flush=True)
