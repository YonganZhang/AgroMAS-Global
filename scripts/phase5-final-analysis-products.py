"""Generate statistics and all quantitative candidates from immutable final rows."""
from pathlib import Path
import subprocess,sys,os,json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5'
if __name__=='__main__':
 receipt=json.loads((P/'final-policy-evaluation-receipt-v4.json').read_text());assert receipt['status']=='completed'
 for script in ('phase5-final-statistics.py','phase5-green-confirmation.py'):
  print('Running '+script,flush=True);subprocess.run([sys.executable,str(R/'scripts'/script)],cwd=R,check=True)
 names=['fig2_netherlands_home_turf_and_ablation','fig3_cross_system_cmip6_urban_policy_matrix','fig4_global_5region_comparison_and_attribution'];entries=[]
 for number,name in zip((2,3,4),names):
  for variant in ('a','b','c'):
   print(f'Figure{number}candidate{variant}',flush=True);env=dict(os.environ,PHASE5_FIGURE_VARIANT=variant)
   subprocess.run([sys.executable,str(R/f'scripts/phase5-plot-fig{number}.py')],cwd=R,env=env,check=True)
   path=R/'reports/figures'/f'{name}.png' if variant=='a' else R/'reports/figures/phase5-candidates-v4'/name/variant/f'{name}.png'
   entries.append(dict(figure=number,candidate=variant,path=str(path.relative_to(R)),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),author_selected=False,visual_qa='pending_actualinspection'))
 p=P/'quantitative-figure-candidate-manifest-v4.json'
 with p.open('x') as f:json.dump(dict(status='rendered_pending_visualQA',candidates=entries,manuscript_inserted=False),f,indent=2)
 print(json.dumps(dict(rendered=len(entries),author_selection='pending',manuscript_inserted=False)),flush=True)
