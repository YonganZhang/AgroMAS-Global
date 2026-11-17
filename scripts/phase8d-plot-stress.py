"""V11 main Fig. 5 (2x2 a-d: Pareto Profit x Compliance trajectory phase diagram in 5d) + Fig. S7."""
import runpy
from pathlib import Path
globals().update(runpy.run_path(str(Path(__file__).with_name('phase8d-plot-style.py'))))
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from scipy.interpolate import RectBivariateSpline

df=pd.read_csv(P/'phase8d-180cell-stress-surface.csv');canon=pd.read_csv(P/'phase8d-canonical90-stress-subset.csv')
keys=['region','climate','cap','price_multiplier','subsidy']
pp=df[(df.policy=='TreeMLP')&(df['mode']=='soft')&(df.track=='Sensorless')]
rr=df[(df.policy=='SensorlessPPO')&(df['mode']=='tree')&(df.track=='Sensorless')]
joined=pp.merge(rr,on=keys,suffixes=('_p','_r'));assert len(joined)==180
joined['delta']=100*(joined.joint_p-joined.joint_r)

fig=plt.figure(figsize=(14.4,9.6))
gs=fig.add_gridspec(2,2,width_ratios=[1.05,1.08],height_ratios=[1.0,1.0],hspace=.34,wspace=.28)

# Panel a: 2D Continuous Iso-Advantage Phase Contour (Cap 25-50 x Warming 0..+3.5C) + 12x3 Econ Glyphs
a=fig.add_subplot(gs[0,0])
caps=[25,35,40,50];temps=[0.0,1.8,3.5];econ_pairs=[(1,0),(2,0),(1,50)]
mean_grid=np.array([[joined[(joined.cap==cap)&(joined.climate==cl)].delta.mean() for cl in CL] for cap in caps])
spl=RectBivariateSpline(caps,temps,mean_grid,kx=2,ky=2)
Xc=np.linspace(25,50,120);Yt=np.linspace(0.0,3.5,120);Xg,Yg=np.meshgrid(Xc,Yt)
Zg=spl(Xc,Yt).T
norm_a=TwoSlopeNorm(vmin=-6,vcenter=0,vmax=8.5)
cf=a.contourf(Xg,Yg,Zg,levels=np.linspace(-6,8.5,24),cmap=HEATMAP_CMAP,norm=norm_a,alpha=.72,zorder=0)
cs0=a.contour(Xg,Yg,Zg,levels=[0.0],colors=['black'],linestyles=['--'],linewidths=1.25,zorder=2)
cs=a.contour(Xg,Yg,Zg,levels=[-2,2,4,5],colors=['#4A5860'],linewidths=.75,zorder=2)
a.clabel(cs0,fmt='0 pp',fontsize=7.0,inline=True);a.clabel(cs,fmt='%+.0f pp',fontsize=6.6,inline=True)
for cap in caps:
 for cl,dt in zip(CL,temps):
  for dx,dy,(pr,sb) in zip([-.90,0.0,.90],[0.0,.14,0.0],econ_pairs):
   dm=joined[(joined.cap==cap)&(joined.climate==cl)&(joined.price_multiplier==pr)&(joined.subsidy==sb)].delta.mean()
   col_g=HEATMAP_CMAP(norm_a(np.clip(dm,-6,8.5)))
   a.scatter(cap+dx,dt+dy,s=68,color=col_g,edgecolor='black',lw=.55,zorder=4)
for cap in caps:a.plot([cap,cap],[0.0,3.5],color='#7E8D96',ls=':',lw=.55,zorder=1)
for dt in temps:a.plot([25,50],[dt,dt],color='#7E8D96',ls=':',lw=.55,zorder=1)
a.add_patch(plt.Rectangle((25,0.0),25,3.5,fill=False,ec='#4A5860',lw=.75,zorder=3))
a.annotate('cap 40 ridge (+5.2..+5.6 pp)\nAU +45 · US +14 · NL +13',xy=(40,2.6),xytext=(31.5,2.95),
           arrowprops=dict(arrowstyle='->',color='black',lw=.85),fontsize=6.8,
           bbox={'facecolor':'#FFFDF9','edgecolor':PINK_MAIN,'lw':.6,'alpha':.92,'pad':2.0},zorder=5)
