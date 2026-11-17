"""Generate contribution-oriented, outcome-first Top-SCI (CEA) paired bilingual Markdown manuscript and captions."""
from pathlib import Path
import json, re

R = Path(__file__).resolve().parents[1]
P = R / 'reports/phase8'
F = P / 'figures'
CAP_DIR = F / 'captions-v12'
CAP_DIR.mkdir(parents=True, exist_ok=True)
M = R / 'manuscript/phase8'

S = json.loads((P / 'phase8d-core-statistics.json').read_text())
G = json.loads((P / 'phase8d-G1-verdict.json').read_text())['results']
W = json.loads((P / 'phase8d-G1-radius-interpretation.json').read_text())['tracks']
DEC = json.loads((P / 'phase8d-full-TRAIN-physical-decoding.json').read_text())
P2_STRATA = json.loads((P / 'phase8d-P2-predictive-cohort-strata.json').read_text())['results']
rows = S['summary']


def q(**kw):
    m = [
        x for x in rows
        if x['source'] == 'NASA'
        and x['tax'] == 0
        and x.get('climate', 'Historical') == kw.get('climate', 'Historical')
        and x.get('cap', 40) == kw.get('cap', 40)
        and x.get('price_multiplier', 1) == kw.get('price_multiplier', 1)
        and x.get('subsidy', 0) == kw.get('subsidy', 0)
        and x.get('benchmark', 'P1') == kw.get('benchmark', 'P1')
        and x.get('cohort', 'Former-Held-Out') == kw.get('cohort', 'Former-Held-Out')
        and x.get('scheme', 'none') == kw.get('scheme', 'none')
        and x['policy'] == kw.get('policy', 'TreeMLP')
        and x['mode'] == kw.get('mode', 'soft')
        and x['track'] == kw.get('track', 'Sensorless')
    ]
    assert len(m) == 1, (kw, len(m))
    return m[0]


def contrast(ref, scheme='none', benchmark='P1'):
    c = [
        x for x in S['contrasts']
        if x['source'] == 'NASA' and x['cohort'] == 'Former-Held-Out'
        and x['scheme'] == scheme and x['benchmark'] == benchmark
        and x['climate'] == 'Historical' and x['cap'] == 40
        and x['price_multiplier'] == 1 and x['subsidy'] == 0 and x['tax'] == 0
        and x['region'] == 'GLOBAL_EQUAL5' and x['metric'] == 'joint'
        and x['primary'] == (['P2-Full64', 'Sensorless', 'soft'] if benchmark == 'P2' else ['TreeMLP', 'Sensorless', 'soft'])
        and x['reference'] == ref
    ]
    assert len(c) == 1, (ref, len(c))
    return c[0]


def p2_pred(co, scheme, var):
    m = [x for x in P2_STRATA if x['cohort'] == co and x['scheme'] == scheme and x['variant'] == var]
    assert len(m) == 1, (co, scheme, var)
    return m[0]


# Exact verified quantities from frozen JSON ledgers
soft = q(policy='TreeMLP', mode='soft', track='Sensorless')
hard = q(policy='TreeMLP', mode='tree', track='Sensorless')
bare = q(policy='TreeMLP', mode='hard-bare-tier2', track='Sensorless')
ppo = q(policy='SensorlessPPO', mode='tree', track='Sensorless')
dvs = q(policy='DVS-N2', mode='tree', track='Full-Telemetry')
full_soft = q(policy='TreeMLP', mode='soft', track='Full-Telemetry')
full_hard = q(policy='TreeMLP', mode='tree', track='Full-Telemetry')
open_lp = q(policy='TreeMLP', mode='open-loop', track='Sensorless')
greedy = q(policy='TreeMLP', mode='greedy-frozen', track='Sensorless')
et_soft = q(policy='TreeExtraTrees', mode='soft', track='Sensorless')
weath_soft = q(policy='TreeWeather', mode='soft', track='Sensorless')
lin_soft = q(policy='TreeLinear', mode='soft', track='Sensorless')
eco25 = q(policy='remove-eco', mode='soft', track='Full-Telemetry', cap=25)
eco40_s = q(policy='remove-eco', mode='soft', track='Sensorless', cap=40)
full25_f = q(policy='TreeMLP', mode='soft', track='Full-Telemetry', cap=25)
ppo_vs = contrast(['SensorlessPPO', 'Sensorless', 'tree'])

soft_w18_40 = q(climate='idealized_mid', cap=40, price_multiplier=1)
soft_w18_25 = q(climate='idealized_mid', cap=25, price_multiplier=1)
dvs_w18_25 = q(climate='idealized_mid', cap=25, price_multiplier=1, policy='DVS-N2', mode='tree', track='Full-Telemetry')
soft_w35_40 = q(climate='idealized_high', cap=40, price_multiplier=1)
ppo_w35_40 = q(climate='idealized_high', cap=40, price_multiplier=1, policy='SensorlessPPO', mode='tree')
dvs_w35_40 = q(climate='idealized_high', cap=40, price_multiplier=1, policy='DVS-N2', mode='tree', track='Full-Telemetry')

soft_2x_hist = q(price_multiplier=2, cap=40)
ppo_2x_hist = q(price_multiplier=2, cap=40, policy='SensorlessPPO', mode='tree')
soft_2x_w18 = q(climate='idealized_mid', price_multiplier=2, cap=40)
ppo_2x_w18 = q(climate='idealized_mid', price_multiplier=2, cap=40, policy='SensorlessPPO', mode='tree')
soft_2x_w35 = q(climate='idealized_high', price_multiplier=2, cap=40)
ppo_2x_w35 = q(climate='idealized_high', price_multiplier=2, cap=40, policy='SensorlessPPO', mode='tree')

w18_s100 = q(climate='idealized_mid', subsidy=100, cap=40)
hist_s200 = q(climate='Historical', subsidy=200, cap=40)
w35_s200 = q(climate='idealized_high', subsidy=200, cap=40)

p2_ly_f = q(policy='P2-Full64', benchmark='P2', scheme='LOYO')
p2_ly_s = q(policy='P2-Static3', benchmark='P2', scheme='LOYO')
p2_ly_e = q(policy='P2-ExtraTrees64', benchmark='P2', scheme='LOYO')
p2_lr_f = q(policy='P2-Full64', benchmark='P2', scheme='LORO')
p2_lr_s = q(policy='P2-Static3', benchmark='P2', scheme='LORO')

pr_ly_f = p2_pred('Former-Held-Out', 'LOYO', 'Full64')
pr_lr_f = p2_pred('Former-Held-Out', 'LORO', 'Full64')
pr_lr_s = p2_pred('Former-Held-Out', 'LORO', 'Static3')

min_r2 = min(
    v[t]['latent_OOF_R2']
    for d in DEC['results'].values()
    for v in d['by_region'].values()
    for t in DEC['required_positive_targets']
)

assert abs(100 * soft['region_equal']['joint'] - 25.06) < 0.02
assert abs(100 * ppo['region_equal']['joint'] - 27.00) < 0.02
assert abs(100 * bare['region_equal']['joint'] - 4.00) < 0.02
assert abs(100 * p2_ly_f['region_equal']['joint'] - 29.83) < 0.02
assert abs(100 * p2_lr_f['region_equal']['joint'] - 20.39) < 0.02
assert abs(min_r2 - 0.0056) < 0.001

# Figure Captions (25-60 EN words, 40-100 ZH chars, zero colons/semicolons/slashes/em-dashes)
CAPTIONS = {
    'fig1.txt': (
        'Architecture of AgroMAS-Global linking five specialized numerical modules with an external mechanistic referee. '
        'The spatial twin, climate forecast, urban eco-safety, socio-economic policy and core agronomic modules exchange public histories and scenario weights while remaining isolated from hidden soil pools.\n'
        'AgroMAS-Global五专职数值模块与外部机理裁判协同架构图。地空孪生、气候预测、城市生态安全、社会经济政策与核心农艺模块仅交换公开观测和方案分布，与隐藏土壤库保持严格隔离。'
    ),
    'fig2.txt': (
        'Climatic context, regional nitrogen regimes and surrogate calibration across five global wheat archetypes. '
        'Panels show a 47-year temperature anomaly and deposition backdrop, b five mutually exclusive efficiency and surplus regimes with agronomic attributes, c covariance ellipses inside the bilateral safety corridor and d conformal coverage, Brier skill and regret reduction.\n'
        '五大麦区气候背景、氮收支格局与代理模型共形校准评价。图a为47年温度距平与沉降背景，图b为五类互斥收支状态及农艺属性，图c为双侧安全走廊与一倍标准差椭圆，图d为覆盖率、Brier技巧及排序遗憾降幅。'
    ),
    'fig3.txt': (
        'Historical control performance, nested corridor compliance and within-season soil nitrogen dynamics. '
        'Panels compare a four primary policies in nutrient space, b ten controllers across nested joint, efficiency and single-bound criteria, c 349-day Perth soil mineral nitrogen and cumulative losses and d aligned apparent efficiency and surplus distributions.\n'
        '历史基准控制对比、嵌套走廊达标结构与季内氮素动态。图a为四类核心策略相空间分布，图b为十种策略在联合、效率与单边边界的嵌套达标对比，图c为349天珀斯站矿质氮与损失演变，图d为表观NUE与盈余分布。'
    ),
    'fig4.txt': (
        'Sensorless spatiotemporal transfer using causal satellite anomaly priors under temporal and cross-regional holdouts. '
        'Panels display a held-out surplus distributions and compliance shifts across five adapters, b grain nitrogen prediction error versus compliance trajectories with paired confidence intervals, c five-region efficiency-surplus shift vectors and d combined transfer ellipses.\n'
        '基于因果卫星距平先验的无传感器跨年与跨区迁移表现。图a为五种适配器盈余分布与达标哑铃迁移，图b为籽粒氮RMSE与达标二维泛化轨迹及置信区间，图c为五大产区二维迁移向量与准入率，图d为迁移椭圆对照。'
    ),
    'fig5.txt': (
        'Factorial climate, policy and economic stress surface across global wheat regimes. '
        'Panels show a continuous cap-by-warming advantage contours, b threshold-dependent crossover with embedded win-tie-loss cell counts, c leave-one-region-out sensitivity ranges and d green subsidy Pareto profit-compliance trajectories with invariant native nitrogen loss insets.\n'
        '全球小麦产区气候、生态红线与经济政策全因子压力相图。图a为盈余上限与升温连续优势等值面，图b为阈值交叉曲线与45格胜平负计数，图c为逐区留一敏感区间，图d为绿色补贴Pareto演化轨迹与原生氮损失插图。'
    ),
    'figs1.txt': (
        'Supplementary comparison of warming trajectories, climate ablation and surplus ceiling gradients. '
        'Panels isolate a warming trends alongside year-matched climate removal and b stricter surplus ceilings paired with realized surplus distributions.\n'
        '增温轨迹、气候模块剥离与氮盈余红线梯度补充对比。图a为气候变暖曲线与同年配对去气候消融，图b为收紧盈余红线下的达标率与实测盈余分布。'
    ),
    'figs2.txt': (
        'Supplementary seasonal soil nitrogen supply balance and 349-day stock drawdown profiles. '
        'Panels contrast a applied fertilizer, soil stock drawdown, grain nitrogen removal and apparent versus stock-adjusted efficiency with b daily organic and mineral nitrogen trajectories.\n'
        '季节土壤氮收支平衡与349天库存动用补充剖析。图a对比外源施氮、土壤动用、籽粒移除及表观与扣库存NUE，图b展示逐日有机氮与矿质氮曲线。'
    ),
    'figs3.txt': (
        'Supplementary fertilizer price shock responses and dual-axis subsidy sensitivity curves. '
        'Panels report a doubled fertilizer price effects across warming levels and b compliance alongside partial profit across subsidy intensities.\n'
        '化肥翻倍价格冲击响应与双轴补贴敏感性补充结果。图a为不同升温情景下肥价翻倍影响，图b为补贴梯度下的达标率与部分收益响应曲线。'
    ),
    'figs4.txt': (
        'Supplementary nine-policy uncertainty intervals and four-metric agronomic scorecard. '
        'Panels present a equal-region bootstrap confidence intervals paired with apparent efficiency and b standardized multi-metric scorecards across yield, nitrogen input, surplus and partial profit.\n'
        '九种控制策略不确定性区间与四指标农艺评分卡。图a展示区域等权自助置信区间及表观NUE，图b展示产量、施氮、盈余与收益四项标准化评分。'
    ),
    'figs5.txt': (
        'Supplementary eight-policy efficiency distributions and 32-year historical evolution trajectories. '
        'Panels summarize a full eight-policy apparent efficiency rainclouds and b multi-decade zero-split baseline versus soft-coupled and bare relaxation trajectories.\n'
        '全量八策略效率分布与32年历史演变补充轨迹。图a为八种策略表观NUE云雨分布，图b为1995至2026年零追肥参考与对照策略演化轨迹。'
    ),
    'figs6.txt': (
        'Supplementary prior admission criteria and grain nitrogen error matrix across transfer cohorts. '
        'Panels show a row-weighted, world-weighted and closed-loop prior admission rates and b mean squared error matrices across five satellite adapters.\n'
        '空间迁移先验准入准则与籽粒氮误差补充矩阵。图a对比按行、世界等权及闭环决策三类准入率，图b为五种适配器的预测均方误差矩阵。'
    ),
    'figs7.txt': (
        'Supplementary complete 180-cell factorial advantage surface across three climate regimes. '
        'Heatmaps display paired compliance differences between soft-coupled control and masked reinforcement learning with black outlines marking the 90 canonical continuity cells.\n'
        '三类气候情景下完整180格全因子优势曲面补充图。热图完整保留软耦合与掩码强化学习的逐格差值，黑框标示90个核心连续性检查单元。'
    ),
    'figs8.txt': (
        'Supplementary latent physical state decoding and daily carbon-nitrogen conservation checks. '
        'Panels show a out-of-fold decoding determination across 50 region-target cells with required positive cells framed and b 349-day mass balance residuals across 6.1 million simulated daily records.\n'
        '隐藏物理状态解码检验与逐日氮碳质量守恒核验补充图。图a为50格折外解码决定系数及30个必正单元边框，图b为610万条逐日记录质量残差核验。'
    ),
}

for fname, txt in CAPTIONS.items():
    (CAP_DIR / fname).write_text(txt + '\n')

blocks = []


def add_block(bid, zh_t, en_t, figs=None):
    blocks.append((bid, zh_t.strip(), en_t.strip(), figs or []))


# Title
add_block(
    'title',
    '# 耦合气候、流域、市场与卫星先验的小麦氮肥管理',
    '# Coupling climate, watershed, market and satellite priors for wheat nitrogen management'
)

# Abstract (Five-Step S1-S5, aligned with Top-SCI exemplar & five-step norm)
add_block('sec-abs', '## 摘要', '## Abstract')

abs_en = (
    'Sustainable wheat production requires keeping seasonal nitrogen use efficiency between 0.50 and 0.90 while holding nitrate surplus positive yet below watershed ceilings, balancing food security against groundwater contamination and long-term humus depletion. '
    'Across multi-continental agroecosystems, however, compounding climate warming, stricter nitrate caps, fertilizer price surges and missing field sensors trap single-system controllers between two structural failures, as rigid safety filters collapse into zero-dose deadlocks under tight caps, unconstrained profit maximizers mine native soil nitrogen during price shocks, and raw satellite embeddings fail cross-continental transfer by confusing permanent site identity with seasonal fertility anomalies. '
    'To resolve this dilemma, AgroMAS-Global couples warming-de-shifted climate analogues, continuous watershed cap margins, bilateral market-corridor scoring and station-demeaned satellite anomalies separated from hydraulic soil baselines inside a 166.3 KB conformalized neural surrogate across three split-application stages. '
    'Across five contrasting global wheat regions, continuous corridor coupling prevents soil-mining collapse (raising joint compliance 6.27-fold over profit-only fallback), preserves statistical parity with full-budget reinforcement learning in mild climates while leading on an independent seven-season Dutch benchmark (28.57 versus 19.05 percent), and compresses serialized storage over 1,690-fold below 64-tree ensembles alongside 38.5 percent higher compliance and up to 49.4 percent lower ranking regret. '
    'Under 1.8 and 3.5 degrees Celsius warming at the operational 40 kg N ha$^{-1}$ ceiling, climate-market coupling overtakes reinforcement learning by 5.15 and 5.61 percentage points (expanding to 7.19 to 8.10 percentage points when fertilizer prices double) by anticipating heat-compressed phenology without retreating into soil mining. '
    'Finally, decoupling hydraulic soil baselines from causal satellite anomalies raises cross-continental prior gate admission from zero to 60.00 percent, while full-profile nitrogen accounting exposes 221 to 224 kg N ha$^{-1}$ of single-season soil humus drawdown behind nominal compliance and identifies a 100 EUR ha$^{-1}$ green-subsidy inflection that aligns farm profitability with clean watersheds.'
)

