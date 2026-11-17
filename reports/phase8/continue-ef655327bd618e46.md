# Task Brief for `team-832`: Phase 8B — 5-Agent Role Sync + Core Experiments G1–G3 (`Q8.2` & `Q8.3` Core-First Gate)

**Target Repository**: `/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体` (current `master`: `bccb180fc3bbaf96ee25162e8b3e7a7b9142213f`; submodule `NUE_PCSE-Gym` `main`: `0354e3c6e53af2b5dc5fd32a40c53d2d16be840e`; submodule `pcse`: `d1fe6d29de828033b850ec51d994988d8d6d406f`, **strictly read-only**).

## Preflight Resolutions (Resolving Epoch 26 `OUTBOX.json` Decision & Findings)

1. **Approved `phase8b-p2-data-role` = Option A** (authorized under the user-approved `DECISION phase8_final_5agent_core_plan_approval: A` and `FINAL_PHASE8_LOGIC_AND_CORE_EXPERIMENT_PLAN.md` Section 4):
   - **`P1` Historical Benchmark**: Keep `1995–2009 TRAIN` and one-shot `2010–2014 Dev` calibration untouched by satellite data; `G1` (`Q8.2`) first validates the weather/soil PyTorch DL World Model backbone on `TRAIN/Dev` (alongside offline `TRAIN` C/N physical decoding).
   - **`P2` Spatial-Prior Benchmark (`2018–2026`, `44` causal `t-1` rows = `40 Former-Held-Out + 4 Public-Reused NL 2018–2021`, strictly stratified)**: Explicitly approved as a **retrospective nested `LOYO / LORO` cross-fitted evaluation**. Freeze the `1995–2014` weather/soil backbone (and pre-freeze all adapter hyperparameters), fit the low-rank (`<= 3–4` dims + `L2` shrinkage) `t-1` 64-D AlphaEarth spatial adapter **strictly inside each outer fold using that fold's training labels only**, score each outer held-out fold once, and explicitly label `P2` as a **retrospective cross-fitted evaluation** (never claiming a prospective or untouched blind test).
   - Record this approved data-role contract explicitly in `_wiki-methodology/_wiki/method.md` (resolving the `Q8.2` data-role precondition on line 36) and `_wiki-methodology/_top/_questions/Q8.md` during Step 0.
2. **Approved Preflight Technical Resolutions (`OUTBOX.json`)**:
   - **Runtime**: Create/use a task-local CUDA/Lightning runtime (8 physical GPUs are visible; keep virtualenv/runtime directories cleanly untracked outside git commits and clean working trees).
   - **Committed-N Projection Wrapper**: Implement a clean local wrapper in `NUE_PCSE-Gym/pcse_gym/agromas_v8/` using an explicitly named committed-N projection-bound feature copy so nominal candidate schedules remain intact in model inputs while skipped applications (`Executed_N_fert`) are projected accurately without altering legacy `agromas/continuation.py`.

## 0. Strict Execution Boundary (READ FIRST)

