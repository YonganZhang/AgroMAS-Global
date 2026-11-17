# Phase8B 五专职与核心门槛执行

授权来源为 `reports/phase8/continue-ef655327bd618e46.md`，attempt27。

P1：1995–2009 TRAIN训练天气土壤主模型，2010–2014 Dev只作一次冻结后的校准及门槛验证。最多两个网络结构；两个均失败则停止，不执行G2/G3。

P2：明确作为回溯逐年/逐地区外折交叉验证。主模型冻结，空间适配器仅用各外折训练标签，超参数提前冻结；40 Former-Held-Out与4 Public-Reused分列，不声称未触碰盲测或前瞻部署。

在线五专职为SpatialTwinSurrogateAgent、ClimateForecastAgent、UrbanEcoSafetyAgent、SocioEconomicPolicyAgent、CoreAgronomicAgent。WOFOST81-SNOMIN在团队之外作为只读物理裁判。生态端盈余与经济端NUE约束分立。原始64维仅留在PyTorch数值后端。

只执行G1及条件满足后的G2/G3；Q8.4、90格压力面、论文图稿未授权启动。旧方法、源代码和负结果保留。