abs_zh = (
    '可持续小麦生产必须将季节表观氮肥利用效率稳固在0.50至0.90双侧走廊内并维持非负且不越线的流域净盈余，以协同保障粮食供给、地下水防污与土壤肥力永续。'
    '然而在跨洲农业生态系统中，气候变暖、严格水源红线、化肥价格暴涨与无在线传感器约束并发叠加，使既有单系统控制陷入两极陷阱，刚性安全滤波在严苛红线下坍缩为零施肥死锁，无护栏逐利策略在高肥价冲击下靠抽支土壤有机氮粉饰账面收益，而原始高维卫星嵌入则因混淆固定站位身份与季节养分变化导致跨洲先验完全拒答。'
    '为此，本研究构建AgroMAS-Global多先验协同框架，在总计仅166.3千字节的共形神经代理与三阶段非预知动态规划中，耦合去升温偏移气候类比、连续流域红线余量、双侧市场走廊效用以及剥离水力土壤基线后的站点因果卫星距平。'
    '跨越五大典型麦区的独立机理评测表明，连续双侧走廊耦合彻底阻断土壤氮透支（较仅收益回退提升6.27倍联合达标率），在温和历史年份与充分预算强化学习保持等效并在荷兰7季独立基准以28.57%领先19.05%，同时较64棵树集成实现逾1,690倍存储压缩并取得高出38.5%的达标率与至多49.4%的排序遗憾降幅。'
    '在每公顷40千克氮主流红线遇1.8与3.5摄氏度升温时，多先验耦合因能前瞻捕捉热害压缩的生育窗口，反超同信息强化学习5.15与5.61个百分点（肥价翻倍时扩至7.19至8.10个百分点）。'
    '此外，土壤与卫星距平因果解耦将跨洲先验门控准入率由零抬升至60.00%，而全剖面氮收支核算揭示出表观达标背后每公顷221至224千克的隐性土壤有机氮动用，并在适度升温下锁定每公顷100欧元绿色补贴的帕累托最优拐点。'
)
add_block('abs-body', abs_zh, abs_en)

# Section 1: Introduction (P1-P5, 80/10/10 citations, zero journal names, author-named, NO paper-roadmap sentence)
add_block('sec-intro', '## 1 引言', '## 1 Introduction')

p1_en = (
    'Over the late twentieth century, widespread adoption of synthetic fertilizers doubled global cereal output, yet global nutrient budgets compiled by Zhang et al. [zhang2015] reveal that less than half of applied fertilizer nitrogen enters harvested grain worldwide. '
    'Excess reactive nitrogen accelerates aquifer nitrate leaching, nitrous oxide emissions and coastal eutrophication, intensifying the conflict between food security and environmental protection highlighted by Lipper et al. [lipper2014]. '
    'Wheat nitrogen management has accordingly expanded from single-dimensional yield pursuit to jointly regulating crop uptake, hydrological export and soil organic nitrogen turnover across diverse cropping zones [chen2014]. '
    'Crucially, field balance diagnostics by Van der Pol [vanderpol1992] established that even unfertilized cereals continue harvesting nitrogen mineralized from native soil humus, meaning that a low or negative seasonal surplus alone hides long-term soil fertility depletion. '
    'To prevent such disguised soil mining while limiting hydrological runoff, the European Nitrogen Expert Panel [eunep2015] instituted a bilateral safety corridor requiring apparent nitrogen use efficiency between 0.50 and 0.90 alongside nonnegative surplus below catchment ceilings.'
)
p1_zh = (
    '二十世纪中后期以来，化学氮肥的广泛施用推动全球谷物单产成倍增长，但Zhang等 [zhang2015] 编制的全球养分收支表明，投入农田的化学氮素不足半数进入收获籽粒。'
    '未能回收的活性氮持续加剧地下水硝态氮污染、温室气体排放与近海富营养化，使Lipper等 [lipper2014] 揭示的粮食安全与生态环境保护矛盾不断收紧。'
    '小麦氮肥管理也随之从单维高产转向兼顾作物吸收、水文流失与土壤有机氮库周转的跨产区协同调控 [chen2014]。'
    '尤为关键的是，Van der Pol [vanderpol1992] 的田间收支诊断证实，即便完全停施化肥，麦田仍会持续吸收原生土壤腐殖质矿化释放的氮素，因此单纯的低盈余甚至负盈余并不能代表生态安全，反而可能掩盖慢性土壤肥力耗竭。'
    '为同步防范隐蔽性土壤氮透支与流域水体污染，欧洲氮专家组 [eunep2015] 正式确立了双侧安全走廊准则，要求表观氮肥利用效率维持在0.50至0.90之间且净盈余保持非负并低于流域上限。'
)
add_block('intro-p1', p1_zh, p1_en)

p2_en = (
    'Existing agricultural nitrogen stewardship studies evolved along three primary routes, yet each encounters critical friction when climate shifts, tight watershed caps, price shocks and sensorless regional transfer interact outside stationary benchmark stations. '
    'Along the biophysical modeling route, dynamic process simulators resolve daily crop phenology, biomass partitioning and soil nitrogen turnover, beginning with Van Diepen et al. [vandiepen1989] on WOFOST water-limited crop growth and Groot and Verberne [groot1991] on winter wheat nitrogen balance calibration. '
    'Mature platforms consolidated by De Wit et al. [dewit2019] standardized regional simulation workflows, while Ceglar et al. [ceglar2019] refined European wheat phenology accuracy and Berghuijs et al. [berghuijs2024] coupled crop nitrogen uptake directly with mineral and organic soil pools to evaluate nitrate directives. '
    'In parallel, multi-crop simulation environments developed by Jones et al. [jones2003] for management diversity, Stockle et al. [stockle2003] for continuous multi-year nutrient accounting and Holzworth et al. [holzworth2014] for semi-arid water-nitrogen coupling broadened field process coverage, whereas Van Ittersum et al. [vanittersum2013], Van Bussel et al. [vanbussel2015] and Van der Velde et al. [vandervelde2019] scaled point simulations to regional yield gaps and continental monitoring. '
    'Along the agronomic management route, multi-site fertilization rules introduced by Cui et al. [cui2010] and Fageria and Baligar [fageria2005] aligned split topdressing with stage-specific crop nitrogen demand. '
    'Empirical syntheses by Yang et al. [yang2022] and Wang et al. [wang2020] quantified water-nitrogen thresholds and advisory gains across intensive wheat belts, while light-soil trials by Faber et al. [faber2021] and sensor workflows reviewed by Fountas et al. [fountas2015] improved field placement. '
    'Using harmonized indicator frameworks [norton2015], farm surveys by Silva et al. [silva2021] and monitoring by Ravensbergen et al. [ravensbergen2024] uncovered substantial room to trim surplus across commercial arable farms, and European and global directives [eu2016, fao2019, klages2020] tied uniform surplus limits to groundwater protection, even as Zhou et al. [zhou2016] and Huang et al. [huang2007] documented multi-decadal deep nitrate retention and slow humus turnover. '
    'Nevertheless, static calendar prescriptions cannot anticipate within-season droughts or heatwaves that compress grain filling and alter soil mineralization [altenbach2003, iizumi2016]. '
    'Along the sequential optimization route, digital-twin control reviews by Pylianidis et al. [pylianidis2021] and Gautron et al. [gautron2022a] built on multi-objective constrained optimization foundations [censor1977, roijers2013, achiam2017] to automate dynamic split decisions. '
    'Process-simulator wrappers by Overweg et al. [overweg2021] and Gautron et al. [gautron2022b], together with multi-year rotation suites by Turchetta et al. [turchetta2022] and modular observation interfaces by Maillard et al. [maillard2023], converted agronomic models into reinforcement learning testbeds. '
    'Early deep policy learners by Wu et al. [wu2022], imitation warm-starts by Tao et al. [tao2022] and watershed-coupled agents by Madondo et al. [madondo2023] reduced fertilizer inputs across stationary benchmarks, while domain randomization by Tobin et al. [tobin2017], reward analyses by Eschmann [eschmann2021] and safe evaluation suites [ji2023, sutton2018] clarified safety-shortcut trade-offs. '
    'Most closely related to this work, Baja et al. [baja2025] integrated constrained reinforcement learning into a nitrogen-coupled wheat simulator to target bilateral efficiency at a single Dutch station, yet relied on continuous station sensors and isolated climatic baselines, even as soil grids by Poggio et al. [poggio2021] and annual satellite embeddings [brown2025, campsvalls2025] opened scalable global spatial representations without ground telemetry.'
)
p2_zh = (
    '围绕小麦氮肥协同调控，学术界已沿机理模拟、农艺分期调控与序贯智能优化三条路径深入推进，但走出单一试验田稳态条件后，既有范式在多系统耦合压力下仍普遍失配。'
    '第一条机理建模路径在日尺度上解析作物物候发育与土壤碳氮周转，始于Van Diepen等 [vandiepen1989] 建立受水肥制约的WOFOST动态生长模型以及Groot等 [groot1991] 构建的冬小麦水氮田间校验数据集。'
    '随后De Wit等 [dewit2019] 凝练形成标准化定量作物模拟平台，Ceglar等 [ceglar2019] 改进了欧洲小麦物候期参数化精度，Berghuijs等 [berghuijs2024] 则进一步将作物吸氮耦合至土壤矿质氮与有机氮库以评估硝酸盐环境指令。'
    '同期，Jones等 [jones2003] 拓展的DSSAT平台、Stockle等 [stockle2003] 构建的CropSyst多年轮作养分收支体系以及Holzworth等 [holzworth2014] 面向干旱麦区的APSIM水氮模拟框架完善了多元农作制表达，而Van Ittersum等 [vanittersum2013]、Van Bussel等 [vanbussel2015] 与Van der Velde等 [vandervelde2019] 完成了田块产量差向区域及洲际农情预测的尺度上推。'
    '第二条农艺调控路径致力于协调分期施肥时间与作物关键生育期需氮节律，Cui等 [cui2010] 与Fageria等 [fageria2005] 确立了高产低污分期施氮基本原则，Yang等 [yang2022] 与Wang等 [wang2020] 分别量化了中国主产麦区的水肥协同阈值及推荐施肥减氮成效，Faber等 [faber2021] 与Fountas等 [fountas2015] 则细化了轻质土减淋洗追肥与冠层变量施肥流程。'
    '依托统一的国际养分指标体系 [norton2015]，Silva等 [silva2021] 与Ravensbergen等 [ravensbergen2024] 在商业农场大样本调查中揭示出不减产前提下的显著降盈余空间，区域环保指令 [eu2016, fao2019, klages2020] 也据此把统一盈余上限锚定于地下水安全红线，而Zhou等 [zhou2016] 与Huang等 [huang2007] 则记录了深层剖面硝态氮厚重滞留与土壤有机碳数十年尺度的缓慢周转。'
    '然而，静态农艺配方缺乏季内动态前瞻修正能力，难以应对花前春旱或热害对灌浆期与矿化节奏的突发冲击 [altenbach2003, iizumi2016]。'
    '第三条序贯智能优化路径将机理模拟器与强化学习相连接，Pylianidis等 [pylianidis2021] 与Gautron等 [gautron2022a] 基于多目标约束优化理论 [censor1977, roijers2013, achiam2017] 系统梳理了随机农业序贯控制前景。'
    'Overweg等 [overweg2021] 与Gautron等 [gautron2022b] 先后把过程作物模型封装为交互式决策环境，Turchetta等 [turchetta2022] 与Maillard等 [maillard2023] 进一步扩展了多季土壤演替与状态观测分离接口。'
    'Wu等 [wu2022] 的深度强化学习节肥策略、Tao等 [tao2022] 的模仿热启动以及Madondo等 [madondo2023] 的流域面源协同减排探索验证了静态单站节肥潜力，同时Tobin等 [tobin2017]、Eschmann [eschmann2021] 与安全学习基准研究 [ji2023, sutton2018] 揭示了环境漂移与标量奖励投机风险。'
    '与本文最为接近的研究是Baja等 [baja2025] 基于含氮扩展小麦模型开展的荷兰单站约束强化学习，但该工作高度依赖连续田间传感器且局限于单一平稳气候，未能把握全球土壤图谱 [poggio2021] 与地球卫星基础表征 [brown2025, campsvalls2025] 带来的无传感器跨洲协同契机。'
)
add_block('intro-p2', p2_zh, p2_en)

p3_en = (
    'Stepping beyond well-monitored single stations reveals that existing paradigms break along four coupled boundaries that trap controllers between starvation and pollution [baja2025]. '
    'At the climate boundary, reactive schedulers ignore post-topdressing rainstorms and scenario warming shifts, leaving fertilizer plans unable to separate leaching storms from heat-compressed grain filling [asseng2015]. '
    'At the watershed boundary, rigid feasibility clipping collapses whenever strict urban nitrate ceilings prune noisy tail forecasts, emptying legal candidate sets and locking fields into zero topdressing [eu1991, klages2020]. '
    'At the market and soil boundary, rising fertilizer prices exploit unguarded profit objectives, allowing controllers to harvest short-term net income by withholding nitrogen and silently mining native soil humus [eschmann2021, tan2005]. '
    'At the spatial observation boundary, feeding raw annual satellite embeddings directly to downstream predictors conflates fixed geographic station identity with seasonal fertility anomalies, triggering total prior rejection on unseen continents [gaso2023, roberts2017]. '
    'The central scientific challenge is therefore how climate analogues, continuous bilateral corridor gradients, market resilience penalties and causal soil-satellite decoupling co-govern the regime transitions linking zero-dose deadlock, soil nitrogen mining and joint watershed compliance.'
)
p3_zh = (
    '走出监测完备的单一平稳试验站后，既有方法在四大相互咬合的系统边界处接连失灵，使控制器陷入作物饥饿与水体污染的两极摇摆 [baja2025]。'
    '在气候边界，反应式规则忽视追肥后强降水与气候变暖偏移，难以及时区分淋洗暴雨与热害逼熟窗口压缩 [asseng2015]。'
    '在流域边界，偏严的水源氮盈余红线一旦叠加预测尾部噪声，刚性截断筛选便会将合法动作集剪裁为空集并锁死在零追肥僵局 [eu1991, klages2020]。'
    '在市场与土壤边界，化肥涨价诱使无防透支护栏的利润目标采取停施化肥策略，靠悄悄掏空土壤腐殖质维持表面高收益 [eschmann2021, tan2005]。'
    '在空间遥感边界，未经剥离的年度高维卫星表征将固定站位坐标与季节养分动态混为一谈，致使陌生大洲外推时先验完全失效 [gaso2023, roberts2017]。'
    '由此凝练的核心科学问题，正是如何耦合气候类比、连续双侧走廊梯度、市场防透支惩戒与土壤卫星因果解耦，共同支配零追肥死锁、土壤氮掠夺与流域双侧达标之间的动态切换机制。'
)
add_block('intro-p3', p3_zh, p3_en)

p4_en = (
    'Leaving these four boundaries decoupled carries heavy agronomic, ecological and fiscal costs across global breadbaskets. '
    'When algorithms are benchmarked solely on benign historical seasons, surface equivalence hides acute fragility that only erupts once warming, strict catchment limits and volatile fertilizer markets co-occur [baja2025]. '
    'Inside drinking-water catchments, brittle hard constraints unnecessarily halt fertilization and penalize harvest stability, whereas profit-maximizing policies trade irreversible long-term soil fertility for temporary cash gains [zhou2016, booth2023]. '
    'Equally troubling, green subsidies tied directly to uncalibrated nominal probabilities inflate public expenditures without reducing deep nitrate drainage. '
    'Mapping these coupled failure mechanisms clarifies when low-memory coupled control unlocks reliable regional adaptation before costly multi-year field rollouts begin [goldenits2024].'
)
p4_zh = (
    '若继续孤立对待这重重相互缠绕的边界冲突，主产麦区将付出高昂的稳产、环保与财政代价。'
    '仅依托温和历史单一气候对比算法表现，表面上的分数持平会严重掩盖多维压力并发时的突发性崩塌脆性 [baja2025]。'
    '在水源保护区内，刚性超限截断会无差别中断正常追肥并损伤籽粒产能，而放任逐利算法则用不可逆的长期耕地肥力枯竭换取短期账面利润 [zhou2016, booth2023]。'
    '同样地，若将农业生态补贴直接挂钩未经校准的名义先验概率，财政支出虽层层加码却无法转化为地下水的真实减氮。'
    '因此，打通四重先验耦合机制并划定严格应用边界，对多压力交织下实现轻量化低成本跨区推广具有重要科学与实践价值 [goldenits2024]。'
)
add_block('intro-p4', p4_zh, p4_en)

