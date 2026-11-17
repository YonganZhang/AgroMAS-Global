"""Train-only paired utility residual. Physical history and legal masks stay separate in records."""
import numpy as np
import torch
import gymnasium as gym
from pcse_gym.agent.ppo_mod import CostActorCriticPolicy
from pcse_gym.envs.observable import CausalGRUExtractor

class CounterfactualGRU(CostActorCriticPolicy):
    def __init__(self,observation_space=None,action_space=None,lr_schedule=None,**kwargs):
        observation_space=observation_space or gym.spaces.Box(-np.inf,np.inf,(4,20),dtype=np.float32)
        action_space=action_space or gym.spaces.Discrete(9)
        defaults=dict(features_extractor_class=CausalGRUExtractor,features_extractor_kwargs=dict(features_dim=7),net_arch=dict(pi=[32,32],vf=[32,32]))
        defaults.update(kwargs);super().__init__(observation_space,action_space,lr_schedule or (lambda _: .001),**defaults)
    def residual_and_aux(self,history):
        actor,value,cost=self.mlp_extractor(self.extract_features(history))
        return self.action_net(actor),self.value_net(value).flatten(),self.cost_value_net(cost).flatten()

def paired_advantage(utility):return utility-utility.mean(-1,keepdim=True)

def counterfactual_loss(policy,history,base,utility,risk,regularization=.1):
    residual,value,cost=policy.residual_and_aux(history);delta=residual[:,3:9]
    advantage=paired_advantage(utility);teacher=paired_advantage(base)
    logits=base+delta;logq=torch.log_softmax(logits,-1);logp=torch.log_softmax(base,-1);q=logq.exp()
    trust=(q*(logq-logp)).sum(-1).mean()
    supervised=(delta-(advantage-teacher)).square().mean()
    paired_update=-(q*advantage.detach()).sum(-1).mean()
    aux=.05*((value-utility.mean(-1)).square().mean()+(cost-risk.mean(-1)).square().mean())
    return supervised+.1*paired_update+regularization*(trust+residual.square().mean())+aux

def select_trust_candidate(baseline,values,candidates):
    """Only TRAIN-CV arrays enter this gate; every fold non-degrading and mean strictly better."""
    baseline=np.asarray(baseline);accepted=[]
    for key,pred in values.items():
        pred=np.asarray(pred)
        if np.all(pred>=baseline-1e-12) and pred.mean()>baseline.mean()+1e-9:accepted.append(key)
    if not accepted:return dict(alpha=0.,regularization=None,reason='no_all_fold_non_degrading_utility_gain')
    best=max(accepted,key=lambda k:(np.asarray(values[k]).mean(),-float(candidates[k]['alpha']),float(candidates[k]['regularization'])))
    return dict(candidates[best],reason='all_fold_non_degrading_train_CV_gain',key=best)
