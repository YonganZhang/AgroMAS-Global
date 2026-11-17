"""Complete requested primary-context sequential and functional contrasts.

Secondary paired analysis, explicitly exploratory; no model/policy selection.
"""
from pathlib import Path
import importlib.util,json,hashlib
import numpy as np,pandas as pd
R=Path(__file__).resolve().parents[1];P=R/'reports/phase5'
if __name__=='__main__':
 from pcse_gym.agromas.final_evaluation import validate_external_dependency
 validate_external_dependency(R,P/'final-evaluation-permit-v4.json')
 spec=importlib.util.spec_from_file_location('frozen_stats_v4',R/'scripts/phase5-final-statistics.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 data=pd.read_csv(P/'final-annual-seed-averaged-metrics-v4.csv');data=data[(data.climate=='Historical')&(data.zone=='standard_40')&(data.price_multiplier==1)&(data.subsidy==0)]
 contrasts=[];ranking=[]
 for (role,region),g in data.groupby(['role','region_id']):
  arms={arm:x.sort_values('harvest_year') for arm,x in g.groupby('arm')}
  for kind,pairs in [('sequential',[('A1','A0'),('A2','A1'),('A2-oracle','A2'),('A3','A2'),('A4','A3')]),('functional',[('A4','LOAO-climate'),('A4','LOAO-eco'),('A4','LOAO-core-state'),('A4','A3')])]:
   for treated,control in pairs:
    a=arms[treated];b=arms[control];result=m.paired(a,b);n=len(a);ix=np.random.default_rng(20261115).integers(0,n,size=(5000,n));doses={}
    for stage in (1,2,3):
     diff=a[f'stage{stage}_dose'].to_numpy()-b[f'stage{stage}_dose'].to_numpy();doses[str(stage)]=dict(difference=float(diff.mean()),CI95=np.quantile(diff[ix].mean(1),[.025,.975]).tolist())
    contrasts.append(dict(role=role,region_id=region,kind=kind,treated=treated,control=control,metrics=result,stage_dose_contrasts=doses,inference='exploratoryunadjusted;notagentorganizationcausality'))
  functional=[x for x in contrasts if x['role']==role and x['region_id']==region and x['kind']=='functional']
  ordered=sorted(functional,key=lambda x:x['metrics']['joint']['difference'],reverse=True);best=ordered[0]['metrics']['joint']['difference'];ties=[x['control'] for x in ordered if np.isclose(x['metrics']['joint']['difference'],best,atol=1e-12,rtol=0)]
  ranking.append(dict(role=role,region_id=region,descriptive_order=[dict(function_removed=x['control'],joint_difference=x['metrics']['joint']['difference'],CI95=x['metrics']['joint']['CI95']) for x in ordered],
   unique_largest_positive_point_effect=ties[0] if best>0 and len(ties)==1 else None,interpretation='descriptiverankingonly;ties/nonpositiveeffectsnotcalleddominance;nomultiplicity-adjusteddominancetest'))
 out=P/'final-sequential-functional-attribution-v4.json'
 with out.open('x') as f:json.dump(dict(status='completed',scope='originaltaskprimarycontextsequential/LOAOcontrasts;secondaryexploratory',
  input_sha256=hashlib.sha256((P/'final-annual-seed-averaged-metrics-v4.csv').read_bytes()).hexdigest(),source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  bootstrap_replicates=5000,contrasts=contrasts,regional_descriptive_rankings=ranking,matched_monolithic='ExactlyFullbyfrozenobjective/tableidentity;noorganizationcausalgain'),f,indent=2)
 out.chmod(0o444);print(json.dumps(dict(contrasts=len(contrasts),regional_rankings=len(ranking))),flush=True)