The user approved **Core-First Execution (`G1 -> G2 -> G3` only)** after auditing our logic with 4 independent checks.
- **IN SCOPE**:
  - **Step 0**: Light 5-Agent role synchronization (`docs + diagram + official Q8 TOP via plan CLI`) + missing Historical `2010–2014 Dev` 343-plan books + one-time read-only `1995–2009 TRAIN` `PCSE` pass for `stock_diagnostics` (`native_Nloss_kg_ha` and daily C/N decoding).
  - **Step 1 (`G1` / `Q8.2`)**: Train & calibrate the `SpatialTwinSurrogateAgent` PyTorch nonlinear DL World Model on `TRAIN (1995–2009)` + conformal calibration on `Dev (2010–2014)`, plus offline physical C/N decoding on `TRAIN`.
  - **Step 2 (`G2` / `Q8.3` Core Exp 1)**: Implement the coupled **5-Agent + Non-Anticipative Branching Scenario-Tree** controller (`NUE_PCSE-Gym/pcse_gym/agromas_v8/`) and execute a **single locked read-only `WOFOST81-SNOMIN` evaluation pass** on `P1` (Matched Full-Telemetry & Matched Sensorless parity tracks) and `P2` (`2018–2026` causal `t-1` cohort with stratified `40 Former-Held-Out + 4 Public-Reused` reporting).
  - **Step 3 (`G3` / `Q8.3` Core Exp 2)**: Execute Controlled 3-Factor Orthogonal Ablations (**Group A**: Surrogate/Prior; **Group B**: Monolithic Bit-Parity + Coupling/Tree vs Open-Loop/Soft-Penalty/Greedy-Frozen; **Group C**: Orthogonal Role Removals under targeted wet/dry quantiles, `S_cap = 25/35`, and `2x` price / `TRAIN`-selected subsidy).
  - **Step 4**: Automated verification tests, external `aid` code/result review, comprehensive report (`reports/phase8/PHASE8B_CORE_EXPERIMENTS_G1_G2_G3_REPORT.md`), clean merge back to `NUE_PCSE-Gym` `main` and root `master`, cleanup of temporary worktrees/branches, `OUTBOX.json` update.
- **STRICTLY OUT OF SCOPE (DO NOT EXECUTE IN THIS DISPATCH)**:
  - **DO NOT** run the 90-cell 4D stress surface sweep.
  - **DO NOT** redraw/regenerate full Phase 8 manuscript figures (Fig. 1–5) or edit manuscript TeX/PDF (`Q8.4` stays unstarted/blocked until user reviews `G1–G3` realized WOFOST results!).

---

## 1. Mandatory Integrity, Branching & Preservation Rules

1. **Isolated Worktrees / Branches & Clean Merge**:
   - Do all code, script, test, doc, and report changes inside isolated git worktrees and named feature branches (e.g., `feat/phase8-core-g1-g3`) in BOTH `NUE_PCSE-Gym` and the root repository.
   - Before completing, merge tested & reviewed commits into `NUE_PCSE-Gym` `main` and root `master`, update the submodule pointer cleanly on `master`, verify clean `git status`, remove all temporary worktrees, and delete temporary feature branches.
2. **Untouched Legacy & Baseline Integrity**:
   - Preserve untouched: `pcse` submodule (`d1fe6d29de828033b850ec51d994988d8d6d406f`), existing `NUE_PCSE-Gym/pcse_gym/agromas/` and `agromas_v6/` runtime code, `Q1–Q7`, `storyline-v1.0.md`, and all verified legacy/Phase 7 assets (`1782` + `242` + `2188` tracked evidence/sources). Run `verify-preservation.py` before finishing.
   - Place all new Phase 8 implementation cleanly in `NUE_PCSE-Gym/pcse_gym/agromas_v8/`, `scripts/phase8-*.py`, and `tests/test_phase8_*.py`.
3. **Canonical `_wiki-methodology/_top/` CLI Handling**:
   - Remember `sixone` / `plan` CLI operates against canonical primary TOP. Do not hand-edit `Q1–Q7`. Update only `Q8` metadata/acceptance/records using the repository's official `plan` CLI (or approved repository tooling). Only ring `waiting_user` if a genuine unresolvable blocker stops execution.
4. **Honesty & Pre-Registered Halt Rules**:
   - Never tune hyperparameters on `Held-Out >= 2015` or run multiple evaluation passes on `Held-Out` to cherry-pick numbers. `Held-Out >= 2015` must be evaluated in a **single locked read-only pass**.
   - Never fabricate or mask failures (including unavailable external AI providers on `aid quota`, `NL n=5` statistical power limits, `CN 0/12` or `FR 1/12` physical ceilings, or `G1` failure if triggered).

---

## 2. Final Audited Architecture (5 Online Specialist Agents + 1 External Referee)

Implement cleanly in `NUE_PCSE-Gym/pcse_gym/agromas_v8/` with zero leakage of raw `A00..A63` floats or simulator oracle state into online agents:

