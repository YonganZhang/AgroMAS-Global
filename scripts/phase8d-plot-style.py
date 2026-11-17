"""Read-only Phase8D plotting contract, unified Rose-Slate tokens and frozen-source registry."""
from pathlib import Path
import json,hashlib,importlib.util,subprocess
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap,TwoSlopeNorm
from scipy.stats import gaussian_kde

R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';O=P/'figures'
PRIMARY=Path('/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体')
assert R==Path.cwd().resolve(),(R,Path.cwd())
assert O==R/'reports/phase8/figures'

STYLE=Path('/mnt/data/yongan-admin-2/.ai-shared/skills/share-sci-plot/references/fpv_v16_muted_style.py')
spec=importlib.util.spec_from_file_location('fpv_style',STYLE);sty=importlib.util.module_from_spec(spec);spec.loader.exec_module(sty)

# Canonical 10-Color Rose-Slate + Harmonized Warm-Orange / Soft-Pink / Teal-Sage Accent Tokens
PAL=sty.PALETTE_SCI_ROSE_SLATE_10
NAVY='#162830';SLATE_DARK='#4C7A99';BLUE='#5B88A8';ICE='#A4BED1';SAGE='#639A88'
PLUM='#947EB0';CREAM='#FFF0C4';BLUSH='#E8B8AE';PINK='#E07A84';ROSE='#B8525A'
ORANGE='#E8985E';PINK_MAIN='#E07A84';SLATE_BLUE='#5B88A8';PLUM_SOFT='#947EB0';TEAL_SAGE='#639A88'
GREY='#C8D1D7';SLATE_GREY='#7E8D96'

POLICY_COLORS={
 'Soft-Coupled':PINK_MAIN,'Soft':PINK_MAIN,'TreeMLP':PINK_MAIN,'Full64':PINK_MAIN,'P2-Full64':PINK_MAIN,
 'SensorlessPPO':SLATE_BLUE,'PPO':SLATE_BLUE,'Static3':SLATE_BLUE,'P2-Static3':SLATE_BLUE,
 'DVS-N2':TEAL_SAGE,'DVS · Full':TEAL_SAGE,'DVS':TEAL_SAGE,
 'Tier2':PLUM_SOFT,'Tier2-Composite':PLUM_SOFT,'ExtraTrees':PLUM_SOFT,'TreeExtraTrees':PLUM_SOFT,'ExtraTrees64':PLUM_SOFT,'P2-ExtraTrees64':PLUM_SOFT,
 'Weather':SLATE_DARK,'TreeWeather':SLATE_DARK,'P2-Weather':SLATE_DARK,
 'Linear':ICE,'TreeLinear':ICE,'Linear64':ICE,'P2-Linear64':ICE,
 'Legacy · Full':PLUM_SOFT,'LegacyV6Full':PLUM_SOFT,
 'Open-loop':ORANGE,'Greedy':ICE,
 'Archived bare':SLATE_GREY,'Bare':SLATE_GREY,'No-climate':SLATE_BLUE,'remove-eco':SLATE_BLUE,
}
CLIMATE_COLORS={'Historical':SLATE_BLUE,'idealized_mid':ORANGE,'idealized_high':PINK_MAIN,'+1.8°C':ORANGE,'+3.5°C':PINK_MAIN}
CL_COLS=[SLATE_BLUE,ORANGE,PINK_MAIN]
REG_COLS=[PINK_MAIN,SLATE_BLUE,TEAL_SAGE,PLUM_SOFT,ORANGE]  # AU, US, NL, FR, CN
HEATMAP_STOPS=['#6A90B0','#A4BED1','#FFF0C4','#F4C8AE','#E07A84','#B8525A']
HEATMAP_CMAP=LinearSegmentedColormap.from_list('sci_rose_slate_6',list(zip([0,.22,.50,.68,.84,1.0],HEATMAP_STOPS)),N=256)
SCORE_CMAP=LinearSegmentedColormap.from_list('sci_score_soft',['#FAFBFD','#A4BED1','#FFF0C4','#F4C8AE','#E07A84'],N=256)

