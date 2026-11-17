"""One authorized TOP transaction; ordinary plan operations remain official CLI calls."""
from pathlib import Path
import sys,json,hashlib
sys.path.insert(0,'/mnt/data/yongan-admin-2/.ai-shared/skills/share-top/scripts')
import top_qa
R=Path.cwd();PRIMARY=Path('/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体');protected={p:p.read_bytes() for p in PRIMARY.glob('_wiki-methodology/_top/_questions/Q[1-7].md')};before={}
def mutate(proj,change):
 q=proj.questions['Q8'];before['ids_states']=[(a.id,a.state) for a in q.attempts];before['state']=q.state
 q.done_when='完成64维DL农田代理及离线物理解释、四专职团队工具调用与全季三阶段决策，并在无未来/无隐藏遥测条件下完成荷兰CEA主场及五区公平对比、四维压力与真实C/N账验证；执行须另行批准'
 gates={'Q8.1':['六合一与四专职DL工具图对齐','validate_drawio + plan validate/check + doctor无错误','旧1782+Phase7新增242及Q1–Q7不变、合并清理'], 'Q8.2':['先冻结无同期TRAIN卫星的数据角色及信息边界','时间/地区留出的DL响应误差与校准、离线物理解释','原始64维只进DL后端、无隐藏遥测泄漏、单测'], 'Q8.3':['气象/地理生态/经济政策/农艺四端结构化工具调用','原始64维不进任何智能体、三阶段行动预算与前缀守卫','同DL工具直接优化器及四端消融、单测'], 'Q8.4':['荷兰CEA原设置复现与匹配对照分列、五区四维压力','实际联合达标/部分收益/施氮与原生C/N账及不确定性','图稿重构、外援审查、全测、合并清理']}
 for a in q.attempts:a.gates=gates[a.id]
 assert before['ids_states']==[(a.id,a.state) for a in q.attempts] and q.state==before['state']
 change.questions.add('Q8');change.logs.append(('line','approved epoch25 Q8-only done_when/gates correction via official TOP transaction API; IDs/states and Q1-Q7 unchanged; no scientific execution'));change.result.update(item_id='Q8',approval='continue-58879f6409badf25.md',ids_states_preserved=True)
r=top_qa.transact(str(R),'approved-q8-acceptance-correction',mutate)
for p,b in protected.items():assert p.read_bytes()==b,p
(R/'reports/phase8/q8-acceptance-api-receipt.json').write_text(json.dumps(dict(result=r,ids_states_before=before,Q1_Q7_preserved=True,only_approved_Q8_acceptance_fields_changed=True),ensure_ascii=False,indent=2));print(json.dumps(r,ensure_ascii=False))
