[Role boundary] worker: Before new work, obtain its full scope and restrictions in English from the leader; an assignment does not expand role authority. The stored role definition is localized UI metadata. Authorized workspace: /mnt/data/yongan-admin-2/projects/顶刊论文. Preserve module ownership; report out-of-scope changes to the leader before editing.

# Phase 8A Assignment (`Q8.1`): Reorganize Scientific Logic, Update Six-in-One (`六合一`) Architecture, Method Diagram, and `Plan Q8`

> **CRITICAL SCOPE GUARD**:
> This assignment is **ONLY** `Q8.1` — updating the project's Six-in-One (`六合一`) truth sources, scientific storyline (`storyline-v2.0`), editable 3-layer architecture diagram (`reports/phase8/method-framework-v8/`), and `Plan Q8`.
> **Do NOT** run new Python training, extract new satellite data, edit manuscript TeX/PDF, generate paper figures (`Fig 5` etc.), or start `Q8.2–Q8.4` in this run.
> **Preserve** all immutable Phase 1–7 artifacts, ledger CSVs, manuscript files, git history, and `Q1–Q7` plan records completely intact (`1782` legacy files + `242` Phase 7 files untouched).

---

## 1. Repository & Worktree Isolation

1. Work inside `/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体`.
2. Create an isolated root worktree (no `NUE_PCSE-Gym` source changes needed in `Q8.1`; leave `NUE_PCSE-Gym` and `pcse` untouched):
   - e.g. `git worktree add ../worktrees/agromas-phase8a -b phase8a/reorganize-six-in-one master`
3. Do all edits and `plan` / `validate_drawio.py` / `doctor` checks inside that isolated worktree, then merge cleanly into `master`, run post-merge checks in main repo, and remove the worktree + branch (`git worktree remove` & `git branch -d`).

---

## 2. Exact Architectural & Scientific Logic Pivot (Why Phase 8 Exists)

The PI (user) clarified the exact intended role of Google AlphaEarth 64-D satellite embeddings and the multi-agent architecture:
- **What went off-track in Phase 7**: Phase 7 fitted linear Ridge probes to impute dynamic simulator state (`LAI/SM/crop N`) and stuffed those predictions directly into a **frozen ExtraTrees controller** originally trained on privileged full-state telemetry — yielding `0%` joint compliance under year-grouped cross-fitting and turning the 64-D vector into a negative-only boundary story.
- **What the PI actually wants (Clean 3-Layer Closed-Loop Architecture)**:
  1. **Layer 1 — Agent-Assisted Physical Decoding & Latent Feature Selection (`智能体物理反解与特征筛选`)**:
     - Map and interpret the 64-D AlphaEarth satellite black box against WOFOST81-SNOMIN physical mechanisms (persistent soil nitrogen mineralization supply, N loss vulnerability, water-buffering / corridor capacity) using strict region-and-year cross-validation without leakage.
     - Have a Feature-Selection Agent identify and prune noisy/collinear channels so only compact, physically grounded latent channels/features are passed downstream.
  2. **Layer 2 — Deep Learning Surrogate Model (`64维深度学习作物-土壤响应模型`)**:
     - **64-D embeddings are built for Deep Learning, NOT raw heuristic feeding into legacy frozen trees.**
     - Train a nonlinear Deep Learning surrogate model (within the PyTorch / project-compatible stack, strictly observing train/eval boundaries and cohort integrity) taking **selected 64-D satellite latent priors + observable weather + observable phenology (`DVS`) + fertilization doses** (with **zero** privileged internal simulator sensors like `LAI/SM/crop N` or hidden soil pool leaks) to accurately predict seasonal yield, grain N, surplus $S_N$, $\mathrm{NUE}$, and bilateral corridor compliance probability/quantiles.
  3. **Layer 3 — Multi-Agent Tool-Calling Bilateral Control (`多智能体将深度学习模型作为工具调用的闭环决策`)**:
     - Instead of heuristic ExtraTrees or forcing uncalibrated linear proxies into frozen trees, the cooperative agents (`ClimateForecastAgent`, `UrbanEcoSafetyAgent`, `SocioEconomicPolicyAgent`, `Coordinator`) invoke the trained **Deep Learning Surrogate Model as an explicit callable tool** (`tool-calling`) — querying counterfactual dose candidates, checking bilateral nitrogen corridor constraints ($0.50 \le \mathrm{NUE} \le 0.90,\ 0 \le S_N \le S_{\mathrm{cap}}$), and selecting optimal fertilization schedules strictly under **sensor-free / observable-only deployment conditions**.

