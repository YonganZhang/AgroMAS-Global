"""Observable-state candidate inference and deterministic specialist coordination."""
from dataclasses import dataclass
import numpy as np
from .contracts import CandidateTable,compliance,upper_cvar


@dataclass(frozen=True)
class Decision:
    dose: float
    predicted_infeasible: bool
    scores: tuple
    model_id: str


class CoreAgronomicAgent:
    """Predictor is TRAIN-fitted; receives only an explicit observable feature vector."""
    def __init__(self, predictor, model_id, continuation_policy_id):
        if not model_id or not continuation_policy_id:
            raise ValueError('Model provenance required')
        self.predictor=predictor
        self.model_id=model_id
        self.continuation_policy_id=continuation_policy_id

    def candidates(self, state, doses, climate_vector, shared_context, soil_profile_id=''):
        context=np.asarray(shared_context,dtype=float)
        if context.ndim!=1 or not np.isfinite(context).all():
            raise ValueError('Only finite observable vectors accepted')
        observed=np.array([state.dvs,state.lai,state.sm,state.n_fert_cum,state.n_uptake,state.stage])
        rows=np.array([np.r_[observed,climate_vector,context,float(d)] for d in doses])
        members=np.asarray(self.predictor(rows),dtype=float)
        if np.any(members[:,:,4] < state.n_fert_cum+np.asarray(doses)[:,None]-1e-7):
            raise ValueError('Predicted seasonal fertilizer below already committed fertilizer')
        return CandidateTable(doses,members,state.as_of,state.region_id,
                              self.continuation_policy_id,climate_vector,self.model_id,soil_profile_id)


def select_objective(table, economic, cap, beta, eta):
    """Shared monolithic reference; same table/target must produce same choice."""
    if not np.isfinite([beta,eta]).all() or min(beta,eta)<0:
        raise ValueError('Invalid objective weights')
    score=economic['expected_profit']+beta*compliance(table.members,cap).mean(1)-eta*np.array([
        upper_cvar(x[:,2]) for x in table.members])
    # Equal objectives choose the smaller dose independently of input ordering.
    i=int(np.lexsort((table.doses,-score))[0])
    return Decision(float(table.doses[i]),False,tuple(float(x) for x in score),table.model_id)


class AgroMASGlobalCoordinator:
    def __init__(self, eco, economics, beta=0., eta=0.):
        self.eco=eco
        self.economics=economics
        self.beta=beta
        self.eta=eta

    def choose(self, table, remaining_budget, agronomic_upper):
        safe=self.eco.filter(table,remaining_budget,agronomic_upper)
        if safe.predicted_infeasible:
            return Decision(0.,True,(),table.model_id)
        priced=self.economics.price(safe.table,self.eco.cap)
        return select_objective(safe.table,priced,self.eco.cap,self.beta,self.eta)
