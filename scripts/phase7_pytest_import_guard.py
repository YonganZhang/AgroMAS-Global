"""Prove source paths inside the actual pytest child at start and finish."""
from pathlib import Path
import os,json,hashlib,importlib
R=Path(os.environ['PHASE7_TEST_ROOT']).resolve();LABEL=os.environ['PHASE7_TEST_LABEL'];P=R/'reports/phase7'
def proof(phase,session=None,exitstatus=None):
 modules={}
 for name in ('pcse_gym.agromas_v7.validation','pcse_gym.agromas_v7.bridge','pcse_gym.agromas_v6.core','pcse_gym.agromas_v6.books','pcse_gym.agromas_v6.training','pcse_gym.agromas_v6.book_env','pcse_gym.agromas.final_evaluation','pcse','stable_baselines3','sb3_contrib'):
  module=importlib.import_module(name);path=Path(module.__file__).resolve();expected=(R/'NUE_PCSE-Gym').resolve() if name.startswith('pcse_gym') else (R/'pcse').resolve() if name=='pcse' else (R/'.venv').resolve();assert path.is_relative_to(expected),(name,str(path));modules[name]=dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
 skipped=None
 if session is not None:
  reporter=session.config.pluginmanager.getplugin('terminalreporter');skipped=len(reporter.stats.get('skipped',[])) if reporter else None
 result=dict(status='passed',phase=phase,root=str(R),modules=modules,pytest_exitstatus=None if exitstatus is None else int(exitstatus),skips=skipped)
 path=P/f'{LABEL}-pytest-import-{phase}-v7.json'
 with path.open('x') as f:json.dump(result,f,indent=2)
def pytest_sessionstart(session):proof('start')
def pytest_sessionfinish(session,exitstatus):proof('finish',session,exitstatus)
