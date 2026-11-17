"""Common reproducible style/data access for Phase5 quantitative candidates."""
from pathlib import Path
import os,sys,json,hashlib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib import font_manager as fm
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5';F=R/'reports/figures'
STYLE=Path(os.environ.get('PHASE5_SCI_STYLE',str(Path.home()/'.ai-shared/skills/share-sci-plot/references')))
sys.path.insert(0,str(STYLE))
from figure_standards import normalize_fonts,assert_no_caption_text
for path in (Path.home()/'.local/share/fonts/msttcorefonts').glob('Times*.TTF'):fm.fontManager.addfont(str(path))
assert 'Times' in fm.findfont('Times New Roman',fallback_to_default=False)
mpl.rcParams.update({'font.family':'Times New Roman','font.size':7,'axes.labelsize':8,'axes.labelcolor':'#000000','text.color':'#000000',
 'xtick.color':'#000000','ytick.color':'#000000','axes.titlesize':8,'axes.linewidth':.5,'lines.linewidth':1,'pdf.fonttype':42,'svg.fonttype':'none','axes.unicode_minus':False})
VARIANT=os.environ.get('PHASE5_FIGURE_VARIANT','a');assert VARIANT in ('a','b','c')
COLORS=['#5882A6','#5E9680','#8E7CA6','#D67E7D','#B8525A'];REGIONS=['netherlands_lelystad','china_ncp_luancheng','usa_kansas_wichita','france_paris_beauce','australia_wa_perth'];SHORT=['NL','CN','US','FR','AU']
C=mpl.colors.LinearSegmentedColormap.from_list('rose-slate',['#6A90B0','#A4BED1','#FFF0C4','#F4C8AE','#D67E7D','#B8525A'])

def data():return pd.read_csv(P/'final-context-summary-v4.csv'),pd.read_csv(P/'final-annual-seed-averaged-metrics-v4.csv'),json.loads((P/'final-paired-year-statistics-v4.json').read_text())['contrasts']
def main_context(d,role='Held-Out'):return d[(d.role==role)&(d.climate=='Historical')&(d.zone=='standard_40')&(d.price_multiplier==1)&(d.subsidy==0)]
def clean(ax,label):
 ax.spines[['top','right']].set_visible(False);ax.tick_params(width=.5,length=3)
 ax.text(-.12,1.035,label,transform=ax.transAxes,fontweight='bold',fontsize=10,va='bottom')
def save(fig,name):
 normalize_fonts(fig);assert_no_caption_text(fig)
 for text in fig.findobj(mpl.text.Text):
  text.set_color('#000000')
  if text.get_text() not in ('a','b','c','d'):text.set_weight('normal')
  assert text.get_fontname()=='Times New Roman',(text.get_text(),text.get_fontname())
 fig.canvas.draw();target=F if VARIANT=='a' else F/'phase5-candidates-v4'/name/VARIANT;target.mkdir(parents=True,exist_ok=True)
 for ext in ('png','pdf','svg'):fig.savefig(target/f'{name}.{ext}',dpi=300,facecolor='white')
 (R/'figures/phase5-quantitative-v4').mkdir(parents=True,exist_ok=True)
 receipt=dict(figure=name,candidate=VARIANT,selection='awaitingauthorchoice',plot_source_path=str(Path(sys.argv[0]).resolve().relative_to(R)),plot_source_sha256=hashlib.sha256(Path(sys.argv[0]).read_bytes()).hexdigest(),common_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),mode='D 7.2x7.2in',script_style_path=str(STYLE/'figure_standards.py'),style_sha256=hashlib.sha256((STYLE/'figure_standards.py').read_bytes()).hexdigest(),
  input_summary_sha256=hashlib.sha256((P/'final-context-summary-v4.csv').read_bytes()).hexdigest(),candidate_not_inserted_into_manuscript=True,
  files={ext:hashlib.sha256((target/f'{name}.{ext}').read_bytes()).hexdigest() for ext in ('png','pdf','svg')})
 (R/f'figures/phase5-quantitative-v4/{name}-candidate-{VARIANT}-receipt.json').write_text(json.dumps(receipt,indent=2));plt.close(fig)
def contrast(contrasts,reg,control,metric):
 x=next(x for x in contrasts if x['primary'] and x['role']=='Held-Out' and x['region_id']==reg and x['control']==control)
 return x['metrics'][metric]
