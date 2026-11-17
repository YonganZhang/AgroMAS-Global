import pathlib,json,statistics,subprocess,hashlib,xml.etree.ElementTree as ET,math
R=pathlib.Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text())
def git(p):return subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip()
def test_result(p):
 root=ET.parse(R/p).getroot();xs=list(root.iter('testsuite'))
 return {k:sum(int(x.get(k,0)) for x in xs) for k in ['tests','failures','errors','skipped']}|{'receipt':p}
files=sorted((R/'reports/phase2-evaluations-v3').glob('*-seed*.json'));ev=[json.loads(p.read_text()) for p in files]
assert len(ev)==48,len(ev)
for e in ev:
 assert len(e['episodes'])==538 and len(set(x['year'] for x in e['episodes']))==538
 for x in e['episodes']:
  for k in ['yield_t_ha','NUE','N_surplus_kg_ha','fertilization_kg_ha','N_loss_kg_ha','profit_kEUR_ha']:assert math.isfinite(x[k])
models=['N2-PA','raw','corrected','shield','recurrent','full'];soils=['default','fast','slow']
old_n2=read('reports/deterministic-baselines.json')['policies']['N2-PA']['episodes']
new_n2=next(e for e in ev if e['model']=='N2-PA' and e['soil']=='default')['episodes'][:39]
assert all(a['year']==b['year'] and abs(a['yield_t_ha']-b['yield_t_ha'])<1e-9 for a,b in zip(old_n2,new_n2)), 'N2 native-rule reproduction mismatch'


def aggregate(ds):
 if not ds:return None
 if isinstance(ds[0],dict):
  return {k:aggregate([x[k] for x in ds]) for k in ds[0]}
 if isinstance(ds[0],(float,int)):
  return {'mean_across_seeds':statistics.mean(ds),'std_across_seeds':statistics.stdev(ds) if len(ds)>1 else 0.,'per_seed':ds}
 return ds

tables={m:{soil:{split:{sl:aggregate([e['summaries'][split][sl] for e in ev if e['model']==m and e['soil']==soil]) for sl in ['all','drought','extreme']} for split in ['historical','stress']} for soil in soils} for m in models}
process=read('reports/phase2-training-processes-v2.json'); original_process=read('reports/phase2-training-processes.json')
assert len(process['runs'])==15 and all(x['exit_code']==0 for x in process['runs'])
receipts=[read(f'reports/phase2-runs/matched-v2-{m}-seed{s}-env16/receipt.json') for m in models[1:] for s in [4,17,29]]
assert {x['actual_steps'] for x in receipts}=={32768}
assert all(x['parameters_changed'] and x['finite_parameters'] for x in receipts)
assert all(set(x['observed_training_years']).issubset(set(range(3002,5000))) for x in receipts)
assert all(x['initialized_from_scratch'] and not x['phase1_weights_used'] for x in receipts)
for e in ev:
 if e['model'] in ['shield','recurrent','full']:
  assert all(x['executed_violation_rate']==0 for x in e['episodes'])
