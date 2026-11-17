"""Train2000 source/unit audit, noHeldOut and no parameter fitting."""
from pathlib import Path
import json,logging
from pcse_gym.agromas.runtime import RegionalWeeklyEnv
R=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 logging.disable(logging.CRITICAL)
 e=RegionalWeeklyEnv(str(R),beta=200,role='Train',evaluation=dict(region_id='china_ncp_luancheng',year=2000,climate='Historical',zone='standard_40',price_multiplier=1.,subsidy=0.))
 e.reset();done=False
 while not done:_,_,done,_,info=e.step(e.coordinated_action())
 names=['NORGT','NORG','NH4T','NO3T','NH4','NO3','RNH4UPTT','RNO3UPTT','NLOSSCUM','RNH4MINTT','RNORGDISTT','RNH4INTT','RNO3INTT','RNH4OUTTT','RNO3OUTTT','RNO3DENITRTT','RNH4NITRTT','RNO3NITRTT','RNORGAMTT','RNH4AMTT','RNO3AMTT']
 import numpy as np
 values={n:np.asarray(e.engine.get_variable(n)).tolist() for n in names}
 out=dict(initial_ledger=info['initial_stock_ledger'],diagnostic=info['stock_diagnostics'],native_values=values,outcome=info['outcome'])
 with (R/'reports/phase5/native-stock-units-audit-v2.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out),flush=True)