for name in ['Times New Roman','Times New Roman:style=Bold','Times New Roman:style=Italic']:
 font_manager.fontManager.addfont(subprocess.check_output(['fc-match','-f','%{file}',name],text=True))
plt.rcParams.update({
 'font.family':'Times New Roman','font.size':11,'font.weight':'normal','axes.labelweight':'normal',
 'mathtext.fontset':'custom','mathtext.cal':'Times New Roman','mathtext.sf':'Times New Roman',
 'mathtext.tt':'Times New Roman','mathtext.fallback':None,'mathtext.rm':'Times New Roman',
 'mathtext.it':'Times New Roman:italic','mathtext.bf':'Times New Roman:bold',
 'text.color':'#000000','axes.labelcolor':'#000000','xtick.color':'#000000','ytick.color':'#000000',
 'axes.edgecolor':'#000000','axes.titleweight':'normal','axes.spines.top':False,'axes.spines.right':False,
 'axes.linewidth':.75,'xtick.major.width':.65,'ytick.major.width':.65,'legend.frameon':False,'legend.fontsize':9,
 'svg.fonttype':'none','pdf.fonttype':42,'figure.facecolor':'white'
})

S=json.loads((P/'phase8d-core-statistics.json').read_text());ROWS=S['summary']
REG=['australia_wa_perth','usa_kansas_wichita','netherlands_lelystad','france_paris_beauce','china_ncp_luancheng']
RN=['AU','US','NL','FR','CN'];TRACKS=['Sensorless','Full-Telemetry'];TC=[PINK_MAIN,SLATE_BLUE]
CL=['Historical','idealized_mid','idealized_high'];CLABS=['Historical','+1.8°C','+3.5°C']
SOURCES=['reports/phase8/'+x for x in [
 'phase8d-core-statistics.json','phase8d-G1-verdict.json','phase8d-full-TRAIN-physical-decoding.json',
 'phase8d-180cell-stress-surface.csv','phase8d-closeout-receipt.json','phase8d-primary-verification.json',
 'phase8d-P2-predictive-cohort-strata.csv','phase8d-case-metrics-seed-averaged.csv',
 'phase8d-G1-radius-interpretation.json','phase8d-root-cause-verification.json'
]]+['manuscript/phase8/all-summary-groups.csv']

def hashes():
 return {p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in SOURCES}

def query(policy='TreeMLP',mode='soft',track='Sensorless',climate='Historical',cap=40,price_multiplier=1,subsidy=0,benchmark='P1',cohort='Former-Held-Out',scheme='none'):
 f=locals();q=[x for x in ROWS if x['source']=='NASA' and x['tax']==0 and all(x[k]==v for k,v in f.items())];assert len(q)<=1,(f,len(q))
 if not q:
  allowed=(policy=='TreeMLP' and mode=='hard-bare-tier2' and price_multiplier==2) or (cap==50 and (track=='Full-Telemetry' or policy=='remove-eco')) or (policy=='remove-econ' and climate in CL[1:] and cap==40 and subsidy==50)
  assert allowed,('Required configuration missing',f)
 return q[0] if q else None

def val(x,k='joint'):
 return np.nan if x is None else x['region_equal'][k]*(100 if k in ['joint','NUE_gt_090'] else 1)

def panel(ax,letter):
 ax.text(-.10,1.025,letter,transform=ax.transAxes,fontsize=16,fontweight='bold',va='bottom')

def grid(ax,axis='x'):
 ax.set_axisbelow(True);ax.grid(axis=axis,color='#E8ECEF',lw=.55)

