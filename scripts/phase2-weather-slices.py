import pathlib,json,pandas as pd,numpy as np
R=pathlib.Path(__file__).resolve().parents[1]
df=pd.read_csv(R/'data/52.57-5.63_random_weather.csv',skiprows=8,usecols=['DAY','RAIN'])
s=df.DAY.astype(str);year=s.str[:4].astype(int);month=s.str[4:6].astype(int)
harvest=year+(month>=10).astype(int);valid=(month>=10)|(month<=7)
rain=df.loc[valid,'RAIN'].groupby(harvest[valid]).sum()
train=rain.loc[3002:4999];q25=float(train.quantile(.25));q10=float(train.quantile(.10))
assert len(train)==1998
out=dict(definition='Cumulative precipitation Oct(previous year)-Jul(harvest year); drought <= training q25; extreme <= training q10. Thresholds never fitted on dev/stress/historical.',training_harvest_years=[3002,4999],training_season_count=len(train),q25_rain_mm=q25,q10_rain_mm=q10,years={str(int(y)):dict(rain_mm=float(x),drought=bool(x<=q25),extreme=bool(x<=q10)) for y,x in rain.items() if 1983<=y<=2021 or 3002<=y<=5998})
(R/'reports/phase2-weather-slices.json').write_text(json.dumps(out,indent=2));print(q25,q10)
