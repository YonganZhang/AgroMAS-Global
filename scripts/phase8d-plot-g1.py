"""V12 main Fig. 2 (unified 2b regime+attributes bar chart & tightened 2c EUNEP frame)."""
import runpy
from pathlib import Path
globals().update(runpy.run_path(str(Path(__file__).with_name('phase8d-plot-style.py'))))
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

context=long_context();G=json.loads((P/'phase8d-G1-verdict.json').read_text())['results']
W=json.loads((P/'phase8d-G1-radius-interpretation.json').read_text())['tracks']
z=cases();assert len(z)==52

fig=plt.figure(figsize=(14.4,9.6))
gs=fig.add_gridspec(2,2,width_ratios=[1.05,1.08],height_ratios=[1.0,1.0],hspace=.34,wspace=.28)

# Panel a: 47-year (1980-2026) Jan-Oct climate anomalies + NL CLO N deposition trends
a=fig.add_subplot(gs[0,0])
arr=pd.DataFrame(context['climate']).sort_index();years=arr.index.astype(int)
for reg,lab,col in zip(REG,RN,REG_COLS):
 v=arr[reg];a.plot(years,v,'o',ms=1.5,alpha=.28,color=col)
 a.plot(years,v.rolling(5,center=True,min_periods=1).mean(),color=col,lw=1.5,label=lab)
a.fill_between(years,arr.quantile(.25,axis=1),arr.quantile(.75,axis=1),color=GREY,alpha=.28,zorder=1)
eras(a);a.set(xlim=(1980,2026),ylim=(-2.2,4.2),xlabel='Year · Spin-up / Train / Dev / locked Test',ylabel='Jan–Oct ΔT (°C)')
a.tick_params(labelsize=8);grid(a,'y');panel(a,'a')
a.legend(ncol=5,fontsize=7.5,loc='lower left',bbox_to_anchor=(0,1.02))
for xmid,tag in [(1987,'Spin-up'),(2002,'Train'),(2012,'Dev'),(2020.5,'Test')]:
 a.text(xmid,.96,tag,transform=a.get_xaxis_transform(),ha='center',va='top',fontsize=7.2,color='#4A5860' if tag!='Test' else '#000000')

at=a.twinx();yr=np.arange(1980,2027)
at.plot(yr,697-.339*yr,color=PLUM_SOFT,ls='--',lw=1.6,label='NH4-N (NL CLO)')
at.plot(yr,538.868-.264*yr,color=SLATE_DARK,ls=':',lw=1.7,label='NOx-N (NL CLO)')
at.set(xlim=(1980,2026),ylim=(0,34));at.set_ylabel('NL deposition (kg N/ha)',fontsize=9)
at.tick_params(labelsize=8);at.spines['right'].set_visible(True)
at.legend(fontsize=7.0,loc='lower right',ncol=2)

# Panel b: Unified Five-Breadbasket 5-Regime Breakdown (0-100%) + Embedded Attribute Bar Tracks (no split void)
b=fig.add_subplot(gs[0,1])
base=pd.DataFrame(context['physical_zero_split_baseline'])
init=base.groupby('region').initial_N_t_ha.mean().reindex(REG)
b_cols=[ORANGE,SLATE_BLUE,TEAL_SAGE,PINK_MAIN,PLUM_SOFT]
b_labs=['Compliant','Surplus only','Surplus+Low NUE','NUE > 0.90','Low NUE']
for i,reg in enumerate(REG):
 q=z[z.region==reg];com=q.joint.astype(bool)
 sur_only=(~com)&(q.S_N>40)&(q.NUE>=.50)
 sur_low=(~com)&(q.S_N>40)&(q.NUE<.50)
 mine=(~com)&(q.S_N<=40)&(q.NUE>.90)
 low_only=(~com)&(q.S_N<=40)&(q.NUE<.50)
 masks=[com,sur_only,sur_low,mine,low_only]
 assert sum(int(m.sum()) for m in masks)==len(q),(reg,[int(m.sum()) for m in masks])
 left=0.0
 for mask,col in zip(masks,b_cols):
  width=100.0*mask.sum()/len(q)
  if width>0:
   b.barh(i,width,left=left,color=col,height=.54,edgecolor='white',lw=.45,zorder=3)
   if width>=14:contrast_label(b,left+width/2,i,f'{width:.0f}%',col,ha='center',va='center',fontsize=7.0,zorder=4)
  left+=width
 vals=[(init[reg],20.0,106.0,TEAL_SAGE,f'{init[reg]:.1f}'),(q.Yield.mean(),10.5,122.0,ORANGE,f'{q.Yield.mean():.1f}'),(q.NUE.mean(),1.35,138.0,PINK_MAIN,f'{q.NUE.mean():.2f}')]
 for val_m,scale,x0,col,txt in vals:
  b.barh(i,12.0,left=x0,color='#EEF1F5',height=.44,edgecolor='#D6DCE2',lw=.45,zorder=1)
  w_fill=12.0*min(val_m/scale,1.0)
  b.barh(i,w_fill,left=x0,color=col,height=.44,edgecolor='white',lw=.35,alpha=.88,zorder=2)
  b.text(x0+6.0,i-.28,txt,ha='center',va='bottom',fontsize=6.6,zorder=4)