def save(fig,name,notes):
 """Run figure standards normalization, caption guard, font enforcement and 450 DPI multi-format export."""
 for main,top,right in getattr(fig,'_joint_groups',[]):
  fig.canvas.draw()
  box=main.get_position();tb=top.get_position();rb=right.get_position()
  top.set_position([box.x0,tb.y0,box.width,tb.height])
  right.set_position([box.x1+.005,box.y0,rb.width,box.height])
 fspec=importlib.util.spec_from_file_location('font_normalizer','/mnt/data/yongan-admin-2/.ai-shared/skills/share-sci-plot/scripts/figure_standards.py')
 fn=importlib.util.module_from_spec(fspec);fspec.loader.exec_module(fn);fn.normalize_fonts(fig)
 cspec=importlib.util.spec_from_file_location('caption_guard','/mnt/data/yongan-admin-2/.ai-shared/skills/share-sci-plot/references/figure_standards.py')
 cg=importlib.util.module_from_spec(cspec);cspec.loader.exec_module(cg);cg.assert_no_caption_text(fig,max_words=18)
 plt.rcParams.update({
  'mathtext.fontset':'custom','mathtext.rm':'Times New Roman','mathtext.it':'Times New Roman:italic',
  'mathtext.bf':'Times New Roman:bold','mathtext.cal':'Times New Roman','mathtext.sf':'Times New Roman',
  'mathtext.tt':'Times New Roman','mathtext.fallback':None,'axes.unicode_minus':True
 })
 from matplotlib.text import Text
 for ax in fig.axes:
  assert not any(ax.get_title(loc=k) for k in ['left','center','right'])
  for spine in ax.spines.values():spine.set_edgecolor('#000000')
 for t in fig.findobj(Text):
  t.set_fontfamily('Times New Roman')
  if t.get_gid() not in {'contrast_white','callout_badge'}:t.set_color('#000000')
  if t.get_text() not in list('abcdefgh'):t.set_fontweight('normal')
 assert fig._suptitle is None
 fig.canvas.draw();ren=fig.canvas.get_renderer()
 bounds=[list(map(float,a.get_tightbbox(ren).bounds)) for a in fig.axes]
 for ext in ['png','pdf','svg']:
  fig.savefig(O/(name+'.'+ext),dpi=450,facecolor='white',bbox_inches='tight',pad_inches=.06)
 fp=O/(name+'-render-audit.json')
 fp.write_text(json.dumps({
  'figure':name,'sources':hashes(),'palette':PAL,'font':'Times New Roman','black_regular_text':True,
  'contrast_labels':[{'text':t.get_text(),'background':list(t._contrast_background)} for t in fig.findobj(Text) if t.get_gid()=='contrast_white'],
  'descriptive_titles':False,'axes_count':len(fig.axes),'axes_bounds':bounds,'notes':notes,
  'runtime_paths':{'cwd':str(Path.cwd()),'style_file':str(Path(__file__).resolve()),'figure_output':str(O)}
 },indent=2))
 plt.close(fig)

def metric_columns(ax,q,y,x=1.02):
 ax.text(x,1.015,'NUE     S_N',transform=ax.transAxes,fontsize=9,ha='left')
 for row,yy in zip(q,y):
  if row:ax.text(x,yy,f"{val(row,'NUE'):5.2f}   {val(row,'S_N'):6.1f}",transform=ax.get_yaxis_transform(),va='center',fontsize=8.8)

# Frozen case-level joins are used only for matched descriptive figure diagnostics.
CASES=pd.read_csv(P/'phase8d-case-metrics-seed-averaged.csv')

def cases(policy='TreeMLP',mode='soft',track='Sensorless',**kw):
 defaults=dict(source='NASA',cohort='Former-Held-Out',scheme='none',climate='Historical',cap=40,price_multiplier=1,subsidy=0,tax=0,benchmark='P1',policy=policy,mode=mode,track=track)
 defaults.update(kw);mask=np.ones(len(CASES),dtype=bool)
 for k,v in defaults.items():mask &= CASES[k].eq(v)
 return CASES[mask].copy()

def contrast(reference,scheme='none',benchmark='P1'):
 q=[x for x in S['contrasts'] if x['source']=='NASA' and x['cohort']=='Former-Held-Out' and x['scheme']==scheme and x['benchmark']==benchmark and x['climate']=='Historical' and x['cap']==40 and x['price_multiplier']==1 and x['subsidy']==0 and x['tax']==0 and x['region']=='GLOBAL_EQUAL5' and x['metric']=='joint' and x['primary']==(['P2-Full64','Sensorless','soft'] if benchmark=='P2' else ['TreeMLP','Sensorless','soft']) and x['reference']==reference]
 assert len(q)==1,len(q);return q[0]

