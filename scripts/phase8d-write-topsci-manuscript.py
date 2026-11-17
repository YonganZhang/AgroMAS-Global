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
        'Factorial climate, policy and economic stress surface across global winter wheat regimes. '
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
    '# 耦合气候、流域、市场与卫星先验的小麦精准氮肥管理',
    '# Coupling climate, watershed, market and satellite priors for precision wheat nitrogen management'
)

# Abstract (Five-Step S1-S5, ~245 EN words)
add_block('sec-abs', '## 摘要', '## Abstract')

abs_en = (
    'Synchronizing split nitrogen fertilization in global wheat production must sustain farm profitability and grain yield while keeping seasonal efficiency inside a safe bilateral corridor and curbing watershed nitrate surplus. '
    'Conventional process-based reinforcement learning and static split rules remain confined to stationary single-station fields with full in-situ sensors, leaving unresolved how coupled decision systems behave when climate warming, stringent nitrate caps, fertilizer price surges and unseen continental transfers act together. '
    'This work introduces AgroMAS-Global, a coupled five-specialist control framework unifying compact conformalized response surrogates, station-demeaned satellite anomaly priors and warming-de-shifted weather branching under non-anticipative three-stage planning verified by a mechanistic simulator. '
    f'While remaining statistically equivalent to full-budget reinforcement learning under benign historical baselines (25.06 versus 27.00 percent compliance, 46 of 52 seasons tied, mean difference minus 1.94 percentage points, Holm p equals 1.00) and averaging 0.58 percentage points globally across all 180 factorial stress cells (40 wins, 93 ties and 47 losses), continuous bilateral coupling prevents soil-mining collapse (6.27-fold compliance gain over profit-only relaxation), breaks ahead by 5.15 and 5.61 percentage points along the operational 40 kg N ha$^{{-1}}$ ceiling under 1.8 and 3.5 degrees Celsius warming (7.19 to 8.10 percentage points under doubled prices), edges matched reinforcement learning on a seven-season Wageningen cohort (28.57 versus 19.05 percent), reduces serialized model storage over 1,690-fold versus 64-tree ensembles (166.3 KB versus 275.52 MB) alongside 38.5 percent higher compliance and up to 49.4 percent lower regret, and raises cross-continental prior gate admission from zero to 60.00 percent. '
    'These advances reveal how threshold-dependent coupling prevents both high-price humus depletion and cap-induced deadlocks.'
)

abs_zh = (
    '全球小麦全季分期精准施氮必须在稳固产量与农户收益的同时，将表观氮利用效率锁定在双侧安全区间并抑制流域硝态氮盈余超标。'
    '现有过程强化学习与静态农艺分期规则高度依赖气候平稳与田间传感器完备的孤立试验田，未能揭示气候变暖、严格水源红线、高肥价冲击与无传感器跨洲迁移耦合作用时的调控失效与稳健机制。'
    '本研究提出AgroMAS-Global多系统耦合协同调控框架，将紧凑共形响应代理、站点去均值卫星距平先验与去升温偏移天气分支整合于三阶段非预知动态规划，并由独立机理引擎开展封闭检验。'
    f'在温和历史基准上与充分预算强化学习保持统计等效（联合达标25.06%对比27.00%、52年中有46年一致、配对均值差负1.94个百分点、Holm校正p等于1.00）且180格全因子平均差为0.58个百分点（40胜、93平、47负）的前提下，连续双侧耦合彻底阻断仅收益回退诱发的土壤氮掠夺（达标率跃升6.27倍），在每公顷40千克氮常规红线叠加1.8及3.5摄氏度升温时反超匹配强化学习5.15与5.61个百分点（双倍肥价扩大至7.19至8.10个百分点），并在7季瓦赫宁根独立样本取得28.57%对比19.05%优势，同时较64棵极端随机树实现逾1,690倍存储压缩（166.3千字节对比275.52兆字节）并伴随38.5%相对达标提升与至多49.4%遗憾下降，跨洲先验门控准入率从零升至60.00%。'
    '结果表明，红线阈值依赖的多系统耦合可同步防范高肥价地力透支与严红线无肥死锁。'
)
add_block('abs-body', abs_zh, abs_en)