p5_en = (
    'To answer this scientific question, AgroMAS-Global integrates four domain priors for climate, watershed, market and causal spatial inference inside a compact three-stage dynamic planner evaluated against an independent crop-soil simulator across Australia, the United States, the Netherlands, France and China. '
    'First, continuous bilateral corridor scoring inside compact conformalized neural surrogates prevents zero-dose deadlocks and soil-mining collapses (6.27-fold compliance gain over profit-only fallback) while shrinking deployment storage over 1,690-fold below 64-tree ensembles. '
    'Second, stripping prescribed warming shifts prior to weather-analogue matching while retaining elevated temperature and carbon-dioxide physiology along decision branches overcomes the warming-price trap along the 40 kg N ha$^{-1}$ ceiling, overtaking matched reinforcement learning by 5.15 and 5.61 percentage points under 1.8 and 3.5 degrees Celsius warming. '
    'Third, separating hydraulic soil baselines from causal station-demeaned satellite anomalies unlocks sensorless cross-continental prior admission from zero to 60.00 percent while isolating where soil calibration remains indispensable for error reduction. '
    'Fourth, integrating full-profile organic nitrogen accounting with green-subsidy stress surfaces exposes hidden single-season humus drawdown alongside a 100 EUR ha$^{-1}$ moderate-warming policy inflection, establishing a conservation-verified pathway for resilient split fertilization.'
)
p5_zh = (
    '针对上述核心科学问题，本研究提出AgroMAS-Global多先验协同调控框架，将气候、流域、市场与因果卫星先验融入三阶段动态规划并由独立作物土壤机理引擎在澳大利亚、美国、荷兰、法国与中国五大典型麦区开展全量封闭验证。'
    '第一，构建共形校准轻量化神经代理并嵌入连续双侧走廊效用，在避免严苛红线死锁与高肥价土壤透支的同时将联合达标率较仅收益回退提升6.27倍，且比64棵树集成节省逾1,690倍存储空间。'
    '第二，在历史天气类比匹配阶段先行剥离情景增温偏移并保留后续高温与二氧化碳生理响度，借以攻克气候变暖叠加高肥价陷阱，在每公顷40千克氮常规红线上于1.8与3.5摄氏度升温分别领先强化学习5.15与5.61个百分点。'
    '第三，将水力土壤物理基线与站点历史去均值因果卫星距平严格剥离，在不依赖田间传感器前提下将跨洲先验门控准入率从零拉升至60.00%，并明晰门控准入与局部定量误差校准的各自角色。'
    '第四，联立全剖面有机氮库存动用核算与生态补贴响应测试，穿透表面达标掩盖的土壤腐殖质隐性净亏损并锁定适度升温下每公顷100欧元的理想政策拐点，形成兼顾产量、流域水质与长期地力的可扩展范式。'
)
add_block('intro-p5', p5_zh, p5_en)

# Section 2: Methodology (Readable 3-section structure with motivation-first sub-sections)
add_block('sec-methods', '## 2 研究方法', '## 2 Methodology')

add_block('sec-m21', '### 2.1 问题定义', '### 2.1 Problem Formulation')

m21_p1_en = (
    'Seasonal wheat fertilization is posed as a finite-horizon non-anticipative control problem across three sequential phenological windows triggered when observable development stage crosses 0.20, 0.55 and 0.82 [ceglar2019, baja2025]. '
    'At each event $t \\in \\{1, 2, 3\\}$, controllers choose discrete topdressing nitrogen $u_t \\in \\{0, 10, 20, 40, 60, 80, 100\\}$ kg N ha$^{-1}$ subject to a cumulative seasonal ceiling of 220 kg N ha$^{-1}$, spanning 343 budget-legal action schedules. '
    'In the primary sensorless deployment track, real-time field telemetry of leaf area, soil water and plant nitrogen stays completely masked during online decisions.'
)
m21_p1_zh = (
    '小麦全生育期追肥被形式化为三阶段有限时域非预知序贯控制问题，当外部可观测发育阶段依次跨越0.20、0.55与0.82阈值时触发第一至第三阶段追肥决策 [ceglar2019, baja2025]。'
    '每次决策 $t \\in \\{1, 2, 3\\}$ 仅可从离散剂量集合 $\\{0, 10, 20, 40, 60, 80, 100\\}$ 千克氮每公顷中选取方案并受总上限220千克每公顷制约，共同构成343套合法全季动作计划。'
    '主线无传感器部署轨道全程屏蔽叶面积指数、土壤墒情与植株含氮量实时田间观测，确保迁移方案不依赖昂贵在线硬件。'
)
add_block('m21-p1', m21_p1_zh, m21_p1_en)

m21_p2_en = (
    'Total seasonal external input $I_N = \\sum_{t=1}^{3} u_t + N_{\\text{base}} + N_{\\text{seed}} + N_{\\text{dep}}$ accounts for topdressing, pre-sowing basal fertilizer, seed nitrogen and atmospheric wet deposition while excluding baseline soil organic nitrogen stocks, and grain removal is denoted $H_N$ [eunep2015]. '
    'Because $H_N$ incorporates nitrogen mineralized from native soil organic matter whereas $I_N$ falls as low as 3.5 kg N ha$^{-1}$ of seed and deposition when synthetic fertilizer is withheld, unfertilized soil mining mathematically pushes apparent efficiency $\\text{NUE}_{\\text{app}} = H_N / I_N$ well above 1.0 alongside negative surplus $S_N < 0$. '
    'Bilateral EUNEP sustainability therefore demands simultaneous satisfaction of $0.50 \\le \\text{NUE}_{\\text{app}} \\le 0.90$ and watershed-safe surplus $0 \\le S_N \\le S_{\\text{cap}}$ alongside partial profit $\\Pi$.'
)
m21_p2_zh = (
    '外源总投入 $I_N = \\sum_{t=1}^{3} u_t + N_{\\text{base}} + N_{\\text{seed}} + N_{\\text{dep}}$ 计入追肥、播前底肥、种子氮与湿沉降并剥离初始土壤氮库，收获籽粒氮移出记作 $H_N$ [eunep2015]。'
    '由于籽粒吸收 $H_N$ 兼含土壤原生有机氮矿化贡献，一旦停施化肥使分母 $I_N$ 骤降至种子与沉降之和（仅约每公顷3.5千克），土壤氮透支便在数学上推动表观利用率 $\\text{NUE}_{\\text{app}} = H_N / I_N$ 远超 1.0 并伴随负盈余 $S_N < 0$。'
    '正因如此，EUNEP双侧可持续管理目标要求表观利用效率 $0.50 \\le \\text{NUE}_{\\text{app}} \\le 0.90$ 与净盈余红线 $0 \\le S_N \\le S_{\\text{cap}}$ 同步达标，并与部分毛收益 $\\Pi$ 共同受物理系统约束。'
)
add_block('m21-p2', m21_p2_zh, m21_p2_en)

m21_eq1_en = (
    '$$S_N = I_N - H_N, \\qquad \\text{NUE}_{\\text{app}} = \\frac{H_N}{I_N}, \\qquad \\Pi = p_g Y - p_f \\sum_{t=1}^{3} u_t + \\psi \\mathbb{I}_{\\text{joint}} - \\tau \\max(S_N, 0)$$'
)
m21_eq1_zh = m21_eq1_en
add_block('m21-eq1', m21_eq1_zh, m21_eq1_en)

m21_p3_en = (
    'where $Y$ is dry grain yield, $p_g = 200$ EUR per tonne is wheat price, $p_f = 1.5$ EUR per kg N scales baseline nitrogen cost by scenario multipliers, $\\psi$ is the ecological compliance subsidy and $\\tau$ denotes an optional nonnegative surplus levy fixed at zero in standard baseline evaluations. '
    'Independently, internal soil conservation monitors organic and mineral pool changes, daily bottom leaching and denitrification loss $L_{\\text{nat}}$ and net mineralization to contrast apparent efficiency against native soil drawdown $\\Delta N_{\\text{org}}$ [silva2021, dewit2019].'
)
m21_p3_zh = (
    '其中 $Y$ 为收获籽粒干重，小麦基准收购价 $p_g = 200$ 欧元每吨，基准氮肥单价 $p_f = 1.5$ 欧元每千克按情景倍数缩放，$\\psi$ 为绿色生态达标补贴，$\\tau$ 为可选非负净盈余环境税（主流基准对比设为零）。'
    '与此同时，剖面土壤氮收支模块独立追踪有机氮与矿质氮库存演变、逐日底部淋洗与反硝化原生损失 $L_{\\text{nat}}$ 及净矿化量，借以透视表观指标背后的真实土壤有机氮动用 $\\Delta N_{\\text{org}}$ [silva2021, dewit2019]。'
)
add_block('m21-p3', m21_p3_zh, m21_p3_en)

add_block('sec-m22', '### 2.2 多先验耦合控制架构', '### 2.2 Multi-Prior Coupled Control Architecture')

m22_intro_en = (
    'Collapsing competing meteorological, environmental and economic constraints into an unstructured scalar reward frequently induces shortcut depletion or constraint deadlock whenever stressors interact. '
    'AgroMAS-Global resolves this bottleneck by partitioning control over five typed numerical modules, namely the spatial twin, climate forecast, urban eco-safety, socio-economic policy and core agronomic specialists, communicating solely through public weather histories and calibrated probability distributions while an unchanged WOFOST81-SNOMIN engine acts as an isolated physical referee (Fig. 1). '
    'Thirty paired equivalence tests spanning 323 budget-legal schedules across both full-telemetry and sensorless tracks verify 100.0 percent decision agreement (zero action discrepancies) between this five-specialist coordinator and a consolidated monolithic solver, confirming that performance gains derive strictly from causal spatial adaptation, warming-de-shifted analogue branching, continuous bilateral corridor scoring and non-anticipative dynamic continuation.'
)
m22_intro_zh = (
    '将相互冲突的气象风险、流域环保红线与经济回报强行压缩为无结构单一标量奖励，极易在多重胁迫并发时诱发智能体投机透支或死锁。'
    '为此，AgroMAS-Global 将决策流程清晰解耦为地空孪生、气候预测、城市生态安全、社会经济政策与核心农艺统筹五大数值专职模块，各模块仅传递公开气象历史与校准概率分布，并与外部只读 WOFOST81-SNOMIN 过程模型保持严格隔离的物理裁判边界（图1）。'
    '跨越完整遥测与无传感器双轨道共30组配对不变性检验（每组覆盖323套合法预算动作组合）实证了五专职协同决策与单体集成求解在动作输出上达成100.0%零偏差严格一致，从而确证系统增益完全来源于因果卫星适应、去升温天气分支、连续双侧走廊评分及非预知动态续策四大物理机理算子。'
)
add_block('m22-intro', m22_intro_zh, m22_intro_en, figs=['@fig reports/phase8/figures/fig1-architecture.png | reports/phase8/figures/captions-v12/fig1.txt | Fig. 1'])

add_block('sec-m221', '#### 2.2.1 卫星与土壤空间先验耦合', '#### 2.2.1 Satellite and Soil Spatial Prior Coupling')

m221_en = (
    'Online search across hundreds of budget-legal fertilization sequences precludes slow daily mechanistic loops and favors smooth calibrated surrogates running in sub-millisecond batches. '
    'The spatial twin specialist therefore replaces bulky tree ensembles with a compact three-seed multilayer perceptron mapping 36 normalized public features covering heat-unit progression, seasonal weather, cumulative doses and static soil properties through two 96-unit SiLU hidden layers (13,155 weights per network) to jointly estimate grain yield, grain nitrogen and executed doses with all weights frozen on 1995 to 2009 seasons. '
    'Because feeding raw satellite embeddings directly confounds fixed geographic coordinates with seasonal fertility shifts [brown2025], sensorless cross-regional transfer decouples hydraulic soil Ridge priors $\\Delta_{\\text{Static3}}(\\mathbf{x}_{\\text{soil}})$ capturing field capacity, wilting point and saturated conductivity from causal site-demeaned annual satellite anomalies $\\Delta \\mathbf{e}_{s,t-1}$ computed strictly up to prior year $t-1$.'
)
m221_zh = (
    '针对在线三阶段三百余套合法施肥序列寻优对毫秒级前向推演与平滑联合概率估计的双重需求，空间孪生模块弃用了臃肿树模型，部署了三随机种子冻结轻量多层感知机集成（输入涵盖积温发育、时序气象、已施氮量与土壤属性共36维公开归一化特征，两层96单元SiLU隐层，每成员仅含13,155个参数），权重于1995至2009年训练后永久冻结。'
    '考虑到原始高维遥感嵌入直接回归会将永久站点身份与季节养分波动混为一谈 [brown2025]，无传感器跨区迁移模块设计了两阶段因果分解，先行剥离表征田间持水量、凋萎系数与导水率的水力土壤岭回归基线 $\\Delta_{\\text{Static3}}(\\mathbf{x}_{\\text{soil}})$，再叠加严格受限于前一年 $t-1$ 历史站均值的因果卫星距平 $\\Delta \\mathbf{e}_{s,t-1}$。'
)
add_block('m221-p1', m221_zh, m221_en)

m221_eq_en = (
    '$$\\Delta \\mathbf{e}_{s,t-1} = \\mathbf{e}_{s,t-1} - \\frac{1}{|\\mathcal{Y}_{s, \\le t-1}|} \\sum_{y \\in \\mathcal{Y}_{s, \\le t-1}} \\mathbf{e}_{s,y}, \\qquad \\hat{H}_N^{\\text{adapt}} = \\hat{H}_N^{\\text{base}} + \\Delta_{\\text{Static3}}(\\mathbf{x}_{\\text{soil}}) + \\mathbb{I}_{\\text{in}}(\\Delta \\mathbf{e}_{s,t-1}) \\Delta_{\\text{PCA4}}(\\Delta \\mathbf{e}_{s,t-1})$$'
)
m221_eq_zh = m221_eq_en
add_block('m221-eq', m221_eq_zh, m221_eq_en)

m221_en2 = (
    'Whenever incoming anomalies exceed the weighted four-component trust region encoded by $\\mathbb{I}_{\\text{in}}$, out-of-distribution inputs fall back deterministically to $\\Delta_{\\text{Static3}}$ rather than extrapolating noise.'
)
m221_zh2 = (
    '一旦外推距平超脱四维主成分加权可信包络，准入指示函数 $\\mathbb{I}_{\\text{in}}$ 自动关闭低秩修正并安全退守物理土壤基线，从结构上杜绝失真外推。'
)
add_block('m221-p2', m221_zh2, m221_en2)

add_block('sec-m222', '#### 2.2.2 气候、流域与市场先验耦合', '#### 2.2.2 Climate, Watershed, and Market Prior Coupling')

m222_en = (
    'To anticipate post-topdressing leaching storms and warming compression without peeking at realized weather, the climate specialist strips scenario warming offsets $\\Delta T_{\\text{scen}}$ from observed prefixes before matching historical weather analogues, thereby preserving daily rainfall clustering statistics while retaining full elevated temperature and carbon-dioxide covariates along physiological branches [asseng2015]. '
    'Every decision node reveals seven-day precipitation prior to temperature realizations so root doses obey strict non-anticipative information structure. '
    'Under tight nitrate ceilings where strict tail pruning empties feasibility sets, the urban eco-safety and socio-economic modules integrate a 2 kg N ha$^{-1}$ cap margin alongside a 1.5-weighted mining penalty ($\\text{NUE}_{\\text{app}} > 0.90$) across the full weather-by-residual product distribution, preventing agents from buying cheap surplus compliance via humus depletion [tessler2018, cawley2010].'
)
m222_zh = (
    '为在不泄漏未来真实气象前提下捕捉追肥后强降雨淋洗与高温逼熟胁迫，气候预测模块在检索历史类比天气前缀前先从观测序列表面剥离情景增温偏移 $\\Delta T_{\\text{scen}}$，在保持逐日降雨聚类统计规律的同时于下游生理分支完整保留升温与二氧化碳协变量 [asseng2015]。'
    '每个分支节点先揭示七日降水再展开温度实现，确保根节点配肥严格符合非预知因果律。'
    '面对严苛水源上限下硬筛选频繁空集的问题，生态安全与经济政策模块将每公顷2千克内部盈余余量与1.5倍高效率透支惩罚融合积分至完整天候与残差乘积分布，构造平滑走廊效用函数 $J(u)$，借以彻底封堵靠消耗土壤氮库换取虚假达标的捷径 [tessler2018, cawley2010]。'
)
add_block('m222-p1', m222_zh, m222_en)

m222_eq_en = (
    '$$J(u) = \\mathbb{E}[\\Pi(u)] + 250 \\, P_{\\text{active}}(\\text{joint} \\mid u) - 300 \\, d_{\\text{corr}}\\!\\left(\\bar{S}_N(u), \\bar{\\text{NUE}}_{\\text{app}}(u)\\right)$$'
)
m222_eq_zh = m222_eq_en
add_block('m222-eq', m222_eq_zh, m222_eq_en)