def bar_values(ax,bars,fmt='{:.1f}',horizontal=False,size=7,pad=2):
 for rect in bars:
  v=rect.get_width() if horizontal else rect.get_height()
  if np.isfinite(v):
   ax.annotate(fmt.format(v),(v,rect.get_y()+rect.get_height()/2) if horizontal else (rect.get_x()+rect.get_width()/2,v),
               xytext=(pad,0) if horizontal else (0,pad),textcoords='offset points',
               ha='left' if horizontal else 'center',va='center' if horizontal else 'bottom',fontsize=size)

text_color=sty.text_color
contrast_text=sty.contrast_text

def contrast_label(ax,x,y,label,bg,**kw):
 color=contrast_text(bg);t=ax.text(x,y,label,color=color,**kw)
 if color in ['white','#FFFFFF','#ffffff']:
  t.set_gid('contrast_white');t._contrast_background=matplotlib.colors.to_rgba(bg)
 return t

def callout_badge(ax,x,y,label,col=ROSE,**kw):
 """Place a compact semantic callout badge colored with WCAG >= 4.5 darkened hue."""
 dark_col=text_color(col)
 box_kw=kw.pop('bbox',{'facecolor':'#FAFBFD','edgecolor':col,'alpha':0.92,'lw':0.65,'pad':2.5})
 t=ax.text(x,y,label,color=dark_col,bbox=box_kw,**kw)
 t.set_gid('callout_badge')
 return t

def draw_eunep_corridor(ax,cap=40,xlim=(0,300),ylim=(0,300),kde_bg=None,kde_color=ROSE,penalty=False):
 """Render exact polygon-filled EUNEP safe corridor, violation fields and unmasked KDE density."""
 x=np.linspace(*xlim,240); y=np.linspace(*ylim,240); X,Y=np.meshgrid(x,y)
 # Base fill: Soft Blush-Rose outside NUE [0.50, 0.90]
 ax.axhspan(ylim[0],ylim[1],facecolor='#F9ECEA',zorder=0)
 # Surplus > cap region inside [0.50x, 0.90x] in Soft Ice-Slate
 y_low_50=.50*x; y_high_90=np.minimum(.90*x, ylim[1])
 y_sur=np.maximum(x-cap, .50*x)
 y_sur_top=np.minimum(y_sur, y_high_90)
 ax.fill_between(x,y_low_50,y_sur_top,where=y_sur_top>y_low_50,facecolor='#EDF2F7',edgecolor='none',zorder=0)
 # EUNEP Safe Target Wedge in crisp Warm Ivory-White
 y_safe_bot=np.maximum(.50*x, x-cap)
 y_safe_top=np.minimum(.90*x, ylim[1])
 ax.fill_between(x,y_safe_bot,y_safe_top,where=y_safe_top>y_safe_bot,facecolor='#FFFDF9',edgecolor='none',zorder=1)
 if penalty:
  ratio=np.divide(Y,X,out=np.zeros_like(Y),where=X>0); sur=X-Y
  safe=(ratio>=.5)&(ratio<=.9)&(sur>=0)&(sur<=cap)
  violation=np.maximum.reduce([np.maximum(.5*X-Y,0),np.maximum(Y-.9*X,0),np.maximum(sur-cap,0)])
  cmap,norm,_=sty.continuous_scale([0,15,40,80,140,300],anchors=sty.MAP_ANCHORS_ROSE_SLATE_6)
  ax.pcolormesh(X,Y,np.ma.masked_where(safe,violation),cmap=cmap,norm=norm,alpha=.28,shading='auto',rasterized=True,zorder=1)
  ax.fill_between(x,y_safe_bot,y_safe_top,where=y_safe_top>y_safe_bot,facecolor='#FFFDF9',edgecolor='none',zorder=1)
 # Crisp boundary lines
 for slope in [.5,.9]:
  ax.plot(x,slope*x,'--',color=SAGE,lw=.90,zorder=2)
 for k in ([25,35,40,50] if penalty else [cap]):
  ax.plot(x,x-k,'--' if k==cap else ':',color=SAGE if k==cap else SLATE_GREY,lw=.85 if k==cap else .55,zorder=2)
 if kde_bg is not None and len(kde_bg)>3:
  nin=kde_bg.Grain_N+kde_bg.S_N;nout=kde_bg.Grain_N
  points=np.array([nin,nout]);points+=np.random.default_rng(17).normal(0,.04,points.shape)
  density=gaussian_kde(points)(np.vstack([X.ravel(),Y.ravel()])).reshape(X.shape)
  lv=np.linspace(density.max()*.14,density.max(),5)
  ax.contourf(X,Y,density,levels=lv,colors=[kde_color],alpha=.20,zorder=2)
  ax.contour(X,Y,density,levels=lv[:-1],colors=[kde_color],linewidths=.65,alpha=.62,zorder=2)
 ax.set(xlim=xlim,ylim=ylim,xlabel='N input (kg N/ha)',ylabel='Grain N (kg N/ha)');ax.tick_params(labelsize=8)

