"""1:1 hybrid reconstruction of selected Image2 candidate; illustrations cropped, structure native.
Run with python-pptx + Pillow. No bitmap candidate is modified.
"""
from pathlib import Path
import json,hashlib,math
from PIL import Image
from pptx import Presentation
from pptx.util import Inches,Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE,MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN,MSO_ANCHOR
from pptx.oxml.xmlchemy import OxmlElement
R=Path(__file__).resolve().parents[1];O=R/'reports/phase8/figures';A=O/'fig1-assets';A.mkdir(exist_ok=True)
source=O/'fig1-candidates/candidate-b-v2-best.png';im=Image.open(source);W,H=im.size
# Coordinates are normalized to the reference's 1568 x 1024 artboard.
SX=W/1568;SY=H/1024
pr=Presentation();pr.slide_width=Inches(15.68);pr.slide_height=Inches(10.24);sl=pr.slides.add_slide(pr.slide_layouts[6]);sl.background.fill.solid();sl.background.fill.fore_color.rgb=RGBColor(255,255,255)
assets={};texts=[];arrows=[]
def pic(name,box,x,y,w,h):
 crop=im.crop(tuple(round(v*(SX if i%2==0 else SY)) for i,v in enumerate(box)));f=A/(name+'.png');crop.save(f);assets[name]={'source_box':box,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()};sl.shapes.add_picture(str(f),Inches(x/100),Inches(y/100),width=Inches(w/100),height=Inches(h/100))
def txt(x,y,w,h,s,size=13,bold=False,align='left'):
 sh=sl.shapes.add_textbox(Inches(x/100),Inches(y/100),Inches(w/100),Inches(h/100));tf=sh.text_frame;tf.clear();tf.word_wrap=True;tf.margin_left=Pt(2);tf.margin_right=Pt(2);tf.margin_top=Pt(1);tf.margin_bottom=Pt(0)
 for i,line in enumerate(s.split('\n')):
  p=tf.paragraphs[0] if i==0 else tf.add_paragraph();p.alignment={'left':PP_ALIGN.LEFT,'center':PP_ALIGN.CENTER,'right':PP_ALIGN.RIGHT}[align];p.space_before=Pt(0);p.space_after=Pt(0);p.font.name='Times New Roman';p.font.size=Pt(size);p.font.bold=bold;p.font.color.rgb=RGBColor(0,0,0);p.text=line
  for rr in p.runs:rr.font.name='Times New Roman';rr.font.size=Pt(size);rr.font.bold=bold;rr.font.color.rgb=RGBColor(0,0,0)
 texts.append(s);return sh

def card(x,y,w,h,fill='FFFFFF',edge='5882A6',radius=True):
 sh=sl.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE,Inches(x/100),Inches(y/100),Inches(w/100),Inches(h/100));sh.fill.solid();sh.fill.fore_color.rgb=RGBColor.from_string(fill);sh.line.color.rgb=RGBColor.from_string(edge);sh.line.width=Pt(.9)
 if radius:sh.adjustments[0]=.06
 return sh

def line(x1,y1,x2,y2,arrow=True,width=1.3):
 sh=sl.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(x1/100),Inches(y1/100),Inches(x2/100),Inches(y2/100));sh.line.color.rgb=RGBColor(0,0,0);sh.line.width=Pt(width)
 if arrow:
  end=OxmlElement('a:tailEnd');end.set('type','triangle');end.set('w','sm');end.set('len','sm');sh._element.spPr.find('{http://schemas.openxmlformats.org/drawingml/2006/main}ln').append(end)
 arrows.append([x1,y1,x2,y2,arrow]);return sh

def route(points):
 for i,(p,q) in enumerate(zip(points,points[1:])):line(*p,*q,arrow=(i==len(points)-2))
# Preserve asymmetric module geometry and rich physical illustration locations.
card(20,45,490,395,'F4F8FB');pic('weather-field',(25,50,510,440),25,50,480,385)
# Native text cards completely cover all raster labels within the input illustration.
card(180,65,315,91,'FFFFFF');txt(188,70,300,78,'Public weather history\nObserved through current day\nT, P, RH, radiation, wind',15,True)
card(180,165,315,90,'FFFFFF');txt(188,172,300,75,'Current crop prefix\nStage and dose history\nOptional field telemetry',14,True)
card(31,361,462,64,'FFFFFF',edge='C8D1D7');txt(38,366,450,54,'Soil physical anchor\nStatic3: field capacity, wilting point and conductivity',14,False,'center')
# Main spatial specialist panel, native operator microcircuit and private adaptor.
card(550,18,1008,424,'F5F9FC');txt(735,23,760,39,'Agent 1: Spatial Twin Specialist',22,True,'center')
pic('satellite-earth-raster',(568,70,877,245),565,71,307,174)
# Satellite is an emblem; native label distinguishes its computational specialist role.
card(908,77,285,185,'EDF3F8');txt(918,82,265,43,'PyTorch MLP · 3 frozen seeds',16,True,'center')
# Bipartite neuron web remains fully editable.
for xx,nn in [(938,3),(1003,4),(1081,4),(1154,3)]:
 ys=[137+i*18 for i in range(nn)]
 for yy in ys:
  sh=sl.shapes.add_shape(MSO_SHAPE.OVAL,Inches(xx/100),Inches(yy/100),Inches(.12),Inches(.12));sh.fill.solid();sh.fill.fore_color.rgb=RGBColor.from_string('A4BED1');sh.line.color.rgb=RGBColor(0,0,0);sh.line.width=Pt(.6)
