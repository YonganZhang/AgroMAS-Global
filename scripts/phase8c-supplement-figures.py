from pathlib import Path
import json,runpy
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import subprocess
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';S=json.loads((P/'phase8c-core-statistics.json').read_text());O=P/'figures'
font_manager.fontManager.addfont(subprocess.check_output(['fc-match','-f','%{file}','Times New Roman'],text=True));plt.rcParams.update({'font.family':'Times New Roman','font.size':13,'svg.fonttype':'none','pdf.fonttype':42})
base=[x for x in S['summary'] if x['benchmark']=='P1' and x['cohort']=='Former-Held-Out' and x['climate']=='Historical' and x['cap']==40 and x['price_multiplier']==1 and x['subsidy']==0 and x['track']=='Sensorless']
fig,a=plt.subplots(2,2,figsize=(12,8),layout='constrained')
for axis,pols,modes,title in [(a[0,0],['TreeMLP','TreeExtraTrees','TreeLinear','TreeWeather'],['soft'],'Response-model ablation'),(a[0,1],['TreeMLP'],['soft','tree','open-loop','greedy-frozen','hard-bare-tier2'],'Planning and objective ablation')]:
 q=[x for x in base if x['policy'] in pols and x['mode'] in modes];axis.bar(range(len(q)),[100*x['region_equal']['joint'] for x in q],color='#6A90B0');axis.set_xticks(range(len(q)),[x['policy'].replace('Tree','') if len(pols)>1 else x['mode'] for x in q],rotation=20,ha='right');axis.set_title(title);axis.set_ylabel('Joint compliance (%)')
q=[x for x in base if x['policy'] in ['TreeMLP','remove-climate','remove-eco'] and x['mode']=='soft'];a[1,0].bar(range(len(q)),[100*x['region_equal']['joint'] for x in q],color='#78926B');a[1,0].set_xticks(range(len(q)),[x['policy']+'\nn='+str(x['site_years']) for x in q]);a[1,0].set_ylabel('Joint compliance (%)');a[1,0].set_title('Specialist removal (unequal cohort noted)')
for pol,c in [('TreeMLP','#B8525A'),('remove-econ','#6A90B0')]:
 q=sorted([x for x in S['summary'] if x['benchmark']=='P1' and x['cohort']=='Former-Held-Out' and x['climate']=='Historical' and x['cap']==40 and x['price_multiplier']==1 and x['track']=='Sensorless' and x['mode']=='soft' and x['policy']==pol],key=lambda x:x['subsidy']);a[1,1].plot([x['subsidy'] for x in q],[100*x['region_equal']['joint'] for x in q],'o-',label=pol,color=c)
a[1,1].set_xlabel('Experimental subsidy (EUR ha$^{-1}$)');a[1,1].set_ylabel('Joint compliance (%)');a[1,1].legend(frameon=False);a[1,1].set_title('Economic activation diagnostic')
for ax,l in zip(a.flat,'abcd'):ax.text(-.1,1.04,l,transform=ax.transAxes,fontweight='bold',fontsize=17)
for ext in ['pdf','svg','png']:fig.savefig(O/('figs2-g3-subsidy.'+ext),dpi=450)
