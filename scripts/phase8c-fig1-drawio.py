from pathlib import Path
import xml.etree.ElementTree as E
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
R=Path(__file__).resolve().parents[1];o=R/'reports/phase8/figures';p=Presentation(o/'fig1-architecture.pptx');root=E.Element('mxfile',host='app.diagrams.net');d=E.SubElement(root,'diagram',name='Architecture');m=E.SubElement(d,'mxGraphModel',pageWidth='1600',pageHeight='1000');r=E.SubElement(m,'root');E.SubElement(r,'mxCell',id='0');E.SubElement(r,'mxCell',id='1',parent='0')
for i,s in enumerate(p.slides[0].shapes,2):
 x,y,w,h=[v/914400*100 for v in [s.left,s.top,s.width,s.height]]
 if s.shape_type==MSO_SHAPE_TYPE.LINE:
  x,y,X,Y=[v/914400*100 for v in [s.begin_x,s.begin_y,s.end_x,s.end_y]]
  w,h=X-x,Y-y
  c=E.SubElement(r,'mxCell',id=str(i),edge='1',parent='1',style='endArrow=block;strokeColor=#617889;');g=E.SubElement(c,'mxGeometry',relative='1',attrib={'as':'geometry'});E.SubElement(g,'mxPoint',x=str(x),y=str(y),attrib={'as':'sourcePoint'});E.SubElement(g,'mxPoint',x=str(x+w),y=str(y+h),attrib={'as':'targetPoint'})
 else:
  value=s.text if s.has_text_frame else '';style='text;html=0;whiteSpace=wrap;fontFamily=Times New Roman;fontColor=#000000;fontSize=16;' if value else 'rounded=1;fillColor=#EDF2F5;strokeColor=#617889;'
  c=E.SubElement(r,'mxCell',id=str(i),vertex='1',parent='1',value=value,style=style);E.SubElement(c,'mxGeometry',x=str(x),y=str(y),width=str(w),height=str(h),attrib={'as':'geometry'})
E.ElementTree(root).write(o/'fig1-architecture.drawio',encoding='utf-8',xml_declaration=True)
