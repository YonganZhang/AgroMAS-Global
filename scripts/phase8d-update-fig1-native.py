"""Update existing editable Phase8C Figure1 objects; preserve artwork and layout."""
from pathlib import Path
from datetime import datetime
import shutil,json
from pptx import Presentation
from pptx.util import Pt
R=Path(__file__).resolve().parents[1];O=R/'reports/phase8/figures';f=O/'fig1-architecture.pptx'
backup=R/'cache'/('fig1-before-phase8d-'+datetime.now().strftime('%Y%m%dT%H%M%S')+'.pptx');shutil.copy2(f,backup)
p=Presentation(R/'reports/phase8/phase8c-manuscript-archive/figures/fig1-architecture.pptx')
replacements={
 'Private 64-D (P2)':('Private P2: Static3 + AE',15),
 'PCA/Ridge ≤4-D':('Causal anomaly PCA ≤4-D',14),
 'Output correction':('Static3 + accepted anomaly',13),
 '32 joint members':('32 centered residuals',15),
 'Yield, grain N, executed N':('Each region × stage bank',13),
 't−1; LOYO / LORO; OOD: Δy = 0':('t−1; anomaly OOD → Static3',12),
 'TRAIN 1995–2009 analogs\nFirst 7-day rain, then temperature\nNo identity or later truth revealed':('TRAIN 1995–2009 analogs\nCausal temperature de-shift\nFuture descriptors retain warming',16),
 'Composite = profit + 200 P(active joint) − 200 distance\nTier2-Composite: tier masks + composite ranking\nSoft-Coupled: composite without hard-tail masks\nArchived bare: partial profit only\nController OOD / empty set: dose 0, never compliance\nReplan from updated public observations':('Score = profit + 250 P(active joint) − 300 distance\nTier2: corridor → upper-surplus fallback\nSoft-Coupled: score without hard-tail masks\nArchived bare: partial profit only\nUpper NUE penalty ×1.5; surplus margin 2 kg/ha\nController OOD: dose 0, never compliance',15),
 'Typed numerical specialists; nodewise nonanticipative planning, without a global chance/CVaR optimality claim.':('Full weather × 32 residual integration; nonanticipative planning; no global chance/CVaR optimality claim.',15)}
changed=[]
for s in p.slides[0].shapes:
 if not s.has_text_frame or s.text not in replacements:continue
 old=s.text;new,size=replacements[old]
 # Existing simple text boxes contain a single styled run; keep object geometry.
 first=s.text_frame.paragraphs[0];run=first.runs[0] if first.runs else first.add_run();run.text=new
 for r in list(first.runs)[1:]:r.text=''
 for paragraph in list(s.text_frame.paragraphs)[1:]:paragraph.text=''
 run.font.size=Pt(size);changed.append(dict(before=old,after=new))
assert len(changed)==len(replacements),(len(changed),len(replacements))
p.save(f);assert all(s.left>=0 and s.top>=0 and s.left+s.width<=p.slide_width and s.top+s.height<=p.slide_height for s in p.slides[0].shapes)
(O/'phase8d-fig1-edit-receipt.json').write_text(json.dumps(dict(source='Phase8C archived native PPTX',modified_text_objects=changed,artwork_unchanged=True,geometry_bounds_passed=True,backup=str(backup.relative_to(R))),indent=2));print('Updated',len(changed),'native text objects')
