"""Explicit versioned checkpoint paths do not alter the legacy default API."""
from pathlib import Path
from types import SimpleNamespace
import pickle
import pytest
from pcse_gym.agromas_v8.policies import SensorlessPPOPolicy

@pytest.mark.parametrize('explicit',[False,True])
def test_versioned_checkpoint_directory_is_explicit_and_default_unchanged(tmp_path,monkeypatch,explicit):
 import sb3_contrib
 calls=[]
 model=SimpleNamespace(policy=SimpleNamespace(set_training_mode=lambda enabled:calls.append(enabled)))
 monkeypatch.setattr(sb3_contrib.MaskablePPO,'load',lambda path,device:(calls.append(Path(path)),model)[1])
 folder=tmp_path/'reconstructed' if explicit else tmp_path/'models/phase8-controls/PPO-Sensorless-seed4'
 folder.mkdir(parents=True)
 (folder/'vecnormalize.pkl').write_bytes(pickle.dumps(SimpleNamespace(training=True,norm_reward=True)))
 policy=SensorlessPPOPolicy(tmp_path,object(),4,**({'model_dir':folder} if explicit else {}))
 assert calls==[folder/'model.zip',False]
 assert policy.normalizer.training is False and policy.normalizer.norm_reward is False
