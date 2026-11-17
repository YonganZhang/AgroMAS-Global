"""Five archetype coordinates and metadata-only weather/split registration.

Raw archives are immutable. No yield/model output is accepted by split selection.
"""
from dataclasses import dataclass
from functools import lru_cache
from datetime import date,timedelta,datetime,timezone
from pathlib import Path
import hashlib,json
import numpy as np

PARAMETERS=('T2M_MIN','T2M_MAX','T2MDEW','ALLSKY_SFC_SW_DWN','PRECTOTCORR','RH2M','WS2M')

@dataclass(frozen=True)
class Region:
    region_id: str
    latitude: float
    longitude: float
    hemisphere: str
    sow_month: int
    sow_day: int
    harvest_month: int
    harvest_day: int

    def weather_envelope(self, harvest_year):
        if self.hemisphere=='north':
            return date(harvest_year-1,9,1),date(harvest_year,8,31)
        return date(harvest_year,1,1),date(harvest_year,12,31)

    def crop_dates(self, harvest_year):
        return (date(harvest_year-1 if self.hemisphere=='north' else harvest_year,self.sow_month,self.sow_day),
                date(harvest_year,self.harvest_month,self.harvest_day))

REGIONS={r.region_id:r for r in (
    Region('netherlands_lelystad',52.57,5.63,'north',10,3,8,20),
    Region('china_ncp_luancheng',37.89,114.69,'north',10,5,6,30),
    Region('usa_kansas_wichita',37.69,-97.34,'north',9,25,7,15),
    Region('france_paris_beauce',48.44,1.49,'north',10,10,8,20),
    Region('australia_wa_perth',-31.95,115.86,'south',5,15,12,15),
)}


