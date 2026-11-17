"""Idealized climate/cap/price/subsidy matrix; no CMIP6 or legal claim."""
import importlib.util,json
from pathlib import Path
spec=importlib.util.spec_from_file_location('common',Path(__file__).with_name('phase5-plot-common.py'));c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
import numpy as np
import matplotlib.pyplot as plt
if __name__=='__main__':
 d,_,_=c.data();q=d[(d.role=='Held-Out')&(d.arm=='A4')&(d.zone!='standard_40')];climates=['Historical','idealized_mid','idealized_high'];zones=['strict_25','buffer_35','outer_50'];sigmas=[0,50,100,150,200]
 fig,axs=plt.subplots(2,2,figsize=(7.2,7.2));fig.subplots_adjust(left=.14,right=.90,bottom=.1,top=.96,wspace=.30,hspace=.34)
 for ax,price,label in zip(axs[0],(1,2),('a','b')):
  matrix=np.array([[q[(q.climate==climate)&(q.zone==zone)&(q.subsidy==s)&(q.price_multiplier==price)].joint.mean()*100 for s in sigmas] for climate in climates for zone in zones])
  rowlabels=[f'{cl}/{cap}' for cl in ('Hist.','+1.8C','+3.5C') for cap in (25,35,50)]
  if c.VARIANT=='b':
   xx,yy=np.meshgrid(np.arange(5),np.arange(9));image=ax.scatter(xx,yy,s=180+matrix*2,c=matrix,cmap=c.C,vmin=0,vmax=100,edgecolors='none');ax.set_ylim(8.6,-.6);ax.set_xlim(-.6,4.6)
  elif c.VARIANT=='c':image=ax.imshow(matrix.T,aspect='auto',vmin=0,vmax=100,cmap=c.C)
  else:image=ax.imshow(matrix,aspect='auto',vmin=0,vmax=100,cmap=c.C)
  for i in range(9):
   for j in range(5):ax.text(i if c.VARIANT=='c' else j,j if c.VARIANT=='c' else i,f'{matrix[i,j]:.0f}',ha='center',va='center',fontsize=7).set_gid('heatmap_cell')
  if c.VARIANT=='c':
   ax.set(yticks=range(5),yticklabels=sigmas,xticks=range(9),xticklabels=rowlabels,ylabel='Subsidy (EUR/ha)',xlabel=f'Climate/cap (kg N/ha), price {price}x');ax.tick_params(axis='x',rotation=60)
  else:
   ax.set(xticks=range(5),xticklabels=sigmas,yticks=range(9),yticklabels=rowlabels,xlabel='Subsidy (EUR/ha)',ylabel=f'Climate/cap (kg N/ha), price {price}x')
  c.clean(ax,label)
  if c.VARIANT=='a':
   for y in (2.5,5.5):ax.axhline(y,color='white',lw=1)
 # One compact shared scale placed in figure margin without enlarging panel gaps.
 position=axs[0,1].get_position();cax=fig.add_axes([.92,position.y0,.018,position.height]);cb=fig.colorbar(image,cax=cax);cb.set_label('Joint compliance (%)',labelpad=3)
 ax=axs[1,0];profitrows=[];profitlabels=[];reference=d[(d.role=='Held-Out')&(d.arm=='LOAO-eco')&(d.zone!='standard_40')&(d.subsidy==0)]
 for climate,color in zip(climates,c.COLORS[:3]):
  for price,style in ((1,'-'),(2,'--')):
   vals=[]
   for sigma in sigmas:
    a=q[(q.climate==climate)&(q.price_multiplier==price)&(q.subsidy==sigma)].set_index(['region_id','zone']).partial_profit
    b=reference[(reference.climate==climate)&(reference.price_multiplier==price)].set_index(['region_id','zone']).partial_profit
    vals.append(float((a-b).mean()))
   profitrows.append(vals);profitlabels.append(f'{dict(zip(climates,["Hist.","+1.8C","+3.5C"]))[climate]}/{price}x')
   if c.VARIANT!='c':ax.plot(sigmas,vals,style,color=color,marker='o',ms=3,label=f'{dict(zip(climates,["Hist.","+1.8 C","+3.5 C"]))[climate]} / {price}x')
 if c.VARIANT=='c':
  values=np.array(profitrows);limit=max(1,float(abs(values).max()));im=ax.imshow(values,aspect='auto',cmap=c.mpl.colors.LinearSegmentedColormap.from_list('profit-grey',['#F6F6F6','#C0C0C0']),vmin=0,vmax=limit)
  for i in range(6):
   for j in range(5):ax.text(j,i,f'{values[i,j]:.0f}',ha='center',va='center').set_gid('heatmap_cell')
  ax.set(xticks=range(5),xticklabels=sigmas,yticks=range(6),yticklabels=profitlabels,xlabel='Subsidy (EUR/ha)',ylabel='Climate/price; Full - no-eco')
  cbprofit=fig.colorbar(im,ax=ax,fraction=.035,pad=.03);cbprofit.set_label('Partial profit (EUR/ha)',labelpad=3)
 else:
  ax.axhline(0,color='black',lw=.6);ax.set(xlabel='Subsidy (EUR/ha)',ylabel='Full - no-eco partial profit (EUR/ha)');ax.set_ylim(min(0,float(np.min(profitrows))-5),max(0,float(np.max(profitrows)))*1.4+5);ax.legend(frameon=False,fontsize=7,ncol=2,loc='upper right')
 c.clean(ax,'c')
 ax=axs[1,1];groups=json.loads((c.P/'green-subsidy-TRAIN-freeze-v3.json').read_text())['groups'];selected=np.array([sum(x['region_id']==r and x['selected_subsidy'] is not None for x in groups) for r in c.REGIONS]);no=18-selected
 if c.VARIANT=='b':
  ax.barh(range(5),selected,color=c.COLORS[0],label='TRAIN selected');ax.barh(range(5),no,left=selected,color='#C8D1D7',label='TRAIN no solution');ax.set(yticks=range(5),yticklabels=c.SHORT,xlabel='Registered subsidy groups',xlim=(0,20))
 elif c.VARIANT=='c':
  ax.hlines(range(5),selected,no,color='#C8D1D7',lw=1);ax.plot(selected,range(5),'o',color=c.COLORS[0],label='TRAIN selected');ax.plot(no,range(5),'s',color=c.COLORS[4],label='TRAIN no solution');ax.set(yticks=range(5),yticklabels=c.SHORT,xlabel='Registered subsidy groups',xlim=(-1,20))
 else:
  ax.bar(range(5),selected,color=c.COLORS[0],label='TRAIN selected');ax.bar(range(5),no,bottom=selected,color='#C8D1D7',label='TRAIN no solution');ax.set(xticks=range(5),xticklabels=c.SHORT,ylabel='Registered subsidy groups',ylim=(0,20))
 if c.VARIANT=='a':ax.set_ylim(0,22)
 else:ax.set_ylim(-.5,5.3)
 ax.legend(frameon=False,loc='upper center',ncol=2);c.clean(ax,'d')
 c.save(fig,'fig3_cross_system_cmip6_urban_policy_matrix')
