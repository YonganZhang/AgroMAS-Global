"""V12 main Fig. 4 (distribution-rich & phase-shift 2x2: S_N raincloud + LOYO/LORO dumbbell 4a, RMSE x Compliance trajectory + CI forest 4b, 5-breadbasket NUE x S_N shift map 4c, tightened 4d) + Fig. S6."""
import runpy
from pathlib import Path
globals().update(runpy.run_path(str(Path(__file__).with_name('phase8d-plot-style.py'))))
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

variants=['P2-Full64','P2-Static3','P2-Weather','P2-Linear64','P2-ExtraTrees64']
labs=[x.replace('P2-','') for x in variants]
D=pd.read_csv(P/'phase8d-P2-predictive-cohort-strata.csv')
D=D[(D.cohort=='Former-Held-Out')&(D.source=='NASA')]

fig=plt.figure(figsize=(14.4,9.6))
gs=fig.add_gridspec(2,2,width_ratios=[1.08,1.05],height_ratios=[1.0,1.0],hspace=.36,wspace=.28)

# Panel a: Coupled 40-Case Held-Out Realized S_N Rainclouds + LOYO -> LORO Compliance Dumbbell + Public NL
ag_a=gs[0,0].subgridspec(1,2,width_ratios=[1.35,1.02],wspace=.08)
a1=fig.add_subplot(ag_a[0]);a2=fig.add_subplot(ag_a[1])
a1.axvspan(-78,0,facecolor='#F9ECEA',zorder=0)
a1.axvspan(0,40,facecolor='#FFFDF9',zorder=0)
a1.axvspan(40,142,facecolor='#EDF2F7',zorder=0)
a1.axvline(0,color=TEAL_SAGE,ls='--',lw=.8,zorder=1);a1.axvline(40,color=TEAL_SAGE,ls='--',lw=.8,zorder=1)
for i,p in enumerate(variants):
 z_r=cases(p,benchmark='P2',scheme='LORO');z_y=cases(p,benchmark='P2',scheme='LOYO')
 raincloud(a1,z_r.S_N.to_numpy(),i,SLATE_BLUE,vertical=False,width=.28)
 q25,q50,q75=np.quantile(z_y.S_N.to_numpy(),[.25,.50,.75])
 a1.plot([q25,q75],[i+.34,i+.34],color=PINK_MAIN,lw=1.4,zorder=4)
 a1.scatter(q50,i+.34,marker='D',s=26,color=PINK_MAIN,edgecolor='white',lw=.45,zorder=5)
a1.set(xlim=(-78,142),xticks=[-50,0,40,90,130],yticks=range(5),yticklabels=labs,ylim=(4.6,-.65),xlabel='Held-out S_N (kg/ha)')
a1.tick_params(labelsize=7.8);grid(a1,'x');panel(a1,'a')
a1.legend(handles=[Patch(color=SLATE_BLUE,alpha=.55,label='LORO dist.'),
                   Line2D([],[],marker='D',color=PINK_MAIN,lw=1.4,ms=4.8,label='LOYO med/IQR')],
          fontsize=6.3,ncol=2,columnspacing=.7,handletextpad=.3,loc='lower left',bbox_to_anchor=(0,1.02))

start=[val(query(p,benchmark='P2',scheme='LOYO')) for p in variants]
end=[val(query(p,benchmark='P2',scheme='LORO')) for p in variants]
for i,(v,w) in enumerate(zip(start,end)):
 a2.axhspan(i-.45,i+.45,color='#F7F8FA' if i%2==0 else 'white',zorder=0)
 a2.plot([v,w],[i,i],color='#C8D1D7',lw=3.0,zorder=2)
 a2.scatter(v,i,s=42,color=PINK_MAIN,edgecolor='white',lw=.5,zorder=4)
 a2.scatter(w,i,s=40,marker='s',color=SLATE_BLUE,edgecolor='white',lw=.5,zorder=4)
 a2.text((v+w)/2,i-.20,f'{v:.0f}→{w:.0f}%',ha='center',va='bottom',fontsize=6.5)
 pl_y=val(query(variants[i],benchmark='P2',scheme='LOYO',cohort='Public-Reused'))
 pl_r=val(query(variants[i],benchmark='P2',scheme='LORO',cohort='Public-Reused'))
 dx=.8 if abs(pl_y-pl_r)<1 else 0.0
 a2.scatter(pl_y-dx,i+.22,marker='D',s=24,facecolor=ORANGE,edgecolor='black',lw=.55,clip_on=False,zorder=5)
 a2.scatter(pl_r+dx,i+.22,marker='D',s=24,facecolor='white',edgecolor=ORANGE,lw=.95,clip_on=False,zorder=5)
 if pl_y==0:a2.annotate('0%',(pl_y-dx,i+.22),xytext=(7,0),textcoords='offset points',va='center',ha='left',fontsize=6.3)