trajectories=[t for e in ev for t in e['trajectories']]
shield_example=read('reports/phase2-shield-attribution-example.json')
full_rows=[x for e in ev if e['model']=='full' for x in e['episodes']]
assert all(x['actual_executed_fertilization_kg_ha']==0 for x in full_rows)
assert all(x[f'{kind}_action_domain_violation_rate']==0 for e in ev for x in e['episodes'] for kind in ['proposed','executed'])
metrics=dict(status='completed_short_budget',paper_scale_replication=False,git_commits={'project':git(R),'NUE_PCSE-Gym':git(R/'NUE_PCSE-Gym'),'pcse':git(R/'pcse')},
 test_verification={'target':test_result('reports/phase2-target-tests-acceptance.xml'),'legacy':test_result('reports/phase2-legacy-tests-postcommit.xml')},
 evaluation_configuration={'workers':96,'light_info':True,'native_trajectory_parity_tests':'reports/phase2-target-tests-acceptance.xml','existing_results_overwrite':False,'checkpoint_sha_check':'before and after each task'},
 training_protocol={'years':{'train':[3002,4999],'dev_unused':[5000,5499],'stress':[5500,5998],'historical':[1983,2021]},'seed_list':[4,17,29],'budget_each':32768,'training_total_steps':sum(x['actual_steps'] for x in receipts),'from_scratch':True,'E3B':False,'observation':'DVS/LAI + past 7d weather + executed history; no soil truth','no_hyperparameter_search':True,'training_soil':'default','cross_soil':'zero-shot','cvar_alpha':.25,'cvar_scope':'rolling previous-training-episode VaR threshold and terminal tail cost shaping surrogate; no hard CVaR guarantee'},
 training_timing=read('reports/phase2-training-timing.json'),evaluation_timing=read('reports/phase2-evaluation-timing.json'),tail_activation=read('reports/phase2-tail-activation.json'),evaluation_restart=read('reports/phase2-evaluation-throughput-restart.json'),training_runs=receipts,training_processes=process,initial_training_processes=original_process,preaudit_stops=[read('reports/phase2-preaudit-stop.json'),read('reports/phase2-terminal-guard-stop.json')],preaudit_extra_runs=[json.loads(p.read_text()) for p in (R/'reports/phase2-runs').glob('*/receipt.json') if not p.parent.name.startswith('matched-v2-')],weather_definition=read('reports/phase2-weather-slices.json'),frozen_checkpoints=read('reports/phase2-frozen-checkpoints.json'),
 tables=tables,evaluation_episodes_total=sum(len(e['episodes']) for e in ev),evaluation_records=ev,sample_attribution=trajectories,shield_only_attribution_example=shield_example,observed_failure={'full_deterministic_zero_N_episodes':len(full_rows),'full_method_effectiveness_validated':False},
 limitations=['32768 steps per run, versus requested aspirational300000 and original3000000; 3 seeds retained with exact matched interaction budgets','Raw comparison preserves original constraint/buffer behavior but uses common observable inputs, compact network and no E3B; not full published configuration','Four-frame truncated causal GRU with10 observable features, not full-season recurrent PPO or calibrated soil-N estimation','CVaR terminal shaping proxy with rolling thresholds, not risk upper-bound guarantee','Legacy upstream9 failures retained and disclosed','Simulation-only; three soil presets at one location, no real field or external cohort validation','Closed DVS endpoints follow the explicit task and are a fourth difference from strict raw endpoints; constant budget sentinel means9 informative fields among10 inputs','Training-only precipitation thresholds identify only1 historical drought/extreme year; historical tail summaries are single-case values, not interannual stability evidence','No dev hyperparameter selection was performed; poor test outcomes do not authorize retuning on historical/stress benchmark'])
(R/'reports/phase2_metrics.json').write_text(json.dumps(metrics,indent=2,allow_nan=False))
labels={'N2-PA':'N2-PA','raw':'Raw-LagPPO（共同可观测输入）','corrected':'Corrected-LagPPO','shield':'+Shield','recurrent':'+Shield+GRU','full':'AgroShield-RL Full'}
def val(x,d=3):return f"{x['mean_across_seeds']:.{d}f}±{x['std_across_seeds']:.{d}f}"
def pm(m,k):
 d=tables[m]['default']['historical']['all'];return val(d['mean'][k])+' / '+val(d['median'][k])
