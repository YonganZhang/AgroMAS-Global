"""WOFOST parameter/driver adapters; leave PCSE physical equations untouched."""
import copy
from pcse.util import reference_ET
from pcse.base.weather import WeatherDataProvider

CO2_TABLES=('CO2AMAXTB','CO2EFFTB','CO2TRATB')


def configure_co2(parameters, concentration):
    if not 150 <= concentration <= 1500:
        raise ValueError('CO2 concentration outside research bounds')
    # Must be called after crop activation and before initializing crop physiology.
    for key in CO2_TABLES:
        if key not in parameters:
            raise ValueError('Missing physiological CO2 response table: '+key)
    parameters.set_override('CO2',float(concentration),check=True)
    return parameters


def assert_co2_physiology(engine):
    if engine.crop is None:
        raise ValueError('Crop not emerged/initialized')
    from pcse.crop.evapotranspiration import EvapotranspirationCO2,EvapotranspirationCO2Layered
    module=engine.crop.evtra.etmodule
    if not isinstance(module,(EvapotranspirationCO2,EvapotranspirationCO2Layered)):
        raise ValueError('Active evapotranspiration branch ignores CO2')
    for key in ('CO2',)+CO2_TABLES:
        if key not in engine.parameterprovider:
            raise ValueError('Missing CO2 physiological parameter')
    return type(module).__name__


class ScenarioWeather(WeatherDataProvider):
    """Idealized T/rain/radiation sensitivities, explicitly not actual CMIP6 projections."""
    def __init__(self, source, delta_temperature=0., rain_scale=1., radiation_scale=1., angstrom=None):
        super().__init__()
        import math
        if not all(math.isfinite(x) for x in [delta_temperature,rain_scale,radiation_scale]) or min(rain_scale,radiation_scale)<0:
            raise ValueError('Invalid climate sensitivity')
        self.source=source
        self.delta_temperature=delta_temperature
        self.rain_scale=rain_scale
        self.radiation_scale=radiation_scale
        self.latitude=source.latitude;self.longitude=source.longitude;self.elevation=source.elevation
        self.angstA,self.angstB=angstrom if angstrom is not None else (source.angstA,source.angstB)
        if self.angstA is None or self.angstB is None:
            raise ValueError('Explicit source Angstrom constants required; cached provider lost metadata')
        self.description=['Idealized sensitivity; NOT actual CMIP6 model/member projections']

    def __call__(self, day, member_id=0):
        if member_id!=0:
            raise ValueError('Deterministic physical weather provider')
        w=copy.deepcopy(self.source(day))
        w.TMIN+=self.delta_temperature;w.TMAX+=self.delta_temperature
        if hasattr(w,'TEMP'):w.TEMP+=self.delta_temperature
        w.RAIN*=self.rain_scale;w.IRRAD*=self.radiation_scale
        e0,es0,et0=reference_ET(DAY=w.DAY,LAT=w.LAT,ELEV=w.ELEV,TMIN=w.TMIN,TMAX=w.TMAX,
                              IRRAD=w.IRRAD,VAP=w.VAP,WIND=w.WIND,ANGSTA=self.angstA,ANGSTB=self.angstB)
        w.E0=e0/10.;w.ES0=es0/10.;w.ET0=et0/10.
        return w
