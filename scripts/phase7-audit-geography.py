"""Independent GDAL/VRT orientation and ESA WorldCover station/cropland-ring audit."""
from pathlib import Path
import importlib.util,json,hashlib,math,xml.etree.ElementTree as ET
import numpy as np,rasterio
from rasterio.windows import Window,from_bounds
from rasterio.warp import reproject,Resampling
from affine import Affine
from pyproj import Transformer
from scipy.ndimage import uniform_filter
R=Path(__file__).resolve().parents[1];D=R/'data/phase7-alphaearth-v1';P=R/'reports/phase7'
s=importlib.util.spec_from_file_location('extract',R/'scripts/phase7-extract-alphaearth.py');ex=importlib.util.module_from_spec(s);s.loader.exec_module(ex)
def audit_landcover():
 out=[]
 for site,(lat,lon,epsg) in ex.SITES.items():
  lat0=int(math.floor(lat/3)*3);lon0=int(math.floor(lon/3)*3);tile=f"{'N' if lat0>=0 else 'S'}{abs(lat0):02d}{'E' if lon0>=0 else 'W'}{abs(lon0):03d}";url=f'https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_{tile}_Map.tif'
  forward=Transformer.from_crs(4326,epsg,always_xy=True);inverse=Transformer.from_crs(epsg,4326,always_xy=True);e,n=forward.transform(lon,lat)
  with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif',GDAL_HTTP_TIMEOUT='60'):
   with rasterio.open(url) as ds:
    lo1,la1=inverse.transform(e-5500,n-5500);lo2,la2=inverse.transform(e+5500,n+5500);win=from_bounds(min(lo1,lo2),min(la1,la2),max(lo1,lo2),max(la1,la2),ds.transform).round_offsets().round_lengths();v=ds.read(1,window=win);tr=ds.window_transform(win)
    yy,xx=np.indices(v.shape);longitude,latitude=tr*(xx+.5,yy+.5);east,north=forward.transform(longitude,latitude);dist=np.hypot(east-e,north-n)
    # Preliminary geographic screen only; final eligibility uses exact snapped UTM support below.
    sy=max(1,round(640/(111320*abs(tr.e))));sx=max(1,round(640/(111320*math.cos(math.radians(lat))*tr.a)));fraction=uniform_filter((v==40).astype(float),size=(sy,sx),mode='constant');allowed=(dist<=5000)&(fraction>=.8)&(v==40)
    if allowed.any():idx=np.argmin(np.where(allowed,dist,np.inf));iy,ix=np.unravel_index(idx,v.shape);agri=dict(easting=float(east[iy,ix]),northing=float(north[iy,ix]),lat=float(latitude[iy,ix]),lon=float(longitude[iy,ix]),distance_m=float(dist[iy,ix]),local_cropland_fraction=float(fraction[iy,ix]))
    else:agri=None
    patch=np.zeros((64,64),dtype='u1');dest=Affine(10,0,e-320,0,-10,n+320);reproject(v,patch,src_transform=tr,src_crs=4326,dst_transform=dest,dst_crs=epsg,resampling=Resampling.nearest)
    ring=(dist<=5000)&(dist>=320);classes,counts=np.unique(patch,return_counts=True)
    target=D/f'{site}-WorldCover2021.npz';np.savez_compressed(target,station_class=patch,landscape_class=v,landscape_transform=np.asarray(tuple(tr)[:6]),agricultural_candidate_mask=allowed)
    result=dict(site=site,source_url=url,source_year=2021,station_class_counts={str(a):int(b) for a,b in zip(classes,counts)},station_cropland_fraction=float((patch==40).mean()),ring_5km_cropland_fraction=float((v[ring]==40).mean()),agricultural_patch=agri,npz_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),rule='Nearest center within5km with at least80% WorldCover2021 cropland in640m window; absent candidate retained as missing, no city-to-wheatbelt substitution',scope='Land cover classification is not wheat identity or field validation; static2021 audit does not assert annual2017–2025 land use',attribution='© ESA WorldCover project2021 / Contains modified Copernicus Sentinel data2021 processed by ESA WorldCover consortium',license='CC-BY-4.0');out.append(result);print(site,result['station_cropland_fraction'],agri,flush=True)
 (P/'landcover-and-agricultural-ring-v7.json').write_text(json.dumps(out,indent=2))
 import subprocess
 subprocess.run([__import__('sys').executable,str(R/'scripts/phase7-correct-agricultural-support.py')],check=True)
def audit_vrt():
 out=[]
 for site,year in [('netherlands_lelystad',2020),('australia_wa_perth',2020)]:
  meta=D/f'{site}-{year}.json'
  if not meta.exists():continue
  m=json.loads(meta.read_text());vrt=(D/f'{site}-{year}.vrt').read_text();xml=ET.fromstring(vrt);xml.find('.//SourceDataset').text='/vsicurl/'+m['tiff_url'];local=D/f'{site}-{year}-validation-only.vrt';local.write_bytes(ET.tostring(xml));i=m['indexing']
  with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tiff',GDAL_HTTP_TIMEOUT='60'):
   with rasterio.open(local) as ds:
    assert ds.index(m['easting'],m['northing'])==(i['vrt_top_down_row'],i['col']);actual=ds.read([1,17,64],window=Window(i['station_top_left_col'],i['station_top_left_row'],64,64));expected=np.load(D/m['npz_file'])['station_raw'][:,:,[0,16,63]].transpose(2,0,1);assert np.array_equal(actual,expected),(site,np.max(abs(actual.astype(int)-expected.astype(int))))
  out.append(dict(site=site,year=year,exact_pixels_verified=int(actual.size),bands=[1,17,64],all_equal=True,rasterio_version=rasterio.__version__,GDAL_version=rasterio.__gdal_version__,method='Independent GDAL reads companion top-down VRT, byte-exact comparison with standalone bottom-up range extractor'))
 (P/'independent-VRT-orientation-v7.json').write_text(json.dumps(out,indent=2));print('VRT validated',len(out),flush=True)
if __name__=='__main__':audit_landcover();audit_vrt()
