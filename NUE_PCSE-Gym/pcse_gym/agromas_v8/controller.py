"""Five typed specialists sharing a frozen numerical tool, no sixth coordinator."""
import hashlib,json
from collections import OrderedDict
import numpy as np
from .agents import SpatialTwinSurrogateAgent
from .planning import CoreAgronomicAgent,Regime,legal_schedules
from .online_features import public_state,candidate_features
from .tree_weather import TreeClimateForecastAgent

class _ResponseCapsule:
 """Private numerical result cache: no native engine or raw prior in messages."""
 def __init__(self,responses,applicable,score,version,radius):self._responses=responses;self._applicable=applicable;self._score=score;self._version=version;self._radius=radius
 def predict_joint_response(self,request):
  b=int(request['regime']['scenario_branch'])
  return {'members':self._responses[:,b],'applicable':self._applicable,'ood_score':self._score,'model_version':self._version,'calibration':{'alpha':.1,'radius':self._radius},'forecast_scope':'conditional_TRAIN_historical_analogs_not_NWP'}

class FiveSpecialistTeam:
 def __init__(self,root,model,*,train_analog_years=tuple(range(1995,2010))):
  self.root=root;self.model=model;self.climate=TreeClimateForecastAgent(root,train_analog_years);self.last_response_plan_count=0;self._response_cache=OrderedDict()
 def choose(self,state,history,*,cap=40.,price_multiplier=1.,subsidy=0.,tax=0.,remove=None,mode='tree',monolithic=False,adapter_context=None):
  track='Sensorless' if self.model.family=='Weather' else self.model.track;prefix=public_state(state,track);stage=int(prefix['stage']);plans=legal_schedules(stage,float(prefix['n_fert_cum']))
  history_hash=hashlib.sha256(np.asarray(history.values,dtype='float64').tobytes()+str(history.dates).encode()+str(history.source_id).encode()).hexdigest()
  cache_key=json.dumps({'history':history_hash,'prefix':prefix,'climate':state.get('climate','Historical'),'mean_only':remove=='climate','adapter':getattr(self.model,'adapter_tag',None),'adapter_context':adapter_context},sort_keys=True,default=str)
  if cache_key in self._response_cache:
   weights,rain,temp,provenance,score,applicable,tensor=self._response_cache[cache_key];self._response_cache.move_to_end(cache_key)
  else:
   desc,weights,rain,temp,provenance=self.climate.tree(prefix['region_id'],prefix['as_of'],state.get('climate','Historical'),observed_history=history,mean_only=remove=='climate')
   x=candidate_features(self.root,prefix,plans,state.get('climate','Historical'),history);score,applicable=self.model.applicability(x)
   tensor=self.model.response_tensor(x,desc,adapter_context=adapter_context)
   self._response_cache[cache_key]=(weights,rain,temp,provenance,score,applicable,tensor)
   while len(self._response_cache)>8:self._response_cache.popitem(last=False)
  self.last_response_plan_count=len(plans)
  current_x=candidate_features(self.root,prefix,plans,state.get('climate','Historical'),history);radius=self.model.calibration_radius(current_x,adapter_context);prior_status=self.model.prior_status(current_x,adapter_context)
  spatial=SpatialTwinSurrogateAgent(_ResponseCapsule(tensor,applicable,score,self.model.family,radius))
  opaque_id=prefix['region_id']+':'+str(prefix['as_of'])
  # Every actual inter-specialist response passes the vector/public-state guard.
  replies=[]
  for branch in range(len(weights)):
   request={'as_of':str(prefix['as_of']),'site_prior_id':opaque_id,'observable_prefix':prefix,'dose_schedules':plans.tolist(),'information_track':track,'regime':{'scenario_branch':branch}}
   replies.append(spatial.predict_joint_response(request)['members'])
  response=np.stack(replies,axis=1)
  regime=Regime(cap=cap,price_multiplier=price_multiplier,subsidy=subsidy,tax=tax,eco=remove!='eco',econ=remove!='econ',soft=mode=='soft',bare_tier2=mode=='hard-bare-tier2',radius=radius)
  core=CoreAgronomicAgent(regime,monolithic=monolithic);decision=core.choose(stage,plans,response,weights,rain,temp,applicable=applicable,mode='tree' if mode in ('soft','hard-bare-tier2','tier2-composite') else mode)
  decision['plans']=plans;decision['provenance']=provenance;decision['OOD_score']=score;decision['applicable']=applicable;decision['radius']=radius;decision.update(prior_status)
  decision['request_hash']=hashlib.sha256(json.dumps({'prefix':prefix,'plans':plans.tolist(),'family':self.model.family,'cap':cap,'price':price_multiplier,'subsidy':subsidy,'remove':remove,'mode':mode,'history':history_hash,'tax':tax,'monolithic':monolithic,'adapter':getattr(self.model,'adapter_tag',None),'adapter_context':adapter_context},sort_keys=True,default=str).encode()).hexdigest()
  return decision
