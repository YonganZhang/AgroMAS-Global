import pathlib,json,xml.etree.ElementTree as ET,re,subprocess,ast,statistics
R=pathlib.Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text())
assets=read('reports/asset-receipt.json');environment=read('reports/environment.json');det=read('reports/deterministic-baselines.json')
xml=ET.parse(R/'reports/pytest-final-compatible.xml');s=xml.find('.//testsuite');tests={k:int(s.attrib.get(k,0)) for k in ['tests','failures','errors','skipped']};tests['passed']=tests['tests']-tests['failures']-tests['errors']-tests['skipped'];tests['seconds']=float(s.attrib['time']);tests['command']='source scripts/env.sh; cd NUE_PCSE-Gym; python -m pytest tests -q --junitxml=../reports/pytest-final-compatible.xml';tests['failure_details']=[{'test':c.attrib.get('classname','')+'::'+c.attrib['name'],'message':c.find('failure').attrib.get('message','')} for c in xml.findall('.//testcase') if c.find('failure') is not None]
rl=read('reports/rl-training-receipt.json') if (R/'reports/rl-training-receipt.json').exists() else {'status':'running','steps_run':None,'steps_per_sec':None,'wall_clock_seconds':None,'checkpoint_path':None,'eval_metrics':None}
if (R/'reports/rl-final-evaluation.json').exists():
 ev=read('reports/rl-final-evaluation.json');rl['eval_metrics']=ev;rl['checkpoint_path']=ev['checkpoint_path'];rl['normalizer_path']=ev['normalizer_path']
else:rl['eval_metrics']=None;rl['checkpoint_path']=None
hooks=[{'innovation':'recurrent_latent_state','files_and_symbols':{'pcse_gym/envs/sb3.py':['CustomFeatureExtractor.forward','StableBaselinesWrapper._observation'],'pcse_gym/agent/ppo_mod.py':['CostActorCriticPolicy','CostMlpExtractor','RolloutBufferSteps'],'pcse_gym/envs/winterwheat.py':['WinterWheat.reset','WinterWheat.step']},'contract':'Sequence state reset per episode; no hidden simulator soil layers in inference observations; separate auxiliary labels; feature/normalizer shape compatibility.'},{'innovation':'CVaR_distributionally_robust_policy','files_and_symbols':{'pcse_gym/agent/ppo_mod.py':['LagrangianPPO.collect_rollouts','LagrangianPPO.train','RolloutBufferSteps.add','RolloutBufferSteps.compute_returns_and_advantage','Lagrange'],'pcse_gym/envs/sb3.py':['get_model_kwargs'],'pcse_gym/envs/winterwheat.py':['WinterWheat.init_random_init_conditions_params']},'contract':'Episode-level tails; fixed development weather split, independent seeds and soil groups; no tuning on historical paper-reproduction set.'},{'innovation':'deterministic_safety_and_explanation','files_and_symbols':{'pcse_gym/envs/constraints.py':['ActionConstrainer.action','ActionConstrainer.reset'],'pcse_gym/agent/ppo_mod.py':['fertilization_action_constraint'],'train_winterwheat.py':['train'],'evaluate_agent.py':['evaluate_treatment']},'contract':'Filter executed action before environment step; record proposed/executed action and reasons; LLM receives read-only frozen evidence.'}]
for hook in hooks:
 hook['source_locations']=[]
 for file,names in hook['files_and_symbols'].items():
  found={};tree=ast.parse((R/'NUE_PCSE-Gym'/file).read_text())
  for n in tree.body:
   if isinstance(n,(ast.FunctionDef,ast.ClassDef)):
    found[n.name]=n.lineno
    if isinstance(n,ast.ClassDef):
     for m in n.body:
      if isinstance(m,ast.FunctionDef):found[n.name+'.'+m.name]=m.lineno
  for name in names:
   assert name in found,(file,name)
   hook['source_locations'].append({'file':file,'symbol':name,'line':found[name]})
