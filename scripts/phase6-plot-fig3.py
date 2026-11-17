"""Stress heatmaps, subsidy fans and TRAIN-frozen feasible-rule diagnostics."""
from pathlib import Path
import importlib.util,json,numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
s=importlib.util.spec_from_file_location('common',Path(__file__).with_name('phase6-plot-common.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
STEM='fig3_cross_system_cmip6_urban_policy_matrix';CLIM=['Historical','idealized_mid','idealized_high'];SIG=[0,50,100,150,200];CLABEL={'Historical':'Hist','idealized_mid':'Warm 1','idealized_high':'Warm 2'}
def heat(ax,d,price,cmap,norm,transpose=False):
 matrix=np.array([[100*c.macro(d[(d.climate==cl)&(d.cap==cap)&(d.price_multiplier==price)&(d.subsidy==sigma)],'joint') for sigma in SIG] for cl in CLIM for cap in (25,35,50)])
 shown=matrix.T if transpose else matrix;ax.imshow(shown,aspect='auto',cmap=cmap,norm=norm,interpolation='none')
 for (i,j),value in np.ndenumerate(shown):ax.text(j,i,f'{value:.0f}',ha='center',va='center',color=c.contrast_text(cmap(norm(value))))
 rows=[f'{cl}  {cap}' for cl in ['Hist','Warm 1','Warm 2'] for cap in (25,35,50)]
 if transpose:ax.set_xticks(range(9),rows,rotation=45,ha='right');ax.set_yticks(range(5),SIG);ax.set_ylabel('Subsidy (EUR ha⁻¹)');ax.set_xlabel('Climate and cap (kg N per ha)');ax.xaxis.set_label_position('top')
 else:ax.set_yticks(range(9),rows);ax.set_xticks(range(5),SIG);ax.set_xlabel('Subsidy (EUR ha⁻¹)');ax.set_ylabel('Climate and cap (kg N per ha)')
 for y in (2.5,5.5):
  if transpose:ax.axvline(y,color='white',lw=1.8)
  else:ax.axhline(y,color='white',lw=1.8)
 ax.text(1.01,1.025,f'{price:g}× N price',transform=ax.transAxes,ha='right',va='bottom')
def comparison(d):
 full=d[d.policy=='Phase6-Full'];refs=d[(d.subsidy==0)&(((d.region=='NL')&(d.policy=='N2-PA-calendar'))|((d.region!='NL')&(d.policy=='DVS-N2')))];keys=['region_id','region','year','climate','cohort','cap','price_multiplier'];return full.merge(refs[keys+['partial_profit','joint']],on=keys,suffixes=('_a','_b'))
def fan(ax,d,variant):
 pairs=comparison(d[d.cap.isin((25,35,50))]);pairs['gain']=pairs.partial_profit_a-pairs.partial_profit_b;colors=[c.COL[i] for i in (0,0,4,4,9,9)];endpoint=[]
 for (climate,price),color in zip([(cl,p) for cl in CLIM for p in (1,2)],colors):
  q=pairs[(pairs.climate==climate)&(pairs.price_multiplier==price)];table=q.groupby(['region_id','cap','subsidy']).gain.mean().unstack('subsidy').reindex(columns=SIG);values=table.to_numpy();assert values.shape==(15,5) and np.isfinite(values).all(), 'Incomplete stress fan population';mean=values.mean(0);lo,hi=np.quantile(values,[.25,.75],axis=0)
  for trajectory in values:ax.plot(SIG,trajectory,color=color,alpha=.18,lw=.45)
  ax.fill_between(SIG,lo,hi,color=color,alpha=.15,lw=0);ax.plot(SIG,mean,color='white',lw=3.1);ax.plot(SIG,mean,color=color,lw=1.7,ls='-' if price==1 else '--',label=f'{CLABEL[climate]} {price:g}×');endpoint.append((color,values[:,-1],table.index))
 ax.axhline(0,color='#000000',lw=.55,ls='--');ax.set_xlabel('Green subsidy (EUR ha⁻¹)');ax.set_ylabel('Partial profit gain (EUR ha⁻¹)');ax.set_xticks(SIG);ax.legend(ncol=3,loc='upper left',frameon=False,columnspacing=.7,handlelength=1.1,handletextpad=.25)
 # Attached endpoint distribution keeps spread in the same physical unit.
 box=ax.get_position();strip=c.axis(ax.figure,[box.x1+.008,box.y0,.045,box.height]);strip.set_ylim(ax.get_ylim());strip.set_xticks([0,1,2],['25','35','50'],rotation=90);strip.tick_params(axis='y',labelleft=False);strip.set_xlabel('Cap',labelpad=1)
 for j,cap in enumerate((25,35,50)):
  vals=np.concatenate([v[[i for i,k in enumerate(index) if k[1]==cap]] for _,v,index in endpoint]);strip.plot([j,j],np.quantile(vals,[.05,.95]),color=c.COL[1],lw=.6);strip.plot([j,j],np.quantile(vals,[.25,.75]),color=c.COL[8],lw=3);strip.scatter(j,vals.mean(),s=13,facecolor='white',edgecolor=c.COL[9],zorder=4)
 # Joint-gain encoding is separate from profit axis, without mixed units.
 line=c.axis(ax.figure,[box.x0,box.y0-.11,box.width,.048]);line.set_xticks([]);line.set_yticks([0,20]);line.set_ylabel('ΔJoint\npp',rotation=0,labelpad=13,va='center')
 for (cl,price),color in zip([(cl,p) for cl in CLIM for p in (1,2)],colors):
  q=pairs[(pairs.climate==cl)&(pairs.price_multiplier==price)];v=q.assign(delta=100*(q.joint_a-q.joint_b)).groupby(['region_id','subsidy']).delta.mean().groupby('subsidy').mean().reindex(SIG);line.plot(SIG,v,color=color,lw=.8,ls='-' if price==1 else '--')
 line.axhline(0,color='#000000',lw=.4);line.set_xlim(ax.get_xlim());line.spines['bottom'].set_visible(False);line.set_ylim(0,23)
def dumbbell(ax,d,cmap,norm,variant):
 cmap,norm,_=c.palette.continuous_scale([0,20,40,60,80,100],anchors=c.ANCHORS,name='v6feasible',space='oklch')
 p=comparison(d);p['gain']=p.partial_profit_a-p.partial_profit_b;order=[(r,cl) for r in ('US','AU','NL','FR','CN') for cl in CLIM];active=json.loads((c.P/'ACTIVE_TRAIN_RUN_V6.json').read_text());freeze=json.loads((c.R/active['reports']/'green-subsidy-TRAIN-freeze-v6.json').read_text())['groups'];idmap=d.drop_duplicates('region').set_index('region').region_id.to_dict();box=ax.get_position();bubble=c.axis(ax.figure,[box.x1+.012,box.y0,.085,box.height]);bubble.set_xlim(-.5,2.5);bubble.set_xticks(range(3),['25','35','50']);bubble.set_xlabel('Cap');bubble.set_yticks([])
 for i,(region,climate) in enumerate(order):
  q=p[(p.region==region)&(p.climate==climate)&(p.cap==35)&(p.price_multiplier==1)];values=[q[q.subsidy==sigma].gain.mean() for sigma in (0,100)];ax.plot(values,[i,i],color=c.COL[3],lw=1.5);ax.scatter(values,[i,i],c=[c.COL[2],c.COL[9]],s=17,edgecolor='white',lw=.3,zorder=4)
  for j,cap in enumerate((25,35,50)):
   group=next(g for g in freeze if g['region_id']==idmap[region] and g['climate']==climate and g['cap']==cap and g['price_multiplier']==1);sigma=group['feasible_selected_subsidy']
   if sigma is None:bubble.text(j,i,'×',ha='center',va='center');continue
   rows=d[(d.region==region)&(d.climate==climate)&(d.cap==cap)&(d.price_multiplier==1)&(d.subsidy==sigma)&(d.policy=='Phase6-Full')];feasible=rows[rows.physically_feasible_in_grid==1]
   if feasible.empty:bubble.text(j,i,'×',ha='center',va='center');continue
   rate=100*feasible.joint.mean();bubble.scatter(j,i,s=max(1,rate*.55),c=[cmap(norm(rate))],edgecolors='#000000',lw=.3)
 height_mm=ax.figure.get_figheight()*25.4;bubble.text(.5,1+(12 if variant=='C' else 7)/(box.height*height_mm),'Feasible joint (%)\n1× N price, × none',transform=bubble.transAxes,ha='center',va='bottom');ax.text(.18 if variant in ('A','B') else 0,1.035,'1× N price and cap 35',transform=ax.transAxes,ha='left',va='bottom')
 handles=[bubble.scatter([],[],s=rate*.55,color=cmap(norm(rate)),edgecolors='#000000',lw=.3,label=f'{rate}%') for rate in (25,50,100)];bubble.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,1+2/(box.height*height_mm)),ncol=1 if variant=='C' else 3,frameon=False,handletextpad=.35,columnspacing=.9,labelspacing=.15,handlelength=.8,borderaxespad=0)
 for y in (5.5,8.5):ax.axhline(y,color='#000000',ls='--',lw=.4);bubble.axhline(y,color='#000000',ls='--',lw=.4)
 ax.set_yticks(range(15),[f'{r} {CLABEL[cl]}' for r,cl in order]);ax.set_ylim(14.7,-.7);bubble.set_ylim(ax.get_ylim());ax.axvline(0,color='#000000',lw=.45,ls='--');ax.set_xlabel('Partial profit gain (EUR ha⁻¹)');ax.legend(handles=[plt.Line2D([],[],marker='o',ls='',color=c.COL[2],label='Subsidy 0'),plt.Line2D([],[],marker='o',ls='',color=c.COL[9],label='Subsidy 100')],loc='upper left',bbox_to_anchor=(0,-.18),ncol=2,frameon=False,handletextpad=.2,columnspacing=.6)