m222_en2 = (
    'Here $P_{\\text{active}}(\\text{joint} \\mid u)$ tracks expected joint corridor compliance over the active weather-by-residual distribution and $d_{\\text{corr}}$ sums bilateral efficiency violations (penalizing $\\bar{\\text{NUE}}_{\\text{app}} > 0.90$ at 1.5 times weight) alongside surplus violations evaluated on expected schedule outcomes $\\bar{S}_N(u)$ and $\\bar{\\text{NUE}}_{\\text{app}}(u)$. Notice that $\\Pi(u)$ governs realized cash profit accounting (with external farm subsidy $\\psi$), whereas the weighted terms in $J(u)$ act strictly as dimensionless corridor-alignment planning utilities. '
    'Finally, the core agronomic specialist solves three-stage non-anticipative continuation under a minimum 14-day inter-application interval, preserving the identical action-budget mask used by matched reinforcement learning baselines [ppo2017, mask2020].'
)
m222_zh2 = (
    '式中 $P_{\\text{active}}(\\text{joint} \\mid u)$ 表示完整乘积分布下的预期联合达标概率，$d_{\\text{corr}}$ 则基于分支与残差期望均值 $\\bar{S}_N(u)$ 与 $\\bar{\\text{NUE}}_{\\text{app}}(u)$ 累加双侧效率偏离（对超过0.90的土壤透支施加1.5倍权重）与盈余越界。需要明确，式1中的 $\\Pi(u)$ 与 $\\psi$ 对应外部现金收支核算，而式3中的双侧走廊加权项仅用作内部规划排序无量纲效用，区别于可行集为空后仅顾利润排序的退化逻辑。'
    '最终，核心农艺模块遵循最小14天施氮间隔求解三阶段非预知动态续策规划，并与强化学习基线严格共享统一合法掩码与总预算 [ppo2017, mask2020]。'
)
add_block('m222-p2', m222_zh2, m222_en2)

add_block('sec-m23', '### 2.3 模型校准与验证策略', '### 2.3 Calibration and Validation Strategy')

m23_p1_en = (
    'Rather than approximating surrogate error through independent Gaussian variances that break coupling between yield and grain nitrogen uptake, out-of-fold errors are partitioned across five regions and three stages into 15 residual strata, sorted by surplus residual into 32 equiprobable quantile vectors and centered strictly to zero stratum mean to prevent systematic bias. '
    'Empirical farm profiles draw from their station-specific private residual bank while reverting to the equal-region global bank only for unseen synthetic soil keys, integrating every analogue weather branch across all 32 vectors during online planning. '
    'On the 2010 to 2014 development split, two-sided conformal calibration targets 90 percent empirical coverage and evaluates physical interval width alongside Brier skill across caps of 25, 35, 40 and 50 kg N ha$^{-1}$ and downstream profit ranking regret to guarantee probabilistic sharpness before closed-loop deployment [fisher1981, geurts2006].'
)
m23_p1_zh = (
    '区别于假定正态独立分布并割裂产量与吸氮耦合关系的简化残差假设，训练折外三输出联合误差按五大产区与三个追肥阶段划分为15层，依据有符号盈余残差严格切分为32个等概率联合分位向量并强制零均值去中心化以根除概率漂移。'
    '实证田块优先匹配所属产区私有残差库，仅在未见合成土壤属性上回退至区域等权全局残差库，从而使在线分支积分完整守恒产量与氮平衡尾部协变。'
    '进一步利用2010至2014年独立开发集开展90%名义双侧共形校准，同步考核校准后物理区间宽度、四档红线（25至50千克）Brier技巧及下游收益选优排序遗憾，以在闭环决策前确立严格的概率锐度门槛 [fisher1981, geurts2006]。'
)
add_block('m23-p1', m23_p1_zh, m23_p1_en)

m23_p2_en = (
    'To prevent cross-regime leakage, validation separates 52 historical former-held-out seasons (2015 to 2026), 40 causal satellite-anomaly transfer years (2019 onward) and 7 independent Dutch Wageningen benchmark seasons into non-overlapping cohorts alongside inner-fold hyperparameter freezing for both leave-one-year-out and leave-one-region-out generalization [roberts2017, cawley2010]. '
    'All controllers run freshly from initial conditions inside unchanged WOFOST81-SNOMIN simulations, evaluated first within farm-year seeds and then across equal-region five-archetype averages using unified Holm-adjusted exact sign tests and paired bootstrap intervals [holm1979, phipson2010].'
)
m23_p2_zh = (
    '防泄漏验证严格隔离52个历史留出农场年、40个满足前置条件的卫星距平迁移年以及7个独立荷兰公开基准年，跨年与跨洲适配器全部超参数均在内层训练折锁定 [roberts2017, cawley2010]。'
    '所有控制方案均在未修改的WOFOST81-SNOMIN机理裁判上重头封闭推演，统计检验先行在单农场年多种子内取均值，再基于五产区等权口径施行统一Holm校正双侧精确符号检验与自助置信区间评估 [holm1979, phipson2010]。'
)
add_block('m23-p2', m23_p2_zh, m23_p2_en)

# Section 3: Experimental Results — Readable Five-Section Structure (3.1 - 3.5)
add_block('sec-res', '## 3 实验结果', '## 3 Experimental Results')

# 3.1 Dataset and Benchmark Regions (~350 EN words, Table 1 + Fig. 2a-d deep walkthrough)
add_block('sec-r31', '### 3.1 数据集与典型麦区说明', '### 3.1 Dataset and Benchmark Regions')

r31_p1_en = (
    'Across four continents, the five wheat archetypes segregate into physically distinct climatic warming trends, soil nitrogen endowment pools and dominant EUNEP compliance regimes rather than merely replicating homogeneous field baselines (Table 1 and Fig. 2a to c). '
    'As shown in Fig. 2a, historical climate forcing from 1980 to 2026 exhibits pronounced late-period temperature acceleration exceeding 1.5 degrees Celsius across Europe and Australia during the locked test horizon alongside steadily declining Dutch wet ammonium and nitrate deposition [asseng2015, clo2022]. '
    'Sequential chronological splitting (1985 to 1994 spin-up, 1995 to 2009 training, 2010 to 2014 conformal development and 2015 to 2026 testing) cleanly isolates non-stationary test extremes from surrogate fitting.'
)
r31_p1_zh = (
    '横跨四洲的五大典型麦区呈现出迥异的气候变暖节律、初始土壤氮库存与主导收支失衡格局，并非简单重复平稳试验田设定（表1与图2a至c）。'
    '图2a的近半世纪气候序列显示，2015至2026年锁定测试期增温速率陡峭攀升，同时欧洲参照站湿沉降持续回落 [asseng2015, clo2022]。依托1985至1994年平衡启动、1995至2009年训练、2010至2014年共形开发与2015至2026年测试的严格时序切割，测试季非平稳极端气候与模型拟合实现彻底隔离。'
)
add_block('r31-p1', r31_p1_zh, r31_p1_en)

r31_p2_en = (
    'Decomposing held-out seasons into five mutually exclusive EUNEP outcomes alongside regional agronomic indicators clarifies why a single static rule fails globally (Fig. 2b and c). '
    'Perth (17.4 t ha$^{-1}$ initial organic nitrogen) and Wichita (11.6 t ha$^{-1}$) occupy active fertilizer-responsive dryland corridors reaching 63.6 and 33.3 percent joint compliance, whereas maritime Lelystad achieves the highest grain yield (9.08 t ha$^{-1}$, 0.83 apparent efficiency) from modest organic pools (7.0 t ha$^{-1}$) yet hovers along the upper surplus ceiling (60.0 percent pure surplus exceedance, 20.0 percent compliance). '
    'In contrast, Beauce sustains heavy mineralization from fertile stocks (13.15 t ha$^{-1}$), pushing 91.7 percent of seasons above 0.90 apparent efficiency into soil nitrogen mining despite producing 8.53 t ha$^{-1}$. Conversely, Luancheng starts with lower organic reserves (5.64 t ha$^{-1}$) paired with heavy pre-sowing basal fertilizer plus deposition (174.50 kg N ha$^{-1}$ total input), whereas water-limited yields (3.43 t ha$^{-1}$) export only 69.79 kg N ha$^{-1}$ in grain, simultaneously depressing apparent efficiency to 0.40 (below the 0.50 floor) and stranding 104.71 kg N ha$^{-1}$ of excess surplus across 83.3 percent dual-failure seasons. '
    'Projecting regional 1-sigma covariance ellipses onto the bilateral input-removal plane (Fig. 2c) separates dryland compliance in Perth and Wichita, surplus-border concentration in Lelystad, upper soil mining in Beauce and lower-quadrant saturation in Luancheng.'
)
r31_p2_zh = (
    '结合五类互斥氮收支归属与产区基础农艺指标可以清晰阐明静态单点经验为何难以全球通用（图2b与c）。'
    '珀斯（初始有机氮每公顷17.4吨）与威奇托（每公顷11.6吨）处于积极追肥主导的较高达标带（联合达标63.6%与33.3%），而高产密集区荷兰莱利斯塔德依托每公顷7.0吨土壤库支撑每公顷9.08吨高产，紧贴盈余上限徘徊（60.0%纯超限、20.0%达标）。'
    '反之，巴黎盆地凭借每公顷13.15吨肥沃土壤高矿化支撑8.53吨高产的同时，令91.7%年份表观效率跃过0.90上限陷入土壤透支。华北栾城则因播前基肥与湿沉降总投入已达每公顷174.50千克（初始土壤有机氮5.64吨），而水分限制产量（每公顷3.43吨）仅带走69.79千克籽粒氮，在算术上同步把表观效率拉低至0.40（低于0.50下限）并遗留104.71千克净盈余超限，导致83.3%测试年份双指标同时违约。图2c相平面一倍标准差椭圆直观勾勒出五大产区在双侧安全楔区内外的水肥物理位置分异。'
)
add_block('r31-p2', r31_p2_zh, r31_p2_en)

tbl1_zh = (
    '表1 全球五大典型小麦产区基础水土特征与氮素收支格局。\n'
    '| 产区简称 | 代表麦区 | 气候与流域环境 | 测试年数 | 初始有机氮（吨每公顷） | 均值产量（吨每公顷） | 软耦合达标率（%） | 主导失衡机制 |\n'
    '|---|---|---|---:|---:|---:|---:|---|\n'
    '| AU | 澳大利亚珀斯麦带 | 地中海雨养旱作暖干带 | 11 | 17.37 | 4.87 | 63.6 | 积极追肥高适应区 |\n'
    '| US | 美国堪萨斯威奇托 | 半干旱大陆性高波动粮仓 | 12 | 11.55 | 2.76 | 33.3 | 降水波动混合受限区 |\n'
    '| NL | 荷兰莱利斯塔德 | 温带海洋性密集水网基准 | 5 | 7.01 | 9.08 | 20.0 | 高产贴线纯盈余超限 |\n'
    '| FR | 法国巴黎盆地 | 塞纳河流域高矿化富碳带 | 12 | 13.15 | 8.53 | 8.3 | 高矿化表观过耗区 |\n'
    '| CN | 中国华北栾城 | 京津冀地下水高压区 | 12 | 5.64 | 3.43 | 0.0 | 高盈余叠加低NUE区 |'
)
tbl1_en = (
    'Table 1 Physical baselines and regional nitrogen regimes across the five urban-breadbasket wheat archetypes.\n'
    '| Code | Representative archetype | Climatic and watershed context | Held-out n | Initial organic N (t ha$^{-1}$) | Mean grain yield (t ha$^{-1}$) | Soft-Coupled compliance (%) | Dominant failure regime |\n'
    '|---|---|---|---:|---:|---:|---:|---|\n'
    '| AU | Western Australia Perth belt | Mediterranean dryland warming belt | 11 | 17.37 | 4.87 | 63.6 | Active high-compliance dryland |\n'
    '| US | Kansas Wichita plains | Semi-arid continental grain belt | 12 | 11.55 | 2.76 | 33.3 | Precipitation-volatile mixed belt |\n'
    '| NL | Netherlands Lelystad polder | Maritime river network benchmark | 5 | 7.01 | 9.08 | 20.0 | High-yield surplus-border belt |\n'
    '| FR | France Paris Beauce basin | Seine high-mineralization belt | 12 | 13.15 | 8.53 | 8.3 | High-NUE soil-mining belt |\n'
    '| CN | North China Plain Luancheng | Peri-urban aquifer-stressed belt | 12 | 5.64 | 3.43 | 0.0 | Dual surplus and low-NUE belt |'
)
add_block('tbl-1', tbl1_zh, tbl1_en)

r31_p3_en = (
    'Development-set conformal validation further establishes why the compact neural surrogate outperforms conventional tree ensembles prior to closed-loop deployment (Fig. 2d). '
    f'Both full-telemetry ({100*G["Full-Telemetry-mlp"]["Dev_crossyear_macro_90pct_coverage"]:.2f} percent) and sensorless ({100*G["Sensorless-mlp"]["Dev_crossyear_macro_90pct_coverage"]:.2f} percent) models anchor tightly near the nominal 90 percent band despite single-region dispersion in Western Australia ({100*G["Full-Telemetry-mlp"]["by_region"]["australia_wa_perth"]["crossyear_coverage"]:.2f} percent under full telemetry). '
    f'Across 25 to 50 kg N ha$^{{-1}}$ caps, surplus-event Brier skill improves upon extremely randomized trees by {100*G["Full-Telemetry-mlp"]["caps"]["25"]["BSS_vs_ExtraTrees"]:.1f} to {100*G["Full-Telemetry-mlp"]["caps"]["50"]["BSS_vs_ExtraTrees"]:.1f} percent with full telemetry and {100*G["Sensorless-mlp"]["caps"]["25"]["BSS_vs_ExtraTrees"]:.1f} to {100*G["Sensorless-mlp"]["caps"]["35"]["BSS_vs_ExtraTrees"]:.1f} percent without sensors (beating regional climatology by over half), while conformal scaling contracts interval widths by {100*(1-W["Full-Telemetry-mlp"]["macro_calibrated_width"]/W["Full-Telemetry-mlp"]["macro_uncalibrated_width"]):.1f} and {100*(1-W["Sensorless-mlp"]["macro_calibrated_width"]/W["Sensorless-mlp"]["macro_uncalibrated_width"]):.1f} percent down to {W["Full-Telemetry-mlp"]["macro_calibrated_width"]:.2f} and {W["Sensorless-mlp"]["macro_calibrated_width"]:.2f} kg N ha$^{{-1}}$ and cuts downstream profit ranking regret by {100*(1-G["Full-Telemetry-mlp"]["partial_profit_ranking_regret_EUR_ha"]/G["Full-Telemetry-mlp"]["ExtraTrees_regret_EUR_ha"]):.1f} and {100*(1-G["Sensorless-mlp"]["partial_profit_ranking_regret_EUR_ha"]/G["Sensorless-mlp"]["ExtraTrees_regret_EUR_ha"]):.1f} percent.'
)
r31_p3_zh = (
    '2010至2014年独立开发集上的共形校准验证了轻量神经网络代理在闭环决策前的显著概率优势（图2d）。'
    f'完整遥测与无传感器两套轨道的宏平均90%区间覆盖率分别达到{100*G["Full-Telemetry-mlp"]["Dev_crossyear_macro_90pct_coverage"]:.2f}%与{100*G["Sensorless-mlp"]["Dev_crossyear_macro_90pct_coverage"]:.2f}%（尽管完整遥测在西澳存在{100*G["Full-Telemetry-mlp"]["by_region"]["australia_wa_perth"]["crossyear_coverage"]:.2f}%的区域异质性）。'
    f'图2d下栏同时证明，在25至50千克红线梯度上代理模型对极端随机树的Brier技巧稳定高出{100*G["Full-Telemetry-mlp"]["caps"]["25"]["BSS_vs_ExtraTrees"]:.1f}%至{100*G["Full-Telemetry-mlp"]["caps"]["50"]["BSS_vs_ExtraTrees"]:.1f}%（完整）及{100*G["Sensorless-mlp"]["caps"]["25"]["BSS_vs_ExtraTrees"]:.1f}%至{100*G["Sensorless-mlp"]["caps"]["35"]["BSS_vs_ExtraTrees"]:.1f}%（无传感器），共形校准更将区间物理宽度分别收窄{100*(1-W["Full-Telemetry-mlp"]["macro_calibrated_width"]/W["Full-Telemetry-mlp"]["macro_uncalibrated_width"]):.1f}%与{100*(1-W["Sensorless-mlp"]["macro_calibrated_width"]/W["Sensorless-mlp"]["macro_uncalibrated_width"]):.1f}%，并将下游部分收益排序遗憾大举压低{100*(1-G["Full-Telemetry-mlp"]["partial_profit_ranking_regret_EUR_ha"]/G["Full-Telemetry-mlp"]["ExtraTrees_regret_EUR_ha"]):.1f}%与{100*(1-G["Sensorless-mlp"]["partial_profit_ranking_regret_EUR_ha"]/G["Sensorless-mlp"]["ExtraTrees_regret_EUR_ha"]):.1f}%。'
)
add_block('r31-p3', r31_p3_zh, r31_p3_en, figs=['@fig reports/phase8/figures/fig2-g1.png | reports/phase8/figures/captions-v12/fig2.txt | Fig. 2'])

# 3.2 Experimental Setup and Parameter Configuration (~190 EN words)
add_block('sec-r32', '### 3.2 实验设置与参数配置', '### 3.2 Experimental Setup and Parameter Configuration')