def phase_points(ax,z,col=ROSE,marker='o',label=None):
 ax.scatter(z.Grain_N+z.S_N,z.Grain_N,s=20,c=col,marker=marker,edgecolors='white',linewidths=.42,alpha=.85,label=label,zorder=4)
 upper=ax.get_ylim()[1];above=int((z.Grain_N>upper).sum())
 if above:
  msg=(label+': ' if label else '')+f'{above} above {upper:g}'
  if hasattr(ax,'_overflow_note'):ax._overflow_note.set_text(ax._overflow_note.get_text()+'\n'+msg)
  else:ax._overflow_note=ax.text(.98,.98,msg,transform=ax.transAxes,ha='right',va='top',fontsize=6.5)

def cov_ellipse(ax,x,y,col,ls='-',lw=1.35,alpha_fill=.10,zorder=3):
 """Draw a 1-sigma covariance ellipse (or 1D error bar when one axis is constant)."""
 from matplotlib.patches import Ellipse
 x=np.asarray(x,float);y=np.asarray(y,float);mx,my=float(np.mean(x)),float(np.mean(y))
 sx,sy=float(np.std(x,ddof=1)) if len(x)>1 else 0.0,float(np.std(y,ddof=1)) if len(y)>1 else 0.0
 if len(x)>2 and sx>1e-8 and sy>1e-8:
  vals,vecs=np.linalg.eigh(np.cov(x,y));vals=np.maximum(vals,1e-9)
  ang=np.degrees(np.arctan2(vecs[1,1],vecs[0,1]))
  w,h=2.0*np.sqrt(vals[1]),2.0*np.sqrt(vals[0])
  ax.add_patch(Ellipse((mx,my),w,h,angle=ang,facecolor=col,edgecolor='none',alpha=alpha_fill,zorder=zorder))
  ax.add_patch(Ellipse((mx,my),w,h,angle=ang,facecolor='none',edgecolor=col,ls=ls,lw=lw,zorder=zorder+.5))
 elif sy>1e-8:
  ax.errorbar(mx,my,yerr=sy,fmt='none',ecolor=col,elinewidth=lw+.2,capsize=3.2,capthick=lw,zorder=zorder+.5)
 elif sx>1e-8:
  ax.errorbar(mx,my,xerr=sx,fmt='none',ecolor=col,elinewidth=lw+.2,capsize=3.2,capthick=lw,zorder=zorder+.5)

def dumbbell(ax,starts,ends,labels,cols=None,xlabel='',fmt='.1f'):
 cols=cols or [ROSE]*len(labels)
 for i,(v,w,c) in enumerate(zip(starts,ends,cols)):
  ax.plot([v,w],[i,i],color=GREY,lw=3);ax.scatter(v,i,s=35,facecolor='white',edgecolor=c,zorder=3);ax.scatter(w,i,s=35,color=c,zorder=3)
 ax.set(yticks=range(len(labels)),yticklabels=labels,xlabel=xlabel);ax.invert_yaxis();grid(ax)

