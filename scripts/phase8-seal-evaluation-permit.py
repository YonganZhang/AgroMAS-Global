"""Freeze inference sources and actual assets before any native evaluation."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,platform
import torch,lightning
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if __name__=='__main__':
 path=P/'phase8b-final-evaluation-permit.json'
 if path.exists():raise ValueError('Existing exclusive permit; never silently replace')
 for name in ('phase8b-P2-adapter-training-freeze.json','phase8b-P2-adapter-inputs-freeze.json','phase8b-online-action-invariance.json','phase8b-policy-interface-smoke.json','phase8b-P2-tool-interface-smoke.json','phase8b-locked-campaign-cases.json','phase8b-green-stress-TRAIN-freeze.json','phase8b-PPO-training-complete.json'):
  assert (P/name).is_file(),name
 assert json.loads((P/'phase8b-G1-verdict.json').read_text())['status']=='G1_PASS'
 assert json.loads((P/'phase8b-online-action-invariance.json').read_text())['passed']==30
 p2=json.loads((P/'phase8b-P2-adapter-training-freeze.json').read_text());assert p2['fit_count']==70 and all(not r['outer_labels_used'] for r in p2['fits'])
 sources=list((R/'NUE_PCSE-Gym/pcse_gym/agromas_v8').glob('*.py'))+list((R/'scripts').glob('phase8-*.py'))
 models=[]
 for parent in (R/'models/phase8-v8',R/'models/phase8-controls'):
  for p in parent.rglob('*'):
   if not p.is_file() or p.suffix not in ('.pt','.joblib','.zip','.pkl'):continue
   if 'fold' in p.name or any('fold' in part for part in p.parts):
    if 'fold-1' not in str(p):continue
   models.append(p)
 frozen={}
 for p in sources+models:
  assert p.resolve().is_relative_to(R);p.chmod(p.stat().st_mode&~0o222);frozen[str(p.relative_to(R))]=sha(p)
 dependencies={}
 for parent in ('models/phase6/r2/Full','models/phase6/r2/PPO-structured-seed4','models/phase6/r2/PPO-structured-seed17','models/phase6/r2/PPO-structured-seed29','models/phase5/climate-v2'):
  for p in (R/parent).rglob('*'):
   if p.is_file() and p.suffix in ('.joblib','.pkl','.zip'):dependencies[str(p.relative_to(R))]=sha(p)
 for parent in ('cache/phase8-train-arrays','cache/phase8-weather-control-arrays','NUE_PCSE-Gym/pcse_gym/agromas','NUE_PCSE-Gym/pcse_gym/agromas_v6','reports/phase5/regional-model-inputs'):
  for p in (R/parent).rglob('*'):
   if p.is_file() and p.suffix in ('.npy','.json','.py'):dependencies[str(p.relative_to(R))]=sha(p)
 for p in [R/'data/52.57-5.63_random_weather.csv',R/'NUE_PCSE-Gym/pcse_gym/envs/configs/soil/arminda_soil.yaml',R/'reports/phase3c-frozen-utility-v1.json',R/'reports/phase5/global-date-split-manifest.json']+list((R/'data/global_regions').rglob('*')):
  if p.is_file():dependencies[str(p.relative_to(R))]=sha(p)
 depfile=P/'phase8b-external-inference-dependency-freeze.json';depfile.write_text(json.dumps(dependencies,indent=2));depfile.chmod(0o444);frozen[str(depfile.relative_to(R))]=sha(depfile)
 for name in ('phase8b-G1-verdict.json','phase8b-G2-control-calibration.json','phase8b-P2-adapter-training-freeze.json','phase8b-locked-campaign-cases.json','phase8b-g2-g3-implementation-contract.md','phase8b-green-stress-TRAIN-freeze.json'):
  p=P/name;p.chmod(0o444);frozen[str(p.relative_to(R))]=sha(p)
 pcse_sha=subprocess.check_output(['git','-C',str(R/'pcse'),'rev-parse','HEAD'],text=True).strip();assert pcse_sha=='d1fe6d29de828033b850ec51d994988d8d6d406f';assert not subprocess.check_output(['git','-C',str(R/'pcse'),'status','--porcelain'],text=True).strip()
 permit=dict(registered_UTC=datetime.now(timezone.utc).isoformat(),all_models_frozen=True,dev_verified=True,subsidy_train_frozen=True,split_manifest_sha256=sha(R/'reports/phase5/global-date-split-manifest.json'),files=frozen,external_PCSE_commit=pcse_sha,runtime=dict(python=platform.python_version(),torch=torch.__version__,lightning=lightning.__version__,CUDA=torch.version.cuda),P1='adaptive-reused historical temporal benchmark',P2='retrospective nested crossfit,not prospective blind test',Q8_4='unstarted',no_90_cell_surface=True,ledger_limits=dict(N=1e-10,C=1e-9))
 with path.open('x') as stream:json.dump(permit,stream,indent=2)
 path.with_suffix('.sha256').write_text(sha(path)+'\n');path.chmod(0o444);path.with_suffix('.sha256').chmod(0o444);print(json.dumps(dict(files=len(frozen),models=len(models),external_dependencies=len(dependencies))))
