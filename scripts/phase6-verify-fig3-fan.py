from pathlib import Path
from types import SimpleNamespace
import ast,json
import numpy as np,pandas as pd

R=Path(__file__).resolve().parents[1]
d=pd.read_csv(R/'reports/phase6/annual-policy-metrics-v6.csv',float_precision='round_trip')
d=d[d.cohort=='Former-Held-Out'].copy()
d['region']=d.region_id.map(lambda x:'NL' if 'netherlands' in x else 'AU' if 'australia' in x else 'US' if 'usa' in x else 'FR' if 'france' in x else 'CN')
tree=ast.parse((R/'scripts/phase6-plot-fig3.py').read_text())
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('comparison','fan')]

class Axis:
    def __init__(self):self.calls=[];self.figure=None;self.spines={'bottom':SimpleNamespace(set_visible=lambda x:None)}
    def get_position(self):return SimpleNamespace(x0=.1,x1=.5,y0=.2,width=.4,height=.3)
    def get_ylim(self):return (-10,500)
    def get_xlim(self):return (0,200)
    def plot(self,*args,**kwargs):self.calls.append(('plot',args,kwargs))
    def fill_between(self,*args,**kwargs):self.calls.append(('fill_between',args,kwargs))
    def __getattr__(self,name):return lambda *a,**kw:None

axes=[]
def newaxis(*args,**kwargs):
    axis=Axis();axes.append(axis);return axis
ns=dict(np=np,pd=pd,CLIM=['Historical','idealized_mid','idealized_high'],SIG=[0,50,100,150,200],CLABEL={'Historical':'Hist','idealized_mid':'Warm 1','idealized_high':'Warm 2'},c=SimpleNamespace(COL=['c'+str(i) for i in range(10)],axis=newaxis))
exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-fig3-functions','exec'),ns)
main=Axis();ns['fan'](main,d,'A')
actual=[{'label':kw['label'],'x':list(a[0]),'y':np.asarray(a[1]).tolist()} for method,a,kw in main.calls if method=='plot' and 'label' in kw]
bands=[{'low':np.asarray(a[1]).tolist(),'high':np.asarray(a[2]).tolist()} for method,a,kw in main.calls if method=='fill_between']
corrected=Axis();ns['fan'](corrected,d[d.cap.isin([25,35,50])],'A')
three_caps=[{'label':kw['label'],'y':np.asarray(a[1]).tolist()} for method,a,kw in corrected.calls if method=='plot' and 'label' in kw]
assert len(actual)==len(bands)==6
assert all(np.isfinite(x['y']).all() for x in actual)
assert all(np.isfinite(x['low']).all() and np.isfinite(x['high']).all() for x in bands)
joint=[np.asarray(a[1]) for method,a,kw in axes[1].calls if method=='plot']
assert len(joint)==6 and np.allclose(joint[0],10.32323232323232)
result={'all_six_means':actual,'all_six_bands':bands,'all_six_joint_strips':[x.tolist() for x in joint],'actual_Hist1_plot_call':actual[0],'actual_Hist1_IQR_call':bands[0],'three_stress_caps_Hist1':three_caps[0],'rendered_or_saved_figures':False,'source_sha256':__import__('hashlib').sha256((R/'scripts/phase6-plot-fig3.py').read_bytes()).hexdigest()}
(R/'reports/phase6/final-fig3-fixed-population-verification-v6.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
