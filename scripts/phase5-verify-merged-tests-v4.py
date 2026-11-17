"""Run actual merged-tree pytest while restoring only derived provider caches."""
from pathlib import Path
import subprocess,json,hashlib,pickle,os,sys
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def parameter_sha(data):
 model,version,repository,compatible,store=pickle.loads(data)
 return hashlib.sha256(pickle.dumps((model,version,compatible,store),pickle.HIGHEST_PROTOCOL)).hexdigest(),repository

def restore(path,data,mode):
 temporary=path.with_name(path.name+'.posttest-restore-v4');assert not temporary.exists()
 with temporary.open('xb') as f:f.write(data)
 temporary.chmod(mode);os.replace(temporary,path)

if __name__=='__main__':
 assert '.worktrees' not in R.parts,'Mergedprimarycheckoutrequired'
 assert subprocess.check_output(['git','-C',str(R),'branch','--show-current'],text=True).strip()=='master'
 assert subprocess.check_output(['git','-C',str(R/'NUE_PCSE-Gym'),'branch','--show-current'],text=True).strip()=='main'
 assert not subprocess.check_output(['git','-C',str(R/'NUE_PCSE-Gym'),'status','--porcelain'],text=True).strip(),'NUEprimarymustbecleanbeforetests'
 assert json.loads((P/'final-policy-evaluation-receipt-v4.json').read_text())['status']=='completed'
 ancestry=[]
 for repository,target in ((R,'master'),(R/'NUE_PCSE-Gym','main')):
  feature_tip=subprocess.check_output(['git','-C',str(repository),'rev-parse','feat/phase5-agromas-global'],text=True).strip()
  subprocess.run(['git','-C',str(repository),'merge-base','--is-ancestor',feature_tip,'HEAD'],check=True)
  ancestry.append(dict(repository=str(repository),target=target,feature_tip=feature_tip,merged_head=subprocess.check_output(['git','-C',str(repository),'rev-parse','HEAD'],text=True).strip(),is_ancestor=True))
 # Force both this verifier and its actual pytest child to use merged sources.
 test_env=os.environ.copy()
 test_env.update(PYTHONPATH=os.pathsep.join(map(str,(R/'NUE_PCSE-Gym',R/'pcse',R/'scripts'))),PHASE5_MERGED_ROOT=str(R),
  PCSE_PROJECT_HOME=str(R/'cache/pcse-home'),XDG_CACHE_HOME=str(R/'cache'),MPLCONFIGDIR=str(R/'cache/matplotlib'),TMPDIR=str(R/'cache/tmp'))
 test_env['PYTEST_PLUGINS']=','.join(filter(None,(test_env.get('PYTEST_PLUGINS',''),'phase5_pytest_import_guard_v4')))
 sys.path[:0]=[str(R/'NUE_PCSE-Gym'),str(R/'pcse')]
 import pcse_gym.agromas.final_evaluation as evaluator,pcse,stable_baselines3,sb3_contrib
 assert Path(evaluator.__file__).resolve().is_relative_to((R/'NUE_PCSE-Gym').resolve()),'Wrongverifiermodule'
 assert Path(pcse.__file__).resolve().is_relative_to((R/'pcse').resolve()),'WrongverifierPCSE'
 for package in (stable_baselines3,sb3_contrib):assert Path(package.__file__).resolve().is_relative_to((R/'.venv').resolve()),'WrongSB3source'
 from pcse_gym.agromas.final_evaluation import validate_external_dependency
 permit=P/'final-evaluation-permit-v4.json';validate_external_dependency(R,permit)
 preservation_manifest=P/'final-relocation-source-manifest-v4-r3.json';preservation_manifest_sha=sha(preservation_manifest)
 expected_assets={row['path']:row['sha256'] for row in json.loads(preservation_manifest.read_text())['files']}
 def verify_preserved_assets():
  assert sha(preservation_manifest)==preservation_manifest_sha,'Preservationmanifestchanged'
  actual={relative:sha(R/relative) for relative in expected_assets}
  assert actual==expected_assets,'Phase5assetpreservationfailure'
  return actual
 before_assets=verify_preserved_assets()
 cache=R/'cache/phase5-regional-config/crop/YAMLCropDataProvider.pkl';snapshot=P/'final-native-crop-cache-v4.pkl'
 assert sha(cache)==sha(snapshot);original=cache.read_bytes();original_mode=cache.stat().st_mode&0o777
 source_cache=R/'NUE_PCSE-Gym/pcse_gym/envs/configs/crop/YAMLCropDataProvider.pkl';source_original=source_cache.read_bytes();source_mode=source_cache.stat().st_mode&0o777
 before_parameters,old_repository=parameter_sha(original);exit_code=None;after_parameters=None;new_repository=None
 try:
  # This is a derived cache only; immutable original snapshot stays untouched.
  cache.chmod(0o644)
  with (P/'postmerge-full-pytest-v4.txt').open('x') as log:
   exit_code=subprocess.run([str(R/'.venv/bin/pytest'),'-q'],cwd=R/'NUE_PCSE-Gym',stdout=log,stderr=subprocess.STDOUT,check=False,env=test_env).returncode
  after_parameters,new_repository=parameter_sha(cache.read_bytes())
  assert before_parameters==after_parameters,'Nativecropparameterschangedundertests'
  for phase in ('start','finish'):
   provenance=json.loads((P/f'postmerge-pytest-import-{phase}-v4.json').read_text());assert provenance['status']=='passed'
  assert provenance['pytest_exitstatus']==exit_code
 finally:
  restore(cache,original,original_mode);restore(source_cache,source_original,source_mode)
  assert sha(cache)==sha(snapshot);validate_external_dependency(R,permit)
 after_assets=verify_preserved_assets()
 # Evaluation is closed; keep ordinary derived-cache regeneration functional in the primary checkout.
 cache.chmod(0o644)
 assert sha(cache)==sha(snapshot),'Permissionsmustnotchangefrozenbytes'
 assert not subprocess.check_output(['git','-C',str(R/'NUE_PCSE-Gym'),'status','--porcelain'],text=True).strip(),'UnexpectedNUEtestmodifications'
 with (P/'postmerge-plan-check-v4.txt').open('x') as log:plan_exit=subprocess.run(['plan','check'],cwd=R,stdout=log,stderr=subprocess.STDOUT,check=False).returncode
 proof=dict(status='passed' if exit_code==plan_exit==0 else 'failed',pytest_exit=exit_code,plan_check_exit=plan_exit,
  exact_pytest_command=[str(R/'.venv/bin/pytest'),'-q'],cwd=str(R/'NUE_PCSE-Gym'),native_cache_parameter_sha_before=before_parameters,native_cache_parameter_sha_after=after_parameters,
  repository_before=old_repository,repository_after=new_repository,repository_path_not_parameter=True,sealed_original_restored=True,sealed_original_sha256=sha(snapshot),
  original235assets_verified_after=True,immutable_original_cache_snapshot_preserved=True,derived_cache_final_mode='0644;mutablegeneratedcacheonlyafterevaluationisclosed',raw_data_or_weights_changed=(before_assets!=after_assets),preservation_manifest=str(preservation_manifest.relative_to(R)),preservation_manifest_sha256=preservation_manifest_sha,preserved_asset_count=len(after_assets),all_preservation_hashes_verified_before_and_after=(before_assets==after_assets),helper_launch_scope="Actualpytestonly;noHoldoutcampaignlaunchedbyhelper;notaruntimeinferenceeventaudit",pytest_pythonpath=test_env['PYTHONPATH'],actual_pytest_module_provenance=['postmerge-pytest-import-start-v4.json','postmerge-pytest-import-finish-v4.json'],dual_merge_ancestry=ancestry)
 with (P/'postmerge-verification-v4.json').open('x') as f:json.dump(proof,f,indent=2)
 for name in ('postmerge-full-pytest-v4.txt','postmerge-plan-check-v4.txt','postmerge-verification-v4.json','postmerge-pytest-import-start-v4.json','postmerge-pytest-import-finish-v4.json'):(P/name).chmod(0o444)
 print(json.dumps(proof),flush=True)
 if proof['status']!='passed':raise SystemExit(1)
