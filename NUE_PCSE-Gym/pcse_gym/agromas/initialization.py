"""Native layered water initialization units; no changes to PCSE physics.

WAV is plant-available water ABOVE wilting point, not total water storage.
The native partly rooted first layer counts in TOPLIM in its entirety. Below
that, LOWLIM uses saturation. Actual sowing/late-season states must be checked
separately; initial-capacity algebra alone cannot establish later stress causes.
"""
import numpy as np


def water_initialization(soil, *, target='field_capacity', fraction=1., rooted_depth_cm=10.):
    if target not in ('field_capacity','native_available_capacity') or not 0<=fraction<=1:
        raise ValueError('Explicit bounded initialization convention required')
    layers=soil['SoilProfileDescription']['SoilLayers']
    wp=[];fc=[];sat=[];dz=[];rooted=[];depth=0.
    for layer in layers:
        curve=np.array(layer['SMfromPF'],dtype=float)
        pf=curve[::2];theta=curve[1::2]
        wp.append(np.interp(4.2,pf,theta));fc.append(np.interp(2.,pf,theta));sat.append(np.interp(-1.,pf,theta))
        dz.append(layer['Thickness']);rooted.append(depth<rooted_depth_cm);depth+=layer['Thickness']
    wp,fc,sat,dz=np.array([wp,fc,sat,dz]);rooted=np.array(rooted)
    if not (np.isfinite([wp,fc,sat,dz]).all() and np.all(0<=wp) and np.all(wp<fc) and np.all(fc<sat)):
        raise ValueError('Invalid water-retention capacity')
    # SMLIM is field capacity in rooted layers, identical to source native rule.
    avmax=np.where(rooted,fc-wp,sat-wp)*dz
    top=float(avmax[rooted].sum());low=float(avmax[~rooted].sum())
    wav=float(fraction*np.dot(fc-wp,dz)) if target=='field_capacity' else fraction*(top+low)
    if wav<=top:
        topred=wav/top if top else 0.;lowred=0.
    elif wav<top+low:
        topred=1.;lowred=(wav-top)/low if low else 0.
    else:
        topred=1.;lowred=1.
    sm=wp+np.where(rooted,topred,lowred)*avmax/dz
    return dict(WAV_cm=wav,SMLIM=float(fc[0]),TOPLIM_cm=top,LOWLIM_cm=low,
                TOPRED=topred,LOWRED=lowred,predicted_initial_SM=sm.tolist(),
                wilting_point=wp.tolist(),field_capacity=fc.tolist(),saturation=sat.tolist(),
                target=target,fraction=fraction,scope='Initialization convention/control, not observed regional water state')