a2.set(yticks=range(5),yticklabels=[],xlabel='Compliance (%)',xlim=(-5,56),ylim=(4.6,-.65))
a2.tick_params(labelsize=7.8);a2.tick_params(axis='y',length=0);grid(a2,'x')
a2.legend(handles=[Line2D([],[],marker='o',ls='',color=PINK_MAIN,ms=5,label='LOYO'),
                   Line2D([],[],marker='s',ls='',color=SLATE_BLUE,ms=5,label='LORO'),
                   Line2D([],[],marker='D',ls='',color=ORANGE,markeredgecolor='black',ms=4.5,label='NL LY'),
                   Line2D([],[],marker='D',ls='',markerfacecolor='white',markeredgecolor=ORANGE,ms=4.5,label='NL LR')],
          fontsize=6.0,ncol=2,columnspacing=.55,handletextpad=.2,loc='lower left',bbox_to_anchor=(0,1.02))

# Panel b: 2D Generalization Trajectory (Grain N RMSE x Compliance) + Pure 95% CI Contrast Forest Plot
bg_b=gs[0,1].subgridspec(2,1,height_ratios=[1.16,.96],hspace=.44)
b1=fig.add_subplot(bg_b[0]);b2=fig.add_subplot(bg_b[1])
b1.axvspan(19.8,23.5,color='#FFFDF9',zorder=0);b1.axvspan(23.5,29.0,color='#F7F8FA',zorder=0)
b1.axvline(23.5,color=TEAL_SAGE,ls=':',lw=.75,zorder=1)
b1_offs={
 'Full64':(8,4,'LOYO'),
 'Static3':(8,-6,'LORO'),
 'ExtraTrees64':(8,-3,'LORO'),
 'Weather':(-4,-10,'LORO'),
 'Linear64':(-4,6,'LOYO'),
}
for p,lab in zip(variants,labs):
 col=POLICY_COLORS[lab];cy=val(query(p,benchmark='P2',scheme='LOYO'));cr=val(query(p,benchmark='P2',scheme='LORO'))
 ry=float(np.sqrt(D[(D.scheme=='LOYO')&(D.variant==lab)].iloc[0]['Grain_N_MSE_world_equal']))
 rr=float(np.sqrt(D[(D.scheme=='LORO')&(D.variant==lab)].iloc[0]['Grain_N_MSE_world_equal']))
 rp_y=float(np.sqrt(D[(D.scheme=='LOYO')&(D.variant==lab)].iloc[0]['Grain_N_MSE_row_pooled']))
 rp_r=float(np.sqrt(D[(D.scheme=='LORO')&(D.variant==lab)].iloc[0]['Grain_N_MSE_row_pooled']))
 b1.plot([ry,rp_y],[cy,cy],color=col,lw=1.0,alpha=.45,zorder=2)
 b1.plot([rr,rp_r],[cr,cr],color=col,lw=1.0,alpha=.45,zorder=2)
 b1.annotate('',xy=(rr,cr),xytext=(ry,cy),arrowprops=dict(arrowstyle='->',color=col,lw=1.65,shrinkA=4,shrinkB=4),zorder=3)
 b1.scatter(ry,cy,s=48,color=col,edgecolor='white',lw=.6,zorder=4)
 b1.scatter(rr,cr,s=52,marker='D',color=col,edgecolor='black',lw=.65,zorder=4)
 ox,oy,anchor=b1_offs[lab];ax_pt=(ry,cy) if anchor=='LOYO' else (rr,cr)
 b1.annotate(lab,ax_pt,xytext=(ox,oy),textcoords='offset points',fontsize=7.0,
             ha='right' if ox<0 else 'left',va='top' if oy<0 else 'bottom')
