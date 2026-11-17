"""V9 Supplementary Figs. S1, S3, S4: Compact 2-panel standalone Appendix figures replacing dense multi-panel grid."""
import runpy
from pathlib import Path
globals().update(runpy.run_path(str(Path(__file__).with_name('phase8d-plot-style.py'))))

pols=[('TreeMLP','soft','Sensorless'),('SensorlessPPO','tree','Sensorless'),('DVS-N2','tree','Full-Telemetry'),('LegacyV6Full','tree','Full-Telemetry')]
labels=['Soft','PPO','DVS · Full','Legacy · Full'];cols=[POLICY_COLORS[l] for l in labels]

# Supplementary Fig. S1: Climate warming & matched n=31 (a) + Eco-safety caps & realized S_N rainclouds (b)
fig1=plt.figure(figsize=(11.2,4.4))
gs1=fig1.add_gridspec(1,2,width_ratios=[1.05,1.0],wspace=.30)
ag=gs1[0].subgridspec(1,2,width_ratios=[1.25,1.0],wspace=.34)
a=fig1.add_subplot(ag[0]);ac=fig1.add_subplot(ag[1]);vv=[]
for spec,col,lab in zip(pols,cols,labels):
 v=[val(query(*spec,climate=cl)) for cl in CL];vv.append(v);a.plot(range(3),v,'o-',color=col,label=lab,ms=4.2,lw=1.45)
for v in vv[1:]:a.fill_between(range(3),vv[0],v,color=GREY,alpha=.16)
a.scatter(1,val(query(cap=25,climate=CL[1])),marker='D',color=PINK_MAIN,s=45,edgecolor='white',lw=.5,zorder=5)
a.annotate('cap25',(1,val(query(cap=25,climate=CL[1]))),xytext=(6,-13),textcoords='offset points',fontsize=7.5)
a.set(xticks=range(3),xticklabels=CLABS,ylabel='Joint compliance (%)',ylim=(10,40));a.tick_params(labelsize=7.8);grid(a,'y')
a.legend(fontsize=6.5,ncol=2,loc='upper left');a.text(.02,.03,'Fill: policy gaps',transform=a.transAxes,fontsize=6.2);panel(a,'a')

x=cases().merge(cases(policy='remove-climate'),on=['region','year'],suffixes=('_p','_r'));assert len(x)==31
v=x.groupby('region')[['joint_p','joint_r']].mean().mean()*100;w=x[['joint_p','joint_r']].mean()*100
for i,reg in enumerate(REG):
 z=x[x.region==reg];vv=100*z[['joint_p','joint_r']].mean();ac.barh(i-.15,vv.iloc[0],height=.26,color=PINK_MAIN);ac.barh(i+.15,vv.iloc[1],height=.26,color=SLATE_BLUE)
 ac.text(68,i,f'{vv.iloc[0]-vv.iloc[1]:+.1f}',va='center',fontsize=7.2)
ac.set(yticks=range(5),yticklabels=RN,xlim=(0,88),ylim=(6.7,-.7),xlabel='Joint (%) · Δpp');ac.tick_params(labelsize=7.8);grid(ac,'x')
ac.legend(handles=[plt.Rectangle((0,0),1,1,color=PINK_MAIN,label='Complete'),plt.Rectangle((0,0),1,1,color=SLATE_BLUE,label='No-climate')],fontsize=6.4,ncol=2,loc='lower left',bbox_to_anchor=(0,1.02))
ac.text(.02,.05,f'31 matched · 28 ties\nEq {v.iloc[0]:.1f}/{v.iloc[1]:.1f} · pool {w.iloc[0]:.1f}/{w.iloc[1]:.1f}',transform=ac.transAxes,fontsize=6.2)

bg=gs1[1].subgridspec(1,2,wspace=.40);b=fig1.add_subplot(bg[0]);bs=fig1.add_subplot(bg[1]);comb=[(25,'Full-Telemetry'),(35,'Sensorless'),(40,'Sensorless')];start=[];end=[]
for i,(cap,tr) in enumerate(comb):
 start.append(val(query('remove-eco',track=tr,cap=cap)));end.append(val(query(track=tr,cap=cap)))
 for j,(pol,col) in enumerate([('TreeMLP',PINK_MAIN),('remove-eco',SLATE_BLUE)]):
  z=cases(policy=pol,track=tr,cap=cap);y=i+(j-.5)*.30;raincloud(bs,z.S_N,y,col,vertical=False,width=.16);bs.plot([cap,cap],[i-.45,i+.45],color='black',ls='--',lw=.65)
