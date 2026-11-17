# Phase8D 首轮冻结与证据边界

2026-11-16，用户经组长批准完整Phase8D修复与重评，后续以attempt37（continue-8c00f528d36f805c.md）明确最终范围。

- 旧Phase8B/C证据及图稿完整归档，新输出使用phase8d前缀；主线另立v3.0，不改v1/v2。
- CQR紧致性按有效宏平均覆盖率下的实际校准宽度判断，保留原负数修正量排序失败；解释修订不新增Dev访问或改模型。
- 根据已见Dev/P2结果提出的NUE容差与正则化网格修改撤回。首轮控制器、适配器冻结；硬复合AU紧上限零达标、P2 LORO误差增加如实报告。
- 物理解释仅完成TRAIN内层年份选Ridge正则化、三种子解码预测平均，跳过神经辅助头训练，骨干权重保持不变。
- 完整评测按适应性基准复用解释，不是新的前瞻盲测。全部策略重新决策，物理缓存不替换旧策略轨迹。初次P2加载路径错误仅做显式基础设施恢复，保留原失败和1,915个已完成结果。
- 不宣称胜过匹配PPO、区域条件覆盖、田间保证或隐藏氮碳状态的因果识别。无遥测PPO保留冻结预处理，匹配的是信息访问及行动约束。

证据入口：reports/phase8/phase8d-protocol-amendment-first-pass-boundaries.json、phase8d-G1-width-protocol-amendment.json、phase8d-manual-recovery1.json、phase8d-core-statistics.json。