text=['# 第二阶段实验结果：AgroShield-RL', '', f"已完成约束修正、三个模块、15组同预算短训与{metrics['evaluation_episodes_total']:,}次独立季节评估。所有正式训练进程退出0；目标测试{metrics['test_verification']['target']['tests']}项、0失败。训练规模为32,768步×3种子×5方案，低于任务建议的30万步；结果仅用于验证实现与初步对比，不构成论文尺度复现或优越性证明。", '', '## 约束修正与测试', '', 'Raw模式保留原始函数及缓冲区语义。闭区间DVS端点按本轮任务明确要求执行，与raw严格边界构成额外语义差异，不能把全部对照差异只归因于三个公式。Corrected模式去掉NUE!=0造成的误罚，盈余下界修正为闭区间0，恢复两周间隔罚项；终止信号按每个环境真实done设置。还修正逐环境reset、跨rollout记账、动作前计数与上次施肥时间，避免数学修正被错误状态覆盖。完整季成本跨rollout累计，Lagrange只使用真正完成的季节；物候在原模拟器实际施肥日、发送施肥信号前检查，安全方案按实际执行动作同步奖励与施氮记账。NUE=.70且surplus=20与surplus=0/40合法，NUE=0在终止时不合法；7天违规、14天合法。', '',f"目标套件32项通过、0失败、0错误、0跳过；[验证回执](phase2-target-tests-acceptance.xml)。旧套件完整运行19项通过、9项失败；[原始回执](phase2-legacy-tests-postcommit.xml)。没有删除或放宽原断言。默认pytest.ini仅收集tests/target；显式命令仍可运行全部旧测试。", '', '## 实现位置与边界', '', '- 安全投影：`pcse_gym/envs/constraints.py::AgronomicShield`，继承ActionConstrainer；限制0–80kg/ha、最多4次、间隔14天、DVS闭区间[.01,1]与可选预算。主实验季节预算关闭；同时记录建议与执行违规率。', '- 历史估计：`pcse_gym/envs/observable.py::ObservableHistory/CausalGRUExtractor`；固定10项可观测特征、四帧因果GRU、每环境reset清空。由`initialize_env`只请求DVS/LAI，作为sb3观测适配层的组合扩展；未侵入原sb3.py默认观测。8维隐藏状态没有土氮浓度物理单位。', '- 约束成本与尾风险：`pcse_gym/agent/ppo_mod.py::LagrangianPPO.collect_rollouts/RolloutBufferSteps`。full使用α=.25，以之前最多256个训练季的经验75分位阈值，对超阈值季末风险追加risk/α成本，经成本GAE和原生Lagrange更新；完整季节成本跨rollout保留。是CVaR加权代理，没有实现严格风险上界。', '- 只读解释：`pcse_gym/utils/attribution.py::explain_decision`，冻结输入后输出JSON和符号说明；可选formatter仅收深拷贝，不能改变执行动作。', '', '详见[实现契约](../docs/phase2-implementation.md)与[可编辑方法图](../figures/phase2-execution-day-verified/diagram.drawio)，[PNG预览](../figures/phase2-execution-day-verified/diagram.png)。', '', '## 训练、退出与防泄漏', '', '正式实验采用16环境/组、3个种子任务并行，128步rollout、batch256、10epochs、lr=.001、gamma1、GAE=.95；所有方案不使用E3B。Raw名称专指原始约束与缓冲区语义，输入和网络采用本轮共同受控配置，不是原论文全部超参数。首轮先导实现被独立审查指出季节成本截断与施肥时点问题，已停止并保留全部证据。轻量评估日志路径通过有/无安全层整季逐步精确相等测试，训练路径未启用该开关。最终表仅含matched-v2的15组从头重训；全部先导、替换与中断任务另列JSON，不混入比较预算。参数量当前帧4587，GRU4875（+6.28%）。', '', '训练仅合成收获年3002–4999；开发5000–5499保留未使用。全部最终检查点冻结后才评估历史1983–2021与压力5500–5998，无历史/压力选模或参数调整。训练随机初始氮，评估固定各土壤站点初值，属于显式分布变化。三种土壤均在default训练，fast和slow为零样本；slow映射源码slo。天气阈值只由训练季上年10月至当年7月累计降水决定。', '', '|方案|种子|实际步数|学习秒数|步/秒|进程退出|', '|---|---:|---:|---:|---:|---:|']
full_hist=tables['full']['default']['historical']['all'];n2_hist=tables['N2-PA']['default']['historical']['all']
text.insert(2, f"**主要结论：方法效果未达标。** Full在全部{len(full_rows):,}个确定性评估季节均执行零施肥；历史平均产量{full_hist['mean']['yield_t_ha']['mean_across_seeds']:.3f} t/ha，对照N2为{n2_hist['mean']['yield_t_ha']['mean_across_seeds']:.3f} t/ha，降幅{(1-full_hist['mean']['yield_t_ha']['mean_across_seeds']/n2_hist['mean']['yield_t_ha']['mean_across_seeds'])*100:.1f}%；历史联合合规率为0。Raw、Corrected与GRU消融同样出现确定性零施肥，不能把共同退化单独归因于CVaR。仅安全层消融的建议违规率仍高，而投影后执行违规率为0，证明规则过滤有效，不能据此声称策略学会合理施肥。")
text.insert(3,'')
for r in receipts:
 p=next(x for x in process['runs'] if x['model']==r['model'] and x['seed']==r['seed'])
 text.append(f"|{labels[r['model']]}|{r['seed']}|{r['actual_steps']}|{r['learn_seconds']:.1f}|{r['steps_per_second']:.1f}|{p['exit_code']}|")
