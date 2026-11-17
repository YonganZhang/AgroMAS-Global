"""Editable reconstruction of candidate E with independently corrected interfaces."""
from pathlib import Path
import json, subprocess
from PIL import Image,ImageDraw
from collections import deque
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE,MSO_CONNECTOR
from pptx.oxml.xmlchemy import OxmlElement
R=Path(__file__).resolve().parents[1];O=R/'reports/phase8/figures';O.mkdir(exist_ok=True)
p=Presentation();p.slide_width=Inches(16);p.slide_height=Inches(10);s=p.slides.add_slide(p.slide_layouts[6]);checks=[]
def text(x,y,w,h,t,size=16,bold=False):
 sh=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));tf=sh.text_frame;tf.word_wrap=True;tf.margin_left=tf.margin_right=Inches(.04);tf.margin_top=Inches(.02)
 for i,line in enumerate(t.split('\n')):
  q=tf.paragraphs[0] if i==0 else tf.add_paragraph();q.text=line;q.font.name='Times New Roman';q.font.size=Pt(size);q.font.bold=bold;q.font.color.rgb=RGBColor(0,0,0)
 checks.append(dict(text=t,bounds=[x,y,w,h],font=size));return sh
def card(x,y,w,h,title,body,fill='EDF2F5',size=16):
 sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h));sh.fill.solid();sh.fill.fore_color.rgb=RGBColor.from_string(fill);sh.line.color.rgb=RGBColor.from_string('617889');sh.line.width=Pt(1.3)
 text(x+.12,y+.08,w-.24,.4,title,20,True);text(x+.12,y+.55,w-.24,h-.6,body,size);return sh
def arrow(x,y,X,Y,c='617889',dash=False,head=True):
 sh=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(x),Inches(y),Inches(X),Inches(Y));sh.line.color.rgb=RGBColor.from_string(c);sh.line.width=Pt(1.4)
 ln=sh._element.spPr.get_or_add_ln()
 if head:
  e=OxmlElement('a:tailEnd');e.set('type','triangle');ln.append(e)
 if dash:
  e=OxmlElement('a:prstDash');e.set('val','dash');ln.insert(1,e)
 return sh
# Native card scaffolds preserve the asymmetric five-specialist layout.
card(1.05,.4,2.0,1.15,'Weather','Observed public prefix',size=14)
card(1.05,1.8,2.0,1.15,'DVS + history','Updated public history',size=14)
card(1.05,3.2,2.0,1.3,'Telemetry','LAI, water, plant N\nFull-Telemetry only',size=14)
# Short input headings cannot wrap into their body text.
for sh in s.shapes:
 if sh.has_text_frame and sh.text in ['Weather','DVS + history','Telemetry']:
  for q in sh.text_frame.paragraphs:q.font.size=Pt(16)
card(3.6,.4,7.0,3.65,'Spatial Twin — private feature boundary','')
card(3.85,1.15,2.45,1.05,'36-D backbone','96 → 96 → 3',size=16)
card(7.0,1.15,3.3,1.05,'Private 64-D (P2)','PCA/Ridge ≤4-D',size=16)
text(3.85,2.45,2.4,1.35,'SiLU; dropout 0.05\n13,155 parameters\nThree frozen seeds',16)
text(6.7,2.65,.5,.55,'+',26,True)
arrow(6.3,1.7,6.5,1.7,head=False);arrow(6.5,1.7,6.5,2.9,head=False);arrow(6.5,2.9,6.6,2.9)
arrow(8.6,2.2,8.6,2.5,head=False);arrow(8.6,2.5,6.85,2.5,head=False);arrow(6.85,2.5,6.85,2.65)
text(7.05,2.2,3.1,.3,'Output correction',14)
card(7.65,2.8,2.65,.9,'32 joint members','Yield, grain N, executed N',size=14)
arrow(7.1,2.95,7.65,2.95)
text(6.45,3.5,1.25,.4,'P1 backbone',14)
text(7.05,.87,3.3,.3,'t−1; LOYO / LORO; OOD: Δy = 0',13)
card(11.2,.4,4.5,3.65,'Climate','TRAIN 1995–2009 analogs\nFirst 7-day rain, then temperature\nNo identity or later truth revealed',fill='EEF3EA',size=16)
for y in [2.8,3.2,3.6]:arrow(11.55,3.15,12.25,y,'78926B')
text(12.4,2.65,3.1,1.15,'Historical / +1.8°C, 450 ppm\n+3.5°C, 550 ppm\nIdealized; not operational NWP',15)
card(.3,5.0,4.2,1.7,'Eco Safety','Upper-tail surplus: 0 ≤ surplus ≤ cap\nCaps 25 / 35 / 40 / 50 kg N ha⁻¹',fill='EEF3EA',size=17)
card(.3,7.0,4.2,2.0,'Economics','Partial fertilizer-management budget\nN price 1× / 2×; experimental subsidies\nNUE target: 0.5 ≤ NUE ≤ 0.9',fill='F5EEEE',size=17)
card(5.1,5.0,6.5,4.0,'Agronomic Control','',fill='F5EEEE')
text(5.4,5.95,.5,.4,'a₁',18,True)
for y in [5.7,6.35]:
 arrow(5.9,6.1,6.8,y+.14);text(6.85,y,.5,.4,'a₂',18,True)
 for Y in [y-.18,y+.18]:arrow(7.35,y+.14,8.2,Y+.14);text(8.25,Y,.5,.4,'a₃',18,True)
