"""Three TRAIN2005native integration checks; never used for model selection."""
from pathlib import Path
import json,torch
from pcse_gym.agromas_v8.joint_model import FrozenJointWorldModel
from pcse_gym.agromas_v8.controller import FiveSpecialistTeam
from pcse_gym.agromas_v8.policies import TreePolicy
from pcse_gym.agromas_v8.referee import run_episode,prepare_daily_outputs
R=Path(__file__).resolve().parents[1];P=R/'reports/phase8';D=R/'data/phase8d-train-native-preflight'
if __name__=='__main__':
 assert not D.exists();D.mkdir();torch.set_num_threads(2);prepare_daily_outputs(R)
 team=FiveSpecialistTeam(R,FrozenJointWorldModel(R,'Sensorless','MLP',device='cuda'));records=[]
 for climate in ('Historical','idealized_mid','idealized_high'):
  case=dict(region='netherlands_lelystad',year=2005,role='Train',climate=climate,source='NASA',cap=40.,price_multiplier=1.,subsidy=0.,tax=0.,policy='TreeMLP',mode='soft',track='Sensorless',scope='TRAIN integration only;no policy/model selection')
  result=run_episode(R,case,TreePolicy(team,mode='soft'),None)
  assert result['mass_audit']['passed'] and len(result['mass_audit']['daily_records'])==result['mass_audit']['daily_rows']
  (D/(climate+'.json')).write_text(json.dumps(result,indent=2,default=str,allow_nan=False))
  records.append(dict(climate=climate,daily_rows=result['mass_audit']['daily_rows'],N=result['mass_audit']['max_abs_N_residual_kg_ha'],C=result['mass_audit']['max_abs_C_residual_kg_ha'],passed=True));print(json.dumps(records[-1]),flush=True)
 (P/'phase8d-native-preflight.json').write_text(json.dumps(dict(records=records,TRAIN_only=True,no_fitting_or_selection=True),indent=2))