b.axvline(103.0,color='#9AA6AC',ls='--',lw=.75,zorder=2)
b.set(xlim=(0,154),xticks=[0,25,50,75,100,112,128,144],
      xticklabels=['0%','25%','50%','75%','100%','Org.N\n(t/ha)','Yield\n(t/ha)','App.\nNUE'],
      yticks=range(5),yticklabels=RN,ylim=(4.6,-.68),
      xlabel='EUNEP regime breakdown (%) & regional agronomic attributes')
b.tick_params(labelsize=7.8);grid(b,'x');panel(b,'b')
b.legend(handles=[Patch(color=c,label=l) for c,l in zip(b_cols,b_labs)],
         ncol=5,fontsize=6.3,columnspacing=.75,handletextpad=.35,handlelength=1.1,loc='lower left',bbox_to_anchor=(0,1.02))

# Panel c: Classical EUNEP Safe Corridor tightly framed to data range [35, 248] with 1-sigma covariance ellipses
c=fig.add_subplot(gs[1,0])
draw_eunep_corridor(c,xlim=(35,248),ylim=(0,300),penalty=True);panel(c,'c')
for reg,lab,col,off in zip(REG,RN,REG_COLS,[(9,8),(8,-14),(8,-2),(-28,-4),(10,-8)]):
 q=z[z.region==reg];nx=q.Grain_N+q.S_N;ny=q.Grain_N
 cov_ellipse(c,nx,ny,col,ls='-',lw=1.35,alpha_fill=.12,zorder=3)
 c.scatter(nx,ny,s=18,c=col,edgecolors='white',linewidths=.38,alpha=.78,zorder=4)
 xm,ym=float(nx.mean()),float(ny.mean())
 c.scatter(xm,ym,marker='D',s=72,color=col,edgecolor='white',lw=.8,zorder=5)
 c.annotate(lab,(xm,ym),xytext=off,textcoords='offset points',fontsize=8.2)
c.text(.97,.04,'1 above 300 (FR)',transform=c.transAxes,ha='right',va='bottom',fontsize=6.8)
c.text(.04,.90,'NUE 0.50–0.90 · S_N 0–40',transform=c.transAxes,fontsize=7.6,bbox={'facecolor':'#FFFDF9','edgecolor':SAGE,'lw':.65,'pad':2.2})
c.legend(handles=[Line2D([],[],marker='D',color=co,lw=1.4,ms=5.5,label=lab) for co,lab in zip(REG_COLS,RN)],fontsize=7.2,ncol=5,loc='lower left',bbox_to_anchor=(0,1.02))

# Panel d: Regional 90% coverage + Dual-scale BSS over ExtraTrees (%) & Raw Brier Score + Grouped Width/Regret Bars
dg=gs[1,1].subgridspec(2,1,height_ratios=[1.0,1.08],hspace=.46)
d1=fig.add_subplot(dg[0])
d1.axhspan(85,95,color='#EDF2F7',alpha=.80,zorder=0);d1.axhline(90,ls='--',color=SLATE_GREY,lw=.8,zorder=1);panel(d1,'d')
for tr,col in zip(TRACKS,TC):
 v=G[tr+'-mlp'];keys=[None,REG[0],REG[4],REG[3],REG[2],REG[1]]
 yy=[100*(v['Dev_crossyear_macro_90pct_coverage'] if k is None else v['by_region'][k]['crossyear_coverage']) for k in keys]
 d1.plot(range(6),yy,'o-',color=col,lw=1.7,ms=5.0,markeredgecolor='white',markeredgewidth=.5,label=tr)
d1.set(xticks=range(6),xticklabels=['Macro','AU','CN','FR','NL','US'],ylabel='90% coverage (%)',ylim=(70,103))
d1.tick_params(labelsize=7.8);grid(d1,'y');d1.legend(fontsize=7.2,loc='lower left',bbox_to_anchor=(0,1.02),ncol=2)