# Section 1: Introduction (P1-P5, 80/10/10 citations, zero journal names)
add_block('sec-intro', '## 1 引言', '## 1 Introduction')

p1_en = (
    'Global cereal productivity doubled over the late twentieth century chiefly through synthetic nitrogen inputs, yet less than half of applied fertilizer nitrogen enters harvested grain worldwide [zhang2015]. '
    'Unrecovered nitrogen accelerates aquifer nitrate contamination, nitrous oxide emissions and coastal eutrophication, tightening the mid-century tension between food security and climate mitigation [lipper2014]. '
    'Wheat nitrogen management has therefore moved beyond yield maximization to co-regulating crop uptake, hydrological losses and soil organic nitrogen turnover across contrasting agroecosystems [chen2014]. '
    'Because unfertilized wheat still harvests nitrogen mineralized from native soil humus, a low seasonal surplus by itself never guarantees sustainable stewardship [vanderpol1992]. '
    'To prevent such disguised soil mining, the European Nitrogen Expert Panel instituted a safe bilateral corridor requiring apparent nitrogen use efficiency between 0.50 and 0.90 alongside nonnegative surplus below watershed limits [eunep2015].'
)
p1_zh = (
    '二十世纪中后期以来，全球谷物增产在很大程度上依托化学氮肥投入，然而农田施氮通常不足半数被籽粒有效回收 [zhang2015]。'
    '流失活性氮持续加剧地下水硝态氮污染、温室气体排放与流域富营养化，使冬小麦管理长期置身于粮食安全与环境减排的双重挤压 [lipper2014]。'
    '精准配肥的核心诉求也随之从单维高产转向协调作物吸收、边界损失与长期土壤氮库维系 [chen2014]。'
    '即便完全停施化肥，小麦仍可借助土壤有机氮矿化维持短期籽粒移出，故而单纯的低氮盈余并不足以表征生态安全 [vanderpol1992]。'
    '欧洲氮专家组为此确立了双侧养分管理走廊，要求表观氮肥利用效率落入0.50至0.90安全区且净盈余维持非负并低于流域上限 [eunep2015]。'
)
add_block('intro-p1', p1_zh, p1_en)

