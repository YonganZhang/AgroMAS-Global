"""Explain fixed Dev dry/wet cases from already recorded application states; no replay simulation."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1]
if __name__=='__main__':
 p=R/'reports/phase3c-dev-full4-v4-sm.json';x=json.loads(p.read_text());control=json.loads((R/'reports/phase3c-dev-utilityprior-v4-sm.json').read_text())['records'];old=json.loads((R/'reports/phase3b-dev-controls-v3.json').read_text())['records'];cases=[]
 for year,soil,label in [(5194,'fast','dry_fast'),(5005,'default','wet_default')]:
  models={}
  for seed in [4,17,29]:
   rec=next(r for r in x['records'] if r['soil']==soil and r['seed']==seed and any(e['year']==year for e in r['episodes']));e=next(e for e in rec['episodes'] if e['year']==year);models[str(seed)]=dict(checkpoint=rec['checkpoint_sha256'],outcome=e,applications=[a for a in rec['events'] if a['year']==year and a['proposed']>0])
  refs={n:next(e for r in rs if r['model']==n and r['soil']==soil for e in r['episodes'] if e['year']==year) for n,rs in [('utilityprior',control),('prior190',old),('N2-PA',old)]}
  cases.append(dict(label=label,year=year,soil=soil,Full4=models,controls=refs))
 out=R/'reports/phase3c-dev-attribution.json';assert not out.exists();out.write_text(json.dumps(dict(dev_only=True,no_new_simulations=True,selection='Same Dev minimum/maximum Oct-July rainfall cases chosen independently of V4 outcomes:5194fast305.2mm,5005default801.7mm',causal_feature_importance_claim=False,input_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),cases=cases),indent=2))
 print([(c['label'],[(s,z['outcome']['actual_N']) for s,z in c['Full4'].items()]) for c in cases])
