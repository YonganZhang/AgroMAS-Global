# Phase8 五专职团队与核心实验

当前执行授权为 `continue-ef655327bd618e46.md`（attempt27）。按 G1 → 条件满足后的 G2 → G3 执行；Q8.4、90格压力面和论文图稿未启动。

- 协议与数据角色：`phase8b-preregistered-protocol.json`、`phase8b-data-role-contract.md`。
- 当前可编辑方法图：`method-framework-v8/diagram.drawio`、PNG/SVG；五个专职端显式列出，原始64维仅留在数值后端，WOFOST为外部只读裁判；`phase8b-diagram-factual-caption.md`澄清36维非线性骨干与64维低秩适配器的组成，以及物理解码不回训。
- TRAIN拟合：`phase8b-train-model-freeze.json`、`phase8b-ExtraTrees-freeze.json`，固定两结构、三种子、年份整组外折；`phase8b-TRAIN-CV-diagnostics.json`只代表条件天气输入的训练期留出误差。
- G1实际结果：`PHASE8B_G1_GATE_REPORT.md`、`phase8b-G1-verdict.json`，两结构、两信息轨均通过；首注册MLP继续作为主模型。
- G2/G3当前进度：全部2017个完成季已核验，193项最终回归通过。G1通过，但Full9.67%及Sensorless4.00%联合达标率不及对应PPO；见`PHASE8B_CORE_EXPERIMENTS_G1_G2_G3_REPORT.md`。原技术中止及授权恢复详见`PHASE8B_NATIVE_HALT_AND_REPAIR_REPORT.md`，旧证据未覆盖。
- 实际物理进度：`phase8b-physical-progress.jsonl`；逐日守恒独立检查：`phase8b-daily-ledger-progress.jsonl`。全量结束后另存最终回执，未结束不预称通过。
- `phase8b-canonical-test-receipt.json`及`phase8b-canonical-pytest.log`记录实际测试；失败的环境/目录准备尝试另留原日志。
- P1不使用未来卫星；P2明确回溯外折适配，40 Former-Held-Out与4 Public-Reused分列，只有G1通过后才执行。
- 历史Phase8A设计、图和入口在`phase8a-*`；`superseded-epoch23/`仍是更早废止草案，均不是当前执行验收。
- `verify-preservation.py`只读核验原1782、Phase7新增242、2188既有源码/证据及Q1–Q7与v1.0；不改旧资产。

G1两个结构均失败时按规则终止，不以代码测试通过代替科研门槛通过，也不声称五区或荷兰获胜。
