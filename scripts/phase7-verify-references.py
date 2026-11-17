"""Pin reference metadata from DOI registration records; never invent bibliographic fields."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests,json,re,time,html
R=Path(__file__).resolve().parents[1];P=R/'reports/phase7';OUT=R/'manuscript/phase7'
DOIS={'zhang2015':'10.1038/nature15743','dewit2019':'10.1016/j.agsy.2018.06.018','berghuijs2024':'10.1016/j.eja.2024.127099','jones2003':'10.1016/S1161-0301(02)00107-7','holzworth2014':'10.1016/j.envsoft.2014.07.009','stockle2003':'10.1016/S1161-0301(02)00109-0','vanittersum2013':'10.1016/j.fcr.2012.09.009','cassman2002':'10.1579/0044-7447-31.2.132','poggio2021':'10.5194/soil-7-217-2021','geurts2006':'10.1007/s10994-006-6226-1','hoerl1970':'10.1080/00401706.1970.10488634','roberts2017':'10.1111/ecog.02881','phipson2010':'10.2202/1544-6115.1585','baja2025':'10.1016/j.compag.2025.110554','asseng2015':'10.1038/nclimate2470'}
def get(kv):
 key,doi=kv;folder=P/'reference-metadata';folder.mkdir(exist_ok=True);cache=folder/(key+'.json')
 if cache.exists():return key,json.loads(cache.read_text())
 for attempt in range(5):
  rr=requests.get('https://api.crossref.org/works/'+doi,headers={'User-Agent':'Phase7AcademicReferenceVerifier/1.0'},timeout=60)
  if rr.status_code==429:time.sleep(min(30,2**attempt));continue
  rr.raise_for_status();d=rr.json()['message'];cache.write_text(json.dumps(d,indent=2));time.sleep(1);return key,d
 raise RuntimeError('Reference metadata rate-limited: '+doi)
if __name__=='__main__':
 with ThreadPoolExecutor(max_workers=2) as pool:metadata=dict(pool.map(get,DOIS.items()))
 (P/'verified-reference-metadata-v7.json').write_text(json.dumps(metadata,indent=2));entries=[]
 for key,d in metadata.items():
  title=re.sub('<[^>]+>','',d['title'][0]);authors=' and '.join(a.get('family','')+', '+a.get('given','') for a in d.get('author',[]));year=d.get('published',d.get('issued'))['date-parts'][0][0];journal=d.get('container-title',[''])[0]
  fields=dict(title=title,author=authors,year=year,journal=journal,doi=d['DOI'],url='https://doi.org/'+d['DOI'])
  for name in ['volume','issue','page']:
   if name in d:fields[{'issue':'number','page':'pages'}.get(name,name)]=d[name]
  def esc(x):return html.unescape(str(x)).replace('&',r'\&').replace('%',r'\%')
  entries.append('@article{'+key+',\n'+',\n'.join('  '+k+' = {'+esc(v)+'}' for k,v in fields.items())+'\n}')
 entries += [r'''@misc{brown2025, title={AlphaEarth Foundations: An embedding field model for accurate and efficient global mapping from sparse label data}, author={Brown, C. F. and Kazmierski, M. R. and Pasquarella, V. J. and others}, year={2025}, eprint={2507.22291}, archivePrefix={arXiv}, doi={10.48550/arXiv.2507.22291}, url={https://arxiv.org/abs/2507.22291}}''',r'''@misc{ppo2017, title={Proximal Policy Optimization Algorithms}, author={Schulman, John and Wolski, Filip and Dhariwal, Prafulla and Radford, Alec and Klimov, Oleg}, year={2017}, eprint={1707.06347}, archivePrefix={arXiv}, url={https://arxiv.org/abs/1707.06347}}''',r'''@misc{mask2020, title={A Closer Look at Invalid Action Masking in Policy Gradient Algorithms}, author={Huang, Shengyi and Onta\~n\'on, Santiago}, year={2020}, eprint={2006.14171}, archivePrefix={arXiv}, url={https://arxiv.org/abs/2006.14171}}''',r'''@article{cawley2010, title={On Over-fitting in Model Selection and Subsequent Selection Bias in Performance Evaluation}, author={Cawley, Gavin C. and Talbot, Nicola L. C.}, journal={Journal of Machine Learning Research}, volume={11}, pages={2079--2107}, year={2010}, url={https://jmlr.org/papers/v11/cawley10a.html}}''',r'''@article{holm1979, title={A Simple Sequentially Rejective Multiple Test Procedure}, author={Holm, Sture}, journal={Scandinavian Journal of Statistics}, volume={6}, pages={65--70}, year={1979}, url={https://www.jstor.org/stable/4615733}}''',r'''@techreport{eunep2015, title={Nitrogen Use Efficiency: An Indicator for the Utilization of Nitrogen in Agriculture and Food Systems}, author={{EU Nitrogen Expert Panel}}, institution={Wageningen University}, year={2015}, url={https://www.eunep.com/wp-content/uploads/2023/12/Report-NUE-Indicator-Nitrogen-Expert-Panel-18-12-2015.pdf}}''',r'''@misc{worldcover2021, title={{ESA WorldCover} 10 m 2021 v200}, author={Zanaga, Daniele and Van De Kerchove, Ruben and Daems, Dirk and others}, year={2022}, doi={10.5281/zenodo.7254221}, url={https://doi.org/10.5281/zenodo.7254221}}''',r'''@misc{aefcatalog, title={Satellite Embedding V1, Earth Engine Data Catalog}, author={{Google and Google DeepMind}}, year={2026}, url={https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL}, note={Accessed 15 November 2026}}''',r'''@misc{aefmirror, title={AlphaEarth Foundations GCS data, Source Cooperative mirror}, author={{TGE Labs}}, year={2026}, url={https://s3.us-west-2.amazonaws.com/us-west-2.opendata.source.coop/tge-labs/aef/README.md}, note={Accessed 15 November 2026, mirror README advertises 2017--2025; copy is not officially supported by Google}}''']
 (OUT/'references.bib').write_text('\n\n'.join(entries)+'\n');print([(k,d['title'][0]) for k,d in metadata.items()])