r32_setup_en = (
    'To test whether lightweight domain-coupled intelligence matches or surpasses heavy tree ensembles and on-policy reinforcement learning without real-time field sensors, AgroMAS-Global (Soft-Coupled) is evaluated against three controller paradigms sharing identical 220 kg N ha$^{-1}$ budgets and legal action masks. '
    'First, reference sequential and agronomic policies encompass a matched sensorless proximal policy optimization agent (20,616 trainable weights across actor and critic) and the full-telemetry agronomic split rule DVS-N2 [baja2025, ppo2017]. '
    'Second, surrogate baselines substitute 64-tree extremely randomized ensembles occupying 275.52 MB serialized storage per model (1,723,434 tree split nodes), weather-only networks and linear regression baselines for the compact three-seed twin neural ensemble (13,155 weights and 55.4 KB per checkpoint, totaling 166.3 KB), delivering a 1,696-fold serialized memory footprint reduction alongside 38.5 percent higher closed-loop compliance than tree ensembles, as well as 36.2 percent fewer trainable weights per network than the reinforcement learning policy (noting that neural parameters and tree split nodes are architectural counterparts rather than directly equivalent capacity metrics). '
    'Third, degraded planner variants isolate strict hard-tail pruning (Tier2-Composite), open-loop static scheduling, greedy single-step selection and profit-only bare relaxation. '
    'Statistical comparisons enforce identical seed averaging followed by full-family Holm-adjusted exact sign tests and equal-region bootstrap confidence intervals.'
)
r32_setup_zh = (
    '为公正比较轻量化多专职协同架构与重型树集成及在线强化学习在无传感器条件下的真实差距，所有对照基线均在相同的每公顷220千克总预算与合法动作掩码下同步考核。'
    '第一类主流参照包括同信息屏蔽传感器的匹配PPO智能体（含20,616个可训练权重）以及享有完整遥测信息的农艺分期规则DVS-N2 [baja2025, ppo2017]。'
    '第二类替代代理基线把本文三随机种子冻结轻量神经网络集成（每成员13,155权重、磁盘仅55.4千字节，三成员合计166.3千字节）替换为单模型序列化达275.52兆字节（含1,723,434个分裂节点）的64棵极端随机树集成、纯气象代理及线性模型。神经网络与树节点属于不同模型范式而非可直接折算的容量指标，但在真实部署存储上本文实现逾1,696倍压缩的同时仍比树代理闭环达标高出38.5%，单网络可训练权重亦较PPO减少36.2%。'
    '第三类退化规划变体涵盖硬截断复合筛选、开环计划、单步贪心与仅保留收益的裸回退机制。所有检验均在农场年内部聚合多种子均值后开展统一Holm校正符号检验。'
)
add_block('r32-setup', r32_setup_zh, r32_setup_en)

# 3.3 Comparative Experiments — PRIMARY CORE (~560 EN words, Table 2 + Fig. 3a-d deep panel-by-panel walkthrough)
add_block('sec-r33', '### 3.3 对比实验', '### 3.3 Comparative Experiments')

r33_comp1_en = (
    'Across mild historical baselines, multi-specialist coupling matches full-budget reference controllers in overall frequency while preventing uncoupled soil-mining collapses and outperforming alternative surrogates and degraded planners (Table 2 and Fig. 3). '
    f'Under these stationary historical conditions, sensorless Soft-Coupled control ({100*soft["region_equal"]["joint"]:.2f} percent) remains statistically indistinguishable from matched sensorless PPO ({100*ppo["region_equal"]["joint"]:.2f} percent, paired difference minus 1.94 percentage points, 95 percent interval minus 8.55 to 4.09 percentage points, 46 of 52 farm-years tied, Holm p equals {ppo_vs["Holm_sign_p_full_family"]:.2f}) and full-telemetry DVS-N2 ({100*dvs["region_equal"]["joint"]:.2f} percent, 47 of 52 tied), confirming parity under benign stationary weather prior to stress differentiation. On the small-sample seven-season single-site Wageningen benchmark (where statistical power is inherently constrained by n equals 7), Soft-Coupled attains 28.57 percent compliance and 1457.25 EUR ha$^{{-1}}$ versus 19.05 percent and 1446.51 EUR ha$^{{-1}}$ for PPO and zero percent for DVS-N2. '
    f'Crucially, compared with profit-only bare relaxation ({100*bare["region_equal"]["joint"]:.2f} percent), Soft-Coupled multiplies equal-region compliance 6.27-fold. While bare fallback, open-loop scheduling and weather-only control report mean apparent NUE values exceeding 1.0 (11.56, 1.68 and 1.31, Table 2), this occurs mathematically because EUNEP apparent NUE divides grain nitrogen harvested partly from mineralized native soil humus by minimal external inputs ($I_N$), producing inflated nominal partial profit ({bare["region_equal"]["partial_profit"]:.2f} versus {soft["region_equal"]["partial_profit"]:.2f} EUR ha$^{{-1}}$ under bare fallback) strictly through unpriced soil nitrogen mining ($S_N$ minus 33.78 kg N ha$^{{-1}}$). '
    f'Under identical sensorless inputs, Soft-Coupled also achieves relative compliance gains of 38.5 percent over ExtraTrees ({100*et_soft["region_equal"]["joint"]:.2f} percent), 39.8 percent over weather-only surrogates ({100*weath_soft["region_equal"]["joint"]:.2f} percent), 73.4 percent over linear models ({100*lin_soft["region_equal"]["joint"]:.2f} percent), 25.9 percent over open-loop schedules ({100*open_lp["region_equal"]["joint"]:.2f} percent) and 52.6 percent over greedy single-step policies ({100*greedy["region_equal"]["joint"]:.2f} percent).'
)
r33_comp1_zh = (
    '在温和历史单点基准上，多专职耦合架构与充分预算参照策略保持整体统计等效，同时彻底阻断无护栏土壤透支并显著领先替代代理与退化规划（表2与图3）。'
    f'平顺历史条件下无传感器软耦合（{100*soft["region_equal"]["joint"]:.2f}%）与同信息PPO（{100*ppo["region_equal"]["joint"]:.2f}%，配对差负1.94个百分点，95%区间负8.55至4.09个百分点，52年中有46年一致，Holm校正p等于{ppo_vs["Holm_sign_p_full_family"]:.2f}）及完整遥测DVS-N2（{100*dvs["region_equal"]["joint"]:.2f}%，47年一致）处于统计等效区间，在独立小样本7季瓦赫宁根基准（受限于n=7检验功效）取得28.57%（收益1457.25欧元）对比PPO的19.05%（1446.51欧元）及DVS-N2的零达标。'
    f'尤为关键的是，软耦合联合达标率较仅收益裸回退（{100*bare["region_equal"]["joint"]:.2f}%）跃升6.27倍。表2中仅收益回退（11.56）、开环（1.68）与纯气象（1.31）的表观NUE均高于1.0，这正源自EUNEP分母仅计入极低外源投入而籽粒移出兼含原生土壤矿化氮的物理机制，导致裸回退靠未计价土壤腐殖质矿化掠夺（净盈余负33.78千克）虚增每公顷{bare["region_equal"]["partial_profit"]:.2f}欧元的账面部分收益（对比软耦合{soft["region_equal"]["partial_profit"]:.2f}欧元）。'
    f'同等无传感器条件下，软耦合相对极端随机树、纯气象、线性、开环与单步贪心分别取得25.9%至73.4%的相对达标率优势。'
)
add_block('r33-p1', r33_comp1_zh, r33_comp1_en)

r33_comp2_en = (
    'Dissecting Fig. 3a to d reveals the exact statistical and sub-seasonal mechanisms driving these comparative rankings. '
    'In phase space (Fig. 3a), profit-only fallback shifts dramatically leftward into negative surplus (mean minus 33.78 kg N ha$^{-1}$) via unfertilized outliers along the vertical axis, whereas Soft-Coupled, PPO and DVS-N2 align their 1-sigma covariance ellipses along the central safety wedge. '
    'Nested policy bars (Fig. 3b) uncover why joint compliance clusters around 25 to 27 percent even for leading methods. Across ten controllers, most achieve 44 to 51 percent safe apparent efficiency and 52 to 58 percent satisfaction on at least one boundary, yet intersecting both bounds drops compliance sharply unless continuous corridor gradients rank borderline choices (giving Soft-Coupled a 16.1 percent relative lead over rigid Tier2-Composite at 21.58 percent and maintaining substantial distance above profit-only relaxation whose either-bound score stalls at 23 percent). '
    'On 349-day Western Australia dynamics (Fig. 3c), Soft-Coupled deploys a front-loaded decaying split schedule (100, 60 and 20 kg N ha$^{-1}$ across S1 to S3) immediately after early-season winter rainfall near day 30, rebuilding soil mineral nitrogen up to roughly 245 kg N ha$^{-1}$ to sustain tiller and stem-elongation uptake while avoiding excessive late-season leaching. Although back-loaded PPO and DVS-N2 (20, 80 and 80 kg N ha$^{-1}$) reach identical total executed nitrogen (180 kg N ha$^{-1}$) and final surplus (41.5 kg N ha$^{-1}$) with slightly lower cumulative seasonal loss (26.90 versus 31.45 kg N ha$^{-1}$), bare fallback applies zero doses throughout, draining mineral nitrogen nearly to exhaustion after S1 and forcing extreme mining (efficiency 40.50, surplus minus 138.2 kg N ha$^{-1}$). '
    'Across continents, Soft-Coupled translates these mechanics into distinct physical strategies, ranging from active full-season fertilization in Perth (177.3 kg N ha$^{-1}$) and Lelystad (220.0 kg N ha$^{-1}$) to cautious rainfed restraint in Wichita (77.5 kg N ha$^{-1}$) and unanimous zero topdressing above rich basal nitrogen (171.0 kg N ha$^{-1}$) in Luancheng. In Luancheng, 49.0 kg N ha$^{-1}$ of legal topdressing headroom (10, 20 and 40 kg N ha$^{-1}$ choices) remains unmasked by the 220 kg N ha$^{-1}$ cap, yet the controller withholds extra fertilizer because pre-sowing basal input and soil mineralization already saturate modeled grain nitrogen demand. '
    'Aligned bilateral rainclouds (Fig. 3d and Supplementary Figs. S4 to S5) corroborate that Soft-Coupled truncates both extreme mining outliers above 0.90 and excess surplus tails cleanly.'
)
r33_comp2_zh = (
    '逐图拆解图3a至d可以透视上述综合排序背后的统计结构与季内水肥互作机理。'
    '图3a相空间中，仅收益裸回退因大量零施氮离群点向左大幅坍缩（均值净盈余低至每公顷负33.78千克），而软耦合、PPO与DVS-N2的标准差椭圆均严密契合双侧安全楔区。'
    '图3b嵌套柱揭示了各方法均停留在两成五至两成七的本质交集瓶颈，十种控制器中主流策略在单一安全效率（44%至51%）及单边合格（52%至58%）上均已过半，唯有连续保留走廊梯度的软耦合能够在严格双交集中比僵化硬筛选（Tier2复合，21.58%）相对多锁定16.1%的有效方案，同时大幅拉开与单边仅达23%的裸回退策略差距。'
    '图3c西澳珀斯349天连续演替轨迹从微观上印证了策略分化机制，软耦合在早期冬季强降雨过后采取前重后轻的递减分期配置（S1至S3依次为100、60与20千克），迅速将剖面矿质氮提升至约每公顷245千克峰值以充分满足拔节期旺长需求，与后重型PPO及DVS-N2（20、80、80千克）虽呈现差异化季内矿质氮缓冲与累积损失过程（31.45对比26.90千克）却在同等总施氮（180千克）及相同季末盈余（41.5千克）下实现等效收口。反观仅收益策略全季零追肥，生生抽干土壤矿质氮并酿成40.50的极端表观透支。'
    '这种物理适应性同样体现在跨区施氮分化上（珀斯与莱利斯塔德积极施氮177.3与220.0千克，威奇托旱作压缩至77.5千克，高底肥栾城虽尚余每公顷49.0千克合法追肥额度与三档正剂量可选，但因高额基肥已饱和模拟吸氮需求，控制器一致主动停施以避免徒增盈余），并反映在图3d与附图S4至S5紧密收拢的双尾云雨分布之中。'
)
add_block('r33-p2', r33_comp2_zh, r33_comp2_en)

tbl2_zh = (
    '表2 历史基准条件（每公顷40千克氮红线、常规肥价、零补贴）下11类对照配置五区等权绩效比较。\n'
    '| 策略架构 | 观测轨道 | 联合达标率（%） | 部分收益（欧元每公顷） | 表观NUE | 净盈余（千克氮每公顷） | 原生氮损失（千克氮每公顷） |\n'
    '|---|---|---:|---:|---:|---:|---:|\n'
    f'| 匹配掩码PPO | 无传感器 | {100*ppo["region_equal"]["joint"]:.2f} | {ppo["region_equal"]["partial_profit"]:.2f} | {ppo["region_equal"]["NUE"]:.2f} | {ppo["region_equal"]["S_N"]:.2f} | {ppo["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| 农艺分期DVS-N2 | 完整遥测 | {100*dvs["region_equal"]["joint"]:.2f} | {dvs["region_equal"]["partial_profit"]:.2f} | {dvs["region_equal"]["NUE"]:.2f} | {dvs["region_equal"]["S_N"]:.2f} | {dvs["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| 软耦合神经网络 | 无传感器 | {100*soft["region_equal"]["joint"]:.2f} | {soft["region_equal"]["partial_profit"]:.2f} | {soft["region_equal"]["NUE"]:.2f} | {soft["region_equal"]["S_N"]:.2f} | {soft["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| 严格硬复合神经网络 | 完整遥测 | {100*full_hard["region_equal"]["joint"]:.2f} | {full_hard["region_equal"]["partial_profit"]:.2f} | {full_hard["region_equal"]["NUE"]:.2f} | {full_hard["region_equal"]["S_N"]:.2f} | {full_hard["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| 严格硬复合神经网络 | 无传感器 | {100*hard["region_equal"]["joint"]:.2f} | {hard["region_equal"]["partial_profit"]:.2f} | {hard["region_equal"]["NUE"]:.2f} | {hard["region_equal"]["S_N"]:.2f} | {hard["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| 静态开环神经网络 | 无传感器 | {100*open_lp["region_equal"]["joint"]:.2f} | {open_lp["region_equal"]["partial_profit"]:.2f} | {open_lp["region_equal"]["NUE"]:.2f} | {open_lp["region_equal"]["S_N"]:.2f} | {open_lp["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| 极端随机树代理 | 无传感器 | {100*et_soft["region_equal"]["joint"]:.2f} | {et_soft["region_equal"]["partial_profit"]:.2f} | {et_soft["region_equal"]["NUE"]:.2f} | {et_soft["region_equal"]["S_N"]:.2f} | {et_soft["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| 纯气象代理对照 | 无传感器 | {100*weath_soft["region_equal"]["joint"]:.2f} | {weath_soft["region_equal"]["partial_profit"]:.2f} | {weath_soft["region_equal"]["NUE"]:.2f} | {weath_soft["region_equal"]["S_N"]:.2f} | {weath_soft["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| 近视单步贪心控制 | 无传感器 | {100*greedy["region_equal"]["joint"]:.2f} | {greedy["region_equal"]["partial_profit"]:.2f} | {greedy["region_equal"]["NUE"]:.2f} | {greedy["region_equal"]["S_N"]:.2f} | {greedy["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| 线性回归代理对照 | 无传感器 | {100*lin_soft["region_equal"]["joint"]:.2f} | {lin_soft["region_equal"]["partial_profit"]:.2f} | {lin_soft["region_equal"]["NUE"]:.2f} | {lin_soft["region_equal"]["S_N"]:.2f} | {lin_soft["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| 归档仅收益裸回退 | 无传感器 | {100*bare["region_equal"]["joint"]:.2f} | {bare["region_equal"]["partial_profit"]:.2f} | {bare["region_equal"]["NUE"]:.2f} | {bare["region_equal"]["S_N"]:.2f} | {bare["region_equal"]["Native_N_loss"]:.2f} |'
)
tbl2_en = (
    'Table 2 Equal-region benchmark comparison across control architectures under the historical reference setting (cap 40 kg N ha$^{-1}$, baseline fertilizer price, zero subsidy).\n'
    '| Controller architecture | Observation track | Joint compliance (%) | Partial profit (EUR ha$^{-1}$) | Apparent NUE | Surplus $S_N$ (kg N ha$^{-1}$) | Native N loss (kg N ha$^{-1}$) |\n'
    '|---|---|---:|---:|---:|---:|---:|\n'
    f'| Matched Sensorless PPO | Sensorless | {100*ppo["region_equal"]["joint"]:.2f} | {ppo["region_equal"]["partial_profit"]:.2f} | {ppo["region_equal"]["NUE"]:.2f} | {ppo["region_equal"]["S_N"]:.2f} | {ppo["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| DVS-N2 split rule | Full-Telemetry | {100*dvs["region_equal"]["joint"]:.2f} | {dvs["region_equal"]["partial_profit"]:.2f} | {dvs["region_equal"]["NUE"]:.2f} | {dvs["region_equal"]["S_N"]:.2f} | {dvs["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| Soft-Coupled neural | Sensorless | {100*soft["region_equal"]["joint"]:.2f} | {soft["region_equal"]["partial_profit"]:.2f} | {soft["region_equal"]["NUE"]:.2f} | {soft["region_equal"]["S_N"]:.2f} | {soft["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| Tier2-Composite neural | Full-Telemetry | {100*full_hard["region_equal"]["joint"]:.2f} | {full_hard["region_equal"]["partial_profit"]:.2f} | {full_hard["region_equal"]["NUE"]:.2f} | {full_hard["region_equal"]["S_N"]:.2f} | {full_hard["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| Tier2-Composite neural | Sensorless | {100*hard["region_equal"]["joint"]:.2f} | {hard["region_equal"]["partial_profit"]:.2f} | {hard["region_equal"]["NUE"]:.2f} | {hard["region_equal"]["S_N"]:.2f} | {hard["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| Open-loop neural | Sensorless | {100*open_lp["region_equal"]["joint"]:.2f} | {open_lp["region_equal"]["partial_profit"]:.2f} | {open_lp["region_equal"]["NUE"]:.2f} | {open_lp["region_equal"]["S_N"]:.2f} | {open_lp["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| ExtraTrees surrogate | Sensorless | {100*et_soft["region_equal"]["joint"]:.2f} | {et_soft["region_equal"]["partial_profit"]:.2f} | {et_soft["region_equal"]["NUE"]:.2f} | {et_soft["region_equal"]["S_N"]:.2f} | {et_soft["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| Weather-only surrogate | Sensorless | {100*weath_soft["region_equal"]["joint"]:.2f} | {weath_soft["region_equal"]["partial_profit"]:.2f} | {weath_soft["region_equal"]["NUE"]:.2f} | {weath_soft["region_equal"]["S_N"]:.2f} | {weath_soft["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| Greedy-frozen selector | Sensorless | {100*greedy["region_equal"]["joint"]:.2f} | {greedy["region_equal"]["partial_profit"]:.2f} | {greedy["region_equal"]["NUE"]:.2f} | {greedy["region_equal"]["S_N"]:.2f} | {greedy["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| Linear surrogate | Sensorless | {100*lin_soft["region_equal"]["joint"]:.2f} | {lin_soft["region_equal"]["partial_profit"]:.2f} | {lin_soft["region_equal"]["NUE"]:.2f} | {lin_soft["region_equal"]["S_N"]:.2f} | {lin_soft["region_equal"]["Native_N_loss"]:.2f} |\n'
    f'| Profit-only fallback | Sensorless | {100*bare["region_equal"]["joint"]:.2f} | {bare["region_equal"]["partial_profit"]:.2f} | {bare["region_equal"]["NUE"]:.2f} | {bare["region_equal"]["S_N"]:.2f} | {bare["region_equal"]["Native_N_loss"]:.2f} |'
)
add_block('tbl-2', tbl2_zh, tbl2_en, figs=['@fig reports/phase8/figures/fig2-p1-regimes.png | reports/phase8/figures/captions-v12/fig3.txt | Fig. 3'])