a.set(xticks=caps,yticks=temps,yticklabels=['0.0 (Hist)','+1.8°C','+3.5°C'],xlabel='Surplus cap S_N (kg N/ha)',ylabel='Climate warming ΔT (°C)',xlim=(23.2,51.8),ylim=(-.65,3.92))
for sp in a.spines.values():sp.set_visible(True);sp.set_linewidth(.90);sp.set_edgecolor('#000000')
a.tick_params(labelsize=7.8);panel(a,'a')
cb=fig.colorbar(cf,ax=a,fraction=.042,pad=.03);cb.set_label('Soft − PPO (pp)',fontsize=8);cb.ax.tick_params(labelsize=7.5)
for sp in cb.ax.spines.values():sp.set_visible(True);sp.set_linewidth(.85);sp.set_edgecolor('#000000')
a.text(.02,.03,'3-dot cluster: left 1×·0 · top 2×·0 · right 1×·50 EUR',transform=a.transAxes,fontsize=6.4,bbox={'facecolor':'white','edgecolor':'none','alpha':.90,'pad':1.5})

# Panel b: Surplus-Cap Warming Crossover + Embedded 45-Cell Win/Tie/Loss Stacked Bars
b=fig.add_subplot(gs[0,1]);counts=[]
for cl,col in zip(CL,CL_COLS):
 means=[joined[(joined.cap==cap)&(joined.climate==cl)].delta.mean() for cap in caps]
 b.plot(range(4),means,'o-',color=col,label=CLABS[CL.index(cl)],ms=4.8,lw=1.65)
 drops=np.array([[joined[(joined.cap==cap)&(joined.climate==cl)&(joined.region!=reg)].delta.mean() for cap in caps] for reg in REG])
 b.fill_between(range(4),drops.min(axis=0),drops.max(axis=0),color=col,alpha=.14)
b.axhline(0,color='black',ls='--',lw=.65);b.axhline(-7.2,color='#D0D7DE',lw=.65)
for i,cap in enumerate(caps):
 v=joined[joined.cap==cap].delta;n=[int((v>1e-9).sum()),int((abs(v)<=1e-9).sum()),int((v<-1e-9).sum())];counts.append(n)
 left=i-.38
 for num,col in zip(n,[TEAL_SAGE,'#D5DCE2',PINK_MAIN]):
  w=.76*num/45.0;b.barh(-9.3,w,left=left,color=col,height=1.7)
  if num>=7:contrast_label(b,left+w/2,-9.3,str(num),col,ha='center',va='center',fontsize=6.8)
  left+=w
b.set(xticks=range(4),xticklabels=[str(c) for c in caps],xlabel='Surplus cap (kg N/ha) · embedded 45-cell W/T/L',ylabel='Soft − PPO (pp)',xlim=(-.55,3.55),ylim=(-11.2,12.8))
b.tick_params(labelsize=8);grid(b,'y');panel(b,'b')
b.legend(handles=[Line2D([],[],color=co,marker='o',lw=1.5,label=lab) for co,lab in zip(CL_COLS,CLABS)]+
                 [Patch(color=TEAL_SAGE,label='Win'),Patch(color='#D5DCE2',label='Tie'),Patch(color=PINK_MAIN,label='Loss')],
         fontsize=6.5,ncol=3,loc='lower left',bbox_to_anchor=(0,1.02))

# Panel c: Leave-One-Region-Out (LORO-Region) Sensitivity Dumbbells
c=fig.add_subplot(gs[1,0])
regs=[(CL[0],1,40),(CL[0],2,40),(CL[1],2,40),(CL[2],2,40),(CL[2],2,25)];hl=[];los=[];his=[]
for i,(cl,price,cap) in enumerate(regs):
 z=joined[(joined.climate==cl)&(joined.price_multiplier==price)&(joined.cap==cap)&(joined.subsidy==0)];assert len(z)==5
 v=z.delta.mean();drop=[z[z.region!=r].delta.mean() for r in REG]
 los.append(min(drop));his.append(max(drop))
 c.plot([min(drop),max(drop)],[i,i],color=GREY,lw=4.2,zorder=2);c.scatter(drop,np.full(5,i),c=REG_COLS,s=30,alpha=.90,zorder=3)
 c.scatter(v,i,marker='D',color='black',s=36,zorder=4);hl.append(f'{CLABS[CL.index(cl)]} {price}× cap{cap}')
