"""Shared, physical-unit interfaces; no simulator state or future truth access."""
from dataclasses import dataclass
from datetime import date
import numpy as np


def finite_array(value, shape=None):
    a = np.array(value, dtype=np.float64, copy=True)
    if (shape is not None and a.shape != shape) or not np.isfinite(a).all():
        raise ValueError('Invalid shape or non-finite values')
    a.setflags(write=False)
    return a


@dataclass(frozen=True)
class FieldState:
    as_of: date
    region_id: str
    dvs: float
    lai: float
    sm: float
    n_fert_cum: float
    n_uptake: float
    stage: int
    privileged_uptake: bool = True

    def __post_init__(self):
        x = finite_array([self.dvs,self.lai,self.sm,self.n_fert_cum,self.n_uptake])
        if not self.region_id or not 0 <= x[2] <= 1 or (not -1 <= x[0] <= 3 or min(x[1:]) < 0) or self.stage not in (0,1,2,3):
            raise ValueError('Invalid field observation')


@dataclass(frozen=True)
class CandidateTable:
    """A x M x 6: yield DM t/ha, grain N, surplus, NUE, full fertilizer, nonfert N."""
    doses: np.ndarray
    members: np.ndarray
    as_of: date
    region_id: str
    continuation_policy_id: str
    climate_vector: np.ndarray
    model_id: str
    soil_profile_id: str = ''

    def __post_init__(self):
        doses = finite_array(self.doses)
        m = finite_array(self.members)
        c = finite_array(self.climate_vector, (4,))
        if doses.ndim != 1 or not len(doses) or np.any(doses < 0) or len(np.unique(doses)) != len(doses):
            raise ValueError('Invalid dose grid')
        if m.ndim != 3 or m.shape[0] != len(doses) or m.shape[1] < 1 or m.shape[2] != 6:
            raise ValueError('Invalid joint members')
        if not self.region_id or not self.model_id or not self.continuation_policy_id:
            raise ValueError('Provenance required')
        if np.any(m[:,:,[0,1,4,5]] < 0) or np.any(m[:,:,4]+m[:,:,5] <= 0):
            raise ValueError('Invalid yield or nitrogen inputs')
        if not np.allclose(m[:,:,2],m[:,:,4]+m[:,:,5]-m[:,:,1],atol=1e-7):
            raise ValueError('Nitrogen surplus mass balance')
        if not np.allclose(m[:,:,3],m[:,:,1]/(m[:,:,4]+m[:,:,5]),atol=1e-7):
            raise ValueError('NUE mass balance')
        if not (0<=c[0]<=1 and 0<=c[1]<=1 and -1<=c[2]<=1 and 0<=c[3]<=1):
            raise ValueError('Invalid climate vector')
        object.__setattr__(self,'doses',doses)
        object.__setattr__(self,'members',m)
        object.__setattr__(self,'climate_vector',c)

    def subset(self, mask):
        return CandidateTable(self.doses[mask],self.members[mask],self.as_of,self.region_id,
                              self.continuation_policy_id,self.climate_vector,self.model_id,self.soil_profile_id)


def upper_cvar(values, fraction=.1):
    """Exact upper-tail mean for equiprobable discrete members, fractional boundary weight."""
    x = finite_array(values)
    if x.ndim != 1 or not len(x) or not 0 < fraction <= 1:
        raise ValueError('Invalid tail')
    x = np.sort(x)[::-1]
    mass = fraction*len(x)
    weights = np.clip(mass-np.arange(len(x)),0,1)
    return float(np.dot(x,weights)/mass)


def compliance(members, cap):
    return ((members[...,3]>=.5)&(members[...,3]<=.9)&
            (members[...,2]>=0)&(members[...,2]<=cap))