# 3.4 Multi-Prior Coupling Ablation Experiments — SECONDARY CORE (Concise causal chain, ~230 EN words, Table 3)
add_block('sec-r34', '### 3.4 多先验耦合消融实验', '### 3.4 Multi-Prior Coupling Ablation Experiments')

r34_p1_en = (
    'Single-module ablations distinguish primary safety guardrails whose removal collapses system compliance from finer predictive couplings that govern edge-regime refinements (Table 3 and Supplementary Figs. S1 and S3 to S5). '
    f'Among primary guardrails, stripping the urban eco-safety specialist coupling (both quantile cap screening and surplus distance penalties) lowers joint compliance by 42.9 percent at the 40 kg N ha$^{{-1}}$ limit ({100*soft["region_equal"]["joint"]:.2f} to {100*eco40_s["region_equal"]["joint"]:.2f} percent as mean surplus swells to {eco40_s["region_equal"]["S_N"]:.2f} kg N ha$^{{-1}}$) and by 72.9 percent under stringent 25 kg N ha$^{{-1}}$ limits ({100*full25_f["region_equal"]["joint"]:.2f} to {100*eco25["region_equal"]["joint"]:.2f} percent). Replacing graded soft retention with strict tail pruning triggers empty-set feasibility deadlocks that collapse joint compliance to 0.00 percent in tight Australian seasons, stripping economic corridor penalties drops compliance by 84.0 percent to 4.00 percent via soil mining, and breaking multi-stage continuation into greedy or open-loop scheduling forfeits 20.5 to 34.5 percent relative compliance. '
    'By comparison, removing climate analogue branching yields a modest 1.81 percentage-point reduction in tranquil historical years (19.39 to 17.58 percent, Supplementary Fig. S1) while satellite-anomaly removal reduces cross-continental compliance by 2.50 percentage points (20.39 to 17.89 percent), demonstrating that primary safety comes from bilateral corridor continuation while climate and spatial modules expand adaptability across extremes and unseen continents.'
)
r34_p1_zh = (
    '系统化单模块消融清晰区分了缺失即引发系统崩溃的底层护栏算子与在边界工况提供精密增益的扩展耦合模块（表3与附图S1、S3至S5）。'
    f'在核心安全护栏中，完整摘除城市生态安全专职耦合（同时撤除分位红线过滤与盈余越界距离惩罚）使常规上限达标率骤降42.9%（由{100*soft["region_equal"]["joint"]:.2f}%跌至{100*eco40_s["region_equal"]["joint"]:.2f}%，净盈余升至{eco40_s["region_equal"]["S_N"]:.2f}千克每公顷）并在25千克严苛红线下大跌72.9%，以刚性硬截断替代软耦合在西澳触发可行集空集死锁并将联合达标率直接压至0.00%，撤除经济防透支罚项令历史达标跌去84.0%至4.00%，而退化为单步贪心或开环规划则各自丧失20.5%至34.5%的相对表现。'
    '相比之下，在平顺历史年份剥离气候类比产生1.81个百分点缓降（19.39%降至17.58%，附图S1），跨洲盲测移除卫星距平回落2.50个百分点（20.39%降至17.89%），证明双侧连续动态规划构成了全系统抗风险底座，而气候分支与空间适配模块则分别在升温高压与跨洲冷启动情景中释放边界延展价值。'
)
add_block('r34-p1', r34_p1_zh, r34_p1_en)

tbl3_zh = (
    '表3 针对核心科研缺口的反事实模块消融诊断汇总。\n'
    '| 对应机理 | 消融操作 | 配对验证范围 | 完整版达标率（%） | 消融后达标率（%） | 主导失效后果 |\n'
    '|---|---|---|---:|---:|---|\n'
    '| 气候类比预测 | 移除气候专职模块 | 同年配对基准 n=31 | 19.39 | 17.58 | 丧失旱涝先兆前瞻调控能力 |\n'
    '| 非预知动态续策 | 退化为单步贪心 | 历史无传感器 n=52 | 25.06 | 16.42 | 割裂三阶段跨期氮素再分配 |\n'
    '| 城市生态红线 | 移除生态安全专职耦合 | 历史红线 cap40 | 25.06 | 14.30 | 净盈余跃升至34.95千克氮超标 |\n'
    '| 连续走廊保留 | 改用刚性硬尾部裁决 | 西澳开发集 cap25 | 20.00 | 0.00 | 可行集归零触发无肥僵局 |\n'
    '| 双侧经济防线 | 退化为仅收益排序 | 历史无传感器 n=52 | 25.06 | 4.00 | 表观NUE飙升至11.56严重耗土 |\n'
    '| 因果卫星距平 | 移除站点距平先验 | 跨洲盲测 n=40 | 20.39 | 17.89 | 跨洲准入由60.00%回退至土壤基线 |'
)
tbl3_en = (
    'Table 3 Counterfactual component ablation synthesis identifying exact operational failure mechanisms.\n'
    '| Target coupling | Ablation intervention | Matched evaluation scope | Full compliance (%) | Ablated compliance (%) | Dominant failure mechanism |\n'
    '|---|---|---|---:|---:|---|\n'
    '| Climate branching | Remove climate specialist | Year-matched baseline n=31 | 19.39 | 17.58 | Loses storm and drought anticipation |\n'
    '| Dynamic planning | Collapse to greedy selector | Historical sensorless n=52 | 25.06 | 16.42 | Breaks cross-stage reallocation |\n'
    '| Eco-safety cap | Remove eco-safety coupling | Historical sensorless cap 40 | 25.06 | 14.30 | Surplus jumps to 34.95 kg N ha$^{-1}$ |\n'
    '| Soft corridor | Strict hard-tail pruning | Dev Australia cap 25 | 20.00 | 0.00 | Empty candidate sets lock zero dose |\n'
    '| Bilateral guard | Profit-only bare fallback | Historical sensorless n=52 | 25.06 | 4.00 | Soil mining spikes NUE to 11.56 |\n'
    '| Satellite prior | Remove station anomaly | Cross-region sensorless n=40 | 20.39 | 17.89 | Drops admission from 60.00% to baseline |'
)
add_block('tbl-3', tbl3_zh, tbl3_en)

# 3.5 Coupling Mechanism and Transfer Sensitivity Experiments (~390 EN words, Fig. 4a-d deep panel-by-panel walkthrough)
add_block('sec-r35', '### 3.5 耦合机理与跨区迁移敏感性实验', '### 3.5 Coupling Mechanism and Transfer Sensitivity Experiments')

r35_p1_en = (
    f'Sensitivity tests across temporal leave-one-year-out and cross-continental leave-one-region-out holdouts (40 unpooled post-2019 seasons) answer the second scientific question by defining exact empirical limits for causal satellite adaptation without field sensors (Fig. 4). '
    f'In Fig. 4a, left-hand held-out surplus rainclouds pair smooth spatial holdout densities against temporal interquartile spans, while right-hand dumbbells trace compliance shifts alongside independent Dutch benchmark points. Decoupling station-demeaned satellite anomalies from static soil baselines (Full64) lifts temporal compliance to {100*p2_ly_f["region_equal"]["joint"]:.2f} percent (beating static physical priors at {100*p2_ly_s["region_equal"]["joint"]:.2f} percent and satellite-augmented trees at {100*p2_ly_e["region_equal"]["joint"]:.2f} percent) and preserves {100*p2_lr_f["region_equal"]["joint"]:.2f} versus {100*p2_lr_s["region_equal"]["joint"]:.2f} percent on unseen continents, whereas weather-only priors drop to zero percent on historical public Dutch seasons (Fig. 4a right). '
    f'Simultaneously, world-equal closed-loop anomaly admission climbs from zero under un-centered vectors to {100*pr_lr_f["prior_acceptance_world_equal"]:.2f} percent globally ({100*pr_lr_f["prior_acceptance_rows"]:.2f} percent of prediction rows).'
)
r35_p1_zh = (
    f'在严格不混池的40个2019年后农场年上开展的跨年（LOYO）与跨洲盲测（LORO）敏感性试验，正面回答了第二个核心科学问题并划定了无传感器空间先验的适用疆界（图4）。'
    f'图4a左栏盈余云雨图将跨洲平滑密度与跨年中位四分位间距对照，右栏达标率哑铃联动呈现了公开荷兰站外推表现。剥离静态土壤与站点去均值卫星距平的Full64适配器将跨年联合达标率抬升至{100*p2_ly_f["region_equal"]["joint"]:.2f}%（高于纯物理土壤基线{100*p2_ly_s["region_equal"]["joint"]:.2f}%及树模型{100*p2_ly_e["region_equal"]["joint"]:.2f}%），并在跨洲外折保持{100*p2_lr_f["region_equal"]["joint"]:.2f}%对{100*p2_lr_s["region_equal"]["joint"]:.2f}%的正向优势（反观纯气象在荷兰公开年跌至零），同时将闭环世界等权先验准入率从零跃升至{100*pr_lr_f["prior_acceptance_world_equal"]:.2f}%（预测行准入{100*pr_lr_f["prior_acceptance_rows"]:.2f}%）。'
)
add_block('r35-p1', r35_p1_zh, r35_p1_en)

r35_p2_en = (
    'Projecting temporal-to-spatial transfer trajectories jointly in RMSE-versus-compliance space paired with 95 percent paired intervals exposes a decisive decoupling between representation acceptance and quantitative prediction error (Fig. 4b and Supplementary Fig. S6). '
    'While neural adapters hold the lowest grain nitrogen RMSE (21.11 to 22.75 kg N ha$^{-1}$ versus 25.71 to 27.76 for weather-only and 26.67 to 26.82 for linear models), cross-continental anomaly admission leaves world-equal mean squared error slightly above static soil baselines (517.65 versus 505.15 kg$^2$ ha$^{-2}$), yielding neutral paired Holm-corrected intervals crossing zero (Holm p equals 1.00). '
    'Regional phase-shift vectors (Fig. 4c) and combined ellipses (Fig. 4d) diagnose the underlying agronomic constraints. Under unseen spatial transfer, Perth drifts slightly across the 40 kg N ha$^{-1}$ border (62.5 to 37.5 percent compliance at 37.5 percent admission), Kansas holds inside the safe box (55.6 to 33.3 percent, 77.8 percent admission) and Lelystad preserves 20.0 percent border performance (80.0 percent admission), whereas Beauce remains fixed inside organic mineralization excess (efficiency 1.18, 100.0 percent admission) and Luancheng stays confined near 102.3 kg N ha$^{-1}$ surplus where 11.1 percent spatial acceptance automatically falls back to physical soil safety priors across all 54 windows.'
)
r35_p2_zh = (
    '图4b的二维RMSE对达标泛化矢量轨迹与底端配对95%置信区间（Holm校正p=1.00）进一步阐明了先验准入并不等同于定量误差自动消减（详见附图S6）。'
    '虽然神经网络适配器始终占据最低预测误差前端（RMSE每公顷21.11至22.75千克对比纯气象25.71至27.76与线性26.67至26.82千克），但跨洲盲测时Full64均方误差（517.65）仍略高于静态土壤基线（505.15），令配对达标净提升落在统计中性区内。'
    '图4c区域迁移相矢量与图4d椭圆对照揭示了背后的地球物理约束差异，跨洲外推下珀斯穿越40千克红线（62.5%降至37.5%）、威奇托守住安全箱（55.6%至33.3%，准入77.8%）、莱利斯塔德稳守20.0%边界（准入80.0%），而巴黎盆地受困于1.18高矿化表观效率（准入100.0%），华北栾城则在102.3千克高盈余象限将超界准入安全回落至11.1%从而严守静态物理底线。'
)
add_block('r35-p2', r35_p2_zh, r35_p2_en, figs=['@fig reports/phase8/figures/fig3-p2-transfer.png | reports/phase8/figures/captions-v12/fig4.txt | Fig. 4'])

# Section 4: Progressive 3-Stage Stress & Nutrient Accounting (~820 EN words)
add_block('sec-stress', '## 4 多系统压力验证与氮碳收支核算', '## 4 Multi-System Stress Verification and Nutrient Accounting')

add_block('sec-s41', '### 4.1 气候、流域与市场耦合压力评估', '### 4.1 Coupled Climate, Watershed, and Market Stress Evaluation')

s41_p1_en = (
    'Crossing climate warming scenarios, watershed surplus ceilings, fertilizer price shocks and green subsidies across 180 factorial configurations demonstrates that policy ranking depends strongly on coupled threshold-warming regimes rather than uniform dominance (Fig. 5a to c and Supplementary Fig. S7). '
    'Across the complete 180-cell space, Soft-Coupled control maintains a modest global average margin of 0.58 percentage points over matched PPO (40 wins, 93 ties and 47 losses), confirming that conservative abstention remains competitive in tranquil historical extremes. '
    f'Within the operational policy manifold of Fig. 5a, however, the smoothed iso-advantage surface and overlaid three-dot economic clusters (baseline price zero subsidy at left, doubled price zero subsidy at top, baseline price 50 EUR subsidy at right) uncover a broad positive plateau centered along the 40 kg N ha$^{{-1}}$ ceiling as warming intensifies. Because elevated temperatures accelerate phenological progression and compress safe topdressing windows while doubled fertilizer prices push uncoupled policies toward excessive restraint, de-shifted weather-analogue planning outperforms PPO by 5.15 percentage points on average at 1.8 degrees Celsius warming (reaching {100*soft_w18_40["region_equal"]["joint"]:.2f} percent baseline and {100*soft_2x_w18["region_equal"]["joint"]:.2f} percent under doubled fertilizer prices) and expands that lead to 5.61 percentage points without a single loss cell at 3.5 degrees Celsius ({100*soft_w35_40["region_equal"]["joint"]:.2f} versus {100*ppo_w35_40["region_equal"]["joint"]:.2f} percent for PPO and {100*dvs_w35_40["region_equal"]["joint"]:.2f} percent for DVS-N2), anchored by Australian, Dutch and severe-warming US adaptation.'
)
s41_p1_zh = (
    '囊括气候增温、氮盈余红线、肥价翻倍与绿色补贴的180格全因子压力试验表明，优势控制策略并非单调通吃，而是由关键生态红线与增温强度共同界定（图5a至c与附图S7）。'
    '尽管在全空间180单元总览层面软耦合仅微弱领先PPO约0.58个百分点（40胜、93平、47负），表明保守停施策略在平顺历史极端边界仍具竞争力，图5a的二维连续等值面与经济三点群（左侧代表1倍肥价零补贴、上方代表2倍高肥价、右侧代表50欧元补贴）清晰勾勒出每公顷40千克氮主流红线随增温攀升的强正优势高原。'
    f'由于升温加快发育节律并压缩追肥窗口、高肥价又易诱使缺乏护栏的对照陷入过度减施，去升温偏移分支规划在40千克红线上于1.8与3.5摄氏度平均领先PPO达5.15与5.61个百分点，其中3.5摄氏度更保持零负单元完胜（8胜、7平、0负，达标率{100*soft_w35_40["region_equal"]["joint"]:.2f}%对比PPO的{100*ppo_w35_40["region_equal"]["joint"]:.2f}%与农艺规则{100*dvs_w35_40["region_equal"]["joint"]:.2f}%），核心驱动源自西澳、荷兰及强升温下美国麦区的稳健保产调氮。'
)
add_block('s41-p1', s41_p1_zh, s41_p1_en)

