"""Honest dev-only Phase3 aggregation. No historical/stress inputs accepted."""
import json,pathlib,statistics,math,hashlib
import numpy as np
from scipy.stats import wilcoxon
R=pathlib.Path(__file__).resolve().parents[1]

def summarize(rows):
    assert rows and all(5000<=r['year']<=5499 for r in rows)
    def avg(k):return statistics.mean(float(r[k]) for r in rows)
    return dict(n=len(rows),yield_t_ha=avg('yield_t_ha'),N_kg_ha=avg('actual_N'),NUE=avg('NUE_actual'),surplus_kg_ha=avg('surplus_actual'),NUE_compliance=statistics.mean(.5<=r['NUE_actual']<=.9 for r in rows),surplus_compliance=statistics.mean(0<=r['surplus_actual']<=40 for r in rows),joint=avg('joint_actual'),cvar10_surplus=statistics.mean(sorted([r['surplus_actual'] for r in rows],reverse=True)[:max(1,math.ceil(len(rows)*.1))]),proposed_violation_rate=avg('proposed_violation_rate'),executed_violation_rate=avg('executed_violation_rate'),guard_interception_rate=avg('guard_interception_rate'),mask_active_rate=avg('mask_active_rate'))

def comparison(full,reference):
    # Pair by weather year + soil; average seeds before pairing, no repeated controls.
    f={};b={}
    for rows,out in [(full,f),(reference,b)]:
        for r in rows:out.setdefault((r['year'],r['soil']),[]).append(r)
    keys=sorted(set(f)&set(b));rng=np.random.default_rng(20261114);result={}
    for metric in ['joint_actual','yield_t_ha','surplus_actual']:
        dif=np.array([statistics.mean(float(r[metric]) for r in f[k])-statistics.mean(float(r[metric]) for r in b[k]) for k in keys])
        # Cluster bootstrap by year, preserving three soil outcomes within each year.
        years=sorted(set(k[0] for k in keys));byyear=np.array([statistics.mean(dif[i] for i,k in enumerate(keys) if k[0]==y) for y in years])
        boot=np.array([rng.choice(byyear,size=len(byyear),replace=True).mean() for _ in range(3000)])
        result[metric]=dict(pairs=len(keys),year_clusters=len(years),mean_difference=float(dif.mean()),ci95=np.quantile(boot,[.025,.975]).tolist(),wilcoxon_year_mean_p=float(wilcoxon(byyear).pvalue) if np.any(byyear) else 1.)
    return result

