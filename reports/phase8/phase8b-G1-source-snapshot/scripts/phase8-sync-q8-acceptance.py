"""Q8-only official TOP transaction under approved Phase8B scope, no legacy changes."""
from pathlib import Path
import hashlib,json,sys
sys.path.insert(0,'/mnt/data/yongan-admin-2/.ai-shared/skills/share-top/scripts')
import top_qa
R=Path(__file__).resolve().parents[1];PRIMARY=Path('/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体');protected={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in PRIMARY.glob('_wiki-methodology/_top/_questions/Q[1-7].md')}
def mutate(proj,change):
 q=proj.questions['Q8'];states=[(a.id,a.state) for a in q.attempts]
 q.done_when='五专职团队的天气土壤DL主模型先过TRAIN/Dev G1，再执行P1一次冻结对比与P2明确回溯外折适配器评价及G3消融；真实C/N账、无未来天气及无向量泄漏；Q8.4图稿与90格压力另待批准'
 gates={'Q8.2':['P1仅1995–2009 TRAIN拟合，Dev2010–2014一次校准；最多两结构','Dev BSS优于气候与同折树、90%盈余覆盖85–95%、排序后悔严格低于树；失败停止G2/G3','TRAIN离线C/N解释、原始64维隔离；P2外折内适配器角色已批'], 'Q8.3':['五专职+非预知分支树、单体逐比特同值、相同三级回退','P1双信息条件；P2明确回溯逐年/地区折内适配，40与4分列','G2对比与G3三组正交消融、零未来天气与实际原生C/N账验证']}
 for a in q.attempts:
  if a.id in gates:a.gates=gates[a.id]
 assert states==[(a.id,a.state) for a in q.attempts]
 change.questions.add('Q8');change.logs.append(('line','approved attempt27 Phase8B Q8-only acceptance synchronization via official transaction; P2 retrospective fold-local roles approved; Q1-Q7 unchanged'));change.result.update(item_id='Q8',approval='continue-ef655327bd618e46.md',ids_states_preserved=True)
result=top_qa.transact(str(R),'phase8b-acceptance-sync',mutate)
for p,digest in protected.items():assert hashlib.sha256(p.read_bytes()).hexdigest()==digest
(R/'reports/phase8/phase8b-q8-acceptance-receipt.json').write_text(json.dumps({'result':result,'Q1_Q7_unchanged':True},ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False))
