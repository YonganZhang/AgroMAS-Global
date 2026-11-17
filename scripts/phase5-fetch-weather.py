"""Acquire real immutable NASA archives; freeze date-only splits before any regional simulation."""
from pathlib import Path
from datetime import date
from concurrent.futures import ThreadPoolExecutor
import json,hashlib
from pcse_gym.agromas.regions import REGIONS,download_weather,metadata_partition
R=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    end=date(2026,11,1)  # Fixed acquisition cutoff before request; only complete envelopes enter roles.
    def fetch(region):return region.region_id,download_weather(region,R/'data/global_regions',end)
    with ThreadPoolExecutor(max_workers=3) as pool:receipts=dict(pool.map(fetch,REGIONS.values()))
    partitions={name:metadata_partition(REGIONS[name],meta) for name,meta in receipts.items()}
    payload=dict(status='date_metadata_frozen_before_regional_simulation',acquisition_cutoff=end.isoformat(),
                 regions=partitions,rule='No yield/soil/calendar/forecast calibration output used to assign roles',
                 heldout_unlocked=False)
    raw=json.dumps(payload,indent=2,sort_keys=True).encode()
    out=R/'reports/phase5/global-date-split-manifest.json'
    with out.open('xb') as f:f.write(raw)
    out.chmod(0o444)
    seal=out.with_suffix('.sha256');seal.write_text(hashlib.sha256(raw).hexdigest()+'\n');seal.chmod(0o444)
    summary={k:{role:len(years) for role,years in v['roles'].items()} for k,v in partitions.items()}
    print(json.dumps(summary))
