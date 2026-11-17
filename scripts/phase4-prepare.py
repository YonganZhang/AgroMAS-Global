"""Record paired physical histories/masks and six-action labels without new simulations."""
import pathlib,json,sys,hashlib,numpy as np
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1];module=SourceFileLoader('cf_data',str(R/'scripts/phase4-cf-train.py')).load_module()
if __name__=='__main__':
 rows,h,u,risk=module.dataset();out=R/'reports/phase4-paired-dataset.json';assert not out.exists();records=[]
 for i,row in enumerate(rows):
  es=sorted(row['episodes'],key=lambda e:e['actual_N']);records.append(dict(year=row['year'],soil=row['soil'],physical_history=h[i,:,:11].tolist(),legal_mask_history=h[i,:,11:].tolist(),candidate_actions=list(range(3,9)),candidate_total_N=list(range(160,211,10)),utility=u[i].tolist(),paired_advantage=(u[i]-u[i].mean()).tolist(),upper_surplus_risk=risk[i].tolist(),surplus=[e['surplus'] for e in es],yield_t_ha=[e['yield_t_ha'] for e in es],NUE=[e['NUE'] for e in es]))
 out.write_text(json.dumps(dict(training_only=True,source_sha256=hashlib.sha256(module.GRID.read_bytes()).hexdigest(),records=records)))
 print('Prepared360paired scenarios, physical4x11 + causal masks4x9')
