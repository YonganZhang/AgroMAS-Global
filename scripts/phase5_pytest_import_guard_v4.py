"""Record and enforce actual pytest module provenance in the merged checkout."""
from pathlib import Path
import os,json,sys

R=Path(os.environ['PHASE5_MERGED_ROOT']).resolve()

def _inspect():
    expected={'pcse_gym':(R/'NUE_PCSE-Gym/pcse_gym').resolve(),'pcse':(R/'pcse/pcse').resolve(),'stable_baselines3':(R/'.venv').resolve(),'sb3_contrib':(R/'.venv').resolve()}
    # Import in the actual pytest process before test collection; no model execution.
    import pcse_gym.agromas.final_evaluation,pcse,stable_baselines3,sb3_contrib
    modules={}
    for name,module in list(sys.modules.items()):
        family=name.split('.')[0]
        if family not in expected or not getattr(module,'__file__',None):continue
        path=Path(module.__file__).resolve()
        if not path.is_relative_to(expected[family]):raise RuntimeError('Unexpectedpytestmodule:'+name+':'+str(path))
        modules[name]=str(path)
    return modules

def pytest_sessionstart(session):
    proof=dict(status='passed',phase='before_collection',root=str(R),modules=_inspect())
    with (R/'reports/phase5/postmerge-pytest-import-start-v4.json').open('x') as f:json.dump(proof,f,indent=2)

def pytest_sessionfinish(session,exitstatus):
    proof=dict(status='passed',phase='after_tests',root=str(R),pytest_exitstatus=int(exitstatus),modules=_inspect())
    with (R/'reports/phase5/postmerge-pytest-import-finish-v4.json').open('x') as f:json.dump(proof,f,indent=2)
