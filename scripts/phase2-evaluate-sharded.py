import pathlib,sys,json,time,concurrent.futures,os,math,statistics,hashlib
import numpy as np
import torch
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'));sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
from importlib.machinery import SourceFileLoader
runner=SourceFileLoader('phase2_runner',str(R/'scripts/phase2-run.py')).load_module()
baseline=SourceFileLoader('baseline_eval',str(R/'scripts/evaluate-baselines.py')).load_module()
from pcse_gym.agent.ppo_mod import LagrangianPPO
from pcse_gym.utils.attribution import explain_decision

KEYS=['yield_t_ha','NUE','N_surplus_kg_ha','fertilization_kg_ha','N_loss_kg_ha','profit_kEUR_ha']
def summary(rows):
    if not rows:return {'n':0}
    out=baseline.summarize(rows)
    out['mean']['actual_executed_fertilization_kg_ha']=statistics.mean(x['actual_executed_fertilization_kg_ha'] for x in rows)
    out['median']['actual_executed_fertilization_kg_ha']=statistics.median(x['actual_executed_fertilization_kg_ha'] for x in rows)
    for key in ['NUE_actual_execution','N_surplus_actual_execution_kg_ha']:
        out['mean'][key]=statistics.mean(x[key] for x in rows);out['median'][key]=statistics.median(x[key] for x in rows)
    out['joint_actual_execution_rate']=statistics.mean(x['joint_actual_execution'] for x in rows)
    for k in ['proposed_violation_rate','executed_violation_rate']+[f'{p}_{c}_violation_rate' for p in ['proposed','executed'] for c in ['action_domain','application_frequency','minimum_spacing','phenology_window']]:
        out[k]=statistics.mean(x[k] for x in rows)
    n=max(1,math.ceil(.25*len(rows)))
    # Downside directions fixed before test: lower yield/NUE/compliance, greater surplus/loss.
    out['cvar25']={k:statistics.mean(sorted([float(x[k]) for x in rows],reverse=k in ['N_surplus_kg_ha','N_loss_kg_ha'])[:n]) for k in ['yield_t_ha','NUE','joint_satisfied','N_surplus_kg_ha','N_loss_kg_ha']}
    out['yield_std_across_years']=statistics.pstdev(x['yield_t_ha'] for x in rows)
    return out