b1.set(xlim=(19.8,29.0),ylim=(14.5,33.2),xlabel='World-equal Grain N RMSE (kg/ha) · tick = pooled',ylabel='Compliance (%)')
b1.tick_params(labelsize=7.5);grid(b1,'both');panel(b1,'b')
b1.legend(handles=[Line2D([],[],marker='o',ls='',color=SLATE_DARK,ms=5.2,label='LOYO'),
                   Line2D([],[],marker='D',ls='',color=SLATE_DARK,markeredgecolor='black',ms=5.2,label='LORO'),
                   Line2D([],[],color=SLATE_DARK,lw=1.5,label='Temporal→Spatial shift')],
          fontsize=6.5,ncol=3,loc='lower left',bbox_to_anchor=(0,1.02))

b2.axvspan(-5,5,color='#FFF6EC',alpha=.85,zorder=0);bl=[]
for j,(sc,ref) in enumerate([(sc,rf) for sc in ['LOYO','LORO'] for rf in [variants[1],variants[4]]]):
 q=contrast([ref,'Sensorless','soft'],sc,'P2');v=q['mean_difference']*100;lo,hi=np.array(q['CI95'])*100
 col=PINK_MAIN if sc=='LOYO' else SLATE_BLUE
 b2.errorbar(v,j,xerr=[[v-lo],[hi-v]],fmt='o',color=col,capsize=3.2,lw=1.5,ms=5.0,zorder=4)
 b2.text(v,j+.18,f'{v:+.1f} pp',ha='center',va='bottom',fontsize=7.0)
 bl.append(sc+' − '+ref[3:])
b2.axvline(0,color='black',ls='--',lw=.7);b2.set(yticks=range(4),yticklabels=bl,xlabel='Full64 − reference (pp)',xlim=(-17,23),ylim=(-.6,3.7))
b2.tick_params(labelsize=7.5);grid(b2,'x');b2.text(.97,.92,'Holm p = 1.00',transform=b2.transAxes,ha='right',va='top',fontsize=7.5)

# Panel c: Five-Breadbasket Bivariate (Realized S_N x Apparent NUE) Regional Transfer Phase Map (LOYO -> LORO)
c=fig.add_subplot(gs[1,0])
c.axhspan(.90,1.52,facecolor='#F9ECEA',zorder=0)
c.axhspan(.14,.50,facecolor='#F9ECEA',zorder=0)
c.fill_between([-92,0],.50,.90,facecolor='#FAF6F0',zorder=0)
c.fill_between([40,148],.50,.90,facecolor='#EDF2F7',zorder=0)
c.fill_between([0,40],.50,.90,facecolor='#FFFDF9',edgecolor=TEAL_SAGE,ls='--',lw=1.1,zorder=1)
for xv in [0,40]:c.plot([xv,xv],[.50,.90],color=TEAL_SAGE,ls='--',lw=1.1,zorder=2)
for yv in [.50,.90]:c.plot([0,40],[yv,yv],color=TEAL_SAGE,ls='--',lw=1.1,zorder=2)

