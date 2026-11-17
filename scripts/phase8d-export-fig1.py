"""Export the rebuilt hybrid deck into the formal single-page figure and a comparison render.
Dependencies: python-pptx, Pillow, PyMuPDF; system LibreOffice and pdftoppm.
Run phase8d-build-fig1-hybrid.py first; the deck retains both editable and reference slides.
"""
from pathlib import Path
import subprocess,sys,tempfile
import pymupdf
R=Path(__file__).resolve().parents[1];O=R/'reports/phase8/figures';A=O/'fig1-assets'
subprocess.run([sys.executable,'/mnt/data/yongan-admin-2/.ai-shared/skills/real-ppt/scripts/normalize_and_validate_pptx.py','--in-place',str(O/'fig1-architecture.pptx')],check=True,stdout=(A/'pptx-validation.json').open('w'))
with tempfile.TemporaryDirectory(prefix='phase8d-lo-') as tmp:
 subprocess.run(['libreoffice','-env:UserInstallation=file://'+tmp+'/profile','--headless','--convert-to','pdf','--outdir',tmp,str(O/'fig1-architecture.pptx')],check=True,capture_output=True)
 paired=pymupdf.open(Path(tmp)/'fig1-architecture.pdf');assert len(paired)==2;paired.save(A/'paired-slide-render.pdf');paired[1].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).save(A/'reference-slide.png')
 one=pymupdf.open();one.insert_pdf(paired,from_page=0,to_page=0);one.save(O/'fig1-architecture.pdf');(O/'fig1-architecture.svg').write_text(one[0].get_svg_image(text_as_path=False))
subprocess.run(['pdftoppm','-f','1','-singlefile','-scale-to','2600','-png',str(O/'fig1-architecture.pdf'),str(O/'fig1-architecture')],check=True)
