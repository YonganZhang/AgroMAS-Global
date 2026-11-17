"""5fold year-grouped paired supervision; no Dev or heldout reads or model selection."""
import pathlib,sys,json,time,hashlib,concurrent.futures
import numpy as np
import torch
from sklearn.model_selection import GroupKFold
from sklearn.ensemble import ExtraTreesRegressor
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
from pcse_gym.agent.counterfactual import CounterfactualGRU,counterfactual_loss,select_trust_candidate
from pcse_gym.envs.moisture4 import utility_features,utility_scores
from pcse_gym.envs.corridor import terminal_compliance
GRID=R/'reports/phase3c-training-utility-grid.json';CAL=R/'reports/phase3c-frozen-utility-v1.json'
def dataset():
    rows=json.loads(GRID.read_text())['records'];assert len(rows)==360 and all(3002<=r['year']<=4999 for r in rows)
    h=np.array([r['observation'] for r in rows],np.float32);es=[sorted(r['episodes'],key=lambda e:e['actual_N']) for r in rows];u=np.array([[e['yield_t_ha']-.002*e['actual_N']+terminal_compliance(e['NUE'],e['surplus'],8)-max(0,(e['surplus']-40)/20) for e in z] for z in es],np.float32);risk=np.array([[max(0,(e['surplus']-40)/20) for e in z] for z in es],np.float32)
    return rows,h,u,risk

def fit(h,base,u,risk,seed,reg,steps=400):
    torch.manual_seed(seed);p=CounterfactualGRU();p.train();x,b,y,r=[torch.tensor(z,dtype=torch.float32) for z in [h,base,u,risk]];first=None
    for step in range(steps):
        loss=counterfactual_loss(p,x,b,y,r,reg)
        if first is None:first=float(loss.detach())
        p.optimizer.zero_grad();loss.backward();torch.nn.utils.clip_grad_norm_(p.parameters(),1.);p.optimizer.step()
    assert all(torch.isfinite(v).all() for v in p.parameters());p.eval()
    return p,dict(first_loss=first,last_loss=float(loss.detach()),updates=steps)

def train(seed):
    torch.set_num_threads(1);start=time.monotonic();out=R/f'reports/phase4-cf-runs/cf-gru-seed{seed}';out.mkdir(parents=True,exist_ok=False)
    rows,h,u,risk=dataset();years=np.array([r['year'] for r in rows]);features=utility_features(h[:,-1,:11]);c=json.loads(CAL.read_text());reg_grid=[.01,.1,1.];alpha_grid=[.05,.1,.25,.5,1.];baseline=[];scores={f'{reg}/{alpha}':[] for reg in reg_grid for alpha in alpha_grid};candidates={f'{reg}/{alpha}':dict(regularization=reg,alpha=alpha) for reg in reg_grid for alpha in alpha_grid};trace=[]
    for fold,(fit_ids,val_ids) in enumerate(GroupKFold(5).split(h,u,years)):
        mu=features[fit_ids].mean(0);sd=features[fit_ids].std(0);sd[sd<1e-8]=1
        forest=ExtraTreesRegressor(n_estimators=64,max_depth=5,min_samples_leaf=4,n_jobs=1,random_state=4).fit(np.clip((features[fit_ids]-mu)/sd,-5,5),u[fit_ids]);bt=forest.predict(np.clip((features[fit_ids]-mu)/sd,-5,5)).astype(np.float32);bv=forest.predict(np.clip((features[val_ids]-mu)/sd,-5,5)).astype(np.float32);base_a=bv.argmax(1);baseline.append(float(u[val_ids,base_a].mean()))
        for reg in reg_grid:
            p,training=fit(h[fit_ids],bt,u[fit_ids],risk[fit_ids],seed,reg)
            with torch.no_grad():g=p.residual_and_aux(torch.tensor(h[val_ids]))[0][:,3:9].numpy()
            for alpha in alpha_grid:
                action=(bv+alpha*g).argmax(1);scores[f'{reg}/{alpha}'].append(float(u[val_ids,action].mean()))
            trace.append(dict(fold=fold,regularization=reg,fit_years=sorted(set(years[fit_ids].tolist())),validation_years=sorted(set(years[val_ids].tolist())),training=training))
    selected=select_trust_candidate(baseline,scores,candidates);reg=selected['regularization'] if selected['regularization'] is not None else 1.
    # Withalpha0fallback, retain a trained residual for transparent capacity accounting; it is inactive at inference.
    base=utility_scores(h[:,-1,:11],c);p,training=fit(h,base,u,risk,seed,reg);p.save(out/'policy.pt')
    source={str(q.relative_to(R)):hashlib.sha256(q.read_bytes()).hexdigest() for q in [pathlib.Path(__file__).resolve(),R/'NUE_PCSE-Gym/pcse_gym/agent/counterfactual.py',R/'NUE_PCSE-Gym/pcse_gym/agent/ppo_mod.py',R/'NUE_PCSE-Gym/pcse_gym/envs/moisture4.py',R/'NUE_PCSE-Gym/pcse_gym/envs/observable.py',GRID,CAL]}
    receipt=dict(status='completed',seed=seed,selection=selected,baseline_fold_utility=baseline,candidate_fold_utility=scores,CV_trace=trace,final_training=training,train_years=sorted(set(years.tolist())),parameter_count=sum(x.numel() for x in p.parameters()),source_sha256=source,checkpoint_sha256=hashlib.sha256((out/'policy.pt').read_bytes()).hexdigest(),calibration_sha256=hashlib.sha256(CAL.read_bytes()).hexdigest(),seconds=time.monotonic()-start,physical_history_shape=[4,11],legal_mask_history_shape=[4,9],network_input_shape=[4,20],additional_PPO_interactions=0)
    assert receipt['parameter_count']==4908;(out/'receipt.json').write_text(json.dumps(receipt,indent=2));return dict(seed=seed,alpha=selected['alpha'],seconds=receipt['seconds'])
if __name__=='__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
        for result in pool.map(train,[4,17,29]):print(json.dumps(result),flush=True)