p2_en = (
    'Prior investigations toward operationalizing seasonal nitrogen stewardship evolved along three distinct routes, each encountering critical friction outside stationary benchmark plots. '
    'Along the biophysical modeling route, dynamic process simulators resolve daily phenology, biomass partitioning and coupled soil carbon-nitrogen cycling [vandiepen1989]. '
    'Foundational field datasets calibrated early winter wheat nitrogen balance routines [groot1991]. '
    'Mature platforms such as WOFOST standardized water-limited cereal assimilate prediction [dewit2019]. '
    'Subsequent wheat phenology updates strengthened European cultivar timing accuracy [ceglar2019]. '
    'Recent soil-nitrogen couplings connected crop uptake directly with mineral and organic nitrogen pools to inform nitrate directives [berghuijs2024]. '
    'Parallel multi-crop platforms expanded management and soil representation across North American wheat belts [jones2003]. '
    'CropSyst quantified multi-year cropping sequence nutrient balances [stockle2003]. '
    'APSIM refined water-nitrogen interactions across drought-prone Mediterranean and subtropical systems [holzworth2014]. '
    'Regional yield-gap protocols bridged field simulations to strategic intensification assessments [vanittersum2013]. '
    'Spatial upscaling methods projected point diagnostics onto national production atlases [vanbussel2015]. '
    'Continental crop monitoring systems operationalized routine in-season forecasting across arable plains [vandervelde2019]. '
    'Along the agronomic stewardship route, multi-site trials matched split topdressing rates with crop developmental demand [cui2010]. '
    'Global syntheses established timing and placement rules improving cereal fertilizer recovery [fageria2005]. '
    'Chinese meta-analyses identified water-fertilizer thresholds optimizing joint productivity [yang2022]. '
    'Site-specific nutrient advisories raised nitrogen efficiency across intensive smallholder wheat plains [wang2020]. '
    'Sandy-soil field experiments quantified leaching abatement from reduced split regimes [faber2021]. '
    'Precision farming reviews cataloged canopy sensors and variable-rate application workflows [fountas2015]. '
    'Global indicator frameworks harmonized efficiency and surplus reporting across farming systems [norton2015]. '
    'Commercial farm surveys uncovered wide efficiency dispersion within intensive European arable zones [silva2021]. '
    'Recent monitoring across northwestern European arable rotations confirmed persistent room to trim excess inputs without yield loss [ravensbergen2024]. '
    'Regulatory syntheses linked uniform surplus caps to groundwater restoration targets [eu2016, fao2019, klages2020]. '
    'Long-term soil profiles further documented heavy deep nitrate accumulation under semi-humid plains [zhou2016] and sluggish organic carbon turnover across decades [huang2007]. '
    'Nevertheless, static split prescriptions falter whenever spring drought or heatwaves compress grain filling and alter soil mineralization [altenbach2003, iizumi2016]. '
    'Along the sequential optimization route, researchers linked simulators with digital twins and reinforcement learning to automate split timing [pylianidis2021]. '
    'Methodological reviews mapped sequential control opportunities under environmental stochasticity [gautron2022a]. '
    'Constrained multi-objective optimization established safety foundations for policy trade-offs [censor1977, roijers2013, achiam2017]. '
    'Initial gym wrappers turned crop models into reinforcement learning testbeds [overweg2021]. '
    'Subsequent environments added stochastic weather and rotation variability [gautron2022b]. '
    'Multi-year platforms like CyclesGym enabled soil nitrogen optimization across rotations [turchetta2022], while modular interfaces separated physical state evolution from noisy observations [maillard2023]. '
    'Deep reinforcement learning policies curbed inputs in stationary single-site climates [wu2022]. '
    'Imitation warm-starts accelerated policy discovery in agronomic action spaces [tao2022]. '
    'Watershed-coupled learners explored downstream nitrate load reductions [madondo2023]. '
    'Domain randomization countered transition drift across heterogeneous environments [tobin2017]. '
    'Reward design analyses warned that mis-weighted scalar objectives induce unintended shortcut exploitation [eschmann2021]. '
    'Safe reinforcement learning suites standardized constraint evaluation protocols [ji2023, sutton2018]. '
    'Notably, Baja and collaborators applied constrained reinforcement learning within a nitrogen-enabled wheat model to target bilateral efficiency at a single Dutch site [baja2025]. '
    'Harmonized soil grids supplied continuous physical property priors across unmeasured croplands [poggio2021]. '
    'In parallel, annual satellite foundation embeddings created a scalable spatial representation layer beyond ground sensors [brown2025, campsvalls2025].'
)
p2_zh = (
    '围绕冬小麦季内精准配肥，学术界形成了三条主要研究脉络，但各自在脱离平稳单点条件后均显露机制局限。'
    '第一条机理建模脉络在日尺度上刻画作物物候与土壤碳氮周转过程 [vandiepen1989]。'
    '早期试验数据集率先支撑了冬小麦水肥动态与氮素平衡校验 [groot1991]。'
    'WOFOST等标准平台系统确立了受水肥限制的谷物干物质生产框架 [dewit2019]。'
    '物候参数化改进进一步提升了欧洲冬小麦发育期预测精度 [ceglar2019]。'
    '近年的氮扩展模块则把作物吸收直接耦合至土壤有机与矿质氮库以评估硝酸盐法规 [berghuijs2024]。'
    '同期DSSAT拓展了北美麦区多元轮作与耕作模拟能力 [jones2003]。'
    'CropSyst形式化构建了长周期养分连续收支模型 [stockle2003]。'
    'APSIM则面向地中海型雨养旱作强化了水分硝态氮迁移描述 [holzworth2014]。'
    '产量差诊断架构打通了田块模拟与区域增产潜力评估之间的桥梁 [vanittersum2013]。'
    '空间尺度上推规程随即将站点诊断延展至国家粮食图谱 [vanbussel2015]。'
    '洲际农情系统继而支撑了全欧尺度的季内动态产量预测 [vandervelde2019]。'
    '第二条农艺试验脉络致力于使分期施肥速率与作物阶段需氮同步 [cui2010]。'
    '全球农艺评述凝练出通过优化施期与基追比例提升恢复率的关键规律 [fageria2005]。'
    '中国主产麦区的荟萃分析界定了水氮协同增效的田间管理阈值 [yang2022]。'
    '养分专家系统推荐帮助广大农户麦田显著提高了化肥利用效率 [wang2020]。'
    '轻质砂土田间试验定量测得减量分期追肥在削减硝态氮淋洗上的实效 [faber2021]。'
    '精准农业综述系统分类了冠层光谱与变量施肥装备路径 [fountas2015]。'
    '国际评价准则统一了效率与净盈余的跨体系核算口径 [norton2015]。'
    '商业农场调查揭示了同一高产区内集约田块效率参差不齐的普遍现实 [silva2021]。'
    '西北欧商业地块监测确认不减产前提下仍存在较大降盈余空间 [ravensbergen2024]。'
    '政策评估进而将统一盈余上限直接锚定于地下水保护红线 [eu2016, fao2019, klages2020]。'
    '华北长期定位监测同时记录了深层剖面厚重硝态氮滞留 [zhou2016] 与有机氮库缓慢周转规律 [huang2007]。'
    '但当春季干旱或花后高温打乱物候节律时，静态配方难以动态前瞻修正 [altenbach2003, iizumi2016]。'
    '第三条序贯优化脉络将过程模拟器、数字孪生与强化学习结合，追求全季自主寻优 [pylianidis2021]。'
    '方法综述总结了强化学习应对农田随机气象与延迟反馈的独特潜力 [gautron2022a]。'
    '多目标与约束策略理论奠定了安全序贯权衡的数学基础 [censor1977, roijers2013, achiam2017]。'
    '初代交互接口首次将机理作物模型改造为强化学习训练环境 [overweg2021]。'
    '后续平台逐步纳入随机气象生成与轮作序列变异性 [gautron2022b]。'
    'CyclesGym拓展了多季土壤氮演化控制基准 [turchetta2022]，模块化界面进一步解耦了物理状态与观测噪声 [maillard2023]。'
    '深度强化学习在单站稳态气候下展现出显著节肥潜力 [wu2022]。'
    '模仿学习预训练有效缓解了连续农艺空间冷启动收敛慢的难题 [tao2022]。'
    '流域尺度耦合探索亦开始面向面源硝态氮减排寻优 [madondo2023]。'
    '域随机化方法缓解了模拟器向目标环境迁移时的动态漂移 [tobin2017]。'
    '奖励机制研究同时警示不当标量权重极易诱发算法投机取巧 [eschmann2021]。'
    '安全强化学习基准规范了多约束策略的统计检验流程 [ji2023, sutton2018]。'
    '代表性工作如Baja等将约束强化学习接入扩展氮平衡小麦模型，率先在荷兰单站检验了双侧效率区间调控 [baja2025]。'
    '全球土壤物理图谱为未测农田提供了标准化质地与水力基底 [poggio2021]。'
    '同期年度地球卫星基础表征模型的成熟则开启了不依赖田间传感器实现跨洲泛化的新窗口 [brown2025, campsvalls2025]。'
)
add_block('intro-p2', p2_zh, p2_en)

