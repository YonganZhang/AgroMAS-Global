"""Artifact-only verification: no simulation, data/model writes, manuscript compilation."""
from pathlib import Path
import json,hashlib,ast,re,subprocess,zipfile
import fitz
import importlib.util
from matplotlib.colors import to_rgb
spec=importlib.util.spec_from_file_location('muted','/mnt/data/yongan-admin-2/.ai-shared/skills/share-sci-plot/references/fpv_v16_muted_style.py');sty=importlib.util.module_from_spec(spec);spec.loader.exec_module(sty)
allowed_dark={int(''.join(f'{round(v*255):02x}' for v in to_rgb(sty.text_color(c))),16) for c in sty.PALETTE_SCI_ROSE_SLATE_10+['#E8985E','#E07A84','#5B88A8','#947EB0','#639A88']}
from lxml import etree
R=Path(__file__).resolve().parents[1];O=R/'reports/phase8/figures';baseline=json.loads((O/'phase8d-redesign-source-baseline.json').read_text());actual={k:hashlib.sha256((R/k).read_bytes()).hexdigest() for k in baseline};assert actual==baseline
captions=json.loads((O/'phase8d-captions.json').read_text());assert captions['integration_status']['figure_batch_only'] and captions['integration_status']['not_submission_ready'];assert captions['P2_inference']['Holm_p']
names=['fig2-g1','fig2-p1-regimes','figs2-g3-subsidy','fig3-p2-transfer','fig4-factorial-stress','fig5-deployment-closure']
supp_names=['figs3-price-subsidy','figs4-policy-scorecard','figs5-p1-all-regimes','figs6-p2-admission-mse','figs7-stress-180cell-grid','figs8-closure-readout-audit']
all_quant=names+supp_names;artifacts={};fontnames=set()
for name in all_quant:
 audit=json.loads((O/(name+'-render-audit.json')).read_text());assert audit['descriptive_titles'] is False and audit['black_regular_text'] is True
 pdf=fitz.open(O/(name+'.pdf'));assert len(pdf)==1
 for f in pdf[0].get_fonts():
  fontnames.add(f[3]);assert 'TimesNewRoman' in f[3].replace('-',''),f
  assert pdf.extract_font(f[0])[3],(name,'font not embedded',f)
 for block in pdf[0].get_text('dict')['blocks']:
  for line in block.get('lines',[]):
   for s in line['spans']:
    if s['color']==0xffffff:
     assert name in all_quant,(name,s['text'])
     approved=[v for v in audit.get('contrast_labels',[]) if v['text']==s['text'] and sty.contrast_text(v['background'])=='white']
     assert approved,(name,s['text'],'unapproved white text')
    else:assert s['color'] in ({0}|allowed_dark),(name,s['text'],s['color'])
    if s['flags']&16:assert s['text'] in list('abcdefgh'),(name,s['text'])
 if name in names:
  for ext in ['png','pdf','svg']:artifacts[str((O/(name+'.'+ext)).relative_to(R))]=hashlib.sha256((O/(name+'.'+ext)).read_bytes()).hexdigest()
for p in (R/'scripts').glob('phase8d-plot-*.py'):
 tree=ast.parse(p.read_text());assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in ['set_title','suptitle'] for n in ast.walk(tree)),p
ppt=O/'fig1-architecture.pptx';ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main','p':'http://schemas.openxmlformats.org/presentationml/2006/main'}
with zipfile.ZipFile(ppt) as z:
 t=etree.fromstring(z.read('ppt/slides/slide1.xml'));text=t.xpath('//a:t/text()',namespaces=ns);joined=' '.join(text)
 for s in ['Agent 1: Spatial Twin Specialist','Agent 2: Climate Forecast Specialist','Agent 3: Urban Eco-Safety Specialist','Agent 4: Socio-Economic Policy Specialist','Agent 5: Core Agronomic Control Specialist','Partial profit + 250 P(active joint) − 300 distance']:
  assert s in joined,s
 for x,n in [('a1',1),('a2',2),('a3',4)]:assert text.count(x)==n,(x,text.count(x))
 assert 'a0' not in text
 shapes=len(t.xpath('//p:sp',namespaces=ns));pictures=len(t.xpath('//p:pic',namespaces=ns));assert shapes>60 and pictures>=7
 for f in t.xpath('//a:latin/@typeface',namespaces=ns):assert f=='Times New Roman',f