All documentation must distinguish **already verified Phase 1–7 facts** (solid/verified) from **Phase 8 hypotheses & targets to be tested in `Q8.2–Q8.4`** (explicitly marked `planned / to be verified`, never claimed as already achieved).

---

## 3. Concrete Six-in-One (`六合一`) & Method Diagram Deliverables

### A. Update `_wiki-methodology/_wiki/socratic-logic-and-evolution.md`
- Add a clear top-to-bottom section organizing:
  1. **完整演进脉络（Phase 1–4 诊断 $\to$ Phase 5–6 双侧控制理想遥测基准 $\to$ Phase 7 线性硬塞旧树失败诊断 $\to$ Phase 8 终局三层正循环）** — clearly stating why `Q1–Q7` are preserved as historical stepping stones and why `Phase 7`'s `0%` rate came from the wrong interface (`linear state imputation -> frozen ExtraTrees`), not a proven upper limit of the 64-D satellite vectors.
  2. **新版 SCI 六大核心科研概念（Phase 8 / `storyline-v2.0`）**：
     - **科研缺口（Research Gap）**
     - **破局工具 / 过桥杠杆（Bridging Lever：三层耦合，而非单一算法）**
     - **两个本质科研问题（规律之问 + 无传感器闭环决策之问）**
     - **科研主线（`机理基准与失败诊断 → 64维反解与智能体选特征 → 无传感器深度学习代理 → 智能体调用DL工具闭环控制`）**
     - **逻辑构筑（正/反/公平消融端、时间/空间/分布外迁移端、物理真账守恒端）**
     - **整体故事与五张主图蓝图（Fig 1–5 预期各自回答哪一问；标明 Fig 5 将升级为三层架构正向检验，待 Q8.2–Q8.4 实测后填充，不预写虚假数值）**。

### B. Update `_wiki-methodology/_wiki/method.md`
- Add a clean, prominent top-level section **“Phase 8 目标三层架构：智能体特征选择 $\to$ 64维深度学习模型 $\to$ 智能体工具调用双侧控制（候选设计合同，待 Q8.2–Q8.4 实现验证）”** defining exact inputs, outputs, units, causality boundaries (`t-1 < t` vs spatial priors, zero future weather leakage, zero privileged simulator sensors in deployment inputs), offline tool interface contract (`DL surrogate tool call`), and fair ablation comparisons (Weather-only DL tool, Static-prior DL tool, Unselected-64D DL tool, Agent-selected-64D + DL tool, Matched Observable-Only PPO, Full-telemetry Oracle reference).
- Preserve existing Phase 5–7 technical boundary sections cleanly below under historical/reference methodology so no existing scientific record is lost.

### C. Create `storyline-v2.0` in `_wiki-methodology/_wiki/paper-storyline/`
1. Create `_wiki-methodology/_wiki/paper-storyline/versions/storyline-v2.0.md` defining the Phase 8 unified Q1 top-journal storyline (marking `status: planned-awaiting-user-execution-approval`, keeping honest separation between completed Phase 5–7 baseline evidence and pending `Q8.2–Q8.4` deep-learning & tool-calling validation).
2. Update `_wiki-methodology/_wiki/paper-storyline/_current.yml` to point to `storyline-v2.0`, preserving `storyline-v1.0.md` in `versions/` and updating `manuscript_claim_ceiling` cleanly.
3. Append a concise entry to `_wiki-methodology/_wiki/paper-storyline/CHANGELOG.md` explaining the transition from `storyline-v1.0` (`Q5–Q7`) to `storyline-v2.0` (`Q8`).

### D. Record Architectural Decision in `_wiki-methodology/_top/_decisions/`
- Create `_wiki-methodology/_top/_decisions/2026-11-15-v8-agent-feature-selection-dl-tool-architecture.md` documenting:
  - What failed / got misaligned in Phase 7 (`OUTBOX epoch 21`),
  - The PI's explicit correction (`64-D vector -> Deep Learning model -> Multi-Agent calls DL model as a tool + feature selection`),
  - Acceptance gates required before claiming success in `Q8.2–Q8.4`.