for xx,nn,xnext,mm in [(944,3,1009,4),(1009,4,1087,4),(1087,4,1160,3)]:
 for i in range(nn):
  for j in range(mm):line(xx+6,143+i*18,xnext,143+j*18,False,.35)
txt(916,211,270,35,'36-D → 96 → 96 → 3\n13,155 parameters',13,False,'center')
# Cropped scientific materials without text.
pic('private-raster',(581,267,656,325),578,268,77,59);card(659,261,161,67,'F2F6ED',edge='5E9680');txt(662,265,155,58,'Private raw 64-D\nAlphaEarth\nt − 1 causal anomaly',12,True,'center')
pic('soil-static3',(581,343,656,405),578,344,77,61);card(659,337,161,69,'F2F6ED',edge='5E9680');txt(663,342,151,57,'Static3 physical\nsoil anchor',13,True,'center')
card(857,288,137,69,'F2F6ED',edge='5E9680');txt(861,295,129,55,'Causal anomaly\nPCA + Ridge',13,False,'center');card(1016,300,111,44,'F2F6ED',edge='5E9680');txt(1020,308,103,30,'≤4-D adapter',13,False,'center')
route([(820,295),(843,295),(843,322),(857,322)]);line(994,322,1016,322);route([(1127,322),(1254,322),(1254,263)]);route([(820,371),(1254,371),(1254,263)])
card(825,203,76,48,'FFFFFF');txt(828,206,70,43,'36-D\npublic\nfeatures',9,False,'center');line(901,227,908,227)
sh=sl.shapes.add_shape(MSO_SHAPE.OVAL,Inches(12.35),Inches(2.23),Inches(.40),Inches(.40));sh.fill.solid();sh.fill.fore_color.rgb=RGBColor(255,255,255);sh.line.color.rgb=RGBColor(0,0,0);txt(1238,224,34,32,'+',21,False,'center');route([(1193,160),(1254,160),(1254,223)])
for y,s in [(79,'Yield'),(119,'Grain N'),(159,'Executed N')]:card(1328,y,210,33,'EDF3F8');txt(1336,y+3,195,26,s,16)
route([(1275,243),(1304,243),(1304,135)]);line(1304,95,1304,175,False);line(1304,95,1328,95);line(1304,135,1328,135);line(1304,175,1328,175);line(1430,192,1430,215)
card(1322,216,225,58,'EDF3F8');txt(1329,220,211,49,'15 strata × 32\nzero-mean joint residuals',14,False,'center');line(1430,274,1430,300)
card(1303,302,244,105,'FAECEB',edge='B8525A');txt(1310,309,230,88,'Surplus & NUE\nSeasonal N accounting\nNUE = grain N / N input',14,False,'center')
txt(860,409,340,23,'NL     CN     US     FR     AU',13,False,'center')
line(510,215,550,215)
# Four deeply illustrated couplings, kept distinct from the control specialist.
card(10,475,455,184,'F4F8FB');txt(31,479,423,34,'Agent 2: Climate Forecast Specialist',18,True,'center');pic('climate-clouds-fan',(28,521,228,649),24,519,202,130);txt(245,519,204,132,'TRAIN 1995–2009\nCausal −dT analog fan\nHistorical\n+1.8°C · 450 ppm\n+3.5°C · 550 ppm',13)
card(10,671,455,145,'F2F6EF',edge='5E9680');txt(24,676,432,33,'Agent 3: Urban Eco-Safety Specialist',18,True,'center');pic('urban-watershed',(26,716,269,804),22,714,244,88);txt(277,717,174,86,'0 ≤ S_N ≤ S_cap\nCaps 25, 35, 40, 50\nkg N/ha',14,False,'center')
card(10,828,455,154,'FBEFEE',edge='B8525A');txt(22,832,435,31,'Agent 4: Socio-Economic Policy Specialist',17,True,'center');pic('market-policy-balance',(32,878,257,968),25,874,228,91);txt(264,873,187,99,'Fertilizer 1× or 2×\nSubsidy and tax\n0.50 ≤ NUE ≤ 0.90\n1.5× upper penalty',13)
# Four orthogonal coupling paths have correctly attributed source modules.
# Spatial bus reaches control directly without passing through the referee.
route([(553,407),(577,407),(577,532),(592,532)]);txt(470,468,93,55,'Coupling 1\nSpatial',12,True,'center')
route([(465,630),(592,630)]);txt(477,583,107,40,'Coupling 2\nClimate',11,True,'center')
route([(465,734),(535,734),(535,710),(592,710)]);txt(475,665,108,44,'Coupling 3\nEco Safety',11,True,'center')
route([(465,923),(577,923),(577,854),(592,854)]);txt(473,866,93,45,'Coupling 4\nEconomics',11,True,'center')
# Core specialist and exact three-stage nonanticipative scenario tree.
core_start=len(sl.shapes)
card(592,476,584,503,'F5F8F0',edge='5E9680');txt(607,483,553,38,'Agent 5: Core Agronomic Control Specialist',20,True,'center')
card(812,544,103,40,'EDF3F8');txt(817,550,93,30,'a1',20,False,'center')
for xx,lab in [(678,'Rain low'),(916,'Rain high')]:card(xx,611,139,34,'FAECEB',edge='B8525A');txt(xx+3,615,133,27,lab,15,False,'center')
line(843,584,747,611);line(888,584,985,611)
for xx in [711,950]:card(xx,669,74,35,'EDF1DF',edge='5E9680');txt(xx+2,672,70,28,'a2',19,False,'center');line(xx+37,645,xx+37,669)
for xx,lab in [(625,'Temp low'),(756,'Temp high'),(891,'Temp low'),(1027,'Temp high')]:card(xx,725,119,34,'FAECEB',edge='B8525A');txt(xx+2,729,115,27,lab,14,False,'center')
for x1,x2 in [(748,684),(748,815),(987,950),(987,1086)]:line(x1,704,x2,725)
for xx in [647,778,913,1049]:card(xx,784,75,34,'EDF3F8');txt(xx+2,787,71,27,'a3',19,False,'center');line(xx+37,759,xx+37,784)
for xx,ww,s in [(617,164,'Soft-Coupled'),(791,174,'Tier2-Composite'),(975,185,'Archived bare')]:card(xx,840,ww,36,'FFFFFF',edge='C8D1D7');txt(xx+3,846,ww-6,26,s,14,False,'center')
card(615,891,545,60,'FAECEB',edge='B8525A');txt(620,897,535,45,'Partial profit + 250 P(active joint) − 300 distance\n2 kg/ha margin · 1.5× upper NUE penalty',14,False,'center')
# Fit the core into the reference's central column without colliding with the referee.
for shape in list(sl.shapes)[core_start:]:
 shape.left=Inches((592+(shape.left/Inches(1)*100-592)*.88)/100)
 shape.width=int(shape.width*.88)
 if shape.has_text_frame:
  for para in shape.text_frame.paragraphs:
   for run in para.runs:
    if run.font.size:run.font.size=Pt(run.font.size.pt*.88)
