"""Guard reviewed numeric claim locations; never auto-refresh the acceptance fixture."""
from pathlib import Path
import json,re,hashlib
R=Path(__file__).resolve().parents[1]
def claims(text):
 # Order and paragraph location matter: occurrence elsewhere cannot mask a swapped headline.
 paragraphs=re.split(r'\n\s*\n',text)
 return [{'paragraph':i,'context_sha256':hashlib.sha256(re.sub(r'\s+',' ',p).strip().encode()).hexdigest(),'numbers':re.findall(r'(?<![A-Za-z])[-−+]?\d+(?:\.\d+)?',p)} for i,p in enumerate(paragraphs) if re.search(r'\d',p)]
def validate(documents,fixture):
 for path,text in documents.items():assert claims(text)==fixture['documents'][path],('Numeric claim location changed',path)
if __name__=='__main__':
 fixture=json.loads((R/'reports/phase7/reviewed-numeric-claim-locations-v7.json').read_text());documents={path:(R/path).read_text() for path in fixture['documents']};validate(documents,fixture)
 # Astra counterexample: a false bilateral headline must fail even with the correct result elsewhere.
 tested=[]
 for path,text in documents.items():
  assert '21.88' in text;bad=dict(documents);bad[path]=text.replace('21.88','23.57',1)
  try:validate(bad,fixture)
  except AssertionError:tested.append(path)
  else:raise AssertionError(('False headline accepted',path))
 policy_tested=[]
 for path,text in documents.items():
  assert 'PPO' in text;bad=dict(documents);bad[path]=text.replace('PPO','SHAM_POLICY',1)
  try:validate(bad,fixture)
  except AssertionError:policy_tested.append(path)
  else:raise AssertionError(('False policy context accepted',path))
 (R/'reports/phase7/document-claim-guard-v7.json').write_text(json.dumps(dict(status='passed',corrupted_headline_rejected=tested,corrupted_policy_context_rejected=policy_tested,scope='Ordered numeric tokens and full policy/window paragraph context at reviewed locations, coupled to independent source recomputation; fixture is a reviewed acceptance baseline, not an independent semantic proof',documents_sha256={p:hashlib.sha256(t.encode()).hexdigest() for p,t in documents.items()}),indent=2));print('All three deliberately corrupted headline cases rejected')
