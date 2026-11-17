"""Descriptive, basis-dependent channel clusters and unvalidated pixel-probe projections."""
from pathlib import Path
import json,importlib.util,numpy as np,pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
R=Path(__file__).resolve().parents[1];P=R/'reports/phase7';D=R/'data/phase7-alphaearth-v1';OUT=P/'spatial-projections-v7';OUT.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('decode',R/'scripts/phase7-analyze-decoding.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
if __name__=='__main__':
 aef=pd.read_csv(P/'station-mean-64d-v7.csv');physical=pd.read_csv(P/'physical-targets-v7.csv');f=np.load(R/'models/phase7/descriptive-linear-probes-v7.npz');axes=[f'A{j:02}' for j in range(64)];values=aef[axes].to_numpy();corr=np.corrcoef(values.T);adj=abs(corr)>=.7;np.fill_diagonal(adj,False);n,labels=connected_components(csr_matrix(adj),directed=False)
 clusters=[dict(cluster=int(k),channels=[axes[j] for j in np.flatnonzero(labels==k)]) for k in range(n)];(P/'sparse-channel-correlation-clusters-v7.json').write_text(json.dumps(dict(threshold_abs_r=.7,cluster_count=n,clusters=clusters,scope='Descriptive correlations among45 site-year means; basis-dependent and spatially confounded, not independent mechanistic factors'),indent=2))
 mean=aef.groupby('region')[axes].mean();unit=mean.to_numpy();unit=unit/np.linalg.norm(unit,axis=1,keepdims=True);cross=unit@unit.T;cosine=json.loads((P/'cosine-stability-v7.json').read_text());diagonal={r['region']:r['within_site_interannual_cosine'] for r in cosine}
 for i,region in enumerate(mean.index):cross[i,i]=diagonal[region]
 (P/'regional-fingerprint-and-cosine-v7.json').write_text(json.dumps(dict(regions=mean.index.tolist(),fingerprint=mean.to_numpy().tolist(),cosine_matrix=cross.tolist(),diagonal='Mean interannual unit-normalized cosine within a region',offdiagonal='Cosine between regional nine-year mean vectors',attribution_scope='All64 coordinates jointly encode the representation; channel order is descriptive'),indent=2))
 metrics=[];target_indices=[0,4]
 for row in aef.itertuples():
  meta=json.loads((D/f'{row.region}-{row.embedding_year}.json').read_text());a=np.load(D/meta['npz_file']);base=physical[(physical.region==row.region)&(physical.year==row.embedding_year)][m.BASE].to_numpy()[0];saved={}
  for name in ['station','macro']:
   emb=a[name+'_embedding'];valid=a[name+'_valid'];x=np.c_[np.repeat(base[None],valid.sum(),axis=0),emb[valid]];z=(x-f['Xmean'])/f['Xscale'];pred=(z@f['coef'].T+f['intercept'])*f['Yscale']+f['Ymean'];maps=np.full((*valid.shape,2),np.nan,dtype='f4');maps[valid]=pred[:,target_indices];saved[name+'_predictions']=maps
   mask=valid
   if name=='macro':
    yy,xx=np.indices(valid.shape);gt=meta['indexing']['vrt_geotransform'];east=gt[0]+320*(xx+.5);north=gt[3]-320*(yy+.5);ring=(np.hypot(east-meta['easting'],north-meta['northing'])<=5000);saved['macro_ring_5km']=ring;mask=valid&ring
   for j,target in enumerate(['mineralization','feasible_fraction']):
    v=maps[:,:,j][mask];train=physical[physical.year.between(2017,2025)][target].to_numpy();meanv=float(np.mean(v));metrics.append(dict(region=row.region,year=int(row.embedding_year),scale='10m_station640m' if name=='station' else '320m_landscape5km',target=target,pixels=len(v),mean=meanv,IQR=np.quantile(v,[.25,.75]).tolist(),CV=float(np.std(v)/abs(meanv)) if abs(meanv)>1e-12 else None,min=float(v.min()),max=float(v.max()),fraction_outside_training_target_range=float(np.mean((v<train.min())|(v>train.max()))),unvalidated_spatial_projection=True))
  np.savez_compressed(OUT/f'{row.region}-{row.embedding_year}.npz',**saved)
 # Agricultural windows are a separate, predeclared sensitivity, never replacements.
 ag=json.loads((P/'agricultural-patch-extraction-v7.json').read_text())
 for q in ag['site_years']:
  a=np.load(D/q['path']);emb=a['embedding'];valid=a['valid'];base=physical[(physical.region==q['site'])&(physical.year==int(q['year']))][m.BASE].to_numpy()[0];x=np.c_[np.repeat(base[None],valid.sum(),axis=0),emb[valid]];pred=(((x-f['Xmean'])/f['Xscale'])@f['coef'].T+f['intercept'])*f['Yscale']+f['Ymean'];maps=np.full((*valid.shape,2),np.nan,dtype='f4');maps[valid]=pred[:,target_indices];np.savez_compressed(OUT/f"{q['site']}-{q['year']}-agricultural.npz",predictions=maps)
  for j,target in enumerate(['mineralization','feasible_fraction']):
   v=maps[:,:,j][valid];metrics.append(dict(region=q['site'],year=int(q['year']),scale='10m_WorldCover_selected640m',target=target,pixels=len(v),mean=float(v.mean()),IQR=np.quantile(v,[.25,.75]).tolist(),CV=float(v.std()/abs(v.mean())) if abs(v.mean())>1e-12 else None,min=float(v.min()),max=float(v.max()),unvalidated_spatial_projection=True))
 (P/'spatial-dispersion-v7.json').write_text(json.dumps(dict(metrics=metrics,scope='Full-data linear probe projections, not observed soil maps or field-validated10m estimates. Macro ring is320m; station/agricultural windows10m. Crop identity and station-to-soil offsets audited separately. Correlated pixels are not independent validation cases.'),indent=2));print('Saved',len(metrics),'spatial dispersion records and',n,'descriptive channel clusters')
