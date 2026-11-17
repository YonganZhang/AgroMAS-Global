"""Three global flow, attribution and independently closed N-ledger composites."""
from pathlib import Path
import importlib.util,json,numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch,Rectangle,Patch
from matplotlib.path import Path as MPath
s=importlib.util.spec_from_file_location('common',Path(__file__).with_name('phase6-plot-common.py'));c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
STEM='fig4_global_5region_comparison_and_attribution';ORDER=['US','AU','NL','FR','CN'];FAM=['climate','surplus-filter','soil-mining-guard','core-state','economics'];LABEL=['Climate','Cap','NUE','State','Econ']
def regime(r):
 if r.joint:return 0
 if r.NUE>.9:return 1
 if r.NUE<.5:return 3
 return 2

def flow(ax,d,variant):
 names=['DVS-N2','Phase5-A4','Phase6-Full'];colors=[c.COL[i] for i in (4,8,2,5)];table=[]
 for name in names:
  g=d[d.policy==name].sort_values(['region_id','year']);assert len(g)==52;table.append(np.array([regime(r) for _,r in g.iterrows()]))
 counts=[np.bincount(x,minlength=4) for x in table];starts=[];gap=4
 for j in range(3):
  bottom=0;locations=[]
  for k,n in enumerate(counts[j]):
   locations.append(bottom);ax.add_patch(Rectangle((j-.035,bottom),.07,n,facecolor=colors[k],edgecolor='#000000',lw=.4));ax.text(j+.06,bottom+max(n,.1)/2,f'{n}  {100*n/52:.0f}%',ha='left',va='center');bottom+=n+gap
  starts.append(locations)
 for j in (0,1):
  outgoing=np.array(starts[j],float);incoming=np.array(starts[j+1],float)
  for a in range(4):
   for b in range(4):
    n=int(np.sum((table[j]==a)&(table[j+1]==b)))
    if not n:continue
    y0=outgoing[a];y1=incoming[b];x0=j+.035;x1=j+1-.035;v=[(x0,y0),(x0+.45,y0),(x1-.45,y1),(x1,y1),(x1,y1+n),(x1-.45,y1+n),(x0+.45,y0+n),(x0,y0+n),(x0,y0)];codes=[MPath.MOVETO]+[MPath.CURVE4]*3+[MPath.LINETO]+[MPath.CURVE4]*3+[MPath.CLOSEPOLY];ax.add_patch(PathPatch(MPath(v,codes),facecolor=colors[a],edgecolor='none',alpha=.43));outgoing[a]+=n;incoming[b]+=n
 ax.set_xlim(-.1,2.35);ax.set_ylim(0,52+3*gap);ax.invert_yaxis();ax.set_yticks([]);ax.set_xticks([0,1,2],['DVS N2','Full v4','Full v6']);ax.spines[:].set_visible(False);ax.tick_params(length=0);ax.legend(handles=[Patch(facecolor=color,label=l) for color,l in zip(colors,['Corridor','High NUE','Surplus','Low NUE'])],ncol=4,loc='lower center',bbox_to_anchor=(.48,-.18 if variant=='C' else -.37),frameon=False,columnspacing=1,handlelength=1)
