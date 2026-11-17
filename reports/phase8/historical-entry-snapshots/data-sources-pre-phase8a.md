# 原始数据与来源

原始数据、原始响应、旧权重和封存季节只读；新下载另存并登记URL、时间、单位、版本、范围、SHA256及缺测，不覆盖旧缓存。

| 来源 | 位置/证据 | 身份与限制 |
|---|---|---|
| WUR/Zenodo15267400 | 原项目data/52.57-5.63_random_weather.csv；reports/download-receipt.json与Phase4清单 | 已有荷兰历史与LARS合成序列；两类来源分别标记；不挪作外国实测 |
| NASA POWER daily API | reports/phase5/nasa-network-preflight.json，五个nasa-probe响应及SHA | 五点2000-01-01至07网络探测全部HTTP200；非完整39年缓存，不是站点实测 |
| NASA1983可用性 | reports/phase5/nasa-1983-availability.json | HTTP200但明确移除1984前辐射字段；禁止伪造补齐 |
| CMIP6 | https://www.wcrp-cmip.org/ 与实际ESGF/NASA产品待确定 | 尚无模型/成员/基准期/目标期/降尺度数据；任务升温/CO2仅为预设敏感性档位 |
| 区域土壤 | 区域水力剖面与作物参数尚待真实来源核验 | 不把荷兰coarse/medium/fine更名冒充四国实测 |
| NVZ/水源区 | https://environment.ec.europa.eu/topics/water/nitrates_en；各国空间资料待接入 | 真实地图尚未获取；25/35/40/50为研究盈余情景，不是法定水质浓度 |
| 预报与经济 | 预报签发档案、价格/汇率/氮含量及政策版本待确定 | NASA历史天气不是天气预报；补贴/税扫描是实验情景 |

拟存原始长序列：data/global_regions/<region_id>/，只在验证来源/时间/单位/完整性后登记已取得。当前短探测在reports/phase5中独立保存，不冒充正式数据缓存。

NASA日数据文档：https://power.larc.nasa.gov/docs/services/api/temporal/daily/；辐射来源：https://power.larc.nasa.gov/docs/methodology/data/sources_fluxes/。其日数据LST/UTC属性必须保留，不能无声明地与签发时刻拼接。

区域氮输入门禁：非荷兰不得使用native荷兰沉降默认值；种子氮须有播量和含氮分数来源，沉降须有区域来源并核对PCSE实际输出。来源缺失则区域校准/评价关闭，不默填荷兰值；统一全部对照。详见method.md第二轮约束。

五区NASA完整原始日序列：`data/global_regions/<region>/nasa-power-19840101-20261101.json`，各receipt包含URL、时刻、版本、单位、无效日期及SHA256；原件只读。日期角色唯一真源`reports/phase5/global-date-split-manifest.json`及.sha256；校准前冻结，实际记录210完整季，其中独立确认52季。
真实SoilGrids原响应与补查：`reports/phase5/soilgrids-{probe,followup}-*.response`，均只读；不是农场实测。补查坐标与初始城市点分开，见`regional-integration-preregistration.md`，未据作物输出选点。
- NASA australia_wa_perth: `39ff5d144d0dc8fc372918d130c09f45f8182320bf80a47a634b47cace3efbae`
- NASA china_ncp_luancheng: `703f833fccf9ddd95c0a94b87e81b4856c24e7ff0ca9dc0a7d6100ea697e5b42`
- NASA france_paris_beauce: `72ec670007cb07b5bd66f532e04c4d987a1872ef79ee117ce14baf1e17be7b83`
- NASA netherlands_lelystad: `7ded8a8b926e5e4906d47185c1746783c335caf3391a345ca3a2f1a06970ee67`
- NASA usa_kansas_wichita: `8ac1a5866cfc0409ec0461432bd01c38745fff6b2cc64c03096679104bc3d8aa`

土壤水力输入：`data/global_regions/<region>/soilgrids-ptf-source.json`及只读receipt；`reports/phase5/regional-model-inputs/*/soil-v1-provenance.json`记录坐标、单位、原SHA、公开PTF与未测先验。原始PDF为`reports/phase5/HiHydroSoil-v2.0-Report213.pdf`。模型氮背景/初水控制不能冒充地域实测，见`regional-controls-v1.json`。

