"""Source-fidelity v2 addition: actual NASA daily T2M, preserve all v1 raw files."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import requests,json,hashlib
from pcse_gym.agromas.regions import REGIONS
R=Path(__file__).resolve().parents[1]
def fetch(region):
    params=dict(latitude=region.latitude,longitude=region.longitude,start='19840101',end='20261101',community='AG',format='JSON',parameters='T2M')
    params['time-standard']='LST'
    r=requests.get('https://power.larc.nasa.gov/api/temporal/daily/point',params=params,timeout=120);r.raise_for_status()
    body=r.json()
    if body['parameters']['T2M']['units']!='C':raise ValueError('Unexpected T2M units')
    p=R/'data/global_regions'/region.region_id/'nasa-t2m-19840101-20261101-v2.json'
    with p.open('xb') as f:f.write(r.content)
    p.chmod(0o444)
    receipt=dict(region_id=region.region_id,url=r.url,sha256=hashlib.sha256(r.content).hexdigest(),
                 timestamp=datetime.now(timezone.utc).isoformat(),reason='Native PCSE NASA provider uses dailyT2M, not(Tmin+Tmax)/2',
                 role_policy='Existing frozen year roles unchanged; date/field validation required before use')
    with p.with_suffix('.receipt.json').open('x') as f:json.dump(receipt,f,indent=2)
    p.with_suffix('.receipt.json').chmod(0o444)
    return receipt
if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(fetch,REGIONS.values()))
    with (R/'reports/phase5/nasa-t2m-v2-source-registry.json').open('x') as f:json.dump(rows,f,indent=2)
    print(json.dumps(rows))
