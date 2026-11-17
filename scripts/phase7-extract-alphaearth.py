"""Deterministic anonymous HTTP-range AlphaEarth BigTIFF extractor; no GDAL needed."""
from pathlib import Path
import argparse,csv,hashlib,io,json,math,struct,subprocess,time,threading,xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import numpy as np, requests
from pyproj import Transformer
R=Path(__file__).resolve().parents[1];D=R/'data/phase7-alphaearth-v1';D.mkdir(parents=True,exist_ok=True)
BASE='https://s3.us-west-2.amazonaws.com/us-west-2.opendata.source.coop/tge-labs/aef/v1/annual/'
SITES={'netherlands_lelystad':(52.57,5.63,32631),'france_paris_beauce':(48.44,1.49,32631),'usa_kansas_wichita':(37.69,-97.34,32614),'china_ncp_luancheng':(37.89,114.69,32650),'australia_wa_perth':(-31.95,115.86,32750)}
FIELDS=['WKT','crs','path','year','utm_zone','utm_west','utm_south','utm_east','utm_north','wgs84_west','wgs84_south','wgs84_east','wgs84_north']
def sha(b):return hashlib.sha256(b).hexdigest()
def fetch(url,start=None,end=None):
 key=sha(f'{url}:{start}:{end}'.encode());cache=D/'http-cache'/key;cache.parent.mkdir(exist_ok=True)
 if cache.exists() and cache.with_suffix('.json').exists():
  content=cache.read_bytes();metadata=json.loads(cache.with_suffix('.json').read_text())
  if sha(content)==metadata['sha256']:return content
 for attempt in range(4):
  try:
   rr=requests.get(url,headers={} if start is None else {'Range':f'bytes={start}-{end}'},timeout=90);rr.raise_for_status()
   if start is not None:
    assert rr.status_code==206 and rr.headers['Content-Range'].startswith(f'bytes {start}-'),(rr.status_code,rr.headers)
    assert len(rr.content)==end-start+1
   cache.write_bytes(rr.content);(cache.with_suffix('.json')).write_text(json.dumps(dict(url=url,start=start,end=end,sha256=sha(rr.content),ETag=rr.headers.get('ETag'),last_modified=rr.headers.get('Last-Modified'))));return rr.content
  except (requests.RequestException,AssertionError):
   if attempt==3:raise
   time.sleep(2**attempt)
def key(row):return (row['utm_zone'][-1],int(row['utm_zone'][:-1]))
def lines_at(pos,size=32768):
 b=fetch(BASE+'aef_index.csv',pos,min(INDEX_SIZE-1,pos+size-1));chunks=b.splitlines(keepends=True);off=pos
 if pos and fetch(BASE+'aef_index.csv',pos-1,pos-1)!=b'\n':off+=len(chunks.pop(0))
 out=[]
 if chunks and not chunks[-1].endswith(b'\n'):chunks.pop()
 for line in chunks:
  if line.strip() and not line.startswith(b'WKT,'):out.append((off,dict(zip(FIELDS,next(csv.reader([line.decode()]))))))
  off+=len(line)
 return out
def locate(target,upper=False):
 lo=0;hi=INDEX_SIZE
 while hi-lo>32768:
  mid=(lo+hi)//2;row=lines_at(mid)[0][1];k=key(row)
  if k<target or (upper and k==target):lo=mid
  else:hi=mid
 return max(0,lo-32768),min(INDEX_SIZE,hi+32768)
def index_sites():
 output=[]
 for zone in sorted({(str(epsg)[2:] if False else ('N' if epsg<32700 else 'S'),epsg%100) for _,_,epsg in SITES.values()}):
  a,_=locate(zone);_,b=locate(zone,True);rows=lines_at(a,b-a)
  for site,(lat,lon,epsg) in SITES.items():
   if zone!=('N' if epsg<32700 else 'S',epsg%100):continue
   e,n=Transformer.from_crs(4326,epsg,always_xy=True).transform(lon,lat)
   for year in range(2017,2026):
    matches=[(pos,row) for pos,row in rows if key(row)==zone and int(row['year'])==year and float(row['utm_west'])<=e<float(row['utm_east']) and float(row['utm_south'])<=n<float(row['utm_north'])]
    assert len(matches)==1,(site,year,len(matches));pos,row=matches[0];output.append(dict(row,site=site,year=year,easting=e,northing=n,lat=lat,lon=lon,epsg=epsg,index_row_byte=pos,index_zone_range=[a,b]))
  print('Indexed',zone,'range',a,b,flush=True)
 assert len(output)==45;(D/'site-year-index-v1.json').write_text(json.dumps(output,indent=2));return output
