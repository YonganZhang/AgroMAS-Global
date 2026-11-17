"""Run canonical active target suite + v8 tests with real-process import proof.

Use the unchanged baseline CPU runtime for existing test compatibility, while
CUDA training is separately evidenced. Restore generated crop cache bytes.
"""
from pathlib import Path
import hashlib,json,os,sys,time
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8'
if __name__=='__main__':
 import pytest,pcse,pcse_gym.agromas_v8.models as v8,pcse_gym.agromas_v6.core as v6,torch
 assert Path(v8.__file__).resolve().is_relative_to((R/'NUE_PCSE-Gym').resolve())
 assert Path(v6.__file__).resolve().is_relative_to((R/'NUE_PCSE-Gym').resolve())
 assert Path(pcse.__file__).resolve().is_relative_to((R/'pcse').resolve())
 files=[R/'NUE_PCSE-Gym/pcse_gym/envs/configs/crop/YAMLCropDataProvider.pkl',R/'cache/phase5-regional-config/crop/YAMLCropDataProvider.pkl'];saved={p:(p.read_bytes(),p.stat().st_mode&0o777) for p in files if p.exists()}
 proof={'v8_source':str(Path(v8.__file__).resolve()),'v6_source':str(Path(v6.__file__).resolve()),'pcse_source':str(Path(pcse.__file__).resolve()),'python':sys.executable,'torch':torch.__version__,'scope':'canonical active tests/target plus all Phase8 tests; no exclusions or skips'}
 os.chdir(R/'NUE_PCSE-Gym');tick=time.monotonic()
 try:rc=pytest.main(['-q','tests/target','tests/test_phase8_invariants.py','tests/test_phase8_climate.py'])
 finally:
  for p,(b,mode) in saved.items():p.chmod(0o644);p.write_bytes(b);p.chmod(mode);assert p.read_bytes()==b
 proof.update(exit_code=int(rc),elapsed_seconds=time.monotonic()-tick,crop_caches_restored=True)
 (P/'phase8b-canonical-test-receipt.json').write_text(json.dumps(proof,indent=2));raise SystemExit(rc)