c.fill_betweenx(range(5),los,his,color='#EDF2F7',alpha=.75,zorder=1)
c.axvline(0,color='black',ls='--',lw=.65);c.set(yticks=range(5),yticklabels=hl,xlabel='Soft − PPO (pp)',ylim=(4.6,-.6));c.tick_params(labelsize=8);grid(c,'x');panel(c,'c')
c.legend(handles=[Line2D([],[],marker='D',ls='',color='black',label='All five')]+[Line2D([],[],marker='o',ls='',color=co,label='Drop '+r) for r,co in zip(RN,REG_COLS)],fontsize=6.6,ncol=2,loc='lower right')

# Panel d: Multi-Objective Pareto Phase-Plane Trajectory (Partial Profit x Joint Compliance, 0 -> 200 EUR/ha) + Native N Loss Inset
d=fig.add_subplot(gs[1,1]);subs=[0,50,100,150,200];sizes=[34,50,68,88,110];nlosses=[]
for cl,col,lab in zip(CL,CL_COLS,CLABS):
 qs=[query(climate=cl,subsidy=s) for s in subs]
 px=[val(q,'partial_profit') for q in qs];jy=[val(q,'joint') for q in qs]
 nlosses.append(float(np.mean([val(q,'Native_N_loss') for q in qs])))
 d.plot(px,jy,color=col,lw=1.4,alpha=.75,zorder=2)
 for k in range(len(subs)-1):
  d.annotate('',xy=(px[k+1],jy[k+1]),xytext=(px[k],jy[k]),arrowprops=dict(arrowstyle='->',color=col,lw=1.2,shrinkA=4,shrinkB=5),zorder=3)
 d.scatter(px,jy,s=sizes,color=col,edgecolor='white',lw=.6,zorder=4,label=lab)
 d.text(px[0]-5,jy[0]+.45,'0',ha='right',fontsize=6.6)
 if cl==CL[1]:d.text(px[-1],jy[-1]-.95,'200',ha='center',va='top',fontsize=6.6)
 else:d.text(px[-1]+5,jy[-1]+.2,'200',ha='left',fontsize=6.6)
 q_ne=query(policy='remove-econ',climate=cl,subsidy=50)
 if q_ne:
  d.scatter(val(q_ne,'partial_profit'),val(q_ne,'joint'),marker='x',s=55,color=col,lw=1.5,zorder=5,label='No-econ (50 EUR)')
# Highlight +1.8C Pareto peak at 100 EUR/ha
q_pk=query(climate=CL[1],subsidy=100)
d.scatter(val(q_pk,'partial_profit'),val(q_pk,'joint'),marker='*',s=130,color=ORANGE,edgecolor='black',lw=.5,zorder=6)
d.annotate('Peak 100 EUR\n(34.4%, 773)',xy=(val(q_pk,'partial_profit'),val(q_pk,'joint')),xytext=(715,35.2),
           arrowprops=dict(arrowstyle='->',color='black',lw=.75),fontsize=6.6,ha='center',zorder=6)
d.set(xlim=(615,960),ylim=(19.2,37.8),xlabel='Partial profit (EUR/ha · size scales with subsidy 0→200)',ylabel='Joint compliance (%)')
d.tick_params(labelsize=7.8);grid(d,'both');panel(d,'d')
d.legend(fontsize=6.5,ncol=4,loc='lower left',bbox_to_anchor=(0,1.02))

# Compact Native N loss inset in upper-right empty whitespace (above Historical 21-25% compliance)
di=d.inset_axes([.63,.65,.34,.27],facecolor='#FAFBFD')
for idx,(nl_v,col,lab) in enumerate(zip(nlosses,CL_COLS,['Hist','+1.8°C','+3.5°C'])):
 di.barh(idx,nl_v,color=col,height=.52,edgecolor='black',lw=.35)
 di.text(nl_v+.5,idx,f'{nl_v:.1f}',va='center',fontsize=6.5)
