"""Validate6original+2011authorized recovery results; no native execution."""
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
 recovery=json.loads((P/'recovery2/receipt.json').read_text());assert not any(recovery['exit_codes']) and recovery['results']==557
 first_recovery=json.loads((P/'recovery1/receipt.json').read_text());assert first_recovery['results']==1454 and first_recovery['original_completed_untouched']
 plan=json.loads((P/'phase8b-proposed-recovery-manifest.json').read_text());cases=json.loads((P/'phase8b-locked-campaign-cases.json').read_text())['cases'];expected={v['episode_id'] for v in cases};selected={}
 for row in plan['completed']:
  path=R/'data/phase8-locked-evaluation'/row['episode_id'];assert sha(path/'result.json')==row['result_sha256'];selected[row['episode_id']]=path
 for folder in ('phase8-locked-recovery1','phase8-locked-recovery2'):
  for path in (R/'data'/folder).glob('*/result.json'):
   identity=path.parent.name;assert identity not in selected;assert json.loads(path.read_text())['case']['episode_id']==identity;selected[identity]=path.parent
 assert set(selected)==expected and len(selected)==2017
 target=R/'data/phase8-combined-evaluation';target.mkdir();files={}
 for identity,path in selected.items():
  (target/identity).symlink_to(path,target_is_directory=True);files[identity]=dict(path=str(path.relative_to(R)),sha256=sha(path/'result.json'))
 receipt=dict(expected=2017,result_count=2017,exit_codes=recovery['exit_codes'],exit_code_scope='actual recovery worker exits; original attempt failed and remains recorded separately',original_attempt_exit_codes=json.loads((P/'phase8b-native-campaign-receipt.json').read_text())['exit_codes'],original_completed=6,recovered=2011,recovery1_completed=1454,recovery2_completed=557,recovery1_attempt_exit_codes=first_recovery['exit_codes'],WUR_preintegration_constructor_failures=4,restarted_incomplete=2,incomplete_original_prefixes_without_serialized_daily_audit=2,original_completed_byte_identical=True,approval='continue-e13ac62c370175d5.md epoch28 OptionA',files=files)
 (P/'phase8b-combined-campaign-receipt.json').write_text(json.dumps(receipt,indent=2));print('Validated2017unique completed episodes; original6unchanged',flush=True)