SIZES={1:1,2:1,3:2,4:4,5:8,12:8,16:8,17:8,18:8};DT={1:'u1',2:'u1',3:'<u2',4:'<u4',12:'<f8',16:'<u8',17:'<i8',18:'<u8'}
class TIFF:
 def __init__(self,url):
  self.url=url;self.ranges=[];h=self.read(0,16);assert h[:4]==b'II+\x00' and struct.unpack_from('<H',h,4)[0]==8;off=struct.unpack_from('<Q',h,8)[0];self.ifds=[]
  for level in range(6):
   count=struct.unpack('<Q',self.read(off,8))[0];raw=self.read(off+8,count*20+8);tags={}
   for i in range(count):
    tag,typ,n,value=struct.unpack_from('<HHQQ',raw,i*20);size=SIZES[typ]*n;b=raw[i*20+12:i*20+20][:size] if size<=8 else self.read(value,size)
    tags[tag]=b if typ==2 else np.frombuffer(b,dtype=DT[typ]).copy()
   self.ifds.append(tags);off=struct.unpack_from('<Q',raw,count*20)[0]
  t=self.ifds[0];assert int(t[277][0])==64 and int(t[284][0])==2 and int(t[259][0])==50000 and int(t[322][0])==1024 and int(t[323][0])==1024
  assert np.all(t[258]==8) and np.all(t[339]==2) and t[42113].rstrip(b'\0')==b'-128'
 def read(self,start,size):
  self.ranges.append([int(start),int(start+size-1)]);return fetch(self.url,int(start),int(start+size-1))
 def block(self,level,band,bx,by):
  t=self.ifds[level];tw,th=int(t[322][0]),int(t[323][0]);w,h=int(t[256][0]),int(t[257][0]);nx=math.ceil(w/tw);ny=math.ceil(h/th);ix=band*nx*ny+by*nx+bx
  raw=self.read(int(t[324][ix]),int(t[325][ix]));dec=subprocess.run(['/usr/bin/zstd','-q','-d','-c'],input=raw,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True).stdout;assert len(dec)==tw*th
  return np.frombuffer(dec,dtype=np.int8).reshape(th,tw)
 def window(self,level,x0,y0,width,height):
  t=self.ifds[level];tw,th=int(t[322][0]),int(t[323][0]);w,h=int(t[256][0]),int(t[257][0]);assert 0<=x0 and x0+width<=w and 0<=y0 and y0+height<=h
  out=np.empty((height,width,64),np.int8)
  def band_extract(band):
   v=np.empty((height,width),np.int8)
   # y0 is TOP-DOWN; TIFF block rows are BOTTOM-UP.
   for by in range((h-y0-height)//th,(h-y0-1)//th+1):
    for bx in range(x0//tw,(x0+width-1)//tw+1):
     block=self.block(level,band,bx,by);top=h-(by+1)*th;left=bx*tw;ya,yb=max(y0,top),min(y0+height,top+th);xa,xb=max(x0,left),min(x0+width,left+tw)
     v[ya-y0:yb-y0,xa-x0:xb-x0]=block[::-1][ya-top:yb-top,xa-left:xb-left]
   return band,v
  with ThreadPoolExecutor(max_workers=12) as pool:
   for band,v in pool.map(band_extract,range(64)):out[:,:,band]=v
  return out

def deq(raw):
 valid=np.all(raw!=-128,axis=-1);x=((raw.astype(np.float64)/127.5)**2)*np.sign(raw);x[~valid]=np.nan;norm=np.linalg.norm(x[valid],axis=-1);assert len(norm) and norm.min()>.99 and norm.max()<1.01,(norm.min(),norm.max());return x,valid,norm

def extract(row):
 name=f"{row['site']}-{row['year']}";dest=D/(name+'.npz');meta=D/(name+'.json')
 if dest.exists() and meta.exists():
  x=json.loads(meta.read_text());assert sha(dest.read_bytes())==x['npz_sha256'];refresh_manifest();return x
 url=row['path'].replace('s3://us-west-2.opendata.source.coop/','https://s3.us-west-2.amazonaws.com/us-west-2.opendata.source.coop/');vrt_url=url[:-5]+'.vrt';vrt=fetch(vrt_url);(D/(name+'.vrt')).write_bytes(vrt);xml=ET.fromstring(vrt);gt=[float(x) for x in xml.findtext('GeoTransform').split(',')];assert len(xml.findall('VRTRasterBand'))==64
 reader=TIFF(url);t=reader.ifds[0];transform=t[34264].reshape(4,4);west,south,east,north=map(float,(row['utm_west'],row['utm_south'],row['utm_east'],row['utm_north']))
 assert np.allclose(gt,[west,10,0,north,0,-10],rtol=0,atol=1e-8);assert transform[0,0]==transform[1,1]==10 and np.allclose(transform[:2,3],[west,south],rtol=0,atol=1e-8)
 col=math.floor((row['easting']-west)/10);bottom_row=math.floor((row['northing']-south)/10);top_row=8191-bottom_row
 # independent VRT georeferencing exactly agrees with the raw-row reversal
 assert top_row==math.floor((gt[3]-row['northing'])/10)
 raw=reader.window(0,col-32,top_row-32,64,64);emb,valid,norm=deq(raw)
 macro_raw=reader.window(5,0,0,256,256);macro,macro_valid,macro_norm=deq(macro_raw)
 # Adjacent-pixel dot products test local continuity, not land-cover class.
 unit=emb/np.linalg.norm(emb,axis=-1,keepdims=True);adj=np.r_[np.sum(unit[:-1]*unit[1:],axis=-1).ravel(),np.sum(unit[:,:-1]*unit[:,1:],axis=-1).ravel()];adj=adj[np.isfinite(adj)]
 np.savez_compressed(dest,station_raw=raw,station_embedding=emb.astype('f4'),station_valid=valid,macro_raw=macro_raw,macro_embedding=macro.astype('f4'),macro_valid=macro_valid)
 info=dict(site=row['site'],year=row['year'],lat=row['lat'],lon=row['lon'],epsg=row['epsg'],easting=row['easting'],northing=row['northing'],tiff_url=url,vrt_url=vrt_url,vrt_sha256=sha(vrt),index_row=row,indexing=dict(col=col,raw_bottom_up_row=bottom_row,vrt_top_down_row=top_row,station_top_left_col=col-32,station_top_left_row=top_row-32,pixel_size_m=10,window_size=[64,64],raw_transform=transform.tolist(),vrt_geotransform=gt,macro_IFD=5,macro_pixel_size_m=320,macro_shape=[256,256]),pct_valid=100*valid.mean(),L2_norm=dict(min=float(norm.min()),max=float(norm.max()),mean=float(norm.mean())),macro_L2_norm=dict(min=float(macro_norm.min()),max=float(macro_norm.max())),adjacent_pixel_cosine_mean=float(adj.mean()),http_ranges=reader.ranges,npz_sha256=sha(dest.read_bytes()),npz_file=dest.name,attribution='The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind.',license='CC-BY-4.0',landcover_status='Station-centered pixels are not certified cropland. Macro covers81.92km and supports an explicitly unclassified5km landscape ring; land-cover audit is separate.',mirror_status='Source Cooperative copy is not officially supported by Google; mirror README advertises2017–2025 while catalog consulted advertises2017–2024.')
 meta.write_text(json.dumps(info,indent=2));refresh_manifest();print(name,'valid',info['pct_valid'],'L2',info['L2_norm'],flush=True);return info
MANIFEST_LOCK=threading.Lock()
def refresh_manifest():
 with MANIFEST_LOCK:
  expected={(s,y) for s in SITES for y in range(2017,2026)};complete=[];seen=set()
  for meta in sorted(D.glob('*-20??.json')):
   x=json.loads(meta.read_text());k=(x['site'],int(x['year']));assert k in expected and k not in seen;seen.add(k);assert sha((D/x['npz_file']).read_bytes())==x['npz_sha256'];complete.append(dict(metadata=meta.name,metadata_sha256=sha(meta.read_bytes()),npz=x['npz_file'],npz_sha256=x['npz_sha256']))
  doc=dict(status='complete' if seen==expected else 'partial',expected_site_years=45,extracted_site_years=len(seen),expected_keys=sorted(expected),missing_keys=sorted(expected-seen),files=complete,index_sha256=sha((D/'site-year-index-v1.json').read_bytes()),attribution='The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind.',license='CC-BY-4.0')
  temp=D/'manifest-alphaearth-v1.tmp';temp.write_text(json.dumps(doc,indent=2));temp.replace(D/'manifest-alphaearth-v1.json')
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--index-only',action='store_true');parser.add_argument('--site');parser.add_argument('--year',type=int);parser.add_argument('--workers',type=int,default=1);args=parser.parse_args()
 INDEX_SIZE=int(requests.head(BASE+'aef_index.csv',timeout=30).headers['Content-Length']);f=D/'site-year-index-v1.json';rows=json.loads(f.read_text()) if f.exists() else index_sites()
 if not args.index_only:
  selected=[r for r in rows if (args.site is None or r['site']==args.site) and (args.year is None or int(r['year'])==args.year)]
  with ThreadPoolExecutor(max_workers=args.workers) as pool:results=list(pool.map(extract,selected))
  refresh_manifest()
