"""Exact daily soil-profile C/N closure; Nsurplus never relabelled native leaching."""
import numpy as np
DAILY=('CORGT','NORGT','NO3T','NH4T','NLOSSCUM','RCORGAMTT','RCORGDISTT','RNH4AMTT','RNO3AMTT','RNH4UPTT','RNO3UPTT','RNH4DEPOSTT','RNO3DEPOSTT','RNH4INTT','RNO3INTT','RNH4OUTTT','RNO3OUTTT','RNO3DENITRTT')
def audit_native_engine(engine,meta,outcome):
 from pcse_gym.agromas.final_evaluation import final_stock_diagnostics
 d=final_stock_diagnostics(engine,meta,outcome);rows=engine.get_output();v=np.array([[float(np.asarray(r[k]).sum()) for k in DAILY] for r in rows]);z={n:v[:,i] for i,n in enumerate(DAILY)}
 n=d['initial_soil_N_kg_ha']+1e4*(z['RNH4AMTT']+z['RNO3AMTT']+z['RNH4DEPOSTT']+z['RNO3DEPOSTT'])-z['NORGT']-z['NO3T']-z['NH4T']-1e4*(z['RNH4UPTT']+z['RNO3UPTT']+z['RNH4OUTTT']+z['RNO3OUTTT']-z['RNH4INTT']-z['RNO3INTT']+z['RNO3DENITRTT'])
 c=d['initial_soil_C_kg_ha']+1e4*z['RCORGAMTT']-z['CORGT']-1e4*z['RCORGDISTT'];mn=float(np.abs(n).max());mc=float(np.abs(c).max())
 passed=bool(np.isfinite(v).all() and mn<1e-10 and mc<1e-9 and abs(outcome[4]-d['native_fertilizer_N_kg_ha'])<=1e-6)
 return {'daily_records':[dict(date=str(row['day']),**{name:float(v[i,j]) for j,name in enumerate(DAILY)},N_residual_kg_ha=float(n[i]),C_residual_kg_ha=float(c[i])) for i,row in enumerate(rows)],'daily_rows':len(rows),'max_abs_N_residual_kg_ha':mn,'max_abs_C_residual_kg_ha':mc,'N_limit':1e-10,'C_limit':1e-9,'passed':passed,'native_loss_scope':'bottomleaching+denitrification,notNsurplusorwaterconcentration'}
