"""Read-only audit of every sealed TRAIN/Dev native daily C/N ledger; no physics."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
import gzip,hashlib,json,time
import numpy as np
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8'

def audit(entry):
 path=R/entry['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'];maxn=0.;maxc=0.;days=0;failn=0;failc=0;rows=0;finaln=0.;finalc=0.
 with gzip.open(path,'rt') as f:
  for line in f:
   x=json.loads(line)
   if x['status']!='completed':raise ValueError('Failed row retained: '+str(x))
   v=np.asarray([r[1:] for r in x['daily_native']],float)
   if not np.isfinite(v).all():raise ValueError('Missing/non-finite daily native output')
   d={name:v[:,i] for i,name in enumerate(x['daily_columns'][1:])};s=x['stock_diagnostics']
   n=s['initial_soil_N_kg_ha']+1e4*(d['RNH4AMTT']+d['RNO3AMTT']+d['RNH4DEPOSTT']+d['RNO3DEPOSTT'])-d['NORGT']-d['NO3T']-d['NH4T']-1e4*(d['RNH4UPTT']+d['RNO3UPTT']+d['RNH4OUTTT']+d['RNO3OUTTT']-d['RNH4INTT']-d['RNO3INTT']+d['RNO3DENITRTT'])
   c=s['initial_soil_C_kg_ha']+1e4*d['RCORGAMTT']-d['CORGT']-1e4*d['RCORGDISTT']
   maxn=max(maxn,float(np.max(abs(n))));maxc=max(maxc,float(np.max(abs(c))));failn+=int(np.any(abs(n)>=1e-10));failc+=int(np.any(abs(c)>=1e-9));days+=len(v);rows+=1
   finaln=max(finaln,abs(s['soil_N_mass_balance_residual_kg_ha']));finalc=max(finalc,abs(s['soil_C_mass_balance_residual_kg_ha']))
 assert rows==343
 return dict(path=entry['path'],role=entry['role'],rows=rows,daily_records=days,max_abs_daily_N_residual_kg_ha=maxn,max_abs_daily_C_residual_kg_ha=maxc,N_bound_failing_rows=failn,C_bound_failing_rows=failc,max_abs_final_N_residual_kg_ha=finaln,max_abs_final_C_residual_kg_ha=finalc)

if __name__=='__main__':
 seen=set();results=[];deadline=time.monotonic()+7200
 with (P/'phase8b-daily-ledger-progress.jsonl').open('x') as log:
  with ProcessPoolExecutor(max_workers=8) as pool:
   pending={}
   while True:
    if time.monotonic()>deadline:raise TimeoutError('Bounded ledger audit timed out')
    source=P/'phase8b-physical-progress.jsonl'
    entries=[json.loads(s) for s in source.read_text().splitlines() if s] if source.exists() else []
    for entry in entries:
     if entry['path'] not in seen:pending[pool.submit(audit,entry)]=entry['path'];seen.add(entry['path'])
    if pending:
     done,_=wait(pending,timeout=5,return_when=FIRST_COMPLETED)
     for f in done:
      result=f.result();results.append(result);log.write(json.dumps(result)+'\n');log.flush();del pending[f];print(json.dumps({'audited_books':len(results),'daily_records':sum(x['daily_records'] for x in results)}),flush=True)
    else:
     if (P/'phase8b-physical-receipt.json').exists():break
     time.sleep(5)
 out=dict(status='passed' if all(x['N_bound_failing_rows']==0 and x['C_bound_failing_rows']==0 for x in results) else 'strict_bounds_failed_do_not_relax',books=len(results),physical_seasons=sum(x['rows'] for x in results),daily_records=sum(x['daily_records'] for x in results),max_abs_N_residual_kg_ha=max(x['max_abs_daily_N_residual_kg_ha'] for x in results),max_abs_C_residual_kg_ha=max(x['max_abs_daily_C_residual_kg_ha'] for x in results),N_bound_failing_seasons=sum(x['N_bound_failing_rows'] for x in results),C_bound_failing_seasons=sum(x['C_bound_failing_rows'] for x in results),scope='100% newly sealed TRAIN diagnostic replays and Dev books, NOT G2/G3 evaluation; PCSE untouched',files=results)
 assert len(results)==250
 (P/'phase8b-daily-ledger-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='files'}),flush=True)