def bootstrap_joint(z):
 rng=np.random.default_rng(20261115);groups=[v.joint.to_numpy() for _,v in z.groupby('region')]
 means=np.array([np.mean([rng.choice(v,len(v),replace=True).mean() for v in groups]) for _ in range(5000)])*100
 return np.quantile(means,[.025,.975])

def raincloud(ax,values,pos,color,vertical=True,width=.32):
 v=np.asarray(values,dtype=float);v=v[np.isfinite(v)];assert len(v)>0
 if len(v)>2 and np.std(v)>1e-9:
  xx=np.linspace(v.min(),v.max(),180);dd=gaussian_kde(v)(xx);dd=dd/dd.max()*width
  if vertical:ax.fill_betweenx(xx,pos-.12-dd,pos-.12,color=color,alpha=.35,lw=.6,edgecolor=color)
  else:ax.fill_between(xx,pos-.12-dd,pos-.12,color=color,alpha=.35,lw=.6,edgecolor=color)
 kw=dict(positions=[pos],widths=.10,showfliers=False,patch_artist=True,boxprops={'facecolor':'white','edgecolor':color,'linewidth':.85},medianprops={'color':'black','linewidth':1.0},whiskerprops={'color':color},capprops={'color':color})
 ax.boxplot([v],vert=vertical,**kw);jj=np.random.default_rng(71).uniform(.10,.30,len(v))
 if vertical:ax.scatter(pos+jj,v,s=8,color=color,alpha=.45,linewidths=0)
 else:ax.scatter(v,pos+jj,s=8,color=color,alpha=.45,linewidths=0)

def joint_axes(fig,slot,z,penalty=False,marginals=None,kde_color=ROSE):
 g=slot.subgridspec(2,2,width_ratios=[5.2,1],height_ratios=[1,5.2],hspace=.05,wspace=.05)
 ax=fig.add_subplot(g[1,0]);top=fig.add_subplot(g[0,0],sharex=ax);right=fig.add_subplot(g[1,1],sharey=ax)
 draw_eunep_corridor(ax,kde_bg=None if penalty else z,kde_color=kde_color,penalty=penalty)
 groups=marginals if marginals is not None else [(z[z.region==reg],lab,col) for reg,lab,col in zip(REG,RN,REG_COLS)]
 for q,lab,col in groups:
  if len(q)>2:
   for aa,v,hor in [(top,q.Grain_N+q.S_N,True),(right,q.Grain_N,False)]:
    xx=np.linspace(0,300,200)
    if np.std(v)>1e-8:
     dd=gaussian_kde(v)(xx)
     if hor:aa.plot(xx,dd,color=col,lw=1.0,label=lab);aa.fill_between(xx,0,dd,color=col,alpha=.12)
     else:aa.plot(dd,xx,color=col,lw=1.0);aa.fill_betweenx(xx,0,dd,color=col,alpha=.12)
 top.axis('off');right.axis('off')
 if not hasattr(fig,'_joint_groups'):fig._joint_groups=[]
 fig._joint_groups.append((ax,top,right));return ax,top,right

def native_selection():
 n=pd.read_csv(P/'phase8d-native-episode-metrics.csv',low_memory=False)
 return n[(n.source=='NASA')&(n.cohort=='Former-Held-Out')&(n.benchmark=='P1')&(n.climate=='Historical')&(n.cap==40)&(n.price_multiplier==1)&(n.subsidy==0)&(n.tax==0)]

def native_case(pol='TreeMLP',mode='soft',track='Sensorless',region=REG[2],year=2020):
 n=native_selection();q=n[(n.policy==pol)&(n['mode']==mode)&(n.track==track)&(n.region==region)&(n.year==year)].sort_values('episode_id');assert len(q)
 r=q.iloc[0];p=PRIMARY/'data/phase8d-evaluation'/r.episode_id/'result.json';assert hashlib.sha256(p.read_bytes()).hexdigest()==r.episode_sha256
 d=json.loads(p.read_text());df=pd.DataFrame(d['mass_audit']['daily_records']);df['day']=pd.to_datetime(df.date);return d,df,p

