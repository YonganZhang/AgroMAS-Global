"""Successful-episode receipts are write-once and individually SHA sealed."""
import pathlib,os,json,hashlib
from pcse_gym.utils.frozen_audit import exclusive_json,sha

def write_episode(path,payload):
 path=pathlib.Path(path);digest=exclusive_json(path,payload);seal=path.with_suffix('.sha256');fd=os.open(seal,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o444)
 with os.fdopen(fd,'w') as f:f.write(digest+'\n');f.flush();os.fsync(f.fileno())
 return digest

def read_episode(path):
 path=pathlib.Path(path);seal=path.with_suffix('.sha256')
 if not seal.exists() or seal.read_text().strip()!=sha(path):raise ValueError('Episode receipt seal missing/mismatch; fail closed')
 return json.loads(path.read_text())