timing=read('reports/phase2-evaluation-timing.json')
text+=['', f"主比较训练窗口（含其间重启）{timing['main_training_campaign_seconds_including_restarts']/60:.1f}分钟；最终96分片评估{timing['final_evaluation_sharded_seconds']/60:.1f}分钟；首次48进程评估在吞吐调整前另运行{timing['first_evaluation_attempt_seconds_before_parallelism_restart']/60:.1f}分钟。额外先导已知完成{timing['additional_pilot_known_completed_steps']:,}步，另有{timing['additional_pilot_directories_with_unknown_exact_steps']}个目录精确步数未知，均不混入491,520步主比较预算。", '', '各组finally显式close VecEnv。短吞吐探测8/16环境约91.5/137.9步/秒，均真实退出0；探测有并行负载，不能视为独占基准。前一轮因审查主动终止的任务收到SIGTERM并作为中止证据保留；主表只含v2的正常退出记录。第一阶段143退出的历史记录保留，未证明其原始原因；本轮独立入口的15次退出0证明当前流程正常收尾。', '', '## 表1：历史39年', '', '主表NUE、盈余与利润沿用原生季节指标以保留基线口径；JSON同时记录actual_executed_fertilization_kg_ha与native_logged_fertilization_kg_ha。未启用安全层时，若作物提前结束导致计划动作未发送，旧原生账本可能仍计入建议剂量，故不能把口径差异视为算法改善。安全层方案已同步实际记账。单元格为“跨年均值的跨种子均值±种子样本标准差 / 跨年中位数的跨种子均值±种子样本标准差”。N2为确定性单次，无种子不确定性估计。', '', '|方案|产量t/ha|NUE|盈余kg/ha|日志施氮kg/ha|执行施氮kg/ha|氮损失kg/ha|利润kEUR/ha|', '|---|---|---|---|---|---|---|---|']
for m in models:text.append('|'+labels[m]+'|'+'|'.join(pm(m,k) for k in ['yield_t_ha','NUE','N_surplus_kg_ha','fertilization_kg_ha','actual_executed_fertilization_kg_ha','N_loss_kg_ha','profit_kEUR_ha'])+'|')
text+=['', '违规率为每季逐步违规比例，再跨季/种子平均；联合合规为季末NUE[.5,.9]且盈余[0,40]。建议/执行分开统计，不能把过滤后的安全归功于原策略。所有方案的物候违规以实际施肥日DVS为准；第一阶段曾按日志动作日期（周初）评估物候，不能直接混用两阶段物候率。', '', '|方案|联合合规比例|建议违规率|执行违规率|建议次数/间隔/物候违规率|执行次数/间隔/物候违规率|','|---|---|---|---|---|---|']
for m in models:
 d=tables[m]['default']['historical']['all'];text.append('|'+labels[m]+'|'+val(d['joint_satisfied_rate'])+'|'+val(d['proposed_violation_rate'])+'|'+val(d['executed_violation_rate'])+'|'+'/'.join(val(d[f'proposed_{c}_violation_rate']) for c in ['application_frequency','minimum_spacing','phenology_window'])+'|'+'/'.join(val(d[f'executed_{c}_violation_rate']) for c in ['application_frequency','minimum_spacing','phenology_window'])+'|')
text+=['','另按实际发送的施肥量重算NUE/盈余与联合合规（只替换投入量，沉降和种子氮口径不变；利润仍保留原生经济账本）。规则见[指标契约](../docs/phase2-metrics-contract.md)。','','|方案|执行口径NUE均值|执行口径盈余均值|执行口径联合合规|','|---|---|---|---|']
for m in models:
 d=tables[m]['default']['historical']['all'];text.append('|'+labels[m]+'|'+val(d['mean']['NUE_actual_execution'])+'|'+val(d['mean']['N_surplus_actual_execution_kg_ha'])+'|'+val(d['joint_actual_execution_rate'])+'|')
text+=['','全部25,824季的建议/执行动作域违规率均为0，完整分年值保留在JSON。','', '## 表2：跨土壤与干旱尾风险', '', f"训练降水阈值：q25={metrics['weather_definition']['q25_rain_mm']:.4f}mm，q10={metrics['weather_definition']['q10_rain_mm']:.4f}mm。各方案/土壤均评估历史39年和全部压力499年，未抽取有利年份。固定阈值仅识别1个历史干旱/极端年，压力集干旱137年、极端52年；历史切片CVaR退化为单年值，不能据此宣称跨干旱年份稳定性。最差四分位按指标各自不利方向排序，yield/NUE/合规取低尾、盈余/损失取高尾，ceil(.25n)；因此它不是一组统一最坏年份。NUE高于.9同样违规，低尾NUE不能单独代表安全性。", '', '|方案|土壤|压力499年产量|压力联合合规|压力产量CVaR25|压力NUE CVaR25|压力合规CVaR25|压力盈余CVaR25|历史干旱产量|压力干旱产量|', '|---|---|---|---|---|---|---|---|---|---|']
for m in models:
 for soil in soils:
  d=tables[m][soil]['stress']['all'];h=tables[m][soil]['historical']['drought'];dr=tables[m][soil]['stress']['drought']
  text.append('|'+labels[m]+'|'+soil+'|'+val(d['mean']['yield_t_ha'])+'|'+val(d['joint_satisfied_rate'])+'|'+val(d['cvar25']['yield_t_ha'])+'|'+val(d['cvar25']['NUE'])+'|'+val(d['cvar25']['joint_satisfied'])+'|'+val(d['cvar25']['N_surplus_kg_ha'])+'|'+val(h['mean']['yield_t_ha'])+'|'+val(dr['mean']['yield_t_ha'])+'|')
