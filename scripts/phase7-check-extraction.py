"""Read-only exact45-key provenance, raw-mask, index and cross-boundary validation."""
from pathlib import Path
import importlib.util,json,hashlib,numpy as np
R=Path(__file__).resolve().parents[1];P=R/'reports/phase7';D=R/'data/phase7-alphaearth-v1'
s=importlib.util.spec_from_file_location('ex',R/'scripts/phase7-extract-alphaearth.py');ex=importlib.util.module_from_spec(s);s.loader.exec_module(ex)
if __name__=='__main__':
 ex.INDEX_SIZE=798152335 # immutable mirror index size recorded with source HTTP receipt
 manifest=json.loads((D/'manifest-alphaearth-v1.json').read_text());assert manifest['status']=='complete' and manifest['extracted_site_years']==45 and not manifest['missing_keys'];rows=json.loads((D/'site-year-index-v1.json').read_text());receipts=[];minN=2.;maxN=0.
 for row in rows:
  found=ex.lines_at(row['index_row_byte'])[0][1];assert found['path']==row['path'] and int(found['year'])==row['year'];meta=D/f"{row['site']}-{row['year']}.json";m=json.loads(meta.read_text());a=np.load(D/m['npz_file']);assert ex.sha((D/m['npz_file']).read_bytes())==m['npz_sha256']
  for name in ['station','macro']:
   raw=a[name+'_raw'];assert np.all((raw==-128)==(raw[...,:1]==-128));deq,valid,norm=ex.deq(raw);np.testing.assert_allclose(deq.astype('f4'),a[name+'_embedding'],equal_nan=True,rtol=0,atol=0);np.testing.assert_array_equal(valid,a[name+'_valid']);minN=min(minN,float(norm.min()));maxN=max(maxN,float(norm.max()))
  t=ex.TIFF(m['tiff_url']);x=t.ifds[0];xml=ex.ET.fromstring((D/f"{row['site']}-{row['year']}.vrt").read_bytes());assert [b.findtext('Description') for b in xml.findall('VRTRasterBand')]==[f'A{i:02}' for i in range(64)];assert str(row['epsg']) in xml.findtext('SRS');assert row['epsg'] in x[34735]
  receipts.append(dict(site=row['site'],year=row['year'],IFD0=dict(width=int(x[256][0]),height=int(x[257][0]),bands=int(x[277][0]),planar=int(x[284][0]),compression=int(x[259][0]),tile_width=int(x[322][0]),tile_height=int(x[323][0])),IFD5=dict(width=int(t.ifds[5][256][0]),height=int(t.ifds[5][257][0])),index_roundtrip=True,raw_dequantized_cubes_equal=True))
 # A deliberate window crossing both1024-pixel block boundaries checks stitching,
 # not just a station that happens to remain in one block. Cached source-only reads.
 m=json.loads((D/'netherlands_lelystad-2020.json').read_text());t=ex.TIFF(m['tiff_url']);raw=t.window(0,1020,1020,8,8)
 import rasterio
 from rasterio.windows import Window
 local=D/'netherlands_lelystad-2020-validation-only.vrt'
 with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR',CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tiff',GDAL_HTTP_TIMEOUT='60'):
  with rasterio.open(local) as ds:expected=ds.read(window=Window(1020,1020,8,8)).transpose(1,2,0)
 assert np.array_equal(raw,expected)
 (P/'extraction-complete-verification-v7.json').write_text(json.dumps(dict(passed=True,site_years=45,station_10m_pixels=45*64*64,macro_320m_pixels=45*256*256,raw_L2_min=minN,raw_L2_max=maxN,index_roundtrip_site_years=45,boundary_stitching_exact_values=int(raw.size),manifest_sha256=ex.sha((D/'manifest-alphaearth-v1.json').read_bytes()),receipts=receipts),indent=2));print('All45 cubes, masks, dequantization, index rows, IFD tags and a4-block-boundary VRT window verified')