di.set(xlim=(0,30),yticks=range(3),yticklabels=['Hist','+1.8°C','+3.5°C'],ylim=(2.6,-.6),xlabel='Native N loss (kg/ha)')
di.tick_params(labelsize=6.6);di.xaxis.label.set_size(6.8);grid(di,'x')

fig.subplots_adjust(left=.06,right=.94,top=.91,bottom=.08)
save(fig,'fig4-factorial-stress','V11 main Fig. 5 (2x2 a-d). Replaces repeated subsidy lines in 5d with a directed Multi-Objective Pareto Phase-Plane (Profit x Compliance, 0->200 EUR/ha) and upper-right invariant Native N loss inset. Cap W/T/L '+str(counts)+'.')

# Supplementary Fig. S7: Complete 180-cell Soft - PPO (pp) matrix across 3 climates with 90 canonical black outlines
fig_s7=plt.figure(figsize=(12.6,4.2))
gs7=fig_s7.add_gridspec(1,4,width_ratios=[1,1,1,.035],wspace=.20)
conditions=[(p,s,c) for p,s in [(1,0),(2,0),(1,50)] for c in [25,35,40,50]]
outline_count=0
for j,cl in enumerate(CL):
 ax=fig_s7.add_subplot(gs7[j])
 arr=np.array([[joined[(joined.region==r)&(joined.climate==cl)&(joined.cap==cap)&(joined.price_multiplier==price)&(joined.subsidy==sub)].iloc[0]['delta'] for price,sub,cap in conditions] for r in REG])
 im=ax.imshow(arr,cmap=HEATMAP_CMAP,vmin=-50,vmax=50,aspect='auto')
 for i in range(5):
  for k,(price,sub,cap) in enumerate(conditions):
   contrast_label(ax,k,i,f'{arr[i,k]:.0f}',im.cmap(im.norm(arr[i,k])),ha='center',va='center',fontsize=7.2,zorder=5)
   ax.add_patch(plt.Rectangle((k-.5,i-.5),1,1,fill=False,ec='#586670',lw=.55,zorder=2))
   if len(canon[(canon.region==REG[i])&(canon.climate==cl)&(canon.cap==cap)&(canon.price_multiplier==price)&(canon.subsidy==sub)]):
    ax.add_patch(plt.Rectangle((k-.5,i-.5),1,1,fill=False,ec='black',lw=.95,zorder=3));outline_count+=1
 ax.set(xlim=(-.5,11.5),ylim=(4.5,-.5),yticks=range(5),yticklabels=RN if j==0 else [],xticks=range(12),xticklabels=[str(c) for p,s,c in conditions],xlabel='Surplus cap (kg N/ha) · N price ×')
 ax.tick_params(labelsize=7.8)
 if j>0:ax.tick_params(labelleft=False)
 for sp in ax.spines.values():sp.set_visible(True);sp.set_linewidth(.95);sp.set_edgecolor('#000000')
 for k in [3.5,7.5]:ax.axvline(k,color='black',lw=1.25,zorder=4)
 for k,lab in zip([1.5,5.5,9.5],['1×·0 EUR','2×·0 EUR','1×·50 EUR']):ax.text(k,1.03,lab,transform=ax.get_xaxis_transform(),ha='center',fontsize=7.5)
 ax.text(.5,1.15,CLABS[j],transform=ax.transAxes,ha='center',fontsize=9.5);panel(ax,'abc'[j])
assert outline_count==90
ca=fig_s7.add_subplot(gs7[3]);cb=fig_s7.colorbar(im,cax=ca);cb.set_label('Soft − PPO (pp)',fontsize=9);cb.ax.tick_params(labelsize=8)
for sp in ca.spines.values():sp.set_visible(True);sp.set_linewidth(.95);sp.set_edgecolor('#000000')
fig_s7.subplots_adjust(left=.05,right=.94,top=.80,bottom=.16)
save(fig_s7,'figs7-stress-180cell-grid','V11 Supplementary Fig. S7 (compact 1x3 appendix). Complete 180-cell Soft-PPO stress advantage surface across 3 climates with 90 canonical black continuity outlines.')
