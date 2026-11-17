"""Shared scientific data and deterministic publication styling for v6 candidates."""
from pathlib import Path
import importlib.util,json,hashlib,glob,numpy as np,pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.text import Text
from matplotlib.ft2font import FT2Font
from matplotlib.colors import to_hex,to_rgba
R=Path(__file__).resolve().parents[1];P=R/'reports/phase6';O=R/'reports/figures/phase6';O.mkdir(parents=True,exist_ok=True)
for pattern in ('/mnt/data/yongan-admin-2/.local/share/fonts/msttcorefonts/Times*.TTF','/mnt/data/yongan-admin-2/.local/share/fonts/msttcorefonts/times*.ttf'):
 for f in glob.glob(pattern):fm.fontManager.addfont(f)
assert 'Times New Roman' in fm.FontProperties(fname=fm.findfont('Times New Roman',fallback_to_default=False)).get_name()
plt.rcParams.update({'font.family':'Times New Roman','font.size':7.2,'axes.labelsize':7.2,'xtick.labelsize':7,'ytick.labelsize':7,'legend.fontsize':7,'text.color':'#000000','axes.labelcolor':'#000000','axes.edgecolor':'#000000','xtick.color':'#000000','ytick.color':'#000000','axes.linewidth':.5,'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none','savefig.facecolor':'white','axes.unicode_minus':False})
spec=importlib.util.spec_from_file_location('v6palette',R/'scripts/phase6-palette.py');palette=importlib.util.module_from_spec(spec);spec.loader.exec_module(palette)
ACTIVE=json.loads((P/'ACTIVE_TRAIN_RUN_V6.json').read_text());PROTOCOL=json.loads((R/ACTIVE['reports']/'TRAIN_PROTOCOL_V6.json').read_text());BOOTSTRAP_SEED=int(PROTOCOL['bootstrap_seed'])
COL=['#162830','#4C7A99','#5882A6','#A4BED1','#5E9680','#8E7CA6','#FFF0C4','#E8B8AE','#D67E7D','#B8525A'];ANCHORS=['#6A90B0','#A4BED1','#FFF0C4','#F4C8AE','#D67E7D','#B8525A']
REGIONS=['usa_iowa_ames','australia_wa_perth','netherlands_lelystad','france_grignon','china_henan_zhengzhou']
SHORT={'usa_iowa_ames':'US','australia_wa_perth':'AU','netherlands_lelystad':'NL','france_grignon':'FR','china_henan_zhengzhou':'CN'}
# Region IDs are resolved from actual metrics rather than silently omitted.
def data():
 d=pd.read_csv(P/'annual-policy-metrics-v6.csv');ids=sorted(d.region_id.unique());mapping={x:('NL' if 'netherlands' in x else 'AU' if 'australia' in x else 'US' if 'usa' in x or 'united' in x else 'FR' if 'france' in x else 'CN') for x in ids};d['region']=d.region_id.map(mapping);return d

def primary(d):return d[(d.climate=='Historical')&(d.cap==40)&(d.price_multiplier==1)&(d.subsidy==0)&(d.cohort=='Former-Held-Out')]
def macro(d,metric):return d.groupby('region_id')[metric].mean().mean()
def pairs(d,ref='DVS-N2'):
 return d[d.policy=='Phase6-Full'].merge(d[d.policy==ref],on=['region_id','region','year','climate','cohort','cap','price_multiplier','subsidy'],suffixes=('_a','_b'))
def clean(ax):
 ax.spines[['top','right']].set_visible(False);ax.tick_params(length=2.2,width=.5,pad=2);ax.set_axisbelow(True)
def tag(ax,letter):
 box=ax.get_position();ax.figure.text(max(.015,box.x0-.035),box.y1+.008,letter,fontsize=10,fontweight='bold',ha='left',va='bottom',color='#000000')
def axis(fig,box,letter=None):
 ax=fig.add_axes(box);clean(ax)
 if letter:tag(ax,letter)
 return ax

