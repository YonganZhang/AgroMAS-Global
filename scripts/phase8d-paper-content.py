"""Bilingual prose from generated campaign metrics and a hash-guarded first-pass snapshot."""
import json

def build(S,R):
 rows=S['summary']
 snapshot={'reports/phase8/phase8d-G1-verdict.json': '089c4e2a6b03414f925be2f89347cda4f2db18b96df626c5b47e64fa4ac95b6c', 'reports/phase8/phase8d-G1-radius-interpretation.json': '9b564a1680d8726972134ee01c3a8bb62e35cca828607a5904efda3ee0037e7e', 'reports/phase8/phase8d-P2-adapter-training-freeze.json': 'd5ead22ab701d452f0fca92ac7155811c3cd427b2f5531173837365cf3d86d2c', 'reports/phase8/phase8d-root-cause-verification.json': '0d4a216d0acd197c6cd3fc4a1b3e6a255416916e85c958d284f04be899ffb9a7'}
 import hashlib
 for name,digest in snapshot.items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,'First-pass prose snapshot drift: '+name

 def base(x):return x['climate']=='Historical' and x['cap']==40 and x['price_multiplier']==1 and x['subsidy']==0 and x['tax']==0
 def get(policy='TreeMLP',track='Sensorless',mode='soft',benchmark='P1',cohort='Former-Held-Out',scheme='none'):
  v=[x for x in rows if base(x) and x['source']=='NASA' and x['policy']==policy and x['track']==track and x['mode']==mode and x['benchmark']==benchmark and x['cohort']==cohort and x['scheme']==scheme];assert len(v)==1
  return v[0]
 soft=get();hard=get(mode='tree');bare=get(mode='hard-bare-tier2');ppo=get('SensorlessPPO',mode='tree');full=get(track='Full-Telemetry')
 def pct(x):return f"{100*x['region_equal']['joint']:.2f}%"
 def money(x):return f"{x['region_equal']['partial_profit']:.2f}"
 g=json.loads((R/'reports/phase8/phase8d-G1-verdict.json').read_text())['results'];p2=json.loads((R/'reports/phase8/phase8d-P2-adapter-training-freeze.json').read_text())['results'];dec=json.loads((R/'reports/phase8/phase8d-full-TRAIN-physical-decoding.json').read_text());count=S['multiplicity']['family_size']
 minimum=min(v[t]['latent_OOF_R2'] for d in dec['results'].values() for v in d['by_region'].values() for t in dec['required_positive_targets'])
 con=[x for x in S['contrasts'] if base(x) and x['source']=='NASA' and x['benchmark']=='P1' and x['cohort']=='Former-Held-Out' and x['region']=='GLOBAL_EQUAL5' and x['primary']==['TreeMLP','Sensorless','soft'] and x['reference']==['SensorlessPPO','Sensorless','tree'] and x['metric']=='joint'];assert len(con)==1
 c=con[0];paired=f"{100*c['mean_difference']:+.2f} percentage points (marginal 95% interval {100*c['CI95'][0]:+.2f} to {100*c['CI95'][1]:+.2f}; full-family Holm-adjusted pooled farm-year sign-test p={c['Holm_sign_p_full_family']:.3g})"
 paired_zh=f"{100*c['mean_difference']:+.2f}个百分点（边际95%区间{100*c['CI95'][0]:+.2f}至{100*c['CI95'][1]:+.2f}；按农场年份汇总的符号检验经全家族Holm校正p={c['Holm_sign_p_full_family']:.3g}）"
 strata=json.loads((R/'reports/phase8/phase8d-P2-predictive-cohort-strata.json').read_text())['results']
 def predrow(co,scheme,variant):return next(v for v in strata if v['cohort']==co and v['scheme']==scheme and v['variant']==variant)
 predictive=[];predictive_zh=[]
 for co in ('Former-Held-Out','Public-Reused'):
  for scheme in ('LOYO','LORO'):
   a=predrow(co,scheme,'Full64');b=predrow(co,scheme,'Static3')
   predictive.append(f"{co} {scheme} (n={a['site_years']}): Full64/Static3 row-pooled MSE {a['Grain_N_MSE_row_pooled']:.2f}/{b['Grain_N_MSE_row_pooled']:.2f}, world-equal MSE {a['Grain_N_MSE_world_equal']:.2f}/{b['Grain_N_MSE_world_equal']:.2f}; Full64 predictive acceptance {100*a['prior_acceptance_rows']:.2f}% of rows and {100*a['prior_acceptance_world_equal']:.2f}% world-equal")
   predictive_zh.append(f"{co} {scheme}（n={a['site_years']}）：Full64/Static3按行MSE为{a['Grain_N_MSE_row_pooled']:.2f}/{b['Grain_N_MSE_row_pooled']:.2f}，世界等权MSE为{a['Grain_N_MSE_world_equal']:.2f}/{b['Grain_N_MSE_world_equal']:.2f}；Full64预测行接受率{100*a['prior_acceptance_rows']:.2f}%，世界等权{100*a['prior_acceptance_world_equal']:.2f}%")
 transfer=[];transfer_zh=[]
 for co in ('Former-Held-Out','Public-Reused'):
  for scheme in ('LOYO','LORO'):
   a=get('P2-Full64',benchmark='P2',cohort=co,scheme=scheme);b=get('P2-Static3',benchmark='P2',cohort=co,scheme=scheme)
   transfer.append(f"{co} {scheme} (n={a['site_years']}): Full64 {pct(a)}, Static3 {pct(b)}")
   transfer_zh.append(f"{co}的{scheme}（n={a['site_years']}）：Full64为{pct(a)}，Static3为{pct(b)}")
 en=[('Abstract',f'''Seasonal fertilizer decisions combine production, nitrogen-surplus and nutrient-use-efficiency objectives under uncertain weather. We examine how retaining these objectives during feasibility relaxation changes realized management, and whether a causal spatial prior improves transfer. Five typed numerical specialists couple a compact frozen response ensemble to nonanticipative weather-conditioned planning; an independent WOFOST81-SNOMIN referee supplies seasonal outcomes and daily mass-balance audits.

In the historical five-region benchmark of 52 former-held-out farm-years, equal-region joint compliance was {pct(soft)} for Sensorless Soft-Coupled, {pct(hard)} for Tier2-Composite, {pct(bare)} for archived bare relaxation and {pct(ppo)} for masked Sensorless PPO. The paired Soft-Coupled-minus-PPO difference was {paired}. The complete analysis covers 18,268 configurations, with seeds averaged within farm-year before inference and sources, cohorts and transfer schemes kept separate.

A first-pass decomposed spatial adapter slightly reduced row-pooled temporal-fold grain-N error, while world-equal and cross-region errors did not improve. Three-seed TRAIN-only physical readouts were positive in all 30 required region-target cells, with the weakest R² {minimum:.4f}. These are simulator-based, adaptively reused benchmark results, not prospective field assurance or proof of universal policy superiority.'''),
 ('Introduction','''Nitrogen management is a sequential allocation problem embedded in crop growth, soil storage and weather variability. Production gains and fertilizer savings need to be interpreted alongside nutrient removal and nitrogen losses [zhang2015]. A low seasonal surplus alone need not establish desirable management: crop removal can be sustained partly by depletion of soil nitrogen. We therefore retain a bilateral nutrient-use-efficiency corridor as well as a bounded surplus target [eunep2015].

Forecast feasibility and realized compliance are distinct. A controller can lack a candidate satisfying every conservative forecast constraint even though some actions remain agronomically reasonable. Once constraints are relaxed, the remaining ranking objective determines whether nutrient criteria continue influencing decisions. Comparing an objective-preserving controller with a profit-only fallback tests this decision mechanism under a common information and action interface.

A second challenge is spatial adaptation. High-dimensional environmental embeddings contain both persistent site differences and temporally varying information [brown2025]. A low-rank projection of raw embeddings can largely reproduce site identity, while an out-of-distribution rejection can remove potentially useful seasonal information. Separating a physical soil baseline from a causal station-relative anomaly makes these roles explicit; successful admission of the anomaly does not by itself demonstrate predictive or management benefit.

Process-model evaluation provides controlled comparisons and exact bookkeeping, but cannot establish field validity by itself [dewit2019] [berghuijs2024]. We use it to ask three bounded questions: how objective retention affects management under matched information; where causal spatial adaptation helps or fails; and whether outputs and mechanistic readouts remain consistent with the frozen interfaces. We disclose the history of benchmark reuse and retain failed first-pass diagnostics rather than tuning their outcomes away.'''),
 ('Methods','''The framework contains Spatial Twin, Climate, Eco Safety, Economics and Agronomic Control specialists. These are typed numerical modules, not conversational language-model agents. Specialists exchange public observations, candidate plans and numerical forecasts; the external physical referee is never exposed to a policy. Full-Telemetry includes contemporaneous leaf area, soil water and plant nitrogen. Sensorless masks these telemetry channels while retaining public crop stage, weather history, fertilizer history and static soil context. Agent decomposition is an implementation structure; modular-versus-monolithic equivalence does not identify an effect of agent count.

The response backbone maps 36 inputs through two 96-unit SiLU layers to yield, grain nitrogen and executed fertilizer nitrogen. Each 13,155-parameter network uses dropout 0.05; the deployed predictor averages three frozen seeds. Neural training and out-of-fold residual construction use TRAIN 1995–2009. No Phase8D neural retraining was performed. Five outer TRAIN year folds support physical readout diagnostics; all normalizers and stock-label regularization selection exclude their scored outer years.

Phase8D replaces an unbalanced random residual draw with deterministic region-by-stage quantile banks. Within each of 15 strata, joint three-output TRAIN residuals are sorted by signed surplus residual, partitioned into 32 bins and centered to zero mean. Candidate soil keys select the matching private bank; only unmatched synthetic soils use the region-equal global bank. For Phase8D planning metrics, every weather branch integrates all32 residual members with product weights, retaining the joint residual vector. Quantile and upper-tail calculations in distribution_metrics use this full weighted measure. The frozen Sensorless PPO comparator retains its registered91-D observation construction and normalization, including32 systematic weather-residual pair summaries. It receives the repaired causal forecasts and residual banks but is not retrained. Thus the comparison matches information access and action constraints, not every distributional preprocessing operation; differences cannot be attributed solely to optimization or agent organization.

Climate analog matching uses only observations available at the decision date and a TRAIN archive. Scenario warming is removed from the observed-history temperature before matching and before the baseline forecast, while future scenario descriptors retain the prescribed warming and carbon-dioxide regime. Source relative humidity is preserved consistently with the training feature contract. The idealized +1.8°C and +3.5°C settings are stress scenarios, not operational numerical weather forecasts. Information partitions reveal seven-day rain and then temperature; the current action is shared across all branches. Nodewise nonanticipativity does not establish global chance-constrained or CVaR optimality.

The operational action set is 0, 10, 20, 40, 60, 80 or 100 kg N/ha, subject to the common stage scheduler and cumulative fertilizer budget. Surplus is total seasonal nitrogen input minus grain nitrogen removal; total input contains fertilizer, seed and wet deposition, excluding initial soil stocks. NUE is grain nitrogen divided by that input. Realized joint compliance requires 0.50 ≤ NUE ≤ 0.90 and 0 ≤ surplus ≤ cap. Native nitrogen loss is bottom leaching plus denitrification, evaluated separately from surplus. Partial profit equals grain revenue minus fertilizer cost plus experimental compliance subsidy minus any specified surplus tax; it excludes other production costs.

The coupled ranking score is partial profit plus 250 times active joint probability minus 300 times normalized corridor distance. Upper NUE violation receives weight 1.5, and surplus distance includes a 2 kg N/ha interior margin. Tier2-Composite first applies strict active forecast masks; if empty, it prefers candidates preserving both the mean-surplus corridor and bilateral NUE safety, then falls back to the archived upper-surplus condition. Soft-Coupled ranks the same legal candidates continuously without hard-tail masks. Archived bare relaxation preserves its profit-only fallback for comparator faithfulness. Operational zero after OOD rejection or an empty set is not labelled compliance.

G1 calibrates signed two-sided conformal corrections on Dev 2010–2014 and evaluates cross-year macro coverage, Brier skill and ranking regret. An approved, explicitly versioned amendment compares actual calibrated interval width, rather than signed correction alone, because different base quantile widths make the signed correction unsuitable as a sharpness measure. The original failed signed-offset verdict remains archived. This amendment uses frozen predictions, with zero additional Dev access or model changes. Pooled calibration and macro coverage are different summaries; marginal empirical coverage is not a conditional regional guarantee.

For spatial transfer, Stage A always supplies a standardized Static3 physical-soil Ridge correction. Stage B uses a 64-D satellite anomaly relative to that station's unlabelled historical mean through the available t−1 embedding year. It uses neither future satellite years nor held-out outcome labels. Weighted PCA has rank at most four; accepted anomalies contribute an additional residual Ridge correction, while anomaly rejection falls back to Static3. LOYO removes the entire scored calendar year across sites; LORO removes the scored region. The first-pass inner-year grid and fits remain frozen after outer results were observed. A later proposed grid expansion and Dev threshold change were withdrawn; neither was executed.

The evaluation retains 18,268 configurations, the complete 180-cell climate-cap-price-subsidy stress surface, and the 90-cell continuity subset. Every policy recomputes its actions. Verified historical physical terminals can be reused only along exact dated requested-action paths after native recovery of the public observation prefixes; old policy traces are not substituted. Unknown paths run the unchanged native WOFOST81-SNOMIN referee. An infrastructure-only P2 path-name failure stopped the first attempt after 1,915 completed configurations; an explicit hash-verified recovery preserved those records and corrected only the loader mapping. Daily absolute N and C residual tolerances are 1e−10 and 1e−9 kg/ha.

PPO seeds are averaged within farm-year before paired inference. Primary campaign and predictive cohort summaries keep NASA/WUR sources, Former-Held-Out/Public-Reused cohorts and LOYO/LORO schemes separate. The original mixed44-site-year predictive aggregate is explicitly labelled archival. Effects and descriptive intervals use equal-region weighting with paired years resampled within region. Exact sign-test probabilities use pooled paired farm-year signs, not a region-weighted test of the equal-region mean. Every reported exact two-sided sign test belongs to one Holm family [holm1979]. Marginal confidence intervals are not simultaneous confidence bands. Reused evaluation data constrain interpretation [cawley2010] [roberts2017]: the campaign is an adaptive benchmark evaluation and P2 is retrospective causal transfer, not a new prospective blind test.'''),
 ('Results',f'''At the historical reference cap of 40 kg N/ha, Sensorless Soft-Coupled reached {pct(soft)} joint compliance, compared with {pct(hard)} for Tier2-Composite and {pct(bare)} for archived bare relaxation. Their equal-region partial profits were {money(soft)}, {money(hard)} and {money(bare)} EUR/ha, respectively. Full-Telemetry Soft-Coupled reached {pct(full)}. These averages describe the registered five-region mixture; regional results are reported separately in Figure2 and the complete summary tables.

Masked Sensorless PPO reached {pct(ppo)} joint compliance. The paired difference relative to Soft-Coupled was {paired}. All {count:,} exact sign-test contrasts share the same Holm family. Neither a favorable mean nor an unadjusted comparison establishes general superiority. The five former-held-out Netherlands years also limit the resolution of an exact two-sided paired sign test to a minimum attainable p of 0.0625.

G1 cross-year macro 90% coverage was {100*g['Full-Telemetry-mlp']['Dev_crossyear_macro_90pct_coverage']:.2f}% for Full-Telemetry and {100*g['Sensorless-mlp']['Dev_crossyear_macro_90pct_coverage']:.2f}% for Sensorless. Both tracks had positive surplus-event Brier skill against ExtraTrees and climatology at caps 25, 35, 40 and 50, with ranking regret below ExtraTrees. Full and Sensorless regrets were 3.666 and 4.757 EUR/ha. Calibrated mean interval widths were 62.504 and 69.533 kg N/ha, although signed corrections were −5.740 and −6.781 kg N/ha. Regional coverage was heterogeneous: Full-Telemetry AU coverage was 75.19%, so the macro result cannot be treated as a regional assurance.

The first-pass Dev closed-loop diagnostic contained 300 configurations and 84 native trajectories. At AU cap25, Soft-Coupled realized compliance in 40% of Full-Telemetry and 20% of Sensorless years, while Tier2-Composite Sensorless remained at zero. Full-Telemetry Netherlands mean doses were 214, 218 and 218 kg N/ha at caps25,35,40. These fixed observations motivate no further threshold tuning and do not establish a monotonic dose response between every pair of caps.

Equal-region spatial closed-loop comparisons remained stratified: {'; '.join(transfer)}. Cohort-separated predictive results were: {'; '.join(predictive)}. These are prediction-row diagnostics, distinct from acceptance across realized policy decisions. The original all44 mixed-cohort predictive diagnostic, retained as an archival aggregate rather than an unpooled result, gave LOYO Full64 grain-N MSE 462.87 versus Static3 465.41, with89.65% row-level prior acceptance. World-equal LOYO MSE was455.29 versus452.59, so the small row-pooled gain was not invariant to weighting. In LORO, Full64 acceptance rose to 75.12% of rows, or 63.64% under world-equal weighting, but predictive MSE was 505.05 versus Static3 492.41 (RMSE22.47 versus22.19 kg N/ha). Admission therefore improved without proving cross-region predictive benefit. No grid expansion or outer-result-dependent refit was used.

The world-weighted, nested TRAIN physical probe achieved positive within-region out-of-fold R² in all 30 required cells across organic nitrogen, soil carbon and net mineralization. The minimum was {minimum:.4f} for Sensorless US soil carbon. Organic nitrogen and net mineralization are algebraically linked under the simulated stock balance, so those two readouts are not independent mechanistic validations. Other diagnostics, including nitrogen-loss decoding, may remain negative; complete target-level results are retained. Backbone weights were unchanged and the proposed neural auxiliary-head experiment was explicitly skipped.

All 18,268 scored configurations passed the daily mass audit. Maximum absolute N and C residuals were {S['mass_all_configurations']['max_N']:.3e} and {S['mass_all_configurations']['max_C']:.3e} kg/ha. The campaign performed {S['actual_native_simulations']:,} actual native simulations and {S['trajectory_cache_hits']:,} verified trajectory replays. Every replay retained fresh policy decisions and a case-specific trace. Figure4 displays all180 registered stress cells, including unfavorable cells; idealized climate responses are descriptive simulator sensitivities.'''),
 ('Discussion','''Objective retention, forecast conservatism and spatial prior admission address different failure modes. The soft and hard-composite designs share a score but apply different feasibility mechanisms. A narrow bilateral corridor can exclude an action near a forecast threshold, whereas continuous penalties preserve a graded preference. The untuned AU contrast illustrates this distinction; it does not identify a universal advantage of continuous relaxation across climates, crops or threshold choices.

Zero-centering residual banks removes an accidental mean shift, while retaining all weather-residual combinations avoids losing rare branch mass through index pairing. These are distributional consistency repairs. Centering does not prove the residual law is conditionally correct, and finite region-stage quantiles are not a complete account of uncertainty. Likewise, correcting the CQR sharpness comparison does not repair regional undercoverage or establish field safety. Those boundaries remain visible rather than being hidden behind a passing macro gate.

Decomposing the spatial prior separates physical-soil adaptation from temporal satellite novelty. The first-pass LORO results show that positive anomaly acceptance and improved prediction need not coincide. A satellite embedding is a compressed environmental descriptor, not a direct soil-stock or management observation. The retained cross-region error increase is therefore a meaningful boundary of this particular frozen anomaly-transfer design. Further regularization studies would be exploratory development and require new confirmatory evidence.

The physical readouts test whether seasonal stock variation is linearly accessible from frozen response features. Region-specific intercepts and world-scaled penalties avoid mistaking between-region stock baselines or repeated plan rows for independent seasonal information. Nested year selection and seed-specific prediction averaging improve the diagnostic without changing the online controller. The near-zero Sensorless US carbon result remains weak evidence, and linked organic-N/mineralization targets must not be counted as independent confirmation. No latent readout demonstrates causal identification of hidden soil state.

The benchmark contains multiple information tracks, policies and weather regimes but remains simulator-based and adaptively reused. Source-specific weather, crop parameterization, soil inputs and fixed prices constrain extrapolation. Partial profit is not whole-farm welfare; prescribed warming is not a downscaled climate projection; macro coverage is not conditional regional coverage. Future field validation should prospectively freeze decisions and analysis before new observations, include operational forecast error and measurement costs, and retain both favorable and unfavorable regional outcomes.'''),
 ('Conclusion',f'''Phase8D repaired residual integration, warming alignment, relaxation scoring, spatial-prior decomposition and physical-readout regularization while keeping neural weights and first-pass Dev/P2 decisions frozen. The resulting Sensorless Soft-Coupled historical joint compliance was {pct(soft)}, with the complete paired and multiplicity-adjusted comparisons reported alongside regional heterogeneity. Causal prior admission improved but did not eliminate cross-region prediction error. The evidence supports a reproducible comparison of objective-preserving decision designs within this simulator benchmark; prospective agronomic effectiveness remains to be established.''')]
 zh=[('摘要',f'''季节施肥需要在不确定天气下兼顾生产、氮盈余和氮利用效率。本研究考察预测可行性不足时保留养分目标如何改变实际管理，以及因果空间先验能否改善迁移。五个数值专职模块将冻结的紧凑响应集成模型与非预知天气分支规划耦合，由独立WOFOST81-SNOMIN过程模型评价季节结果并逐日审计质量守恒。

在五区52个原留出农场年份的历史参考条件下，无遥测软耦合、硬复合、归档仅收益回退及匹配掩码PPO的五区等权联合达标率分别为{pct(soft)}、{pct(hard)}、{pct(bare)}和{pct(ppo)}。软耦合减PPO的配对差为{paired_zh}。完整分析覆盖18,268个配置，先在农场年份内部平均随机种子，再进行统计；来源、队列和迁移方案均不混合。

首轮分解式空间适配略降低了时间折按行汇总的粮粒氮误差，但世界等权和跨区误差未改善。仅用TRAIN的三种子物理读出在30个必检区域—目标单元中均为正，最低R²为{minimum:.4f}。这些结果来自适应性复用的模拟基准，不能视为前瞻田间保证或普遍策略优势。'''),
 ('引言','''氮肥管理是嵌入作物生长、土壤存储和天气变化中的序贯资源分配问题。生产收益和肥料节约需要结合养分移除及氮损失共同解释[zhang2015]。低氮盈余本身不等于理想管理：作物氮移除可能部分依赖消耗土壤氮库。因此，本研究同时保留双侧氮利用效率区间与氮盈余目标[eunep2015]。

预测可行性与实际达标不同。所有候选方案都不能满足保守预测约束时，放松约束后的排序目标决定环境标准是否仍影响动作。将目标保持型控制与仅收益回退放在相同信息和动作接口下比较，可以检验这一决策机制。

空间迁移还面临静态站点差异与时间变化混合的问题。环境嵌入同时包含两类信息[brown2025]。对原始向量直接降维可能主要重现站点身份；拒绝分布外先验又可能一并去掉季节信息。分离物理土壤基线和因果站点异常，可明确各自作用，但先验获准进入模型不等于预测或管理改善。

过程模型能够支持受控比较和精确记账，但不能单独证明田间有效性[dewit2019] [berghuijs2024]。本文关注目标保持、因果空间适配及机制读出的边界，并公开基准复用历史和不利首轮结果。'''),
 ('方法','''框架包括空间孪生、气候、生态安全、经济和农艺控制五个数值模块；它们不是对话式语言模型智能体。模块交换公共观测、候选方案和数值预测，策略不能访问外部过程模型的隐藏状态。完整遥测包含当期叶面积、土壤水分和植株氮；无遥测轨道屏蔽这些通道，保留公开生育期、天气与施肥历史及静态土壤背景。模块化与单体计算等价不构成智能体数量的因果效应。

响应骨干使用36维输入、两个96单元SiLU隐层及3个输出，预测产量、粮粒氮和执行施氮量。每个网络13,155个参数，dropout为0.05；部署时平均三个冻结种子。神经训练和折外残差只使用1995—2009年TRAIN。本阶段不重训神经网络。五个TRAIN外层年份折用于物理读出；归一化和正则化选择均排除该折被评分年份。

残差分布由15个区域×阶段分层构成。各层按有符号盈余残差排序，将联合三输出残差分为32个分位箱并中心化为零均值。候选静态土壤键选择私有分层；只有无法匹配真实站点的合成土壤向量才使用区域等权全局分布。Phase8D规划指标中，每个天气分支均与全部32个残差向量积分，distribution_metrics的分位数和尾部风险使用完整乘积权重。冻结的无遥测PPO保留已登记的91维观测构造和归一化，其中仍使用32个系统性天气—残差配对摘要；它接收修复后的因果预报和残差分布，但不重训。因此比较匹配信息访问和行动约束，并非每一步分布预处理都相同，差异不能仅归因于优化器或模块组织。

历史类比只使用决策日之前的观测和TRAIN天气档案。在类比匹配和基线预报前，先从情景观测温度中扣除规定升温；未来描述符仍保留升温和二氧化碳情景。相对湿度与训练特征来源保持一致。+1.8°C和+3.5°C为理想化压力情景，不是业务数值天气预报。信息分区依次揭示七日降雨和温度；根动作在所有分支共享。节点非预知性不意味着全局机会约束或CVaR最优性。

动作集为0、10、20、40、60、80或100千克氮/公顷，使用共同生育期调度和累计肥料预算。盈余定义为季节总氮投入减粮粒氮移除；总投入包括肥料、种子和湿沉降，不包括初始土壤氮库。NUE为粮粒氮除以该总投入。实际联合达标要求0.50≤NUE≤0.90且0≤盈余≤上限。原生氮损失为底部淋失与反硝化之和，与盈余分别报告。部分收益为粮食收入减肥料成本，加实验性达标补贴并减规定的盈余税，不包含其他生产成本。

复合评分为部分收益加250倍活动联合概率，再减300倍归一化距离。NUE上界违反权重为1.5，盈余包含2千克氮/公顷的内部安全余量。硬复合先使用严格预测掩码；候选为空时，先保留均值盈余区间和双侧NUE安全，再回退到归档盈余上界条件。软耦合在相同合法候选中连续排序，不施加硬尾部掩码。归档仅收益回退保持原比较语义。分布外或空集后的操作性零施氮不计为达标。

G1使用2010—2014年Dev校准有符号双侧共形修正，报告跨年宏平均覆盖率、Brier技巧和排序遗憾。经批准并单独留痕的协议修订改用实际校准区间宽度判断紧致性，因为基础分位区间宽度不同，有符号修正量不能单独代表紧致性。原排序失败记录保留；此次解释修订使用冻结预测，未新增Dev访问或更改模型。边际覆盖不构成区域条件覆盖保证。

空间适配的阶段A始终提供标准化Static3物理土壤Ridge修正。阶段B将64维卫星向量减去该站点截至可用t−1嵌入年的无标签历史均值，不使用未来卫星年份或外层结果标签。加权PCA维数不超过4，异常通过适用性检查才加入残差Ridge修正；拒绝时回退Static3。LOYO从所有站点训练数据中排除评分日历年；LORO排除评分区域。看到外层结果后，首轮内层年份网格和拟合保持冻结。后来提出的扩网格和Dev阈值调整均已撤回，未执行。

评测保留18,268个配置、180个完整压力单元及90个连续性子集。每个策略重新计算动作。旧轨迹只有经哈希和守恒校验，且新策略沿完全相同的带日期请求路径前进时才能复用；公共观测前缀必须由真实过程模拟恢复，不替换旧策略轨迹。新路径运行原生WOFOST81-SNOMIN。首轮在完成1,915个配置后因P2路径映射错误停止，显式恢复流程仅修复加载器并保留全部已完成记录。每日氮、碳绝对残差限值分别为1e−10和1e−9千克/公顷。

PPO随机种子先在农场年份内平均，再做配对统计。主要闭环及预测分队列汇总保持NASA/WUR、原留出/公开复用及LOYO/LORO分开；原44站点年混合预测汇总明确标为归档诊断。效应及区间采用区域等权，各区内部重采样配对年份；精确符号检验概率使用汇总的配对农场年份符号，并非对区域等权均值的区域加权检验。全部精确双侧符号检验进入同一个Holm家族[holm1979]；边际区间不是同时置信带。复用数据限制确认性解释[cawley2010] [roberts2017]：本研究是适应性基准评估，P2为回顾性因果迁移，不是新前瞻盲测。'''),
 ('结果',f'''历史参考上限40千克氮/公顷下，无遥测软耦合、硬复合和归档仅收益回退的联合达标率为{pct(soft)}、{pct(hard)}和{pct(bare)}，部分收益分别为{money(soft)}、{money(hard)}和{money(bare)}欧元/公顷。完整遥测软耦合达标率为{pct(full)}。这些等权平均数描述预先规定的五区组合，区域异质性另见图2和完整汇总表。

匹配无遥测PPO达标率为{pct(ppo)}；软耦合减PPO的配对差为{paired_zh}。全部{count:,}个精确符号检验共享同一个Holm家族。有利均值或未经校正的比较不代表普遍优越；荷兰只有5个原留出年份，精确双侧符号检验最小可达p值为0.0625。

G1完整遥测和无遥测的跨年宏平均覆盖率为90.78%和90.37%，所有4个上限下的Brier技巧均优于ExtraTrees和气候参考，排序遗憾分别为3.666和4.757欧元/公顷，低于ExtraTrees。实际校准区间平均宽度为62.504和69.533千克氮/公顷，虽然有符号修正量分别为−5.740和−6.781。完整遥测AU区域覆盖率只有75.19%，不能将宏平均通过解释成区域保证。

首轮Dev闭环包含300个配置和84条原生轨迹。AU上限25下，软耦合完整遥测和无遥测的达标率为40%和20%，硬复合无遥测仍为零。荷兰完整遥测在上限25、35、40下的平均施氮为214、218、218千克/公顷。这些冻结观测没有被用于进一步调阈值，也不表明任意两上限之间都存在单调剂量下降。

空间闭环的区域等权结果分别为：{'；'.join(transfer_zh)}。分队列预测诊断为：{'；'.join(predictive_zh)}。这些预测行指标不同于实际闭环决策接受率。原冻结预测诊断的44站点年混合队列汇总仅作为归档诊断保留，不属于分队列结果；其中LOYO Full64粮粒氮MSE为462.87，Static3为465.41，行级接受率89.65%；世界等权LOYO MSE为455.29，高于Static3的452.59，说明小幅按行增益不随加权方式保持。LORO Full64接受率提升至75.12%，世界等权为63.64%，但MSE为505.05，高于Static3的492.41，RMSE为22.47与22.19千克氮/公顷。因此，接受率改善并不证明跨区预测改善，且未依据外层结果扩网格或重拟合。

世界等权、内层选正则化的TRAIN物理读出在30个必检单元中均为正，最低为无遥测美国土壤碳R²={minimum:.4f}。有机氮与净矿化在模拟氮库守恒下存在代数联系，不能视作两个独立机制验证；氮损失等其他目标仍可能出现负值，完整结果均保留。骨干权重未变，拟议神经辅助头实验已明确跳过。

全部18,268个配置通过每日质量审计，最大氮、碳绝对残差分别为{S['mass_all_configurations']['max_N']:.3e}和{S['mass_all_configurations']['max_C']:.3e}千克/公顷。实际运行{S['actual_native_simulations']:,}次原生模拟，精确物理缓存命中{S['trajectory_cache_hits']:,}次。所有复用仍重新计算策略动作和对应轨迹。图4展示完整180单元，包括不利区域与情景。'''),
 ('讨论','''目标保持、预测保守性和先验接受针对不同失效机制。软耦合与硬复合共享评分，但可行性机制不同：严格双侧区间可能排除靠近预测阈值的动作，连续惩罚则保留渐进偏好。未调参的AU对照说明这种差异，但不证明连续放松在所有气候、作物和阈值选择下都占优。

残差中心化去除偶然均值偏移，完整天气—残差组合避免索引配对丢失稀有分支质量。这是分布计算一致性修复，不证明残差条件分布完全正确。修正共形紧致性判据同样不解决区域覆盖不足，也不构成田间安全保证。

分解空间先验区分物理土壤适配和卫星时间异常。首轮LORO说明异常被接受与预测改善并不等价。环境嵌入是压缩背景描述，不是土壤氮库或管理的直接测量。保留的跨区误差增加界定了该冻结异常迁移设计的适用边界；进一步调正则化只能另作探索，并需要新的确认性证据。

物理读出检验冻结响应特征能否线性表达季节氮碳库变化。区域截距和世界尺度惩罚避免将区域静态基线或重复方案行误当独立季节信息。内层年份选择和各随机种子预测平均改善诊断，但不改变在线控制器。接近零的美国无遥测土壤碳结果仍是弱证据；有机氮和矿化读出也非独立验证。任何潜在特征读出均不构成隐藏土壤状态的因果识别。

基准仍受模拟器、天气来源、作物土壤参数和固定价格约束。部分收益不是全农场福利，规定升温不是下推气候预测，宏平均覆盖不是区域条件覆盖。后续田间验证应在新增观测前冻结决策和分析，纳入业务预报误差及测量成本，并保留有利和不利区域结果。'''),
 ('结论',f'''Phase8D修复了残差积分、升温对齐、放松评分、空间先验分解和物理读出正则化，同时冻结神经权重及首轮Dev/P2方案。无遥测软耦合的历史参考联合达标率为{pct(soft)}，完整配对、多重比较校正及区域结果同步报告。因果先验接受率提高，但跨区预测误差没有消失。本研究支持在该模拟基准内复现和比较目标保持型决策设计，前瞻农艺有效性仍需验证。''')]
 fixes={'all32':'all 32','registered91-D':'registered 91-D','including32':'including 32','with89.65%':'with 89.65%','was455.29':'was 455.29','versus452.59':'versus 452.59','RMSE22.47':'RMSE 22.47','versus22.19':'versus 22.19','Figure4':'Figure 4','Figure2':'Figure 2','all180':'all 180','caps25,35,40':'caps 25, 35, 40','cap25':'cap 25','cap40':'cap 40'}
 fixes.update({'mixed44-site-year':'mixed 44-site-year','all44':'all 44'})
 for before,after in fixes.items():en=[(h,t.replace(before,after)) for h,t in en]
 return en,zh
