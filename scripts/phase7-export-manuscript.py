"""Render the two Markdown truths into a self-contained parallel reader and two-column TeX."""
from pathlib import Path
import re,json,subprocess,base64,html
R=Path(__file__).resolve().parents[1];O=R/'manuscript/phase7';P=R/'reports/phase7'
def pandoc(text,fmt,*args):
 out=subprocess.run(['pandoc','-f','markdown','-t',fmt,*args],input=text,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,cwd=O);return out.stdout

def bib_records():
 text=(O/'references.bib').read_text();records={}
 for match in re.finditer(r'@\w+\{([^,]+),',text):
  key=match.group(1);start=match.end();next_entry=text.find('\n@',start);chunk=text[start:next_entry if next_entry>=0 else len(text)];fields={}
  for name in ['title','author','year','journal','doi','url']:
   m=re.search(r'\b'+name+r'\s*=\s*\{',chunk)
   if not m:continue
   depth=1;i=m.end();j=i
   while depth:
    if chunk[j]=='{':depth+=1
    elif chunk[j]=='}':depth-=1
    j+=1
   fields[name]=chunk[i:j-1].replace('{','').replace('}','').replace(r'\&','&')
  records[key]=fields
 return records
REFERENCES=bib_records()
def html_doc(md):
 # Publication document layout, not a hosted application. Native MathML needs no external script.
 keys=list(dict.fromkeys(re.findall(r'@([A-Za-z0-9_-]+)',md)));assert set(keys)<=set(REFERENCES)
 def cite(match):
  cited=re.findall(r'@([A-Za-z0-9_-]+)',match.group())
  return '['+', '.join('['+str(keys.index(key)+1)+'](#ref-'+key+')' for key in cited)+']'
 rendered_md=re.sub(r'\[@[^\]]+\]',cite,md);rendered_md=re.sub(r'(\]\([^)]*)\.pdf(\))',r'\1.png\2',rendered_md);result=pandoc(rendered_md,'html5','--mathml')
 refs=[]
 for key in keys:
  d=REFERENCES[key];url=d.get('url','https://doi.org/'+d.get('doi',''));text=d.get('author','')+'. '+d.get('year','')+'. '+d.get('title','')+'. '+d.get('journal','')
  refs.append('<li id="ref-'+key+'"><a href="'+html.escape(url,quote=True)+'">'+html.escape(text)+'</a></li>')
 result+='<ol>'+''.join(refs)+'</ol>' 
 count=0
 def figure(m):
  nonlocal count;count+=1;return '<figcaption>'+('Figure ' if '# Bilateral' in md else '图')+str(count)+'. '+m.group(1)+'</figcaption>'
 result=re.sub(r'<figcaption>(.*?)</figcaption>',figure,result,flags=re.S)
 def image(m):
  path=(O/m.group(1)).resolve();assert path.is_file(),path
  if path.suffix=='.pdf':
   png=path.with_suffix('.png');assert png.exists();path=png
  mime='image/png';return 'src="data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()+'"'
 result=re.sub(r'src="([^"]+)"',image,result);prefix='en-' if '# Bilateral' in md else 'zh-';result=re.sub(r'id="([^"]+)"',lambda m:'id="'+prefix+m.group(1)+'"',result);result=re.sub(r'href="#([^"]+)"',lambda m:'href="#'+prefix+m.group(1)+'"',result);return result