s41_p2_en = (
    f'Threshold crossover lines alongside embedded 45-cell win-tie-loss bars in Fig. 5b corroborate this bifurcation. Wins peak at cap 40 (15 wins, 23 ties and only 7 losses), while under 1.8 degrees Celsius warming at the tight 25 kg N ha$^{{-1}}$ ceiling Soft-Coupled maintains {100*soft_w18_25["region_equal"]["joint"]:.2f} percent compliance (nearly triple DVS-N2 at {100*dvs_w18_25["region_equal"]["joint"]:.2f} percent), whereas mild historical 25 and relaxed 50 kg N ha$^{{-1}}$ cells favor PPO slightly via conservative abstention. '
    f'Under doubled fertilizer prices (Supplementary Fig. S3), Soft-Coupled sustains leading compliance across historical ({100*soft_2x_hist["region_equal"]["joint"]:.2f} versus {100*ppo_2x_hist["region_equal"]["joint"]:.2f} percent), 1.8 degrees Celsius ({100*soft_2x_w18["region_equal"]["joint"]:.2f} versus {100*ppo_2x_w18["region_equal"]["joint"]:.2f} percent) and 3.5 degrees Celsius ({100*soft_2x_w35["region_equal"]["joint"]:.2f} versus {100*ppo_2x_w35["region_equal"]["joint"]:.2f} percent) stress, and leave-one-region-out sensitivity dumbbells (Fig. 5c) confirm strictly positive cap-40 doubled-price gains regardless of which single breadbasket is dropped.'
)
s41_p2_zh = (
    f'图5b的阈值交叉曲线与嵌入式45格胜平负统计条从定量角度确认了这一机制，软耦合在40千克红线赢面最大化（15胜、23平、仅7负），在1.8摄氏度叠加25千克严苛红线下仍维持{100*soft_w18_25["region_equal"]["joint"]:.2f}%达标率（近三倍于DVS-N2的{100*dvs_w18_25["region_equal"]["joint"]:.2f}%），而在平顺历史极严或宽松端点保守型PPO凭借高频停施微弱占优。'
    f'图5c的逐区留一敏感哑铃与附图S3进一步证实在每公顷40千克红线遇化肥价格翻倍冲击时，软耦合在历史（{100*soft_2x_hist["region_equal"]["joint"]:.2f}%对比{100*ppo_2x_hist["region_equal"]["joint"]:.2f}%）、1.8摄氏度（{100*soft_2x_w18["region_equal"]["joint"]:.2f}%对比{100*ppo_2x_w18["region_equal"]["joint"]:.2f}%）与3.5摄氏度（{100*soft_2x_w35["region_equal"]["joint"]:.2f}%对比{100*ppo_2x_w35["region_equal"]["joint"]:.2f}%）全线稳健领跑，任意剔除单一产区仍全员位于正收益半轴。'
)
add_block('s41-p2', s41_p2_zh, s41_p2_en)

add_block('sec-s42', '### 4.2 绿色补贴政策响应分析', '### 4.2 Green Subsidy Policy Response Analysis')

s42_p1_en = (
    'Tracing directed multi-objective trajectories in partial profit versus joint compliance across compliance subsidies from zero to 200 EUR ha$^{-1}$ quantifies concrete conditions under which uncalibrated financial incentives misalign controller behavior (Fig. 5d). '
    f'Under 1.8 degrees Celsius warming, ecological incentives create an optimal Pareto inflection star at 100 EUR ha$^{{-1}}$ reaching {100*w18_s100["region_equal"]["joint"]:.2f} percent compliance alongside {w18_s100["region_equal"]["partial_profit"]:.2f} EUR ha$^{{-1}}$ profit without triggering marginal surplus overshoot. '
    f'Under historical climate and severe 3.5 degrees Celsius warming, however, rewarding uncalibrated prior joint probabilities expands farm profit monotonically (to {hist_s200["region_equal"]["partial_profit"]:.2f} and {w35_s200["region_equal"]["partial_profit"]:.2f} EUR ha$^{{-1}}$) while nudging realized compliance downward (25.06 to {100*hist_s200["region_equal"]["joint"]:.2f} percent and {100*soft_w35_40["region_equal"]["joint"]:.2f} to {100*w35_s200["region_equal"]["joint"]:.2f} percent), demonstrating classic prior-incentive misalignment as higher expected payouts tempt marginal dosing near the surplus border (matching the economic-ablated historical point near 23.39 percent at 50 EUR ha$^{{-1}}$). '
    'Crucially, mean subsurface native nitrogen loss remains invariant across all subsidy tiers within each climate regime (Fig. 5d inset near 22.6, 18.1 and 15.9 kg N ha$^{-1}$), showing that cash transfers anchored to nominal compliance signals raise farm payouts without curbing hydrological nitrate drainage.'
)
s42_p1_zh = (
    '沿每公顷0至200欧元生态补贴梯度追踪部分收益与联合达标率二维Pareto演变轨迹，研究定量揭示了无校准财政补贴可能诱发激励错位的具体触发条件（图5d）。'
    f'在1.8摄氏度适度升温情景下，绿色补贴在每公顷100欧元处形成星标所示理想帕累托拐点（联合达标升至{100*w18_s100["region_equal"]["joint"]:.2f}%、收益达{w18_s100["region_equal"]["partial_profit"]:.2f}欧元每公顷），兼顾环保改善与农户增收。'
    f'但在历史常态与3.5摄氏度极端升温下，将补贴直接挂钩未校正先验预测概率虽单调推高收益（分别升至每公顷{hist_s200["region_equal"]["partial_profit"]:.2f}与{w35_s200["region_equal"]["partial_profit"]:.2f}欧元），却诱发系统在盈余边界增加试探性边际追肥（50欧元处历史点亦与消融经济项近乎重合于23.39%），导致典型的激励错位与实测达标率回落（分别降至{100*hist_s200["region_equal"]["joint"]:.2f}%与{100*w35_s200["region_equal"]["joint"]:.2f}%）。'
    '图5d右上角插图同时表明三档气候下原生土壤氮淋洗与反硝化损失几乎不随补贴金额变化（分别维持在约22.6、18.1与15.9千克氮每公顷），证明仅针对表观先验指标的财政补贴无法转化成深层地下水实质减排。'
)
add_block('s42-p1', s42_p1_zh, s42_p1_en, figs=['@fig reports/phase8/figures/fig4-factorial-stress.png | reports/phase8/figures/captions-v12/fig5.txt | Fig. 5'])

add_block('sec-s43', '### 4.3 土壤氮库动用与氮碳守恒验证', '### 4.3 Soil Nitrogen Drawdown and Mass Conservation Verification')

s43_p1_en = (
    'Full-profile soil stock accounting, latent feature decoding and numerical mass conservation verify software-level arithmetic integrity and clarify true nitrogen sources across every simulated season (Supplementary Figs. S2 and S8). '
    'Across the 52 historical seasons, Soft-Coupled, matched PPO and DVS-N2 all limit seasonal organic soil nitrogen drawdown to 221.13 to 223.51 kg N ha$^{-1}$ (versus 254.07 kg N ha$^{-1}$ under profit-only mining, confirming that bare relaxation extracts an extra 32.94 kg N ha$^{-1}$ of unpriced soil humus to inflate nominal partial profit), yielding stock-adjusted nitrogen use efficiencies of 0.349 to 0.351 alongside apparent input-output efficiencies of 0.776 to 0.796 (Supplementary Fig. S2). '
    f'Training-fold-frozen linear probes confirm positive out-of-fold determination in all 30 required region-target cells spanning organic nitrogen, soil carbon and net mineralization (minimum $R^2$ equals {min_r2:.4f} in sensorless Wichita soil carbon, Supplementary Fig. S8a), while daily nitrogen and carbon accounting residuals across 6,104,146 simulated transitions remain bounded below $1.904 \\times 10^{{-11}}$ kg N ha$^{{-1}}$ and $2.115 \\times 10^{{-10}}$ kg C ha$^{{-1}}$ with zero accounting leakage across the simulator-controller boundary (Supplementary Fig. S8b).'
)
s43_p1_zh = (
    '全剖面土壤库存核算、代理网络隐层物理解码以及逐日质量收支核对共同验明了模拟闭环的数值严密性与真实氮素来源（附图S2与S8）。'
    '在52个历史农场年中，软耦合、PPO与DVS-N2的当季原生土壤有机氮动用被共同控制在每公顷221.13至223.51千克范围内（显著低于仅收益策略的254.07千克掠夺耗损，直接证明裸回退靠额外抽支32.94千克未计价土壤腐殖质虚增账面收益），折算土壤库存后的全口径NUE位于0.349至0.351区间而表观NUE为0.776至0.796（附图S2）。'
    f'训练折内严密冻结的线性探针验证了代理网络在30个必正区域物理状态格点上的内部物理编码可读性（无传感器威奇托土壤碳最低决定系数{min_r2:.4f}，附图S8a），逾610万条逐日状态演替的绝对氮碳账面残差稳定收敛于每公顷 $1.904 \\times 10^{{-11}}$ 与 $2.115 \\times 10^{{-10}}$ 千克双精度浮点极限以内，确认控制器与机理裁判交互全程零漏算漂移（附图S8b）。'
)
add_block('s43-p1', s43_p1_zh, s43_p1_en)

# Section 5: Discussion (~820 EN words, 5.1 -> 5.2 -> 5.3 Top-SCI Abstraction Ladder)
add_block('sec-disc', '## 5 讨论', '## 5 Discussion')

add_block('sec-d51', '### 5.1 多先验协同耦合机理', '### 5.1 Multi-Prior Synergistic Coupling Mechanism')

d51_p1_en = (
    'This investigation demonstrates that encoding climate de-shifting, distributional quantile integration and bilateral corridor geometry inside collaborative specialists eliminates the need for oversized black-box networks or real-time field sensors. '
    'Integrating candidate schedules across complete weather-by-residual distributions rather than deterministic point predictions enables the eco-safety and economic specialists to weigh rare spring nitrate leaching storms directly against dryland organic nitrogen depletion across both semi-arid and maritime wheats. '
    'Equally important, decomposing external climate risks, watershed caps and bilateral incentives into explicit numerical operators liberates each surrogate neural network from memorizing non-stationary regime shifts through parameter inflation, allowing every ensemble member to maintain only 13,155 weights (55.4 KB per checkpoint and 166.3 KB across three members). '
    'Compared with 64-tree ensembles occupying 275.52 MB per serialized instance (1,723,434 decision nodes), this structured neural surrogate shrinks serialized deployment memory footprint over 1,690-fold while raising historical compliance by 38.5 percent relatively (25.06 versus 18.09 percent) and lowering calibrated profit ranking regret by 40.8 to 49.4 percent, while surpassing a 20,616-parameter reinforcement learning agent across warming and price-shock stressors along the standard 40 kg N ha$^{-1}$ ceiling with 36.2 percent fewer trainable weights per network. '
    'Because bilateral efficiency-surplus geometry and seasonal split staging characterize cereals and row crops broadly, embedding physical conservation inside compact structured planners offers direct methodological value across maize, rice and broader watershed agricultural systems.'
)
d51_p1_zh = (
    '本研究从机制上阐明，在协同决策内部显式嵌入去偏移气象分支、联合分位残差积分与双侧养分走廊几何边界，能够以极轻量结构取代庞杂黑箱与昂贵田间传感器。'
    '生态安全与经济模块在完整气候分枝与零均值残差乘积分布上共同权衡，从而摆脱单点确定性预测在旱作矿化爆发与湿季强降水淋洗下的尾部误判。'
    '更为关键的是，将外生气象风险、水源红线与经济走廊显式拆分为专职数值算子，使响应代理网络无需靠参数膨胀去硬吃非平稳环境漂移，每个成员得以维持仅13,155个权重的高度精简结构（单成员55.4千字节、三成员合计仅166.3千字节）。'
    '相较占用275.52兆字节存储的64棵极端随机树基线，本文代理将实际部署磁盘内存缩减逾1,690倍，同时历史闭环达标相对树模型提升38.5%（25.06%对比18.09%）、决策排序遗憾压降40.8%至49.4%，并在单网络可训练权重较20,616参数强化学习减少36.2%的前提下于40千克红线升温与高肥价压力区持续领跑。由于双侧收支几何与分期施氮动力学同样主导玉米、水稻等大田谷物，这种物理与政策同构的轻量化协作架构具备广阔的跨作物迁移价值。'
)
add_block('d51-p1', d51_p1_zh, d51_p1_en)

add_block('sec-d52', '### 5.2 小麦氮肥智能管理范式演进', '### 5.2 Paradigm Shift in Wheat Nitrogen Management')

d52_p1_en = (
    'Systematic divergence between strict tail pruning, soft corridor coupling and profit-only relaxation marks an essential conceptual shift for agricultural intelligence under compounding environmental stress. '
    'Under benign stationary seasons, conservative hard masks locate safe doses cleanly, whereas tightening nitrate directives or amplifying heat stress shrinks feasible envelopes toward zero and precipitates indiscriminate zero-topdressing stalls [baja2025]. '
    'Retaining continuous distance gradients resolves that conflict between safety conservatism and agronomic responsiveness across heterogeneous wheat belts while guaranteeing empirically verified zero-discrepancy equivalence (30 of 30 invariant tests across 323 plans) relative to monolithic solver architectures. '
    'At the public-policy interface, the prior-incentive misalignment exposed under uncalibrated subsidy rewards explains why agri-environmental payments in frameworks such as the Common Agricultural Policy must benchmark against conservative calibrated lower bounds rather than nominal model probabilities [klages2020]. '
    'In parallel, separating static physical soil baselines from causal station-demeaned satellite anomalies overcomes total cross-regional rejection by un-centered embeddings while lifting prior gate admission to 60.00 to 72.02 percent without claiming artificial predictive error drops [brown2025].'
)
d52_p1_zh = (
    '硬截断、软耦合与裸利润回退三者间的系统性分化，标志着农业自主调控正从单田块脆弱约束走向跨域连续校准智能。'
    '在温和单站年份下保守硬过滤尚可稳定挑出合格方案，然而一旦流域水源红线收紧或热害加剧，预测可行集瞬间坍缩便会引发无差别零追肥僵局 [baja2025]。'
    '连续走廊梯度保持既化解了预测保守性与农艺可施性之间的固有矛盾，又经由30组覆盖323套动作计划的配对检验确证五专职协同与单体求解完全零偏差一致。'
    '在环境政策层面，本文揭示的无校准补贴先验激励错位风险同样印证了农业生态补偿机制必须直接锚定保守共形校准下界而非名义概率预期，方能兼顾农民增收与地下水降氮 [klages2020]。同时，分离静态土壤与站点因果卫星距平既扭转了未中心化向量在陌生大洲全员拒答的困境，又诚实界定了先验门控准入提升（60.00%至72.02%）与定量预测误差尚未超越土壤基线之间的边界 [brown2025]。'
)
add_block('d52-p1', d52_p1_zh, d52_p1_en)

add_block('sec-d53', '### 5.3 局限性与未来展望', '### 5.3 Limitations and Future Directions')

