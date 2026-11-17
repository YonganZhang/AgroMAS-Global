"""Seal all completed TRAIN-only models/source before once-only final unlock."""
from pathlib import Path
import json,hashlib,subprocess,platform,sys
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 # Failure must occur before creating a permit or touching final weather.
 campaign=json.loads((P/'PPO-training-campaign-v4.json').read_text())
 assert campaign['all_completed'] and len(campaign['jobs'])==6 and all(x['exit_code']==0 for x in campaign['jobs'])
 assert {(x['mode'],x['seed']) for x in campaign['jobs']}=={(m,s) for m in ('structured-shared','raw-shared') for s in (4,17,29)}
 audit=json.loads((P/'PPO-training-audit-v4.json').read_text());assert audit['status']=='completed' and len(audit['runs'])==6
 receipts=[]
 for mode in ('structured-shared','raw-shared'):
  for seed in (4,17,29):
   d=R/f'models/phase5/ppo-{mode}-seed{seed}-v4';x=json.loads((d/'receipt.json').read_text())
   assert x['status']=='completed' and x['actual_native_weekly_steps']==401408 and x['parameters_finite'] and x['parameters_L2_change']>0 and not x['dev_used'] and not x['heldout_used'];receipts.append(x)
   assert x['source_freeze_sha256']==sha(P/'PPO-source-and-input-freeze-v4.json') and x['budget_sha256']==sha(P/'ppo-training-budget-v4.json')
   assert all(sha(d/n)==h for n,h in x['files'].items())
 dev=json.loads((P/'regional-dev-check-v2-receipt.json').read_text());assert dev['seasons']==25 and dev['failed']==0 and dev['cumulative_dev_check_number']==2 and not dev['reselection'] and not dev['heldout_unlocked']
 assert all(sha(R/relative)==digest for relative,digest in dev['source_hashes'].items())
 dev_rows=list(map(json.loads,(P/'regional-dev-frozen-check-v2.jsonl').read_text().splitlines()));assert len(dev_rows)==25 and all(r['status']=='completed' and r['role']=='Dev' for r in dev_rows)
 green=json.loads((P/'green-subsidy-TRAIN-freeze-v3.json').read_text());assert green['status']=='TRAIN_frozen' and not green['dev_used'] and not green['heldout_used']
 tests=json.loads((P/'final-PPO-Train-replay-equivalence-v4.json').read_text());assert tests['status']=='passed' and len(tests['cases'])==30 and all(x['outcome_max_abs_error']<1e-8 for x in tests['cases'])
 physics=json.loads((P/'final-evaluator-Train-physical-equivalence-v4.json').read_text());assert physics['status']=='passed'
 freeze=json.loads((P/'PPO-source-and-input-freeze-v4.json').read_text());files=set(freeze['files'])
 assert all(sha(R/x)==h for x,h in freeze['files'].items()),'FormalPPOinputdrift'
 files.update(str(x.relative_to(R)) for x in (R/'NUE_PCSE-Gym/pcse_gym').rglob('*.py'))
 files.update(str(x.relative_to(R)) for x in (R/'models/phase5').rglob('*') if x.is_file() and ('continuation-' in str(x) or 'climate-v2' in str(x)) and x.suffix=='.joblib')
 for mode in ('structured-shared','raw-shared'):
  for seed in (4,17,29):
   files.update(f'models/phase5/ppo-{mode}-seed{seed}-v4/{n}' for n in ('model.zip','vecnormalize.pkl','receipt.json','training-curves.jsonl','train-episodes.jsonl'))
 for name in ('global-date-split-manifest.json','regional-controls-v2.json','regional-phenology-train-freeze-v2.json','policy-train-freeze-v2.json',
              'A0-fixed-first-two-train-freeze-v2.json','green-subsidy-TRAIN-freeze-v3.json','final-evaluation-protocol-v4.json','PPO-training-campaign-v4.json'):
  files.add('reports/phase5/'+name)
 files.add('reports/phase3c-frozen-utility-v1.json')
 files.update('NUE_PCSE-Gym/pcse_gym/envs/'+n+'.py' for n in ('moisture4','corridor','moisture','phase3','observable'))
 for pattern in ('outcome-*-train-freeze-v2.json','green-subsidy-*.json','*Train*equivalence*v4.json'):
  files.update(str(p.relative_to(R)) for p in P.glob(pattern))
 files.update('reports/phase5/'+n for n in ('PPO-training-audit-v4.json','final-PPO-Train-replay-equivalence-v4.json','final-evaluator-Train-physical-equivalence-v4.json','final-native-carbon-Train-closure-v4.json','ablation-training-protocol-v2.json','NATIVE_BOUNDARY_CLAIM_LIMITS.md','regional-dev-check-v2-receipt.json','regional-dev-frozen-check-v2.jsonl','regional-validity-gate-v2.json'))
 for directory in ('data/global_regions','reports/phase5/regional-model-inputs','cache/phase5-regional-config'):
  for x in (R/directory).rglob('*'):
   if x.is_file() and x.suffix in ('.json','.yaml','.yml','.conf','.CAB','.crop','.pkl'):files.add(str(x.relative_to(R)))
 files.update('scripts/'+name for name in ('phase5-generate-final-books.py','phase5-score-final-books.py','phase5-final-statistics.py','phase5-seal-final-evaluation.py','phase5-green-confirmation.py','phase5-correct-green-subsidy-v3.py','phase5-check-final-PPO-replay.py','phase5-ppo-training-audit.py'))
 hashes={}
 for relative in sorted(files):
  path=R/relative;assert path.resolve().is_relative_to(R)
  hashes[relative]=sha(path);path.chmod(path.stat().st_mode&~0o222)
 pcse=(R/'pcse').resolve();commit=subprocess.check_output(['git','-C',str(pcse),'rev-parse','HEAD'],text=True).strip()
 assert commit=='d1fe6d29de828033b850ec51d994988d8d6d406f'
 assert not subprocess.check_output(['git','-C',str(pcse),'status','--porcelain'],text=True).strip()
 external={str(x.relative_to(pcse)):sha(x) for x in pcse.rglob('*') if x.is_file() and '.git' not in x.parts and x.suffix in ('.py','.conf','.yaml','.yml')}
 permit=dict(status='final_once_only_seal',all_models_frozen=True,dev_verified=True,dev_scope='Frozenphenology/referencephysicscheck#2only;noDevpolicyselection',
  subsidy_train_frozen=True,split_manifest_sha256=sha(P/'global-date-split-manifest.json'),files=hashes,
  external_dependency=dict(kind='readonlyPCSE',commit=commit,files=external),
  physical_NASA_input_readonly=True,selection_role='Trainonly',python=sys.version,platform=platform.platform(),
  runtime_versions={name:__import__('importlib.metadata',fromlist=['version']).version(name) for name in ('numpy','pandas','scipy','scikit-learn','joblib','torch','stable-baselines3','sb3-contrib','gymnasium')},
  final_independent_seasons=52,public_reused_seasons=7,claim_limits='reports/phase5/NATIVE_BOUNDARY_CLAIM_LIMITS.md')
 path=P/'final-evaluation-permit-v4.json'
 with path.open('x') as f:json.dump(permit,f,indent=2)
 path.chmod(0o444)
 with path.with_suffix('.sha256').open('x') as f:f.write(sha(path)+'\n')
 path.with_suffix('.sha256').chmod(0o444)
 print(json.dumps(dict(status='sealed',files=len(hashes),external_source_files=len(external),permit_sha256=sha(path))))

if __name__=='__main__':main()