1. **`SpatialTwinSurrogateAgent` (5th Online Specialist Agent)**:
   - Wraps the **PyTorch nonlinear DL World Model tool** (`predict_joint_response`), out-of-distribution (OOD) applicability-domain check, `TRAIN OOF` + one-shot `Dev` conformal calibration, and `t-1` 64-D AlphaEarth Spatial Prior Adapter (`P2`, using fold-local low-rank bottleneck `<= 3–4` dims + `L2` shrinkage).
   - Emits `K=32` joint ensemble members predicting **`(Yield, Grain_N, Executed_N_fert)`** (explicitly predicting `Executed_N_fert` rather than assuming nominal planned dose because `31/59,310` budget-legal `TRAIN` plans skip doses under 14-day/DVS guards!).
   - Projects each member deterministically via `agromas/continuation.py::project_members(prediction, features, budget=220.)` (`nonfert=3.5`, `grain=min(grain, 1000*y)`, `S_N = fert + nonfert - grain`, `NUE = grain / (fert + nonfert)`) to obtain member-wise `S_N` and `NUE` distributions.
   - **Hard Vector Quarantine**: Raw `A00..A63` 64-D floats stay strictly internal to the PyTorch spatial-prior encoder / tool and MUST NEVER appear in any agent prompt, message payload, state dict exposed to reasoning/dialogue, or human-readable decision rule.
2. **`ClimateForecastAgent`**:
   - Fixes the 14-day horizon limitation of `agromas/climate_agent.py`.
   - Generates **causal full remaining-season weather scenario branches** (covering planting/stage `t` through maturity) sampled/constructed strictly from `TRAIN (1995–2009)` rolling-origin / historical year blocks (plus explicit `(delta_T, CO2)` regime metadata where applicable). Explicitly document/tag these in code & docstrings as **conditional historical weather analogs** (NOT operational NWP forecast skill!).
3. **`UrbanEcoSafetyAgent` (Unbundled Strictly to Eco-Safety)**:
   - Enforces regional nitrate-surplus corridor `0 <= S_N <= S_cap`, probabilistic safety `q_{1-epsilon}(S_N) <= S_cap`, and upper-tail `S_N` CVaR across `S_cap in {25, 35, 40, 50}` kg/ha.
   - **Strictly decoupled from `NUE`**: Do NOT bundle `NUE` into `UrbanEcoSafetyAgent` (resolves Flaw 1 from the independent audit so Group C ablations cleanly separate ecological nitrate safety from agronomic efficiency!).
4. **`SocioEconomicPolicyAgent` (Owns NUE Soil-Mining Corridor + Dynamic Economics)**:
   - Enforces the agronomic nitrogen-efficiency / anti-soil-mining corridor `0.50 <= NUE <= 0.90`.
   - Computes dynamic expected partial profit (`EUR/ha`: aligned with `agromas_v6/core.py` baseline `200 * Yield - 1.5 * price_multiplier * Executed_N_fert`, parameterized generally as `1000 * price_grain * Yield - price_n * Executed_N_fert`) plus green subsidy minus surplus tax under active `(price_n, price_grain, subsidy, tax)`.
5. **`CoreAgronomicAgent` (Phenology + Non-Anticipative Branching Scenario-Tree Solver)**:
   - Enforces DVS application windows `[0.20, 0.55, 0.82]`, `>= 14`-day inter-application spacing, `220 kg N/ha` total cap, and discrete `GRID = [0, 10, 20, 40, 60, 80, 100]`.
   - Solves a **True Non-Anticipative Branching Scenario Tree / Backward DP** across all 3 decision stages over the causal remaining-season weather scenario branches from `ClimateForecastAgent` (NO Wait-and-See future cheating such as taking `max u_2(m), u_3(m)` conditional on realized path `m`!).
   - Executes only the root optimal action `u_t^*` and causally re-plans at `t+1`.
   - Implements identical **Tier-1 -> Tier-2 -> Tier-3 `dose=0` operational fallback** parity (shared across baselines, with Tier-3 `dose=0` NEVER mislabelled as compliant).
