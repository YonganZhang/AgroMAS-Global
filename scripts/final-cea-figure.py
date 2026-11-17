"""Real-data quantitative four-panel figure, shared SVG and native editable mxGraph primitives."""
import pathlib,json,math,statistics,html,xml.etree.ElementTree as E,subprocess
import numpy as np
R=pathlib.Path(__file__).resolve().parents[1];D=R/'figures/phase4-final';D.mkdir(parents=True,exist_ok=True)
W,H=2500,1900;svg=[];mx=E.Element('mxfile',host='app.diagrams.net');dia=E.SubElement(mx,'diagram',name='Frozen CEA results');graph=E.SubElement(dia,'mxGraphModel',dx=str(W),dy=str(H),grid='0',page='1',pageWidth=str(W),pageHeight=str(H));root=E.SubElement(graph,'root');E.SubElement(root,'mxCell',id='0');E.SubElement(root,'mxCell',id='1',parent='0');counter=1
COL=['#C8D1D7','#E8B8AE','#D67E7D'];DROUGHT=['#4C7A99','#FFF0C4'];MC={'full4':'#5882A6','utilityprior':'#B8525A','cf-gru':'#5E9680'}
def cell(x,y,w,h,style,value=''):
 global counter
 counter+=1;c=E.SubElement(root,'mxCell',id=str(counter),value=value,style=style,vertex='1',parent='1');E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(max(w,.01)),height=str(max(h,.01)),attrib={'as':'geometry'})
def rect(x,y,w,h,c,stroke='none'):
 svg.append(f'<rect x="{x}" y="{y}" width="{max(0,w)}" height="{h}" fill="{c}" stroke="{stroke}"/>');cell(x,y,w,h,f'rounded=0;fillColor={c};strokeColor={stroke};')
def line(x,y,xx,yy,c='#000000',width=2,dashed=False):
 dash='7 5' if dashed else 'none'
 svg.append(f'<line x1="{x}" y1="{y}" x2="{xx}" y2="{yy}" stroke="{c}" stroke-width="{width}" stroke-dasharray="{dash}"/>')
 global counter
 counter+=1;n=E.SubElement(root,'mxCell',id=str(counter),style=f'endArrow=none;startArrow=none;strokeColor={c};strokeWidth={width};dashed={int(dashed)};dashPattern=7 5;',edge='1',parent='1');g=E.SubElement(n,'mxGeometry',relative='1',attrib={'as':'geometry'});E.SubElement(g,'mxPoint',x=str(x),y=str(y),attrib={'as':'sourcePoint'});E.SubElement(g,'mxPoint',x=str(xx),y=str(yy),attrib={'as':'targetPoint'})
def text(x,y,s,size=29,anchor='start',bold=False):
 s=str(s)
 if not s:return
 svg.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" dominant-baseline="middle" font-family="Times New Roman" font-size="{size}" font-weight="{"bold" if bold else "normal"}" fill="#000000">{html.escape(s)}</text>')
 w=max(size*.53*len(s)+16,30);left=x if anchor=='start' else x-w if anchor=='end' else x-w/2
 cell(left,y-size*.7,w,size*1.4,f'text;html=0;whiteSpace=wrap;overflow=visible;fillColor=none;strokeColor=none;fontColor=#000000;fontFamily=Times New Roman;fontSize={size};fontStyle={1 if bold else 0};align={"left" if anchor=="start" else "right" if anchor=="end" else "center"};verticalAlign=middle;',s)
def circle(x,y,r,c,fill=True):
 svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c if fill else "#FFFFFF"}" stroke="{c}" stroke-width="2"/>');cell(x-r,y-r,2*r,2*r,f'ellipse;fillColor={c if fill else "#FFFFFF"};strokeColor={c};strokeWidth=2;')
