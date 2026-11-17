"""Causal field-observable history. Hidden soil and future weather are never selected."""
from collections import deque
import numpy as np
import gymnasium as gym
import torch
from torch import nn
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor

OBSERVABLE_CROP = ['DVS', 'LAI']
# IRRAD/TMIN/RAIN are the preceding 7 daily observations, not forecasts.
FRAME_FIELDS = ['DVS', 'LAI', 'IRRAD_7d_mean', 'TMIN_7d_mean', 'RAIN_7d_mean',
                'cumulative_N_kg_ha', 'days_since_last_application', 'last_executed_action',
                'applications_used', 'remaining_budget_kg_ha']

class ObservableHistory(gym.Wrapper):
    def __init__(self, env, history=1):
        super().__init__(env)
        self.history = history
        self.frames = deque(maxlen=history)
        self.observation_space = gym.spaces.Box(-np.inf, np.inf, shape=(history, len(FRAME_FIELDS)), dtype=np.float32)
        self.cumulative = 0.
        self.since = 365.
        self.last = 0.

    def frame(self, obs):
        obs = np.asarray(obs)
        if obs.shape != (23,): raise ValueError("Observable contract requires DVS/LAI +7x3 past weather")
        # Underlying env is initialized with exactly two crop features, no action features.
        weather = obs[2:].reshape(7, 3).mean(axis=0)
        # Fixed physical scales, never fitted on validation/audit/test data.
        return np.asarray([obs[0], obs[1]/10, weather[0]/1e7, weather[1]/30, weather[2]/10,
                           self.cumulative/400, min(self.since,365)/365, self.last/8,
                           self.env.counter/4, max(0,self.env.n_budget-self.cumulative)/400 if self.env.n_budget>0 else -1], dtype=np.float32)

    def reset(self, **kwargs):
        obs, info = self.env.reset(**kwargs)
        self.cumulative = self.last = 0.
        self.since = 365.
        self.frames.clear()
        for _ in range(self.history-1): self.frames.append(np.zeros(len(FRAME_FIELDS),np.float32))
        self.frames.append(self.frame(obs))
        return np.stack(self.frames), info

    def step(self, action):
        obs, reward, term, trunc, info = self.env.step(action)
        executed = info['executed_action']
        self.cumulative += executed*10
        self.since = 7 if executed > 0 else self.since+7
        self.last = executed
        self.frames.append(self.frame(obs))
        # Independent per-env reset clears the deque on VecEnv auto-reset.
        info['observable_frame'] = self.frames[-1].tolist()
        return np.stack(self.frames), reward, term, trunc, info

class CausalGRUExtractor(BaseFeaturesExtractor):
    """Recomputes causal truncated history per sample; shuffle-safe BPTT, no hidden carry leakage."""
    def __init__(self, observation_space, features_dim=8):
        super().__init__(observation_space, features_dim)
        self.gru = nn.GRU(observation_space.shape[-1], features_dim, batch_first=True)
    def forward(self, observations):
        _, hidden = self.gru(observations.float())
        return hidden[-1]