z_fy=cases(variants[0],benchmark='P2',scheme='LOYO')
z_fr=cases(variants[0],benchmark='P2',scheme='LORO')
z_sr=cases(variants[1],benchmark='P2',scheme='LORO')
z_er=cases(variants[4],benchmark='P2',scheme='LORO')
c_notes={
 'australia_wa_perth':((12,1.06),'left','bottom','AU 62→38% (adm 38%)'),
 'usa_kansas_wichita':((-86,.56),'left','center','US 56→33% (adm 78%)'),
 'netherlands_lelystad':((62,.80),'left','center','NL 20→20% (adm 80%)'),
 'france_paris_beauce':((-86,1.39),'left','center','FR 11→11% (mining)'),
 'china_ncp_luancheng':((68,.21),'left','center','CN 0→0% (adm 11%)'),
}
for reg,lab,col in zip(REG,RN,REG_COLS):
 qy=z_fy[z_fy.region==reg];qr=z_fr[z_fr.region==reg]
 qs=z_sr[z_sr.region==reg];qe=z_er[z_er.region==reg]
 cov_ellipse(c,qr.S_N,qr.NUE,col,ls='-',lw=1.25,alpha_fill=.10,zorder=2)
 c.scatter(qr.S_N,qr.NUE,s=15,c=col,edgecolors='white',lw=.35,alpha=.55,zorder=3)
 mx_y,my_y=float(qy.S_N.mean()),float(qy.NUE.mean())
 mx_r,my_r=float(qr.S_N.mean()),float(qr.NUE.mean())
 c.annotate('',xy=(mx_r,my_r),xytext=(mx_y,my_y),arrowprops=dict(arrowstyle='->',color=col,lw=1.8,shrinkA=3,shrinkB=3),zorder=4)
 c.scatter(mx_y,my_y,s=48,color=col,edgecolor='white',lw=.6,zorder=5)
 c.scatter(mx_r,my_r,s=56,marker='D',color=col,edgecolor='black',lw=.65,zorder=6)
 c.scatter(float(qs.S_N.mean()),float(qs.NUE.mean()),s=32,marker='^',facecolor='white',edgecolor=col,lw=1.0,zorder=5)
 c.scatter(float(qe.S_N.mean()),float(qe.NUE.mean()),s=30,marker='s',facecolor='white',edgecolor=col,lw=1.0,zorder=5)
 (tx,ty),ha,va,txt=c_notes[reg]
 c.annotate(txt,xy=(mx_r,my_r),xytext=(tx,ty),ha=ha,va=va,fontsize=6.8,
            arrowprops=dict(arrowstyle='-',color=col,lw=.7,alpha=.75),
            bbox={'facecolor':'#FAFBFD','edgecolor':col,'lw':.55,'alpha':.90,'pad':1.6},zorder=7)
c.text(2.5,.52,'Safe box',ha='left',va='bottom',fontsize=6.8,color='#3E6A5C')
c.set(xlim=(-92,148),ylim=(.14,1.48),xlabel='Realized Surplus S_N (kg N/ha)',ylabel='Apparent NUE')
c.tick_params(labelsize=7.8);grid(c,'both');panel(c,'c')
c.legend(handles=[Line2D([],[],marker='o',ls='',color=SLATE_DARK,ms=4.8,label='Full64 LOYO'),
                  Line2D([],[],marker='D',ls='',color=SLATE_DARK,markeredgecolor='black',ms=4.8,label='Full64 LORO'),
                  Line2D([],[],marker='^',ls='',markerfacecolor='white',markeredgecolor=SLATE_DARK,ms=5.0,label='Static3 LR'),
                  Line2D([],[],marker='s',ls='',markerfacecolor='white',markeredgecolor=SLATE_DARK,ms=4.8,label='ET64 LR')],
         fontsize=6.3,ncol=4,columnspacing=.7,handletextpad=.25,loc='lower left',bbox_to_anchor=(0,1.02))

# Panel d: Tightly framed LOYO vs LORO n=40 EUNEP Phase Space with 1-sigma covariance ellipses
d=fig.add_subplot(gs[1,1]);draw_eunep_corridor(d,xlim=(25,248),ylim=(0,300));panel(d,'d')
comp_vars=[variants[0],variants[1],variants[4]]
for sc,col,ls,filled in [('LOYO',PINK_MAIN,'-',True),('LORO',SLATE_BLUE,'--',False)]:
 z_kde=cases(variants[0],benchmark='P2',scheme=sc)
 cov_ellipse(d,z_kde.Grain_N+z_kde.S_N,z_kde.Grain_N,col,ls=ls,lw=1.45,alpha_fill=.12 if filled else .06,zorder=3)
 for p,mk in zip(comp_vars,['o','^','s']):
  zz=cases(p,benchmark='P2',scheme=sc);assert len(zz)==40
  d.scatter(zz.Grain_N+zz.S_N,zz.Grain_N,s=20,marker=mk,facecolor=col if filled else 'none',edgecolor='white' if filled else col,linewidths=.55,alpha=.85,zorder=4)