6. **External Read-Only Physics Referee (`WOFOST81-SNOMIN`)**:
   - Strictly external to all 5 online agents; provides daily mechanistic simulation and exact N/C conservation ledger (`|N_residual| < 1e-10` kg/ha, `|C_residual| < 1e-9` kg/ha) during offline `TRAIN` C/N decoding and the single locked Held-Out evaluation pass.

---

## 3. Step-by-Step Execution Specification

### Step 0: Light 5-Agent Role Sync + Missing `Dev` Books & `TRAIN` Diagnostics
1. Synchronize the **5-Agent + External Referee** architecture concisely across:
   - `_wiki-methodology/_wiki/method.md`
   - `_wiki-methodology/_wiki/socratic-logic-and-evolution.md`
   - `_wiki-methodology/paper-storyline/versions/storyline-v2.0.md`
   - `_wiki-methodology/_codemap.md`
   - `_wiki-methodology/_top/_questions/Q8.md` (via official `plan` CLI; verify `Q1–Q7` and `v1.0` untouched)
   - `reports/phase8/method-framework-v8/diagram.drawio`, `.png`, `.svg`: ensure `SpatialTwinSurrogateAgent` appears explicitly alongside `ClimateForecastAgent`, `UrbanEcoSafetyAgent`, `SocioEconomicPolicyAgent`, `CoreAgronomicAgent`, the `64-D PyTorch DL Tool`, and the external read-only `WOFOST81-SNOMIN` referee. Pass `validate_drawio.py` & `method_diagram.py check`, and visually inspect the rendered PNG.
2. Generate the missing **25 Historical `2010–2014 Dev` 343-plan books** on disk (matching `regions.py` 5 regions x 5 years = 25 books; inspect existing Phase 5/6 book scripts to match format and seed conventions).
3. Run a **one-time read-only `PCSE` pass on `1995–2009 TRAIN` only** to backfill missing `stock_diagnostics` (`native_Nloss_kg_ha` and daily C/N mass terms) and record actual `Executed_N_fert` (capturing skipped doses under 14-day/DVS guards).

### Step 1 (`G1` / `Q8.2`): `SpatialTwinSurrogateAgent` PyTorch DL World Model + Conformal Calibration
1. Inspect `agromas/features.py` (`shared_features`) and explicitly construct clean feature extractors for BOTH parity settings:
   - `Full-Telemetry` (`observed = [dvs, lai, sm, n_fert_cum, n_uptake, stage]` + causal weather/context), and
   - `Sensorless` (strictly causal observables without privileged `lai`, `sm`, `n_uptake`; verify exact availability of observables at each DVS trigger).
2. Implement the PyTorch nonlinear DL World Model generating `K=32` ensemble predictions of `(Yield, Grain_N, Executed_N_fert)` -> per-member `project_members` -> marginalized conformal calibration:
   - Fit on `TRAIN (1995–2009)` with out-of-fold CV predictions (`TRAIN OOF`).
   - Run **one-shot conformal calibration on `Dev (2010–2014)`** **marginalized over full remaining-season `ClimateForecastAgent` weather scenario branches** (not oracle future weather!).
   - Enforce the **2-Architecture Pre-Registered Cap**: register at most 2 PyTorch architectures evaluated on `TRAIN` CV before touching `Dev`. **If `G1` gates fail on `Dev` for both, HALT cleanly and report the negative finding without leaking/tuning on `Dev` or running `G2/G3`.**
3. **Mandatory `G1` Pass Gates on `Dev (2010–2014)`** (remember raw `TRAIN` compliance base rate is `~6.82%` overall / `~8.53%` legal, so raw `Brier < 0.15` alone is trivial/vacuous!):
   - `BSS > 0` (`Brier Skill Score`) for `S_N <= S_cap` compliance probability over **BOTH** (a) region-stage climatology base rate AND (b) fold-matched `ExtraTreesRegressor` baseline on identical reachable candidate prefixes.
   - Marginalized `90%` $S_N$ empirical coverage within `[85%, 95%]` on `Dev`.
   - Strictly lower within-prefix utility / ranking regret than fold-matched `ExtraTrees` on `Dev`.
