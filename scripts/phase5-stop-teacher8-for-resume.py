"""Explicit epoch15 scheduling-only stop; preserve all completed/partial evidence."""
import signal,time,json,hashlib
from pathlib import Path
import psutil
root=Path(__file__).resolve().parents[1];owned=[]
for p in psutil.process_iter(['pid','ppid','cmdline','cwd']):
    try:
        a=p.info['cmdline'] or []
        if len(a)>1 and Path(a[1]).name=='phase5-generate-teachers.py' and p.info['cwd']==str(root):owned.append(p)
    except (psutil.NoSuchProcess,psutil.AccessDenied):pass
if len(owned)!=9:raise RuntimeError(f'Expected own1parent+8workers;found{len(owned)}; no signals sent')
identity=[dict(pid=p.pid,ppid=p.ppid(),created=p.create_time(),cmdline=p.cmdline()) for p in owned]
for p in owned:p.send_signal(signal.SIGSTOP)
for _ in range(50):
    if all(p.status()==psutil.STATUS_STOPPED for p in owned):break
    time.sleep(.1)
else:raise RuntimeError('Could not freeze own process cohort')
for p in owned:p.send_signal(signal.SIGTERM);p.send_signal(signal.SIGCONT)
gone,alive=psutil.wait_procs(owned,timeout=5)
for p in alive:
    if p.status()!=psutil.STATUS_ZOMBIE:raise RuntimeError(f'Own process{p.pid} did not exit')
base=root/'data/phase5-teachers-v2';interrupted=base/'interrupted-8worker-pass';interrupted.mkdir(exist_ok=False)
complete=[];partial=[];failed=0
for path in sorted(base.glob('*.jsonl')):
    data=path.read_bytes();rows=[];bad=0
    for line in data.splitlines():
        try:rows.append(json.loads(line))
        except json.JSONDecodeError:bad+=1
    failed+=sum(r['status']!='completed' for r in rows)
    if not path.stat().st_mode&0o222 and len(rows)==343 and not bad and all(r['status']=='completed' for r in rows):
        complete.append(dict(path=str(path.relative_to(root)),rows=343,sha256=hashlib.sha256(data).hexdigest()))
    else:
        path.chmod(0o444);target=interrupted/path.name;path.rename(target)
        partial.append(dict(path=str(target.relative_to(root)),complete_json_rows=len(rows),bad_lines=bad,sha256=hashlib.sha256(data).hexdigest()))
report=dict(reason='Explicit epoch15 authorizes scheduling-only32worker resume; no scientific protocol or functional physics/feature changes',old_processes=identity,preserved_complete_files=complete,interrupted_files=partial,
    interrupted_complete_row_count=sum(x['complete_json_rows'] for x in partial),completed_unique_seasons=343*len(complete),simulation_failures=failed)
p=root/'reports/phase5/teacher-resume32-transition-v2.json';p.write_text(json.dumps(report,indent=2));p.chmod(0o444)
print(json.dumps(dict(stopped_own_processes=len(owned),preserved_complete_files=len(complete),archived_partial_files=len(partial),archived_complete_rows=report['interrupted_complete_row_count'])))
