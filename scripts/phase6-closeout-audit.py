"""Read-only acceptance of preserved assets, raw ledgers, figures and merged trees."""
from pathlib import Path
import hashlib, importlib.util, json, subprocess, sys
R=Path(__file__).resolve().parents[1];P=R/'reports/phase6'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
def main(label):
 s=importlib.util.spec_from_file_location('frozen_score',R/'scripts/phase6-score-final.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);permit=m.validate()
 physical_root=Path(permit['primary_root']);max_n=max_c=0.;count=0
 for entry in permit['final_physical_books']:
  f=physical_root/entry['path'];assert sha(f)==entry['sha256']
  rows=[json.loads(x) for x in f.read_text().splitlines()];assert len(rows)==343
  for x in rows:
   stock=x['stock_diagnostics'];n=abs(stock['soil_N_mass_balance_residual_kg_ha']);c=abs(stock['soil_C_mass_balance_residual_kg_ha']);assert n<1e-10 and c<1e-9
   max_n=max(max_n,n);max_c=max(max_c,c);count+=1
 receipt=json.loads((P/'final-policy-evaluation-receipt-v6.json').read_text());score_rows=0
 for x in receipt['files']:
  f=R/x['path'];assert sha(f)==x['sha256'];assert sum(1 for _ in f.open())==x['rows'];score_rows+=x['rows']
 audits=[]
 for f in sorted(P.glob('fig*-style-audit-v6.json')):
  d=json.loads(f.read_text());assert not d['outside_canvas_text'] and not d['text_overlap_candidates'] and d['minimum_font_pt']>=7
  for n,h in d['source_sha256'].items():assert sha(R/n)==h,(f,n)
  for x in d['files']:assert sha(R/x['path'])==x['sha256']
  audits.append({'path':str(f.relative_to(R)),'sha256':sha(f)})
 assert len(audits)==9
 manifest=P/'phase6-final-transfer-manifest-v6.json'
 if manifest.exists():
  for x in json.loads(manifest.read_text())['files']:assert sha(R/x['path'])==x['sha256'],x['path']
 cache=json.loads((P/'ignored-cache-transfer-v6.json').read_text())
 for x in cache['files']:assert sha(physical_root/x['path'])==x['sha256']
 assert git(R/'pcse','rev-parse','HEAD')==permit['external_PCSE_commit'];assert not git(R/'pcse','status','--porcelain')
 result=dict(status='passed',label=label,root=str(R),root_branch=git(R,'branch','--show-current'),root_head=git(R,'rev-parse','HEAD'),nested_branch=git(R/'NUE_PCSE-Gym','branch','--show-current'),nested_head=git(R/'NUE_PCSE-Gym','rev-parse','HEAD'),PCSE_head=git(R/'pcse','rev-parse','HEAD'),permit_sha256=sha(P/'final-evaluation-permit-v6.json'),permit_files=len(permit['files']),old_assets=1220,physical_books=len(permit['final_physical_books']),physical_rows=count,new_score_files=len(receipt['files']),new_score_rows=score_rows,max_N_residual=max_n,max_C_residual=max_c,figure_audits=audits,transfer_manifest_sha256=sha(manifest) if manifest.exists() else None,ignored_caches_verified=len(cache['files']),policy_scoring_executed=False)
 if label.startswith('postmerge'):assert result['root_branch']=='master' and result['nested_branch']=='main'
 (P/f'{label}-asset-acceptance-v6.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main(sys.argv[1])
