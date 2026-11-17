"""Independent endpoint assertions for all newly generated TRAIN/Dev rows, no physics."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import gzip,hashlib,json
import numpy as np
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8'
def audit(ent):
 path=R/ent['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==ent['sha256'];rows=0;fert_error=0.;identity_error=0.;loss_error=0.
 with gzip.open(path,'rt') as f:
  for line in f:
   x=json.loads(line);assert x['status']=='completed';m=np.asarray(x['outcome'],float);d=x['stock_diagnostics'];assert np.isfinite(m).all()
   fert_error=max(fert_error,abs(m[4]-d['native_fertilizer_N_kg_ha']));assert abs(m[4]-d['native_fertilizer_N_kg_ha'])<=1e-6
   err=max(abs(m[2]-(m[4]+m[5]-m[1])),abs(m[3]-m[1]/(m[4]+m[5])));identity_error=max(identity_error,err);assert err<1e-10
   assert -1e-8<=m[4]<=220+1e-8 and m[0]>=-1e-8 and -1e-8<=m[1]<=1000*m[0]+1e-7
   assert abs(m[5]-3.5)<1e-10
   last=x['daily_native'][-1];native_loss=last[x['daily_columns'].index('NLOSSCUM')];loss_error=max(loss_error,abs(native_loss-d['native_Nloss_kg_ha']));assert abs(native_loss-d['native_Nloss_kg_ha'])<1e-10
   rows+=1
 return dict(path=ent['path'],rows=rows,max_native_fert_error=fert_error,max_accounting_identity_error=identity_error,max_daily_final_Nloss_error=loss_error)
if __name__=='__main__':
 receipt=json.loads((P/'phase8b-physical-receipt.json').read_text());assert receipt['status']=='completed' and len(receipt['files'])==250
 results=[]
 with ProcessPoolExecutor(max_workers=8) as pool:
  for f in as_completed([pool.submit(audit,e) for e in receipt['files']]):results.append(f.result());print(len(results),flush=True)
 out=dict(status='passed',books=len(results),seasons=sum(e['rows'] for e in results),max_native_fert_error=max(e['max_native_fert_error'] for e in results),max_accounting_identity_error=max(e['max_accounting_identity_error'] for e in results),max_daily_final_Nloss_error=max(e['max_daily_final_Nloss_error'] for e in results),no_new_physical_calls=True,files=results)
 (P/'phase8b-native-endpoint-audit.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items() if k!='files'}))