def ranges(ax,d,variant):
 width_mm=ax.get_position().width*ax.figure.get_figwidth()*25.4;first=1+14/width_mm;second=1+34/width_mm
 def signed(v):return '0.0' if round(float(v),1)==0 else f'{v:+.1f}'
 def decimal(v):return '0.0' if round(float(v),1)==0 else f'{v:.1f}'
 stats=json.loads((c.P/'benchmark-statistics-v6.json').read_text());refs=['DVS-N2','PPO-v6-structured-book'];colors=[c.COL[2],c.COL[9]]
 for j,(reference,col) in enumerate(zip(refs,colors)):
  p=c.pairs(d,reference);p['delta']=p.partial_profit_a-p.partial_profit_b
  for i,region in enumerate(ORDER+['Macro']):
   q=p if region=='Macro' else p[p.region==region];x=q.delta.to_numpy();y=i+(j-.5)*.27;lo,lq,med,hq,hi=np.quantile(x,[0,.25,.5,.75,1]);
   if variant=='B' and len(x)>1:
    parts=ax.violinplot(x,positions=[y],vert=False,widths=.24,showextrema=False)
    for body in parts['bodies']:body.set_facecolor(col);body.set_alpha(.18)
   ax.plot([lo,hi],[y,y],color=col,lw=.6);ax.plot([lq,hq],[y,y],color=col,lw=3);ax.scatter(med,y,marker='D',s=14,facecolor='white',edgecolor=col,lw=.65,zorder=4)
   if variant=='C':ax.scatter(x,np.full(len(x),y),s=4,facecolor=col,alpha=.35,edgecolors='none')
 for i,region in enumerate(ORDER+['Macro']):
  contrast=next(x for x in stats['contrasts'] if x['reference']=='PPO-v6-structured-book' and x['metric']=='joint');profit=next(x for x in stats['contrasts'] if x['reference']=='PPO-v6-structured-book' and x['metric']=='partial_profit')
  if region=='Macro':v=contrast['macro_equal_region_mean']*100;ci=np.array(contrast['year_cluster_CI95'])*100;pval=profit['macro_equal_region_mean'];pci=profit['year_cluster_CI95']
  else:
   rid=d[d.region==region].region_id.iloc[0];z=next(x for x in contrast['regions'] if x['region_id']==rid);v=z['mean']*100;ci=np.array(z['CI95'])*100;pz=next(x for x in profit['regions'] if x['region_id']==rid);pval=pz['mean'];pci=pz['CI95']
  ax.text(first,i,f'{signed(v)}\n[{decimal(ci[0])}, {decimal(ci[1])}]',transform=ax.get_yaxis_transform(),va='center',ha='right');ax.text(second,i,f'{signed(pval)}\n[{decimal(pci[0])}, {decimal(pci[1])}]',transform=ax.get_yaxis_transform(),va='center',ha='right')
 for y in (1.5,2.5,4.5):ax.axhline(y,color='#000000',ls='--',lw=.4)
 ax.axvline(0,color='#000000',ls='--',lw=.5);ax.set_yticks(range(6),ORDER+['Macro']);ax.invert_yaxis();ax.set_xlabel('Paired profit gain (EUR ha⁻¹)');ax.text(first,1.025,'ΔJoint (pp)\nvs PPO v6',transform=ax.transAxes,ha='right');ax.text(second,1.025,'ΔProfit\nEUR per ha\nvs PPO v6',transform=ax.transAxes,ha='right');ax.legend(handles=[plt.Line2D([],[],color=col,lw=2,label=l) for col,l in zip(colors,['N2','PPO v6'])],loc='lower left',bbox_to_anchor=(0,1.035),frameon=False,ncol=2,handlelength=1,columnspacing=.8)
def attribution(ax,d,variant):
 box=ax.get_position();ax.set_position([box.x0,box.y0,box.width*.47,box.height]);profit=c.axis(ax.figure,[box.x0+box.width*.57,box.y0,box.width*.43,box.height]);colors=[c.COL[i] for i in (0,2,8,5,4)]
 for j,(family,color) in enumerate(zip(FAM,colors)):
  p=c.pairs(d,'Phase6-LOAO-'+family)
  for i,r in enumerate(ORDER):
   q=p[p.region==r];y=i+(j-2)*.145;delta=100*(q.joint_a-q.joint_b).mean();dp=(q.partial_profit_a-q.partial_profit_b).mean();
   if variant=='B':ax.plot([0,delta],[y,y],color=color,lw=.8);ax.scatter(delta,y,s=11 if abs(delta)>1e-9 else 0,facecolor=color,edgecolor='white',lw=.2)
   else:ax.barh(y,delta,height=.13,color=color,edgecolor='white',lw=.15)
   profit.barh(y,dp,height=.13,color=color,edgecolor='white',lw=.15)
 net=c.pairs(d,'Phase5-A4')
 for i,region in enumerate(ORDER):
  q=net[net.region==region];profit.text(1.07,i,f'{100*(q.joint_a-q.joint_b).mean():+.0f}',transform=profit.get_yaxis_transform(),va='center')
 profit.text(1.07,1.025,'Net ΔJ',transform=profit.transAxes)
 for a in (ax,profit):a.axvline(0,color='#000000',lw=.5);a.set_ylim(4.55,-.55);a.grid(axis='x',color='#C8D1D7',lw=.3)
 ax.set_yticks(range(5),ORDER);profit.set_yticks([]);ax.set_xticks([-10,0,20,40]);profit.set_xticks([-75,-50,-25,0]);ax.set_xlabel('ΔJoint (pp)');profit.set_xlabel('ΔProfit (EUR ha⁻¹)');ax.legend(handles=[Patch(facecolor=x,label=l) for x,l in zip(colors,LABEL)],ncol=5,loc='upper left',bbox_to_anchor=(-.2,-.15 if variant=='B' else -.24),frameon=False,columnspacing=.7,handlelength=.9,handletextpad=.3)