def marker(x,y,r,c,soil,fill=True):
 if soil=='default':return circle(x,y,r,c,fill)
 if soil=='slow':return rect(x-r,y-r,2*r,2*r,c if fill else '#FFFFFF',c)
 points=f'{x},{y-r} {x-r},{y+r} {x+r},{y+r}'
 svg.append(f'<polygon points="{points}" fill="{c if fill else "#FFFFFF"}" stroke="{c}" stroke-width="2"/>');cell(x-r,y-r,2*r,2*r,f'shape=triangle;direction=north;fillColor={c if fill else "#FFFFFF"};strokeColor={c};strokeWidth=2;')
def axis(x,y,w,h,xmin,xmax,ymin,ymax,xt,yt,xlabel,ylabel):
 fx=lambda v:x+(v-xmin)/(xmax-xmin)*w;fy=lambda v:y+h-(v-ymin)/(ymax-ymin)*h
 line(x,y,x,y+h);line(x,y+h,x+w,y+h)
 for v in xt:line(fx(v),y+h,fx(v),y+h+8);text(fx(v),y+h+42,f'{v:g}',26,'middle')
 for v in yt:line(x-8,fy(v),x,fy(v));text(x-15,fy(v),f'{v:g}',26,'end')
 text(x+w/2,y+h+88,xlabel,29,'middle');text(x,y-40,ylabel,29)
 return fx,fy

