"""Unified physical environment; new frozen manifest exclusively controls heldout access."""
import pathlib,sys,json
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
ppo=SourceFileLoader('phase4_ppo_env',str(R/'scripts/phase4-ppo-run.py')).load_module()
from pcse_gym.initialize_envs import initialize_env
from pcse_gym.envs.observable import OBSERVABLE_CROP
from pcse_gym.envs.constraints import AgronomicShield
from pcse_gym.envs.phase3 import Phase3History
from pcse_gym.envs.moisture import MoistureHistory
from pcse_gym.envs.moisture4 import Moisture4History
from pcse_gym.utils.frozen_audit import validate_manifest
MODELS=['raw','corrected','masked','guided','full4','utilityprior','cf-gru']
def check_years(years,audit=False):
 if all(5000<=y<=5499 for y in years):return
 if not audit:raise ValueError('Heldout locked')
 from importlib.machinery import SourceFileLoader
 protocol=SourceFileLoader('phase4_heldout_protocol',str(R/'scripts/phase4-protocol.py')).load_module()
 protocol.validate_domain_manifest(R,False)
 if not all(y in set(range(1983,2022))|set(range(5500,5999)) for y in years):raise ValueError('Only frozen heldout splits allowed')
def make_env(name,seed,soil,year,audit=False):
 check_years([year],audit)
 if name in ['raw','corrected','masked','guided','full4']:return ppo.make_env(name,seed,0,years=[year],soil=soil,training=False,audit=audit)
 native=initialize_env(pcse_env=2,crop_features=list(OBSERVABLE_CROP),action_features=[],years=[year],locations=[(52.57,5.63)],random_weather=True,random_init=False,reward='NUE',seed=seed,soil='slo' if soil=='slow' else None if soil=='default' else soil,start_type='sowing')
 if name in ['prior160','prior170','prior190']:return Phase3History(AgronomicShield(native,enabled=True,n_budget=195),history=1,aligned=False,guided=name=='prior160')
 if name=='old_SM-adaptiveprior':return MoistureHistory(AgronomicShield(native,enabled=True,n_budget=210,max_applications=4),history=4,guided=True,calibration=json.loads((R/'reports/phase3b3-frozen-calibration-sm-v1.json').read_text()),stages=[70,130],joint_bonus=8)
 return Moisture4History(AgronomicShield(native,enabled=name!='N2-PA',n_budget=0 if name=='N2-PA' else 210,max_applications=3 if name!='N2-PA' else 4),history=4 if name=='cf-gru' else 1,guided=name!='N2-PA',calibration=None,stages=[70,130],aligned=False,budget=name!='N2-PA')