text+=['','完整JSON另含每土壤历史/压力的全部均值、中位数、种子标准差、干旱/极端切片与CVaR25的NUE、联合合规、产量及逐年动作。', '', '## 真实干旱季归因', '']
for t in trajectories:
 events=[x for x in t['events'] if x['proposed_action']>0] or t['events'][:1]
 if events:
  text+= [f"历史干旱年{t['year']}，full种子4、default土壤。以下为真实轨迹中的一个决策（优先显示正建议；若全季零施肥则如实展示零动作）（全季逐步记录在JSON中）；说明记录了实际触发条件，不声称隐状态就是可观测土氮浓度。", '', '```json',json.dumps(events[0],ensure_ascii=False,indent=2),'```',''];break
chosen=next(x for x in shield_example['events'] if x['executed_action']>0)
filtered=next(x for x in shield_example['events'] if x['proposed_action']!=x['executed_action'])
text+=['另一个实际示例来自同一1996年、种子4的仅安全层消融（明确不是Full）：执行四次秋冬季80kg/ha施肥，后续建议被规则拦截。该轨迹重放与主表产量和施氮逐项一致，说明硬规则不等于养分平衡或高产。该消融没有GRU，归因中的latent为扁平输入特征；Full的8维GRU记录在前一个示例。完整逐步记录在JSON及phase2-shield-attribution-example.json。','','```json',json.dumps({'model':'shield-only ablation','first_executed_event':chosen,'filtered_event':filtered},ensure_ascii=False,indent=2),'```','']
text+=['## 限制与结论边界','','本轮拒绝“Full效果优越”的结论：其确定性推理退化为零施肥，历史产量下降且NUE/盈余不在联合合规区间。NUE数值约4.28伴随负盈余，不能解释为可持续高效率。当前尚未定位短训练预算、奖励/成本尺度、探索设置或表征的因果贡献；风险代理本身未直接纳入NUE上界和负盈余，亦是明确限制。本轮能回答实现是否可运行、安全投影是否遵守规则、短训下各模块如何表现。不能凭32,768步或零动作违规声称最终产量、NUE或氮盈余已优于论文；安全硬规则也不保证季末NUE/盈余联合合规。尾风险代理和GRU在三种子结果中的任何退化都完整保留。旧套件9项失败、单站点模拟与未达论文训练规模仍是限制。下一轮如需改超参数，应仅使用预留开发年，不得根据本轮历史/压力结果调参后继续当作未见盲测。', '', '## 复核命令', '', '```bash','source scripts/env.sh','(cd NUE_PCSE-Gym && python -m pytest -q)','python scripts/phase2-report.py','python3 /mnt/data/yongan-admin-2/.agents/skills/share-technical-roadmap/scripts/method_diagram.py check --project . --manifest figures/phase2-execution-day-verified/manifest.json','```', '', f"源码提交：NUE_PCSE-Gym `{metrics['git_commits']['NUE_PCSE-Gym']}`；PCSE `{metrics['git_commits']['pcse']}`。项目生成报告时提交 `{metrics['git_commits']['project']}`；最终归档提交由OUTBOX记录，避免报告自引用哈希。"]
(R/'reports/PHASE2_EXPERIMENTAL_RESULTS.md').write_text('\n'.join(text)+'\n')
(R/'reports/phase2-artifact-validation.json').write_text(json.dumps({'status':'passed','evaluation_files':48,'episodes':metrics['evaluation_episodes_total'],'training_runs':15,'total_training_steps':metrics['training_protocol']['training_total_steps'],'all_training_exit_codes_zero':True,'all_shield_executed_violations_zero':True,'all_metrics_finite':True,'training_years_valid':True,'matched_step_budget':32768},indent=2))
print('Validated 48 evaluation files, 15 matched runs; report and metrics written.')
