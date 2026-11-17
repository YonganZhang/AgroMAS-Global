"""Five-region paired contrasts, functional attribution and boundary diagnostic."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('common',Path(__file__).with_name('phase5-plot-common.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
import numpy as np
import matplotlib.pyplot as plt
if __name__=='__main__':
 d,annual,contrasts=c.data();q=c.main_context(d);fig,axs=plt.subplots(2,2,figsize=(7.2,7.2));fig.subplots_adjust(left=.12,right=.97,bottom=.1,top=.96,wspace=.34,hspace=.30)
 for ax,metric,factor,label in [(axs[0,0],'joint',100,'a'),(axs[0,1],'partial_profit',1,'b')]:
  for control,off,color,name in [('DVS-N2',-.12,c.COLORS[0],'DVS N2'),('PPO-structured-shared',.12,c.COLORS[2],'PPO structured')]:
   for i,reg in enumerate(c.REGIONS):
    x=c.contrast(contrasts,reg,control,metric);v=x['difference']*factor;lo,hi=np.array(x['CI95'])*factor
    if c.VARIANT=='b':ax.barh(i+off,v,height=.22,color=color,alpha=.6)
    if c.VARIANT=='c':
     aa=c.main_context(annual);aa=aa[aa.region_id==reg];full=aa[aa.arm=='A4'].set_index('harvest_year')[metric];other=aa[aa.arm==control].set_index('harvest_year')[metric];differences=(full-other).to_numpy()*factor
     ax.scatter(differences,i+off+np.linspace(-.035,.035,len(differences)),s=7,facecolors='none',edgecolors=color,linewidths=.5)
    ax.errorbar(v,i+off,xerr=[[v-lo],[hi-v]],fmt='o',ms=4,color=color,capsize=2,label=name if i==0 else None)
  ax.axvline(0,color='black',ls='--',lw=.6);ax.set(yticks=range(5),yticklabels=c.SHORT,xlabel='Full - reference joint (percentage points)' if metric=='joint' else 'Full - reference partial profit (EUR/ha)');ax.invert_yaxis();ax.legend(frameon=False,loc='best');c.clean(ax,label)
 ax=axs[1,0];abl=['LOAO-climate','LOAO-eco','LOAO-core-state','A3'];matrix=[]
 for reg in c.REGIONS:
  values=q[q.region_id==reg].set_index('arm').joint;matrix.append([(values['A4']-values[a])*100 for a in abl])
 matrix=np.array(matrix);limit=max(5,float(abs(matrix).max()))
 if c.VARIANT=='c':
  for j,name in enumerate(['Climate','Eco','Core state','Economics']):ax.bar(np.arange(5)+(j-1.5)*.18,matrix[:,j],width=.17,color=c.COLORS[j],label=name)
  ax.axhline(0,color='black',lw=.6);ax.set(xticks=range(5),xticklabels=c.SHORT,ylabel='Joint change (percentage points)');ax.legend(frameon=False,ncol=2,loc='best')
 else:
  if c.VARIANT=='b':
   xx,yy=np.meshgrid(np.arange(4),np.arange(5));image=ax.scatter(xx,yy,s=180+620*abs(matrix)/limit,c=matrix,cmap=c.C,vmin=-limit,vmax=limit,edgecolors='none');ax.set_ylim(4.6,-.6);ax.set_xlim(-.5,3.5)
  else:image=ax.imshow(matrix,aspect='auto',cmap=c.C,vmin=-limit,vmax=limit)
  for i in range(5):
   for j in range(4):ax.text(j,i,f'{matrix[i,j]:.1f}',ha='center',va='center').set_gid('heatmap_cell')
  ax.set(xticks=range(4),xticklabels=['Climate','Eco','Core state','Economics'],yticks=range(5),yticklabels=c.SHORT,xlabel='Function removed');ax.tick_params(axis='x',rotation=25);cb=fig.colorbar(image,ax=ax,fraction=.04,pad=.02);cb.set_label('Joint change (percentage points)')
 c.clean(ax,'c')
 ax=axs[1,1]
 for arm,off,color,name in [('DVS-N2',-.12,c.COLORS[0],'DVS N2'),('A4',.12,c.COLORS[4],'Full')]:
  values=q[q.arm==arm].set_index('region_id').loc[c.REGIONS]['mean_upper_boundary_export_not_in_published_loss_kg_ha'].to_numpy()
  if c.VARIANT=='b':ax.bar(np.arange(5)+off,values,width=.22,color=color,label=name)
  elif c.VARIANT=='c':ax.plot(values,range(5),'o',color=color,ms=4,label=name)
  else:ax.plot(range(5),values,'o-',color=color,ms=4,label=name)
 if c.VARIANT=='c':
  v1=q[q.arm=='DVS-N2'].set_index('region_id').loc[c.REGIONS]['mean_upper_boundary_export_not_in_published_loss_kg_ha'].to_numpy();v2=q[q.arm=='A4'].set_index('region_id').loc[c.REGIONS]['mean_upper_boundary_export_not_in_published_loss_kg_ha'].to_numpy();ax.hlines(range(5),v1,v2,color='#C8D1D7',lw=1);ax.set(yticks=range(5),yticklabels=c.SHORT,xlabel='Native upper-boundary export (kg N/ha)')
 else:ax.set(xticks=range(5),xticklabels=c.SHORT,ylabel='Native upper-boundary export (kg N/ha)')
 ax.invert_yaxis() if c.VARIANT=='c' else None
 ax.legend(frameon=False);c.clean(ax,'d')
 c.save(fig,'fig4_global_5region_comparison_and_attribution')
