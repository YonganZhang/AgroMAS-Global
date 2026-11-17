"""Editable native method diagram + actual dev Pareto scatter (no schematic performance)."""
from pathlib import Path
import json,xml.etree.ElementTree as E,hashlib,math
R=Path(__file__).resolve().parents[1]
x=json.loads((R/'reports/phase3b_metrics.json').read_text())
out=R/'figures/phase3b-breakthrough-final';out.mkdir(exist_ok=True)
p=out/'diagram.drawio'
if p.exists():raise RuntimeError('Use a new version directory to preserve evidence')
mx=E.Element('mxfile');d=E.SubElement(mx,'diagram',name='Phase3B development evidence');model=E.SubElement(d,'mxGraphModel',page='1',pageWidth='1700',pageHeight='1240');root=E.SubElement(model,'root');E.SubElement(root,'mxCell',id='0');E.SubElement(root,'mxCell',id='1',parent='0')
def box(i,label,a,b,w,h,color='#FFFFFF',style=''):
 c=E.SubElement(root,'mxCell',id=i,value=label,vertex='1',parent='1',style=f'rounded=1;whiteSpace=wrap;html=0;fillColor={color};strokeColor=#526276;fontFamily=Arial;fontSize=20;fontColor=#24364B;'+style)
 E.SubElement(c,'mxGeometry',x=str(a),y=str(b),width=str(w),height=str(h),as_='geometry').attrib['as']='geometry';c[0].attrib.pop('as_',None)
def edge(i,s,t,label,exit_x=.5,entry_x=.5,offset_x=0):
 style=f'edgeStyle=orthogonalEdgeStyle;rounded=0;html=0;endArrow=block;fontFamily=Arial;fontSize=16;fontColor=#426387;labelBackgroundColor=#FFFFFF;whiteSpace=wrap;exitX={exit_x};exitY=1;entryX={entry_x};entryY=0;'
 c=E.SubElement(root,'mxCell',id=i,value=label,edge='1',parent='1',source=s,target=t,style=style)
 g=E.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'});E.SubElement(g,'mxPoint',x=str(offset_x),y='0',**{'as':'offset'})
def line(i,a,b,c,d):
 cell=E.SubElement(root,'mxCell',id=i,edge='1',parent='1',style='endArrow=none;strokeColor=#94A3B8;');g=E.SubElement(cell,'mxGeometry',relative='1',**{'as':'geometry'});E.SubElement(g,'mxPoint',x=str(a),y=str(b),**{'as':'sourcePoint'});E.SubElement(g,'mxPoint',x=str(c),y=str(d),**{'as':'targetPoint'})
box('title','AgroShield-RL v3 | Dev gate failed',50,25,1580,65,style='strokeColor=none;fontSize=30;fontStyle=1;')
box('input','SM variant: crop + past weather + soil water\nDVS / LAI / applied N / idealized soil water',50,135,630,90,'#EEF3F8')
box('history','Causal four-frame GRU\nHistory representation',50,285,280,110,'#E5EFFB')
box('prior','Phenology prior + N envelope\nSeasonal N: 160–210 kg/ha',400,285,280,110,'#F7F0E2')
box('policy','Masked policy logits\nStore proposal + its log-probability',100,455,530,100,'#DFF1EA')
box('engine','Native weekly simulator\nFinal execution-day guard',100,630,530,100,'#E5EFFB')
box('audit','Yield / NUE / surplus / actual N\nExecuted violations + guard interceptions',50,805,630,110,'#F2F5F8')
edge('e1','input','history','history',exit_x=140/630,offset_x=55);edge('e2','input','prior','current\nobservables',exit_x=490/630,offset_x=-80);edge('e3','history','policy','features',entry_x=90/530,offset_x=55);edge('e4','prior','policy','causal mask\n+ prior logits',entry_x=440/530,offset_x=-85);edge('e5','policy','engine','sampled proposal',offset_x=120);edge('e6','engine','audit','actual outcomes',offset_x=120)
box('plot-title','Dev 5000–5499 | 3 soils',770,125,810,50,style='strokeColor=none;fontSize=24;fontStyle=1;')
# Scatter axes yield 5–10 t/ha; joint 0–100%. Every point uses all 1500 unique scenarios.
x0,y0,w,h=840,745,650,490
selected={n:s['pooled'] for n,s in x['stats'].items() if n in ['N2-PA','prior160','prior190'] or n in ['v3-c8/full3','v3-sm/full3']}
xmin=math.floor(min(s['yield_t_ha'] for s in selected.values())*10)/10-.1
xmax=math.ceil(max(s['yield_t_ha'] for s in selected.values())*10)/10+.1
line('axisx',x0,y0,x0+w,y0);line('axisy',x0,y0,x0,y0-h)
for k in range(6):
 xx=x0+k*w/5;box('xt'+str(k),f'{xmin+k*(xmax-xmin)/5:.2f}',xx-20,y0+10,40,30,style='strokeColor=none;fontSize=17;')
for k in range(6):
 yy=y0-k*h/5;box('yt'+str(k),str(k*20),x0-60,yy-15,45,30,style='strokeColor=none;fontSize=17;');line('grid'+str(k),x0,yy,x0+w,yy)
