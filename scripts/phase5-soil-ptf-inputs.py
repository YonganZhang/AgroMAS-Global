"""Immutable source inputs for published HiHydroSoil/Toth pedotransfer equations."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import requests,json,hashlib
R=Path(__file__).resolve().parents[1]
POINTS=[('netherlands_lelystad',52.57,5.63),('china_ncp_luancheng',37.89,114.69),
        ('usa_kansas_wichita',37.89,-97.34),('france_paris_beauce',48.44,1.59),('australia_wa_perth',-31.95,116.36)]

def fetch(point):
    name,lat,lon=point
    params=[('lat',lat),('lon',lon)]+[('property',p) for p in ('sand','silt','clay','bdod','soc','phh2o','cec','nitrogen')]+[
        ('depth',d) for d in ('0-5cm','5-15cm','15-30cm','30-60cm','60-100cm','100-200cm')]+[('value','mean')]
    response=requests.get('https://rest.isric.org/soilgrids/v2.0/properties/query',params=params,timeout=90)
    response.raise_for_status()
    out=R/'data/global_regions'/name/'soilgrids-ptf-source.json'
    with out.open('xb') as f:f.write(response.content)
    out.chmod(0o444)
    receipt=dict(region_id=name,soil_latitude=lat,soil_longitude=lon,url=response.url,
                 sha256=hashlib.sha256(response.content).hexdigest(),timestamp=datetime.now(timezone.utc).isoformat(),
                 source='ISRIC SoilGrids gridded estimates, not farm observations',
                 selection='Point fixed before any regional crop output; city-null alternatives explicitly separate from weather coordinates')
    with out.with_suffix('.receipt.json').open('x') as f:json.dump(receipt,f,indent=2)
    out.with_suffix('.receipt.json').chmod(0o444)
    return receipt

if __name__=='__main__':
    with ThreadPoolExecutor(max_workers=5) as pool:receipts=list(pool.map(fetch,POINTS))
    out=R/'reports/phase5/soil-ptf-source-registry.json'
    with out.open('x') as f:json.dump(receipts,f,indent=2)
    url='https://www.futurewater.nl/wp-content/uploads/2020/10/HiHydroSoil-v2.0-High-Resolution-Soil-Maps-of-Global-Hydraulic-Properties.pdf'
    response=requests.get(url,timeout=60);response.raise_for_status()
    pdf=R/'reports/phase5/HiHydroSoil-v2.0-Report213.pdf'
    with pdf.open('xb') as f:f.write(response.content)
    pdf.chmod(0o444)
    print(json.dumps(receipts))
