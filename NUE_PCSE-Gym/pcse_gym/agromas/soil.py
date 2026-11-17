"""Point-wise published HiHydroSoil/Toth PTF replication from real SoilGrids inputs.

This derives estimates, NOT downloaded HiHydroSoil map values or measured farm
hydraulics. European-PTF transfer uncertainty must remain visible outside Europe.
Source: Simons et al.2020, FutureWater Report213, section2.2 and Annex1.
"""
from pathlib import Path
import json,hashlib
import numpy as np
from .regions import sha256

PTF_SOURCE='https://www.futurewater.nl/wp-content/uploads/2020/10/HiHydroSoil-v2.0-High-Resolution-Soil-Maps-of-Global-Hydraulic-Properties.pdf'
PF=np.array([-1.,0.,1.,1.3,1.7,2.,2.5,3.,3.4,3.7,4.,4.2,5.,6.])


def published_ptf(bulk_density,clay_pct,silt_pct,sand_pct,organic_carbon_pct,ph,cec,topsoil):
    x=np.array([bulk_density,clay_pct,silt_pct,sand_pct,organic_carbon_pct,ph,cec],dtype=float)
    if not np.isfinite(x).all() or bulk_density<=0 or min(x[1:])<0 or not 0<ph<14:
        raise ValueError('Invalid PTF source units')
    bd,cl,si,sa,oc,ph,cec=x;ts=float(bool(topsoil))
    residual=.041 if sa>=2 else .179
    saturation=.83080-.28217*bd+.0002728*cl+.000187*si
    alpha=10**(-.43348-.41729*bd-.04762*oc+.21810*ts-.01581*cl-.01207*si)
    n=1+10**(.22236-.30189*bd-.05558*ts-.005306*cl-.003084*si-.01072*oc)
    ksat=10**(.40220+.26122*ph+.44565*ts-.02329*cl-.01265*si-.01038*cec)
    if not 0<=residual<saturation<1 or alpha<=0 or n<=1 or ksat<=0:
        raise ValueError('Published PTF outside physical domain; no clamping')
    m=1-1/n
    se=(1+(alpha*10**PF)**n)**(-m)
    theta=residual+(saturation-residual)*se
    # Canonical Mualem connectivity exponent0.5, not a fitted regional multiplier.
    k=ksat*np.sqrt(se)*(1-(1-se**(1/m))**m)**2
    if not (np.isfinite(theta).all() and np.all(np.diff(theta)<0) and np.all(k>0)):
        raise ValueError('Invalid hydraulic curve')
    return dict(theta_residual=residual,theta_saturated=saturation,alpha_cm_inverse=alpha,n=n,
                ksat_cm_day=ksat,SMfromPF=np.column_stack([PF,theta]).ravel().tolist(),
                CONDfromPF=np.column_stack([PF,np.log10(k)]).ravel().tolist())


def derive_soil(raw_path,expected_sha256):
    if sha256(raw_path)!=expected_sha256:raise ValueError('Raw soil SHA drift')
    body=json.loads(Path(raw_path).read_text())
    layers={layer['name']:layer for layer in body['properties']['layers']}
    required=('bdod','clay','silt','sand','soc','phh2o','cec')
    if set(required)-set(layers):raise ValueError('Missing soil input properties')
    # Convert using response metadata. Targets:BD kg/dm3=g/cm3;texture %;SOC g/kg;pH;CEC cmol(c)/kg.
    expected_units={'bdod':'kg/dm³','clay':'%','silt':'%','sand':'%','soc':'g/kg','phh2o':'-','cec':'cmol(c)/kg'}
    for key in required:
        if layers[key]['unit_measure']['target_units']!=expected_units[key]:
            raise ValueError('Unexpected soil units for '+key)
    source_depths=[(d['range']['top_depth'],d['range']['bottom_depth']) for d in layers['bdod']['depths']]
    def average(key,start,end):
        layer=layers[key];values=[];weights=[]
        for d,(lo,hi) in zip(layer['depths'],source_depths):
            overlap=max(0,min(end,hi)-max(start,lo))
            if overlap:
                value=d['values'].get('mean')
                if value is None:raise ValueError('Null soil source; no replacement')
                values.append(value/layer['unit_measure']['d_factor']);weights.append(overlap)
        if sum(weights)!=end-start:raise ValueError('Unobserved soil depth, no extrapolation')
        return float(np.average(values,weights=weights))
    result=[];diagnostics=[]
    for start,end in ((0,20),(20,30),(30,40),(40,60),(60,80),(80,100),(100,125)):
        inp={key:average(key,start,end) for key in required}
        hydraulic=published_ptf(inp['bdod'],inp['clay'],inp['silt'],inp['sand'],
                                inp['soc']/10,inp['phh2o'],inp['cec'],start<30)
        # Native process/aeration/C:N priors are explicit common model assumptions,
        # NOT inferred organic C:N from SoilGrids total N (which includes mineral N).
        cn_prior=9. if start<30 else 18.
        result.append(dict(Thickness=float(end-start),SMfromPF=hydraulic['SMfromPF'],
                           CONDfromPF=hydraulic['CONDfromPF'],RHOD=inp['bdod'],
                           FSOMI=1.72*inp['soc']/1000,CNRatioSOMI=cn_prior,
                           Soil_pH=inp['phh2o'],CRAIRC=.09))
        diagnostics.append(dict(depth_cm=[start,end],source_inputs=inp,**{k:v for k,v in hydraulic.items() if k not in ('SMfromPF','CONDfromPF')}))
    subsoil=dict(result[-1]);subsoil['Thickness']=200.
    profile=dict(RDMSOL=125.,SoilProfileDescription=dict(GroundWater=False,PFFieldCapacity=2.,PFWiltingPoint=4.2,
                 SoilLayers=result,SubSoilType=subsoil,SurfaceConductivity=diagnostics[0]['ksat_cm_day']))
    identity=hashlib.sha256(json.dumps(profile,sort_keys=True).encode()).hexdigest()
    return profile,dict(profile_id=identity,source_sha256=expected_sha256,soil_coordinates=body['geometry']['coordinates'],
         pedotransfer_source=PTF_SOURCE,method='Pointwise published PTF replication; not official raster extraction or measured profile',
         assumptions={'CN_top':9.,'CN_sub':18.,'CRAIRC':.09,'organic_C_to_OM':1.72,'Mualem_L':.5},layers=diagnostics)
