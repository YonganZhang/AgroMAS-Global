"""Source-only null-profile investigation; no crop outputs are consulted."""
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import requests,json,hashlib
R=Path(__file__).resolve().parents[1]
# Nearby representative points are explicitly different coordinates, not repaired city observations.
POINTS=[('france_nearby_east',48.44,1.59),('kansas_nearby_north',37.89,-97.34),
        ('perth_nearby_east',-31.95,116.36),('netherlands_water',52.57,5.63),('luancheng_water',37.89,114.69)]

def fetch(item):
    name,lat,lon=item
    properties=('sand','silt','clay','bdod','soc','wv0010','wv0033','wv1500')
    params=[('lat',lat),('lon',lon)]+[('property',p) for p in properties]+[
        ('depth',d) for d in ('0-5cm','5-15cm','15-30cm','30-60cm','60-100cm')]+[('value','mean')]
    response=requests.get('https://rest.isric.org/soilgrids/v2.0/properties/query',params=params,timeout=60)
    out=R/'reports/phase5'/('soilgrids-followup-'+name+'.response')
    with out.open('xb') as f:f.write(response.content)
    out.chmod(0o444)
    try:
        body=response.json();layers={a['name']:[d['values'].get('mean') for d in a['depths']] for a in body['properties']['layers']}
    except Exception:layers=None
    return dict(name=name,latitude=lat,longitude=lon,http_status=response.status_code,url=response.url,
                sha256=hashlib.sha256(response.content).hexdigest(),layers=layers)

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=5) as pool:results=list(pool.map(fetch,POINTS))
    out=R/'reports/phase5/soilgrids-followup.json'
    with out.open('x') as f:json.dump(dict(time=datetime.now(timezone.utc).isoformat(),results=results,
        scope='Source investigation; no soil/profile selected and no regional calibration yet'),f,indent=2)
    out.chmod(0o444);print(json.dumps(results))
