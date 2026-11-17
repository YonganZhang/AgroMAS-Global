"""Dev-only v4 evidence; no fabricated ablation or heldout rows."""
import pathlib,json,hashlib,statistics,math
from importlib.machinery import SourceFileLoader
R=pathlib.Path(__file__).resolve().parents[1]
old=SourceFileLoader('c_statistics',str(R/'scripts/phase3-report.py')).load_module()
b=SourceFileLoader('c_summary',str(R/'scripts/phase3b-report.py')).load_module()
def main():
 sources={};groups={}
 for name in ['phase3b-dev-controls-v3.json','phase3b3-dev-moisture-controls-audited-v3-sm.json','phase3c-dev-utilityprior-v4-sm.json','phase3c-dev-full4-v4-sm.json']:
  p=R/'reports'/name;x=json.loads(p.read_text());assert x['status']=='completed';sources[str(p.relative_to(R))]=hashlib.sha256(p.read_bytes()).hexdigest()
  for rec in x['records']:
   key=rec['model']
   if name.startswith('phase3b3'):key='old_SM-'+key
   if key in groups and key=='corridorprior':continue
   groups.setdefault(key,[]).extend(rec['episodes'])
 # Keep one complete matched v4 fixed corridor cohort, not a single50year chunk.
 controls=json.loads((R/'reports/phase3c-dev-utilityprior-v4-sm.json').read_text())['records'];groups['corridorprior']=[e for rec in controls if rec['model']=='corridorprior' for e in rec['episodes']]
 stats={n:dict(pooled=b.summary(rows),by_seed={str(seed):b.summary([r for r in rows if r['seed']==seed]) for seed in sorted({r['seed'] for r in rows})},by_soil={soil:b.summary([r for r in rows if r['soil']==soil]) for soil in ['default','fast','slow']}) for n,rows in groups.items()}
 gate=json.loads((R/'reports/phase3c-dev-gate-v4-sm.json').read_text());comparisons=gate['comparisons'];utility_comparisons={n:old.comparison(groups['utilityprior'],groups[n]) for n in ['N2-PA','prior160','prior190','old_SM-adaptiveprior']};result=dict(stats=stats,episodes=groups,comparisons=comparisons,utility_comparisons=utility_comparisons,gate=gate,sources=sources,historical_started=False,stress_started=False)
 (R/'reports/phase3c_metrics.json').write_text(json.dumps(result));compact={k:v for k,v in result.items() if k!='episodes'};compact['full_metrics_sha256']=hashlib.sha256((R/'reports/phase3c_metrics.json').read_bytes()).hexdigest();(R/'reports/phase3c-metrics-summary.json').write_text(json.dumps(compact,indent=2))
 s=stats['full4']['pooled'];lines=['# AgroShield-RL第四版开发集验证','',f"开发门禁通过：{gate['dev_gate_passed']}。Full4联合达标{s['joint']:.2%}，产量{s['yield_t_ha']:.3f}t/ha，平均N{s['N_kg_ha']:.2f}kg/ha。",'','|方案|季节数|产量t/ha|N kg/ha|联合达标|盈余kg/ha|最差十分位盈余|提案违规|实际违规|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
 for n,st in stats.items():
  t=st['pooled'];lines.append(f"|{n}|{t['n']}|{t['yield_t_ha']:.3f}|{t['N_kg_ha']:.2f}|{t['joint']:.2%}|{t['surplus_kg_ha']:.2f}|{t['cvar10_surplus']:.2f}|{t['proposed_violation_rate']:.2%}|{t['executed_violation_rate']:.2%}|")
 lines+=['','|Full4参照|联合达标差pp|年份聚类95%CI pp|Wilcoxon p|','|---|---:|---|---:|']
 for n,c in comparisons.items():
  z=c['joint_actual'];lines.append(f"|{n}|{100*z['mean_difference']:.2f}|[{100*z['ci95'][0]:.2f},{100*z['ci95'][1]:.2f}]|{z['wilcoxon_year_mean_p']:.4g}|")
 lines+=['','## 冻结评分先验的独立结果','','下列只属于同校准监督评分先验，不属于强化学习增益。','','|UtilityPrior参照|联合达标差pp|年份聚类95%CI pp|Wilcoxon p|','|---|---:|---|---:|']
 for n,c in utility_comparisons.items():
  z=c['joint_actual'];lines.append(f"|{n}|{100*z['mean_difference']:.2f}|[{100*z['ci95'][0]:.2f},{100*z['ci95'][1]:.2f}]|{z['wilcoxon_year_mean_p']:.4g}|")
 lines+=['','## 实现与数据边界','','策略、熵与KL只在掩码允许多个动作的决策步上取均值；优势矩在整个rollout的有效决策步上计算，价值与成本价值仍训练全部转移。默认开关关闭，旧算法未被静默替换。gamma=1、lambda=1、奖励不使用运行归一化；完整终止轨迹取消中间价值误差，但滚动窗口尾端仍可自举。不能把这一改动说成已数学证明恒定190的唯一原因。旧回执有效决策比例8.07%，而非1/39。','','运行时先检查首层土壤深度为20厘米，再读取理想化无噪声SM；没有NO3、NH4、NAVAIL或NLOSSL输入策略。终端NUE与盈余仍是训练反馈，不能混淆为传感器输入。所有学习层共享11个物理/记账通道，掩码另附9位。','','120个训练年份×3土壤×6档剂量=2160个完整剂量结果；900个旧训练结果有SHA来源，另模拟1260个。五折按训练年份分组选出64棵深度5的ExtraTrees评分先验；固定初始土壤校准与随机土壤初始化PPO训练不同，这仍是局限。相同冻结评分先验、不加PPO的UtilityPrior必须单列。它是训练过的监督评分模型，不是无学习的固定农艺常数。','','引导方案先固定70/60，末次由策略选择，最多3次非零施肥；季节上限固定210。状态适应来自评分先验与残差，而不是上限变化。评分通过比较六档效用选择动作，不对连续剂量向上取整。','', 'PPO交互预算相同不等于全部数据或计算量相同：指导与完整方案另用了2160个监督校准季节；冻结森林的存储与计算复杂度也必须计入，不能只凭4908个可训练参数宣称总容量相同。','','最初正式标签v4-sm在任何Full4开发评估之前因门禁对照筛选错误中断；中断快照、日志和不完整回执均保留。修正仅涉及评估参照的筛选，训练配置未变；三种子正式结果使用新标签v4-sm-final。','','## 剩余工作','','若门禁失败，按任务中的诚实回退要求立即结束本轮实验；raw/corrected/masked/guided三种子的完整消融及历史1983–2021、压力5500–5998、干旱子集均未运行。没有补写空缺结果或降低阈值。若门禁通过，本脚本的仅开发集阶段报告须在冻结15个检查点并完成单次盲测后另行扩充。','','|项目|本报告状态|','|---|---|','|Full4三种子开发集|已完成|','|其余四层正式消融|按门禁条件执行；本阶段未填入结果|','|历史与压力|本阶段锁定|','|干旱盲测与归因|本阶段未运行|','','60项目标与集成测试、训练回执、源码逐项SHA、评分校准文件及门禁JSON为验证入口。DeepSeek和Gemini原始审查报告另存。Phase3B原报告、完整数据及图件在reports/phase3b-final归档，Phase3A与Phase2证据保留。']
 (R/'reports/PHASE3C_DEV_RESULTS.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
