"""Feature-only prior availability/OOD audit; never scores outcome labels."""
from pathlib import Path
import json,joblib,numpy as np
R=Path(__file__).resolve().parents[1];D=R/'cache/phase8-p2-adapter-inputs';P=R/'reports/phase8'
if __name__=='__main__':
 metadata=joblib.load(D/'metadata.joblib');x=np.load(D/'x.npy');world=np.array(metadata['world']);regions=np.array([w.rsplit(':',1)[0] for w in world]);years=np.array([w.rsplit(':',1)[1] for w in world]);context=metadata['context'];rows=[]
 for receipt in json.loads((P/'phase8b-P2-adapter-training-freeze.json').read_text())['fits']:
  scheme,held,variant=receipt['scheme'],receipt['held'],receipt['variant'];adapter=joblib.load(R/f'models/phase8-controls/p2-adapters/{scheme}-{held}/{variant}.joblib');labels=years if scheme=='LOYO' else regions
  for role,indices in [('outer_train',np.flatnonzero(labels!=held)),('outer_test',np.flatnonzero(labels==held))]:
   for region in np.unique(regions[indices]):
    ix=indices[regions[indices]==region];_,accepted=adapter.correction(x[ix],[context[i] for i in ix]);rows.append(dict(scheme=scheme,held=held,variant=variant,role=role,region=region,rows=len(ix),accepted=int(accepted.sum()),rejected=int((~accepted).sum()),site_years=len(set(world[ix]))))
 # All timing checks are row-local features, not a reason to open labels.
 from datetime import date
 timing=sum(date.fromisoformat(metadata['priors'][key][1])<date.fromisoformat(day) for key,day in context)
 cn=[v for v in rows if v['scheme']=='LOYO' and v['variant']=='Full64' and v['role']=='outer_train' and v['region']=='china_ncp_luancheng'];assert sum(v['rejected'] for v in cn)==0,'Site-year-weighted99%threshold must not exclude sparse China training worlds'
 (P/'phase8b-prior-admissibility-audit.json').write_text(json.dumps(dict(feature_only=True,outcome_labels_read=False,annual_timing_admissible=timing,total_rows=len(x),rows=rows,China_LOYO_Full64_train_rejections=sum(v['rejected'] for v in cn)),indent=2));print('Feature-only prior admissibility audited; China weighted training rejections=0',flush=True)