metrics={**assets,'repo_commit_semantics':'Downloaded upstream baseline commit before documented local compatibility patches','working_source_commits':read('reports/working-source-commits.json'),'python_bin':environment['python_bin'],'environment':environment,'pytest_summary':tests,'deterministic_baselines':det,'process_exit_audit':read('reports/process-exit-audit.json'),'checkpoint_validation':read('reports/rl-checkpoint-validation.json'),'rl_probe_verification':read('reports/rl-probe-receipt.json'),'rl_training_verification':rl,'paper_total_N_sensitivity':read('reports/paper-initial-n-sensitivity.json') if (R/'reports/paper-initial-n-sensitivity.json').exists() else None,'phase2_hooks':hooks,'phase2_blueprint':str(R/'docs/phase2-blueprint.md'),'hardware':read('reports/hardware.json'),'constraint_audit':read('reports/constraint-audit.json'),'paper_reference':{'source':'compag2025rl.pdf Table 2 and Table 3; medians','N2':{'yield_t_ha':9.61,'NUE':.78,'N_surplus_kg_ha':52.6,'fertilization_kg_ha':220,'N_loss_kg_ha':45.0,'profit_kEUR_ha':1.49},'NUE_Agent':{'yield_t_ha':9.43,'NUE':.87,'N_surplus_kg_ha':27.2,'fertilization_kg_ha':190,'N_loss_kg_ha':42.6,'profit_kEUR_ha':1.44}},'completion_status':'partial_validation: official suite not green; bounded RL verification is not full paper replication'}
(R/'reports/baseline_metrics.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2,allow_nan=False))
def row(label,d):return '| '+label+' | '+' | '.join(f'{d[k]:.4f}' for k in ['yield_t_ha','NUE','N_surplus_kg_ha','fertilization_kg_ha','N_loss_kg_ha','profit_kEUR_ha'])+' |'
table='| 策略 / 口径 | 产量 t/ha | NUE | 氮盈余 kg/ha | 施氮 kg/ha | N损失 kg/ha | 利润 kEUR/ha |\n|---|---:|---:|---:|---:|---:|---:|\n'
for p,d in det['policies'].items():table+=row(p+' 均值',d['summary']['mean'])+'\n'+row(p+' 中位数',d['summary']['median'])+'\n'
for p,d in metrics['paper_reference'].items():
 if p!='source':table+=row('原论文 '+p+' 中位数',d)+'\n'
if rl.get('eval_metrics') and rl['eval_metrics'].get('status')=='completed':
 for k in ['mean','median']:table+=row('本轮LagPPO '+k,rl['eval_metrics']['summary'][k])+'\n'
viols='| 策略 | NUE合格 | 氮盈余合格 | 两者均合格 | 频率合格 | 间隔合格 | 物候合格 |\n|---|---:|---:|---:|---:|---:|---:|\n'
for p,d in det['policies'].items():
 keys=['NUE_satisfied_rate','surplus_satisfied_rate','joint_satisfied_rate','action_frequency_satisfied_rate','spacing_satisfied_rate','phenology_satisfied_rate'];viols+='| '+p+' | '+' | '.join(f'{d["summary"][k]*100:.2f}%' for k in keys)+' |\n'
report=f'''# 第一阶段：精准施肥基线复现与实现审计

## 结论

已建立独立代码与Python环境，下载并校验官方天气和原论文，完成四种确定性策略各39年的真实仿真，以及原生LagPPO+E3B训练链路验证。**官方完整测试仍为{tests['passed']}通过、{tests['failures']}失败、{tests['skipped']}跳过，不能宣称第一阶段全部验收通过。** 发布代码的部分配置、约束逻辑与论文叙述不一致；本报告区分发布代码运行结果与原论文数值。当前RL状态：`{rl['status']}`。

N2中位产量约9.605 t/ha、NUE约0.779、施氮220 kg/ha，与论文9.61、0.78、220接近；氮盈余、氮损失和利润并未全部重合。没有用测试结果调参来追齐论文，也没有将短训当作300万步复现。

## 资产与环境回执

- 项目：`{R}`。
- NUE上游原始提交：`{assets['repo_commit']}`。
- PCSE上游原始提交：`{assets['pcse_commit']}`。PCSE源文件另有项目缓存目录适配，见补丁。本地兼容提交另记于`reports/working-source-commits.json`；上游提交与本地工作提交分开保留。
- 官方天气：`{assets['weather_csv_path']}`，{assets['weather_csv_bytes']:,}字节，SHA256 `{assets['weather_csv_sha256']}`。
- 论文：`{assets['paper_pdf_path']}`，{assets['paper_pdf_bytes']:,}字节，SHA256 `{assets['paper_pdf_sha256']}`。
- 解释器：`{environment['python_bin']}`；Python 3.11.15；本轮使用CPU，未占用GPU，torch为CPU构建。

| 包 | 实际版本 |
|---|---|
'''+''.join(f'| {k} | {v} |\n' for k,v in environment['packages'].items())+f'''
完整锁文件：`reports/requirements.lock`。按作者README将rllte-core以`--no-deps`安装；`reports/pip-check.txt`如实保留5项依赖缺失/冲突，包含旧matplotlib/seaborn/pynvml精确锁版本及未安装的huggingface-hub/torchvision。E3B实际训练路径成功不等于所有rllte可选功能可用，不能声称pip check通过。

天气API原始content入口GET一度返回403；改用同一官方记录的`https://zenodo.org/records/15267400/files/52.57-5.63_random_weather.csv?download=1`成功取得63,774,426字节。原文入口：`https://www.athanasiadis.info/assets/pdf/compag2025rl.pdf`。官方天气文件中同时存在1982—2021历史年份和3001起的合成年份；`--random-weather`在此代码中也用于选择CSV提供器，不能仅由这个开关认定历史评估用了合成天气。数据软链接位于`NUE_PCSE-Gym/pcse_gym/utils/weather_utils/random_weather_csv/52.57-5.63_random_weather.csv`。

## 可复现命令

```bash
source scripts/env.sh
cd NUE_PCSE-Gym
python -m pytest tests -q --junitxml=../reports/pytest-final-compatible.xml
cd ..
python scripts/evaluate-baselines.py
python scripts/run-training.py --reward NUE --environment 2 --agent LagPPO --seed 4 --nsteps 100000 --random-weather --random-init --irs E3B --no-comet --device cpu --multiprocess --nenvs 4 --eval-freq 25000
python scripts/evaluate-rl.py <latest-model.zip> <latest-env.pkl> reports/rl-final-evaluation.json
python scripts/audit-constraints.py
python scripts/build-report.py
```

`env.sh`把PCSE用户数据、Matplotlib、临时文件和缓存限制在项目目录；不改系统HOME或其他项目环境。中文长路径导致forkserver的AF_UNIX路径过长，原生SubprocVecEnv增加可选`PCSE_MP_START_METHOD`参数，本机设为fork。这是CPU路径兼容处理，不用于CUDA多进程。

## 官方测试与必要适配

初次收集8处错误，主要为父目录`pcse/`遮蔽可编辑安装包、缓存目录尚未建立。修正PYTHONPATH及项目PCSE缓存后，剩余一个未使用的`normalization`导入导致收集失败；仅移除了该无效导入，没有删除测试或放宽断言。

其后完整运行28项：初期13通过/15失败。修正MaskedCategoricalDistribution错误继承，并把循环策略入口观测转换为参数dtype、episode_start转换为数值dtype后，循环策略5项全部通过。还从同一作者团队的PCSE-Gym固定提交恢复了缺失的model-1.zip/model-1.pkl测试夹具；这些是旧CropGym测试权重，不是CEA 2025 NUE预训练模型。

最终完整测试：**{tests['passed']}通过 / {tests['failures']}失败 / {tests['errors']}收集错误 / {tests['skipped']}跳过，{tests['seconds']:.2f}秒**；证据`reports/pytest-final-compatible.xml`与`logs/pytest-final-compatible.log`。另修复了环境1的旧WOFOST80接口迁移和ec_3.CAB文件名错误；该分支当前配置明确采用WOFOST81 Classic的N-only提供器，非CEA目标环境2，未改变本轮SNOMIN结果。剩余失败包括发布仓缺失MeasureOrNot、初始化旧随机值断言不符、NASA天气/氮浓度精确旧值不符、旧模型输出断言和奖励断言不符。没有伪造全绿结果，也没有为追齐旧数值改变测试容差。

`pcse_gym/utils/eval.py`与`evaluate_agent.py`原有循环导入已改为函数内延迟导入，使两个评估入口均能加载。科研成本函数、奖励和土壤动力学本轮未修改。补丁另存`reports/nue-compat.patch`和`reports/pcse-path.patch`；运行生成的YAMLCropDataProvider.pkl不作为源码修改提交。

## 论文协议与源码差异

原论文2.5节：Lelystad (52.57,5.63)，1983—2021共39年历史天气，七层粉壤土，初始NO3-N 70 kg/ha、NH4-N 0，固定CO2；训练用随机天气、初始N均值35/标准差15，10种子各300万步。附录B.7：学习率0.001，batch276，gamma1，clip0.2，GAE0.95，10 epochs。

发布代码：`arminda_soil.yaml`、`arminda_site.yaml`、`wheat_cropcalendar.yaml`；NO3I之和72.589687、NH4I=0、CO2=344.85；`init_random_init_conditions_params`为50±35。随机训练年份3002—5998；历史评估1983—2021。周步长7天，动作Discrete(9)，索引乘10即0—80 kg N/ha。默认训练观测38维，天气七天平均后接两层256单元Tanh策略/价值网络，另有成本价值分支。

**评估口径也有差异**：训练回调的get_nue/get_nsurplus使用日历年度统计沉降，环境info使用实际模拟的季节沉降。本轮主要表沿用evaluate_agent.py读取环境info的口径，同时在JSON中保留年度沉降的另算结果；不能挑更接近论文的一个再回称原始口径。训练脚本评估环境继承random_init=True，本轮最终独立评估明确关闭随机初始化；原生回调曲线与最终固定初始化评估分开保存。

## 确定性基线与论文比较

实际采用作者`get_standard_practices`与`evaluate_treatment`。PAGV：N1=80+0+0，N2=60+80+80，N3=60+140+40 kg/ha，日期2月17日、5月11日、6月21日；按原函数的周窗口执行。Zero-N每步0。每策略同一39年、固定初始化、原始土壤；未给规则策略另加安全过滤器。N3的140 kg/ha单次剂量超出RL动作域上限80，作为作者规则参照单列，不能当作同动作域算法比较；JSON另报动作域合格率。N1/N3/Zero-N在原论文表2/3没有直接对应行，不补造原论文指标。

{table}

合格率按episode计：NUE 0.5—0.9、氮盈余0—40（包含0），动作域为0—80 kg/ha且10 kg/ha离散网格，非零施肥至多4次，间隔至少14天，施肥日DVS 0.01—1；违规率为1减合格率。不同约束分别报告，规则策略不强行套上RL训练的软成本。原evaluate_agent.py有一处盈余下界写成严格大于0，此处采用论文公式的包含0定义。

{viols}

## 初始氮总量的单独诊断

`reports/paper-initial-n-sensitivity.json`只把NO3总量缩放到70、NH4保持0，沿用发布版本各层比例，并固定其他配置。它是已知设定差异的敏感性分析，不是按测试成绩挑参数，也不声称恢复了论文未公开的逐层初始分布。主基线表保留原发布值；当前偏差不能仅归因于这个总量差异。

## RL训练证据

首个单进程2208步探测通过完整learn并保存latest模型，原脚本打印学习阶段耗时296.138184秒，包含初末评估/绘图，约7.456步/秒；按该测量外推300万步约111.8小时，**这只是短探测含固定开销的线性估计，不是完整运行耗时**。因此本轮选择100000目标步、4环境的有界验证，优化周期仍为2208步/环境；总步数会向完整rollout取整。向量化改变每次更新采样量，属于工程训练验证配置，不冒充原论文10种子配方。

实际100k阶段回执：

```json
'''+json.dumps({k:v for k,v in rl.items() if k!='eval_metrics'},ensure_ascii=False,indent=2)+'''
```

参数前后SHA和`parameters_changed`用于证明发生更新；检查点重载并在固定39年独立评估，主要结果写入上表与JSON。原生TensorBoard原始曲线保存在检查点目录；`reports/rl-learning-curves.json`为可机读导出。短训准确指标不与论文已收敛NUE Agent直接作优劣判定。

## 第二阶段接入与必须先修的问题

完整说明见`docs/phase2-blueprint.md`，可编辑图为`figures/phase2-r4/diagram.drawio`，实际预览`diagram.png`与`diagram.svg`。图中绿色/黄色块是设计候选，尚未实现；LLM是只读终点，无环境执行权限。r4与获审r3的PNG逐字节相同（见diagram-review-equivalence.json）；实际图像由Gemini Carbon medium两轮检查，修订版PASS，原始意见保留于`reports/visual-review-first.md`和`reports/visual-review-final.md`；主控另核对真实PNG与7条连线。

1. 递归状态：`sb3.py:CustomFeatureExtractor.forward`和`StableBaselinesWrapper._observation`定义输入，`ppo_mod.py:CostActorCriticPolicy/CostMlpExtractor`接潜在状态；序列buffer及episode重置必须同步。不可把隐藏土层状态偷偷放进推理输入。
2. CVaR/分布鲁棒：`LagrangianPPO.collect_rollouts/train`、`RolloutBufferSteps`与`Lagrange`接episode尾部风险；`get_model_kwargs(soil='fast'/'slo')`定义土壤切换。按episode计算尾部，不能把步均值当CVaR。
3. 安全/解释：`constraints.py:ActionConstrainer.action/reset`在执行前检查域、预算、频率、间隔和物候；记录建议动作与实际动作。LLM只读证据，不改过滤器。

独立运行`audit-constraints.py`已证实：NUE=0.7、盈余20的合格终止样例仍得到两个成本1；一周间隔的施肥得到间隔成本0。原因是终止判断包含`!=0`、盈余下界误用NUE阈值，以及间隔项被置零。该函数本轮保留原状，修复后必须单列“修正基线”，不能把修bug收益直接包装成新算法收益。

未来开发仅用合成天气分组：训练3002—4999、开发5000—5499、压力验证5500—5998；历史39年保留固定复现审计，不用于挑超参。本轮官方短训已接触3002—5998，不能把本轮权重当成第二阶段留年协议下的无泄漏预训练；第二阶段基线和新方法必须从头训练并仅使用其训练年。按普通/干旱/极端干旱/低氮与默认/快排水/慢排水交叉分片；天气阈值仅用训练统计，五种子，同交互预算，报告全体与最差分片、配对区间。部分观测方法同测量预算比较；不从模拟器结果推断真实田间收益。

## 尚未完成与下一步

本轮不具备“官方测试全绿、完整300万步×10种子且所有表2/3数值一致”的证据。先锁定作者代码/PCSE版本及论文参数差异，明确NUE/沉降口径，建立不依赖旧遗留接口的目标环境科学测试，再修正已证实的成本函数问题。以上是继续创新前的前置工作，不应默认为本轮已完成。
'''
if rl.get('steps_per_sec') and rl.get('status')=='completed':
 report=report.replace('参数前后SHA',f"本轮有界训练实际完成{rl['steps_run']:,}步，学习阶段墙钟{rl['wall_clock_seconds']:.2f}秒（含评估和绘图），平均{rl['steps_per_sec']:.2f}步/秒；按同配置粗略线性外推300万步约{rl['projected_3M_seconds']/3600:.2f}小时。此为投影，不是已执行的300万步实验。\n\n参数前后SHA")
if rl.get('eval_metrics') and rl['eval_metrics'].get('status')=='completed':
 report=report.replace('## 资产与环境回执','短训最终39年评估：中位产量9.6966 t/ha、中位施氮750 kg/ha、NUE 0.2498，NUE与氮盈余同时合格率0%。这些结果只证明计算和评估链路走通，明显未复现原论文资源效率。学习计算完成并打印耗时后，外层执行会话返回143，收尾原因尚未查明；独立重载评估退出0、全部权重有限且无训练子进程残留，不能据此声称训练进程干净退出。\n\n## 资产与环境回执')
(R/'reports/PHASE1_BASELINE_REPRODUCTION.md').write_text(report)
print('Reports built; RL status:',rl['status'],'tests:',tests['passed'],tests['failures'])
