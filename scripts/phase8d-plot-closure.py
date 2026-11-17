"""V9 Supplementary Figs. S2 & S8: Compact 2-panel Appendix figures for soil budget/traces and 50-cell readout/C-N audit."""
import runpy
from pathlib import Path
globals().update(runpy.run_path(str(Path(__file__).with_name('phase8d-plot-style.py'))))
from matplotlib.lines import Line2D

D=json.loads((P/'phase8d-full-TRAIN-physical-decoding.json').read_text())
native=pd.read_csv(P/'phase8d-native-episode-metrics.csv',low_memory=False)
primary=Path('/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体')
items=[('TreeMLP','soft','Sensorless','Soft'),('SensorlessPPO','tree','Sensorless','PPO'),('DVS-N2','tree','Full-Telemetry','DVS · Full'),('TreeMLP','hard-bare-tier2','Sensorless','Bare')]
budget=[];sources={}
for pol,mode,tr,lab in items:
 z=native[(native.source=='NASA')&(native.cohort=='Former-Held-Out')&(native.benchmark=='P1')&(native.climate=='Historical')&(native.cap==40)&(native.price_multiplier==1)&(native.subsidy==0)&(native.tax==0)&(native.policy==pol)&(native['mode']==mode)&(native.track==tr)]
 records=[]
 for _,r in z.iterrows():
  path=primary/'data/phase8d-evaluation'/r.episode_id/'result.json';digest=hashlib.sha256(path.read_bytes()).hexdigest()
  assert digest==r.episode_sha256;data=json.loads(path.read_text());sd=data['stock_diagnostics'];sources[str(path)]=digest
  records.append(dict(region=r.region,year=r.year,drawdown=sd['soil_N_stock_drawdown_kg_ha'],adjusted=sd['stock_adjusted_apparent_NUE']))
 d=pd.DataFrame(records).groupby(['region','year']).mean().reset_index();assert len(d)==52
 mean=d.groupby('region')[['drawdown','adjusted']].mean().mean();q=query(pol,mode,tr)
 budget.append({'label':lab,'Executed_N':val(q,'Executed_N'),'drawdown':float(mean.drawdown),'Grain_N':val(q,'Grain_N'),'loss':val(q,'Native_N_loss'),'NUE':val(q,'NUE'),'adjusted':float(mean.adjusted)})

(O/'phase8d-cea-v5-stock-budget.json').write_text(json.dumps({'selection':'NASA Former P1 Historical cap40 1x subsidy0 tax0; seeds averaged within farm-year then equal regions','budget':budget,'native_result_sha256':sources,'qualification':'Supply/fate components are not a closed grain-only budget: straw, roots and other boundary transfers are omitted. Native stock diagnostic scope remains unchanged.'},indent=2))

# Supplementary Fig. S2: Compact 2-panel Soil N supply/fate + NUE (a) and 349-day AU Perth 2015 C/N traces (b)
fig2=plt.figure(figsize=(10.4,4.4))
gs2=fig2.add_gridspec(1,2,width_ratios=[1.12,1.0],wspace=.32)
ag=gs2[0].subgridspec(1,2,width_ratios=[1.35,1.0],wspace=.38)
a=fig2.add_subplot(ag[0]);an=fig2.add_subplot(ag[1])
for i,q in enumerate(budget):
 for offset,fields,cols in [(-.15,['Executed_N','drawdown'],[SLATE_BLUE,ORANGE]),(.15,['Grain_N','loss'],[TEAL_SAGE,PINK_MAIN])]:
  left=0
  for field,col in zip(fields,cols):a.barh(i+offset,q[field],left=left,color=col,height=.26,label=field if i==0 else None);left+=q[field]
a.set(yticks=range(4),yticklabels=[x['label'] for x in budget],xlabel='N supply / selected fate (kg N/ha)',ylim=(4.6,-.8))
a.legend(fontsize=6.2,ncol=2,loc='lower right');grid(a,'x')
a.text(.02,1.03,'Applied+drawdown · grain+loss',transform=a.transAxes,fontsize=6.8,va='bottom');panel(a,'a')

