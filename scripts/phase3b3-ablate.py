"""Run only after the frozen SM Full3 Dev gate passes; six bounded runners at once."""
import pathlib,json,subprocess,sys,concurrent.futures,time,hashlib
R=pathlib.Path(__file__).resolve().parents[1]
def train(task):
 model,seed=task;cmd=[sys.executable,str(R/'scripts/phase3b3-run.py'),'--model',model,'--seed',str(seed),'--tag','v3-sm','--steps','65536'];start=time.monotonic()
 with open(R/f'logs/phase3b3-v3-sm-{model}-seed{seed}.log','w') as log:code=subprocess.run(cmd,cwd=R,stdout=log,stderr=subprocess.STDOUT).returncode
 return dict(model=model,seed=seed,command=cmd,returncode=code,seconds=time.monotonic()-start)
if __name__=='__main__':
 gate=R/'reports/phase3b-full3-dev-gate-v3-sm.json';g=json.loads(gate.read_text());assert g['dev_gate_passed'] and g['actual_training_steps_per_seed']==67200
 out=R/'reports/phase3b3-v3-sm-ablation-processes.json';assert not out.exists();rows=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for r in pool.map(train,[(m,s) for m in ['raw','corrected','masked','guided'] for s in [4,17,29]]):
   rows.append(r);out.write_text(json.dumps(rows,indent=2));print(json.dumps(r),flush=True)
 assert all(r['returncode']==0 for r in rows)
 freeze={}
 for model in ['raw','corrected','masked','guided','full3']:
  for seed in [4,17,29]:
   folder=R/f'reports/phase3b3-runs/v3-sm-{model}-seed{seed}';receipt=json.loads((folder/'receipt.json').read_text());assert receipt['status']=='completed' and receipt['actual_steps']==67200 and receipt['finite_parameters'] and receipt['parameters_changed']
   digest=hashlib.sha256((folder/'model.zip').read_bytes()).hexdigest();assert digest==receipt['checkpoint_sha256'];freeze[folder.name]=digest
 p=R/'reports/phase3b3-frozen-checkpoints-v3-sm.json';assert not p.exists();p.write_text(json.dumps(dict(checkpoint_sha256=freeze,all_checkpoints_frozen=True,gate_sha256=hashlib.sha256(gate.read_bytes()).hexdigest()),indent=2))
