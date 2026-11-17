# STEER CORRECTION (attempt_epoch >= 23): Align Q8.1 with Original 4-Agent Team + 64-D DL Surrogate Tool Architecture

**Target Project Repository**: `/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体`

---

## 1. URGENT CORRECTION TO IN-PROGRESS Q8.1 DRAFT

The user explicitly corrected our framing at `2026-11-15T20:38`:
1. **Agents NEVER read, interpret, or do feature selection on raw 64-D satellite vectors.** Agents 100% cannot understand raw 64-D latent vectors (`A00..A63`). Drop every mention of "agent-side 64-D feature selection / agent-driven 64-D physical inversion".
2. **Recover and preserve the original Research Core**: All of our work is **secondary research upgrading Baja et al. (*Computers and Electronics in Agriculture / CEA* 2025, `237:110554`, `NUE_PCSE-Gym`)** via a **4-Agent Cooperative Team (`AgroMAS-Global`)** operating across **4 system ends** and **5 Global Urban-Wheat Archetypes** (`NL Lelystad`, `CN Luancheng`, `US Wichita`, `FR Beauce`, `AU Perth`):
   - **Climate / Weather End (`ClimateForecastAgent` / 气象端)**: seasonal weather trajectory, rainfall/drought/heat extremes, leaching and volatilization weather risk.
   - **Geo / Soil-Landscape & Urban Eco-Safety End (`UrbanEcoSafetyAgent` / 地理与城市生态端)**: spatial soil-landscape heterogeneity, nitrate leaching / groundwater & peri-urban ecological safety corridor (`0 <= S_N <= S_cap`).
   - **Socio-Economic & Policy End (`SocioEconomicPolicyAgent` / 社会经济与政策端)**: N price, farmer profit, policy incentives/subsidies, bilateral NUE & grain-protein compliance (`0.50 <= NUE <= 0.90`).
   - **Core Agronomic Mechanism Coordinator (`CoreAgronomicAgent` / 农田机理统筹端)**: phenology (`DVS`) and crop N demand-supply coordination across the 3 topdressing stages.
3. **Exact Role of Deep Learning & 64-D AlphaEarth Satellite Embeddings (`深度学习模型做代理模型的工作`)**:
   - **Deep Learning** builds the nonlinear **Crop-Soil Agronomic Surrogate Model (`DL Surrogate Model`)** to replace/upgrade the shallow paired `ExtraTrees` proxy (Phases 5–6).
   - Inside this **DL Surrogate**, **64-D Google AlphaEarth satellite embeddings** (capturing hard-to-measure local geographic, soil, texture, drainage, and micro-field properties) are fused with **observable meteorological time series, crop phenology (`DVS`), and candidate fertilization actions** to predict seasonal yield, grain N, surplus/leaching `S_N`, and `NUE` (with calibrated uncertainty) without needing expensive in-situ soil-state sensors at deployment time.
   - Offline `WOFOST81-SNOMIN` C/N ground-truth diagnostics validate *why* the DL Surrogate works physically (bridging 64-D representation to crop-soil physics as an offline scientific interpretability audit, NOT as raw vector input to LLM agents).
   - The **4-Agent Cooperative Team** calls this trained **DL Surrogate Model as its structured counterfactual decision-support tool** (predicting domain outcomes & risks for candidate 3-stage topdressing plans) to beat the 2025 *CEA* single-agent PPO baseline both on the Netherlands home turf (`NL Lelystad`) and across all 5 global regions.

**Action on existing epoch 22/23 edits**: If you already created or drafted `Q8`, `Q8.1–Q8.4`, `socratic-logic-and-evolution.md`, `method.md`, `storyline-v2.0.md`, `_decisions/...`, or `diagram.drawio` under the previous wording, **revise all of them** (including updating/rewording `Q8` & `Q8.1–Q8.4` via the official `plan` CLI) before committing, validating, or merging!

---

## 2. CRITICAL SCOPE GUARD & APPROVED CANONICAL `plan` EXCEPTION

- **SCOPE GUARD — ONLY `Q8.1`**:
  - Update **only** `六合一` (6-in-1) methodology & repository docs, `paper-storyline` (`storyline-v2.0.md`), the editable 3-layer architecture diagram (`diagram.drawio` + `.png` + `.svg`), `Plan Q8` (`Q8` + `Q8.1–Q8.4`), and validation checks.
  - **STRICTLY DO NOT** train any Deep Learning model, run Phase 8 experiments, edit manuscript `.tex`/PDF, or draw paper figures in `Q8.1`! Wait for explicit user approval of this corrected plan before `Q8.2–Q8.4`.
  - **PRESERVE ALL LEGACY & PHASE 7 ASSETS**: Do NOT alter or delete Phase 1–7 artifacts (`1782` legacy assets + `242` Phase 7 assets verified on `master`). Keep `Q1–Q7` workbooks byte-for-byte untouched!
