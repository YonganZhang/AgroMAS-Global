"""Add predeclared WorldCover-selected patches without moving registered station points."""
from pathlib import Path
import importlib.util,json,numpy as np,math,hashlib
R=Path(__file__).resolve().parents[1];D=R/'data/phase7-alphaearth-v1';P=R/'reports/phase7'
s=importlib.util.spec_from_file_location('ex',R/'scripts/phase7-extract-alphaearth.py');ex=importlib.util.module_from_spec(s);s.loader.exec_module(ex)
if __name__=='__main__':
 audit=json.loads((P/'landcover-and-agricultural-ring-v7.json').read_text());index=json.loads((D/'site-year-index-v1.json').read_text());out=[]
 for a in audit:
  pt=a['agricultural_patch']
  if pt is None:continue
  assert pt['distance_m']<=5000 and pt['local_cropland_fraction']>=.8
  assert pt.get('support','').startswith('Exact AEF snapped'), 'Run exact-support WorldCover correction before extraction'
  for row in [x for x in index if x['site']==a['site']]:
   west,south,east,north=map(float,(row['utm_west'],row['utm_south'],row['utm_east'],row['utm_north']));e,n=pt['easting'],pt['northing'];assert west+320<=e<east-320 and south+320<=n<north-320
   url=row['path'].replace('s3://us-west-2.opendata.source.coop/','https://s3.us-west-2.amazonaws.com/us-west-2.opendata.source.coop/');reader=ex.TIFF(url);col=math.floor((e-west)/10);top=math.floor((north-n)/10);raw=reader.window(0,col-32,top-32,64,64);emb,valid,norm=ex.deq(raw);f=D/f"{a['site']}-{row['year']}-agricultural.npz";np.savez_compressed(f,raw=raw,embedding=emb.astype('f4'),valid=valid);out.append(dict(site=a['site'],year=row['year'],crop_center=pt,source_url=url,path=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),pct_valid=float(valid.mean()*100),L2_min=float(norm.min()),L2_max=float(norm.max()),col=col,top_down_row=top,http_ranges=reader.ranges));print(f.name,flush=True)
 (P/'agricultural-patch-extraction-v7.json').write_text(json.dumps(dict(station_coordinates_unchanged=True,qualifying_sites=[a['site'] for a in audit if a['agricultural_patch'] is not None],nonqualifying_sites=[a['site'] for a in audit if a['agricultural_patch'] is None],site_years=out),indent=2))
