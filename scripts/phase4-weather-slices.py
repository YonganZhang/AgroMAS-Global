"""Training-only drought thresholds. Heldout labels are computed only after authorization."""
import pathlib,json,csv,collections,numpy as np,hashlib
R=pathlib.Path(__file__).resolve().parents[1]
def rain_totals(allowed):
 result=collections.defaultdict(float)
 with (R/'data/52.57-5.63_random_weather.csv').open() as f:
  for line in f:
   if line.startswith('DAY,'):break
  for row in csv.DictReader(f,fieldnames=line.strip().split(',')):
   d=row['DAY'];year=int(d[:4]);month=int(d[4:6]);harvest=year+1 if month>=10 else year
   if harvest in allowed and (month>=10 or month<=7):result[harvest]+=float(row['RAIN'])
 return dict(result)
if __name__=='__main__':
 out=R/'reports/phase4-training-weather-thresholds.json';assert not out.exists();train=rain_totals(set(range(3002,5000)));assert len(train)==1998
 q10,q25=np.quantile(list(train.values()),[.1,.25]);out.write_text(json.dumps(dict(training_only=True,train_harvest_years=[3002,4999],n=1998,season='October1previousyear_toJuly31harvestyear',q10_mm=float(q10),q25_mm=float(q25),weather_sha256=hashlib.sha256((R/'data/52.57-5.63_random_weather.csv').read_bytes()).hexdigest()),indent=2));print(q10,q25)