for ext in ['png','pdf','pptx','svg']:p=O/('fig1-architecture.'+ext);artifacts[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
for k in [1,2,3]:
 p=O/f'fig1-candidates/candidate-b-v2-{k}.png';assert p.is_file() and p.with_suffix('.prompt.txt').is_file()
 sources=sorted(Path('/mnt/data/yongan-admin-2/.codex-homes/顶刊论文-3fa034/generated_images').rglob('*.png'))
 assert any(hashlib.sha256(x.read_bytes()).hexdigest()==hashlib.sha256(p.read_bytes()).hexdigest() for x in sources),p
# Guard protected binary/statistical/LaTeX files against task-start commit while allowing updated Markdown/BIB/HTML drafts.
start_commit='d57698d93721eb49d107485d18d5adaea500077d'
protected={}
editable_drafts={'manuscript/phase8/zh.md','manuscript/phase8/en.md','manuscript/phase8/references.bib','manuscript/phase8/paper-bilingual-en-zh.html'}
for name in subprocess.check_output(['git','ls-tree','-r','--name-only',start_commit,'manuscript/phase8'],cwd=R,text=True).splitlines():
 current=(R/name).read_bytes()
 if name in editable_drafts:
  assert len(current)>500,(name,'unexpectedly empty editable draft')
 else:
  expected=subprocess.check_output(['git','show',start_commit+':'+name],cwd=R);assert expected==current,name
 protected[name]=hashlib.sha256(current).hexdigest()
primary=Path('/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体');code_repos={}
for name,expected in [('NUE_PCSE-Gym','c242b6dd62d853c5888144bab864f9a509599633'),('pcse','d1fe6d29de828033b850ec51d994988d8d6d406f')]:
 repo=primary/name;commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip();status=subprocess.check_output(['git','status','--porcelain'],cwd=repo,text=True);assert commit==expected and not status,(name,commit,status);code_repos[name]={'path':str(repo),'commit':commit,'clean':True}
feature=primary/'NUE_PCSE-Gym/pcse_gym/agromas/features.py'
static3={'source':str(feature),'sha256':hashlib.sha256(feature.read_bytes()).hexdigest(),'definition':'soil_context: SMfromPF at pF2 and pF4.2, CONDfromPF at pF-1; field capacity, wilting point, conductivity','inspected_lines':'19-26','source_read_only':True}
# CEA v4 guards extend earlier frozen-data protection to all selected raw images and PPTX.
cea=json.loads((O/'phase8d-cea-v4-protected-baseline.json').read_text())
for name,digest in cea['sha256'].items():
 if name in editable_drafts:continue
 assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
for name in ['reports/phase8/phase8d-case-metrics-seed-averaged.csv','reports/phase8/phase8d-G1-radius-interpretation.json','reports/phase8/phase8d-root-cause-verification.json']:
 assert (R/name).read_bytes()==subprocess.check_output(['git','show',cea['start_commit']+':'+name],cwd=R),name
v4=json.loads((O/'phase8d-fig1-v4-raw-receipt.json').read_text())
for item in v4['variants']:
 p=R/item['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'];assert p.with_suffix('.prompt.txt').exists()
 assert p.read_bytes()==Path(item['original_imagegen_output']).read_bytes()
assert (O/'fig1-candidates/candidate-b-v4-best.png').read_bytes()==(R/v4['selected']).read_bytes()
v5=json.loads((O/'phase8d-cea-v5-protected-baseline.json').read_text())
for name,digest in v5.items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
# Independent frozen-source arithmetic and output geometry audit.
import pandas as pd,numpy as np
from PIL import Image
case=pd.read_csv(R/'reports/phase8/phase8d-case-metrics-seed-averaged.csv')
ref=case[(case.source=='NASA')&(case.cohort=='Former-Held-Out')&(case.benchmark=='P1')&(case.climate=='Historical')&(case.cap==40)&(case.price_multiplier==1)&(case.subsidy==0)&(case.tax==0)&(case.track=='Sensorless')&(case['mode']=='soft')]
matched=ref[ref.policy=='TreeMLP'].merge(ref[ref.policy=='remove-climate'],on=['region','year'],suffixes=('_p','_r'));assert len(matched)==31
full50=case[(case.policy=='TreeMLP')&(case.track=='Full-Telemetry')&(case.cap==50)];assert full50.empty
readouts=json.loads((R/'reports/phase8/phase8d-full-TRAIN-physical-decoding.json').read_text());readout_targets=['final_organic_N_kg_ha','final_soil_C_kg_ha','native_net_mineralization_N_kg_ha','final_mineral_N_kg_ha','native_Nloss_kg_ha'];matrix=np.array([[cell[t]['latent_OOF_R2'] for t in readout_targets] for tr in ['Sensorless','Full-Telemetry'] for cell in readouts['results'][tr+'-mlp']['by_region'].values()]);assert matrix.shape==(10,5) and (matrix[:,:3]>0).all() and int((matrix<0).sum())==6
geometry={}
for name in all_quant:
 doc=fitz.open(O/(name+'.pdf'));spans=[(s['text'],fitz.Rect(s['bbox'])) for b in doc[0].get_text('dict')['blocks'] for line in b.get('lines',[]) for s in line['spans'] if s['text'].strip()];overlaps=[]
 for i,(text_i,box_i) in enumerate(spans):
  assert doc[0].rect.contains(box_i),(name,text_i,'out of page')
  for text_j,box_j in spans[i+1:]:
   intersection=box_i&box_j
   if not intersection.is_empty and intersection.get_area()>.2*min(box_i.get_area(),box_j.get_area()):overlaps.append([text_i,text_j])
 assert not overlaps,(name,overlaps)
 dpi=Image.open(O/(name+'.png')).info['dpi'];assert all(abs(x-450)<.1 for x in dpi),dpi
 geometry[name]={'overlapping_text_spans_over_20pct':0,'out_of_page_spans':0,'dpi':dpi}
facts={'matched_climate_n':len(matched),'matched_region_equal_pct':(matched.groupby('region')[['joint_p','joint_r']].mean().mean()*100).to_dict(),'matched_pooled_pct':(matched[['joint_p','joint_r']].mean()*100).to_dict(),'Full_cap50_record_count':len(full50),'Full_cap50_display':'Not evaluated, OptionA confirmed by leader','heatmap_shape':list(matrix.shape),'required_positive_cells':int((matrix[:,:3]>0).sum()),'minimum_required_R2':float(matrix[:,:3].min()),'negative_exploratory_cells':int((matrix[:,3:]<0).sum()),'geometry':geometry}
# Validate new soil-budget sources independently from the plotting process.
budget=json.loads((O/'phase8d-cea-v5-stock-budget.json').read_text())
for name,digest in budget['native_result_sha256'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,name
facts['verified_native_budget_sources']=len(budget['native_result_sha256'])
facts['soil_budget']=budget['budget']
facts['soil_budget_qualification']=budget['qualification']
assert [v['label'] for v in budget['budget']]==['Soft','PPO','DVS · Full','Bare']
assert all(v['drawdown']>0 and 0<v['adjusted']<.5 for v in budget['budget'])
low=ref[(ref.policy=='TreeMLP')&(ref.joint==0)&(ref.NUE<=.9)&(ref.S_N<=40)&(ref.Executed_N>0)]
assert len(low)==2 and set(low.region)=={'usa_kansas_wichita'}
facts['extra_low_NUE_regime_count']=len(low)
facts['missing_bare_2x']=len(case[(case.policy=='TreeMLP')&(case['mode']=='hard-bare-tier2')&(case.price_multiplier==2)])
assert facts['missing_bare_2x']==0
(O/'phase8d-cea-v5-data-audit.json').write_text(json.dumps(facts,indent=2))

out={'status':'PASS','immutable_sources_unchanged':actual,'protected_manuscript_start_commit':start_commit,'protected_manuscript_files':protected,'code_repositories_unchanged':code_repos,'Static3_source_proof':static3,'scope':'CEA v5 artifact-only verification; manuscript/PPTX protected, no simulations.' , 'cea_v4_protected_files':len(cea['sha256']),'cea_start_commit':cea['start_commit'],'v4_raw_candidates_byte_identical':True,'v5_protected_files':len(v5),'cea_data_audit':'reports/phase8/figures/phase8d-cea-v5-data-audit.json','artifact_sha256':artifacts,'quantitative_pdf_fonts':sorted(fontnames),'native_fig1_shapes':shapes,'native_fig1_pictures':pictures,'fig1_action_counts':{'a1':1,'a2':2,'a3':4},'no_simulation_or_manuscript_compile':True,'raw_candidates_preserved_byte_for_byte':True,'limitations':['V4 raw AI candidates are visual drafts with inherited scientific simplifications; historical PPTX is untouched and is not a v4 conversion.','LibreOffice rendering and OPC validation do not prove desktop PowerPoint behavior.','Original frozen publication integrity ledger remains unchanged; this is a separate figure-only artifact audit.']}
(O/'phase8d-redesign-verification.json').write_text(json.dumps(out,indent=2));print(json.dumps({'status':'PASS','artifact_count':len(artifacts),'immutable_source_count':len(actual),'native_shapes':shapes,'pictures':pictures}))
