"""Read native whole-profile stocks/flows; never redefine primary native NUE/S."""
import numpy as np


def stock_diagnostics(engine,metadata,outcome):
    def value(name):
        x=engine.get_variable(name)
        if x is None:raise ValueError('Missing native stock/flow:'+name)
        return float(np.asarray(x).sum())
    initial=metadata['initial_stock_ledger']
    n0=float(sum(initial['organic_N_kg_ha'])+sum(initial['initial_NO3_kg_ha'])+sum(initial['initial_NH4_kg_ha']))
    # Native published total stocks are already kg/ha; raw cumulative R* are kg/m2.
    organic=value('NORGT');mineral=value('NO3T')+value('NH4T');n1=organic+mineral
    uptake=1e4*(value('RNH4UPTT')+value('RNO3UPTT'))
    fert=1e4*(value('RNH4AMTT')+value('RNO3AMTT'))
    deposition=1e4*(value('RNH4DEPOSTT')+value('RNO3DEPOSTT'))
    loss=value('NLOSSCUM')
    net_boundary=1e4*(value('RNH4OUTTT')+value('RNO3OUTTT')-value('RNH4INTT')-value('RNO3INTT'))
    denitrification=1e4*value('RNO3DENITRTT')
    delta=n0-n1
    inputs=float(outcome[4]+outcome[5]);extended=inputs+delta
    return dict(initial_soil_N_kg_ha=n0,final_soil_N_kg_ha=n1,final_organic_N_kg_ha=organic,
        final_mineral_N_kg_ha=mineral,soil_N_stock_drawdown_kg_ha=delta,
        native_soil_crop_uptake_N_kg_ha=uptake,native_Nloss_kg_ha=loss,
        net_profile_mineral_N_boundary_export_kg_ha=net_boundary,
        native_denitrification_N_kg_ha=denitrification,
        native_published_leaching_plus_denitrification_kg_ha=loss,
        upper_boundary_export_not_in_published_loss_kg_ha=net_boundary+denitrification-loss,
        soil_N_mass_balance_residual_kg_ha=n0+fert+deposition-n1-uptake-net_boundary-denitrification,
        initial_soil_C_kg_ha=float(sum(initial['organic_C_kg_ha'])),final_soil_C_kg_ha=value('CORGT'),
        native_net_mineralization_N_kg_ha=1e4*value('RNH4MINTT'),
        native_fertilizer_N_kg_ha=fert,native_deposition_N_kg_ha=deposition,
        native_NUE=float(outcome[3]),native_surplus_kg_ha=float(outcome[2]),
        stock_adjusted_apparent_NUE=float(outcome[1]/extended) if extended>0 else None,
        stock_adjusted_balance_kg_ha=extended-float(outcome[1]),
        scope='Campaign-start to crop-end native profile stock/flow diagnostics; NLOSSCUM is bottom leaching+denitrification, not all boundary exports; upper-boundary flux requires physical-interface qualification; stock-adjusted boundary is secondary, never the primary research compliance criterion')
