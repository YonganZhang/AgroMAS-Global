"""V12 main Fig. 3 (tightened 3a EUNEP [0, 252], nested Either-bound + Safe-NUE + Joint 10-policy 3b, 2-row hydrograph 3c, dual NUE/S_N 3d) + Fig. S5."""
import runpy
from pathlib import Path
globals().update(runpy.run_path(str(Path(__file__).with_name('phase8d-plot-style.py'))))
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

items=[
 ('TreeMLP','soft','Sensorless','Soft-Coupled'),
 ('TreeMLP','tree','Sensorless','Tier2'),
 ('TreeMLP','hard-bare-tier2','Sensorless','Archived bare'),
 ('SensorlessPPO','tree','Sensorless','PPO'),
 ('DVS-N2','tree','Full-Telemetry','DVS · Full'),
 ('TreeExtraTrees','soft','Sensorless','ExtraTrees'),
 ('TreeWeather','soft','Sensorless','Weather'),
 ('TreeLinear','soft','Sensorless','Linear'),
]
b_items=[
 ('SensorlessPPO','tree','Sensorless','PPO'),
 ('DVS-N2','tree','Full-Telemetry','DVS · Full'),
 ('TreeMLP','soft','Sensorless','Soft-Coupled'),
 ('TreeMLP','tree','Sensorless','Tier2'),
 ('TreeMLP','open-loop','Sensorless','Open-loop'),
 ('TreeExtraTrees','soft','Sensorless','ExtraTrees'),
 ('TreeWeather','soft','Sensorless','Weather'),
 ('TreeMLP','greedy-frozen','Sensorless','Greedy'),
 ('TreeLinear','soft','Sensorless','Linear'),
 ('TreeMLP','hard-bare-tier2','Sensorless','Archived bare'),
]

fig=plt.figure(figsize=(14.4,9.6))
gs=fig.add_gridspec(2,2,width_ratios=[1.05,1.08],height_ratios=[1.0,1.0],hspace=.34,wspace=.28)

# Panel a: Clean EUNEP Phase Space tightly framed to [0, 252] with 2D 1-sigma covariance ellipses & centroid markers
a=fig.add_subplot(gs[0,0]);draw_eunep_corridor(a,xlim=(0,252),ylim=(0,300))
a_specs=[(items[0],'o'),(items[3],'^'),(items[4],'D'),(items[2],'s')]
for (p,m,tr,lab),mk in a_specs:
 z=cases(p,m,tr);assert len(z)==52;col=POLICY_COLORS[lab]
 nx=z.Grain_N+z.S_N;ny=z.Grain_N
 cov_ellipse(a,nx,ny,col,ls='--' if lab=='Archived bare' else '-',lw=1.35,alpha_fill=.10,zorder=3)
 a.scatter(nx,ny,s=18,c=col,marker=mk,edgecolors='white',linewidths=.38,alpha=.78,zorder=4)
 a.scatter(float(nx.mean()),float(ny.mean()),s=68,color=col,marker=mk,edgecolor='black',lw=.7,label=f"{lab} ({val(query(p,m,tr)):.1f}%)",zorder=5)
a.text(.97,.04,'Each policy: 1 above 300',transform=a.transAxes,ha='right',fontsize=6.8)
a.legend(fontsize=6.8,loc='lower left',bbox_to_anchor=(0,1.02),ncol=2);panel(a,'a')

# Panel b: 10-Policy Nested Compliance Tracks (Either safe bound + Safe NUE 0.5-0.9 + Joint Regional Stack + 95% CI)
b=fig.add_subplot(gs[0,1])
for i,(p,m,tr,lab) in enumerate(b_items):
 q=query(p,m,tr);z=cases(p,m,tr);lo,hi=bootstrap_joint(z);left=0.0
 nue_ok=float(np.mean([((z[z.region==r].NUE>=.5)&(z[z.region==r].NUE<=.9)).mean() for r in REG])*100)
 either_ok=float(np.mean([(((z[z.region==r].NUE>=.5)&(z[z.region==r].NUE<=.9))|((z[z.region==r].S_N>=0)&(z[z.region==r].S_N<=40))).mean() for r in REG])*100)
 b.barh(i,either_ok,height=.64,facecolor='#EDF2F7',edgecolor=SLATE_BLUE,lw=.65,ls='--',zorder=1)
 b.barh(i,nue_ok,height=.42,facecolor='#F9ECEA',edgecolor=PINK_MAIN,lw=.60,zorder=2)
 for r,col in zip(REG,REG_COLS):
  share=100*q['by_region'][r]['joint']/5.0
  b.barh(i,share,left=left,color=col,height=.64,edgecolor='white',lw=.35,zorder=3)
  left+=share
 b.errorbar(left,i,xerr=[[max(0,left-lo)],[max(0,hi-left)]],fmt='none',ecolor='black',capsize=2.2,lw=.85,zorder=4)
 b.text(max(hi,either_ok)+1.0,i,f'{left:.1f}% · {either_ok:.0f}%',va='center',fontsize=7.0)