if __name__=='__main__':
 en=(O/'MANUSCRIPT_EN.md').read_text();zh=(O/'MANUSCRIPT_ZH.md').read_text()
 # Markdown image widths preserve original figure canvases in TeX. HTML scales only a screen preview.
 columns=[html_doc(en),html_doc(zh)];parts=[[x for x in re.split(r'(?=<h[123][ >])',body) if x.strip()] for body in columns];assert len(parts[0])==len(parts[1]);document='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AgroMAS bilingual manuscript</title><style>body{margin:0;background:white;color:black;font-family:Georgia,"Times New Roman","Noto Serif CJK SC",serif;line-height:1.65}header{padding:1.2rem 3%;border-bottom:1px solid black}main{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:2.5rem;padding:1rem 3%}section{min-width:0}h1{font-size:1.55rem;line-height:1.35}h2{font-size:1.3rem;border-top:1px solid black;padding-top:.8rem}h3{font-size:1.1rem}p{text-align:justify}img{max-width:100%;height:auto}figure{margin:1.4rem 0}figcaption{font-size:.92rem;line-height:1.5}table{border-collapse:collapse;width:100%;font-size:.87rem}th,td{padding:.35rem;border-bottom:1px solid black;text-align:left}a{color:black;text-decoration:underline}math{font-size:1em}#refs{font-size:.9rem}@media(max-width:70rem){main{grid-template-columns:1fr}}@media print{header{display:none}main{display:block}section{break-after:page}}</style></head><body><header><strong>AgroMAS-Global 中英对照研究稿</strong><p>左侧英文，右侧中文。五张主图均为所选版本，图4保留宽幅原件。数据为自适应复用验证，卫星投影不等于田间土壤实测。本文尚未投稿或发布。</p></header><main>'''+''.join('<section lang="'+lang+'">'+piece+'</section>' for pair in zip(*[[x for x in re.split(r'(?=<h[123][ >])',body) if x.strip()] for body in columns]) for lang,piece in zip(['en','zh-CN'],pair))+'</main></body></html>'
 (O/'MANUSCRIPT_BILINGUAL_GUIDE.html').write_text(document)
 title=en.splitlines()[0][2:];body=en.split('## Abstract\n\n',1)[1];abstract,body=body.split('\n\n## 1 ',1);body='## 1 '+body;main,si=body.split('## Supplementary information',1);si='## Supplementary information'+si;si=si.rsplit('## References',1)[0]
 def headings(text):
  text=re.sub(r'^(#{2,3})\s+(?:\d+(?:\.\d+)?\s+)?',lambda m:'#'*(len(m.group(1))-1)+' ',text,flags=re.M)
  return text.replace('−','-')
 maintex=pandoc(headings(main),'latex','--natbib');sitex=pandoc(headings(si),'latex','--natbib');abstracttex=pandoc(abstract.replace('−','-'),'latex','--natbib')
 # Figure4 is a rotated full-width original246mm canvas, not a shrunk183mm copy.
 chunks=re.split(r'(\\begin\{figure\}.*?\\end\{figure\})',maintex,flags=re.S)
 for i,chunk in enumerate(chunks):
  if chunk.startswith('\\begin{figure}'):
   if 'fig4_global_5region_comparison_and_attribution_C' in chunk:
    chunk=chunk.replace('\\begin{figure}','\\begin{sidewaysfigure*}[p]').replace('\\end{figure}','\\end{sidewaysfigure*}');chunk=re.sub(r'\\includegraphics\[[^\]]*\]',r'\\includegraphics[width=246mm]',chunk)
   else:
    chunk=chunk.replace('\\begin{figure}','\\begin{figure*}[p]').replace('\\end{figure}','\\end{figure*}');chunk=re.sub(r'\\includegraphics\[[^\]]*\]',r'\\includegraphics[width=183mm]',chunk)
   chunks[i]=chunk
 maintex=''.join(chunks)
 preamble=r'''\documentclass[10pt,twocolumn,a4paper]{article}
\usepackage[margin=13.5mm,columnsep=6mm]{geometry}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{mathptmx,amsmath,amssymb,graphicx,booktabs,longtable,array,calc}
\usepackage[numbers,sort&compress]{natbib}
\usepackage{rotating,caption,placeins,hyperref}
\captionsetup{font=footnotesize,skip=2pt}
\hypersetup{hidelinks}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\setlength{\emergencystretch}{3em}
\setlength{\parindent}{1em}
\title{'''+title+r'''}
\author{}
\date{}
\begin{document}
\maketitle
\begin{abstract}
'''+abstracttex+r'''\end{abstract}
'''
 # Main comparison table must remain a proper float without repeating its caption number.
 if '\\begin{longtable}' in maintex:
  mdrows=[line.strip().strip('|').split('|') for line in re.findall(r'^\|.*\|$',main,re.M) if '---' not in line];caption=re.search(r'^: (.+)$',main,re.M).group(1)
  def esc(text):return text.strip().replace('%',r'\%').replace('&',r'\&').replace('_',r'\_')
  tab='\\begin{table*}[t]\n\\centering\\footnotesize\n\\caption{'+esc(caption)+'}\n\\begin{tabular}{lrrr}\n\\toprule\n'
  for i,row in enumerate(mdrows):tab+=' & '.join(esc(x) for x in row)+r' \\'+'\n'+('\\midrule\n' if i==0 else '')
  tab+='\\bottomrule\n\\end{tabular}\n\\end{table*}'
  maintex=re.sub(r'\\begin\{longtable\}.*?\\end\{longtable\}',lambda m:tab,maintex,flags=re.S)
 tex=preamble+maintex+'\n\\FloatBarrier\\clearpage\n\\appendix\n\\onecolumn\n'+sitex+'\n\\FloatBarrier\\clearpage\n\\bibliographystyle{unsrtnat}\n\\bibliography{references}\n\\end{document}\n'
 (O/'main.tex').write_text(tex)
 (P/'manuscript-export-receipt-v7.json').write_text(json.dumps(dict(English=str((O/'MANUSCRIPT_EN.md').relative_to(R)),Chinese=str((O/'MANUSCRIPT_ZH.md').relative_to(R)),HTML=str((O/'MANUSCRIPT_BILINGUAL_GUIDE.html').relative_to(R)),TeX=str((O/'main.tex').relative_to(R)),figures=5,embedded_images_per_language=5,pandoc=subprocess.check_output(['pandoc','--version'],text=True).splitlines()[0]),indent=2));print('Exported self-contained bilingual reader and two-column TeX')
