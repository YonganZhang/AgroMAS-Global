"""Offline fixed-model verification with the controller's full product measure."""
from datetime import date
import numpy as np
from .tree_weather import TreeClimateForecastAgent
from .online_features import history_from_provider
from pcse_gym.agromas.season import regional_weather
from .scoring import conformal_radius,ranking_regret
CAPS=(25.,35.,40.,50.)
def summarize_product(tensor,prob):
 a=np.asarray(tensor);prob=np.asarray(prob,float);prob=prob/prob.sum();flat=a.reshape(len(a),-1,6);w=np.repeat(prob,a.shape[2])/a.shape[2];s=flat[:,:,2];order=np.argsort(s,axis=1,kind='stable');sorted_s=np.take_along_axis(s,order,axis=1);cdf=np.cumsum(np.broadcast_to(w,s.shape)[np.arange(len(a))[:,None],order],axis=1)
 def q(level):return sorted_s[np.arange(len(a)),np.minimum((cdf<level).sum(1),s.shape[1]-1)]
 joint=(s>=0)&(flat[:,:,3]>=.5)&(flat[:,:,3]<=.9)
 return dict(mean=np.sum(flat*w[None,:,None],axis=1),low=q(.05),upper=q(.95),upper_probability=np.stack([np.sum(w*(s<=cap),axis=1) for cap in CAPS],axis=1),joint_probability=np.stack([np.sum(w*(joint&(s<=cap)),axis=1) for cap in CAPS],axis=1))
def predict_summary(root,x,meta,model):
 groups={};out={}
 for i,m in enumerate(meta):groups.setdefault((m['region'],m['as_of'],m['climate']),[]).append(i)
 agent=TreeClimateForecastAgent(root)
 for (region,day,climate),ids in groups.items():
  history=history_from_provider(regional_weather(str(root),region,'v2'),region,date.fromisoformat(day));desc,w,*_=agent.tree(region,day,climate,observed_history=history);ids=np.asarray(ids)
  summary=summarize_product(model.response_tensor(x[ids],desc),w)
  for k,v in summary.items():
   if k not in out:out[k]=np.empty((len(x),)+v.shape[1:],dtype=float)
   out[k][ids]=v
 return out

def evaluate_summary(summary,y,meta,reference,train_y,train_meta):
 groups={}
 for i,m in enumerate(meta):groups.setdefault((m['region'],m['year'],m['stage']),[]).append(i)
 weight=np.zeros(len(meta))
 for ids in groups.values():weight[ids]=1/len(ids)
 weight/=weight.sum();truth=y[:,2]+3.5-y[:,1];low=summary['low'];up=summary['upper'];scores=np.maximum(low-truth,truth-up);radius=conformal_radius(scores);years=np.array([m['year'] for m in meta]);cross=np.zeros(len(meta),bool)
 for year in sorted(set(years)):
  test=years==year;r=conformal_radius(scores[~test]);cross[test]=(truth[test]>=low[test]-r)&(truth[test]<=up[test]+r)
 train_s=train_y[:,2]+3.5-train_y[:,1];caps={}
 for j,cap in enumerate(CAPS):
  event=truth<=cap;prior={}
  for region in sorted({m['region'] for m in train_meta}):
   for stage in (1,2,3):
    ids=np.array([m['region']==region and m['stage']==stage and m['climate']=='Historical' for m in train_meta]);prior[(region,stage)]=float(np.mean(train_s[ids]<=cap))
  p=np.array([prior[(m['region'],m['stage'])] for m in meta]);bs=float(np.sum(weight*(summary['upper_probability'][:,j]-event)**2));bt=float(np.sum(weight*(reference['upper_probability'][:,j]-event)**2));bc=float(np.sum(weight*(p-event)**2));caps[str(int(cap))]=dict(brier=bs,tree_brier=bt,climatology_brier=bc,BSS_vs_ExtraTrees=1-bs/bt if bt>0 else None,BSS_vs_region_stage_climatology=1-bs/bc if bc>0 else None,primary_event='S_N <= cap')
 real=200*y[:,0]-1.5*y[:,2];regret,n=ranking_regret(meta,200*summary['mean'][:,0]-1.5*summary['mean'][:,4],real,macro=True);et_regret,_=ranking_regret(meta,200*reference['mean'][:,0]-1.5*reference['mean'][:,4],real,macro=True)
 by_region={}
 for region in sorted({m['region'] for m in meta}):
  ids=np.array([m['region']==region for m in meta]);by_region[region]=dict(crossyear_coverage=float(np.sum(weight[ids]*cross[ids])/weight[ids].sum()),samples=int(ids.sum()))
 gates=dict(BSS_positive_both_references_all_caps=all(v[k] is not None and v[k]>0 for v in caps.values() for k in ['BSS_vs_ExtraTrees','BSS_vs_region_stage_climatology']),coverage_85_to_95=.85<=float(np.sum(weight*cross))<=.95,ranking_regret_strictly_lower_than_ExtraTrees=regret<et_regret)
 return dict(samples=len(y),unique_prefix_groups=n,caps=caps,conformal_radius_kg_ha=radius,Dev_crossyear_macro_90pct_coverage=float(np.sum(weight*cross)),Dev_calibration_set_90pct_coverage=float(np.sum(weight*((truth>=low-radius)&(truth<=up+radius)))),partial_profit_ranking_regret_EUR_ha=regret,ExtraTrees_regret_EUR_ha=et_regret,by_region=by_region,gates=gates,passed=all(gates.values()),distribution='full TRAIN analog branch x32 region-stage residual product',coverage_scope='fixed reused Dev cross-year calibration diagnostic,not prospective assurance')
