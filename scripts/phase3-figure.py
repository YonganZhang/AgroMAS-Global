"""Editable native method diagram + actual dev Pareto scatter (no schematic performance)."""
from pathlib import Path
import json,xml.etree.ElementTree as E,hashlib,math
R=Path(__file__).resolve().parents[1]
x=json.loads((R/'reports/phase3_metrics.json').read_text())
out=R/'figures/phase3-breakthrough';out.mkdir(exist_ok=True)
p=out/'diagram.drawio'
if p.exists():raise RuntimeError('Use a new version directory to preserve evidence')
mx=E.Element('mxfile');d=E.SubElement(mx,'diagram',name='Phase3 development evidence');model=E.SubElement(d,'mxGraphModel',page='1',pageWidth='1700',pageHeight='1200');root=E.SubElement(model,'root');E.SubElement(root,'mxCell',id='0');E.SubElement(root,'mxCell',id='1',parent='0')
def box(i,label,a,b,w,h,color='#FFFFFF',style=''):
 c=E.SubElement(root,'mxCell',id=i,value=label,vertex='1',parent='1',style=f'rounded=1;whiteSpace=wrap;html=0;fillColor={color};strokeColor=#526276;fontFamily=Arial;fontSize=20;fontColor=#24364B;'+style)
 E.SubElement(c,'mxGeometry',x=str(a),y=str(b),width=str(w),height=str(h),as_='geometry').attrib['as']='geometry';c[0].attrib.pop('as_',None)
def edge(i,s,t,label,exit_x=.5,entry_x=.5,offset_x=0):
 style=f'edgeStyle=orthogonalEdgeStyle;rounded=0;html=0;endArrow=block;fontFamily=Arial;fontSize=16;fontColor=#426387;labelBackgroundColor=#FFFFFF;whiteSpace=wrap;exitX={exit_x};exitY=1;entryX={entry_x};entryY=0;'
 c=E.SubElement(root,'mxCell',id=i,value=label,edge='1',parent='1',source=s,target=t,style=style)
 g=E.SubElement(c,'mxGeometry',relative='1',**{'as':'geometry'});E.SubElement(g,'mxPoint',x=str(offset_x),y='0',**{'as':'offset'})
def line(i,a,b,c,d):
 cell=E.SubElement(root,'mxCell',id=i,edge='1',parent='1',style='endArrow=none;strokeColor=#94A3B8;');g=E.SubElement(cell,'mxGeometry',relative='1',**{'as':'geometry'});E.SubElement(g,'mxPoint',x=str(a),y=str(b),**{'as':'sourcePoint'});E.SubElement(g,'mxPoint',x=str(c),y=str(d),**{'as':'targetPoint'})
box('title','AgroShield-RL v2 | Dev gate failed',50,25,1580,65,style='strokeColor=none;fontSize=30;fontStyle=1;')
box('input','Observed crop + past weather\nDVS / LAI / applied N / spacing',50,135,630,90,'#EEF3F8')
box('history','Causal four-frame GRU\nHistory representation',50,285,280,110,'#E5EFFB')
box('prior','Phenology prior + N envelope\nNo internal soil-N inputs',400,285,280,110,'#F7F0E2')
box('policy','Masked policy logits\nStore proposal + its log-probability',100,455,530,100,'#DFF1EA')
box('engine','Native weekly simulator\nFinal execution-day guard',100,630,530,100,'#E5EFFB')
box('audit','Yield / NUE / surplus / actual N\nExecuted violations + guard interceptions',50,805,630,110,'#F2F5F8')
edge('e1','input','history','history',exit_x=140/630,offset_x=55);edge('e2','input','prior','current\nobservables',exit_x=490/630,offset_x=-80);edge('e3','history','policy','features',entry_x=90/530,offset_x=55);edge('e4','prior','policy','causal mask\n+ prior logits',entry_x=440/530,offset_x=-85);edge('e5','policy','engine','sampled proposal',offset_x=120);edge('e6','engine','audit','actual outcomes',offset_x=120)
box('plot-title','Dev 5000–5499 | 3 soils',770,125,810,50,style='strokeColor=none;fontSize=24;fontStyle=1;')
# Scatter axes yield 5–10 t/ha; joint 0–100%. Every point uses all 1500 unique scenarios.
x0,y0,w,h=840,745,650,490
selected={n:s['pooled'] for n,s in x['stats'].items() if n in ['N2','prior','prior190'] or n.startswith('full-')}
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
 if name not in ['N2','prior','prior190'] and not name.startswith('full-'):continue
 s=st['pooled'];xx=x0+(s['yield_t_ha']-xmin)/(xmax-xmin)*w;yy=y0-s['joint']*h
 color={'N2':'#526276','prior':'#257DAD','prior190':'#228B53','full-v1':'#BC3D49','full-v2b':'#7B4BAC'}.get(name,'#BC3D49')
 points.append((name,xx,yy,s))
frontier=[pt for pt in points if not any(other[3]['yield_t_ha']>=pt[3]['yield_t_ha'] and other[3]['joint']>=pt[3]['joint'] and (other[3]['yield_t_ha']>pt[3]['yield_t_ha'] or other[3]['joint']>pt[3]['joint']) for other in points)]
frontier.sort(key=lambda pt:pt[1])
for j,(a,b) in enumerate(zip(frontier,frontier[1:])):line('frontier'+str(j),a[1],a[2],b[1],b[2])
for name,xx,yy,s in points:
 color={'N2':'#526276','prior':'#257DAD','prior190':'#228B53','full-v1':'#BC3D49','full-v2b':'#7B4BAC'}.get(name,'#BC3D49')
 box('point-'+name,'',xx-7,yy-7,14,14,color,style='shape=ellipse;')
for j,(name,xx,yy,s) in enumerate(points):
 # Label in separate right-side legend to prevent close-point overlap.
 lc={'N2':'#526276','prior':'#257DAD','prior190':'#228B53','full-v1':'#BC3D49','full-v2b':'#7B4BAC'}.get(name,'#BC3D49')
 display='prior160' if name=='prior' else name
 box('swatch-'+name,'',790,879+j*35,14,14,lc,style='shape=ellipse;')
 box('legend-'+name,f'{display}: {s["yield_t_ha"]:.3f} t/ha | {s["joint"]:.1%}',780,870+j*35,800,32,style='strokeColor=none;fontSize=19;fillColor=none;align=left;spacingLeft=45;fontColor='+lc+';')
box('mean-note','Means: 500 years x 3 soils; RL: 3 seeds. Line connects observed non-dominated points.',50,1080,1550,35,style='strokeColor=none;fontSize=18;')
box('footer','Development comparisons are exploratory. Historical / stress evaluation remains locked.',50,1130,1550,38,style='strokeColor=none;fontSize=18;')
E.ElementTree(mx).write(p,encoding='utf-8',xml_declaration=True)
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=dict(schema_version=1,kind='method-diagram-derived-view',spec=dict(path='scripts/phase3-figure.py',sha256=digest(Path(__file__))),sources=[dict(path=str(q.relative_to(R)),sha256=digest(q)) for q in [R/'reports/phase3_metrics.json',R/'NUE_PCSE-Gym/pcse_gym/envs/phase3.py',R/'tasks/PHASE3_RULING.md']],artifacts={'diagram.drawio':digest(p)},rendered=False,meaning='Actual development means; connecting observed non-dominated points does not prove unseen generalization')
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(p)