def main():
 q=json.loads((R/'reports/final_cea_metrics.json').read_text());raw=json.loads((R/'reports/phase4-heldout-final.json').read_text());spl=q['heldout']['splits'];dev=q['Dev'];names=['utilityprior','cf-gru','full4','guided','masked','corrected','raw','old_SM-adaptiveprior','prior190','N2-PA'];label={'utilityprior':'CUO-Forest','cf-gru':'CUO-GRU','full4':'Full4','guided':'Guided PPO','masked':'Masked PPO','corrected':'Corrected PPO','raw':'Raw PPO','old_SM-adaptiveprior':'SM-adaptive prior','prior190':'Prior190','N2-PA':'N2-PA'}
 text(40,45,'a',46,bold=True);text(1300,45,'b',46,bold=True);text(40,1000,'c',46,bold=True);text(1300,1000,'d',46,bold=True)
 # a: means with between-training-seed SD for three-seed neural assets only.
 x,y,w,h=350,150,800,660
 for i,(title,c) in enumerate(zip(['Dev','Historical','Stress'],COL)):rect(350+i*245,79,30,18,c);text(393+i*245,90,title,29)
 for i,n in enumerate(names):
  yy=y+i*64;text(325,yy+21,label[n],29,'end')
  for j,tables in enumerate([dev['tables'],spl['historical']['tables'],spl['stress']['tables']]):
   v=100*tables[n]['pooled']['joint'];rect(x,yy+j*16, v/100*w,12,COL[j]);sd=tables[n]['seed_std']['joint']
   if sd is not None:
    lo=max(0,v-100*sd);hi=min(100,v+100*sd);line(x+lo/100*w,yy+j*16+6,x+hi/100*w,yy+j*16+6,width=1.5)
 for v in range(0,101,20):xx=x+v/100*w;line(xx,805,xx,815);text(xx,847,v,27,'middle')
 line(x,150,x,805,width=1.5);line(x,805,x+w,805);text(x+w/2,900,'Joint compliance (%)',31,'middle')
 # b: x surplus, y yield, bubble radius proportional sqrt(CVaR), both benchmark splits.
 keys=['N2-PA','prior190','old_SM-adaptiveprior','full4','utilityprior','cf-gru'];colors=['#162830','#8E7CA6','#A4BED1','#5882A6','#B8525A','#5E9680'];vals=[spl[s]['tables'][n]['pooled'] for s in ['historical','stress'] for n in keys];xx=[v['surplus_kg_ha'] for v in vals];yy=[v['yield_t_ha'] for v in vals];xmin=min(0,math.floor(min(xx)/20)*20);xmax=math.ceil(max(xx)/20)*20;ymin=math.floor(min(yy)*2)/2;ymax=math.ceil(max(yy)*2)/2
 fx,fy=axis(1440,235,950,525,xmin,xmax,ymin,ymax,np.arange(xmin,xmax+1,20),np.arange(ymin,ymax+.01,.5),'Mean N surplus (kg/ha)','Mean grain yield (t/ha)')
 for j,s in enumerate(['historical','stress']):
  for n in [k for k in keys if k!='utilityprior']+['utilityprior']:
   c=colors[keys.index(n)];p=spl[s]['tables'][n]['pooled'];circle(fx(p['surplus_kg_ha']),fy(p['yield_t_ha']),max(4,math.sqrt(max(0,p['cvar10_surplus']))*1.7),c,j==1)
 for i,(n,c) in enumerate(zip(keys,colors)):
  bx=1410+(i%3)*330;by=89+(i//3)*47;circle(bx,by,9,c);text(bx+22,by,label[n],26)
 text(1440,895,'Open Historical; filled Stress',27)
 text(1440,940,'CVaR10 (kg/ha)',27)
 for bx,v in [(1740,40),(1900,80)]:circle(bx,940,math.sqrt(v)*1.7,'#000000',False);text(bx+30,940,v,27)
 # c: frozen final-dose decisions binned by observed SM and past rain. No PCSE rerun.
 final={}
 for rec in raw['records']:
  if rec['model'] not in MC:continue
  for e in rec['events']:
   if e['year']>=5500 and .62<=e['DVS']<=.88:
    final.setdefault((rec['model'],rec['soil']),[]).append(e)
 for j,(field,xlabel) in enumerate([('SM','Top-layer soil moisture (m³/m³)'),('past_rain','Previous 7-day mean rain (mm/day)')]):
  points=[float(e[field])*(100 if field=='past_rain' else 1) for es in final.values() for e in es];a,b=(.1,.75) if field=='SM' else (0.,12.);ticks=[.1,.3,.5,.7] if field=='SM' else [0,4,8,12];fx,fy=axis(140+j*590,1180,480,460,a,b,155,215,ticks,[160,180,200,210],xlabel,'Final total N (kg/ha)' if j==0 else '')
  for name in ['full4','cf-gru','utilityprior']:
   for soil in ['default','fast','slow']:
    es=final.get((name,soil),[]);vx=np.array([e[field]*(100 if field=='past_rain' else 1) for e in es]);vn=np.array([e['cumulative_N']+10*e['executed'] for e in es]);edges=np.quantile(vx,[0,.25,.5,.75,1]) if len(es) else []
    last=None
    for k in range(4):
     mask=(vx>=edges[k])&(vx<=edges[k+1] if k==3 else vx<edges[k+1]);
     if not mask.any():continue
     p=(fx(float(vx[mask].mean())),fy(float(vn[mask].mean())))
     if last:line(*last,*p,MC[name],2,dashed=name=='cf-gru')
     marker(*p,10 if name=='cf-gru' else 6,MC[name],soil,fill=name!='cf-gru');last=p
 for i,n in enumerate(MC):line(150+i*330,1060,188+i*330,1060,MC[n],4,dashed=n=='cf-gru');text(201+i*330,1060,label[n],28)
 for i,soil in enumerate(['default','fast','slow']):marker(160+i*330,1105,8,'#000000',soil,False);text(185+i*330,1105,soil.capitalize(),27)
 # d: drought stress compliance and exact model-input sensitivity (two rainfall-selected cases).
 methods=['prior190','full4','utilityprior','cf-gru'];fx,fy=axis(1450,1150,900,280,0,4,0,100,[],[0,50,100],'','Joint compliance (%)')
 # Native categorical ticks: no hidden numeric cells or cover-up patches.
 for i,n in enumerate(methods):
  for j,s in enumerate(['stress_q10','stress_q25']):
   value=100*spl[s]['tables'][n]['pooled']['joint'];rect(fx(i+.15+j*.35),fy(value),65,1430-fy(value),DROUGHT[j],stroke='#000000')
  line(fx(i+.5),1430,fx(i+.5),1438);text(fx(i+.5),1473,label[n],27,'middle')
 for i,(s,c) in enumerate(zip(['q10','q25'],DROUGHT)):rect(1850+i*215,1074,26,18,c,stroke='#000000');text(1890+i*215,1084,s,27)
 rect(1520,1510,20,16,MC['utilityprior']);text(1555,1518,'CUO-Forest',26)
 phi={k:[] for k in ['LAI','SM','RAIN','IRRAD','TMIN']}
 for case in q['attribution']:
  if case['policy']=='utilityprior':
   for e in case['decisions']:
    for k,v in e.get('shapley',{}).items():phi[k].append(abs(v))
 av={k:statistics.mean(v) if v else 0 for k,v in phi.items()};maximum=max(av.values()) or 1
 for i,(k,v) in enumerate(av.items()):text(1500,1550+i*49,k,27,'end');rect(1520,1539+i*49,700*v/maximum,22,MC['utilityprior']);text(2245,1550+i*49,f'{v:.3f}',26)
 text(1520,1835,'Mean |Shapley value| of selected-dose utility score',27)
 (D/'diagram.drawio').write_bytes(E.tostring(mx,encoding='utf-8',xml_declaration=True));(D/'diagram.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><rect width="100%" height="100%" fill="white"/>'+''.join(svg)+'</svg>')
 subprocess.run(['rsvg-convert','-w','4000','-o',str(D/'diagram.png'),str(D/'diagram.svg')],check=True)
 (D/'caption.md').write_text('Four-panel frozen-policy audit. CUO-Forest denotes utilityprior; CUO-GRU denotes the exploratory frozen cf-gru residual; Full4 denotes the bundled on-policy variant. a: mean joint compliance across Dev, Historical and Stress; thin horizontal marks show SD across 3 training seeds where available, not confidence intervals. Deterministic controls have one fitted policy. Zero-length Raw and Corrected bars represent measured zero compliance, not missing data. b: held-out scenario means, open Historical and filled Stress; marker area is proportional to upper-tail CVaR10 surplus, with reference bubbles in kg/ha; larger means worse tail risk. Coincident bubbles reflect similar results and are not jittered. c: Stress final-stage total N versus observed top-layer SM and preceding 7-day mean rain; quartile-bin means within each policy and soil, with 3 neural seeds pooled. Circles denote default, triangles fast, and squares slow soil. CUO-GRU uses dashed lines and larger open markers; CUO-Forest is drawn on top with solid lines and smaller filled markers so coincident policies remain identifiable. This is descriptive model-input association, not causal intervention. d upper: Stress q10 and q25 drought compliance, using TRAIN-only rainfall thresholds. d lower: CUO-Forest mean absolute exact 5-group Shapley sensitivity of selected-dose utility score for the rainfall-extreme dry-fast and wet-default cases, using TRAIN-median background and fixed other inputs. These are model sensitivities, not field causal effects; neither case was selected for policy success. Historical overall and q10 contrasts versus Prior190 remain uncertain, while q25 has a positive paired effect. Full counts, paired-year 3,000-bootstrap intervals, unadjusted Wilcoxon tests and small-n warnings are in final_cea_metrics.json. All text uses Times New Roman and black; bars, points, axes and labels are native editable drawio primitives.\n')
 parsed=E.fromstring((D/'diagram.svg').read_text());texts=list(parsed.iter('{http://www.w3.org/2000/svg}text'))
 assert texts and all(t.attrib['font-family']=='Times New Roman' and t.attrib['fill']=='#000000' for t in texts)
 assert all(t.attrib['font-weight']=='normal' or t.text in ['a','b','c','d'] for t in texts)
 assert not list(root.iter('image')) and all(c.attrib.get('style','').find('image=')<0 for c in root.iter('mxCell'))
 font=subprocess.check_output(['fc-match','-f','%{file}','Times New Roman'],text=True).strip();assert 'Times' in pathlib.Path(font).name
 (D/'validation.json').write_text(json.dumps(dict(actual_svg_text_nodes=len(texts),native_mx_cells=len(list(root.iter('mxCell'))),all_text_Times_New_Roman=True,all_text_black=True,bold_only_panel_letters=True,embedded_bitmap_cells=0,font_file=font,PNG_width_px=4000,scope='Native SVG and mxGraph validation; not matplotlib font helpers'),indent=2))
 print('Native editable four-panel figure:',D)
if __name__=='__main__':main()
