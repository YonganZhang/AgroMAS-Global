# 代码入口

## 已有底座
- `NUE_PCSE-Gym/pcse_gym/initialize_envs.py`：原生环境构建。
- `NUE_PCSE-Gym/pcse_gym/envs/constraints.py`：实际施肥日期、动作投影与计数；不能只靠周索引推断新引擎日期。
- `NUE_PCSE-Gym/pcse_gym/agent/ppo_mod.py`：现有LagrangianPPO；公平基线须另登记充分训练预算与信息集。
- `pcse/pcse/crop/wofost81.py`、`assimilation.py`、`evapotranspiration.py`：只读WOFOST81和CO2生理响应入口。
- `reports/heldout-unlock-manifest.json`及逐季索引：Phase4已封存证据，不作为新盲测。

## Phase5模块入口（校准与效果另验）
- `pcse_gym/agromas/climate_agent.py`：带签发时刻的7/14日预测与情景输入。
- `urban_eco_agent.py`：区域约束和预测风险可行集。
- `socio_econ_agent.py`：利润、转移支付和剂量边际收益。
- `core_agronomic_agent.py`：可观测状态候选推断、三阶段协调、同信息充分预算PPO接口。
- `regions.py`：五区坐标、南北半球历法、真实数据缓存和年份角色。
模块的数学定义、采用边界和待识别关系以Wiki方法页为准；此图不复制调用图。

- `agromas/contracts.py`、`scheduler.py`：单位、联合成员、上尾CVaR和共享执行日守卫。
- `agromas/outcome_model.py`：TRAIN年份分组残差模型。
- `agromas/baseline.py`：PPO/协调器共用周步环境与生态动作掩码；区域编码器须另接。
- `agromas/physiology.py`、`scripts/phase5-co2-probe.py`：CO2/ET物理接入与旧TRAIN天气探针。

## v2区域与训练入口
- `agromas/season.py`、`initialization.py`：版本化原生总SOM、水容量、真实T2M、文献底肥及逐季完整C/N初始账。
- `agromas/features.py`：早期Train气象模型与共享因果可观测向量。
- `agromas/continuation.py`：第3→2→1阶段老师、外层年份隔离和明确的预测氮量投影。
- `agromas/runtime.py`：真实五区共享周步、90维结构化/76维原始信息对照，实际季末施肥账核验。
- `scripts/phase5-{calibrate-regions-v2,regional-v2-diagnostics,v2-validity-report,fit-climate}.py`：已完成的仅训练校准、诊断及累计Dev检查#2。
- `scripts/phase5-{generate-teachers,fit-continuation,ppo}.py`：物理标签生成、续策拟合、全封装吞吐和原生PPO；完成状态以逐项回执为准。

## 冻结评估与证据
- `agromas/final_evaluation.py`：只给当前状态的确定性/PPO回放，冻结归一化，PCSE外部依赖核验。
- `agromas/legacy_comparators.py`：v2物理背景下的荷兰日历N2及冻结Phase4处方迁移，明确不冒充原场景复现。
- `scripts/phase5-{seal-final-evaluation,generate-final-books,score-final-books,final-statistics,green-confirmation}.py`：一次解锁、共同物理轨迹复用、完整矩阵与年份簇统计。
- `scripts/phase5-correct-green-subsidy-v3.py`：恢复原协议的全部训练季联合达标及零补贴N2参照；v2宽松筛选仅保留为次要证据。

- `scripts/phase5-{derive-functional-attribution-v4,physical-feasibility-diagnostic-v4}.py`：不重选策略的次级功能与有限网格存在性分析。
- `scripts/phase5-verify-merged-tests-v4.py`：双仓合并后真实原生测试、派生缓存复原及冻结证据核验。
- `reports/phase5/PHASE5_TOP_JOURNAL_REPORT.md`：完整负结果、统计口径与证据边界。
- `scripts/phase5-macro-stratified-sensitivity-v4-r1.py`：审查后事后分层年份敏感性，保留原冻结同步年簇主结果。

## Phase6 独立扩展
- `agromas_v6/core.py`：64树配对32成员、双侧筛选、目标及一致的协调器入口。
- `agromas_v6/books.py`、`training.py`：前缀因果检查、年份内续策老师与TRAIN回放。
- `agromas_v6/book_env.py`：仅当前信息的91维三决策PPO账簿环境。
- `scripts/phase6-{fit,prepare-ppo,ppo,green-subsidy}.py`：训练选择与冻结，全部不读最终账簿。
- `scripts/phase6-{audit-train-boundaries,ppo-context-audit,seal-permit,score-final}.py`：训练重建、冻结诊断、新许可及复用评分。
- `scripts/phase6-analyze.py`：年份内种子平均、5000次年簇与区域分层敏感性、冻结补贴规则投射。
- `scripts/phase6-plot-{common,fig2,fig3,fig4}.py`：全新九张定量候选；`phase6-palette.py`仅复用OKLCh色彩函数。
- `scripts/phase6-verify-tests.py`、`phase6_pytest_import_guard.py`：真实pytest子进程来源证明与缓存原字节恢复。
