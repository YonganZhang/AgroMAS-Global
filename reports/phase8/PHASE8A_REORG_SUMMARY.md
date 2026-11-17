# Phase8A 四专职团队与64维DL工具重整

本轮Q8.1内容已完成并通过主目录验收。只关闭文档重整；Q8.2–Q8.4未启动，等待作者批准纠正后的计划。没有训练、卫星提取、原生模拟、论文TeX/PDF改动或图1–5更新。

## 当前方法与主线

研究以Baja等CEA 2025（237:110554）及NUE_PCSE-Gym为开源底座，四专职团队是核心。气象端ClimateForecastAgent、地理城市生态端UrbanEcoSafetyAgent、社会经济政策端SocioEconomicPolicyAgent、核心农艺统筹端CoreAgronomicAgent共同调用统一DL农田响应工具，Core承担调用协调，不增加第五成员。

原始64维只进入DL数值后端，不进智能体提示、答复或筛选任务。DL拟融合卫星先验、可观测天气、DVS和候选三阶段计划，返回带单位与校准记录的产量、籽粒N、S_N、NUE响应；智能体执行当前剂量后按下一前缀再查询。WOFOST C/N仅作离线标签、物理解释与最终核验。S_N是盈余，不能称淋溶或水质浓度。

旧树非线性不足是升级动机，不是已单独识别的原因；Phase7 0%仅限定所测线性补全接冻结树的44行逐年接口。荷兰主场和五区超越CEA仍是目标，没有Phase8新实验数字。早期TRAIN无同期卫星、回溯产品发布和52+7复用队列身份均保留为后续门槛。

## 真源与文件

- `_wiki-methodology/_wiki/method.md`：四角色结构化输入输出、DL工具、离线解释、时序与公平对照合同，历史全文保留。
- `_wiki-methodology/_wiki/socratic-logic-and-evolution.md`：CEA二次研究、Phase1–7演进及六大科研概念，历史全文保留。
- `_wiki-methodology/_wiki/paper-storyline/versions/storyline-v2.0.md`、`_current.yml`、`CHANGELOG.md`及新evidence：纠正后设计，状态planned-awaiting-user-execution-approval。v1.0原文不变。
- `_wiki-methodology/_top/_decisions/2026-11-15-v8-4agent-64d-dl-surrogate-tool-architecture.md`：当前架构决定。
- `_codemap.md`2459字节、`_meta/_data_sources.md`3922字节，均≤5000；压缩前全文快照在`historical-entry-snapshots/`，原信息未丢失。
- `_wiki-methodology/_top/_questions/Q8.md`：精确纠正后的问题与四项任务。标题和状态经官方CLI；CLI无setter的答清/gate字段仅在epoch25明确批准后通过官方TOP事务API修改，IDs/状态保留，日志可追溯。
- `reports/phase8/method-framework-v8/diagram.drawio`及PNG/SVG：正式三层图，14业务节点加标题/图例/图注共17节点、21连线。三条实线为已有来源索引，18条虚线为计划中的DL/审计/四端/控制/评价，无原始64维进入智能体的连线。
- `reports/phase8/superseded-epoch23/`：废止草案及其旧审查，明确不作为当前验收。所有本轮创建/修改文件见`changed-files.txt`，原始执行指令与两项流程例外也在本目录留存。

## 检查实际结果

主目录执行的命令与原始输出分别在postmerge/final命名的JSON和文本回执中。

- `plan check`：退出0，无错误；仅原Q2与作者指定长Q8标题的文字长度提醒。
- `sixone-cli.py plan validate .`：errors=[]，verdict=warn仅QA_TEXT_LONG；未修改全局阈值掩盖提醒。
- `sixone-cli.py doctor .`：verdict=ok，block=0、warn=0、info=2。
- `validate_drawio.py reports/phase8/method-framework-v8/diagram.drawio`：ok=true，errors=[]，17节点/21边。
- `method_diagram.py check`：ok=true，issues=[]；源/规格/三个图产物SHA均匹配。
- `python3 reports/phase8/verify-preservation.py postmerge`：原1782、Phase7新增242、2188先前跟踪证据/源码及Q1–Q7/v1.0八份文件全部不变。该检查只读旧文件，新回执只写Phase8。

Gemini Carbon high、DeepSeek Flash high、Kimi K3.1 Pro对纠正版实际审查并取得三个退出码0，无实质性阻塞；三者均查看当前PNG。Claude当前Opus未实际执行，刷新检查后Sonnet也无兼容可用账号，已记录缺席，不计作通过，未擅用旧4.6。达到3人quorum，不声称4人全通过。旧epoch23审查未复用。Kimi的路径建议经JSON解码、文件存在与SHA校验未能复现，已改为直读中文序列化，路径值未变。见`corrected-review-final-receipt.json`、`review-finding-reconciliation.json`及reviews原件。

## 合并与清理

科学设计分支末提交`b2ae0e4c68c7bde628016a042122149c404b224d`已合入master，合并提交`168e15be6f68fa4af24ba3251807444a1cd62515`。主目录TOP纠正提交`78f6da1`保留，合并前后Q8、计划总表、审计日志SHA完全相同，没有采用工作树旧TOP。见merge-verification.json。

已移除临时工作树和已合并分支；原数据与NUE/PCSE不变，NUE仍0354e3c，PCSE仍d1fe6d29。原始外援运行材料保存在忽略且本地私有的cache/phase8a-private-review-runs/，账号/额度元数据未入Git。见worktree-cleanup.json和private-review-archive.json。

本轮没有未完成的Q8.1内容。后续DL构建、四端接入、荷兰/五区实验和图稿重构全部等待另行批准，不自动开展。
