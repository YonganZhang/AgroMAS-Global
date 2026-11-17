"""Read-only posthoc evidence: no environment construction, resets, training or tuning."""
import pathlib,sys,json,time,statistics,itertools,math,hashlib
import numpy as np
import torch
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
from pcse_gym.envs.moisture4 import UtilityScorer
from pcse_gym.agent.counterfactual import CounterfactualGRU
from pcse_gym.agent.ppo_mod import LagrangianPPO
from pcse_gym.utils.attribution import explain_decision
load=lambda name:SourceFileLoader(name,str(R/f'scripts/{name}.py')).load_module()
protocol=load('phase4-protocol');evaluator=load('phase4-frozen-eval');controller=load('phase4-controller')
def main():
 protocol.validate_domain_manifest(R,True);torch.set_num_threads(1)
 raw=json.loads((R/'reports/phase4-heldout-final.json').read_text());assert raw['status']=='completed'
 allrows=[r for rec in raw['records'] for r in rec['episodes']];assert len(allrows)==38736
 stats=json.loads((R/'reports/phase4-heldout-metrics-summary.json').read_text());dev=json.loads((R/'reports/phase4-dev-metrics-summary.json').read_text())
 rain={int(k):v for k,v in stats['rain_by_harvest_year'].items()};years=[y for y in rain if y>=5500]
 cases=[('dry_fast',min(years,key=lambda y:(rain[y],y)),'fast'),('wet_default',max(years,key=lambda y:(rain[y],-y)),'default')]
 dataset=json.loads((R/'reports/phase4-paired-dataset.json').read_text())['records'];background=np.median(np.asarray([d['physical_history'] for d in dataset]),axis=0)
 cal=json.loads(evaluator.CAL.read_text());scorer=UtilityScorer(cal);models={};overhead={};attribution=[]
 features=[('LAI',1),('SM',10),('RAIN',4),('IRRAD',2),('TMIN',3)]
 for name in ['utilityprior','cf-gru']:
  for seed in ([4] if name=='utilityprior' else [4,17,29]):
   ck=evaluator.model_asset(name,seed);res=CounterfactualGRU.load(ck,device='cpu') if name=='cf-gru' else None
   if res:res.eval()
   alpha=json.loads((ck.parent/'receipt.json').read_text())['selection']['alpha'] if res else 0
   models[(name,seed)]=controller.FrozenCUOController(scorer,res,alpha)
 for label,year,soil in cases:
  for name in ['utilityprior','cf-gru','full4']:
   rec=next(r for r in raw['records'] if r['model']==name and r['seed']==4 and r['soil']==soil and any(e['year']==year for e in r['episodes']))
   events=[e for e in rec['events'] if e['year']==year];row=next(e for e in rec['episodes'] if e['year']==year)
   explanations=[]
   for event in events:
    h=np.asarray(event['history'],np.float32)
    ex=explain_decision(h.tolist(),dict(policy=name,role='model-input sensitivity only; no hidden nitrogen inferred'),event['proposed'],event['executed'],event['reasons'])
    ex.update(application_date=event['application_date'],DVS=event['DVS'],LAI=event['LAI'],SM=event['SM'],past_rain_scaled=event['past_rain'])
    if name!='full4' and .62<=event['DVS']<=.88:
     ctrl=models[(name,4)];chosen=int(ctrl.scores(h).argmax());values={}
     for bits in itertools.product([0,1],repeat=5):
      z=h.copy()
      for keep,(_,col) in zip(bits,features):
       if not keep:z[:,col]=background[-len(z):,col]
      values[bits]=float(ctrl.scores(z)[chosen])
     phi={}
     for i,(feature,_) in enumerate(features):
      total=0
      for bits in itertools.product([0,1],repeat=5):
       if bits[i]:continue
       k=sum(bits);other=list(bits);other[i]=1
       total+=math.factorial(k)*math.factorial(4-k)/math.factorial(5)*(values[tuple(other)]-values[bits])
      phi[feature]=total
     assert abs(sum(phi.values())-(values[(1,)*5]-values[(0,)*5]))<1e-4
     ex.update(shapley=phi,score_for_total_N=160+10*chosen,background_score=values[(0,)*5],observed_score=values[(1,)*5])
    explanations.append(ex)
   attribution.append(dict(case=label,year=year,soil=soil,weather_rain_mm=rain[year],policy=name,episode=row,decisions=explanations))
 # Identical frozen physical histories, all9 legal to avoid synthetic invalid masks.
 histories=np.asarray([np.concatenate([np.asarray(d['physical_history']),np.asarray(d['legal_mask_history'])],axis=1) for d in dataset],np.float32)
 bench=histories[:64].copy();bench[:,:,11:]=1
 for name in ['raw','corrected','masked','guided','full4','utilityprior','cf-gru']:
  perseed={}
  for seed in ([4] if name=='utilityprior' else [4,17,29]):
   ck=evaluator.model_asset(name,seed)
   if name in ['utilityprior','cf-gru']:fn=models[(name,seed)].act
   else:
    model=LagrangianPPO.load(ck,device='cpu');shape=model.observation_space.shape
    def fn(h,m=model,shape=shape):return m.predict(h[-shape[0]:,:shape[1]],deterministic=True)[0]
   for h in bench[:8]:fn(h)
   samples=[]
   for i in range(512):
    h=bench[i%len(bench)];start=time.perf_counter_ns();fn(h);samples.append((time.perf_counter_ns()-start)/1e6)
   receipt=json.loads((ck.parent/'receipt.json').read_text()) if name!='utilityprior' else {}
   perseed[str(seed)]=dict(median_ms=statistics.median(samples),p95_ms=float(np.quantile(samples,.95)),mean_ms=statistics.mean(samples),n_calls=len(samples),checkpoint_bytes=ck.stat().st_size,training_wall_seconds_receipt=receipt.get('seconds'),alpha=receipt.get('selection',{}).get('alpha'))
  overhead[name]=perseed
 cea={}
 for name in ['N2-PA','utilityprior','cf-gru','full4','prior190']:
  rows=[r for rec in raw['records'] if rec['model']==name for r in rec['episodes'] if r['soil']=='default' and 1983<=r['year']<=2021]
  cea[name]={k:{'mean':statistics.mean(float(r[k]) for r in rows),'median':statistics.median(float(r[k]) for r in rows)} for k in ['yield_t_ha','NUE_actual','surplus_actual','native_NUE','native_surplus_kg_ha','actual_N']}
  cea[name]['n_episodes']=len(rows);cea[name]['n_unique_years']=len({r['year'] for r in rows});cea[name]['policy_seeds']=sorted({r['seed'] for r in rows})
 dose={}
 for name in ['full4','utilityprior','cf-gru']:
  for soil in ['default','fast','slow']:
   rows=[r for rec in raw['records'] if rec['model']==name and rec['soil']==soil for r in rec['episodes'] if r['year']>=5500]
   unique,counts=np.unique([r['actual_N'] for r in rows],return_counts=True);dose[f'{name}/{soil}']=dict(N=unique.tolist(),counts=counts.tolist(),unique_totals=len(unique))
 manifest=R/'reports/heldout-unlock-manifest.json'
 output=dict(status='completed',manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),episodes=len(allrows),Dev=dev,heldout=stats,CEA2025_default_39=cea,attribution=attribution,overhead=overhead,dose_distribution=dose,benchmark_protocol='CPU one torch thread; same64 TRAIN histories;8warmups+512single-state calls per checkpoint; masksalllegal; excludesPCSE, model loading, network and language-model latency',attribution_protocol='Exact five-group Shapley of frozen chosen-dose utility score; TRAIN-median physical history background; fixed other observed fields and masks; case years selected only by rainfall extrema. Model sensitivity, not causal agronomic effects.',budgets=dict(selected_PPO_interactions=1008000,reused_Full4_interactions=201600,superseded_corrected_extra_interactions=201600,total_development_PPO_interactions=1209600,smoke_interactions=1920,paired_calibration_outcomes=2160,CF_gradient_updates=19200,CV_teacher_fits=15,extra_verification_Dev_seasons=48,extra_verification_TRAIN_seasons=1))
 output['evaluation_elapsed_seconds']=raw['seconds']
 output['evaluation_runtime']={}
 for name in sorted({r['model'] for r in raw['records']}):
  records=[r for r in raw['records'] if r['model']==name];steps=sum(r['inference_steps'] for r in records);seconds=sum(r['inference_seconds'] for r in records)
  output['evaluation_runtime'][name]=dict(inference_steps=steps,inference_seconds=seconds,mean_ms_per_decision=1000*seconds/steps if steps else None,scope='Actual parallel evaluation timing; includes contention, excludes simulator steps')
 path=R/'reports/final_cea_metrics.json';assert not path.exists();path.write_text(json.dumps(output,indent=2));print('Final evidence created; no simulations or fitting performed')
if __name__=='__main__':main()