def main():
 all_data=c.data();d=all_data[all_data.cohort=='Former-Held-Out'];full=d[(d.policy=='Phase6-Full')&(d.cap!=40)];vals=[100*c.macro(g,'joint') for _,g in full.groupby(['climate','cap','price_multiplier','subsidy'])];cmap,norm,bounds=c.scale(np.r_[0,vals])
 for variant in 'ABC':
  if variant=='A':size=(183,163);boxes=[[.12,.64,.32,.27],[.59,.64,.32,.27],[.12,.20,.33,.26],[.61,.16,.22,.34]];transpose=False
  elif variant=='B':size=(183,195);boxes=[[.12,.77,.75,.14],[.12,.50,.75,.16],[.12,.15,.33,.21],[.61,.08,.22,.28]];transpose=True
  else:size=(246,150);boxes=[[.10,.57,.27,.32],[.10,.14,.27,.30],[.47,.28,.215,.50],[.80,.20,.10,.64]];transpose=False
  fig=plt.figure(figsize=(size[0]/25.4,size[1]/25.4));axes=[c.axis(fig,b,l) for b,l in zip(boxes,'abcd')];heat(axes[0],full,1,cmap,norm,transpose);heat(axes[1],full,2,cmap,norm,transpose)
  a,b=axes[:2];mid=.5*(min(a.get_position().x0,b.get_position().x0)+max(a.get_position().x1,b.get_position().x1));width=.32 if variant=='A' else .35 if variant=='B' else .27;y=.565 if variant=='A' else .415 if variant=='B' else .058;cax=fig.add_axes([mid-width/2,y,width,.013]);bar=c.palette.smooth_colorbar(fig,cax,cmap,norm,bounds,labels=[f'{v:.1f}' if v else '0' for v in bounds],label='Macro joint compliance (%)',fontsize=7);bar.outline.set_edgecolor('#000000');assert abs(cax.get_position().x0+cax.get_position().width/2-mid)<1e-12
  fan(axes[2],d,variant);dumbbell(axes[3],d,cmap,norm,variant);
  if variant in ('A','B'):
   for text in fig.texts:
    if text.get_text()=='d':text.set_x(boxes[3][0]+.005)
  c.save(fig,STEM,variant)
if __name__=='__main__':main()