b.set(xlim=(0,72),yticks=range(10),yticklabels=[x[3] for x in b_items],ylim=(9.6,-.65),xlabel='Equal-region compliance: Joint · Either safe (%)')
b.tick_params(labelsize=7.8);grid(b,'x');panel(b,'b')
b_handles=[Patch(color=c,label=r) for c,r in zip(REG_COLS,RN)]+[
 Patch(facecolor='#F9ECEA',edgecolor=PINK_MAIN,lw=.6,label='Safe NUE'),
 Patch(facecolor='#EDF2F7',edgecolor=SLATE_BLUE,lw=.65,ls='--',label='Either bound')]
b.legend(handles=b_handles,ncol=4,fontsize=6.5,columnspacing=.8,handletextpad=.35,loc='lower left',bbox_to_anchor=(0,1.02))

# Panel c: Classical 2-Row Framed Seasonal Agronomic Dynamics (AU Perth 2015, 349 days)
cg=gs[1,0].subgridspec(2,1,height_ratios=[1.85,.78],hspace=.16)
c1=fig.add_subplot(cg[0]);loss=c1.twinx();c2=fig.add_subplot(cg[1],sharex=c1);c2_r=c2.twinx()
paths={};case_items=[items[0],items[3],items[4],items[2]]
weather=PRIMARY/'data/global_regions'/REG[0]/'nasa-power-19840101-20261101.json'
w_rain=json.loads(weather.read_text())['properties']['parameter']['PRECTOTCORR']
paths[str(weather)]=hashlib.sha256(weather.read_bytes()).hexdigest()
for j,(pol,mode,tr,lab) in enumerate(case_items):
 co=POLICY_COLORS[lab];data,dd,path=native_case(pol,mode,tr,REG[0],2015);assert len(dd)==349
 paths[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest();days=np.arange(len(dd))
 c1.plot(days,dd.NO3T+dd.NH4T,color=co,lw=1.65 if j==1 else 1.0,marker='o' if j==1 else ('s' if j==2 else None),markevery=(j*7,28),ms=2.2,zorder=5+j,label=lab+(' · seed '+str(data['case']['seed']) if 'seed' in data['case'] else ''))
 loss.plot(days,dd.NLOSSCUM,color=co,lw=.9,ls='--')
 for e in data['events']:
  day=(pd.Timestamp(e['date'])-dd.day.iloc[0]).days
  c2_r.bar(day+(j-1.5)*2,e['dose'],width=2,color=co,edgecolor='white',linewidth=.25,zorder=4)
  if j==0:
   c1.axvspan(day-3,day+3,color=co,alpha=.07,zorder=0)
   c2_r.text(day,104,'S'+str(e['stage']),ha='center',fontsize=7.0)
 if j==0:
  rain=np.asarray([w_rain[t.strftime('%Y%m%d')] for t in dd.day]);assert rain.min()>=0
  c2.bar(days,rain,width=1.2,color=SLATE_BLUE,alpha=.65,zorder=2)
c1.set(xlim=(0,348),ylim=(0,260),ylabel='Mineral N · solid (kg/ha)');c1.tick_params(labelbottom=False,labelsize=7.8);grid(c1,'y');panel(c1,'c')
c1.legend(fontsize=6.8,ncol=2,loc='lower left',bbox_to_anchor=(0,1.02))
c1.text(.98,.56,'PPO / DVS overlap',transform=c1.transAxes,ha='right',fontsize=6.6)
loss.set_ylim(0,35);loss.set_ylabel('Cum. loss · dashed (kg/ha)',fontsize=8.2);loss.tick_params(labelsize=7.5);loss.spines['right'].set_visible(True)
c2.set(xlim=(0,348),ylim=(0,80),xlabel='AU Perth 2015 · day from start',ylabel='Rain (mm/d)');c2.tick_params(labelsize=7.6);grid(c2,'y')
c2_r.set(ylim=(0,120),ylabel='Dose (kg/ha)');c2_r.tick_params(labelsize=7.5);c2_r.spines['right'].set_visible(True)

# Panel d: Classical 2-Row Bilateral Corridor Distributions across 6 Core Policies (Apparent NUE top + S_N bottom)
dg=gs[1,1].subgridspec(2,1,height_ratios=[1.0,1.0],hspace=.28)
d_items=[items[0],items[3],items[4],items[1],items[6],items[2]]
d_short=['Soft','PPO','DVS','Tier2','Weather','Bare']
for j,(metric,yl,limits,safe_lo,safe_hi,hi_col) in enumerate([
 ('NUE','Apparent NUE',(0.2,2.15),.5,.9,'#F9ECEA'),
 ('S_N','Surplus S_N (kg/ha)',(-65,135),0,40,'#EDF2F7')
]):
 d_ax=fig.add_subplot(dg[j])
 d_ax.axhspan(limits[0],limits[1],facecolor='#FFFDF9',zorder=0)
 d_ax.axhspan(limits[0],safe_lo,facecolor='#F9ECEA',zorder=0)
 d_ax.axhspan(safe_hi,limits[1],facecolor=hi_col,zorder=0)
 d_ax.axhline(safe_lo,color=TEAL_SAGE,ls='--',lw=.8,zorder=1);d_ax.axhline(safe_hi,color=TEAL_SAGE,ls='--',lw=.8,zorder=1)
 for i,spec in enumerate(d_items):
  raincloud(d_ax,cases(*spec[:3])[metric].to_numpy(),i,POLICY_COLORS[spec[3]],vertical=True,width=.30)
 d_ax.set(xlim=(-.6,5.6),ylim=limits,xticks=range(6),xticklabels=d_short if j==1 else [],ylabel=yl)
 d_ax.tick_params(labelsize=7.6);grid(d_ax,'y')
 if j==0:d_ax.tick_params(labelbottom=False);d_ax.text(.98,.90,'Bare mean 11.56 · clipped 2.15',transform=d_ax.transAxes,ha='right',fontsize=6.5,bbox={'facecolor':'white','edgecolor':'none','alpha':.88,'pad':1.5});panel(d_ax,'d')
 else:d_ax.set_xlabel('Core control policies',fontsize=8.5);d_ax.text(.98,.88,'Tails cropped cleanly',transform=d_ax.transAxes,ha='right',fontsize=6.4,bbox={'facecolor':'white','edgecolor':'none','alpha':.88,'pad':1.5})

(O/'phase8d-cea-v6-season-sources.json').write_text(json.dumps({'case':'AU Perth 2015; exact 349 native days; illustrative, not representative inference','sources':paths,'daily_styles':'solid mineral N, dashed cumulative native N loss','stage_definition':'S1/S2/S3 actual decision-event dates; bands mark ±3 days, not measured DVS intervals'},indent=2))
fig.subplots_adjust(left=.06,right=.94,top=.91,bottom=.08)
save(fig,'fig2-p1-regimes','V12 main Fig. 3 (2x2). Uses tightened [0,252] 1-sigma covariance ellipses (3a), nested 10-policy Joint + Safe NUE + Either-bound bars (3b), 2-row framed hydrograph (3c), and aligned 2-row NUE/S_N corridor distributions (3d).')

# Supplementary Fig. S5: Compact 2-panel full 8-policy NUE rainclouds & 32-year trajectories
fig_s5=plt.figure(figsize=(10.2,4.4))
gs5=fig_s5.add_gridspec(1,2,width_ratios=[1.18,1.0],wspace=.30)
s5a=fig_s5.add_subplot(gs5[0])
s5a.axhspan(.2,2.2,facecolor='#F9ECEA',zorder=0);s5a.axhspan(.5,.9,facecolor='#FFFDF9',zorder=0)
s5a.axhline(.5,color=TEAL_SAGE,ls='--',lw=.8);s5a.axhline(.9,color=TEAL_SAGE,ls='--',lw=.8)
short8=['Soft','Tier2','Bare','PPO','DVS','ET','Weath','Lin']
for i,(spec,sl) in enumerate(zip(items,short8)):
 raincloud(s5a,cases(*spec[:3]).NUE.to_numpy(),i,POLICY_COLORS[spec[3]],width=.28)
s5a.set(xticks=range(8),xticklabels=short8,ylabel='Apparent NUE',xlabel='Full eight-policy cohort',ylim=(.2,2.2))
s5a.tick_params(labelsize=7.5);grid(s5a,'y');panel(s5a,'a')
bare=cases(*items[2][:3]);s5a.text(.98,.92,f'Bare mean {val(query(mode="hard-bare-tier2"),"NUE"):.2f} · clipped 2.2',transform=s5a.transAxes,ha='right',fontsize=6.6,bbox={'facecolor':'white','edgecolor':'none','alpha':.88,'pad':1.5})

s5g=gs5[1].subgridspec(2,1,hspace=.42)
for j,metric in enumerate(['NUE','S_N']):
 ax=fig_s5.add_subplot(s5g[j]);lo,hi=(.5,.9) if j==0 else (0,40)
 ax.axhspan(lo,hi,color='#FFF6EC',alpha=.85,zorder=0);annual_trajectory(ax,metric)
 ax.set_ylabel('NUE (symlog)' if j==0 else 'S_N (kg N/ha)',fontsize=8.2)
 if j==1:ax.set_xlabel('Year · Train / Dev / Test',fontsize=8.2)
 if j==0:ax.set_yscale('symlog',linthresh=1);ax.set_yticks([.5,.9,2,10,40]);ax.set_yticklabels(['.5','.9','2','10','40']);ax.legend(fontsize=6.5,ncol=3,loc='lower left',bbox_to_anchor=(0,1.03));panel(ax,'b')
 grid(ax,'y')
fig_s5.subplots_adjust(left=.07,right=.97,top=.88,bottom=.14)
save(fig_s5,'figs5-p1-all-regimes','V11 Supplementary Fig. S5 (2-panel compact appendix). Full 8-policy apparent NUE rainclouds (a) and 32-year descriptive reference vs Test trajectories (b).')