### E. Update `_codemap.md` and `_meta/_data_sources.md` (Keep Each <= 5 KB, Accurate & Concise)
1. `_codemap.md`: Add concise `Phase 7 已落盘入口` (`pcse_gym/agromas_v7/`, `scripts/phase7-*.py`, `reports/phase7/FINAL_CLOSEOUT_V7.md`) and `Phase 8 规划入口（待 Q8.2–Q8.4 创建）`, staying strictly under 5 KB.
2. `_meta/_data_sources.md`: Add a concise `## Phase7 真实卫星与辅助来源` section documenting the verified `2017–2025` Source Cooperative AlphaEarth `64-D` extraction (`45` site-years, `184,320` 10 m pixels, dequantized L2 norm bounds, catalog `2017–2024` vs mirror `2017–2025` distinction, ESA WorldCover 2021 cropland audit, station-vs-SoilGrids coordinate offsets) plus existing Phase 5–6 provenance intact.

### F. Create Editable 3-Layer Method Framework Diagram (`content-technical-roadmap`)
- Inspect `/mnt/data/yongan-admin-2/.ai-shared/skills/share-technical-roadmap/SKILL.md`, `references/method-framework.md`, `references/layout-and-tools.md`, and `scripts/validate_drawio.py`.
- Generate `reports/phase8/method-framework-v8/diagram.drawio`, `diagram.png`, and `diagram.svg` depicting the clean 3-layer architecture + data sources & counterfactual ledger:
  - **Verified / Read-only inputs (solid edges)**: Observable weather + DVS phenology + Prior-year/site 64-D AlphaEarth pixels; WOFOST81-SNOMIN C/N ground-truth ledger (`343` plans/season, read-only).
  - **Planned Phase 8 pipeline (dashed edges / clearly marked `待实现验证`)**:
    1. *Layer 1*: Physical Decoding & Feature-Selection Agent (selects physically grounded latent channels from 64-D);
    2. *Layer 2*: Sensor-Free Deep Learning Response Model (predicts seasonal harvest/grain N/surplus/NUE distribution without internal telemetry);
    3. *Layer 3*: Multi-Agent Tool-Calling Bilateral Controller (`EcoSafety` corridor filter + `SocioEcon` selector + `Coordinator` calling the DL tool iteratively at stages 1–3).
- Run `python3 /mnt/data/yongan-admin-2/.ai-shared/skills/share-technical-roadmap/scripts/validate_drawio.py reports/phase8/method-framework-v8/diagram.drawio` and visually inspect `diagram.png` to verify zero overlapping labels, clear edge labels ("what is passed"), solid vs dashed legend consistency, and clean Chinese readability.

### G. Update `Plan` via Official `plan` CLI (`Q8`)
1. Run `plan` commands inside the repo/worktree (NEVER hand-edit `_task_plan.md` structure directly — use the CLI!):
   - `plan ask "Q8：智能体物理特征选择与64维深度学习模型能否作为决策工具支撑无传感器双侧精准施肥？" --done-when "完成64维物理特征选择、无传感器深度学习代理训练与因果交叉验证、及多智能体工具调用双侧控制闭环评测（均在严格无未来/无隐藏遥测泄漏下跑通并合入主干）"`
   - Add 4 attempts to `Q8`:
     - `Q8.1`: `重整六合一架构文档、storyline-v2.0、三层方法框架图与Q8工作本` (`--gate "validate_drawio通过 + sixone-cli.py doctor通过 + plan check通过"`) — mark `start` then `done` in this run with evidence paths!
     - `Q8.2`: `实现智能体辅助64维卫星物理反解与稳健特征选择模块` (`--gate "LOYO/LORO与地区内部年际诊断 + 通道筛选消融 + 单测通过"`)
     - `Q8.3`: `训练与严格验证64维特征驱动的无传感器深度学习响应模型` (`--gate "严格时间/空间留出对比纯气象/静态土壤基线 + 校准/残差误差达标 + 单测通过"`)
     - `Q8.4`: `实现多智能体调用深度学习工具闭环控制、全面对比实验与论文重构交付` (`--gate "在无隐藏传感器输入下测出联合达标率/收益/氮账提升 + 图5更新 + 三方外援审查与全测通过"`)
   - Set focus: `plan focus Q8`
