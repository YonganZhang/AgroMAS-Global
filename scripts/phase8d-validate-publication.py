"""Programmatic publication integrity and bounds; visual review is separate."""
from pathlib import Path
import json,hashlib,re,xml.etree.ElementTree as ET
import fitz
from PIL import Image
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';F=P/'figures';M=R/'manuscript/phase8';files=[];issues=[]
for name in ('fig1-architecture','fig2-p1-regimes','fig3-p2-transfer','fig4-factorial-stress','fig5-deployment-closure','fig2-g1','figs2-g3-subsidy'):
 for ext in ('png','pdf','svg'):
  f=F/(name+'.'+ext);assert f.is_file() and f.stat().st_size>100
  if ext=='png':
   with Image.open(f) as im:im.verify()
  elif ext=='svg':ET.parse(f)
  else:
   doc=fitz.open(f);assert len(doc)==1
   for page in doc:
    for b in page.get_text('blocks'):
     if b[0]<-.5 or b[1]<-.5 or b[2]>page.cropbox.width+.5 or b[3]>page.cropbox.height+.5:issues.append(dict(file=str(f.relative_to(R)),page=page.number+1,bounds=list(b[:4])))
  files.append(dict(path=str(f.relative_to(R)),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
for name in ('en','zh','supplement'):
 f=M/(name+'.pdf');d=fitz.open(f);assert len(d)>3
 for page in d:
  for b in page.get_text('blocks'):
   if b[0]<-.5 or b[1]<-.5 or b[2]>page.cropbox.width+.5 or b[3]>page.cropbox.height+.5:issues.append(dict(file=str(f.relative_to(R)),page=page.number+1,bounds=list(b[:4])))
 text=' '.join(' '.join(page.get_text().split()) for page in d);text=re.sub(r'-\s+', '-',text)
 if name in ('en','zh'):assert '452.02' in text and '549.91' in text,'Cohort correction missing from PDF'
 if name=='en':assert 'pooled farm-year sign-test' in text,'Exact-test weighting missing from PDF'
 if name=='supplement':assert 'equal-region means' in text,'Table weighting missing from PDF'
 log=(M/(name+'.log')).read_text();assert 'Missing character:' not in log and 'Undefined control sequence' not in log and 'Overfull' not in log,name
 files.append(dict(path=str(f.relative_to(R)),pages=len(d),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
s=json.loads((P/'phase8d-core-statistics.json').read_text());assert s['mass_all_configurations']['all_passed'] and s['mass_all_configurations']['scored_case_configurations']==18268
bounds=json.loads((F/'phase8d-figure-source-and-bounds.json').read_text())
for name,d in bounds['figures'].items():
 for title in d['titles']:assert title['center']=='' and (title['left'] or name=='fig4-factorial-stress'),(name,title)
receipt=dict(passed=not issues,issues=issues,files=files,rendered_visual_review='Separate Gemini review required; not replaced by these checks',N_residual_max=s['mass_all_configurations']['max_N'],C_residual_max=s['mass_all_configurations']['max_C'])
(P/'phase8d-publication-integrity.json').write_text(json.dumps(receipt,indent=2));assert not issues,issues;print('PASS: publication formats, text/page bounds, glyphs, titles and mass-audit linkage')