d2g=dg[1].subgridspec(1,2,width_ratios=[1.15,1.05],wspace=.48)
d2a=fig.add_subplot(d2g[0]);d2ar=d2a.twinx();d2b=fig.add_subplot(d2g[1]);d2bt=d2b.twiny()
caps_k=['25','35','40','50'];caps_v=[25,35,40,50]
bss_curves=[]
for tr,col in zip(TRACKS,TC):
 bss=[100*G[tr+'-mlp']['caps'][k]['BSS_vs_ExtraTrees'] for k in caps_k];bss_curves.append(bss)
 d2a.plot(caps_v,bss,'o-',color=col,lw=1.6,ms=4.5,markeredgecolor='white',markeredgewidth=.45,label=tr.split('-')[0]+' BSS')
 bs=[G[tr+'-mlp']['caps'][k]['brier'] for k in caps_k]
 d2ar.plot(caps_v,bs,'s--',color=col,lw=1.1,ms=3.5,alpha=.75)
d2a.fill_between(caps_v,*bss_curves,color=GREY,alpha=.25)
et_b=[G['Full-Telemetry-mlp']['caps'][k]['tree_brier'] for k in caps_k]
d2ar.plot(caps_v,et_b,':',color=PLUM_SOFT,lw=1.3,label='ET Brier')
d2a.set(xticks=caps_v,ylim=(0,28),xlabel='Surplus cap (kg/ha)',ylabel='BSS vs ET · solid (%)')
d2ar.set(ylim=(.025,.044),ylabel='Brier · dashed');d2ar.spines['right'].set_visible(True)
d2a.tick_params(labelsize=7.2);d2ar.tick_params(labelsize=7.0);grid(d2a,'y')
d2a.legend(handles=[Line2D([],[],color=PINK_MAIN,lw=1.5,label='Sens BSS'),Line2D([],[],color=SLATE_BLUE,lw=1.5,label='Full BSS'),
                    Line2D([],[],color='black',ls='--',lw=1.1,label='MLP Brier'),Line2D([],[],color=PLUM_SOFT,ls=':',lw=1.3,label='ET Brier')],
           fontsize=6.0,ncol=2,loc='upper left',bbox_to_anchor=(0,.99))

r_s,r_f=G['Sensorless-mlp'],G['Full-Telemetry-mlp']
w_rows=[(0,W['Full-Telemetry-mlp']['macro_uncalibrated_width'],W['Full-Telemetry-mlp']['macro_calibrated_width'],SLATE_BLUE),
        (1,W['Sensorless-mlp']['macro_uncalibrated_width'],W['Sensorless-mlp']['macro_calibrated_width'],PINK_MAIN)]
r_rows=[(2,r_f['ExtraTrees_regret_EUR_ha'],r_f['partial_profit_ranking_regret_EUR_ha'],SLATE_BLUE),
        (3,r_s['ExtraTrees_regret_EUR_ha'],r_s['partial_profit_ranking_regret_EUR_ha'],PINK_MAIN)]
for y_idx,v0,v1,col in w_rows:
 d2b.barh(y_idx-.16,v0,height=.28,facecolor='#EEF1F5',edgecolor=col,lw=.85)
 d2b.barh(y_idx+.16,v1,height=.28,facecolor=col,edgecolor='black',lw=.35)
 d2b.text(v0+1.5,y_idx,f'−{100*(1-v1/v0):.1f}%',va='center',fontsize=6.5)
for y_idx,v0,v1,col in r_rows:
 d2bt.barh(y_idx-.16,v0,height=.28,facecolor='#EEF1F5',edgecolor=col,lw=.85)
 d2bt.barh(y_idx+.16,v1,height=.28,facecolor=col,edgecolor='black',lw=.35)
 d2bt.text(v0+.2,y_idx,f'−{100*(1-v1/v0):.1f}%',va='center',fontsize=6.5)
d2b.axhline(1.5,color='#9AA6AC',ls='--',lw=.65)
d2b.set(xlim=(0,108),ylim=(-.5,3.55),yticks=[0,1,2,3],yticklabels=['Full W','Sens W','Full R','Sens R'],xlabel='Width: base/G1 (kg/ha)')
d2bt.set(xlim=(0,10.6),xlabel='Regret: ET/G1 (EUR/ha)');d2bt.spines['top'].set_visible(True)
d2b.tick_params(labelsize=7.0);d2bt.tick_params(labelsize=7.0);grid(d2b,'x')

fig.subplots_adjust(left=.06,right=.96,top=.92,bottom=.08)
save(fig,'fig2-g1','V12 main Fig. 2 (unified 2b regime+attributes chart & tightened 2c EUNEP frame xlim=[35,248]).')