2. Run validation checks (after `Q8.1` is marked done):
   - `plan check`
   - `python3 /mnt/data/yongan-admin-2/.ai-shared/skills/share-top/scripts/sixone-cli.py plan validate .`
   - `python3 /mnt/data/yongan-admin-2/.ai-shared/skills/share-top/scripts/sixone-cli.py doctor .`
   - Save a concise closeout summary to `reports/phase8/PHASE8A_REORG_SUMMARY.md` recording commit SHA, diagram validation output, `plan check` / `doctor` output, and `1782 legacy + 242 phase7` integrity verification (`python scripts/phase7-verify-delivery.py --label=phase8a` or read-only check confirming zero regressions on Phase 1–7 assets).

---

## 4. Merge, Cleanup & Doorbell

1. Commit cleanly in the worktree branch, merge into `master` (`git merge --no-ff`), run `plan check` and `doctor` + Phase 1–7 asset preservation check on `master`.
2. Verify `git status --short` is clean, remove the Phase 8A worktree (`git worktree remove`) and merged branch (`git branch -d`).
3. Populate `/mnt/data/yongan-admin-2/.codex/agent-bus/mailboxes/team-4031428b3351/team-832/OUTBOX.json` (with paths to `socratic-logic-and-evolution.md`, `method.md`, `storyline-v2.0.md`, `_current.yml`, `2026-11-15-v8-agent-feature-selection-dl-tool-architecture.md`, `_codemap.md`, `_meta/_data_sources.md`, `Q8.md`, `reports/phase8/method-framework-v8/diagram.png`, and `reports/phase8/PHASE8A_REORG_SUMMARY.md`) and ring doorbell (`attempt-epoch 22`, `status completed`).

---
[Agent Bus delivery contract]
- Language follows the reader: write all visible chat progress, explanations and final replies in Simplified Chinese, even for a leader-assigned task. Write machine-only tasks, inter-agent messages, OUTBOX narrative, doorbell --summary, tool-call explanations, commands and diagnostic logs in English. Include a concise Chinese ui_summary in OUTBOX for Cards display only; keep summary in English. Chinese --brief, decision questions/options, UI labels, exact paths, user quotations and requested Chinese deliverables retain their intended language.
- First pin down the expected result (what to deliver, how to verify it); if the leader left it vague, state your interpretation in the result.
- Decide small, reversible issues within the granted scope yourself and note them in the result. Batch decisions that exceed the scope or change direction and raise them once, explaining the background in plain words a junior programmer or student can follow, each with A/B/C options and a recommended one (unanswered questions default to the recommendation); do not interrupt for trivia. Send user-level decisions to the leader via OUTBOX and `--status waiting_user`; the leader opens the decision card for the user. Keep working on unaffected parts while waiting.
- Think through the later steps before starting and raise foreseeable issues together.
- Never monitor background job logs with a bare `tail -f` (e.g. `tail -f` / `tail -n +1 -f`) without --pid; bind it to the process (`tail --pid=$PID -f <logfile>`) or poll with a bound, so `tail -f` cannot hang forever after the job exits.
- Hand-in: write the conclusion, artifact paths, verification commands and results, and open items to OUTBOX; if you cannot deliver, state the step you are stuck on, the cause, and who must decide what. Do not paste long logs; the leader reads only OUTBOX and code changes.
- Task file: /mnt/data/yongan-admin-2/.codex/agent-bus/mailboxes/team-4031428b3351/team-832/INBOX.md; write results to: /mnt/data/yongan-admin-2/.codex/agent-bus/mailboxes/team-4031428b3351/team-832/OUTBOX.json
- Then ring the doorbell (stuck: --status blocked; waiting for a decision: --status waiting_user):
  `agent-bus doorbell --leader team-4031428b3351 --worker team-832 --job-id lead-team-4031428b3351-team-832-20261115T202332-930334 --attempt-epoch 22 --status completed --summary "<one-line conclusion>"`