4. **Offline Physical Interpretability Audit (`TRAIN 1995–2009` only)**:
   - Perform C/N physical decoding relating learned latent/prior representations to `WOFOST` soil organic/mineral N & `Native_N_loss` on `TRAIN` (offline audit only; never used online).
   - Verify OOD applicability-domain scoring & raw 64-D vector isolation.

### Step 2 (`G2` / `Q8.3` Core Exp 1): 5-Agent Team vs Baselines on `P1` & `P2`
1. Assemble the full coupled 5-agent controller in `NUE_PCSE-Gym/pcse_gym/agromas_v8/`.
2. Execute a **single locked read-only `WOFOST81-SNOMIN` evaluation pass** covering:
   - **`P1` Historical Benchmark (`>= 2015`)** across all 5 regions (`AU, US, NL, CN, FR`), keeping **`NL` home-turf WUR** and **NASA (`n=5` / `52` total Held-Out)** explicitly separate and documented (never silently pooled!). Run BOTH parity tracks:
     - **Track 1 (Matched Full-Telemetry)**: vs verified baselines (`Phase6-Full` `21.8788%`, `PPO-v6-structured-book` `23.5657%`, `DVS-N2` `7.4848%`, `N2-PA`, `Phase4-Forest` `40%`/`28.57%` as reported in `reports/phase5` & `reports/phase6`).
     - **Track 2 (Matched Sensorless)**: vs newly evaluated/matched `Sensorless PPO-v8`, `Sensorless ExtraTrees`, `3D Static-Soil DL`, and `Pure-Weather DL`.
   - **`P2` Spatial-Prior Benchmark (`2018–2026` causal `t-1` AlphaEarth cohort)**:
     - Verify exact cohort on disk (`44` rows = `36 NH + 8 AU`, split cleanly into **`40 Former-Held-Out`** and **`4 Public-Reused NL 2018–2021`**, reported **strictly stratified**!).
     - Enforce nested `LOYO / LORO` fold-local low-rank spatial-prior bottleneck (`<= 3–4` dims + `L2` shrinkage) in `SpatialTwinSurrogateAgent`.
     - Compare `5-Agent + 64-D Causal t-1 DL` against ALL THREE required controls: **`3D Static-Soil DL`**, **`Pure-Weather DL`**, and Phase 7 `0%` baseline.
3. **Mandatory Metrics & Statistical Reporting (`G2`)**:
   - Report 5-region equal-weight compliance, pooled compliance, ALL 5 individual regions (`AU, US, NL [NASA & WUR separate], CN, FR`), expected partial profit (`EUR/ha`), Tier-1/2/3 fallback breakdown, `Native_N_loss`, and physical ceilings (`AU 11/11, US 12/12, NL 4/5, FR 1/12, CN 0/12`, `CN` basal `171.0 kg N/ha`).
   - Run paired bootstrap (`B=5000`, `seed=20261115`) on `[NL, US, AU]` solvable core (`95% CI`) plus exact sign/Wilcoxon tests (honestly note `NL n=5` minimum exact two-sided sign test `p=0.0625`).
   - Verify **zero future-weather leakage** (`30` future-perturbation invariance tests on online action choice) and **mass conservation** on 100% of evaluated runs (`N < 1e-10` kg/ha, `C < 1e-9` kg/ha).

### Step 3 (`G3` / `Q8.3` Core Exp 2): Controlled 3-Factor Orthogonal Ablation
Evaluate all three orthogonal factor groups honestly (using the same single locked read-only regime evaluation without expanding into the 90-cell `Q8.4` stress surface):
- **Group A (Surrogate & Prior Axis, fixed 5-Agent Tree)**:
  - `Linear` vs `ExtraTrees` vs `Pure-Weather DL` vs `3D Static-Soil DL` vs `Full Causal 64-D Spatial-Prior DL`.