box('xlabel','Mean yield (t/ha)',960,805,420,40,style='strokeColor=none;')
box('ylabel','Joint NUE + surplus compliance (%)',500,480,500,40,style='strokeColor=none;rotation=270;')
points=[]
for name,st in x['stats'].items():
 if name not in ['N2-PA','prior160','prior190'] and not name in ['v3-c8/full3','v3-sm/full3']:continue
 s=st['pooled'];xx=x0+(s['yield_t_ha']-xmin)/(xmax-xmin)*w;yy=y0-s['joint']*h
 color={'N2-PA':'#526276','prior160':'#257DAD','prior190':'#228B53','v3-c8/full3':'#BC3D49','v3-sm/full3':'#7B4BAC'}.get(name,'#BC3D49')
 points.append((name,xx,yy,s))
frontier=[pt for pt in points if not any(other[3]['yield_t_ha']>=pt[3]['yield_t_ha'] and other[3]['joint']>=pt[3]['joint'] and (other[3]['yield_t_ha']>pt[3]['yield_t_ha'] or other[3]['joint']>pt[3]['joint']) for other in points)]
frontier.sort(key=lambda pt:pt[1])
for j,(a,b) in enumerate(zip(frontier,frontier[1:])):line('frontier'+str(j),a[1],a[2],b[1],b[2])
for name,xx,yy,s in points:
 color={'N2-PA':'#526276','prior160':'#257DAD','prior190':'#228B53','v3-c8/full3':'#BC3D49','v3-sm/full3':'#7B4BAC'}.get(name,'#BC3D49')
 box('point-'+name,'',xx-7,yy-7,14,14,color,style='shape=ellipse;')
for j,(name,xx,yy,s) in enumerate(points):
 # Label in separate right-side legend to prevent close-point overlap.
 lc={'N2-PA':'#526276','prior160':'#257DAD','prior190':'#228B53','v3-c8/full3':'#BC3D49','v3-sm/full3':'#7B4BAC'}.get(name,'#BC3D49')
 display={'v3-c8/full3':'C1 short/long + C8 Full3','v3-sm/full3':'SM Full3'}.get(name,name)
 box('swatch-'+name,'',790,879+j*35,14,14,lc,style='shape=ellipse;')
 box('legend-'+name,f'{display}: {s["yield_t_ha"]:.3f} t/ha | {s["joint"]:.2%}',780,870+j*35,800,32,style='strokeColor=none;fontSize=19;fillColor=none;align=left;spacingLeft=45;fontColor='+lc+';')
# True-coordinate inset separates the three close means without moving data points.
box('zoom-bg','',1000,245,490,220,'#FFFFFF',style='rounded=0;strokeColor=#A8B5C5;')
box('zoom-title','Zoom: clustered methods',1050,250,400,30,style='strokeColor=none;fontSize=17;')
line('zoom-x',1060,425,1440,425);line('zoom-y',1060,425,1060,295)
for k,value in enumerate([54,54.5,55,55.5]):
 yy=425-(value-54)/1.5*130
 box('zoom-y'+str(k),str(value),1010,yy-10,45,20,style='strokeColor=none;fontSize=14;')
for k,value in enumerate([8.430,8.434,8.438]):
 xx=1060+(value-8.430)/.008*380
 box('zoom-x'+str(k),f'{value:.3f}',xx-30,430,60,22,style='strokeColor=none;fontSize=14;')
for name in ['prior190','v3-c8/full3','v3-sm/full3']:
 st=x['stats'][name]['pooled'];xx=1060+(st['yield_t_ha']-8.430)/.008*380;yy=425-(st['joint']*100-54)/1.5*130
 color={'prior190':'#228B53','v3-c8/full3':'#BC3D49','v3-sm/full3':'#7B4BAC'}[name]
 box('zoom-point-'+name,'',xx-6,yy-6,12,12,color,style='shape=ellipse;')
 dx,dy=(20,-10) if name=='v3-c8/full3' else (-50,-30)
 box('zoom-label-'+name,{'prior190':'prior190','v3-c8/full3':'C1/C8 Full3','v3-sm/full3':'SM Full3'}[name],xx+dx,yy+dy,125,25,style='strokeColor=none;fillColor=none;fontSize=14;fontColor='+color+';')
box('mean-note','All seeds: SM Full3 = fixed 70/60/60; vs prior190: +0.40 pp (95% CI 0.00–0.80), p=0.058.',50,1080,1550,35,style='strokeColor=none;fontSize=18;')
box('footer','Exploratory Dev: 500 years x 3 soils; RL: 3 seeds. Historical / stress remain locked.',50,1130,1550,38,style='strokeColor=none;fontSize=18;')
box('line-note','Grey line: observed Dev non-dominated means only.',50,1175,1550,32,style='strokeColor=none;fontSize=17;')
E.ElementTree(mx).write(p,encoding='utf-8',xml_declaration=True)
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=dict(schema_version=1,kind='method-diagram-derived-view',spec=dict(path='scripts/phase3b-figure.py',sha256=digest(Path(__file__))),sources=[dict(path=str(q.relative_to(R)),sha256=digest(q)) for q in [R/'reports/phase3b_metrics.json',R/'NUE_PCSE-Gym/pcse_gym/envs/moisture.py',R/'tasks/TASK_PHASE3B_190_CORRIDOR_AND_FINAL_UNLOCK.md']],artifacts={'diagram.drawio':digest(p)},rendered=False,meaning='Actual development means; connecting observed non-dominated points does not prove unseen generalization')
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(p)
