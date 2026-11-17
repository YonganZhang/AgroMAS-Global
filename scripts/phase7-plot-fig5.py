"""Three quantitative layouts separating spatial association from deployment failure."""
from pathlib import Path
import importlib.util,json,numpy as np,pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
R=Path(__file__).resolve().parents[1];P=R/'reports/phase7';s=importlib.util.spec_from_file_location('style',R/'scripts/phase7-plot-common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
STEM='fig5_alphaearth_64d_physical_decoding_and_field_bridge';ORDER=['US','AU','NL','FR','CN'];SHORT=lambda x:'NL' if 'netherlands' in x else 'AU' if 'australia' in x else 'US' if 'usa' in x else 'FR' if 'france' in x else 'CN'
STATS=json.loads((P/'decoding-nested-statistics-v7.json').read_text())['results'];BRIDGE=json.loads((P/'bridge-comparison-statistics-v7.json').read_text());FINGER=json.loads((P/'regional-fingerprint-and-cosine-v7.json').read_text());LOAD=pd.read_csv(P/'descriptive-channel-loadings-v7.csv')
TARGETS=['mineralization','upper_export','NLOSSCUM','harvest_grain_DM','corridor_width'];LABELS=['N mineralization','Upper export','NLOSSCUM','Grain dry mass','Corridor width']
def stat(target,model,scheme):return next(x for x in STATS if x['window']=='overlap2017_2025' and x['target']==target and x['model']==model and x['scheme']==scheme)
def colorbar(fig,axes,values,cmap,norm,bounds,y,width,label):
 left=min(a.get_position().x0 for a in axes);right=max(a.get_position().x1 for a in axes);mid=(left+right)/2;ax=fig.add_axes([mid-width/2,y,width,.012]);bar=c.palette.smooth_colorbar(fig,ax,cmap,norm,bounds,labels=[f'{v:.2f}' for v in bounds],label=label,fontsize=7);bar.outline.set_edgecolor('#000000');assert abs(ax.get_position().x0+ax.get_position().width/2-mid)<1e-12

def fingerprint(fig,box,cosbox,variant):
 ax=c.axis(fig,box,'a');cross=c.axis(fig,cosbox);load=LOAD[LOAD.target.isin(TARGETS)].pivot(index='channel',columns='target',values='standardized_loading')[TARGETS];groups=np.abs(load.to_numpy()).argmax(axis=1);ix=sorted(range(64),key=lambda i:(groups[i],-abs(load.iloc[i,groups[i]])));regions=FINGER['regions'];rid=[next(i for i,r in enumerate(regions) if SHORT(r)==code) for code in ORDER];data=np.array(FINGER['fingerprint'])[rid];data/=np.linalg.norm(data,axis=1,keepdims=True);data=data[:,ix];cm,no,bounds=c.scale(data);ax.imshow(data,cmap=cm,norm=no,aspect='auto',interpolation='none');ax.set_yticks(range(5),ORDER);ax.set_xticks([0,16,32,48,63],[f'A{i:02}' for i in np.array(ix)[[0,16,32,48,63]]]);ax.set_xlabel('Latent channels, ordered by probe loadings',labelpad=1)
 matrix=np.array(FINGER['cosine_matrix'])[np.ix_(rid,rid)];cm2,no2,b2=c.scale(matrix);cross.imshow(matrix,cmap=cm2,norm=no2,aspect='auto',interpolation='none');cross.set_xticks(range(5),ORDER);cross.set_yticks(range(5),ORDER)
 for (i,j),v in np.ndenumerate(matrix):cross.text(j,i,f'{v:.2f}',ha='center',va='center',color=c.c.contrast_text(cm2(no2(v))))
 y=box[1]-.068 if variant!='B' else box[1]-.055;colorbar(fig,[ax],data,cm,no,bounds,y,box[2]*.7,'Normalized signature');colorbar(fig,[cross],matrix,cm2,no2,b2,y,cosbox[2]*.96,'Cosine similarity')

def decoding(fig,box,variant):
 ax=c.axis(fig,box,'b');y=np.arange(5);colors=[c.COL[2],c.COL[9]]
 for k,model in enumerate(['Climate_coordinates','Same_year_retrospective']):
  values=[stat(t,model,'LOYO')['R2'] for t in TARGETS];ax.barh(y+(k-.5)*.28,values,height=.24,color=colors[k],label=['Weather + coordinates','Same-year AEF + baseline'][k]);
 ax.set_yticks(y,LABELS);ax.invert_yaxis();ax.set_xlim(0,1.02);ax.set_xticks([0,.5,1]);ax.set_xlabel('LOYO coefficient of determination',labelpad=1);ax.legend(ncol=1 if variant=='C' else 2,loc='lower left',bbox_to_anchor=(0,1.03),frameon=False,handlelength=.9,columnspacing=1,handletextpad=.3)
 # Fixed physical-mm columns retain readable tabular fields across layouts.
 b=ax.get_position();mm=b.width*fig.get_figwidth()*25.4;cols=[1+12/mm,1+27/mm,1+43/mm];heads=['LORO\nr / RMSE','Within\nregion R²','Year-null\nHolm p']
 for x,h in zip(cols,heads):ax.text(x,1.04,h,transform=ax.transAxes,ha='right',va='bottom')
 for i,t in enumerate(TARGETS):
  q=stat(t,'Same_year_retrospective','LORO');l=stat(t,'Same_year_retrospective','LOYO');vals=[f"{q['r']:.2f} / {q['RMSE']:.1f}",f"{l['within_region_R2']:.2f}",f"{l['permutations']['within_region']['Holm_p']:.2f}"]
  for x,v in zip(cols,vals):ax.text(x,i,v,transform=ax.get_yaxis_transform(),ha='right',va='center')

def bridge(fig,box,variant):
 ax=c.axis(fig,box,'c');regimes=['Weather_only','Static_soil','Satellite_bridge','Full_telemetry_reference','PPO_telemetry_reference'];labels=['Weather only','Static soil','SatBridge','Full telemetry','PPO telemetry'];rows=[next(x for x in BRIDGE['summary'] if x['window']=='prior2018_2026' and x['scheme']=='LOYO' and x['stratum']=='Explicit_combined_regions' and x['regime']==r) for r in regimes];rate=100*np.array([x['joint'] for x in rows]);colors=[c.COL[3],c.COL[4],c.COL[9],c.COL[2],c.COL[5]]
 ax.barh(range(5),rate,color=colors,height=.55);ax.scatter(rate,range(5),c=colors,s=12,edgecolors='#000000',lw=.3,zorder=4);ax.set_yticks(range(5),labels);ax.invert_yaxis();ax.set_xlim(-1.2,max(28,rate.max()+6));ax.set_xticks([0,10,20]);ax.set_xlabel('Joint compliance (%)',labelpad=2)
 mm=ax.get_position().width*fig.get_figwidth()*25.4;cols=[1+9/mm,1+20/mm,1+31/mm]
 for x,h in zip(cols,['Profit\nEUR/ha','N\nkg/ha','Gap\n%']):ax.text(x,1.035,h,transform=ax.transAxes,ha='right',va='bottom')
 den=rate[3]-rate[0]
 for i,row in enumerate(rows):
  ax.annotate(f'{rate[i]:.1f}',xy=(rate[i],i),xytext=(4,0),textcoords='offset points',va='center');vals=[f"{row['partial_profit']:.0f}",f"{row['applied_N']:.0f}",f'{100*(rate[i]-rate[0])/den:.1f}' if den else 'NA']
  for x,v in zip(cols,vals):ax.text(x,i,v,transform=ax.get_yaxis_transform(),ha='right',va='center')

def maps(fig,boxes,variant):
 sites=['australia_wa_perth','netherlands_lelystad','china_ncp_luancheng'];arrays=[np.load(P/f'spatial-projections-v7/{s}-2020.npz')['station_predictions'][:,:,0] for s in sites];cm,no,bounds=c.scale(np.concatenate([a.ravel() for a in arrays]));axes=[]
 for i,(site,box,a) in enumerate(zip(sites,boxes,arrays)):
  ax=c.axis(fig,box,'d' if i==0 else None);axes.append(ax);ax.imshow(a,extent=[-320,320,-320,320],origin='upper',cmap=cm,norm=no,interpolation='none',aspect='equal');ax.set_xticks([-300,0,300]);ax.set_yticks([0,300] if i==0 else []);ax.tick_params(pad=1);ax.text(.5,1.04,SHORT(site),transform=ax.transAxes,ha='center',va='bottom');ax.plot([-250,-50],[-240,-240],color='#000000',lw=1);ax.text(-150,-215,'200 m',ha='center',va='bottom');ax.annotate('N',xy=(240,250),xytext=(240,-40),ha='center',arrowprops=dict(arrowstyle='->',lw=.6,color='#000000'))
 y=min(b[1] for b in boxes)-(.055 if variant=='B' else .065);colorbar(fig,axes,np.ravel(arrays),cm,no,bounds,y,(boxes[-1][0]+boxes[-1][2]-boxes[0][0])*.9,'Descriptive N probe (kg per ha)')

def main():
 for variant in 'ABC':
  if variant=='A':size=(183,175);a=[.13,.79,.52,.12];cos=[.75,.79,.20,.12];b=[.17,.44,.43,.18];cc=[.15,.12,.18,.20];mapsbox=[[.62,.20,.098,.12],[.75,.20,.098,.12],[.88,.20,.098,.12]]
  elif variant=='B':size=(183,230);a=[.13,.82,.52,.10];cos=[.75,.82,.20,.10];b=[.17,.54,.43,.13];cc=[.32,.32,.30,.13];mapsbox=[[.16,.10,.17,.14],[.43,.10,.17,.14],[.70,.10,.17,.14]]
  else:size=(246,168);a=[.08,.72,.27,.17];cos=[.40,.72,.14,.17];b=[.64,.68,.16,.20];cc=[.10,.20,.20,.28];mapsbox=[[.60,.22,.105,.20],[.74,.22,.105,.20],[.88,.22,.105,.20]]
  fig=plt.figure(figsize=(size[0]/25.4,size[1]/25.4));fingerprint(fig,a,cos,variant);decoding(fig,b,variant);bridge(fig,cc,variant);maps(fig,mapsbox,variant)
  if variant=='B':
   for text in fig.texts:
    if text.get_text()=='c':text.set_x(.135)
  c.save(fig,STEM,variant)
if __name__=='__main__':main()
