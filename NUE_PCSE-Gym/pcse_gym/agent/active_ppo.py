"""Opt-in active-decision reductions. Passive transitions still train both critics."""
import numpy as np
import torch

def active_decisions(obs,offset=None):
    if offset is None:return torch.ones(obs.shape[0],dtype=torch.bool,device=obs.device)
    mask=obs[:,-1,offset:]
    if mask.shape[-1]!=9 or not bool(torch.all((mask==0)|(mask==1))):raise ValueError('Nine binary action-mask bits required')
    return mask.sum(-1)>1

def active_stats(values,mask):
    x=np.asarray(values)[np.asarray(mask,dtype=bool)]
    if len(x)<2:return (0.,1.)
    scale=float(x.std())
    return (float(x.mean()),max(scale,1e-8))

def active_mean(values,mask):
    return values[mask].mean() if bool(mask.any()) else values.sum()*0.
