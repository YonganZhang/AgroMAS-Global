"""Member-wise partial farmer budgets; subsidies/taxes are public transfers."""
from dataclasses import dataclass
import numpy as np
from .contracts import compliance


@dataclass(frozen=True)
class EconomicPolicy:
    nitrogen_price: float
    grain_price: float
    subsidy: float=0.
    surplus_tax: float=0.
    market_moisture: float=0.

    def __post_init__(self):
        x=[self.nitrogen_price,self.grain_price,self.subsidy,self.surplus_tax,self.market_moisture]
        if not np.isfinite(x).all() or min(x)<0 or self.market_moisture>=1:
            raise ValueError('Invalid economic units or values')


class SocioEconomicPolicyAgent:
    def __init__(self, policy):
        self.policy=policy

    def price(self, table, cap):
        if not np.isfinite(cap) or cap<=0:
            raise ValueError('Invalid surplus cap')
        p=self.policy
        m=table.members
        transfer=p.subsidy*compliance(m,cap)-p.surplus_tax*np.maximum(m[:,:,2]-cap,0)
        partial_profit=1000*p.grain_price*m[:,:,0]/(1-p.market_moisture)-p.nitrogen_price*m[:,:,4]+transfer
        order=np.argsort(table.doses)
        gradient=np.zeros(len(order))
        if len(order)>1:
            gradient[order]=np.gradient(partial_profit.mean(1)[order],table.doses[order])
        means=partial_profit.mean(1)
        best=table.doses[np.isclose(means,means.max(),rtol=0,atol=1e-8)]
        return dict(member_profit=partial_profit,expected_profit=means,public_transfer=transfer,
                    marginal_return=gradient,marginal_return_defined=len(order)>1,dose_bracket=(float(best.min()),float(best.max())),
                    metric='partial_N_management_budget_EUR_ha')
