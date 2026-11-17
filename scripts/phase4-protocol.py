"""Domain-specific19-asset catalog and approved pre-heldout progression rules."""
import pathlib,json,sys,hashlib
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'NUE_PCSE-Gym'))
from pcse_gym.utils.frozen_audit import validate_manifest,sha
EXPECTED={(m,s) for m in ['raw','corrected','masked','guided','full4','cf-gru'] for s in [4,17,29]}|{('utilityprior',None)}
def check_catalog(payload,root=R):
 root=pathlib.Path(root)
 models=payload.get('models',[]);keys=[(m['model'],m['seed']) for m in models]
 if len(models)!=19 or len(set(keys))!=19 or set(keys)!=EXPECTED:raise ValueError('All19distinct model assets required')
 if any(payload['files'].get(m['path'])!=m['sha256'] for m in models):raise ValueError('Model catalog/files mismatch')
 if payload.get('primary_policy')!='utilityprior':raise ValueError('Frozen primary policy mismatch')
 amendment=root/'reports/phase4-protocol-amendment.json'
 if not amendment.exists() or payload['files'].get(str(amendment.relative_to(root)))!=sha(amendment):raise ValueError('Approved protocol amendment missing')
 approved=json.loads(amendment.read_text())
 if approved['option']!='A' or not approved['approved'] or approved['decision_id']!='phase4_cf_dev_shortfall':raise ValueError('Protocol amendment invalid')
 if payload.get('cf_point_target_passed') is not False:raise ValueError('OriginalCFpoint target must remainfailed')
 return payload

def validate_domain_manifest(root=R,verify_files=True):
 return check_catalog(validate_manifest(root,verify_files),root)