- **Group B (Coupling & Tree-Planning Axis)**:
  - **Mandatory Bit-for-Bit Parity Assert (`pytest`)**: prove `Hard-Constrained Monolithic Controller === 5-Agent Collaborative Controller` bit-for-bit identically when given identical unbundled constraints (`0 <= S_N <= S_cap`, `0.50 <= NUE <= 0.90`), causal climate branches, dynamic objective, and Tier 1–3 fallback.
  - Compare `5-Agent Non-Anticipative Branching Tree` vs `Soft-Penalty`, `Open-Loop 343`, and `Greedy Frozen-Continuation`.
- **Group C (Unbundled Orthogonal Role Ablations under Targeted Stressors)**:
  - Using pre-frozen `TRAIN`-quantile wet/dry extreme years, strict caps `S_cap = 25` & `35 kg/ha`, and `2x` N price / `TRAIN`-selected green subsidy:
    1. **Ablate `ClimateForecastAgent`** (climatology mean / short-horizon only vs causal full-season climate branches) -> isolate value on wet/dry climate extremes.
    2. **Ablate `UrbanEcoSafetyAgent`** (remove `0 <= S_N <= S_cap` ONLY, keeping `0.50 <= NUE <= 0.90` intact!) -> isolate unbundled nitrate-safety value under `S_cap = 25/35`.
    3. **Ablate `SocioEconomicPolicyAgent`** (remove `0.50 <= NUE <= 0.90` + dynamic policy valuation ONLY, keeping `0 <= S_N <= S_cap` intact!) -> isolate soil-mining prevention (`NUE > 0.90`) and policy-adapted partial profit under `2x` N price / green subsidy.

### Step 4: Automated Verification, Independent Review, Clean Merge & Reporting
1. Write & pass pytest suite (`tests/test_phase8_*.py`) covering:
   - `Monolithic === 5-Agent` bit-for-bit parity assertion,
   - Zero future-weather leakage (`30`-perturbation invariance),
   - Zero raw `A00..A63` 64-D floats in any agent prompt/reply/rule,
   - Unbundled `UrbanEco` vs `SocioEcon` constraint independence,
   - `Executed_N_fert` / `project_members` / conformal coverage / `BSS` calculations,
   - `WOFOST81-SNOMIN` N/C conservation bounds (`N < 1e-10`, `C < 1e-9` kg/ha).
2. Run repository checks: `pytest`, `plan check`, `sixone-cli.py plan validate .`, `sixone-cli.py doctor .`, `validate_drawio.py`, `method_diagram.py check`, `verify-preservation.py`.
3. Run independent external review via `aid` on your implementation diff & `G1–G3` numerical findings using currently available providers (`aid quota` — e.g., `gemini-4-carbon-high` + `deepseek` + host checks; accurately note any unavailable provider like Claude if absent, without fabricating a pass) and resolve any real findings before merging.
4. Write structured engineering & scientific results report at:
   - `reports/phase8/PHASE8B_CORE_EXPERIMENTS_G1_G2_G3_REPORT.md`
   Ensure every metric, comparison, `G1/G2/G3` pass/fail verdict, limitation, and baseline reference is backed by real saved files/logs on disk. Update `Q8.2` / `Q8.3` state in `_top/` cleanly via official `plan` CLI (leaving `Q8.4` unstarted/pending user approval!).
5. Merge feature branches cleanly (`NUE_PCSE-Gym` -> `main`, root -> `master`), remove temporary worktrees/branches, verify clean `git status` & SHA hashes, update `OUTBOX.json`, and ring completion doorbell.

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
  `agent-bus doorbell --leader team-4031428b3351 --worker team-832 --job-id lead-team-4031428b3351-team-832-20261115T222141-279512 --attempt-epoch 27 --status completed --summary "<one-line conclusion>"`