SNOMIN主论文原件：`reports/phase5/Berghuijs2024-SNOMIN-primary.pdf`及提取文本，DOI10.1016/j.eja.2024.127099；来源与SHA见v2-source-review-jobs.json。NASA实际日均温v2补充档：`data/global_regions/*/nasa-t2m-19840101-20261101-v2.json`，只读receipt及汇总nasa-t2m-v2-source-registry.json；v1原件/划分不覆盖。

v2来源裁决已批准原生总SOM定义，见`tasks/steer-phase5-native-total-som-approved.md`。荷兰采用明确注册的原生Arminda完整耕地剖面先验；其余地区仍保留原SoilGrids总SOM，使用逐层原生C:N、24年表观年龄及矿质氮先验，全部不标为田间实测。零沉降与共同种子氮是已批准的研究情景控制，不冒充地域估计。详细来源/局限见`regional-controls-v2.json`及`STAGE5C_V2_VALIDITY.md`，v1原证据不覆盖。

栾城底肥171kgN/ha来源于https://pmc.ncbi.nlm.nih.gov/articles/PMC9964450/记载900kg/ha、19%N复合肥；底肥计入220kg全季研究上限，并非重建文献的全部农户管理。60mm单次灌溉量有区域文献支持，第三次灌浆期事件明确是情景假设。

早期Train气象权重：`models/phase5/climate-v2/`；各区最早十个Train季拟合，具体日期、模型ID与权重SHA见`climate-train-freeze-v2.json`。后续1995–2009Train季用于结局/续策标签，不把已拟合自己的天气当成独立预测误差。预报仍是统计模型，不是实况NWP签发档案。

价格为明确的实验EUR控制（干物质谷价0.20EUR/kg、氮价1.5EUR/kg及倍价），不是已获取的区域市场历史序列；收入只解释为部分氮管理预算。政策扫描不等于已实施真实补贴。

正式策略与物理训练证据：225本Train处方轨迹、77,175次计划世界调用（59,974个不同执行事件序列，非独立样本），见`teacher-book-receipt-v2.json`；预报、倒推续策和各功能消融的权重来源与SHA由各freeze回执登记。正式PPO使用`PPO-source-and-input-freeze-v4.json`的59项输入。原生上边界溶质输出未计入NLOSSCUM的局限及两家独立源审查见`NATIVE_BOUNDARY_CLAIM_LIMITS.md`；完整库存/通量账不替代田间验证。

冻结最终回执：177物理世界、60,711调用、47,055不同执行序列，52独立年与7公开复用年分列；详见final-physical-book-receipt-v4.json及final-policy-evaluation-receipt-v4.json。主结果不支持全面胜出，完整边界见PHASE5_TOP_JOURNAL_REPORT.md。原235项冻结文件与706项外部源不因缓存恢复变动。

## Phase6 数据复用与身份

Phase6没有新增原始数据或研究物理模拟。仅复用Phase5的225本1995–2009 TRAIN物理干预账簿进行年份外折选参和三组新账簿PPO训练；177本旧最终物理账簿在新许可证后用于一次固定策略评分，包含52个原Held-Out及7个公开复用荷兰季节、各3种理想化气候。新评分48321行，年度种子平均后与只读旧参照合计104195行。原始物理值、来源与日期角色不改；本轮最终结果统一标Adaptive-Reused Temporal Benchmark。

新版权重、协议、统计与图件分别在`models/phase6/`、`reports/phase6/`、`reports/figures/phase6/`。独立子模块为`NUE_PCSE-Gym/pcse_gym/agromas_v6/`。C/N闭合按批准N<1e-10、C<1e-9报告原始残差，未改写物理账。内部训练账簿缓存`cache/phase6/r2/train-book-ppo-inputs-v6.joblib`含训练终端标签供环境奖励；在线91维观测不接收标签。缓存SHA在开训协议及评分许可证中冻结。
