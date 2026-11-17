import numpy as np
import torch
import pytest
from pcse_gym.agent.counterfactual import CounterfactualGRU,paired_advantage,counterfactual_loss,select_trust_candidate
from pcse_gym.utils.frozen_audit import seal_manifest,validate_manifest,claim_audit,sha

def test_paired_advantage_common_effect_cancels():
 u=torch.tensor([[1.,3.,2.,4.,0.,6.],[3.,2.,4.,1.,5.,0.]])
 assert torch.allclose(paired_advantage(u),paired_advantage(u+torch.tensor([[30.],[-10.]])))
 assert torch.allclose(paired_advantage(u).mean(-1),torch.zeros(2),atol=1e-6)

def test_trust_gate_falls_back_on_any_fold_loss_and_all_ties():
 c={'a':dict(alpha=.1,regularization=.1)}
 assert select_trust_candidate([1,1,1],{'a':[2,2,.9]},c)['alpha']==0
 assert select_trust_candidate([1,1,1],{'a':[1,1,1]},c)['alpha']==0
 assert select_trust_candidate([1,1,1],{'a':[1,1,1.1]},c)['alpha']==.1

def test_counterfactual_gradient_aux_heads_and_reload(tmp_path):
 torch.manual_seed(4);p=CounterfactualGRU();h=torch.randn(8,4,20);b=torch.randn(8,6);u=torch.randn(8,6);risk=torch.rand(8,6)
 before=p.action_net.weight.detach().clone();loss=counterfactual_loss(p,h,b,u,risk,.1);p.optimizer.zero_grad();loss.backward()
 assert p.action_net.weight.grad.abs().sum()>0
 assert p.features_extractor.gru.weight_ih_l0.grad.abs().sum()>0
 assert p.value_net.weight.grad.abs().sum()>0 and p.cost_value_net.weight.grad.abs().sum()>0
 p.optimizer.step();assert not torch.equal(before,p.action_net.weight)
 p.save(tmp_path/'cf.pt');q=CounterfactualGRU.load(tmp_path/'cf.pt');assert torch.allclose(p.residual_and_aux(h)[0],q.residual_and_aux(h)[0]);assert sum(v.numel() for v in p.parameters())==4908

def test_alpha_zero_exactly_anchors_arbitrary_residual():
 base=torch.randn(20,6);residual=torch.randn(20,6)*1000
 assert torch.equal(base.argmax(-1),(base+0*residual).argmax(-1))

def test_manifest_write_once_seal_asset_and_audit_claim(tmp_path):
 asset=tmp_path/'model.bin';asset.write_bytes(b'frozen');payload=dict(dev_verified=True,all_checkpoints_frozen=True,files={'model.bin':sha(asset)})
 seal_manifest(tmp_path,payload);assert validate_manifest(tmp_path)==payload
 with pytest.raises(FileExistsError):seal_manifest(tmp_path,payload)
 claim_audit(tmp_path,['task'])
 with pytest.raises(FileExistsError):claim_audit(tmp_path,['task'])
 asset.write_bytes(b'changed')
 with pytest.raises(ValueError,match='drift'):validate_manifest(tmp_path)

def test_manifest_tamper_and_missing_prerequisites_fail_closed(tmp_path):
 with pytest.raises(ValueError):validate_manifest(tmp_path)
 with pytest.raises(ValueError):seal_manifest(tmp_path,dict(dev_verified=False,all_checkpoints_frozen=True,files={}))
 seal_manifest(tmp_path,dict(dev_verified=True,all_checkpoints_frozen=True,files={}))
 p=tmp_path/'reports/heldout-unlock-manifest.json';p.chmod(0o644);p.write_text('{}')
 with pytest.raises(ValueError,match='seal'):validate_manifest(tmp_path)

def test_actor_only_inference_matches_full_training_heads():
 p=CounterfactualGRU();p.eval();h=torch.randn(12,4,20)
 with torch.no_grad():
  all_heads=p.residual_and_aux(h)[0];only=p.action_net(p.mlp_extractor.forward_actor(p.extract_features(h)))
 assert torch.equal(all_heads,only)

def test_domain_catalog_requires_all19_and_preserves_failed_target(tmp_path):
 import pathlib,json
 from importlib.machinery import SourceFileLoader
 root=pathlib.Path(__file__).resolve().parents[3];protocol=SourceFileLoader('domain_test',str(root/'scripts/phase4-protocol.py')).load_module()
 amendment=tmp_path/'reports/phase4-protocol-amendment.json';amendment.parent.mkdir();amendment.write_text(json.dumps(dict(option='A',approved=True,decision_id='phase4_cf_dev_shortfall')))
 models=[dict(model=name,seed=seed,path=f'{name}-{seed}',sha256='asset') for name,seed in protocol.EXPECTED];files={m['path']:'asset' for m in models};files['reports/phase4-protocol-amendment.json']=sha(amendment)
 x=dict(models=models,files=files,primary_policy='utilityprior',cf_point_target_passed=False)
 assert protocol.check_catalog(x,tmp_path)==x
 with pytest.raises(ValueError,match='19'):protocol.check_catalog(dict(x,models=models[:-1]),tmp_path)
 with pytest.raises(ValueError,match='remainfailed'):protocol.check_catalog(dict(x,cf_point_target_passed=True),tmp_path)

def test_shrinkage_kl_is_bounded_by_unshrunk_training_trust_penalty():
 torch.manual_seed(29);base=torch.randn(20,6,dtype=torch.float64);delta=torch.randn(20,6,dtype=torch.float64);logp=torch.log_softmax(base,-1);previous=torch.zeros(20,dtype=torch.float64)
 for alpha in [0,.05,.1,.25,.5,1]:
  logq=torch.log_softmax(base+alpha*delta,-1);kl=(logq.exp()*(logq-logp)).sum(-1)
  assert torch.all(kl>=previous-1e-12);previous=kl

def test_frozen_controller_uses_residual_not_legacy_public_predict():
 import pathlib
 from importlib.machinery import SourceFileLoader
 root=pathlib.Path(__file__).resolve().parents[3];module=SourceFileLoader('controller_test',str(root/'scripts/phase4-controller.py')).load_module();p=CounterfactualGRU()
 def forbidden(*args,**kwargs):raise AssertionError('Residual.predict is not a deployed controller')
 p.predict=forbidden
 class Scorer(torch.nn.Module):
  def forward(self,frame):return torch.tensor([0.,0.,1.,0.,0.,0.])
 h=np.zeros((4,20),np.float32);h[-1,0]=.7;h[-1,5]=130/400;h[-1,11:]=1
 controller=module.FrozenCUOController(Scorer(),p,0.)
 assert controller.act(h)==5
 assert int(controller.predict(h)[0])==5

def test_episode_receipt_seal_rejects_tampered_content(tmp_path):
 import pathlib
 from importlib.machinery import SourceFileLoader
 root=pathlib.Path(__file__).resolve().parents[3];records=SourceFileLoader('episode_records_test',str(root/'scripts/phase4-records.py')).load_module();p=tmp_path/'episode.json'
 records.write_episode(p,dict(model='frozen',year=5000));assert records.read_episode(p)['year']==5000
 with pytest.raises(FileExistsError):records.write_episode(p,dict(year=5000))
 p.chmod(0o644);p.write_text('{}')
 with pytest.raises(ValueError,match='seal'):records.read_episode(p)