for i,(u,vv) in enumerate(zip(start,end)):
 b.barh(i-.16,vv,height=.27,color=PINK_MAIN);b.barh(i+.16,u,height=.27,color=SLATE_BLUE);b.text(max(u,vv)+.6,i,f'{vv:.1f}/{u:.1f}',fontsize=6.6,va='center')
b.set(yticks=range(3),yticklabels=['25·Full','35·Sens','40·Sens'],xlabel='Joint compliance (%)',xlim=(0,42),ylim=(3.8,-.6));b.tick_params(labelsize=7.6);grid(b,'x')
b.text(.02,.08,f'50 · Sensor complete {val(query(cap=50)):.1f}%\nFull & no-eco: Not eval',transform=b.transAxes,fontsize=6.4);panel(b,'b')
bs.set(yticks=range(3),yticklabels=['25 Full','35 Sens','40 Sens'],xlabel='Realized S_N (kg N/ha)',ylim=(3.8,-.6));bs.tick_params(labelsize=7.6);grid(bs,'x')
bs.text(.02,.08,'Pink complete · blue no-eco',transform=bs.transAxes,fontsize=6.4)
fig1.subplots_adjust(left=.06,right=.98,bottom=.15,top=.87)
save(fig1,'figs2-g3-subsidy','V10 Supplementary Fig. S1 (compact 2-panel appendix). Warming trajectories and n=31 matched remove-climate comparison (a) paired with eco-safety cap compliance and S_N rainclouds (b).')

# Supplementary Fig. S3: 1x->2x price shock bars (a) + dual-axis subsidy curves under Historical/+1.8C (b)
fig3=plt.figure(figsize=(9.8,4.3))
gs3=fig3.add_gridspec(1,2,width_ratios=[1.05,1.0],wspace=.34)
c=fig3.add_subplot(gs3[0]);cs=fig3.add_subplot(gs3[1]);c2=cs.twinx()
for j,(idx,col) in enumerate([(0,PINK_MAIN),(1,SLATE_BLUE),(3,PLUM_SOFT)]):
 for k,price in enumerate([1,2]):
  bars=c.bar(np.arange(3)+(j*2+k-2.5)*.13,[val(query(*pols[idx],climate=cl,price_multiplier=price)) for cl in CL],.12,color=col,hatch=None if k==0 else '////',edgecolor='black',linewidth=.38,label=labels[idx]+f' {price}×')
  for rect in bars:c.text(rect.get_x()+rect.get_width()/2,rect.get_height()+.5,f'{rect.get_height():.1f}',rotation=90,ha='center',va='bottom',fontsize=6.2)
c.set(xlabel='Climate · N price 1× / 2×',xticks=range(3),xticklabels=CLABS,ylabel='Joint compliance (%)',ylim=(0,44));c.tick_params(labelsize=8);grid(c,'y')
c.legend(fontsize=6.5,ncol=3,loc='lower left',bbox_to_anchor=(0,1.02));c.text(.98,.95,'Bare 2× not evaluated',transform=c.transAxes,ha='right',va='top',fontsize=6.5);panel(c,'a')

for cl,col in zip(CL[:2],CL_COLS[:2]):
 qq=[query(climate=cl,subsidy=s) for s in [0,50,100,150,200]];assert all(qq)
 cs.plot([0,50,100,150,200],[val(q) for q in qq],'o-',color=col,label=CLABS[CL.index(cl)],ms=4.2,lw=1.5)
 c2.plot([0,50,100,150,200],[val(q,'partial_profit') for q in qq],'D--',color=col,ms=3.8,lw=1.25)
cs.set(xlabel='Subsidy (EUR/ha)',ylabel='Joint (%) · solid');c2.set_ylabel('Profit (EUR/ha) · dashed');c2.spines['right'].set_visible(True)
cs.legend(fontsize=7.2,ncol=2,loc='lower center',bbox_to_anchor=(.5,1.02));cs.tick_params(labelsize=8);c2.tick_params(labelsize=8);grid(cs,'y');panel(cs,'b')
fig3.subplots_adjust(left=.07,right=.92,bottom=.15,top=.84)
save(fig3,'figs3-price-subsidy','V9 Supplementary Fig. S3 (compact 2-panel appendix). Fertilizer 1x solid vs 2x hatched price-shock bars across warming (a) and dual-axis subsidy compliance/profit response (b).')

