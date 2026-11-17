"""Publication G1 quantitative panels from immutable source JSON, no hand entries."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager,colors
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';OUT=P/'figures';OUT.mkdir(exist_ok=True)
font=Path(subprocess.check_output(['fc-match','-f','%{file}','Times New Roman'],text=True));font_manager.fontManager.addfont(str(font));assert font_manager.FontProperties(fname=str(font)).get_name()=='Times New Roman'
plt.rcParams.update({'font.family':'Times New Roman','mathtext.fontset':'stix','font.size':11,'axes.labelcolor':'#000000','text.color':'#000000','xtick.color':'#000000','ytick.color':'#000000','axes.edgecolor':'#000000','axes.labelweight':'normal','font.weight':'normal','svg.fonttype':'none','pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
source=P/'phase8b-G1-verdict.json';decode=P/'phase8b-full-TRAIN-physical-decoding.json';g=json.loads(source.read_text())['results'];d=json.loads(decode.read_text())['results'];tracks=['Full-Telemetry','Sensorless'];palette=['#6A90B0','#B8525A'];caps=[25,35,40,50];fig,axes=plt.subplots(2,3,figsize=(13.2,8.0),layout='constrained');ax=axes.ravel();data={}
for track,color in zip(tracks,palette):
 v=g[track+'-mlp'];x=np.arange(4)
 a=[v['caps'][str(c)]['BSS_vs_ExtraTrees'] for c in caps];b=[v['caps'][str(c)]['additional_events']['joint_surplus_and_NUE']['BSS_vs_ExtraTrees'] for c in caps]
 ax[0].plot(x,a,'o-',color=color,label=track);ax[1].plot(x,b,'o-',color=color,label=track);data[track]=dict(upper_surplus_BSS=a,joint_BSS=b)
for a in ax[:2]:a.set_xticks(np.arange(4),caps);a.set_xlabel('Surplus cap (kg N ha$^{-1}$)');a.set_ylabel('Brier skill against ExtraTrees');a.axhline(0,color='#000000',lw=.7);a.legend(frameon=False,fontsize=9,loc='upper left')
regions=['australia_wa_perth','china_ncp_luancheng','france_paris_beauce','netherlands_lelystad','usa_kansas_wichita'];names=['AU','CN','FR','NL','US'];x=np.arange(6)
for j,(track,color) in enumerate(zip(tracks,palette)):
 v=g[track+'-mlp'];values=[v['Dev_crossyear_macro_90pct_coverage']]+[v['by_region'][r]['crossyear_coverage'] for r in regions];ax[2].plot(x,100*np.array(values),'o-' if j==0 else 's--',color=color,label=track);data[track]['coverage']=values
ax[2].axhspan(85,95,color='#D9E4D7',alpha=.6,label='Macro gate');ax[2].set_xticks(x,['Macro']+names);ax[2].set_ylim(50,103);ax[2].set_ylabel('Cross-year coverage (%)');ax[2].legend(frameon=False,fontsize=9)
for j,(track,color) in enumerate(zip(tracks,palette)):
 v=g[track+'-mlp'];vals=[v['partial_profit_ranking_regret_EUR_ha'],v['ExtraTrees_regret_EUR_ha']];ax[3].bar(np.arange(2)+(j-.5)*.32,vals,.32,color=color,label=track);data[track]['regret']=vals
ax[3].set_xticks([0,1],['Neural model','ExtraTrees']);ax[3].set_ylabel('Ranking regret (EUR ha$^{-1}$)');ax[3].legend(frameon=False,fontsize=9)
targets=['final_organic_N_kg_ha','final_mineral_N_kg_ha','native_Nloss_kg_ha','final_soil_C_kg_ha','native_net_mineralization_N_kg_ha'];labels=['Organic N','Mineral N','Native N loss','Soil C','Net mineralization'];x=np.arange(len(targets));offsets=[-.27,-.09,.09,.27];idx=0
for track,color in zip(tracks,palette):
 for kind,alpha in [('latent_OOF_R2',1.),('raw_OOF_R2',.4)]:
  values=[d[track+'-mlp']['targets'][t][kind] for t in targets];ax[4].bar(x+offsets[idx],values,.18,color=color,alpha=alpha,label=track+(' latent' if kind.startswith('latent') else ' raw'));idx+=1
ax[4].set_xticks(x,labels,rotation=28,ha='right');ax[4].set_ylim(0,1.05);ax[4].set_ylabel('Pooled TRAIN decoding $R^2$');ax[4].legend(frameon=False,fontsize=8,ncol=2,loc='lower center',bbox_to_anchor=(.5,1.02))
values=np.array([[d[t+'-mlp']['by_region'][r]['native_Nloss_kg_ha'] for r in regions] for t in tracks]);data['within_region_native_Nloss_R2']=values.tolist();cmap=colors.LinearSegmentedColormap.from_list('qualified',['#6A90B0','#FFFFFF','#B8525A']);norm=colors.SymLogNorm(linthresh=.1,vmin=-100,vmax=100,base=10);im=ax[5].imshow(values,cmap=cmap,norm=norm,aspect='auto');ax[5].set_xticks(np.arange(5),names);ax[5].set_yticks([0,1],tracks);ax[5].set_xlabel('Within-region native N loss decoding')
for (i,j),value in np.ndenumerate(values):ax[5].text(j,i,f'{value:.3f}',ha='center',va='center',fontsize=10,color='#000000')
cb=fig.colorbar(im,ax=ax[5],shrink=.75,ticks=[-100,-10,-1,-.1,0,.1,1,10,100]);cb.set_label('$R^2$')
for letter,a in zip('abcdef',ax):a.text(-.12,1.03,letter,transform=a.transAxes,fontweight='bold',fontsize=14,va='bottom');a.tick_params(labelsize=10)
fig.savefig(OUT/'fig2-g1.png',dpi=450,facecolor='white');fig.savefig(OUT/'fig2-g1.svg',facecolor='white');fig.savefig(OUT/'fig2-g1.pdf',facecolor='white');plt.close(fig)
(OUT/'fig2-g1-source.json').write_text(json.dumps(dict(sources={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,decode)},values=data,font=str(font),scope='MLP first registered architecture;G1 literal upper-surplus event;retrospective crossyear diagnostic;TRAIN decoding associations,not physical identification'),indent=2))
