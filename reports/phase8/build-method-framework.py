"""Build the Phase8B five-agent explanation using the shared native renderer and explicit page padding."""
from pathlib import Path
import subprocess,sys,json,hashlib,xml.etree.ElementTree as ET
R=Path.cwd();P=R/'reports/phase8';tool=Path('/mnt/data/yongan-admin-2/.ai-shared/skills/share-technical-roadmap/scripts/method_diagram.py');out=P/'method-framework-v8'
subprocess.run([sys.executable,str(tool),'build','--project',str(R),'--spec','reports/phase8/method-framework-spec-v8.json','--out-dir','reports/phase8/method-framework-v8'],check=True)
p=out/'diagram.drawio';tree=ET.parse(p);model=tree.getroot().find('diagram/mxGraphModel');model.set('pageWidth',str(int(model.get('pageWidth'))+240))
for c in model.findall('./root/mxCell'):
 if c.get('id')=='__legend':c.set('value','实线：已有来源；虚线：本轮计算与门槛，效果待实测。WOFOST不在五智能体在线团队内。')
tree.write(p,encoding='utf-8',xml_declaration=True)
m=out/'manifest.json';d=json.loads(m.read_text());d['artifacts']['diagram.drawio']=hashlib.sha256(p.read_bytes()).hexdigest();d['native_layout_edits']='Added240px rightpage padding to retain edge labels; replaced generic legend with task-specific verified/planned meaning. No scientific edges changed.';m.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
subprocess.run([sys.executable,str(tool),'render','--diagram',str(p),'--cache-dir',str(R/'cache/phase8-method-render')],check=True)
