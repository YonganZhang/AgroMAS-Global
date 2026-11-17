"""Exactly two pre-registered, equal-parameter PyTorch response architectures."""
import torch
from torch import nn

class WorldModel(nn.Module):
 def __init__(self,input_dim=36,architecture='mlp'):
  super().__init__()
  if architecture not in ('mlp','residual-mlp'):raise ValueError('Architecture cap')
  self.architecture=architecture;self.first=nn.Linear(input_dim,96);self.second=nn.Linear(96,96);self.head=nn.Linear(96,3);self.dropout=nn.Dropout(.05)
 def latent(self,x):
  h=torch.nn.functional.silu(self.first(x));r=self.dropout(torch.nn.functional.silu(self.second(h)))
  return (h+r)/2**.5 if self.architecture=='residual-mlp' else r
 def forward(self,x):return self.head(self.latent(x))
