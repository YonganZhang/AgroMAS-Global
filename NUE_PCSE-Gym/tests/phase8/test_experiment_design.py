"""Guard scientific comparison regimes before the expensive native campaign."""
from pathlib import Path
from itertools import product
import json
import pytest

@pytest.fixture(scope='module')
def design():
 root=Path(__file__).resolve().parents[3]
 return json.loads((root/'reports/phase8/phase8c-frozen-cases-v2.json').read_text())

def test_all_p1_worlds_have_standard_regime_without_last_case_contamination(design):
 p1=[c for c in design['cases'] if 'P1' in c['phase8c_groups']]
 assert len(p1)==924
 assert len({(c['region'],c['year'],c['source']) for c in p1})==66
 assert all((c['cap'],c['price_multiplier'],c['subsidy'],c['tax'])==(40.,1.,0.,0.) for c in p1)
 for c in design['cases']:
  if c['price_multiplier']==2. and any(g.startswith('G3-') for g in c['phase8c_groups']):assert c['subsidy']==0.

def test_factorial_and_continuity_subsets_contain_every_declared_combination(design):
 regions={c[0] for c in design['factorial_cells']};assert len(regions)==5
 expected=set(product(regions,('Historical','idealized_mid','idealized_high'),(25.,35.,40.,50.),('standard','price2','sub50')))
 assert set(map(tuple,design['factorial_cells']))==expected
 expected90={c for c in expected if c[2] in (25.,35.,50.) and c[3] in ('standard','price2')}
 assert len(expected90)==90 and set(map(tuple,design['canonical90_cells']))==expected90

def test_repaired_and_archived_modes_are_not_conflated(design):
 p1=[c for c in design['cases'] if 'P1' in c['phase8c_groups'] and c['policy']=='TreeMLP']
 bare=[c for c in p1 if c['mode']=='hard-bare-tier2'];assert len(bare)==132 and all('reuse' in c for c in bare)
 repaired=[c for c in p1 if c['mode']=='tree'];assert len(repaired)==132 and all('reuse' not in c for c in repaired)
 assert sum('reuse' in c for c in design['cases'])==719
 assert design['new_native']==17549


def test_v3_versions_every_reconstructed_ppo_and_removes_old_ppo_reuse():
 root=Path(__file__).resolve().parents[3];d=json.loads((root/'reports/phase8/phase8c-frozen-cases-v3.json').read_text())
 assert d['total']==18268 and d['new_native']==17747 and d['reused']==521
 for c in d['cases']:
  if c['policy']=='SensorlessPPO':
   assert c['ppo_checkpoint']=='phase8c-train-reconstruction-v1' and 'reuse' not in c
 assert all((c['cap'],c['price_multiplier'],c['subsidy'],c['tax'])==(40.,1.,0.,0.) for c in d['cases'] if 'P1' in c['phase8c_groups'])
