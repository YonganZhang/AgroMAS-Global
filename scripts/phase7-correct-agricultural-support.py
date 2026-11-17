"""Correct only WorldCover sensitivity selection on the exact snapped AEF footprint."""
from pathlib import Path
import json,shutil,math,numpy as np
from affine import Affine
from rasterio.warp import reproject,Resampling
from pyproj import Transformer
R=Path(__file__).resolve().parents[1];P=R/'reports/phase7';D=R/'data/phase7-alphaearth-v1'
if __name__=='__main__':
 archive=P/'agricultural-support-attempt1-v7';archive.mkdir(exist_ok=True)
 for name in ['landcover-and-agricultural-ring-v7.json','agricultural-patch-extraction-v7.json','spatial-dispersion-v7.json']:
  dest=archive/name
  if not dest.exists():shutil.copy2(P/name,dest)
 audit=json.loads((archive/'landcover-and-agricultural-ring-v7.json').read_text());index=json.loads((D/'site-year-index-v1.json').read_text());checks=[]
 for a in audit:
  row=next(x for x in index if x['site']==a['site']);meta=json.loads((D/f"{a['site']}-2020.json").read_text());epsg=meta['epsg'] if 'epsg' in meta else None
  # CRS is independently recoverable from the validated VRT.
  import rasterio
  crs=rasterio.crs.CRS.from_epsg(meta['epsg'])
  west,north=float(row['utm_west']),float(row['utm_north']);e,n=meta['easting'],meta['northing'];c=int((e-west)//10);t=int((north-n)//10);c0,t0=c-560,t-560
  raw=np.load(D/f"{a['site']}-WorldCover2021.npz");grid=np.zeros((1120,1120),dtype='u1');tr=Affine(10,0,west+10*c0,0,-10,north-10*t0)
  reproject(raw['landscape_class'],grid,src_transform=Affine(*raw['landscape_transform']),src_crs=4326,dst_transform=tr,dst_crs=crs,resampling=Resampling.nearest)
  integ=np.pad((grid==40).astype('i4'),((1,0),(1,0))).cumsum(0).cumsum(1);counts=integ[64:,64:]-integ[:-64,64:]-integ[64:,:-64]+integ[:-64,:-64]
  yy,xx=np.indices(counts.shape);cols=c0+xx+32;tops=t0+yy+32;east=west+10*(cols+.5);ns=north-10*(tops+.5);dist=np.hypot(east-e,ns-n);allowed=(dist<=5000)&(counts>=math.ceil(.8*4096));old=a['agricultural_patch'];oldfraction=None
  if old:
   oc=math.floor((old['easting']-west)/10)-c0-32;ot=math.floor((north-old['northing'])/10)-t0-32;oldfraction=float(counts[ot,oc]/4096)
  if allowed.any():
   iy,ix=np.unravel_index(np.argmin(np.where(allowed,dist,np.inf)),dist.shape);ee,nn=float(east[iy,ix]),float(ns[iy,ix]);lon,lat=Transformer.from_crs(crs,4326,always_xy=True).transform(ee,nn);pt=dict(easting=ee,northing=nn,lat=lat,lon=lon,distance_m=float(dist[iy,ix]),local_cropland_fraction=float(counts[iy,ix]/4096),cropland_pixels=int(counts[iy,ix]),total_pixels=4096,support='Exact AEF snapped64x64 UTM10m footprint, nearest-neighbor WorldCover2021');a['agricultural_patch']=pt
  else:a['agricultural_patch']=None
  a['rule']='Nearest AEF pixel center within5km whose exact snapped64x64 UTM10m footprint contains at least80% nearest-neighbor WorldCover2021 class40; target and AEF values unused'
  checks.append(dict(site=a['site'],original_candidate_exact_fraction=oldfraction,corrected_candidate=a['agricultural_patch']))
 (P/'landcover-and-agricultural-ring-v7.json').write_text(json.dumps(audit,indent=2));(P/'agricultural-exact-support-correction-v7.json').write_text(json.dumps(dict(reason='Astra F1: geographic screening rectangle differed from extracted UTM support',original_evidence_preserved=str(archive.relative_to(R)),selection_uses_only_WorldCover_and_coordinates=True,station_analyses_unchanged=True,checks=checks),indent=2));print(checks)
