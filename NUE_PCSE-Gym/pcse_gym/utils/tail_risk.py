"""Pre-registered training-only terminal risk surrogate; no test-derived calibration."""
import numpy as np

def episode_risk(outcome):
    return (max(0., (outcome['surplus']-40)/40) +
            max(0., (8.-outcome['yield_t_ha'])/8) +
            max(0., (outcome['N_loss']-40)/40))

def tail_cost(risk, previous_risks, alpha):
    if alpha is None or not previous_risks:return 0.,None,False
    if not 0 < alpha <= 1:raise ValueError('alpha must be in (0,1]')
    threshold=float(np.quantile(previous_risks[-256:],1-alpha))
    selected=bool(risk>=threshold)
    return float(risk/alpha if selected else 0.),threshold,selected