d53_p1_en = (
    'Important physical assumptions bound these findings and explain remaining cross-regime trade-offs. '
    'First, even compliant seasonal controls extract approximately 221 to 224 kg N ha$^{-1}$ from baseline soil organic nitrogen within an isolated reset wheat season, confirming that short-term apparent corridor compliance cannot substitute for multi-year crop-rotation stock stewardship. '
    'Second, lifting closed-loop cross-continental anomaly admission under frozen causal linear adapters leaves out-of-region grain nitrogen squared error marginally above static soil Ridge models (517.65 versus 505.15 kg$^2$ ha$^{-2}$), demonstrating that out-of-distribution gate passage does not automatically lower prediction error without regional fine-tuning. Simultaneously, 90 percent macro conformal coverage coexists with conditional undercoverage of 75.19 percent in semi-arid Western Australia, capping direct dryland deployment until region-stratified conformal recalibration is applied. '
    'Third, benchmark experiments rely on historical climate analogues, idealized warming shifts and complete annual prior-year satellite composites over representative regional profiles rather than operational synoptic weather forecasts, cloud-gapped near-real-time imagery, within-field textural transects or whole-farm machinery cost ledgers. Daily carbon-nitrogen balance verification confirms numerical accounting integrity within the simulator-controller pipeline rather than replacing empirical lysimeter observations. '
    'Finally, uncalibrated ecological subsidies tied directly to prior compliance probabilities risk incentivizing borderline surplus dosing without reducing deep nitrate leaching. '
    'Future work will pursue three concrete extensions, including within-region multi-texture soil and lysimeter groundwater nitrate monitoring transects, region-conditional conformal recalibration and subsidy coupling to calibrated lower bounds, and multi-season prospective field trials driven by operational numerical weather ensembles.'
)
d53_p1_zh = (
    '若干物理设定与建模边界客观刻画了本研究结论的适用外延及残余权衡。'
    '首先，即便在满足EUNEP双侧达标要求的控制轨迹下，单季重置小麦模拟仍会动用约每公顷221至224千克初始土壤有机氮（对应扣除库存后的全口径NUE约0.35），提示表观投入产出达标绝不能替代多年连续轮作下的长周期土壤肥力平衡核算。'
    '其次，冻结参数版因果空间适配器虽将跨洲先验门控准入率提升至60.00%至72.02%，但跨洲籽粒氮均方误差（517.65）尚未优于物理土壤基线（505.15），证实先验准入并不等同于无需微调即可降低定量误差。同期开发集90%宏平均覆盖率在半干旱西澳存在75.19%的条件覆盖不足，提示旱作实际推广前必须执行区域条件共形再校准。'
    '再次，基准测试依赖区域代表性土壤剖面、完整前一年卫星年度合成表征与类比增温气象逼近，尚未完整纳入真实业务集合天气预报误差、实时光学卫星云层遮挡与延迟、百米级田块质地空间变异与农机作业全成本核算。逐日碳氮收支验证衡量的是仿真与控制闭环的数值无损计算完整性，尚不能取代原位渗漏池与多质地地下水实测。'
    '此外，补贴试验提示未来政策激励必须绑定共形安全下界以根除边界投机。后续研究将围绕产区内多质地水土渗漏断面实测、区域条件共形再校准及接入业务数值天气预报的多作季前瞻田间示范三大方向扎实推进。'
)
add_block('d53-p1', d53_p1_zh, d53_p1_en)

# Section 6: Conclusions (~220 EN words)
add_block('sec-conc', '## 6 结论', '## 6 Conclusions')

conc_en = (
    'Single-system wheat nitrogen controllers fracture once global warming, strict watershed nitrate caps, volatile fertilizer markets and missing in-situ sensors collide, oscillating between zero-dose feasibility deadlocks and hidden soil organic nitrogen mining. '
    'By coupling warming-de-shifted climate analogues, watershed nitrate cap margins, bilateral market-corridor scoring and station-demeaned satellite anomalies separated from hydraulic soil baselines inside a 166.3 KB conformalized neural surrogate, AgroMAS-Global resolves this structural trade-off across five contrasting global wheat regions without heavy black-box ensembles or field hardware. '
    'First, replacing brittle tail clipping and profit-only fallbacks with continuous bilateral corridor scoring breaks the deadlock-versus-mining trap, elevating joint compliance 6.27-fold over profit-only control, matching full-budget reinforcement learning under mild climates while leading on the independent Wageningen benchmark, and compressing serialized storage over 1,690-fold below 64-tree ensembles. '
    'Second, coupling de-shifted climate branching with bilateral dynamic continuation anticipates heat-compressed crop phenology along the operational 40 kg N ha$^{-1}$ watershed ceiling, overtaking matched reinforcement learning under 1.8 and 3.5 degrees Celsius warming and widening its advantage when fertilizer prices double. '
    'Third, decoupling static soil physics from causal site-relative satellite anomalies lifts cross-continental prior gate admission from zero to 60.00 percent while clarifying that gate passage and regional soil calibration govern distinct stages of spatial deployment. '
    'Finally, verifying daily carbon-nitrogen conservation across six million transitions exposes persistent single-season humus drawdown alongside a 100 EUR ha$^{-1}$ green-subsidy inflection under moderate warming, demonstrating that durable agri-environmental policies must reward verified nutrient outcomes rather than uncalibrated prior probabilities.'
)
conc_zh = (
    '走出温和平稳单站试验田后，孤立优化产量、收益或生态上限的单系统氮肥控制必将在气候变暖、严格流域红线、肥价冲击与无在线传感器叠加下全面失稳，在零追肥死锁与隐性土壤氮透支之间剧烈摇摆。'
    '通过将去升温偏移气候类比、流域红线余量、双侧市场走廊效用及与水力土壤基线解耦的站点因果卫星距平联合嵌入总计166.3千字节的共形轻量化神经代理，AgroMAS-Global在不依赖田间硬件或重参数黑箱的前提下跨五大麦区破解了这一结构性两难困境。'
    '首先，以连续双侧走廊评分取代刚性截断与裸利润回退，彻底阻断零肥僵局与耗土投机，较仅收益策略实现6.27倍达标跃升，在温和气候下保持与充分预算强化学习等效并于荷兰独立基准领跑，同时较64棵树集成缩减逾1,690倍磁盘存储。'
    '其次，将去升温分支与双侧动态续策耦合，在每公顷40千克氮常规流域红线下提前捕获热害压缩的发育窗口，在1.8与3.5摄氏度升温及肥价翻倍冲击下稳定反超同信息强化学习。'
    '再次，因果分离物理土壤基线与站点历史去均值卫星距平将跨洲先验准入由零升至60.00%，并界定出空间门控准入与本地定量校准的分工边界。'
    '最后，依托逾六百万条日步长的氮碳质量守恒核算，揭示出表观达标背后不容忽视的原生腐殖质净亏损与适度升温下每公顷100欧元补贴最优拐点，证明可持续农业生态政策必须锚定经验证的真实养分结局而非未校准名义概率。'
)
add_block('conc-body', conc_zh, conc_en)

# Author Declarations, Data Availability & Code Availability
add_block('sec-decl', '## 声明与开源共享', '## Declarations and Availability')

add_block('sec-dcredit', '### 作者贡献', '### CRediT Authorship Contribution Statement')
avail_credit_en = 'Yongan Zhang conceived the study, designed the multi-prior coupled architecture, developed the simulation and surrogate codebase, performed the experiments, drafted the manuscript and curated public data and model artifacts. Zhiling Guo supervised the study, validated the experimental protocol and methodological boundaries, and reviewed and edited the manuscript.'
avail_credit_zh = '张永安负责研究构思、多先验协同控制架构设计、模拟与代理代码开发、实验执行、论文撰写与开源数据模型整理，郭直灵负责研究指导、实验方案与边界核验以及论文审阅修订。'
add_block('avail-credit', avail_credit_zh, avail_credit_en)

add_block('sec-dcomp', '### 利益冲突与基金声明', '### Declaration of Competing Interest and Funding')
avail_comp_en = 'The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper. This research received no external funding.'
avail_comp_zh = '作者声明不存在任何可能影响本研究客观性的已知经济利益冲突或个人关系。本研究未获外部资助。'
add_block('avail-competing', avail_comp_zh, avail_comp_en)

add_block('sec-ddata', '### 数据可用性', '### Data Availability')
avail_data_en = 'All daily meteorological forcing datasets from NASA POWER, SoilGrids and HWSD soil hydraulic profiles, annual 64-D satellite embeddings across Australia, the United States, the Netherlands, France and China, independent Wageningen weather sequences, conformal calibration predictions, latent physical-decoding arrays and complete statistical contrast ledgers are openly archived in the project repository at https://github.com/YonganZhang/AgroMAS-Global under the GNU General Public License v3.0.'
avail_data_zh = '本研究涉及澳大利亚、美国、荷兰、法国与中国五大产区的逐日NASA气象驱动数据、SoilGrids水力土壤剖面参数、64维年度卫星表征、瓦赫宁根独立基准气象序列、共形校准输出、隐层物理状态解码数据及全部统计检验台账均已按GNU GPL v3.0协议公开托管于项目仓库 https://github.com/YonganZhang/AgroMAS-Global 。'
add_block('avail-data', avail_data_zh, avail_data_en)

add_block('sec-dcode', '### 代码可用性', '### Code Availability')
avail_code_en = 'All source code for the AgroMAS-Global control modules, surrogate neural network training, conformal calibration, causal satellite adaptation, invariance verification suites, reproducible figure rendering scripts, 72 frozen neural surrogate weights and 245 frozen spatial-temporal adapters, together with the local runtime patch over upstream PCSE, is publicly released under the GNU General Public License v3.0 at https://github.com/YonganZhang/AgroMAS-Global (twelve oversized tree reference binaries omitted due to file-size caps can be reproduced directly via the released reference-fitting script).'
avail_code_zh = 'AgroMAS-Global协同控制模块源码、轻量代理神经网络训练与共形校准流程、因果卫星适配器、不变性测试套件、可复现制图脚本、72个冻结代理权重、245个跨时空线性适配器以及上游PCSE运行时补丁均已依据GNU GPL v3.0协议公开托管于 https://github.com/YonganZhang/AgroMAS-Global （受仓库单文件大小上限略去的12个大型极端随机树基准文件可通过已公开训练脚本直接复现生成）。'
add_block('avail-code', avail_code_zh, avail_code_en)

# Appendix: Compact Overview + Embedded Supplementary Figs S1-S8 without stub clutter
add_block('sec-app', '## 附录 补充图表', '## Appendix Supplementary Figures')

SUPP_FIGS = [
    ('@fig reports/phase8/figures/figs2-g3-subsidy.png | reports/phase8/figures/captions-v12/figs1.txt | Supplementary Fig. S1'),
    ('@fig reports/phase8/figures/fig5-deployment-closure.png | reports/phase8/figures/captions-v12/figs2.txt | Supplementary Fig. S2'),
    ('@fig reports/phase8/figures/figs3-price-subsidy.png | reports/phase8/figures/captions-v12/figs3.txt | Supplementary Fig. S3'),
    ('@fig reports/phase8/figures/figs4-policy-scorecard.png | reports/phase8/figures/captions-v12/figs4.txt | Supplementary Fig. S4'),
    ('@fig reports/phase8/figures/figs5-p1-all-regimes.png | reports/phase8/figures/captions-v12/figs5.txt | Supplementary Fig. S5'),
    ('@fig reports/phase8/figures/figs6-p2-admission-mse.png | reports/phase8/figures/captions-v12/figs6.txt | Supplementary Fig. S6'),
    ('@fig reports/phase8/figures/figs7-stress-180cell-grid.png | reports/phase8/figures/captions-v12/figs7.txt | Supplementary Fig. S7'),
    ('@fig reports/phase8/figures/figs8-closure-readout-audit.png | reports/phase8/figures/captions-v12/figs8.txt | Supplementary Fig. S8'),
]

app_intro_en = 'Supplementary Figures S1 to S8 preserve detailed counterfactual warming-cap gradients (S1), 349-day organic-mineral stock drawdown profiles (S2), doubled fertilizer price and dual-axis subsidy sensitivity curves (S3), nine-policy bootstrap uncertainty and four-metric agronomic scorecards (S4), eight-policy efficiency distributions across 32 historical years (S5), cross-regional satellite admission versus prediction error matrices (S6), complete 180-cell stress surface differences (S7) and 50-cell out-of-fold physical readout alongside six-million-record carbon-nitrogen mass conservation residuals (S8).'
app_intro_zh = '附图S1至S8完整补充了增温与红线梯度配对消融（S1）、349天土壤有机氮与矿质氮库存动用剖面（S2）、肥价翻倍及双轴补贴梯度曲线（S3）、九策略自助置信区间与四指标评分卡（S4）、全量八策略效率云雨与32年演化轨迹（S5）、无传感器先验准入与预测均方误差矩阵（S6）、180格全因子逐格差值相图（S7）以及50格隐层物理解码与逾六百万条日质量守恒残差检验（S8）。'
add_block('app-intro', app_intro_zh, app_intro_en, figs=SUPP_FIGS)

# Hygiene Validation before writing to disk
FORBIDDEN_WORDS = ['audit', 'auditable', 'auditability', '审计', '可审计', 'Phase8', 'v6', 'v7', 'v8', 'v9', 'v10', 'v11', 'v12', '.csv', '.json', '.py', 'We ', 'Our ', ' we ', ' our ', '我们', '**']


def strip_math_and_cites(s):
    s = re.sub(r'\$\$.*?\$\$', ' ', s, flags=re.S)
    s = re.sub(r'\$[^$]*\$', ' ', s)
    s = re.sub(r'\[[^\]]+\]', ' ', s)
    s = re.sub(r'https?://\S+', ' ', s)
    return s


violations = []
for bid, zh_t, en_t, _ in blocks:
    for lang, txt in [('zh', zh_t), ('en', en_t)]:
        if txt.startswith('|') or '|---' in txt:
            for w in ['audit', 'auditable', 'auditability', '审计', '可审计', 'Phase8', '.csv', '.json', '.py', '**']:
                if w in txt:
                    violations.append((bid, lang, 'table_word', w))
            continue
        clean = strip_math_and_cites(txt)
        for ch in [':', '：', ';', '；', '/', '—', '--', '?', '？']:
            if ch in clean:
                violations.append((bid, lang, 'punct', ch, clean[:120]))
        if re.search(r'\+[0-9]', clean):
            violations.append((bid, lang, 'leading_plus', clean))
        for w in FORBIDDEN_WORDS:
            if w in ('v6', 'v7', 'v8', 'v9', 'v10', 'v11', 'v12') and 'Legacy' in txt:
                continue
            if w in txt:
                violations.append((bid, lang, 'word', w))

for cap_file in sorted(CAP_DIR.glob('*.txt')):
    ctxt = strip_math_and_cites(cap_file.read_text())
    for ch in [':', '：', ';', '；', '/', '—', '--', '?', '？']:
        if ch in ctxt:
            violations.append((cap_file.name, 'cap', 'punct', ch))
    for w in FORBIDDEN_WORDS:
        if w in ctxt:
            violations.append((cap_file.name, 'cap', 'word', w))

assert not violations, f'Prose hygiene violations detected: {violations}'

zh_out = []
en_out = []
for bid, zh_t, en_t, figs in blocks:
    zh_out.append(f'<!-- id:{bid} -->\n{zh_t}')
    en_out.append(f'<!-- id:{bid} -->\n{en_t}')
    for fg in figs:
        zh_out.append(fg)

(M / 'zh.md').write_text('\n\n'.join(zh_out) + '\n')
(M / 'en.md').write_text('\n\n'.join(en_out) + '\n')

bib_keys = set(re.findall(r'@\w+\{([^,]+),', (M / 'references.bib').read_text()))
used_cites = []
for txt in [(M / 'en.md').read_text(), (M / 'zh.md').read_text()]:
    for grp in re.findall(r'\[([A-Za-z][\w-]*(?:,\s*[A-Za-z][\w-]*)*)\]', txt):
        for k in [x.strip() for x in grp.split(',')]:
            used_cites.append(k)
missing_keys = sorted(set(used_cites) - bib_keys)
assert not missing_keys, f'Missing BibTeX keys: {missing_keys}'

# Word-count summary matching Top-SCI budgets
sec_wc = {}
cur_sec = 'front'
for bid, _, en_t, _ in blocks:
    if en_t.startswith('## '):
        cur_sec = bid
    if en_t.startswith('#') or '|---' in en_t or en_t.startswith('$$'):
        continue
    cleaned = re.sub(r'\$\$.*?\$\$', ' ', en_t, flags=re.S)
    cleaned = re.sub(r'\$[^$]*\$', 'X', cleaned)
    cleaned = re.sub(r'\[[^\]]+\]', ' ', cleaned)
    sec_wc[cur_sec] = sec_wc.get(cur_sec, 0) + len(cleaned.split())

main_wc = sum(sec_wc[k] for k in ['sec-intro', 'sec-methods', 'sec-res', 'sec-stress', 'sec-disc', 'sec-conc'])
p2_cites = re.findall(r'\[([A-Za-z][\w-]*(?:,\s*[A-Za-z][\w-]*)*)\]', p2_en)
counts_per_cite = [len(c.split(',')) for c in p2_cites]
print(json.dumps({
    'status': 'PASS',
    'blocks': len(blocks),
    'word_counts': sec_wc,
    'main_sections_1_to_6_words': main_wc,
    'bib_keys_total': len(bib_keys),
    'unique_cited_keys': len(set(used_cites)),
    'intro_p2_cite_groups': len(p2_cites),
    'intro_p2_1key_pct': round(100 * sum(1 for n in counts_per_cite if n == 1) / len(counts_per_cite), 1),
    'intro_p2_2to3key_pct': round(100 * sum(1 for n in counts_per_cite if 2 <= n <= 3) / len(counts_per_cite), 1),
    'intro_p2_gt3key': sum(1 for n in counts_per_cite if n > 3),
}, indent=2))
