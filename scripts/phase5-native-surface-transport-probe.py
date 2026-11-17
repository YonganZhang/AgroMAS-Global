"""Synthetic isolated native transport counterexample, not field/calibration evidence."""
from types import SimpleNamespace
from pathlib import Path
import json,numpy as np
from pcse.soil.snomin import SNOMIN
R=Path(__file__).resolve().parents[1]
if __name__=='__main__':
 layers=[SimpleNamespace(Thickness_m=.2,RHOD_kg_per_m3=1400.) for _ in range(7)]
 flow=np.zeros(8);flow[0]=-.001 #1mm/day outward upper waterflux, e.g.soilevaporation
 nitrate=np.zeros(7);nitrate[0]=.01 #100kgN/ha in top20cm
 sm=np.full(7,.3)
 model=SNOMIN.SoilInorganicNModel.SoilNNitrateModel()
 incoming,outgoing=model.calculate_NO3_flow_rates(layers,flow,nitrate,sm)
 out=dict(scope='Synthetic pure transport unit probe, not regional observation or fitted result',
 upper_water_flux_m_day=float(flow[0]),initial_NO3_kg_ha=float(nitrate.sum()*1e4),
 NO3_profile_boundary_export_kg_ha_day=float((outgoing-incoming).sum()*1e4),
 bottom_NO3_export_kg_ha_day=float(outgoing[-1]*1e4),
 interpretation='Nativeupperoutwardwaterfluxexportsnitrate;separatefrompublishedbottomleaching.Nofieldatmosphericlossclaim.',
 source='multilayer_waterbalance.pyFlow0=RIN-EVflow0;snomin.pyget_water_flow_rates;SoilNNitrateModel.calculate_NO3_flow_rates')
 with (R/'reports/phase5/native-surface-transport-probe-v2.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out),flush=True)