def evaluate(task):
    model_name,seed,soil,part,selected_years=task;torch.set_num_threads(1)
    import logging;logging.disable(logging.CRITICAL)
    folder=R/'reports/phase2-evaluation-parts-v3';folder.mkdir(exist_ok=True)
    out=folder/f'{model_name}-seed{seed}-{soil}-part{part}.json'
    if out.exists():raise RuntimeError('Refuse to trust or overwrite existing audit output: '+str(out))
    slices=json.loads((R/'reports/phase2-weather-slices.json').read_text())['years']
    env=runner.make_env(model_name,seed,0,years=[1983],soil=soil,training=False)
    env.unwrapped.sb3_env._phase2_fast_info=True
    model=None
    if model_name!='N2-PA':
        ckpt=R/'reports/phase2-runs'/f'matched-v2-{model_name}-seed{seed}-env16/model.zip'
        frozen=json.loads((R/'reports/phase2-frozen-checkpoints.json').read_text())
        assert hashlib.sha256(ckpt.read_bytes()).hexdigest()==frozen[ckpt.parent.name], 'Frozen checkpoint drift'
        model=LagrangianPPO.load(str(ckpt),device='cpu');assert model.num_timesteps==32768
    rows=[];trajectories=[];start=time.monotonic()
    sample_years=[int(y) for y,v in slices.items() if 1983<=int(y)<=2021 and v['drought']][:2]
    try:
        for year in selected_years:
            env.unwrapped.overwrite_year(year);obs,_=env.reset(seed=seed)
            done=False;merged={};counts={p:{c:0 for c in ['action_domain','application_frequency','minimum_spacing','phenology_window']} for p in ['proposed','executed']};steps=0;trajectory=[];actual_N=0.
            while not done:
                before=obs.copy();decision_date=env.unwrapped.date.isoformat()
                if model_name=='N2-PA':
                    # Native published PAGV rule dates/doses, applied in the containing weekly interval.
                    from datetime import date,timedelta
                    current=env.unwrapped.date
                    action=sum(dose//10 for month,day,dose in [(2,17,60),(5,11,80),(6,21,80)] if date(year,month,day)<current<=date(year,month,day)+timedelta(days=7))
                else:action=int(np.asarray(model.predict(obs,deterministic=True)[0]).item())
                obs,rew,term,trunc,info=env.step(action);done=term or trunc;steps+=1;actual_N+=info['executed_action']*10
                for p,key in [('proposed','shield_reason'),('executed','executed_violation_reasons')]:
                    for c in counts[p]:counts[p][c]+=int(c in info[key])
                for k,v in info.items():
                    if isinstance(v,dict): merged.setdefault(k,{}).update(v)
                if model_name=='full' and seed==4 and soil=='default' and year in sample_years:
                    with torch.no_grad():latent=model.policy.extract_features(torch.as_tensor(before[None],device=model.device)).cpu().numpy()[0].tolist()
                    record=explain_decision(before.tolist(),latent,action,info['executed_action'],info['shield_reason'])
                    record.update(date=decision_date,application_date=info['application_date'],outcome_date=env.unwrapped.date.isoformat(),proposal_DVS=info['proposal_dvs'],application_DVS=info['application_dvs'])
                    trajectory.append(record)
            row=baseline.extract(merged,year,model_name)
            row['actual_executed_fertilization_kg_ha']=actual_N
            row['native_logged_fertilization_kg_ha']=row['fertilization_kg_ha']
            native_input = row['grain_N_kg_ha']/row['NUE'] if row['NUE']>0 else None
            row['NUE_actual_execution'] = row['grain_N_kg_ha']/(native_input-row['fertilization_kg_ha']+actual_N) if native_input is not None else 0.
            row['N_surplus_actual_execution_kg_ha'] = row['N_surplus_kg_ha']-row['fertilization_kg_ha']+actual_N
            row['joint_actual_execution'] = .5<=row['NUE_actual_execution']<=.9 and 0<=row['N_surplus_actual_execution_kg_ha']<=40
            row.update(soil=soil,seed=seed,proposed_violation_rate=info['proposed_violation_rate'],executed_violation_rate=info['executed_violation_rate'],weather=slices[str(year)])
            for p in counts:
                for c,x in counts[p].items():row[f'{p}_{c}_violation_rate']=x/steps
            # These checks use pre-execution DVS; original extract's action dates are post-transition.
            row['phenology_satisfied']=counts['executed']['phenology_window']==0
            row['spacing_satisfied']=counts['executed']['minimum_spacing']==0
            row['action_frequency_satisfied']=counts['executed']['application_frequency']==0
            rows.append(row)
            if trajectory:trajectories.append({'year':year,'events':trajectory})
            if len(rows)%50==0:(folder/f'{model_name}-{seed}-{soil}-part{part}.progress.json').write_text(json.dumps({'episodes':len(rows),'seconds':time.monotonic()-start}))
        groups={split:[x for x in rows if (x['year']<3000)==(split=='historical')] for split in ['historical','stress']}
        summaries={}
        for split,xs in groups.items():
            summaries[split]={slice_name:summary([x for x in xs if slice_name=='all' or x['weather'][slice_name]]) for slice_name in ['all','drought','extreme']}
        result={'status':'completed','part':part,'checkpoint_sha256':None if model is None else frozen[ckpt.parent.name],'model':model_name,'seed':seed,'soil':soil,'training_soil':'default','zero_shot_soil':True,'wall_seconds':time.monotonic()-start,'summaries':summaries,'episodes':rows,'trajectories':trajectories}
        if model is not None:assert hashlib.sha256(ckpt.read_bytes()).hexdigest()==frozen[ckpt.parent.name]
        temp=out.with_suffix('.json.tmp');temp.write_text(json.dumps(result,indent=2));os.replace(temp,out);return {'file':str(out),'status':'completed','seconds':result['wall_seconds']}
    finally:env.close()

if __name__=='__main__':
    train=json.loads((R/'reports/phase2-training-processes-v2.json').read_text());assert train.get('status')=='completed'
    freeze={p.parent.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (R/'reports/phase2-runs').glob('matched-v2-*/model.zip')}
    assert len(freeze)==15
    freeze_path=R/'reports/phase2-frozen-checkpoints.json'
    assert freeze_path.exists() and json.loads(freeze_path.read_text())==freeze, 'Freeze must remain unchanged across evaluation shards'
    tasks=[(m,s,soil) for m in runner.MODELS for s in [4,17,29] for soil in ['default','fast','slow']]+[('N2-PA',4,soil) for soil in ['default','fast','slow']]
    canonical_tasks=tasks
    all_years=list(range(1983,2022))+list(range(5500,5999))
    tasks=[(*task,part,all_years[part*269:(part+1)*269]) for task in canonical_tasks for part in [0,1]]
    records=[]
    with concurrent.futures.ProcessPoolExecutor(max_workers=96) as ex:
        for row in ex.map(evaluate,tasks):
            records.append(row);print(json.dumps(row),flush=True)
            (R/'reports/phase2-evaluation-processes-v3.json').write_text(json.dumps(records,indent=2))

    canonical=R/'reports/phase2-evaluations-v3';canonical.mkdir(exist_ok=False)
    for model_name,seed,soil in canonical_tasks:
        parts=[json.loads((R/'reports/phase2-evaluation-parts-v3'/f'{model_name}-seed{seed}-{soil}-part{part}.json').read_text()) for part in [0,1]]
        rows=sorted([row for p in parts for row in p['episodes']],key=lambda x:x['year'])
        assert [x['year'] for x in rows]==all_years
        summaries={}
        for split in ['historical','stress']:
            subset=[x for x in rows if (x['year']<3000)==(split=='historical')]
            summaries[split]={sl:summary([x for x in subset if sl=='all' or x['weather'][sl]]) for sl in ['all','drought','extreme']}
        result={k:v for k,v in parts[0].items() if k not in ['part','episodes','summaries','trajectories','wall_seconds']}
        result.update(episodes=rows,summaries=summaries,trajectories=[t for p in parts for t in p['trajectories']],wall_seconds=max(p['wall_seconds'] for p in parts),combined_worker_seconds=sum(p['wall_seconds'] for p in parts),year_shards=2)
        out=canonical/f'{model_name}-seed{seed}-{soil}.json';temp=out.with_suffix('.json.tmp');temp.write_text(json.dumps(result,indent=2));os.replace(temp,out)
    print('All48 canonical evaluation datasets merged and validated',flush=True)