def ledger(ax,d):
 colors=[c.COL[i] for i in (4,2,8,5)];maxres=0;width_mm=ax.get_position().width*ax.figure.get_figwidth()*25.4;first=1+7/width_mm;second=1+22/width_mm
 for i,region in enumerate(ORDER):
  for j,policy in enumerate(('DVS-N2','Phase6-Full')):
   q=d[(d.region==region)&(d.policy==policy)];grain=q.grainN.mean();loss=q.stock_native_published_leaching_plus_denitrification_kg_ha.mean();upper=q.stock_upper_boundary_export_not_in_published_loss_kg_ha.mean();other=(q.stock_native_soil_crop_uptake_N_kg_ha-q.grainN+q.stock_final_soil_N_kg_ha-q.stock_initial_soil_N_kg_ha-q.stock_native_deposition_N_kg_ha).mean();values=[grain,loss,upper,other];positive=negative=0.;y=i+(j-.5)*.48
   for k,(value,col) in enumerate(zip(values,colors)):
    left=positive if value>=0 else negative;ax.barh(y,value,left=left,height=.36,color=col,edgecolor='#A6424C' if k==2 else 'white',linewidth=.3,hatch='////' if k==2 else None)
    if value>=0:positive+=value
    else:negative+=value
   residual=q.stock_soil_N_mass_balance_residual_kg_ha.abs().max();maxres=max(maxres,residual);assert np.isclose(sum(values),q.fertN.mean(),atol=1e-9);ax.text(first,y,f'{q.fertN.mean():.0f}',transform=ax.get_yaxis_transform(),va='center',ha='right');ax.text(second,y,f'{residual:.1e}',transform=ax.get_yaxis_transform(),va='center',ha='right')
   if i==0:ax.text(.02,y,'N2' if j==0 else 'Full v6',transform=ax.get_yaxis_transform(),ha='left',va='center',bbox=dict(facecolor='white',edgecolor='none',alpha=.8,pad=.1))
 ax.axvline(0,color='#000000',lw=.4);ax.set_yticks(range(5),ORDER);ax.set_ylim(4.6,-.6);ax.set_xticks([-100,0,100,200,300]);ax.set_xlabel('Native N ledger terms (kg ha⁻¹)');ax.text(first,1.025,'Fert N',transform=ax.transAxes,ha='right');ax.text(second,1.025,'|N residual|',transform=ax.transAxes,ha='right');ax.legend(handles=[Patch(facecolor=x,label=l,hatch='////' if i==2 else None) for i,(x,l) in enumerate(zip(colors,['Grain','Published loss','Upper export','Other crop and stock']))],loc='upper left',bbox_to_anchor=(-.1,-.24),ncol=2,frameon=False,columnspacing=.8,handlelength=1)
def main():
 d=c.primary(c.data())
 for variant in 'ABC':
  if variant=='A':size=(183,180);boxes=[[.10,.73,.80,.19],[.12,.40,.62,.22],[.12,.13,.36,.17],[.64,.13,.18,.17]]
  elif variant=='B':size=(183,210);boxes=[[.12,.71,.76,.20],[.12,.365,.27,.21],[.64,.365,.27,.21],[.12,.12,.67,.16]]
  else:size=(246,158);boxes=[[.08,.52,.47,.37],[.64,.56,.18,.29],[.08,.15,.48,.20],[.64,.17,.20,.24]]
  fig=plt.figure(figsize=(size[0]/25.4,size[1]/25.4));axes=[c.axis(fig,b,l) for b,l in zip(boxes,'abcd')];flow(axes[0],d,variant);ranges(axes[1],d,variant);attribution(axes[2],d,variant);ledger(axes[3],d);c.save(fig,STEM,variant)
if __name__=='__main__':main()
