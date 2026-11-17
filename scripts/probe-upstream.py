import requests,json,pathlib,concurrent.futures
repos=['WUR-AI/PCSE-Gym','hbja/PCSE-Gym','hbja/NUE_PCSE-Gym','hbja/pcse','ajwdewit/WOFOST']
def check(n):
 s=requests.Session();m=s.get('https://api.github.com/repos/'+n,timeout=25);out={'repo':n,'status':m.status_code}
 if m.ok:
  j=m.json();r=s.get('https://api.github.com/repos/'+n+'/git/trees/'+j['default_branch']+'?recursive=1',timeout=30);out['tree']=r.json();out['matches']=[z['path'] for z in r.json().get('tree',[]) if any(v in z['path'].lower() for v in ['normalization','52.57','weather_csv','lelystad'])];print(n,out['matches'][:30],flush=True)
 pathlib.Path('reports/upstream-'+n.replace('/','-')+'.json').write_text(json.dumps(out,indent=2))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as x:list(x.map(check,repos))