# Supplementary Fig. S4: 9-policy typology bootstrap 95% CIs & NUE lollipops (a) + 4-metric physical scorecard (b)
fig4=plt.figure(figsize=(10.2,4.6))
gs4=fig4.add_gridspec(1,2,width_ratios=[1.35,1.0],wspace=.20)
dg=gs4[0].subgridspec(1,2,width_ratios=[1.55,.95],wspace=.18)
d=fig4.add_subplot(dg[0]);dn=fig4.add_subplot(dg[1]);ds=fig4.add_subplot(gs4[1])
t_items=[
 ('TreeMLP','soft','I. MLP'),('TreeExtraTrees','soft','ExtraTrees'),('TreeWeather','soft','Weather'),('TreeLinear','soft','Linear'),
 ('TreeMLP','soft','II. Soft-Coupled'),('TreeMLP','tree','Tier2'),('TreeMLP','open-loop','Open-loop'),('TreeMLP','greedy-frozen','Greedy'),('TreeMLP','hard-bare-tier2','Archived bare')
]
cis={}
for i,(p,m,lab) in enumerate(t_items):
 q=query(p,m);v=val(q);lo,hi=bootstrap_joint(cases(p,m));cis[lab]=[float(lo),float(hi)]
 d.barh(i,v,color=PINK_MAIN if i in [0,4] else GREY,height=.56);d.errorbar(v,i,xerr=[[v-lo],[hi-v]],fmt='none',ecolor='black',capsize=2,lw=.75)
 d.text(51,i,f'{v:.1f}',fontsize=7.2,va='center');n=val(q,'NUE')
 dn.add_patch(plt.Rectangle((.5,i-.28),.4,.56,color='#FFF6EC',zorder=0));dn.plot([0,min(n,2)],[i,i],color=SLATE_BLUE,lw=3);dn.scatter(min(n,2),i,color=PINK_MAIN,s=16,zorder=3)
 dn.text(2.06,i,f'{n:.2f}',fontsize=7.2,va='center')
for ax in [d,dn,ds]:ax.set_ylim(8.6,-1);ax.axhline(3.5,color='black',ls='--',lw=.65)
d.set(yticks=range(9),yticklabels=[x[2] for x in t_items],xlabel='Joint compliance (%)',xlim=(0,63));d.tick_params(labelsize=8);grid(d,'x');panel(d,'a')
dn.set(xlim=(0,2.85),yticks=[],xticks=[0,.5,.9,2],xlabel='Apparent NUE');dn.tick_params(labelsize=7.5)
metrics=['Yield','Executed_N','S_N','partial_profit'];mat=np.array([[val(query(p,m),k) for k in metrics] for p,m,l in t_items])
scaled=np.clip((mat-np.array([0,0,-60,0]))/np.array([8,250,180,1200]),0,1)
im=ds.imshow(scaled,aspect='auto',cmap=SCORE_CMAP,vmin=0,vmax=1)
ds.set(xticks=range(4),xticklabels=['Yield\n(t/ha)','N applied\n(kg/ha)','S_N\n(kg/ha)','Profit\n(EUR/ha)'],yticks=[],ylim=(8.6,-1));ds.tick_params(labelsize=6.8)
for i in range(9):
 for j in range(4):contrast_label(ds,j,i,f'{mat[i,j]:.2f}' if j==0 else f'{mat[i,j]:.1f}' if j==2 else f'{mat[i,j]:.0f}',im.cmap(im.norm(scaled[i,j])),fontsize=6.8,ha='center',va='center')
panel(ds,'b')
fig4.subplots_adjust(left=.13,right=.98,bottom=.16,top=.92)
save(fig4,'figs4-policy-scorecard','V9 Supplementary Fig. S4 (compact 2-panel appendix). Nine-policy bootstrap CI compliance and apparent NUE (a) paired with 4-metric SCORE_CMAP scorecard (b). CI '+json.dumps(cis))
