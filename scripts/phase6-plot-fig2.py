"""Three genuinely different data-driven Fig2 composite layouts."""
from pathlib import Path
import importlib.util,numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Patch
from matplotlib.lines import Line2D
from scipy.stats import gaussian_kde
s=importlib.util.spec_from_file_location('common',Path(__file__).with_name('phase6-plot-common.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
STEM='fig2_netherlands_home_turf_and_ablation'
def ladder(ax,d,variant):
 arms=['Phase5-A0','Phase5-A1','Phase5-A2','Phase5-A2-oracle','Phase5-A3','Phase5-A4','Phase6-Full']
 labels=['A0','A1','A2','Oracle','A3','v4','v6'];colors=[c.COL[i] for i in (0,4,3,5,1,3,8)];colors[5]='#C8D1D7';colors[6]='#DE9698'
 values=[100*c.macro(d[d.policy==p],'joint') for p in arms];rng=np.random.default_rng(c.BOOTSTRAP_SEED)
 for i,(policy,value,color) in enumerate(zip(arms,values,colors)):
  matrix=d[d.policy==policy].pivot(index='year',columns='region_id',values='joint').to_numpy();bootstrap=[]
  while len(bootstrap)<5000:
   sample=matrix[rng.integers(len(matrix),size=len(matrix))]
   if not np.any(np.all(np.isnan(sample),axis=0)):bootstrap.append(np.nanmean(sample,axis=0).mean()*100)
  low,high=np.quantile(bootstrap,[.025,.975]);hatch='////' if i==6 else None
  if variant=='C':
   ax.barh(i,value,color=color,edgecolor='#A6424C' if i==6 else '#000000',linewidth=.5,hatch=hatch,linestyle='--' if i==5 else '-')
   ax.errorbar(value,i,xerr=[[max(0,value-low)],[max(0,high-value)]],fmt='none',ecolor='#000000',capsize=2,lw=.65,zorder=5)
  else:
   if i==3:ax.scatter(i,value,marker='D',s=22,facecolor=color,edgecolor='#000000',zorder=6)
   else:
    previous=0 if i==0 else values[2] if i==4 else values[i-1]
    ax.bar(i,abs(value-previous),bottom=min(previous,value),color=color,edgecolor='#A6424C' if i==6 else '#000000',linewidth=.6,hatch=hatch,linestyle='--' if i==5 else '-')
    ax.plot([i-.38,i+.38],[value,value],color='#000000',lw=.65)
   if i==6:ax.plot([i,i],[low,high],color='white',lw=2.4,zorder=4)
   ax.errorbar(i,value,yerr=[[max(0,value-low)],[max(0,high-value)]],fmt='none',ecolor='#000000',capsize=2,lw=.65,zorder=5)
   if i in (0,1,4,5):ax.plot([i+.38,i+.62],[value,value],ls='--',color='#000000',lw=.5)
 # Oracle remains in its comparison slot but is never a parent of A3.
 if variant=='C':
  ax.set_yticks(range(7),labels);ax.invert_yaxis();ax.set_xlabel('Joint compliance (%)');ax.set_xlim(-.8,44)
  for y in (2.5,3.5):ax.axhline(y,color='#000000',lw=.45,ls='--')
  ax.annotate('',xy=(38,6),xytext=(38,5),arrowprops=dict(arrowstyle='<->',lw=.65,color='#000000'));ax.text(40,5.5,f'{values[6]-values[5]:+.1f} pp',rotation=90,ha='center',va='center')
 else:
  ax.set_xticks(range(7),labels);ax.set_ylabel('Joint compliance (%)');ax.set_ylim(-.8,max(values)+18)
  ax.annotate('',xy=(6,max(values)+12),xytext=(5,max(values)+12),arrowprops=dict(arrowstyle='<->',lw=.65,color='#000000'));ax.text(5.5,max(values)+14,f'{values[6]-values[5]:+.1f} pp',ha='center',va='bottom')
 ax.grid(axis='x' if variant=='C' else 'y',color='#C8D1D7',lw=.3,alpha=.5)

def dose(ax,d,all_data,variant):
 names=['DVS-N2','N2-PA-calendar','Phase4-Forest-transfer','PPO-v4-raw-shared','PPO-v4-structured-shared','PPO-v6-structured-book','Phase5-A4','Phase6-Full']
 labels=['DVS N2','Calendar','Forest','PPO raw v4','PPO str v4','PPO book v6','Full v4','Full v6'];nl=d[d.region=='NL'];public=all_data[(all_data.region=='NL')&(all_data.cohort=='Public-Reused')&(all_data.climate=='Historical')&(all_data.cap==40)&(all_data.price_multiplier==1)&(all_data.subsidy==0)]
 width_mm=ax.get_position().width*ax.figure.get_figwidth()*25.4;first=1+9/width_mm;second=1+24/width_mm
 for i,name in enumerate(names):
  group=nl[nl.policy==name];left=0
  for stage,color in zip((1,2,3),[c.COL[2],c.COL[4],c.COL[8]]):
   value=group[f'dose{stage}'].mean();ax.barh(i,value,left=left,color=color,edgecolor='white',height=.66,lw=.4)
   if value>=25:ax.text(left+value/2,i,f'{value:.0f}',ha='center',va='center',color=c.contrast_text(color))
   left+=value
  ax.barh(i,max(0,220-left),left=left,color='#C8D1D7',edgecolor='white',height=.66,lw=.4)
  pub=public[public.policy==name].joint.mean()*100
  ax.text(first,i,f'{group.joint.mean()*100:.0f}   {pub:.0f}',transform=ax.get_yaxis_transform(),va='center',ha='right',clip_on=False)
  ax.text(second,i,f'{group.partial_profit.mean():.0f}',transform=ax.get_yaxis_transform(),va='center',ha='right',clip_on=False)
 for line in (2.5,5.5):ax.axhline(line,color='#000000',lw=.45,ls=(0,(3,3)))
 for label,y in (('I',1),('II',4),('III',6.5)):ax.text(-16/width_mm,y,label,transform=ax.get_yaxis_transform(),ha='right',va='center')
 ax.text(first,1.035,'Joint %\nHeld Pub',transform=ax.transAxes,ha='right',va='bottom');ax.text(second,1.035,'Profit\nEUR per ha',transform=ax.transAxes,ha='right',va='bottom')
 ax.set_yticks(range(8),labels);ax.invert_yaxis();ax.set_xlim(0,220);ax.set_xticks([0,100,220]);ax.set_xlabel('Stage fertilizer N (kg per ha)')
 ax.legend(handles=[Patch(facecolor=x,label=label) for x,label in zip([c.COL[2],c.COL[4],c.COL[8],'#C8D1D7'],['Stage 1','Stage 2','Stage 3','Unspent'])],ncol=4,loc='upper left',bbox_to_anchor=(-.02,-.30 if variant=='B' else -.14 if variant=='A' else -.24),frameon=False,handlelength=.8,handletextpad=.3,columnspacing=.6)

def phase(ax,d,variant):
 arms=['DVS-N2','Phase5-A4','Phase6-Full'];cols=[c.COL[2],c.COL[3],c.COL[9]];g=d[d.policy.isin(arms)];xmin=min(-10,g.surplus.min()*1.03);xmax=max(60,g.surplus.max()*1.03);ymax=max(1.2,g.NUE.max()*1.1)
 ax.axhspan(.9,ymax,color=c.COL[7],alpha=.25);ax.axhspan(0,.5,color='#C8D1D7',alpha=.35);ax.add_patch(Rectangle((40,.5),xmax-40,.4,facecolor=c.COL[3],edgecolor='none',alpha=.25));ax.add_patch(Rectangle((0,.5),40,.4,facecolor=c.COL[6],edgecolor=c.COL[4],ls='--',lw=.9,zorder=1));cent=[]
 for name,col,label in zip(arms,cols,['N2','Full v4','Full v6']):
  z=g[g.policy==name];ax.scatter(z.surplus,z.NUE,s=10,facecolor=col,edgecolor='white',lw=.2,alpha=.7,label=label,zorder=3);x,y=z.surplus.mean(),z.NUE.mean();cent.append((x,y));ax.scatter([x],[y],marker='D',s=30,facecolor='white',edgecolor=col,lw=1,zorder=5)
 for a,b in zip(cent[:-1],cent[1:]):ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',connectionstyle='arc3,rad=.22',color='#000000',lw=.75))
 ax.set_yscale('symlog',linthresh=1.2,linscale=1);ax.set_xlim(xmin,xmax);ax.set_ylim(0,ymax);ax.set_yticks([.5,.9,2,10,30]);ax.set_yticklabels(['0.5','0.9','2','10','30']);ax.set_xticks([-150,-75,0,40,120,200]);ax.set_xlabel('Native N surplus (kg per ha)');ax.set_ylabel('Native NUE');ax.text(1,.92,'Native\ncorridor',ha='left',va='bottom',fontsize=7,bbox=dict(facecolor='white',edgecolor='none',alpha=.7,pad=.5));handles,labels=ax.get_legend_handles_labels();handles.append(Line2D([],[],marker='D',ls='',markerfacecolor='white',markeredgecolor='#000000',label='Mean'));ax.legend(handles=handles,loc='upper right',frameon=False,handletextpad=.25,labelspacing=.2)
def barcode(ax,d,variant):
 pairs=c.pairs(d);pairs['dp']=pairs.partial_profit_a-pairs.partial_profit_b;pairs['dn']=pairs.fertN_a-pairs.fertN_b;names=['US','AU','NL','FR','CN','Macro'];ax.axvspan(0,max(1,pairs.dp.max()*1.15),color=c.COL[6],alpha=.4)
 width_mm=ax.get_position().width*ax.figure.get_figwidth()*25.4;first=1+8/width_mm;second=1+19/width_mm
 for i,name in enumerate(names):
  group=pairs if name=='Macro' else pairs[pairs.region==name];x=group.dp.to_numpy();weights=np.array([1/len(group[group.region==region]) for region in group.region]) if name=='Macro' else np.ones(len(group))
  order=np.argsort(x);cdf=(np.cumsum(weights[order])-.5*weights[order])/sum(weights);quant=np.interp([.05,.10,.25,.75,.90,.95],cdf,x[order]);mean=np.average(x,weights=weights);dn=np.average(group.dn,weights=weights)
  if variant=='B' and len(x)>2 and np.std(x)>1e-8:
   grid=np.linspace(x.min(),x.max(),180);density=gaussian_kde(x,weights=weights)(grid);height=.28*density/density.max();ax.fill_between(grid,i-height,i+height,color=c.COL[8],edgecolor=c.COL[9],alpha=.15,lw=.5)
  jitter=.12*np.sin(np.arange(len(x))*2.3999632297);sizes=5*weights/weights.mean();ax.scatter(x,i+jitter,s=sizes,facecolor=c.COL[1],edgecolor='white',lw=.15,alpha=.45,zorder=2)
  ax.plot([quant[0],quant[-1]],[i,i],color=c.COL[1],lw=.8);ax.plot([quant[2],quant[3]],[i,i],color=c.COL[8],lw=5,solid_capstyle='butt');ax.plot([quant[1],quant[1]],[i-.15,i+.15],color='#000000',lw=.7);ax.plot([quant[4],quant[4]],[i-.15,i+.15],color='#000000',lw=.7);ax.scatter(mean,i,s=22,facecolor='white',edgecolor=c.COL[9],zorder=5)
  ax.text(first,i,f'{mean:+.0f}',transform=ax.get_yaxis_transform(),va='center',ha='right',clip_on=False);ax.text(second,i,'0' if abs(dn)<.5 else f'{dn:+.0f}',transform=ax.get_yaxis_transform(),va='center',ha='right',clip_on=False)
 ax.axvline(0,color='#000000',lw=.55,ls='--');ax.set_yticks(range(6),names);ax.invert_yaxis();ax.set_xlabel('Paired partial profit gain (EUR per ha)');ax.set_xticks([-50,0,100,200,300]);ax.set_xlim(min(-55,pairs.dp.min()*1.08),max(305,pairs.dp.max()*1.08))
 ax.text(first,1.025,'ΔProfit',transform=ax.transAxes,ha='right');ax.text(second,1.025,'ΔN',transform=ax.transAxes,ha='right')
 handles=[Line2D([],[],color=c.COL[1],lw=.8,label='5–95%'),Line2D([],[],color='#000000',marker='|',ls='',label='10–90%'),Line2D([],[],color=c.COL[8],lw=4,label='IQR'),Line2D([],[],color=c.COL[9],marker='o',markerfacecolor='white',ls='',label='Mean')]
 ax.legend(handles=handles,loc='upper left',bbox_to_anchor=(-.01,-.19 if variant=='A' else -.25),ncol=4,frameon=False,handlelength=.8,handletextpad=.25,columnspacing=.6)

def main():
 all_data=c.data();d=c.primary(all_data)
 for variant in 'ABC':
  if variant=='A':size=(183,150);boxes=[[.10,.61,.38,.30],[.64,.61,.185,.30],[.10,.13,.38,.35],[.60,.13,.25,.35]]
  elif variant=='B':size=(183,185);boxes=[[.10,.79,.78,.14],[.15,.49,.61,.19],[.10,.12,.38,.22],[.60,.12,.25,.22]]
  else:size=(246,145);boxes=[[.07,.15,.15,.74],[.36,.58,.18,.32],[.69,.58,.26,.32],[.35,.13,.50,.26]]
  fig=plt.figure(figsize=(size[0]/25.4,size[1]/25.4));axes=[c.axis(fig,box,l) for box,l in zip(boxes,'abcd')]
  ladder(axes[0],d,variant);dose(axes[1],d,all_data,variant);phase(axes[2],d,variant);barcode(axes[3],d,variant);c.save(fig,STEM,variant)
if __name__=='__main__':main()
