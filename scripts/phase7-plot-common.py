"""Phase7 output adapter using the immutable Phase6 typography and palette helpers."""
from pathlib import Path
import importlib.util,hashlib,json
import matplotlib.pyplot as plt
from matplotlib.text import Text
from matplotlib import font_manager as fm
from matplotlib.ft2font import FT2Font
from matplotlib.colors import to_hex
R=Path(__file__).resolve().parents[1];P=R/'reports/phase7';O=R/'reports/figures/phase7';O.mkdir(exist_ok=True)
s=importlib.util.spec_from_file_location('phase6_style',R/'scripts/phase6-plot-common.py');c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
axis=c.axis;scale=c.scale;COL=c.COL;palette=c.palette;ANCHORS=c.ANCHORS

def save(fig,stem,variant):
 for ax in fig.axes:assert not ax.get_title()
 assert not getattr(fig,'_suptitle',None)
 for t in fig.findobj(Text):
  t.set_fontfamily('Times New Roman');t.set_fontsize(max(7,t.get_fontsize()));t.set_fontweight('bold' if t.get_text() in ['a','b','c','d'] else 'normal')
  if to_hex(t.get_color()).lower() not in ['#000000','#ffffff']:t.set_color('#000000')
  f=fm.findfont(t.get_fontproperties(),fallback_to_default=False);assert fm.FontProperties(fname=f).get_name()=='Times New Roman';face=FT2Font(f);assert not [ch for ch in t.get_text() if not ch.isspace() and face.get_char_index(ord(ch))==0],t.get_text()
 fig.canvas.draw();renderer=fig.canvas.get_renderer();excluded=set()
 for ax in fig.axes:
  for a in [ax.xaxis,ax.yaxis]:
   lo,hi=sorted(a.get_view_interval())
   for tick in a.get_major_ticks()+a.get_minor_ticks():
    if not a.get_visible() or not lo-1e-10<=tick.get_loc()<=hi+1e-10:excluded.update([id(tick.label1),id(tick.label2)])
 texts=[t for t in fig.findobj(Text) if t.get_visible() and t.get_text().strip() and id(t) not in excluded];outside=[];overlap=[]
 for i,t in enumerate(texts):
  b=t.get_window_extent(renderer)
  if b.x0<-.5 or b.y0<-.5 or b.x1>fig.bbox.x1+.5 or b.y1>fig.bbox.y1+.5:outside.append(t.get_text())
  for u in texts[i+1:]:
   v=u.get_window_extent(renderer);dx=min(b.x1,v.x1)-max(b.x0,v.x0);dy=min(b.y1,v.y1)-max(b.y0,v.y0)
   if dx>0 and dy>0 and dx*dy>.2*min(b.width*b.height,v.width*v.height):overlap.append([t.get_text(),u.get_text()])
 assert not outside,('Outside',outside)
 files=[]
 for ext in ['png','pdf','svg']:
  f=O/f'{stem}_{variant}.{ext}';fig.savefig(f,dpi=400);files.append(dict(path=str(f.relative_to(R)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
 sources=[R/'scripts/phase7-plot-fig5.py',R/'scripts/phase7-plot-common.py',R/'scripts/phase6-plot-common.py',P/'decoding-nested-statistics-v7.json',P/'bridge-comparison-statistics-v7.json',P/'regional-fingerprint-and-cosine-v7.json']
 (P/f'{stem}_{variant}-style-audit-v7.json').write_text(json.dumps(dict(font='Times New Roman',minimum_font_pt=min(t.get_fontsize() for t in texts),ink='black;WCAGwhiteincells',palette='PALETTE_SCI_ROSE_SLATE_10 / MAP_ANCHORS_ROSE_SLATE_6 in OKLCh',outside_canvas_text=outside,text_overlap_candidates=overlap,no_titles=True,files=files,source_sha256={str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources}),indent=2));plt.close(fig)
