"""Exercise actual PPO.train reductions, including empty-active critic updates."""
import numpy as np
import torch
import gymnasium as gym
import pytest

@pytest.mark.parametrize('active',[False,True])
def test_actual_train_active_head_and_all_transition_critics(active,tmp_path):
 from pcse_gym.agent.ppo_mod import LagrangianPPO
 from pcse_gym.envs.moisture import MoisturePolicy,VisibleFrameExtractor
 from pcse_gym.envs.constraints import upper_surplus_constraint
 from stable_baselines3.common.logger import configure
 class E(gym.Env):
  observation_space=gym.spaces.Box(-np.inf,np.inf,(1,20),dtype=np.float32)
  action_space=gym.spaces.Discrete(9)
  def reset(self,*,seed=None,options=None):return np.zeros((1,20),np.float32),{}
  def step(self,a):raise AssertionError('Direct train test must not simulate')
 m=LagrangianPPO(MoisturePolicy,E(),n_steps=8,batch_size=8,n_epochs=1,learning_rate=.001,gamma=1,gae_lambda=1,active_step_grad=True,active_mask_offset=11,constraint_fn=upper_surplus_constraint,constraint_mode='corrected',endpoint_cost_mode='upper_surplus',policy_kwargs=dict(prior_strength=0,features_extractor_class=VisibleFrameExtractor,net_arch=dict(pi=[32,32],vf=[32,32])),seed=4)
 m.set_logger(configure(str(tmp_path),['csv']));m._current_progress_remaining=1.
 b=m.rollout_buffer;b.observations[:,0,0,0]=.7;b.observations[:,0,0,10]=.2;b.observations[:,0,0,11]=1
 if active:b.observations[:2,0,0,12]=1;b.actions[1,0,0]=1
 obs=torch.tensor(b.observations[:,0]);actions=torch.tensor(b.actions[:,0,0],dtype=torch.long)
 with torch.no_grad():b.log_probs[:,0]=m.policy.evaluate_actions(obs,actions)[2].numpy()
 b.advantages[:,0]=10000
 if active:b.advantages[:2,0]=[1,-1]
 b.cost_advantages[:]=0;b.returns[:]=1;b.cost_returns[:]=1;b.full=True;b.pos=8
 head=m.policy.action_net.weight.detach().clone();vf=m.policy.value_net.bias.detach().clone();cost=m.policy.cost_value_net.bias.detach().clone()
 m.train()
 changed=not torch.equal(head,m.policy.action_net.weight)
 assert changed==active
 assert not torch.equal(vf,m.policy.value_net.bias)
 assert not torch.equal(cost,m.policy.cost_value_net.bias)
 assert m.logger.name_to_value['train/active_count']==(2 if active else 0)
 assert np.isfinite(m.logger.name_to_value['train/loss'])
