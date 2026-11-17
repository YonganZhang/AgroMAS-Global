"""Actual fitted fold-tool interface check, no native runs or outcome scoring."""
from pathlib import Path
import json,joblib,numpy as np,torch
from pcse_gym.agromas_v8.joint_model import FrozenJointWorldModel
from pcse_gym.agromas_v8.controller import FiveSpecialistTeam
from pcse_gym.agromas_v8.online_features import history_from_provider
from pcse_gym.agromas.season import regional_weather
from datetime import date
R=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 torch.set_num_threads(2);m=json.loads((R/'cache/phase8-train-arrays/meta.json').read_text())[0];x=np.load(R/'cache/phase8-train-arrays/x.npy')[0];state=dict(zip(['dvs','lai','sm','n_fert_cum','n_uptake','stage'],x[:6]));state.update(region_id=m['region'],as_of=m['as_of'],days_since_last_fert=60.,climate='Historical');history=history_from_provider(regional_weather(str(R),m['region'],'v2'),m['region'],date.fromisoformat(m['as_of']));records=[]
 for variant,family in [('Full64','MLP'),('Static3','MLP'),('Weather','Weather'),('Linear64','Linear'),('ExtraTrees64','ExtraTrees')]:
  model=FrozenJointWorldModel(R,'Sensorless',family,device='cuda');model._adapter=joblib.load(R/f'models/phase8-controls/p2-adapters/LOYO-2018/{variant}.joblib');model.adapter_tag=variant;team=FiveSpecialistTeam(R,model);context=dict(prior_id='australia_wa_perth:2017',as_of=state['as_of']);decision=team.choose(state,history,adapter_context=context)
  assert decision['dose'] in (0,10,20,40,60,80,100);records.append(dict(variant=variant,private_tool_loaded=True,TRAIN_fixture_only=True,prior_future_rejected=variant.endswith('64'),dose=decision['dose'],radius=decision['radius']));print(records[-1],flush=True)
 (R/'reports/phase8/phase8b-P2-tool-interface-smoke.json').write_text(json.dumps(dict(records=records,native_runs=0,outer_label_scoring=False),indent=2))
