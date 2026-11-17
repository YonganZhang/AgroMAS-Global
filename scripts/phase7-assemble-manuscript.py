"""Append selected immutable figures, comparison table and evidence supplements to Markdown."""
from pathlib import Path
import json,pandas as pd,numpy as np
R=Path(__file__).resolve().parents[1];P=R/'reports/phase7';O=R/'manuscript/phase7';S=O/'supplement';S.mkdir(exist_ok=True)
if __name__=='__main__':
 facts=json.loads((P/'core-facts-v7.json').read_text());annual=pd.read_csv(R/'reports/phase6/annual-policy-metrics-v6.csv');group=['region_id','climate','cohort','policy','cap','price_multiplier','subsidy'];annual.groupby(group).agg(n_years=('year','nunique'),joint=('joint','mean'),partial_profit=('partial_profit','mean'),fertN=('fertN','mean')).reset_index().to_csv(S/'regional-scenario-metrics.csv',index=False)
 rows=json.loads((P/'decoding-nested-statistics-v7.json').read_text())['results'];pd.json_normalize(rows).to_csv(S/'satellite-decoding-all-targets.csv',index=False);pd.json_normalize(facts['bridge']['summary']).to_csv(S/'deployment-cohort-summary.csv',index=False);pd.json_normalize(facts['bridge']['paired_contrasts']).to_csv(S/'deployment-paired-intervals.csv',index=False);pd.read_json(P/'state-reconstruction-v7.json').to_csv(S/'state-reconstruction.csv',index=False)
 # Full first-unseal and corrected reused numerical evidence remains at its immutable source.
 audit=json.loads((R/'reports/phase6/benchmark-statistics-v6.json').read_text());(S/'preserved-control-statistical-evidence.json').write_text(json.dumps(audit,indent=2))
 entries=[('Unilateral controller','单侧控制器','Phase5-A4'),('Matched masked PPO','匹配掩码PPO','PPO-v6-structured-book'),('Bilateral controller','双侧控制器','Phase6-Full'),('Fixed phenological doses','固定物候剂量','DVS-N2')]
 for lang in ['EN','ZH']:
  f=O/f'MANUSCRIPT_{lang}.md';text=f.read_text();assert '## Supplementary' not in text and '## 补充材料' not in text
  table='\n| '+('Controller | Joint compliance (%) | Partial return (EUR/ha) | Fertilizer (kg N/ha)' if lang=='EN' else '控制器 | 联合达标率（%） | 部分收益（欧元/公顷） | 化肥（千克氮/公顷）')+' |\n|---|---:|---:|---:|\n'
  for en,zh,key in entries:
   x=facts['policy_primary'][key];table+=f"| {en if lang=='EN' else zh} | {100*x['joint']:.2f} | {x['partial_profit']:.2f} | {x['fertN']:.2f} |\n"
  table+='\n: '+('Primary historical context over52 Former-Held-Out seasons, equal-region averages. Partial return excludes whole-farm costs and externalities.' if lang=='EN' else '52个原Held-Out季节主历史情境的地区等权结果。部分收益不包括全部农场成本与外部性。')+'\n\n'
  anchor='### 3.2 ' if lang=='EN' else '### 3.2 ';pos=text.index(anchor);text=text[:pos]+table+text[pos:]
  figures=[('### 2.3 ','../../reports/figures/fig1_agromas_architecture_and_global_map.pdf','Global architecture and regional wheat-model archetypes. The four computational decision roles share an explicit objective. The satellite observation assay is detailed separately in the final figure.','全局架构与区域小麦模型类型。四种计算决策职责共享显式目标，卫星观测验证在最后一幅图中单独展开。','fig:architecture'),('### 3.4 ','../../reports/figures/phase6/fig2_netherlands_home_turf_and_ablation_A.pdf','Control progression, Dutch regional comparison and joint-efficiency geometry. Detached perfect-information forecasting is a reference rather than a stage in the progression. Historical public-reused Dutch seasons remain separate from the five later Former-Held-Out seasons. Global distributions use equal-region weights.','控制演进、荷兰地区比较与联合效率几何。独立的完美信息预报只是参考，不是控制演进的一步。荷兰历史公开复用季节与五个较晚的原Held-Out季节分别报告，全局分布使用地区等权。','fig:comparison'),('## 4 ','../../reports/figures/phase6/fig3_cross_system_cmip6_urban_policy_matrix_A.pdf','Climate, price, cap and subsidy stress responses. The90 stress combinations use three fixed cap populations, with retrospective empirical spread rather than confidence ribbons. Subsidy markers evaluate training-frozen rules, including groups with no qualifying rule. Climate perturbations are idealized and caps are experimental.','气候、价格、上限与补贴压力响应。90种压力组合使用三个固定上限群体，带状区域是经验离散而非置信区间。补贴标记评价训练冻结规则，并保留没有合格规则的群体。气候扰动为理想化设置，上限为实验控制。','fig:stress'),('## 4 ','../../reports/figures/phase6/fig4_global_5region_comparison_and_attribution_C.pdf','Regional nitrogen-regime transitions, paired control comparisons, non-additive ablations and native nitrogen ledgers. This selected broadside layout retains its original246mm width on a rotated figure page. Upper export is distinguished from the published bottom-loss variable, and stock change remains explicit.','地区氮情境转移、控制配对比较、非加和消融与原生氮账。选定的宽幅版式在旋转图页中保留原246毫米宽度。上边界输出与已发布底部损失变量区分，库存变化明确保留。','fig:ledger'),('## 5 ','../../reports/figures/phase7/fig5_alphaearth_64d_physical_decoding_and_field_bridge_A.pdf','Satellite fingerprints, retrospective physical probes, prior-year-input control comparison and descriptive spatial projections. Panel a contrasts interannual within-region and cross-region mean-vector cosine. Panel b uses45 combined site-years and reports nested holdout performance, within-region R² and ten-target adjusted year-null p-values. Panel c uses44 prior-year observations and preserves zero compliance for the three restricted regimes. Panel d projects a fitted probe onto real10m station pixels, not measured soil maps. Original cohort roles, retrospective product release, urban footprints and unvalidated extrapolation remain explicit in the text and supplementary notes.','卫星签名、回溯物理探针、上一年输入控制比较与描述性空间投影。a比较地区内部年际余弦与跨地区均值向量余弦。b使用45个组合场地年，给出嵌套留出表现、地区内部R²和十目标校正年份置换p值。c使用44个上一年观测，保留三个受限方案的零达标。d把拟合探针投影到真实10米站点像元，不是实测土壤图。正文与补充说明保留原队列身份、产品回溯发布时间、城市足迹和未验证外推。','fig:satellite')]
  for anchor,path,en,zh,label in figures:
   # Repeated Section4 anchor deliberately preserves Figure3 then Figure4 order.
   pos=text.index(anchor);caption=en if lang=='EN' else zh;text=text[:pos]+f'![{caption}]({path}){{#{label} width=183mm}}\n\n'+text[pos:]
  # Move detailed source provenance out of the scientific conclusion.
  en_sentence='The original pretraining source record for the matched PPO did not cover every supporting module, so its later source provenance remains supplementary rather than a retroactive claim about unlogged execution. '
  zh_sentence='匹配PPO最初的预训练源码记录没有覆盖全部支持模块，因此后来的来源佐证仍属于补充证据，不能追溯证明未记录的执行。'
  text=text.replace(en_sentence,'').replace(zh_sentence,'')
  if lang=='EN':
   text+='''## Supplementary information

### Supplementary Note 1 Evidence and target boundaries

The original first-unsealing control evidence and the later reused comparison remain distinct. Supplementary numerical files provide regional scenario means, all nested satellite targets, original cohort strata, paired intervals and state reconstruction. Native endpoint probes separate zero-fertilizer mineralization and grain nitrogen, a derived upper-boundary residual, fixed-policy harvest and published loss, and hindsight grid-management quantities. Their different conditioning policies prevent an additive interpretation. The initial pretraining source record for matched PPO did not cover every support module. Later source provenance is retained as supplementary evidence without retroactively certifying unlogged execution.

### Supplementary Note 2 Satellite provenance and spatial support

The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind. The dataset and mirror retain CC-BY4.0 licensing. The ESA WorldCover audit is credited as © ESA WorldCover project2021 / Contains modified Copernicus Sentinel data2021 processed by ESA WorldCover consortium. WorldCover classifies land cover, not crop identity, and its2021 mask does not establish annual land use throughout the satellite series. Station windows are640m squares at10m, and the macro tiles are256 by256 pixels at320m, covering81.92km rather than a5km field window. A separately defined5km mask supplies the landscape-ring summary. Agricultural candidates are retained separately and never replace original stations.

### Supplementary Note 3 Statistics and availability

All64 satellite channels enter each Ridge probe. Region-block permutation inference has only120 distinct arrangements, so exhaustive p-values retain a minimum resolution of1/120 and ten-target Holm correction cannot be treated as having5000 independent region permutations. The unbalanced44-observation prior-year window uses a separate balanced40-observation block-null sensitivity. Prior anomalies start in2019 with at least two earlier annual observations. The narrow25-observation and full59-observation deployment tables include respectively5 and15 static-soil fallback seasons. Their satellite branch is explicitly unavailable in those seasons. The paired bootstrap conditions on fitted models and its zero-width intervals for observed zero compliance do not establish zero future risk.

### Supplementary numerical files

[Regional scenario metrics](supplement/regional-scenario-metrics.csv), [all satellite targets](supplement/satellite-decoding-all-targets.csv), [deployment cohort strata](supplement/deployment-cohort-summary.csv), [paired deployment intervals](supplement/deployment-paired-intervals.csv), [state reconstruction](supplement/state-reconstruction.csv), and [preserved control statistical evidence](supplement/preserved-control-statistical-evidence.json) accompany this manuscript. Original tile URLs, exact HTTP ranges and output SHA256 hashes are retained in the satellite provenance ledger.

## Data and code availability

The manuscript package includes selected figures, bilingual Markdown, the parallel reader, LaTeX sources and the numerical supplements. Satellite inputs are accessible through the cited public mirror and upstream catalog, while original crop and control evidence remains in its immutable project records. Availability of these materials is not a statement that a new public code repository or submission has been published.

## References
'''
  else:
   text+='''## 补充材料

### 补充说明1 证据与目标边界

首次解封控制证据与后来的复用比较保持区分。补充数值文件提供地区情境均值、全部嵌套卫星目标、原队列分层、配对区间和状态重建。原生端点探针区分零肥料矿化与籽粒氮、推导的上边界残差、固定策略收获及发布损失、事后网格管理量。其条件策略不同，不能加和解释。匹配PPO最初的预训练源码记录没有覆盖全部支持模块，后来的来源佐证作为补充保留，不追溯证明未记录的执行。

### 补充说明2 卫星来源与空间支持

The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind. 数据集和镜像保留CC-BY4.0许可。ESA WorldCover核验署名为© ESA WorldCover project2021 / Contains modified Copernicus Sentinel data2021 processed by ESA WorldCover consortium。WorldCover区分土地覆盖而非作物身份，2021年掩码不证明整个卫星系列每年的土地利用。站点窗口为10米分辨率的640米方形，宏观切片为320米分辨率、256乘256像元，覆盖81.92千米，并非5千米田间窗口。景观环另用5千米掩码汇总。农业候选窗口单独保留，从不替换原站点。

### 补充说明3 统计与可用性

每个Ridge探针均使用全部64通道。地区块置换只有120种不同排列，精确p值保留1/120的最小分辨率，十目标Holm校正不能被当作有5000次独立地区置换。不平衡44观测上一年窗口另用平衡40观测开展块零分布敏感性分析。上一年异常量从2019年开始，至少需要两个更早年度观测。较窄25观测与完整59观测部署表分别包含5个和15个静态土壤回退季节，这些季节明确没有卫星分支。配对自助区间条件于已拟合模型，观测零达标得到的零宽区间不代表未来风险为零。

### 补充数值文件

本稿随附[地区情境指标](supplement/regional-scenario-metrics.csv)、[全部卫星目标](supplement/satellite-decoding-all-targets.csv)、[部署队列分层](supplement/deployment-cohort-summary.csv)、[部署配对区间](supplement/deployment-paired-intervals.csv)、[状态重建](supplement/state-reconstruction.csv)及[保留的控制统计证据](supplement/preserved-control-statistical-evidence.json)。卫星来源账保留原始切片URL、精确HTTP字节范围与输出SHA256。

## 数据与代码可用性

稿件包包含选定图件、双语Markdown、对照阅读页、LaTeX源码及数值补充材料。卫星输入可通过所引公开镜像和上游目录获取，原作物与控制证据保留在不可修改的项目记录中。提供这些材料不代表新公开代码仓或投稿已经发布。

## 参考文献
'''
  f.write_text(text)
 print('Inserted five selected figures and supplementary numerical files')