text(9.0,5.65,2.25,1.05,'Shared root\n7-day rain → a₂\n7-day temperature → a₃',15)
text(5.3,7.0,6.1,1.85,'Composite = profit + 200 P(active joint) − 200 distance\nTier2-Composite: tier masks + composite ranking\nSoft-Coupled: composite without hard-tail masks\nArchived bare: partial profit only\nController OOD / empty set: dose 0, never compliance\nReplan from updated public observations',15)
card(12.2,5.0,3.5,4.0,'External referee','WOFOST81-SNOMIN\nRealized yield, surplus, NUE\nNative N loss; daily C/N closure',fill='F2F1EE',size=16)
text(12.35,8.5,3.15,.4,'No hidden-state / future-truth feedback',14)
for y in [1.0,2.4,3.8]:arrow(3.05,y,3.6,y,dash=y==3.8)
arrow(11.2,1.5,10.6,1.5,'78926B')
arrow(11.7,4.05,11.7,4.7,'78926B',head=False);arrow(11.7,4.7,10.8,4.7,'78926B',head=False);arrow(10.8,4.7,10.8,5,'78926B')
text(11.85,4.2,3.7,.35,'Branch weights / information partitions',14)
arrow(8.8,5,8.8,4.05);text(8.95,4.1,2.25,.6,'Candidate-dose query',15)
arrow(6.3,4.05,6.3,4.55,head=False);arrow(6.3,4.55,2.4,4.55,head=False);arrow(2.4,4.55,2.4,5)
# Independent economics tap enters its top via the free inter-card gap.
arrow(4.7,4.55,4.7,6.85,head=False);arrow(4.7,6.85,2.4,6.85,head=False);arrow(2.4,6.85,2.4,7)
arrow(6.3,4.55,6.3,5);text(3.4,4.1,2.8,.4,'Joint-distribution bus',15)
arrow(4.5,5.8,5.1,5.8,'78926B');arrow(4.5,8.4,5.1,8.4,'B8525A');arrow(11.6,6.7,12.2,6.7)
text(.4,9.4,15,.35,'Typed numerical specialists; nodewise nonanticipative planning, without a global chance/CVaR optimality claim.',17)
# Preserve the original domain artwork using Gemini-verified crop bounds.
assets=O/'fig1-assets';assets.mkdir(exist_ok=True);original=Image.open(O/'fig1-candidates/candidate-e.png').convert('RGBA')
for name,box,x,y,w,h in [('wheat-soil',(0,128,103,502),.08,.55,.78,3.2),('tractor',(1110,668,1255,890),14.6,7.0,.75,1.15),('referee-soil',(1304,636,1522,789),12.4,7.0,1.95,1.37)]:
 im=original.crop(box)
 # Remove only edge-connected near-white background; retain internal highlights.
 pix=im.load();todo=deque([(i,0) for i in range(im.width)]+[(i,im.height-1) for i in range(im.width)]+[(0,j) for j in range(im.height)]+[(im.width-1,j) for j in range(im.height)]);seen=set()
 while todo:
  u,v=todo.popleft()
  if (u,v) in seen or not(0<=u<im.width and 0<=v<im.height):continue
  seen.add((u,v));rgb=pix[u,v]
  if min(rgb[:3])<245:continue
  pix[u,v]=rgb[:3]+(0,);todo.extend([(u-1,v),(u+1,v),(u,v-1),(u,v+1)])
 im.save(assets/(name+'.png'));s.shapes.add_picture(str(assets/(name+'.png')),Inches(x),Inches(y),Inches(w),Inches(h))
f=O/'fig1-architecture.pptx';p.save(f)
assert all(x>=0 and y>=0 and x+w<=16 and y+h<=10 for d in checks for x,y,w,h in [d['bounds']])
(O/'fig1-native-rebuild-note.json').write_text(json.dumps(dict(source='fig1-candidates/candidate-e.png',executor='Codex; Claude authoring unavailable; explicit latest instruction prohibits further Claude calls',native_text_boxes=len(checks),native_shapes=len(s.shapes),bounds_passed=True,minimum_font_pt=min(d['font'] for d in checks),scientific_connector_corrections=True,limitation='Editable geometric reconstruction preserves five-specialist/referee macro-layout; Original wheat/soil/tractor crops retained; text and simple schematics are native editable. Not author-final approved.',text_objects=checks),indent=2))