p3_en = (
    'Despite these advances, current constrained controllers remain anchored to an isolated single-field formulation exhibiting four coupled structural gaps [baja2025]. '
    'First, instantaneous policies ignore post-decision weather uncertainty and anthropogenic warming trends, leaving controllers unable to balance impending leaching storms against late-season drought risk [asseng2015]. '
    'Second, uniform station assumptions overlook tight peri-urban watershed nitrate ceilings where strict hard filtering frequently empties candidate sets and triggers zero-dose deadlock [eu1991, klages2020]. '
    'Third, uncalibrated scalar rewards fail under input price shocks, allowing profit-seeking agents to boost short-term income by withholding nitrogen and mining soil humus [eschmann2021, tan2005]. '
    'Fourth, telemetry-dependent learners require expensive continuous field sensors, whereas feeding raw global satellite vectors into models conflates static geographic identity with seasonal dynamics [gaso2023, roberts2017]. '
    'This motivates two central scientific questions. How do continuous bilateral corridor retention and climate-adjusted forecast uncertainty govern the transition among deadlock, soil nitrogen mining and joint compliance across coupled climate, watershed and price stress. And can causal decomposition of static soil baselines from station-demeaned satellite anomalies enable reliable sensorless adaptation across contrasting continents without inflating predictive error.'
)
p3_zh = (
    '尽管研究持续深入，既有最前沿约束控制仍被锁定在孤立单试验田假设之中，暴露出四项互为因果的结构性科研缺口 [baja2025]。'
    '首先，既有策略仅对过往及瞬时状态作被动反应，缺乏前瞻天气分支不确定性与升温偏移校正，无法分辨追肥后降雨究竟有利吸收还是加剧淋洗 [asseng2015]。'
    '其次，单一稳态田块假设脱离真实城郊水源地生态红线，一旦氮盈余上限收紧，传统硬约束过滤极易陷入无解空集死锁 [eu1991, klages2020]。'
    '再次，静态奖励缺乏高肥价防透支护栏，经济压力下策略往往靠少施或不施肥换取短期账面收益并悄然掏空土壤有机氮库 [eschmann2021, tan2005]。'
    '最后，在线遥测策略仰赖昂贵田间监测设备，而把高维全球卫星表征直接喂入模型则会将固定站点身份与年际气象波动混为一谈 [gaso2023, roberts2017]。'
    '由此凝聚出两个核心科学问题。其一，在气候变暖、流域红线与肥价冲击多重压力下，连续双侧走廊保留与气象不确定性校准如何支配可行域死锁、土壤透支与联合达标之间的机制切换。其二，将静态土壤基线与站点历史去均值卫星距平因果解耦后，无传感器控制能否实现稳健的跨洲迁移而不陷入先验准入与实际误差脱节。'
)
add_block('intro-p3', p3_zh, p3_en)

