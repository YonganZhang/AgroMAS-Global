"""Phase8C publication figures from locked statistical outputs (no resimulation)."""
from pathlib import Path
import json,hashlib,subprocess
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';O=P/'figures';S=json.loads((P/'phase8c-core-statistics.json').read_text());rows=S['summary']
font=Path(subprocess.check_output(['fc-match','-f','%{file}','Times New Roman'],text=True));font_manager.fontManager.addfont(str(font))
plt.rcParams.update({'font.family':'Times New Roman','font.size':13,'mathtext.fontset':'stix','svg.fonttype':'none','pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False,'text.color':'black','axes.labelcolor':'black','xtick.color':'black','ytick.color':'black'})
colors=['#B8525A','#6A90B0','#78926B','#9D8C74','#9586A8'];regions=['australia_wa_perth','usa_kansas_wichita','netherlands_lelystad','france_paris_beauce','china_ncp_luancheng'];names=['AU','US','NL','FR','CN'];receipt={}
def base(x):return x['climate']=='Historical' and x['cap']==40 and x['price_multiplier']==1 and x['subsidy']==0 and x['tax']==0
def get(policy,mode='soft',track='Sensorless',benchmark='P1',cohort='Former-Held-Out',scheme='none'):
 v=[x for x in rows if base(x) and x['policy']==policy and x['mode']==mode and x['track']==track and x['benchmark']==benchmark and x['cohort']==cohort and x['scheme']==scheme];assert len(v)==1,(policy,mode,track,benchmark,cohort,scheme,len(v));return v[0]
def save(fig,name):
 fig.canvas.draw();ren=fig.canvas.get_renderer();bounds=[]
 for a in fig.axes:
  b=a.get_tightbbox(ren);bounds.append([float(v) for v in b.bounds]);assert b.x0>=-2 and b.y0>=-2 and b.x1<=fig.bbox.width+2 and b.y1<=fig.bbox.height+2,(name,b.bounds)
 for ext in ['pdf','svg','png']:fig.savefig(O/(name+'.'+ext),dpi=450,facecolor='white')
 receipt[name]={'axes_tight_bounds_pixels':bounds,'canvas_pixels':[fig.bbox.width,fig.bbox.height],'titles':[dict(center=a.get_title(),left=a.get_title(loc='left')) for a in fig.axes]};plt.close(fig)
def panel(a,label,title):a.set_title(title,loc='left',fontsize=14);a.text(-.1,1.06,label,transform=a.transAxes,fontweight='bold',fontsize=17)
fig,axs=plt.subplots(2,2,figsize=(12,8),layout='constrained');a=axs.ravel();pol=['TreeMLP','SensorlessPPO','TreeExtraTrees','TreeLinear','TreeWeather'];labs=['Neural','PPO','ExtraTrees','Linear','Weather'];v=[get(p,mode='tree' if p=='SensorlessPPO' else 'soft') for p in pol]
a[0].bar(labs,[100*x['region_equal']['joint'] for x in v],color=colors);a[0].set_ylabel('Joint compliance (%)');panel(a[0],'a','P1 Sensorless: soft controllers; masked PPO')
for tr,c in [('Sensorless',colors[0]),('Full-Telemetry',colors[1])]:
 q=[get('TreeMLP',m,tr) for m in ['soft','tree','hard-bare-tier2']];a[1].plot(['Soft-Coupled','Tier2-Composite','Archived bare'],[100*x['region_equal']['joint'] for x in q],'o-',label=tr,color=c)
a[1].set_ylabel('Joint compliance (%)');a[1].legend(frameon=False);panel(a[1],'b','Objective retained across relaxation')
for j,(m,l) in enumerate([('soft','Soft-Coupled'),('tree','Tier2-Composite'),('hard-bare-tier2','Archived bare')]):
 x=get('TreeMLP',m);a[2].bar(np.arange(5)+(j-1)*.24,[100*x['by_region'][r]['joint'] for r in regions],.24,color=colors[j],label=l)
a[2].set_xticks(range(5),['AU (11)','US (12)','NL (5)','FR (12)','CN (12)']);a[2].set_ylabel('Joint compliance (%)');a[2].legend(frameon=False,fontsize=11);panel(a[2],'c','Regional heterogeneity')
for m,l,c in [('soft','Soft',colors[0]),('tree','Composite',colors[1]),('hard-bare-tier2','Bare',colors[2])]:
 x=get('TreeMLP',m)['region_equal'];a[3].scatter(x['partial_profit'],100*x['NUE_gt_090'],label=l,color=c,s=90,marker={'Soft':'o','Composite':'x','Bare':'s'}[l]);a[3].annotate(l,(x['partial_profit'],100*x['NUE_gt_090']),xytext={'Soft':(18,20),'Composite':(18,-22),'Bare':(-35,-18)}[l],textcoords='offset points',arrowprops=dict(arrowstyle='-',color=c));a[3].set_xlim(888,987);a[3].set_ylim(27,69)
a[3].set_xlabel('Partial profit (EUR ha$^{-1}$)');a[3].set_ylabel('NUE > 0.90 (%)');panel(a[3],'d','Sensorless partial profit and N mining');save(fig,'fig2-p1-regimes')
fig,axs=plt.subplots(2,2,figsize=(12,8),layout='constrained');a=axs.ravel();variants=['P2-Full64','P2-Static3','P2-Weather','P2-Linear64','P2-ExtraTrees64'];labels=['Full64','Static3','Weather','Linear64','ExtraTrees64']
for j,(co,scheme,lab) in enumerate([('Former-Held-Out','LOYO','Former LOYO (40)'),('Public-Reused','LOYO','Public NL LOYO (4)'),('Former-Held-Out','LORO','Former LORO (40)')]):
 vals=[get(p,benchmark='P2',cohort=co,scheme=scheme)['region_equal']['joint']*100 for p in variants];a[0].plot(labels,vals,'o-',color=colors[j],label=lab)
a[0].legend(frameon=False,fontsize=11);a[0].tick_params(axis='x',rotation=20);a[0].set_ylabel('Joint compliance (%)');panel(a[0],'a','P2 sources and folds kept separate')
for j,(scheme,mode) in enumerate([('LOYO','soft'),('LOYO','tree'),('LORO','soft'),('LORO','tree')]):
 x=get('P2-Full64',mode,benchmark='P2',scheme=scheme);a[1].plot(np.arange(5)+(j-1.5)*.035,[100*x['by_region'][r]['joint'] for r in regions],('o-' if mode=='soft' else 's--'),mfc=('white' if mode=='tree' else colors[j]),color=colors[j],label=scheme+(' soft' if mode=='soft' else ' composite'));a[1].set_xticks(range(5),names)
a[1].set_ylabel('Joint compliance (%)');a[1].legend(frameon=False,fontsize=11);panel(a[1],'b','Regional Full64 behavior (Former)')
for j,scheme in enumerate(['LOYO','LORO']):
 vals=[]
 for p in variants:
  x=get(p,benchmark='P2',scheme=scheme)['pooled'];vals.append(100*x['prior_accepted']/x['prior_decisions'] if x['prior_decisions'] else 0)
 a[2].bar(np.arange(5)+(j-.5)*.32,vals,.32,color=colors[j],label=scheme)
a[2].set_xticks(range(5),labels,rotation=20);a[2].set_ylabel('Accepted prior decisions (%)');a[2].set_ylim(0,115);a[2].set_yticks([0,25,50,75,100]);a[2].legend(frameon=False);panel(a[2],'c','Prior OOD → zero correction; backbone retained')
C=[x for x in S['contrasts'] if x['benchmark']=='P2' and x['cohort']=='Former-Held-Out' and x['source']=='NASA' and x['primary']==['P2-Full64','Sensorless','soft'] and x['reference']==['P2-Static3','Sensorless','soft'] and x['metric']=='joint'];print('P2 contrast regions',sorted(set(x['region'] for x in C)))
C=sorted([x for x in C if x['region']=='GLOBAL_EQUAL5'],key=lambda x:0 if x['scheme']=='LOYO' else 1);
if not C:C=[x for x in S['contrasts'] if x['benchmark']=='P2' and x['cohort']=='Former-Held-Out' and x['primary']==['P2-Full64','Sensorless','soft'] and x['reference']==['P2-Static3','Sensorless','soft'] and x['metric']=='joint' and x['region'] not in regions][:2]
for i,x in enumerate(C):
 d=x['mean_difference']*100;lo,hi=np.array(x['CI95'])*100;a[3].errorbar(d,i,xerr=[[d-lo],[hi-d]],fmt='o',color=colors[i]);a[3].text(.98,i+.17,f"Holm p={x['Holm_sign_p_full_family']:.2g}",va='center',ha='right',transform=a[3].get_yaxis_transform(),fontsize=11)
a[3].set_yticks(range(len(C)),[x['scheme']+' / equal 5-region' for x in C]);a[3].set_xlim(-15,14);a[3].set_ylim(-.45,len(C)-.5+.45);a[3].axvline(0,c='black',lw=.8);a[3].set_xlabel('Full64 − Static3 joint compliance (pp)');panel(a[3],'d','Marginal 95% bootstrap intervals');save(fig,'fig3-p2-transfer')
df=pd.read_csv(P/'phase8c-180cell-stress-surface.csv');climates=['Historical','idealized_mid','idealized_high'];fig,axs=plt.subplots(3,3,figsize=(13,11.5),layout='constrained')
for j,cl in enumerate(climates):
 v=df[(df.climate==cl)&(df.policy=='TreeMLP')&(df.track=='Sensorless')&(df['mode']=='soft')].copy();v['row']=v.region.map(dict(zip(regions,names)))+' / '+v.price_multiplier.astype(int).astype(str)+'× / '+v.subsidy.astype(int).astype(str);order=[n+' / '+str(p)+'× / '+str(s) for n in names for p,s in [(1,0),(2,0),(1,50)]];mat=v.pivot(index='row',columns='cap',values='joint').reindex(order);im=axs[0,j].imshow(mat*100,vmin=0,vmax=100,cmap='Blues',aspect='auto');axs[0,j].set_xticks(range(4),[25,35,40,50]);axs[0,j].set_yticks(range(15),order if j==0 else ['']*15,fontsize=10);axs[0,j].set_title({'Historical':'Historical','idealized_mid':'+1.8°C / 450 ppm','idealized_high':'+3.5°C / 550 ppm'}[cl]);axs[0,j].set_xlabel('Surplus cap (kg N ha$^{-1}$)')
 for ri in range(15):
  for ci in range(4):
   z=mat.iloc[ri,ci]*100;axs[0,j].text(ci,ri,f'{z:.0f}',ha='center',va='center',fontsize=10,color='white' if z>60 else 'black')
   if ri%3 in [0,1] and ci in [0,1,3]:axs[0,j].add_patch(plt.Rectangle((ci-.48,ri-.48),.96,.96,fill=False,ec='black',lw=.7))
 q=df[(df.climate==cl)&(df.policy=='SensorlessPPO')].copy();q['row']=q.region.map(dict(zip(regions,names)))+' / '+q.price_multiplier.astype(int).astype(str)+'× / '+q.subsidy.astype(int).astype(str);other=q.pivot(index='row',columns='cap',values='joint').reindex(order);delta=100*(mat-other);im2=axs[1,j].imshow(delta,vmin=-100,vmax=100,cmap='RdBu_r',aspect='auto');axs[1,j].set_xticks(range(4),[25,35,40,50]);axs[1,j].set_yticks(range(15),order if j==0 else ['']*15,fontsize=10);axs[1,j].set_xlabel('Surplus cap (kg N ha$^{-1}$)');axs[1,j].set_title('Soft-Coupled − PPO (pp)')
for j,(metric,label) in enumerate([('joint','Joint compliance (%)'),('partial_profit','Partial profit (EUR ha$^{-1}$)'),('Native_N_loss','Native N loss (kg ha$^{-1}$)')]):
 for pol,c in [('TreeMLP',colors[0]),('remove-econ',colors[1])]:
  q=sorted([x for x in rows if x['benchmark']=='P1' and x['cohort']=='Former-Held-Out' and x['climate']=='Historical' and x['cap']==40 and x['price_multiplier']==1 and x['track']=='Sensorless' and x['mode']=='soft' and x['policy']==pol],key=lambda x:x['subsidy'])
  axs[2,j].plot([x['subsidy'] for x in q],[(100 if metric=='joint' else 1)*x['region_equal'][metric] for x in q],'o-' if len(q)>1 else 'o',label='Complete' if pol=='TreeMLP' else 'Economics removed (50 only)',color=c)
 axs[2,j].set_xlabel('Experimental subsidy (EUR ha$^{-1}$)');axs[2,j].set_ylabel(label);axs[2,j].set_title('Historical cap40 diagnostic',fontsize=13)
 if j==0:axs[2,j].legend(frameon=False,fontsize=10)
axs[0,0].set_ylabel('Region / N-price / subsidy (EUR ha$^{-1}$)');fig.suptitle('Sensorless Soft-Coupled; black outlines = 90 continuity cells; idealized climates',fontsize=15)
for letter,axis in zip('abcdefghi',axs.flat):
 title=axis.get_title();axis.set_title('');axis.set_title(letter+'  '+title,loc='left',fontsize=13)
 assert axis.get_title()=='' and axis.get_title(loc='left').startswith(letter+'  ')
fig.colorbar(im,ax=axs[0,:],shrink=.8,label='Joint compliance (%)');fig.colorbar(im2,ax=axs[1,:],shrink=.8,label='Difference (pp)');save(fig,'fig4-factorial-stress')
fig,axs=plt.subplots(2,2,figsize=(12,8),layout='constrained');a=axs.ravel();a[0].axis('off');a[0].text(.03,.88,'36-D → 96 → 96 → 3',fontsize=23);a[0].text(.03,.68,'13,155 parameters per neural network\nFrozen three-seed ensemble; 32 outcome members',fontsize=16);a[0].text(.03,.35,'Private 64-D → PCA/Ridge ≤4-D\nAdditive output correction; no raw-feature broadcast',fontsize=16);panel(a[0],'a','Compact backbone and private adaptation');a[1].axis('off');a[1].text(.03,.82,'Regime',fontsize=24,fontweight='bold');a[1].text(.03,.64,'Climate • surplus cap • N price • subsidy\nEco / economics activation • objective mode',fontsize=16);a[1].text(.03,.32,'Sensorless: public weather, DVS and management\nFull-Telemetry: optional LAI / soil water / plant N\nRuntime claims require a separate timing benchmark',fontsize=15);panel(a[1],'b','Runtime interface and telemetry scope')
m=S['mass_new_native'];a[2].bar(['Nitrogen','Carbon'],[m['max_N'],m['max_C']],color=colors[:2]);a[2].set_yscale('log');a[2].set_ylim(1e-12,2e-9);a[2].axhline(1e-10,c=colors[0],ls='--',lw=.8,label='N tolerance');a[2].axhline(1e-9,c=colors[1],ls='--',lw=.8,label='C tolerance');a[2].legend(frameon=False,fontsize=10);a[2].set_ylabel('Maximum absolute closure residual (kg ha$^{-1}$)');panel(a[2],'c',f"{m['daily_records']:,} configuration-day records")
for i,z in enumerate([m['max_N'],m['max_C']]):a[2].annotate(f'{z:.3e}',(i,z),xytext=(0,6),textcoords='offset points',ha='center')
a[3].axis('off');a[3].text(.03,.85,'18,268 scored configurations',fontsize=22);a[3].text(.03,.62,'17,747 new configurations + 521 verified reuses\n1,917 actual unique native simulations\n15,830 exact trajectory cache hits',fontsize=17);a[3].text(.03,.28,'Repeated records are closure checks,\nnot independent physical trajectories.\n120 future-weather invariance checks passed.',fontsize=16);panel(a[3],'d','Execution and independence denominators');save(fig,'fig5-deployment-closure')
(O/'phase8c-figure-source-and-bounds.json').write_text(json.dumps({'sources':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [P/'phase8c-core-statistics.json',P/'phase8c-180cell-stress-surface.csv',P/'phase8c-canonical90-stress-subset.csv']},'figures':receipt,'font':str(font),'limits':'Axis bounds verified; semantic overlap requires external rendered-image review.'},indent=2))