an.axvspan(.5,.9,color='#FFF6EC',zorder=0)
for i,q in enumerate(budget):
 an.barh(i-.15,q['adjusted'],height=.25,color=SLATE_BLUE);an.barh(i+.15,q['NUE'],height=.25,color=PINK_MAIN)
an.set(yticks=range(4),yticklabels=[q['label'] for q in budget],xlabel='NUE (symlog) · blue adj / pink app')
an.set_xlim(0,12);an.set_xscale('symlog',linthresh=1);an.set_xticks([0,.5,.9,2,5,10]);an.set_xticklabels(['0','.5','.9','2','5','10'])
an.tick_params(labelsize=7.5);an.set_ylim(4.6,-.8);grid(an,'x')

trace=fig2.add_subplot(gs2[1]);mineral=trace.twinx()
trace_sources={};case_cols=[POLICY_COLORS[x[3]] for x in items]
for j,((pol,mode,tr,lab),co) in enumerate(zip(items,case_cols)):
 data,dd,path=native_case(pol,mode,tr,REG[0],2015);assert len(dd)==349;trace_sources[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
 day=np.arange(len(dd))
 trace.plot(day,dd.NORGT-dd.NORGT.iloc[0],color=co,lw=1.15,marker=['o','s','D','v'][j],ms=2.2,markevery=(j*7,28),label=lab+(' · seed '+str(data['case']['seed']) if 'seed' in data['case'] else ''))
 mineral.plot(day,dd.NO3T+dd.NH4T,color=co,lw=.9,ls='--',marker='o' if lab=='PPO' else ('s' if lab=='DVS · Full' else None),ms=2.0,markevery=(0 if lab=='PPO' else 14,28))
trace.set(xlabel='AU Perth 2015 · day from start',ylabel='Organic N Δstock · solid (kg/ha)',xlim=(0,348));grid(trace,'y')
mineral.set_ylabel('Mineral N · dashed (kg/ha)',fontsize=8.2);mineral.spines['right'].set_visible(True)
trace.tick_params(labelsize=7.6);mineral.tick_params(labelsize=7.6);trace.legend(fontsize=6.4,ncol=2,loc='lower left')
trace.text(.98,.92,'Organic N curves overlap',transform=trace.transAxes,ha='right',fontsize=6.8);panel(trace,'b')

(O/'phase8d-cea-v6-closure-traces.json').write_text(json.dumps({'source_sha256':trace_sources,'case':'AU Perth 2015, four policies, 349 days each','zero_residuals':'Exact zeros omitted on logarithmic axes; no positive floor fabricated','scope':'Illustrative daily traces; all-configurations maxima and record totals are independently frozen aggregate audits'},indent=2))
fig2.subplots_adjust(left=.07,right=.92,bottom=.16,top=.87)
save(fig2,'fig5-deployment-closure','V9 Supplementary Fig. S2 (compact 2-panel appendix). Test soil N supply/fate and stock-adjusted NUE (a) paired with 349-day AU Perth 2015 organic drawdown and mineral N traces (b).')

# Supplementary Fig. S8: Compact 2-panel 50-cell TRAIN readout R2 heatmap (a) + daily C/N mass closure & gauges (b)
fig8=plt.figure(figsize=(10.6,4.6))
gs8=fig8.add_gridspec(1,2,width_ratios=[1.15,1.0],wspace=.34)
targets=['final_organic_N_kg_ha','final_soil_C_kg_ha','native_net_mineralization_N_kg_ha','final_mineral_N_kg_ha','native_Nloss_kg_ha']
tl=['Organic N','Soil C','Mineralization','Mineral N','Native N loss']
s8a=fig8.add_subplot(gs8[0])
mat=np.array([[D['results'][tr+'-mlp']['by_region'][r][t]['latent_OOF_R2'] for t in targets] for tr in TRACKS for r in REG])
raw=np.array([[D['results'][tr+'-mlp']['by_region'][r][t]['raw_OOF_R2'] for t in targets] for tr in TRACKS for r in REG])
im=s8a.imshow(mat,aspect='auto',cmap=HEATMAP_CMAP,norm=TwoSlopeNorm(vmin=-.65,vcenter=0,vmax=1))
s8a.set(xlim=(-.5,4.5),ylim=(9.5,-.5),xticks=range(5),xticklabels=tl,yticks=range(10),yticklabels=[tr+' · '+r for tr in ['Sensorless','Full'] for r in RN])
s8a.tick_params(axis='y',labelsize=7.5);s8a.tick_params(axis='x',labelsize=6.8,rotation=18)
for sp in s8a.spines.values():sp.set_visible(True);sp.set_linewidth(.95);sp.set_edgecolor('#000000')
for i in range(10):
 for j in range(5):
  s8a.add_patch(plt.Rectangle((j-.5,i-.5),1,1,fill=False,ec='#586670',lw=.55,zorder=2))
  contrast_label(s8a,j,i,f'{mat[i,j]:.3f}' if 0<mat[i,j]<.01 else f'{mat[i,j]:.2f}',im.cmap(im.norm(mat[i,j])),ha='center',va='center',fontsize=7.2,zorder=5)
s8a.axhline(4.5,color='black',lw=1.1,zorder=3);s8a.add_patch(plt.Rectangle((-.5,-.5),3,10,fill=False,ec='black',lw=1.5,zorder=4,clip_on=False))
panel(s8a,'a');s8a.text(.02,1.03,'Frame: 30/30 required positive cells',transform=s8a.transAxes,fontsize=7.2)
cb=fig8.colorbar(im,ax=s8a,fraction=.042,pad=.03);cb.set_label('TRAIN latent readout R²',fontsize=8);cb.ax.tick_params(labelsize=7.5)
for sp in cb.ax.spines.values():sp.set_visible(True);sp.set_linewidth(.85);sp.set_edgecolor('#000000')

bg_d=gs8[1].subgridspec(2,1,height_ratios=[1.65,1.0],hspace=.52)
b=fig8.add_subplot(bg_d[0]);br=fig8.add_subplot(bg_d[1]);m=S['mass_all_configurations']
for metric,col,tol in [('N',PINK_MAIN,1e-10),('C',SLATE_BLUE,1e-9)]:
 for pol,mode,tr,lab in items:
  data,dd,path=native_case(pol,mode,tr,REG[0],2015);vv=abs(dd[metric+'_residual_kg_ha'].to_numpy())
  b.plot(np.arange(len(dd)),np.where(vv>0,vv,np.nan),color=col,lw=.6,alpha=.62)
 b.axhline(tol,color=col,ls='--',lw=.9,label=metric+' tolerance')
b.axhspan(1e-9,1e-8,color=PINK_MAIN,alpha=.08);b.set(yscale='log',xlim=(0,348),ylim=(1e-16,1e-8),xlabel='AU Perth 2015 · archived day',ylabel='|Daily residual| (kg/ha)')
b.tick_params(labelsize=7.5);grid(b,'y');b.legend(fontsize=7.2,ncol=2,loc='lower right');panel(b,'b')

for i,(v,t,col) in enumerate(zip([m['max_N'],m['max_C']],[1e-10,1e-9],[PINK_MAIN,SLATE_BLUE])):
 br.barh(i,t,height=.38,color='#E6F0EA');br.scatter(v,i,color=col,s=28,zorder=3);br.text(v*1.3,i,f'{v:.3e} · {t/v:.2f}×',fontsize=7.5,va='center')
br.set(xscale='log',xlim=(1e-12,2e-8),yticks=[0,1],yticklabels=['N max','C max'],xlabel='All-config tolerance (kg/ha)',ylim=(-.5,1.9));br.tick_params(labelsize=7.5)
callout_badge(br,.5,.95,f"{m['daily_records']:,} records · 0 violations · 1,886 native / 16,382 replays",col=TEAL_SAGE,transform=br.transAxes,ha='center',va='top',fontsize=6.4)

fig8.subplots_adjust(left=.12,right=.96,bottom=.15,top=.90)
save(fig8,'figs8-closure-readout-audit','V9 Supplementary Fig. S8 (compact 2-panel appendix). All 50 TRAIN physical readout R2 cells with 30/30 required frame (a) and 6,104,146-record daily C/N mass closure audit (b).')