p4_en = (
    'Closing these coupled gaps carries direct significance because fertilization failures cascade simultaneously across harvest stability, drinking-water compliance and farm solvency. '
    'Existing benchmarks focus predominantly on benign historical single-station years where simple heuristics already achieve comparable apparent performance, concealing acute controller fragility under compounding shocks [baja2025]. '
    'Without explicit bilateral corridor gradients, distributional uncertainty calibration and multi-region verification, advisory systems risk imposing zero-dose stalls in nitrate-vulnerable catchments or encouraging hidden organic nitrogen depletion under market stress [zhou2016, booth2023]. '
    'Equally important, naive green subsidies linked directly to uncalibrated model probabilities may elevate farm payouts without curbing watershed losses. '
    'Quantifying failure transitions across contrasting global archetypes therefore gives agronomists and catchment managers transparent operating boundaries prior to deployment [goldenits2024].'
)
p4_zh = (
    '回应上述科学问题具有紧迫的农学与环境意义，因为配肥决策失当会同步波及粮食供给、水源达标与农户收入。'
    '当前领域普遍依赖温和单站历史年份开展基准对决，不同方法在平顺条件下的表面一致严重掩盖了多重胁迫叠加时的策略脆性 [baja2025]。'
    '若缺少连续双侧走廊梯度、严格校准的预测不确定性边界与跨产区独立验证，决策系统便可能在水源保护区酿成零追肥减产僵局，或在肥价攀升时纵容掠夺土壤氮库的伪最优陷阱 [zhou2016, booth2023]。'
    '而在公共政策端，直接与未经校准先验概率挂钩的生态补贴极易消耗预算却难以下降深层淋溶。'
    '因此，跨典型产区刻画调控相变规律，可为农技推广与流域治理提前划定清晰可信的运行安全边界 [goldenits2024]。'
)
add_block('intro-p4', p4_zh, p4_en)