- **APPROVED WORKFLOW EXCEPTION (`phase8a_plan_canonical_main = A`, already approved in epoch 23)**:
  - Keep all non-`_top` edits (`_wiki/`, `paper-storyline/`, `_decisions/`, `_codemap.md`, `_meta/_data_sources.md`, `reports/phase8/`) in an **isolated git worktree + named branch** branched cleanly from current `master`.
  - Use the official `plan` CLI from the worktree (which writes canonical primary `_wiki-methodology/_top/`), and commit `_top` cleanly while verifying `Q1–Q7` workbooks remain byte-for-byte untouched.
  - At wrap-up, verify all checks, merge cleanly into `master`, remove the worktree and temporary branch cleanly, write `OUTBOX.json`, and ring the doorbell.

---

## 3. REQUIRED HONEST EVOLUTION TRACE (Zero Fabricated Numbers)

Ensure `socratic-logic-and-evolution.md`, `method.md`, `storyline-v2.0.md`, and `_decisions/...` state the exact, factual arc:
- **Basis**: Secondary research building directly on Baja et al. (*CEA* 2025, `237:110554`, `NUE_PCSE-Gym` single-agent PPO in NL).
- **Phase 1–4**: Exposed pseudo-convergence / single-region unilateral limitations (e.g., CF-GRU / early single-site baselines lacking cross-regional & bilateral rigor).
- **Phase 5–6 (`52` `Former-Held-Out` seasons, 5 regions + bilateral corridor `0.50 <= NUE <= 0.90`, `0 <= S_N <= S_cap`)**: Elevated problem to **4-Agent Cooperative Team (`AgroMAS-Global`)** across **5 Global Urban-Wheat Regions** (`NL`, `CN`, `US`, `FR`, `AU`), lifting joint compliance from `6.67%` (unilateral) to `21.88%` (4-Agent Bilateral using 64-tree paired `ExtraTrees` proxy), yet still trailing matched masked single-agent `PPO` (`23.57%` global; `NL`: `Full v6 = 20.0%` vs `PPO book v6 = 26.67%`, `Forest = 40.0%`) because the shallow tree proxy poorly captures nonlinear local soil/field differences and weather-crop dynamics.
- **Phase 7 (`45` real site-years of 10 m AlphaEarth embeddings, `184,320` pixels, `2017–2025`; `44` prior-year `t-1` bridge seasons)**: Linear Ridge state imputation from `t-1` 64-D embeddings into a **frozen `ExtraTrees`** proxy yielded `0%` joint compliance — proving raw 64-D spatial embeddings neither work via linear imputation into frozen shallow trees nor belong inside agent prompts.
- **Phase 8 Corrected Architecture (`Q8`)**: Keep the **4-Agent Cross-System Team (`Climate`, `Urban-Geo`, `Socio-Econ`, `Core Agronomic`)** as the decision-making core; **replace the shallow `ExtraTrees` + linear probe with a unified Deep Learning Surrogate Model (`DL Surrogate`)** that digests `64-D AlphaEarth embeddings + weather + phenology + candidate doses` to predict structured yield/grain-N/`S_N`/`NUE` outcomes and uncertainty; have the **4-Agent Team invoke this DL Surrogate Tool** to negotiate and optimize 3-stage fertilization decisions across NL and all 5 regions. State clearly that Phase 8 (`Q8.2–Q8.4`) experiments are **planned (not yet run)** — report **zero fabricated Phase 8 numbers**.

---

## 4. EXACT DELIVERABLES FOR `Q8.1`

1. **`_wiki-methodology/_wiki/socratic-logic-and-evolution.md`**:
   - Update with the honest `Phase 1–4 -> Phase 5–6 -> Phase 7 -> Phase 8 Corrected Architecture` evolution narrative and the updated **Six Core Scientific Concepts (六大科研核心词汇)**: Research Gap, Bridging Tool (`64-D DL Surrogate + 4-Agent Decision Framework`), Essential Scientific Question, Methodological Mainline, Logical Construction, Overall Storyline.
2. **`_wiki-methodology/_wiki/method.md`**:
   - Add a clear top-level **Phase 8 Master Methodology (`AgroMAS-Global v8`: 4-Agent Team Powered by 64-D Deep Learning Surrogate Tool)** section specifying:
     - exact roles & structured domain inputs/outputs of the 4 Agents (`ClimateForecastAgent`, `UrbanEcoSafetyAgent`, `SocioEconomicPolicyAgent`, `CoreAgronomicAgent`);
     - the **DL Surrogate Model** input/output contract (`[64-D AlphaEarth + weather + phenology (DVS) + 3-stage actions] -> [yield, grain N, S_N, NUE, calibrated uncertainty]`) replacing shallow `ExtraTrees` without leaking privileged simulator internals in observable/sensor-free mode;
     - the offline `WOFOST81-SNOMIN` C/N physical interpretability audit (how DL internal representations map to soil/crop physics offline without ever exposing raw 64-D numbers to LLM agents);
     - fair comparison protocol against Baja et al. (*CEA* 2025) PPO, unilateral, and `ExtraTrees` baselines (keeping historical Phase 5–7 contracts preserved below).