def contrast_text(c):
 rgb=np.array(mpl.colors.to_rgb(c));linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4);return 'white' if np.dot(linear,[.2126,.7152,.0722])<.179 else '#000000'
def scale(values):
 lo=float(np.nanmin(values));hi=float(np.nanmax(values))
 if hi==lo:hi=lo+1
 bounds=np.linspace(lo,hi,6);cmap,norm,_=palette.continuous_scale(bounds,anchors=ANCHORS,name='v6rose',space='oklch');return cmap,norm,bounds

def save(fig,stem,variant):
 # Strict equivalent of assert_no_caption_text, with explicit typography/ink checks.
 for ax in fig.axes:assert not ax.get_title()
 assert not getattr(fig,'_suptitle',None)
 for obj in fig.findobj(Text):
  obj.set_text(obj.get_text().replace('ha⁻¹','per ha'));obj.set_fontfamily('Times New Roman');obj.set_fontsize(max(7,obj.get_fontsize()))
  if obj.get_text() not in ('a','b','c','d'):obj.set_fontweight('normal')
  if to_hex(obj.get_color()).lower() not in ('#ffffff','#000000'):obj.set_color('#000000')
  font_path=fm.findfont(obj.get_fontproperties(),fallback_to_default=False);assert fm.FontProperties(fname=font_path).get_name()=='Times New Roman'
  face=FT2Font(font_path);assert not [ch for ch in obj.get_text() if not ch.isspace() and face.get_char_index(ord(ch))==0],('Missingfontglyph',obj.get_text())
 fig.canvas.draw();renderer=fig.canvas.get_renderer();outside=[];unrendered_ticks=set()
 for ax in fig.axes:
  for axis in (ax.xaxis,ax.yaxis):
   lo,hi=sorted(axis.get_view_interval())
   for tick in axis.get_major_ticks()+axis.get_minor_ticks():
    if not axis.get_visible() or not lo-1e-10<=tick.get_loc()<=hi+1e-10:unrendered_ticks.update((id(tick.label1),id(tick.label2)))
 for obj in fig.findobj(Text):
  if obj.get_visible() and obj.get_text() and id(obj) not in unrendered_ticks:
   b=obj.get_window_extent(renderer);fb=fig.bbox
   if b.x0<-.5 or b.y0<-.5 or b.x1>fb.x1+.5 or b.y1>fb.y1+.5:outside.append(obj.get_text())
 assert not outside,('Textoutsidecanvas',outside)
 overlaps=[];artists=[t for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip() and id(t) not in unrendered_ticks]
 for i,a in enumerate(artists):
  ba=a.get_window_extent(renderer)
  for b in artists[i+1:]:
   bb=b.get_window_extent(renderer);dx=min(ba.x1,bb.x1)-max(ba.x0,bb.x0);dy=min(ba.y1,bb.y1)-max(ba.y0,bb.y0)
   if dx>0 and dy>0 and dx*dy>.20*min(ba.width*ba.height,bb.width*bb.height):overlaps.append([a.get_text(),b.get_text()])
 files=[]
 for ext in ('png','pdf','svg'):
  path=O/f'{stem}_{variant}.{ext}';fig.savefig(path,dpi=400);files.append(dict(path=str(path.relative_to(R)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
 sources=[R/'scripts/phase6-plot-common.py',R/'scripts/phase6-palette.py',R/'scripts'/f'phase6-plot-{stem.split("_")[0]}.py',P/'annual-policy-metrics-v6.csv',P/'benchmark-statistics-v6.json']
 audit=dict(source_sha256={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},font='Times New Roman',minimum_font_pt=min(t.get_fontsize() for t in fig.findobj(Text)),ink='black;WCAGwhiteincells',no_titles=True,outside_canvas_text=outside,text_overlap_candidates=overlaps,excluded_unrendered_locator_labels=len(unrendered_ticks),variant=variant,files=files)
 (P/f'{stem}_{variant}-style-audit-v6.json').write_text(json.dumps(audit,indent=2));plt.close(fig)