p5_en = (
    'To answer these questions, this study establishes AgroMAS-Global, a coupled five-specialist numerical architecture integrating spatial twin inference, de-shifted warming analogue forecasting, urban watershed safety screening, socio-economic corridor scoring and three-stage non-anticipative dynamic planning over an independent mechanistic crop-soil referee. '
    'Validation spans five global urban-breadbasket archetypes in Perth, Wichita, Lelystad, Beauce and Luancheng across historical baselines, temporal and cross-continental satellite holdouts, and a complete climate-cap-price-subsidy factorial surface. '
    'Three primary contributions advance coupled agricultural control. First, continuous bilateral corridor retention combined with non-anticipative continuation remains equivalent to reinforcement learning across mild historical years while preventing profit-driven soil-mining collapse (6.27-fold compliance gain), leading under 1.8 and 3.5 degrees Celsius warming and doubled fertilizer prices at the 40 kg N ha$^{-1}$ cap, and cutting serialized ensemble storage over 1,690-fold versus 64-tree baselines with 38.5 percent higher compliance. Second, conformalized zero-mean residual integration and station-demeaned satellite decomposition raise cross-continental prior gate admission from zero to 60.00 percent while transparently delineating out-of-region error bounds. Third, full factorial stress testing exposes cap-dependent warming crossovers, uncalibrated prior-subsidy misalignment and strict double-precision accounting verification across over six million daily transitions. '
    'Section 2 formulates the methodology, Section 3 analyzes comparative, ablation and spatial transfer experiments, Section 4 investigates factorial stress regimes and mass closure, and Sections 5 and 6 synthesize mechanisms and conclusions.'
)
p5_zh = (
    '为此，本研究构建了AgroMAS-Global多系统耦合五专职数值协同架构，将空间孪生代理推理、去升温偏移天气类比预报、城市生态安全筛查、社会经济双侧走廊评分与三阶段非预知农艺规划严密耦合并由独立机理引擎封闭校验。'
    '研究基于澳大利亚珀斯、美国威奇托、荷兰莱利斯塔德、法国巴黎盆地与华北平原栾城五大全球城郊麦区，覆盖历史基准、跨年跨洲无传感器迁移及气候政策经济全因子压力场景开展系统实证。'
    '本文凝练出三项核心学术贡献。其一，连续双侧走廊保留与三阶段非预知规划在温和历史年与强化学习保持等效并彻底遏制土壤透支塌缩（达标较仅收益回退提升6.27倍），在40千克红线叠加1.8与3.5摄氏度升温及高肥价下实现反超，同时代理序列化存储较集成树缩减逾1,690倍且达标高出38.5%。其二，共形零均值联合残差与站点因果距平分离将跨洲先验门控准入从零拉升至60.00%，并诚实界定准入率与定量预测误差间的边界。其三，全因子压力曲面揭示了红线依赖型升温交叉律与先验补贴激励错位风险，并在逾六百万条日状态记录上完成双精度账面核验。'
    '第2节阐述方法与校准协议，第3节展示数据、对比、消融与时空迁移结果，第4节剖析全因子压力与物理闭合检验，第5与第6节探讨科学机理与全文结论。'
)
add_block('intro-p5', p5_zh, p5_en)

# Section 2: Materials and Methods (~1,150 EN words)
add_block('sec-methods', '## 2 材料与方法', '## 2 Materials and Methods')

add_block('sec-m21', '### 2.1 问题定义与物理收支边界', '### 2.1 Problem Formulation')

