"""Publish honest negative screening evidence only if the fourth Dev gate fails."""
import pathlib,json,hashlib,shutil
R=pathlib.Path(__file__).resolve().parents[1]
def main():
 g=json.loads((R/'reports/phase3b-full3-dev-gate-v3-sm.json').read_text());assert not g['dev_gate_passed']
 assert not (R/'reports/phase3b-heldout-unlock.json').exists()
 m=json.loads((R/'reports/phase3b_metrics.json').read_text());s=m['stats']['v3-sm/full3']['pooled']
 screening=(R/'reports/PHASE3B_SCREENING_RESULTS.md').read_text()
 text=f'''# AgroShield-RL第三阶段B验证结果

本阶段尚未通过预先声明的开发集门禁。最新水分观测候选的联合达标率为{s['joint']:.2%}，平均施氮{s['N_kg_ha']:.2f}kg/ha，产量{s['yield_t_ha']:.3f}t/ha，实际违规率{s['executed_violation_rate']:.2%}。完整核查见下表与独立门禁JSON；不能把消除低氮退化或零违规写成超过简单规则的证据。

因此历史1983–2021、压力5500–5998及干旱子集继续锁定，未启动以通过门禁为前提的其余四层训练。任务要求的五层完整消融与最终盲测尚未完成，本报告不填补不存在的结果。

|评估或消融|实际状态|原因|
|---|---|---|
|Full3三种子开发集|四个候选均有独立完整回执|检查点冻结后评估|
|raw / corrected / masked / guided，三种子|未启动|Full3开发门禁尚未全部通过|
|历史39年×三土壤|锁定，未运行|未满足解锁条件|
|压力499年×三土壤|锁定，未运行|未满足解锁条件|
|历史/压力干旱归因|未运行|不提前读取盲测结果|

## 本轮实现

统一发育期窗口0.10/0.32/0.62/0.88，分次累计目标70/130/190，单次0–80kg/ha，允许季节160–210kg/ha。前两次非零剂量由引导固定，学习集中于末次窗口；这是一项明确的搜索限制。终端奖励显式奖励联合达标，惩罚双向边界距离；单乘子和CVaR10仅针对盈余上侧超标。原始每周执行时钟未改，提案动作及其概率进入PPO，安全记录按实际执行动作计算。

最初LAI上限系数与奖励C1由1800训练季节确定；加倍预算仍无增益。训练集原始目标代理核查后另冻C8候选，仍无增益。随后给全部学习层统一扩展已授权的理想化0–20厘米体积水分SM观测，并用150个训练场景重新校准上限。水分只是可部署观测的理想化假设，不是实测传感器；未测试噪声、缺失或传感深度变化。禁止NO3、NH4、NAVAIL、NLOSSL以及未来天气进入策略。

四个候选共12个正式Full3检查点、1002240次PPO交互。它们均从头训练；旧阶段权重没有复用。源文件逐项快照，训练结束和评估前核对。前三候选的参数不同却有相同确定性结果，参数变化审计可排除“权重未更新”解释，但不能据此证明所有实现都无误。

## 验证与证据

- 目标测试52项通过，0失败、0跳过；包括水分读取权限、20厘米层厚、掩码偏移、动作概率一致、梯度非零、保存重载以及完整季节奖励望远镜核查。
- 完整开发数据按500年份、三土壤、三种子配对。置信区间以年份聚类，种子先取均值；多次查看开发集后的检验均属探索性，不能替代盲测。
- 固定规则每种只有1500个场景，不伪造三份随机种子。原生NUE和盈余保留为别名，正式指标按实际执行施氮重算。
- 两次旧模块DeepSeek审查和新增水分模块审查报告分别保留；质量结论以原件及核实记录为准。
- Phase3A原报告、完整JSON与图在reports/phase3a-final归档；Phase2原始证据未覆盖。

## 开发集详细结果

'''+screening.split('\n',1)[1]+'''

## 局限与后续

当前证据只能支持“实现与安全门禁可核验，效果门禁尚未通过”。水分自适应规则的改进必须单独报告，不能归因于GRU或强化学习。小规模训练内响应探针不证明当前观测不可能解决问题；要改变训练方法、增加预算或改变部署观测假设，应另开可验收的实验合同，保留本轮全部负结果。无需为完成表格提前消耗历史和压力盲测。

关键路径：reports/phase3b3-validation.json、reports/phase3b-full3-dev-gate-v3-sm.json、reports/phase3b-metrics-summary.json、reports/phase3b-policy-change-audit.json、reports/phase3b-contract.md；原始模型与评估JSON保留本地，体积较大的权重和季节数据不纳入Git。
'''
 cases=json.loads((R/'reports/phase3b3-dev-attribution.json').read_text())['cases']
 text+='\n## 开发集决策记录\n\n仅为开发集事后最干/最湿季节的可观测状态说明，不是因果特征重要性，也不是历史或压力集归因。\n\n|案例|年份|季节雨量mm|土壤|三种子N kg/ha|末次决策LAI|末次决策SM|末次剂量kg/ha|\n|---|---:|---:|---|---|---:|---:|---:|\n'
 for case in cases:
  p=case['policy_cases'][0];event=p['application_states'][-1]
  text+=f"|{case['case']}|{case['year']}|{case['seasonal_rain_mm']:.1f}|{case['soil']}|{','.join(str(int(z['outcome']['actual_N'])) for z in case['policy_cases'])}|{event['LAI']:.3f}|{event['top20cm_SM']:.3f}|{event['executed']*10:.0f}|\n"
 text+='\n干旱快渗土与湿润默认土中，三种子均为70/60/60，总量190；全部开发场景亦如此，不能据此宣称双向适应。训练上限中145/150场景为210、5/150为200，较宽松而非强自适应。传感通道可以区分状态，但该次学习策略未形成剂量差异。\n'
 text+='\n最终图件：[PNG](../figures/phase3-breakthrough/diagram.png)、[可编辑drawio](../figures/phase3-breakthrough/diagram.drawio)。Gemini Carbon medium实际PNG终检PASS，原始首轮修改意见及最终报告分别在phase3b-figure-review-round1.md与phase3b-figure-review-final.md。完整交付SHA清单见phase3b-artifact-registry.json；最终一致性核验见phase3b-final-validation.json。\n'
 (R/'reports/PHASE3_BREAKTHROUGH_RESULTS.md').write_text(text)
 shutil.copyfile(R/'reports/phase3b_metrics.json',R/'reports/phase3_metrics.json')
 shutil.copyfile(R/'reports/phase3b-metrics-summary.json',R/'reports/phase3-metrics-summary.json')
 print('Canonical negative screening report updated; heldout still locked.')
if __name__=='__main__':main()