def eras(ax):
 """Clean neutral study-era background bands with subtle dashed era dividers."""
 for lo,hi in [(1980,1994.5),(2009.5,2014.5)]:
  ax.axvspan(lo,hi,color='#EEF1F5',alpha=.60,zorder=0)
 for div in [1994.5,2009.5,2014.5]:
  ax.axvline(div,color='#9AA6AC',ls='--',lw=.60,zorder=1)

def long_context():
 import gzip
 dest=O/'phase8d-cea-v6-long-context.json'
 if dest.exists():
  cached=json.loads(dest.read_text())
  for path,digest in cached['source_sha256'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
  baseline=cached['physical_zero_split_baseline'];assert len(baseline)==100 and set(v['year'] for v in baseline)==set(range(1995,2015));assert all(v['role']==('Train' if v['year']<=2009 else 'Dev') for v in baseline)
  return cached
 sources={};climate={};baseline=[]
 for reg in REG:
  p=PRIMARY/'data/global_regions'/reg/'nasa-power-19840101-20261101.json';sources[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
  raw=json.loads(p.read_text())['properties']['parameter'];df=pd.DataFrame(raw);df.index=pd.to_datetime(df.index)
  temp=(df.T2M_MIN+df.T2M_MAX)/2;temp=temp.where((df.T2M_MIN>-900)&(df.T2M_MAX>-900))
  annual=temp[temp.index.month<=10].groupby(temp[temp.index.month<=10].index.year).mean();annual=annual-annual.loc[1984:1994].mean()
  climate[reg]={str(k):float(v) for k,v in annual.items()}
 for p in sorted((PRIMARY/'data/phase8-physical-books').glob('*Historical*.jsonl.gz')):
  sources[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
  with gzip.open(p,'rt') as f:d=json.loads(next(f))
  assert d['plan']==[0,0,0],(p,d['plan']);assert 1995<=d['harvest_year']<=2014 and d['role']==('Train' if d['harvest_year']<=2009 else 'Dev'),(p,d['role'])
  baseline.append({'role':d['role'],'region':d['region_id'],'year':d['harvest_year'],'NUE':d['outcome'][3],'S_N':d['outcome'][2],'initial_N_t_ha':sum(d['initial_stock_ledger']['organic_N_kg_ha'])/1000})
 helper=PRIMARY/'NUE_PCSE-Gym/pcse_gym/utils/nitrogen_helpers.py';txt=helper.read_text();assert 'NO3 = 538.868 - 0.264 * year' in txt and 'NH4 = 697 - 0.339 * year' in txt
 sources[str(helper)]=hashlib.sha256(helper.read_bytes()).hexdigest()
 out={'climate':climate,'physical_zero_split_baseline':baseline,'source_sha256':sources,'climate_definition':'NASA POWER Jan-Oct mean temperature anomaly relative to 1984-1994, fixed window all years; not crop-specific growing season','baseline_definition':'First archived zero-split plan [0,0,0] per Historical Train/Dev book; descriptive reference, not a fitted policy or continuous policy evaluation','deposition_definition':'NL CLO trend implemented in nitrogen_helpers.py; annual empirical parameterization, not regional observations'}
 dest.write_text(json.dumps(out,indent=2));return out

def annual_trajectory(ax,metric,context=None,draw_eras=True):
 context=context or long_context();base=pd.DataFrame(context['physical_zero_split_baseline']);g=base.groupby('year')[metric];yy=g.mean()
 ax.plot(yy.index,yy,'o-',color=SLATE_GREY,ms=2.2,lw=1.0,label='Zero-split reference');ax.fill_between(yy.index,g.quantile(.25),g.quantile(.75),color=GREY,alpha=.28)
 for mode,col,lab in [('soft',ROSE,'Soft'),('hard-bare-tier2',SLATE_DARK,'Bare')]:
  q=cases(mode=mode).groupby('year')[metric];v=q.mean();ax.plot(v.index,v,'o-',color=col,ms=2.4,lw=1.2,label=lab);ax.fill_between(v.index,q.quantile(.25),q.quantile(.75),color=col,alpha=.14)
 if draw_eras:eras(ax)
 ax.set_xlim(1995,2026);ax.tick_params(labelsize=7.5)
