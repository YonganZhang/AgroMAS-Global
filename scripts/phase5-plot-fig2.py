"""NL references, paired uncertainty, stage redistribution and global ablations."""
import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('common',Path(__file__).with_name('phase5-plot-common.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
import numpy as np
import matplotlib.pyplot as plt
if __name__=='__main__':
 d,a,contrasts=c.data();fig,axs=plt.subplots(2,2,figsize=(7.2,7.2));fig.subplots_adjust(left=.12,right=.98,bottom=.12,top=.96,wspace=.32,hspace=.32)
 arms=['N2-PA-calendar','Phase4-Forest-transfer','PPO-structured-shared','PPO-raw-shared','A4'];labels=['N2 calendar','Phase4 transfer','PPO structured','PPO raw','Full'];reg=c.REGIONS[0]
 ax=axs[0,0]
 for role,offset,marker in [('Held-Out',-.12,'o'),('Public-Reused-Benchmark',.12,'s')]:
  q=c.main_context(a,role);q=q[q.region_id==reg]
  for i,arm in enumerate(arms):
   values=q[q.arm==arm].joint.to_numpy();ix=np.random.default_rng(20261115).integers(0,len(values),size=(5000,len(values)));ci=np.quantile(values[ix].mean(1),[.025,.975])*100;mean=values.mean()*100
   if c.VARIANT=='b':ax.bar(i+offset,mean,width=.22,color=c.COLORS[i],alpha=.35 if role=='Public-Reused-Benchmark' else .65)
   if c.VARIANT=='c':ax.vlines(i+offset,0,mean,color=c.COLORS[i],lw=.6)
   ax.errorbar(i+offset,mean,yerr=[[mean-ci[0]],[ci[1]-mean]],fmt=marker,color=c.COLORS[i],ecolor='black' if c.VARIANT=='b' else c.COLORS[i],capsize=2,ms=4,label=('Independent n=5' if role=='Held-Out' else 'Public reused n=7') if i==0 else None)
 ax.set(xticks=range(5),xticklabels=labels,ylabel='Joint compliance (%)',ylim=(-5,105));ax.tick_params(axis='x',rotation=35);ax.legend(frameon=False,loc='upper left');c.clean(ax,'a')
 ax=axs[0,1]
 for i,arm in enumerate(arms[:-1]):
  x=c.contrast(contrasts,reg,arm,'partial_profit');mean=x['difference'];lo,hi=x['CI95']
  if c.VARIANT=='b':ax.barh(i,mean,color=c.COLORS[i],height=.55,alpha=.6)
  ax.errorbar(mean,i,xerr=[[mean-lo],[hi-mean]],fmt='o',color=c.COLORS[i],capsize=3)
 ax.axvline(0,color='black',ls='--',lw=.6);ax.set(yticks=range(4),yticklabels=labels[:-1],xlabel='Full - reference partial profit (EUR/ha)');c.clean(ax,'b')
 ax=axs[1,0];arms2=['A0','A1','A2','A3','A4'];q=c.main_context(d);q=q[q.region_id==reg];bottom=np.zeros(5)
 doses=np.array([[q[q.arm==arm][f'stage{stage}_dose'].iloc[0] for stage in (1,2,3)] for arm in arms2])
 if c.VARIANT=='c':
  ax.imshow(doses,aspect='auto',cmap=c.C,vmin=0,vmax=max(100,doses.max()))
  for i in range(5):
   for j in range(3):ax.text(j,i,f'{doses[i,j]:.0f}',ha='center',va='center').set_gid('heatmap_cell')
  ax.set(xticks=range(3),xticklabels=['Stage 1','Stage 2','Stage 3'],yticks=range(5),yticklabels=arms2,xlabel='Mean topdress N (kg/ha)')
 else:
  for stage,color in zip((1,2,3),c.COLORS[:3]):
   values=doses[:,stage-1]
   ax.bar(np.arange(5)+(stage-2)*.23 if c.VARIANT=='b' else np.arange(5),values,bottom=None if c.VARIANT=='b' else bottom,color=color,width=.22 if c.VARIANT=='b' else .65,label=f'Stage {stage}');bottom+=values
  ax.set(xticks=range(5),xticklabels=arms2,ylabel='Mean topdress N (kg/ha)');ax.set_ylim(0,120 if c.VARIANT=='b' else 250);ax.legend(frameon=False,ncol=3,loc='upper center')
 c.clean(ax,'c')
 ax=axs[1,1];arms3=['A0','A1','A2','A2-oracle','A3','A4'];q=c.main_context(d)
 ablation_colors=['#162830','#5E9680','#5882A6','#8E7CA6','#D67E7D','#B8525A']
 matrix=np.array([q[q.arm==arm].set_index('region_id').loc[c.REGIONS].joint.to_numpy()*100 for arm in arms3]).T
 if c.VARIANT=='b':
  shown=np.vstack([matrix,matrix.mean(0)]);ax.imshow(shown,aspect='auto',cmap=c.C,vmin=0,vmax=100)
  for i in range(6):
   for j in range(6):ax.text(j,i,f'{shown[i,j]:.0f}',ha='center',va='center').set_gid('heatmap_cell')
  ax.set(xticks=range(6),xticklabels=['A0','A1','A2','Oracle','A3','A4'],yticks=range(6),yticklabels=c.SHORT+['Macro'],xlabel='Joint compliance (%)')
 else:
  if c.VARIANT=='c':
   for i,values in enumerate(matrix):ax.plot(range(6),values,'o-',color=c.COLORS[i],ms=3,lw=.7,label=c.SHORT[i])
   ax.plot(range(6),matrix.mean(0),'D--',color='black',ms=4,lw=1,label='Macro');ax.legend(frameon=False,ncol=3,loc='upper left')
  else:
   for j,region in enumerate(c.SHORT):
    ax.plot(np.arange(6)+np.linspace(-.32,.32,5)[j],matrix[j],linestyle='none',marker=['o','s','^','v','P'][j],mfc='none',mec=c.COLORS[j],ms=3,label=region)
   ax.plot(range(6),matrix.mean(0),'D',linestyle='none',color='black',ms=3.5,label='Macro');ax.legend(frameon=False,ncol=3,loc='upper left')
  ax.set(xticks=range(6),xticklabels=['A0','A1','A2','Oracle','A3','A4'],ylabel='Regional joint compliance (%)',ylim=(-5,105))
 c.clean(ax,'d')
 c.save(fig,'fig2_netherlands_home_turf_and_ablation')