d.text(.04,.94,'Each model: 1 above 300',transform=d.transAxes,fontsize=6.8)
d.legend(handles=[Line2D([],[],marker=mk,ls='',color=SLATE_DARK,label=p[3:]) for p,mk in zip(comp_vars,['o','^','s'])]+
                 [Line2D([],[],color=PINK_MAIN,lw=1.5,label='LOYO (n=40)'),Line2D([],[],color=SLATE_BLUE,ls='--',lw=1.5,label='LORO (n=40)')],
         fontsize=6.8,loc='lower left',bbox_to_anchor=(0,1.02),ncol=5)

fig.subplots_adjust(left=.06,right=.96,top=.91,bottom=.08)
save(fig,'fig3-p2-transfer','V12 main Fig. 4 (distribution & phase-shift 2x2). Replaced 3 bar tables with S_N raincloud + LOYO/LORO dumbbell (4a), 2D RMSE x Compliance trajectory + CI forest (4b), 5-breadbasket NUE x S_N shift map (4c), and tightened EUNEP frame (4d).')

# Supplementary Fig. S6: Compact 2-panel P2 prior admission bubble matrix & 5x4 Grain N MSE heatmap
fig_s6=plt.figure(figsize=(9.6,4.3))
gs6=fig_s6.add_gridspec(1,2,width_ratios=[1.0,1.15],wspace=.32)
s6a=fig_s6.add_subplot(gs6[0]);s6b=fig_s6.add_subplot(gs6[1])
for j,sc in enumerate(['LOYO','LORO']):
 for i,p in enumerate(variants):
  q=D[(D.scheme==sc)&(D.variant==labs[i])].iloc[0];z=cases(p,benchmark='P2',scheme=sc)
  rates=[100*q.prior_acceptance_rows,100*q.prior_acceptance_world_equal,100*z.prior_accepted.sum()/z.prior_decisions.sum()]
  for k,v in enumerate(rates):
   xx=k+(j-.5)*.32;s6a.scatter(xx,i,s=v*2.8,facecolors=PINK_MAIN if j==0 else 'white',edgecolors=PINK_MAIN if j==0 else SLATE_BLUE,lw=.9,alpha=.80)
   s6a.text(xx,i+.31,f'{v:.0f}',ha='center',fontsize=6.5)
s6a.set(xticks=range(3),xticklabels=['Rows','World','Closed'],yticks=range(5),yticklabels=labs,xlim=(-.55,2.55),ylim=(4.7,-.65),xlabel='Prior admission (%) · LOYO rose / LORO open')
s6a.tick_params(labelsize=8);panel(s6a,'a')

mv=np.array([[D[(D.scheme==sc)&(D.variant==p)].iloc[0]['Grain_N_MSE_'+w] for sc in ['LOYO','LORO'] for w in ['world_equal','row_pooled']] for p in labs])
im=s6b.imshow(mv,cmap=HEATMAP_CMAP,aspect='auto',vmin=420,vmax=800)
s6b.set(xticks=range(4),xticklabels=['LY W','LY R','LR W','LR R'],yticks=range(5),yticklabels=labs,ylim=(4.6,-.65),xlabel='Grain N MSE ((kg N/ha)²) · LY/LR · W/R')
s6b.tick_params(labelsize=7.5);panel(s6b,'b')
for i in range(5):
 for j in range(4):
  contrast_label(s6b,j,i,f'{mv[i,j]:.0f}',im.cmap(im.norm(mv[i,j])),ha='center',va='center',fontsize=7.2)
cb=fig_s6.colorbar(im,ax=s6b,fraction=.046,pad=.03);cb.set_label('MSE ((kg/ha)²)',fontsize=8)
fig_s6.subplots_adjust(left=.10,right=.94,top=.90,bottom=.16)
save(fig_s6,'figs6-p2-admission-mse','V11 Supplementary Fig. S6 (2-panel compact appendix). Prior admission bubble matrix (a) and 5x4 Grain N MSE matrix (b).')
