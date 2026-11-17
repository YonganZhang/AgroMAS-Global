"""Fit causal regional forecasts using only the first ten TRAIN season envelopes.

Later TRAIN harvest years1995..2009 are reserved for outcome/continuation teachers.
No Dev or Held-Out weather enters forecasting coefficients or residual pools.
"""
from pathlib import Path
from datetime import timedelta
import hashlib,json,logging
import joblib
from pcse_gym.agromas.regions import REGIONS,load_split_manifest
from pcse_gym.agromas.season import regional_weather
from pcse_gym.agromas.climate_agent import ClimateForecastAgent
R=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    logging.disable(logging.CRITICAL)
    p=R/'reports/phase5/climate-training-protocol-v2.json'
    protocol=dict(status='registered_before_forecast_fit',fit_envelopes='First10Train harvest seasons per region',
        outcome_teacher_harvest_years=list(range(1995,2010)),ensemble_size=32,ridge=1.,
        validation='Rolling-origin TRAIN calendar-year residuals,14day boundary purge',
        interpretation='Statistical forecast, not operational NWP; NASA archive only; future truth denied at inference',
        split_sha256=hashlib.sha256((R/'reports/phase5/global-date-split-manifest.json').read_bytes()).hexdigest())
    with p.open('x') as f:json.dump(protocol,f,indent=2)
    p.chmod(0o444)
    m=load_split_manifest(R/'reports/phase5/global-date-split-manifest.json')
    out=R/'models/phase5/climate-v2';out.mkdir(parents=True,exist_ok=False)
    records=[]
    for name,region in REGIONS.items():
        years=m['regions'][name]['roles']['Train'][:10]
        allowed=set()
        for year in years:
            start,end=region.weather_envelope(year)
            allowed.update(start+timedelta(days=i) for i in range((end-start).days+1))
        assert all(y in m['regions'][name]['roles']['Train'] for y in protocol['outcome_teacher_harvest_years'])
        weather=regional_weather(str(R),name,'v2')
        history=weather.history(min(allowed),max(allowed),as_of=max(allowed))
        model=ClimateForecastAgent(ensemble_size=32,ridge=1.).fit(history,allowed)
        path=out/(name+'.joblib')
        joblib.dump(model,path,compress=3);path.chmod(0o444)
        records.append(dict(region_id=name,model_id=model.model_id,source_id=model.source_id,
             train_first=str(min(allowed)),train_last=str(max(allowed)),train_dates=len(allowed),
             rolling_origin_residual_blocks=len(model.residual),path=str(path.relative_to(R)),
             sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        print(json.dumps(records[-1]),flush=True)
    receipt=R/'reports/phase5/climate-train-freeze-v2.json'
    with receipt.open('x') as f:json.dump(dict(protocol=protocol,models=records,dev_used=False,heldout_used=False),f,indent=2)
    receipt.chmod(0o444)
