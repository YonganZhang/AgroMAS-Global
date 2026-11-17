import pathlib,sys,json,time,statistics
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from importlib.machinery import SourceFileLoader
baseline=SourceFileLoader('baseline_eval',str(ROOT/'scripts/evaluate-baselines.py')).load_module()
from pcse_gym.initialize_envs import initialize_env
from pcse_gym.utils.defaults import get_default_crop_features
from pcse_gym.agent.ppo_mod import LagrangianPPO
from pcse_gym.utils.eval import evaluate_policy
from stable_baselines3.common.vec_env import DummyVecEnv,VecNormalize
ckpt=pathlib.Path(sys.argv[1]).resolve();stats=pathlib.Path(sys.argv[2]).resolve();out=pathlib.Path(sys.argv[3]).resolve()
env=initialize_env(pcse_env=2,crop_features=get_default_crop_features(2),years=[1983],locations=[(52.57,5.63)],random_weather=True,random_init=False,reward='NUE',start_type='sowing',seed=4)
vec=VecNormalize.load(str(stats),DummyVecEnv([lambda:env]));vec.training=False;vec.norm_reward=False
model=LagrangianPPO.load(str(ckpt),env=vec,device='cpu')
start=time.monotonic();rows=[]
for year in range(1983,2022):
 vec.env_method('overwrite_year',year);_,infos=evaluate_policy(model,vec,deterministic=True);rows.append(baseline.extract(infos[0],year,'LagPPO'))
 out.write_text(json.dumps({'status':'running','last_year':year,'episodes':rows},indent=2))
result={'checkpoint_path':str(ckpt),'normalizer_path':str(stats),'checkpoint_num_timesteps':model.num_timesteps,'protocol':{'years':list(range(1983,2022)),'location':[52.57,5.63],'random_init':False,'weather_provider':'official CSV historic rows','policy':'deterministic','seed':4,'normalize_training':False},'summary':baseline.summarize(rows),'episodes':rows,'wall_clock_seconds':time.monotonic()-start,'status':'completed'}
out.write_text(json.dumps(result,indent=2));vec.close();print(result['summary'])