m21_p1_en = (
    'Winter wheat seasonal fertilization is posed as a finite-horizon non-anticipative control problem across three sequential phenological windows triggered when observable development stage crosses 0.20, 0.55 and 0.82 [ceglar2019, baja2025]. '
    'At each event $t \\in \\{1, 2, 3\\}$, controllers choose discrete topdressing nitrogen $u_t \\in \\{0, 10, 20, 40, 60, 80, 100\\}$ kg N ha$^{-1}$ subject to a cumulative seasonal ceiling of 220 kg N ha$^{-1}$, spanning 343 budget-legal action schedules. '
    'In the primary sensorless deployment track, real-time field telemetry of leaf area, soil water and plant nitrogen stays completely masked during online decisions.'
)
m21_p1_zh = (
    '冬小麦全生育期追肥被形式化为三阶段有限时域非预知序贯控制问题，当外部可观测发育阶段依次跨越0.20、0.55与0.82阈值时触发返青、拔节与孕穗决策 [ceglar2019, baja2025]。'
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

add_block('sec-m22', '### 2.2 AgroMAS-Global 多专职协同架构', '### 2.2 AgroMAS-Global Architecture')

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
add_block('m22-intro', m22_intro_zh, m22_intro_en, figs=['@fig reports/phase8/figures/fig1-candidates/candidate-b-v4-best.png | reports/phase8/figures/captions-v12/fig1.txt | Fig. 1'])

add_block('sec-m221', '#### 2.2.1 地空孪生响应代理与因果卫星距平解耦', '#### 2.2.1 Spatial Twin Specialist and Causal Satellite Prior Adaptation')

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

add_block('sec-m222', '#### 2.2.2 气候预测类比分支与社会经济走廊协同控制', '#### 2.2.2 Climate Analogue Branching, Bilateral Corridor Scoring, and Dynamic Continuation')

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

add_block('sec-m23', '### 2.3 共形校准与防泄漏时空验证策略', '### 2.3 Conformal Surrogate Calibration and Spatiotemporal Validation Strategy')

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

# Section 3: Experimental Results — Locked Top-SCI 5-Part Structure (3.1 - 3.5)
add_block('sec-res', '## 3 实验结果与分析', '## 3 Experimental Results')

# 3.1 Dataset and Classic Case Description (~350 EN words, Table 1 + Fig. 2a-d deep walkthrough)
add_block('sec-r31', '### 3.1 数据集、典型麦区特征与代理世界模型校准', '### 3.1 Dataset and Classic Case Description')

r31_p1_en = (
    'Across four continents, the five winter wheat archetypes segregate into physically distinct climatic warming trends, soil nitrogen endowment pools and dominant EUNEP compliance regimes rather than merely replicating homogeneous field baselines (Table 1 and Fig. 2a to c). '
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
    'Table 1 Physical baselines and regional nitrogen regimes across the five urban-breadbasket winter wheat archetypes.\n'
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
add_block('sec-r32', '### 3.2 实验设置与基线参数规模对比', '### 3.2 Experimental Setup and Parameter Configuration')

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
add_block('sec-r33', '### 3.3 多策略综合对比实验与季内物理机制解析', '### 3.3 Comparative Experiments')

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
    '| Controller architecture | Observation track | Joint compliance (%) | Partial profit (EUR ha$^{-1}$) | Apparent NUE | Surplus S_N (kg N ha$^{-1}$) | Native N loss (kg N ha$^{-1}$) |\n'
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

# 3.4 Ablation Experiments — SECONDARY CORE (Concise causal chain, ~230 EN words, Table 3)
add_block('sec-r34', '### 3.4 关键机制消融实验与失效路径验证', '### 3.4 Ablation Experiments')

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

# 3.5 Sensitivity and Spatiotemporal Transfer Experiments (~390 EN words, Fig. 4a-d deep panel-by-panel walkthrough)
add_block('sec-r35', '### 3.5 无传感器时空迁移与卫星先验敏感性边界', '### 3.5 Sensitivity and Spatiotemporal Transfer Experiments')

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

# Section 4: Progressive 3-Stage Stress & Physical Closure (~820 EN words)
add_block('sec-stress', '## 4 气候经济压力交叉、绿色政策校准与物理闭合检验', '## 4 Multi-Factor Stress Regimes, Policy Calibration, and Physical Closure')

add_block('sec-s41', '### 4.1 气候变暖与盈余红线耦合交叉律及高肥价抗逆性', '### 4.1 Cap-Dependent Warming Crossover and Fertilizer Price Resilience')

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

add_block('sec-s42', '### 4.2 绿色生态补贴Pareto轨迹与先验激励错位风险', '### 4.2 Green Subsidy Pareto Trajectories and Prior-Incentive Misalignment')

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

add_block('sec-s43', '### 4.3 土壤库存双账核算、潜在物理解码与质量守恒验证', '### 4.3 Seasonal Soil Nitrogen Budgets, Physical Decoding, and Numerical Mass Closure')

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

add_block('sec-d51', '### 5.1 多系统结构耦合与轻量化代理压缩机制', '### 5.1 Domain-Coupled Mechanisms and Surrogate Compression Efficiency')

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

add_block('sec-d52', '### 5.2 从单田块僵化约束向跨洲校准智能控制演进', '### 5.2 Evolution from Brittle Single-Field Pruning to Calibrated Regional Control')

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

add_block('sec-d53', '### 5.3 物理适用边界、实质权衡与未来展望', '### 5.3 Mechanistic Boundaries, Trade-Offs, and Future Research Directions')

d53_p1_en = (
    'Important physical assumptions bound these findings and explain remaining cross-regime trade-offs. '
    'First, even compliant seasonal controls extract approximately 221 to 224 kg N ha$^{-1}$ from baseline soil organic nitrogen within an isolated reset winter wheat season, confirming that short-term apparent corridor compliance cannot substitute for multi-year crop-rotation stock stewardship. '
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
    'Coupling compact conformalized surrogates, warming-de-shifted analogue weather ensembles, watershed surplus safeguards, bilateral socio-economic corridor scoring and three-stage non-anticipative dynamic planning inside AgroMAS-Global advances sequential wheat fertilization from isolated stationary stations to resilient multi-continental management. '
    f'Across five contrasting archetypes, objective-preserving soft coupling maintains statistical parity with full-budget reinforcement learning across mild historical years (46 of 52 seasons tied, mean difference minus 1.94 percentage points, Holm p equals 1.00) and averages a narrow 0.58 percentage-point margin across all 180 factorial stress cells (40 wins, 93 ties and 47 losses), yet prevents soil-mining collapses (6.27-fold compliance gain over profit-only relaxation to {100*soft["region_equal"]["joint"]:.2f} percent), edges matched reinforcement learning across seven Wageningen seasons (28.57 versus 19.05 percent), leads by 5.15 and 5.61 percentage points under 1.8 and 3.5 degrees Celsius warming along the operational 40 kg N ha$^{{-1}}$ ceiling (7.19 to 8.10 percentage points under doubled fertilizer prices), compresses ensemble storage over 1,690-fold versus tree baselines (166.3 KB versus 275.52 MB) alongside 38.5 percent higher compliance and up to 49.4 percent less regret, and lifts cross-continental sensorless prior gate admission from zero to 60.00 percent. '
    'Finally, full factorial testing quantifies both a 100 EUR ha$^{{-1}}$ moderate-warming subsidy inflection and uncalibrated prior-incentive misalignment, alongside single-season soil drawdown diagnostics and double-precision accounting verification across six million daily transitions for upcoming multi-season field validation.'
)
conc_zh = (
    '通过将紧凑共形响应代理、去升温偏移天气类比集合、流域氮盈余红线、社会经济双侧走廊与三阶段非预知动态规划解耦耦合于AgroMAS-Global，本研究推动小麦精准施氮从理想平稳单田走向多洲际高压协同调控。'
    f'跨越五大典型麦区的系统评估证明，连续目标保持型软耦合在温和历史年份与充分预算强化学习统计等效（52年中有46年一致、均值差负1.94个百分点、Holm校正p等于1.00）且180格全因子平均净差为0.58个百分点（40胜、93平、47负），但在关键压力带发挥决定性防塌缩效用，较仅收益回退提升6.27倍至{100*soft["region_equal"]["joint"]:.2f}%，在7季瓦赫宁根基准取得28.57%对比19.05%优势，在1.8与3.5摄氏度升温及每公顷40千克氮主流红线下净胜PPO达5.15与5.61个百分点（肥价翻倍扩至7.19至8.10个百分点），以逾1,690倍存储压缩（166.3千字节对比275.52兆字节）取得高出树基线38.5%的达标表现并削减至多49.4%遗憾，同时把跨洲无传感器先验准入率由零拉升至60.00%。'
    '同期完成的全口径土壤氮动用拆解、适度升温每公顷100欧元补贴拐点与激励错位边界分析，以及逾六百万条日步长双精度质量账面核验，为后续多年多季田间实证提供了严谨基准。'
)
add_block('conc-body', conc_zh, conc_en)

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
