"""Prepare TRAIN-only current-state sufficient-statistic cache; freeze PPO budget."""
from pathlib import Path
import json,hashlib,joblib
from pcse_gym.agromas_v6.books import load_train
from pcse_gym.agromas_v6.book_env import build_tables
R=Path(__file__).resolve().parents[1];P=R/'reports/phase6'
if __name__=='__main__':
 active=json.loads((P/'ACTIVE_TRAIN_RUN_V6.json').read_text());P=R/active['reports'];model_root=R/active['models']
 assert json.loads((P/'outcome-train-freeze-v6.json').read_text())['status']=='completed'
 data=load_train(R);models={s:joblib.load(model_root/f'Full/stage-{s}.joblib') for s in (1,2,3)};tables,legal=build_tables(data,models)
 folder=R/'cache/phase6'/active['run'];folder.mkdir(parents=True,exist_ok=True);cache=folder/'train-book-ppo-inputs-v6.joblib';assert not cache.exists();joblib.dump((data,tables,legal),cache,compress=3);cache.chmod(0o444)
 protocol=dict(status='registered_before_PPO_training',seeds=[4,17,29],decision_steps_per_seed=151552,algorithm='MaskablePPO64x64;8env;nsteps256;batch256;epochs10;gamma1;gae1;ent.01;lr.0003;targetKL.03;CPUoneTorchthread',source='TRAINphysicalinterventionbooks1995–2009;currentobservablesonly;futurelabelsoutsidepolicy',cache_sha256=hashlib.sha256(cache.read_bytes()).hexdigest(),baseline_scope='Newdecision-stepbookbaselinewithv6masksandfeatures;notnativeweeklyPPO;v4PPOremainsseparatelylabelledlegacytransfer',no_clipping_parity_claim_until_actual_diagnostic=True,fitting_or_selection_on_final_books=False,checkpoint='Finalfixedbudget;noeffectdrivenextension')
 with (P/'PPO_TRAIN_PROTOCOL_V6.json').open('x') as f:json.dump(protocol,f,indent=2)
 print(json.dumps(protocol))