def sha256(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_daily_payload(payload):
    values=payload['properties']['parameter']
    fill=payload.get('header',{}).get('fill_value',-999)
    if set(PARAMETERS)-set(values):raise ValueError('Missing NASA weather fields')
    dates=sorted(set.intersection(*(set(values[p]) for p in PARAMETERS)))
    if not dates:raise ValueError('No complete weather date keys')
    complete=[];invalid=[]
    for key in dates:
        x=np.array([values[p][key] for p in PARAMETERS],dtype=float)
        if (not np.isfinite(x).all() or np.any(x==fill) or x[0]>x[1] or
            min(x[3:])<0 or x[5]>100):invalid.append(key)
        else:complete.append(key)
    # Units come from the response, not assumptions about community defaults.
    units={p:payload['parameters'][p]['units'] for p in PARAMETERS}
    if units['ALLSKY_SFC_SW_DWN'] not in ('MJ/m^2/day','MJ/m2/day'):
        raise ValueError('Unexpected radiation units: '+units['ALLSKY_SFC_SW_DWN'])
    if units['PRECTOTCORR'] not in ('mm/day','mm'):
        raise ValueError('Unexpected rain units: '+units['PRECTOTCORR'])
    return dict(complete_dates=complete,invalid_dates=invalid,units=units,
                first_date=dates[0],last_date=dates[-1],fill_value=fill)


def download_weather(region, data_root, end_date):
    import requests
    out=Path(data_root)/region.region_id;out.mkdir(parents=True,exist_ok=True)
    stem='nasa-power-19840101-'+end_date.strftime('%Y%m%d')
    raw=out/(stem+'.json');receipt=out/(stem+'.receipt.json')
    if raw.exists():
        if not receipt.exists():raise ValueError('Unreceipted immutable raw response')
        meta=json.loads(receipt.read_text())
        if sha256(raw)!=meta['sha256']:raise ValueError('Raw weather SHA drift')
        return meta
    params=dict(latitude=region.latitude,longitude=region.longitude,start='19840101',
                end=end_date.strftime('%Y%m%d'),community='AG',format='JSON',
                parameters=','.join(PARAMETERS))
    params['time-standard']='LST'
    response=requests.get('https://power.larc.nasa.gov/api/temporal/daily/point',params=params,timeout=180)
    response.raise_for_status()
    payload=response.json();validation=validate_daily_payload(payload)
    with raw.open('xb') as f:f.write(response.content)
    raw.chmod(0o444)
    meta=dict(region_id=region.region_id,latitude=region.latitude,longitude=region.longitude,
              request_url=response.url,downloaded_at=datetime.now(timezone.utc).isoformat(),
              sha256=sha256(raw),raw_file=str(raw),http_status=response.status_code,
              api_header=payload.get('header'),validation=validation,
              scope='NASA satellite/reanalysis grid; not ground station measurement')
    with receipt.open('x') as f:json.dump(meta,f,indent=2)
    receipt.chmod(0o444)
    return meta


def metadata_partition(region, weather_metadata):
    """Fixed chronological roles; metadata only. NL pre2022 heldout gap is public reuse."""
    valid=set(weather_metadata['validation']['complete_dates'])
    first=date.fromisoformat(weather_metadata['validation']['first_date'][:4]+'-01-01').year
    last=int(weather_metadata['validation']['last_date'][:4])
    roles={x:[] for x in ('Train','Dev','Held-Out','Public-Reused-Benchmark')}
    rejected=[]
    for year in range(first,last+1):
        start,end=region.weather_envelope(year)
        required={(start+timedelta(days=i)).strftime('%Y%m%d') for i in range((end-start).days+1)}
        missing=required-valid
        if missing:
            rejected.append(dict(harvest_year=year,reason='incomplete_date_envelope',missing_count=len(missing)))
            continue
        role='Train' if year<=2009 else 'Dev' if year<=2014 else 'Held-Out'
        if region.region_id=='netherlands_lelystad' and 2015<=year<=2021:role='Public-Reused-Benchmark'
        roles[role].append(year)
    if any(not roles[x] for x in ('Train','Dev','Held-Out')):
        raise ValueError('Insufficient complete seasons for preregistered roles')
    return dict(region_id=region.region_id,roles=roles,rejected=rejected,raw_weather_sha256=weather_metadata['sha256'],
                method='Date-only fixed cutoffs Train<=2009,Dev2010-2014,Held-Out>=2015;NLindependent>=2022',
                envelope='NH Sep1(previous)-Aug31(harvest);SH Jan1-Dec31(harvest)',
                calibration_outputs_seen=False)


def load_split_manifest(path):
    path=Path(path)
    expected=path.with_suffix('.sha256').read_text().strip()
    if sha256(path)!=expected:raise ValueError('Date partition seal drift')
    data=json.loads(path.read_text())
    if data['status']!='date_metadata_frozen_before_regional_simulation':
        raise ValueError('Missing metadata-first freeze')
    return data


@lru_cache(maxsize=1024)
def _digest_stat_version(path,size,mtime_ns,ctime_ns,inode):
    return sha256(path)


def frozen_asset_sha(path):
    """Avoid hashing large unchanged weights everyepisode; detect ordinary drift.

    Writable code/config is always hashed: metadata resolution can be coarse on
    network filesystems. Only already-readonly immutable assets use stat-keyed
    caching. This relies on the explicit no-overwrite boundary, not root security.
    """
    path=Path(path).resolve();stat=path.stat()
    if stat.st_mode&0o222:return sha256(path)
    return _digest_stat_version(str(path),stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns,stat.st_ino)


def authorize_year(manifest,region_id,year,role,*,permit_path=None,project_root=None):
    if role not in ('Train','Dev','Held-Out','Public-Reused-Benchmark'):
        raise ValueError('Unknown year role')
    if year not in manifest['regions'][region_id]['roles'][role]:
        raise ValueError('Year does not belong to requested role')
    if role in ('Held-Out','Public-Reused-Benchmark'):
        if permit_path is None or project_root is None:raise ValueError('Final evaluation locked')
        path=Path(permit_path)
        if sha256(path)!=path.with_suffix('.sha256').read_text().strip():
            raise ValueError('Final evaluation permit drift')
        permit=json.loads(path.read_text())
        if not (permit.get('all_models_frozen') and permit.get('dev_verified') and permit.get('subsidy_train_frozen')):
            raise ValueError('Incomplete final model/policy freeze')
        if not permit.get('files'):raise ValueError('No frozen assets')
        if permit.get('split_manifest_sha256')!=sha256(Path(project_root)/'reports/phase5/global-date-split-manifest.json'):
            raise ValueError('Final split hash mismatch')
        for relative,digest in permit['files'].items():
            target=(Path(project_root)/relative).resolve()
            if not target.is_relative_to(Path(project_root).resolve()):raise ValueError('Freeze path escape')
            if frozen_asset_sha(target)!=digest:raise ValueError('Frozen source/model asset drift: '+relative)
    return year
