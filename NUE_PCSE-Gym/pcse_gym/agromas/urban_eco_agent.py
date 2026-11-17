"""Research surplus scenarios, not legal water-quality concentration thresholds."""
from dataclasses import dataclass
import numpy as np
from .contracts import CandidateTable

@dataclass(frozen=True)
class SoilHydraulicContext:
    profile_id: str
    region_id: str
    source_id: str
    texture: str
    field_capacity: float
    wilting_point: float
    saturated_conductivity_cm_day: float

    def __post_init__(self):
        if not self.profile_id or not self.region_id or not self.source_id:
            raise ValueError('Soil provenance required')
        if self.texture not in ('coarse','medium','fine'):
            raise ValueError('Unknown hydraulic texture class')
        values=[self.field_capacity,self.wilting_point,self.saturated_conductivity_cm_day]
        if not np.isfinite(values).all() or not 0<=self.wilting_point<self.field_capacity<=1 or self.saturated_conductivity_cm_day<=0:
            raise ValueError('Invalid hydraulic profile')


CAPS={'strict_25':25.,'buffer_35':35.,'standard_40':40.,'outer_50':50.}


@dataclass(frozen=True)
class EcoResult:
    table: CandidateTable | None
    safe_doses: tuple
    upper_dose: float
    violation_probability: np.ndarray
    shadow_penalty: float
    predicted_infeasible: bool


class UrbanEcoSafetyAgent:
    def __init__(self, zone='standard_40', epsilon=.1, dual=0., dual_rate=0., soil_profile=None):
        if zone not in CAPS or not 0 < epsilon < 1 or not np.isfinite([dual,dual_rate]).all() or min(dual,dual_rate)<0:
            raise ValueError('Invalid research zone or tolerance')
        self.cap=CAPS[zone]
        self.epsilon=epsilon
        self.zone=zone
        self.dual=dual
        self.dual_rate=dual_rate
        self.soil_profile=soil_profile

    def filter(self, table, remaining_budget, agronomic_upper):
        if not np.isfinite([remaining_budget,agronomic_upper]).all() or min(remaining_budget,agronomic_upper)<0:
            raise ValueError('Invalid dose bound')
        if self.soil_profile is not None and (table.soil_profile_id!=self.soil_profile.profile_id or table.region_id!=self.soil_profile.region_id):
            raise ValueError('Candidate risk model and hydraulic profile mismatch')
        # Hydraulic effects enter the same TRAIN conditional member table; no arbitrary vulnerability multiplier.
        surplus=table.members[:,:,2]
        q=np.quantile(surplus,1-self.epsilon,axis=1,method='higher')
        mask=(q<=self.cap)&(table.doses<=min(remaining_budget,agronomic_upper))
        safe=tuple(float(x) for x in table.doses[mask])
        violation=np.mean(surplus>self.cap,axis=1)
        violation.setflags(write=False)
        return EcoResult(table.subset(mask) if safe else None,safe,max(safe,default=0.),violation,
                         max(0.,self.dual+self.dual_rate*(float(q.min())-self.cap)),not bool(safe))
