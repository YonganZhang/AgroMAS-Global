"""Versioned v3 screening report; never invents locked historical/stress outcomes."""
import pathlib,json,statistics,math,hashlib,argparse
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1]
old=SourceFileLoader('phase3b_report_stats',str(R/'scripts/phase3-report.py')).load_module()
def summary(rows):
 def mean(k):return statistics.mean(float(r[k]) for r in rows)
 return dict(n=len(rows),yield_t_ha=mean('yield_t_ha'),N_kg_ha=mean('actual_N'),NUE=mean('NUE_actual'),surplus_kg_ha=mean('surplus_actual'),NUE_compliance=statistics.mean(.5<=r['NUE_actual']<=.9 for r in rows),surplus_compliance=statistics.mean(0<=r['surplus_actual']<=40 for r in rows),joint=mean('joint_actual'),cvar10_surplus=statistics.mean(sorted([r['surplus_actual'] for r in rows],reverse=True)[:max(1,math.ceil(len(rows)*.1))]),proposed_violation_rate=mean('proposed_violation_rate'),executed_violation_rate=mean('executed_violation_rate'),guard_interception_rate=mean('guard_interception_rate'))
def main():
 groups={};sources={}
 files=[R/'reports/phase3b-dev-controls-v3.json']+sorted((R/'reports').glob('phase3b-dev-full3-v3*.json'))+sorted((R/'reports').glob('phase3b-dev-ablations-*.json'))+sorted((R/'reports').glob('phase3b2-dev-full3-*.json'))+sorted((R/'reports').glob('phase3b3-dev-full3-*.json'))+[R/'reports/phase3b3-dev-moisture-controls-audited-v3-sm.json']
 for p in files:
  if not p.exists() or '.progress.' in p.name:continue
  x=json.loads(p.read_text());assert x['status']=='completed';sources[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
  tag='v3-sm' if 'v3-sm' in p.name else 'v3-c8' if 'v3-c8' in p.name else 'v3-long' if 'v3-long' in p.name else 'v3'
  for rec in x['records']:
   name=tag+'/'+rec['model'] if rec['model'] in ['raw','corrected','masked','guided','full3'] else ('SM-'+rec['model'] if 'moisture-controls' in p.name else rec['model'])
   groups.setdefault(name,[]).extend(rec['episodes'])
 stats={}
 for name,rows in groups.items():
  assert all(5000<=r['year']<=5499 for r in rows)
  byseed={str(s):summary([r for r in rows if r['seed']==s]) for s in sorted(set(r['seed'] for r in rows))}
  stats[name]=dict(pooled=summary(rows),by_seed=byseed,by_soil={s:summary([r for r in rows if r['soil']==s]) for s in ['default','fast','slow']},seed_std={k:statistics.stdev(v[k] for v in byseed.values()) if len(byseed)>1 else 0. for k in summary(rows) if k!='n'})
 comparisons={n:{b:old.comparison(rows,groups[b]) for b in ['N2-PA','prior160','prior190','corridorprior','adaptiveprior','SM-corridorprior','SM-adaptiveprior'] if b in groups} for n,rows in groups.items() if n.endswith('/full3')}
 gates={p.stem:json.loads(p.read_text()) for p in (R/'reports').glob('phase3b-full3-dev-gate-*.json')}
 result=dict(stats=stats,comparisons=comparisons,gates=gates,sources=sources,episodes=groups,historical_started=False,stress_started=False,all_checkpoints_frozen=False)
 (R/'reports/phase3b_metrics.json').write_text(json.dumps(result))
 compact={k:v for k,v in result.items() if k!='episodes'};compact['full_metrics_sha256']=hashlib.sha256((R/'reports/phase3b_metrics.json').read_bytes()).hexdigest();(R/'reports/phase3b-metrics-summary.json').write_text(json.dumps(compact,indent=2))
 lines=['# 第三阶段B开发集验证','','数据只来自开发集5000–5499。训练校准参数冻结；历史和压力集尚未解锁。','','|方案|季节数|N kg/ha|产量t/ha|NUE|盈余kg/ha|联合达标|最差十分位盈余|实际违规|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
 for n,x in stats.items():
  s=x['pooled'];lines.append(f"|{n}|{s['n']}|{s['N_kg_ha']:.2f}|{s['yield_t_ha']:.3f}|{s['NUE']:.3f}|{s['surplus_kg_ha']:.2f}|{s['joint']:.2%}|{s['cvar10_surplus']:.2f}|{s['executed_violation_rate']:.2%}|")
 lines+=['','## 配对开发差异','','按年份聚类，三土壤保留为同组；三个随机种子先取均值。下表为联合达标率差值的百分点与95%区间，开发集检验均为探索性。','','|候选|参照|差值pp|95%区间pp|Wilcoxon p|','|---|---|---:|---|---:|']
 for n,cs in comparisons.items():
  for b,c in cs.items():
   z=c['joint_actual'];lo,hi=z['ci95'];lines.append(f"|{n}|{b}|{100*z['mean_difference']:.2f}|[{100*lo:.2f}, {100*hi:.2f}]|{z['wilcoxon_year_mean_p']:.3g}|")
 lines+=['','## 候选演变','','C1短训、C1加倍预算和C8短训均保留独立检查点。前三组共9个正式检查点、800640步，开发结果完全一致，联合达标54.38%，未超过prior190的54.73%。权重确实更新；不能把同结果归因于训练未运行。C8来自训练集原始目标代理的尺度核查，不是开发集选系数。','','v3-sm给全部五个学习方案统一增加0–20厘米体积水分观测。只读取SM，不读取NO3、NH4、NAVAIL或NLOSSL。该通道是假设无噪声的可测量状态，尚未代表真实传感器部署。上限用150个训练场景的LAI、SM、SM平方和近期雨量拟合；拟合误差13.57kg/ha为训练内误差。增加观测、重复查看开发集后形成的新候选属于探索性开发，不能把开发检验当作最终盲测。','','## 实施与边界','','统一窗口 .10/.32/.62/.88；引导前两次非零剂量70/60，最后一窗允许30–80kg，使160–210的季节总量可在三次内达到。早期引导属于搜索限制，不把它称为自主学习。独立CorridorPrior采用相同窗口、上限与固定190目标；AdaptivePrior采用拟合的最优量点预测，不加20kg上界安全余量，不能把两种先验混为一谈。','','终端奖励包括联合达标奖励和双向边界距离；拉格朗日只处理盈余上侧及超标尾部风险。均为训练终端反馈，不进入策略输入。运行依赖逐项在启动时快照、结束与评估前核对，原每周末施肥时钟未改。','','训练校准1800季，其中50/110分次的90个200/210请求实际只执行190；原始请求与实际数值全部保留。拟合仅使用70/130下可完整执行的剂量，未使用开发集调校系数。','','旧阶段报告、完整JSON与图已在phase3a-final归档，原始检查点和评估回执保留原位。没有补写未做的消融或盲测。']
 (R/'reports/PHASE3B_SCREENING_RESULTS.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