3. **Paper Storyline (`_wiki-methodology/_wiki/paper-storyline/`)**:
   - Create `versions/storyline-v2.0.md` aligned to the 4-Agent Team + 64-D DL Surrogate Tool storyline (marked clearly as `planned-awaiting-user-execution-approval`, zero fabricated Phase 8 numbers).
   - Keep `versions/storyline-v1.0.md` archived untouched.
   - Update `_current.yml` to point to `storyline-v2.0` and append an entry to `CHANGELOG.md`.
4. **Canonical Decision Record**:
   - Create `_wiki-methodology/_top/_decisions/2026-11-15-v8-4agent-64d-dl-surrogate-tool-architecture.md` documenting why raw 64-D vectors never enter agent prompts, why `ExtraTrees` + linear probes (`Phase 5–7`) motivated the DL Surrogate upgrade, and how this restores the original `MASTER_PLAN_AGROMAS_GLOBAL_TOP_JOURNAL.md` 4-Agent secondary-research vision.
5. **Repo Navigation & Data Provenance**:
   - Update `_codemap.md` (keep strictly `<= 5 KB`, adding `Phase 7 已落盘` + `Phase 8 规划入口`).
   - Update `_meta/_data_sources.md` (add `Phase 7` real 45 site-years Google AlphaEarth 64-D GeoTIFFs / 184,320 10 m pixels, ESA WorldCover 10 m, coordinate offsets, and strict read-only evaluation boundary rules).
6. **Editable 3-Layer Method Framework Diagram (`share-technical-roadmap` compliant)**:
   - Create/update `reports/phase8/method-framework-v8/diagram.drawio`, export `.png` and `.svg`.
   - Structure cleanly in 3 layers (Input/Grounding Data -> `64-D Deep Learning Surrogate Model [DL Surrogate Tool]` & offline `WOFOST C/N Physical Audit` -> `4-Agent Cooperative Team [Climate / Urban-Geo / Socio-Econ / Core Agronomic]` -> Seasonal 3-Stage Decision & Bilateral Global Validation across 5 Regions + NL *CEA* 2025 Comparison).
   - Follow `share-technical-roadmap` rules: explicitly visually distinguish **Verified / Solid** assets (`Phase 6–7 data, WOFOST ground truth, AlphaEarth 45 site-years`) vs **Planned / Dashed** (`Q8.2 DL Surrogate training`, `Q8.3 4-Agent + DL Surrogate integration`, `Q8.4 Global + NL validation`), ensure **NO** arrow passes raw 64-D vectors into any Agent box (Agents only call the DL Surrogate Tool API and receive agronomic/ecological/economic predictions), run the repo's/skill's `validate_drawio.py`, and inspect the rendered `.png` visually for overlaps/clipping.
7. **Official `plan` CLI Updates (`Q8` & `Q8.1–Q8.4`)**:
   - Locate and use the official `plan` CLI and `sixone-cli.py` in the workspace/environment.
   - Ensure `Q1–Q7` remain byte-for-byte unchanged.
   - Set/update `Q8` and `Q8.1–Q8.4` strictly to these aligned Chinese titles and scopes:
     - `Q8`: `融合64维卫星隐向量的深度学习代理模型能否赋能四专职智能体团队，在五区及荷兰主场超越CEA基线？`
     - `Q8.1`: `重整六合一架构文档、storyline-v2.0、四智能体+深度学习代理总图与Q8计划` *(mark completed/closed ONLY after all Q8.1 files and validations pass)*
     - `Q8.2`: `构建融合64维卫星隐向量与气象物候的深度学习农田机理代理模型（DL Surrogate）及物理解码解释` *(open/planned)*
     - `Q8.3`: `将深度学习代理模型接入四专职智能体协同团队（气象端+地理城市端+经济政策端+农田统筹端）并优化全季三阶段决策` *(open/planned)*
     - `Q8.4`: `在荷兰原论文主场与全球五大典型麦区完成全面对比、四维压力矩阵、图表更新与顶刊双语稿重构` *(open/planned)*
8. **Verification, Summary Report & Clean Landing**:
   - Run `plan check`, `sixone-cli.py plan validate .`, `sixone-cli.py doctor .`, `validate_drawio.py`, and verify Phase 1–7 asset integrity (`1782` legacy + `242` Phase 7 files intact) plus `Q1–Q7` byte-for-byte unchanged (`git diff master -- ...`).
   - Write `reports/phase8/PHASE8A_REORG_SUMMARY.md` listing every created/modified file, exact CLI verification outputs, and clean boundary reminder (`Q8.2–Q8.4` not started).
   - Merge cleanly to `master`, remove temporary worktree and branch, populate `OUTBOX.json` with exact absolute file paths & command outputs, and ring the doorbell.

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
  `agent-bus doorbell --leader team-4031428b3351 --worker team-832 --job-id lead-team-4031428b3351-team-832-20261115T202332-930334 --attempt-epoch 24 --status completed --summary "<one-line conclusion>"`