# Execute and referee: only incoming physical evaluation arrows.
card(1156,550,148,83,'EDF1DF',edge='5E9680');txt(1161,562,138,60,'Execute\ncurrent dose',15,True,'center');line(1106,592,1156,592)
pic('tractor-wheat',(1328,517,1561,666),1323,516,235,151);line(1304,592,1323,592)
card(1134,697,424,284,'FBF2F0',edge='B8525A');txt(1142,700,408,51,'External WOFOST81-SNOMIN\nReferee',16,True,'center');pic('referee-root-soil',(1138,749,1299,964),1141,750,157,216)
for yy,hh,lab in [(759,42,'Yield'),(808,42,'Native N loss'),(866,83,'Daily C/N closure')]:card(1314,yy,231,hh,'FFFFFF',edge='C8D1D7');txt(1321,yy+8,217,hh-12,lab,18,False,'center')
line(1230,633,1230,697)
# Rebuild the N/C labels as editable glyphs over the retained soil illustration.
for cy,label in [(901,'N'),(949,'C')]:
 sh=sl.shapes.add_shape(MSO_SHAPE.OVAL,Inches(12.04),Inches((cy-17)/100),Inches(.35),Inches(.35));sh.fill.solid();sh.fill.fore_color.rgb=RGBColor(255,255,255);sh.line.color.rgb=RGBColor(0,0,0);sh.line.width=Pt(.5);txt(1207,cy-15,28,28,label,17,True,'center')

# Reference page is comparison-only; page one is the formal editable figure.
reference=pr.slides.add_slide(pr.slide_layouts[6]);reference.shapes.add_picture(str(source),0,0,width=pr.slide_width,height=pr.slide_height)
pr.save(O/'fig1-architecture.pptx')
(O/'fig1-assets/asset-manifest.json').write_text(json.dumps({'reference':str(source.relative_to(R)),'reference_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'assets':assets,'native_texts':texts,'native_connections':arrows,'editable_slide':1,'reference_slide':2,'total_slide_objects':len(sl.shapes),'count_definitions':'Total includes native simple shapes, native connectors and raster picture assets; verification native_fig1_shapes counts p:sp only.','numerical_specialists_not_LLMs':True,'referee_outgoing_edges':0,'action_levels':['a1','a2','a3'],'executor':'Codex; only Gemini and DeepSeek external reviewers authorized'},indent=2))
