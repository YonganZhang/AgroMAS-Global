"""Read-only Phase1–7 preservation; all new receipts stay under reports/phase8."""
from pathlib import Path
import hashlib,json,sys,subprocess
PRIMARY=Path('/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体');R=Path.cwd();P=R/'reports/phase8'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
if __name__=='__main__':
 base=json.loads((PRIMARY/'reports/phase7/preservation-baseline-v7.json').read_text());assets=json.loads((PRIMARY/'reports/phase7/delivery-assets-manifest-v7.json').read_text())['assets'];history=json.loads((P/'protected-history-sha256.json').read_text())
 for x in base['files']:assert sha(PRIMARY/x['path'])==x['sha256'],x['path']
 for x in assets:assert sha(PRIMARY/x['path'])==x['sha256'],x['path']
 for path,digest in history.items():assert sha(PRIMARY/path)==digest,path
 # Every prior tracked evidence/source file remains its baseline blob, not merely the sampled manifests.
 paths=subprocess.check_output(['git','-C',str(PRIMARY),'ls-tree','-r','--name-only','17c393d'],text=True).splitlines();protected=[p for p in paths if p.startswith(('reports/phase','reports/figures/','models/','manuscript/','scripts/phase')) and not p.startswith('reports/phase8/')]
 changed=subprocess.check_output(['git','-C',str(PRIMARY),'diff','17c393d','--name-only','--',*protected],text=True).splitlines();assert not changed,changed
 label=sys.argv[1] if len(sys.argv)>1 else 'check';receipt=dict(status='passed',legacy_1782=len(base['files']),phase7_assets_242=len(assets),prior_tracked_evidence_and_sources=len(protected),Q1_Q7_and_v1_files_unchanged=len(history),read_only=True,primary_root=str(PRIMARY),no_manuscript_edits=True,phase8_training_authorized=True)
 (P/f'{label}-preservation.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