def main():
    groups={};sources=[]
    base=R/'reports/phase3-dev-baselines-v1.json'
    if base.exists():
        x=json.loads(base.read_text());sources.append(base)
        for r in x['records']:
            if r['model'] not in ['N1','N3']:groups.setdefault(r['model'],[]).extend(r['episodes'])
    fixed=R/'reports/phase3-dev-baselines-corrected-v1.json'
    if fixed.exists():
        sources.append(fixed)
        for r in json.loads(fixed.read_text())['records']:groups.setdefault(r['model'],[]).extend(r['episodes'])
    strong=R/'reports/phase3-dev-strong-prior-v1.json'
    if strong.exists():
        sources.append(strong)
        for r in json.loads(strong.read_text())['records']:groups.setdefault(r['model'],[]).extend(r['episodes'])
    for file in sorted((R/'reports').glob('phase3-dev-full-v*.json')):
        if '.progress.' in file.name:continue
        sources.append(file);version=file.stem.rsplit('-',1)[-1]
        for r in json.loads(file.read_text())['records']:groups.setdefault('full-'+version,[]).extend(r['episodes'])
    stats={}
    for name,rows in groups.items():
        seeds=sorted(set(r['seed'] for r in rows));byseed={str(s):summarize([r for r in rows if r['seed']==s]) for s in seeds}
        stats[name]=dict(pooled=summarize(rows),seed_mean={k:statistics.mean(v[k] for v in byseed.values()) for k in summarize(rows) if k!='n'},by_seed=byseed,by_soil={s:summarize([r for r in rows if r['soil']==s]) for s in ['default','fast','slow']},seed_std={k:statistics.stdev(x[k] for x in byseed.values()) if len(seeds)>1 else 0. for k in summarize(rows) if k!='n'})
    contrasts={};gates={}
    for name,rows in groups.items():
        if not name.startswith('full-'):continue
        contrasts[name]={b:comparison(rows,groups[b]) for b in ['N2','prior','prior190'] if b in groups}
        s=stats[name]['pooled'];seedstats=stats[name]['by_seed'];required=all(b in groups for b in ['N2','prior'])
        gates[name]=dict(complete_500_years_3_soils_3_seeds=len(rows)==4500,noncollapse=120<=s['N_kg_ha']<=200 and all(40<=v['N_kg_ha']<=250 for v in seedstats.values()),executed_safe=s['executed_violation_rate']==0,minimum_joint_target=s['joint']>=.4,better_than_prior=required and s['joint']>=stats['prior']['pooled']['joint']+.05 and contrasts[name]['prior']['joint_actual']['ci95'][0]>0,better_than_N2=required and s['joint']>=stats['N2']['pooled']['joint']+.05 and contrasts[name]['N2']['joint_actual']['ci95'][0]>0,yield_competitive=required and s['yield_t_ha']>=stats['N2']['pooled']['yield_t_ha']-.4,corrected_comparison_available='corrected' in groups,full_ablation_available=all(m in groups for m in ['raw','corrected','reward','masked','guided']))
        gates[name]['better_than_stronger_prior']=('prior190' in groups and s['joint']>=stats['prior190']['pooled']['joint']+.05 and contrasts[name]['prior190']['joint_actual']['ci95'][0]>0)
        gates[name]['screening_pass']=all(v for k,v in gates[name].items() if k not in ['corrected_comparison_available','full_ablation_available'])
        gates[name]['final_unlock_pass']=all(gates[name].values())
    out=dict(split='dev',heldout_phase3_started=False,stats=stats,comparisons=contrasts,gates=gates,episodes=groups,sources={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},excluded='N1/N3 from baselines-v1 used incorrect schedules and are excluded; corrected-v1 is authoritative.')
    (R/'reports/phase3_metrics.json').write_text(json.dumps(out))
    lines=['# 第三阶段结果：已消除零施肥，未达到突破门禁','','历史与压力集保持锁定。下表只来自5000–5499开发年份；门禁尚未通过时不得宣称帕累托突破。','','|方案|季节数|施氮kg/ha|产量t/ha|NUE|盈余kg/ha|联合达标|实际违规|','|---|---:|---:|---:|---:|---:|---:|---:|']
    for name,x in stats.items():
        s=x['pooled'];lines.append(f"|{name}|{s['n']}|{s['N_kg_ha']:.2f}|{s['yield_t_ha']:.3f}|{s['NUE']:.3f}|{s['surplus_kg_ha']:.2f}|{s['joint']:.1%}|{s['executed_violation_rate']:.2%}|")
    lines+=['','## 门禁实况','', '```json',json.dumps(gates,ensure_ascii=False,indent=2),'```','','按年份聚类进行配对bootstrap（3000次），同年三土壤保持成组；Wilcoxon检验对同年三土壤均值进行，三种子先取均值，避免把确定性对照重复三次。完整数值、土壤分片与种子标准差见phase3_metrics.json。','','N1/N3首批错误日程结果已排除，保留原证据；只有重跑的标准方案用于上述表格。']
    if 'full-v2b' in stats:
        final=stats['full-v2b']['pooled'];strong=stats['prior190']['pooled']
        lines.insert(2,f"第二候选三种子共4500个开发季节：平均施氮{final['N_kg_ha']:.2f} kg/ha、产量{final['yield_t_ha']:.3f} t/ha、联合达标{final['joint']:.2%}，实际违规为0；独立190 kg/ha先验达{strong['joint']:.2%}。本轮开发门禁失败，停止历史/压力审计。\n")
    lines+=['','## 种子与土壤分片','','确定性方案只有一个固定策略；RL结果以三个种子计标准差，不将1500个确定性场景重复为4500个独立对照。','','|RL版本|种子|平均N|平均产量|联合达标|','|---|---:|---:|---:|---:|']
    for n,st in stats.items():
        if not n.startswith('full-'):continue
        for seed,s in st['by_seed'].items():lines.append(f"|{n}|{seed}|{s['N_kg_ha']:.2f}|{s['yield_t_ha']:.3f}|{s['joint']:.1%}|")
    lines+=['','|方案|土壤|平均N|平均产量|联合达标|','|---|---|---:|---:|---:|']
    for n,st in stats.items():
        if n not in ['N2','prior','prior190'] and not n.startswith('full-'):continue
        for soil,s in st['by_soil'].items():lines.append(f"|{n}|{soil}|{s['N_kg_ha']:.2f}|{s['yield_t_ha']:.3f}|{s['joint']:.1%}|")
    lines+=['','## 三种子平均与标准差','','|版本|NUE|盈余kg/ha|最差十分位盈余kg/ha|联合达标|','|---|---:|---:|---:|---:|']
    for n,st in stats.items():
        if not n.startswith('full-'):continue
        m=st['seed_mean'];d=st['seed_std']
        lines.append(f"|{n}|{m['NUE']:.3f} ± {d['NUE']:.3f}|{m['surplus_kg_ha']:.2f} ± {d['surplus_kg_ha']:.2f}|{m['cvar10_surplus']:.2f} ± {d['cvar10_surplus']:.2f}|{m['joint']:.1%} ± {d['joint']:.1%}|")
    lines+=['','## 探索性配对比较','','下表为联合达标率差值（百分点）；同年三土壤作为一组，三种子先平均。开发集参与调参，p值不能替代未触碰盲测的验证。','','|版本|参照|差值|95%区间|Wilcoxon p|','|---|---|---:|---|---:|']
    for n,cs in contrasts.items():
        for b,v in cs.items():
            z=v['joint_actual'];lo,hi=z['ci95'];lines.append(f"|{n}|{b}|{z['mean_difference']*100:.2f}|[{lo*100:.2f}, {hi*100:.2f}]|{z['wilcoxon_year_mean_p']:.3g}|")
    lines+=['','## 实现、审查与未完成项','','两版各三种子、每种子67200实际步，正式学习总计403200步。第二版有三次进度回调失败启动；失败回执及独立冒烟训练保留在phase3-attempt-ledger.json，不算入正式比较。','','44项目标测试通过，包含原32项；没有失败或跳过。DeepSeek Flash/high完成两轮独立代码审查，第二轮无动作概率/执行路径阻断问题，残留口径、窗口和来源覆盖限制见phase3-review-resolution.md。机制与奖励的精确语义见phase3-method-and-limitations.md。','','保留原每周末施肥物理过程。报告提议违规、遮罩活跃率、执行日拦截率及实际违规，不能把系统的零违规解释为未经遮罩策略本身的安全性。当前N3忠实原生60/140/40，其中140事件超过RL九动作域，违规如实保留。','','如果开发门禁失败，本轮按裁定在此收口：不运行历史/压力，不补写未做的Raw/Corrected/Reward/Masked/Guided完整消融，不宣称单模块增益或帕累托突破。单独NUE/盈余双critic及两个乘子尚未实现；当前仍是聚合成本乘子，详见实现边界。','','下一步优先在开发集将先验、阶段窗口与包络逐项对齐，隔离比较奖励、先验强度、预算与双变量节奏；再决定是否值得扩大训练，而不是用弱先验或未见数据制造优势。']
    lines+=['','## 交付与复现','','完整数据：`reports/phase3_metrics.json`（保留本机，SHA登记）；小型摘要：`phase3-metrics-summary.json`；文件校验：`phase3-delivery-validation.json`及`phase3-artifact-registry.json`。源码补丁与完整树重建核验：`phase3-source.patch`、`phase3-source-provenance.json`。','','可编辑总图与实际开发结果：[结果图](../figures/phase3-breakthrough/diagram.png)、[draw.io](../figures/phase3-breakthrough/diagram.drawio)。[冻结决策回放](phase3-attribution-cases.md)展示剂量、DVS、LAI、过去雨量和季节预算；这是状态/约束解释，不是因果特征归因。','','正式命令和退出码保存在`phase3-v1-processes.json`、`phase3-v2b-processes.json`，所有命令先在项目目录`source scripts/env.sh`。新实验必须使用新tag和新输出文件，脚本拒绝覆盖原证据。图渲染采用系统Python与已装Playwright浏览器，不依赖训练虚拟环境。','','检查点环境版本保护已经验证：接受v2b冻结源，拒绝把pre-stage的smoke-d权重放到当前阶段遮罩下评估。对v1缺乏完整启动快照的限制如实保留；完整源码补丁可重建当前目录树，不冒充过去未采集的快照。']
    (R/'reports/PHASE3_BREAKTHROUGH_RESULTS.md').write_text('\n'.join(lines)+'\n')
if __name__=='__main__':main()
