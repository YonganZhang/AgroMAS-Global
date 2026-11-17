"""Canonical hand-in for the explicit Phase3C honesty fallback only."""
import pathlib,json,shutil
R=pathlib.Path(__file__).resolve().parents[1]
if __name__=='__main__':
 gate=json.loads((R/'reports/phase3c-dev-gate-v4-sm.json').read_text());assert not gate['dev_gate_passed'];assert not (R/'reports/phase3b-heldout-unlock.json').exists()
 text=(R/'reports/PHASE3C_DEV_RESULTS.md').read_text();z=gate['comparisons']['utilityprior']['joint_actual']
 header=f"本轮未突破：Full4全部4500个开发场景仍为190kg/ha，联合达标55.13%，显著低于同校准、无PPO的监督评分先验59.40%（差{100*z['mean_difference']:.2f}个百分点，95%CI[{100*z['ci95'][0]:.2f},{100*z['ci95'][1]:.2f}]，p={z['wilcoxon_year_mean_p']:.6g}）。对原prior190的+0.40个百分点亦未通过显著性门禁。按任务的诚实回退要求停止新增实验，历史与压力保持锁定。\n\n"
 text=text.split('\n',1)[0]+'\n\n'+header+text.split('\n',1)[1]
 text=text.replace('按门禁条件执行；本阶段未填入结果','门禁失败，12个剩余训练未启动')
 text+='\n## 开发集决策记录\n\n同一套已记录决策，无新仿真。最干快渗土案例5194年、季节雨量305.2mm；最湿默认土案例5005年、801.7mm，仅在开发集内按天气选择，与结果无关。不是因果特征重要性，也不是盲测归因。\n\n|开发案例|土壤|三种子Full4总N|评分先验总N|prior190总N|N2总N|\n|---|---|---|---:|---:|---:|\n'
 x=json.loads((R/'reports/phase3c-dev-attribution.json').read_text())
 for case in x['cases']:
  dose=','.join(str(int(case['Full4'][str(s)]['outcome']['actual_N'])) for s in [4,17,29]);c=case['controls'];text+=f"|{case['label']} {case['year']}|{case['soil']}|{dose}|{c['utilityprior']['actual_N']:.0f}|{c['prior190']['actual_N']:.0f}|{c['N2-PA']['actual_N']:.0f}|\n"
 text+='\n评分先验分别选择160与200，Full4两例均70/60/60。三个种子完整开发物理结果相同，联合达标均55.13%，种子间标准差0；这不代表年份不确定性为0，检验仍按500年份聚类。动作头权重确实发生变化，L2变化约0.889、1.057、0.864，不能把恒定输出解释为训练未运行；也不能凭此确认某个唯一病因。\n'
 text+='\n## 交付与验证\n\n60项测试全部通过（0失败、0跳过）。独立DeepSeek Flash/high认可核心更新与先验数学，门禁及来源意见的逐项核实见phase3c-review-resolution.md；其旧标签与冻结一次先验两项陈述被相同SHA的源码证据否定，原报告完整保留。实际3个最终检查点、169项启动依赖和全部超参数另经加载核验。早期smoke是旧元数据版本，不冒充最终源码证书。\n\n[最终PNG](../figures/phase3-breakthrough/diagram.png)、[可编辑drawio](../figures/phase3-breakthrough/diagram.drawio)。实际PNG交由Gemini Carbon medium质检，结论见phase3c-figure-review.md。\n\n主要核验：phase3c-validation.json、phase3c-contract-audit.json、phase3c-artifact-registry.json、phase3c-source-reconstruction.json。复核命令：先source scripts/env.sh，再运行python scripts/phase3c-validate.py及python scripts/phase3c-contract-audit.py；它们只读冻结科学结果，不运行盲测或改模型。完整本地JSON与压缩权重保留并登记SHA，大体积原始文件按项目规则不入Git。\n'
 (R/'reports/PHASE3_BREAKTHROUGH_RESULTS.md').write_text(text)
 shutil.copyfile(R/'reports/phase3c_metrics.json',R/'reports/phase3_metrics.json');shutil.copyfile(R/'reports/phase3c-metrics-summary.json',R/'reports/phase3-metrics-summary.json')
 print('Negative fallback report and canonical metrics updated; heldout locked.')
