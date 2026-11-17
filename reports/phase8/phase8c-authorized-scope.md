# TASK_PHASE8C_TIER2_SOFT_SUPPLEMENT_AND_Q84

**Team**: `team-4031428b3351` | **Worker**: `team-832` | **Decision Authority**: `DECISION phase8_post_g1_g3_next_step = Option A` (`2026-11-16T04:52:56+08:00`) + Leader Preflight Resolution on `phase8c_stress_matrix_cardinality` (`Option A`: Full `180`-Cell Factorial + Canonical `90`-Group Phase 5/6 Continuity Subset)

---

## 0. Mandatory Isolation, Repo Anchors, and Preservation Rules

1. **Primary Workspace & Git Anchors**:
   - Root repo: `/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体` (`master` baseline: `e773fcb4501d5445a38ad86014c9202bfcd0b9b5`)
   - Submodule `NUE_PCSE-Gym`: `/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体/NUE_PCSE-Gym` (`main` baseline: `b97976055f2699cc2d04acf1c16a02f33cdf24d6`)
   - Submodule `pcse`: `d1fe6d29de828033b850ec51d994988d8d6d406f` — **STRICTLY READ-ONLY, DO NOT MODIFY**.
2. **Worktree Isolation & Merge Cleanliness**:
   - Create isolated worktrees and branches named `feat/phase8c-supplement-and-q84` on BOTH root repo and `NUE_PCSE-Gym`.
   - Do not modify files outside your isolated worktrees during execution. At final completion, verify tests/builds, merge cleanly back into `NUE_PCSE-Gym` `main` and root `master`, remove temporary worktrees and feature branches, and leave both `master` and `main` clean.
3. **Immutable Asset Preservation (100% Untouched)**:
   - **Preserve 100% of the existing `2,017` Phase 8B episodes in `data/phase8-combined-evaluation`** as the immutable benchmark of **"Hard-Truncation Bare-Profit Tier-2 Collapse (`4.00%` Sensorless / `9.67%` Full-Telemetry)"**. Never delete, overwrite, or mutate `data/phase8-combined-evaluation` or `reports/phase8/PHASE8B_CORE_EXPERIMENTS_G1_G2_G3_REPORT.md`.
   - Preserve all `1,782` legacy assets, `242` Phase 7 assets, `2,188` tracked evidence/source files, `Q1–Q7`, and `storyline-v1.0.md`.
4. **Scientific Integrity, Architectural Terminology & Preflight Clarifications**:
   - **Architectural Naming**: Accurately describe the world model + spatial integration as a **`36-D` PyTorch neural world-model backbone (`13,155` params) plus a private `64-D` AlphaEarth PCA/Ridge low-rank spatial adapter (`<=4-D` bottleneck) encapsulated inside `SpatialTwinSurrogateAgent`** — never mislabel it as a pure `64-D` end-to-end neural encoder.
   - **Within-Region `N_loss` Decoding Bounds**: Preserve the exact qualified regional findings from Phase 8A/8B (`AU` exhibits positive within-region `N_loss` $R^2$, whereas `NL`, `FR`, `US`, and `CN` are nonpositive or bounded; do not claim `R^2 <= 0` uniformly across all regions).
   - **Native Conservation & Statistical Rigor**: All native evaluation episodes must run in real `WOFOST81-SNOMIN` and log full daily mass conservation audits (`max |N_balance_error| < 1e-10` kg/ha, `max |C_balance_error| < 1e-9` kg/ha). Explicitly document statistical multiplicity (Holm-adjusted p-values), finite-sample bounds (`NL Former-Held-Out n=5`, minimum two-sided exact sign `p >= 0.0625`), structural physical ceilings (`CN 0/12`, `FR 1/12` under high basal N), and `LORO` cross-continent OOD prior-fallback behavior (`100%` fallback).

---

## 1. Exact Code Repair in `NUE_PCSE-Gym/pcse_gym/agromas_v8/`

### 1.1 Repair `planning.py` (`Regime` & `distribution_metrics`, `lines 25–75`)
1. Update the existing **`Regime`** dataclass (note: the actual dataclass name is `Regime`, not `DecisionRegime`) in `NUE_PCSE-Gym/pcse_gym/agromas_v8/planning.py`:
   - Add field `bare_tier2: bool = False` (default `False`) so the repaired composite objective is the default, while `bare_tier2=True, soft=False` deterministically reproduces the archived Phase 8B `Hard-BareTier2` collapse (`4.00%` Sensorless / `9.67%` Full-Telemetry) in unit tests and ablations.
   - Wire `mode='hard-bare-tier2'` (sets `soft=False, bare_tier2=True`) alongside `mode='tree'` (`soft=False, bare_tier2=False`, i.e., `Tier2-Composite`), `mode='soft'` (`soft=True`), `'open-loop'`, and `'greedy-frozen'` in `FiveSpecialistTeam.choose` (`controller.py`), `CoreAgronomicAgent`, and `TreePolicy` (`policies.py`), checking all callers across `agromas_v8` and `scripts/phase8*` to preserve full API compatibility.
2. Update `distribution_metrics(members, branch_weights, regime)` in `NUE_PCSE-Gym/pcse_gym/agromas_v8/planning.py` (`lines 35–68`):
   - Keep the true physical joint indicator `joint = (s >= 0) & (s <= regime.cap) & (nue >= 0.5) & (nue <= 0.9)` for audit/logging (`joint_prob = float(np.sum(w * joint))`).
   - Compute active specialist terms respecting `regime.eco` and `regime.econ`:
     - `eco_ok = ((s >= 0) & (s <= regime.cap)) if regime.eco else np.ones_like(s, dtype=bool)`
     - `econ_ok = ((nue >= 0.5) & (nue <= 0.9)) if regime.econ else np.ones_like(nue, dtype=bool)`
     - `active_joint = eco_ok & econ_ok`
     - `econ_dist = (max(0.5 - mean[3], 0.0) + max(mean[3] - 0.9, 0.0)) if regime.econ else 0.0`
     - `eco_dist = (max(mean[2] - regime.cap, 0.0) / regime.cap + max(-mean[2], 0.0) / regime.cap) if regime.eco else 0.0`
     - `active_distance = econ_dist + eco_dist`
   - Compute `composite_score`:
     - `composite_score = partial + (200.0 * float(np.sum(w * active_joint)) - 200.0 * active_distance if (regime.eco or regime.econ) else 0.0)`
   - Compute `score`:
     - `score = partial if (regime.bare_tier2 and not regime.soft) else composite_score`
   - Keep `choose_tier` logic intact (`soft=True` skips hard tail truncation; `soft=False` preserves the 3-tier hierarchy while `bare_tier2=False` ensures `Tier 2` ranks using `composite_score` rather than bare `partial`).

### 1.2 Climate Scenario Propagation Guard (`online_features.py` & `policies.py`)
Before running `Q8.4` under `idealized_mid` and `idealized_high` climates, audit and fix climate propagation in `NUE_PCSE-Gym/pcse_gym/agromas_v8/online_features.py` and `policies.py`:
- In `online_features.py` (`public_state` L19), preserve `climate` if present (or pass `climate=case.get('climate', state.get('climate', 'Historical'))` explicitly everywhere `tree(...)` and `candidate_features(...)` are called).
- Fix `TreePolicy` open-loop path (`policies.py` L15/L17) and `SensorlessPPOPolicy` (`policies.py` L48–49) where `'Historical'` / default `climate` was previously used instead of the active episode `climate`.
- Verify that `candidate_features(...)` receives the true `climate` (`'Historical'`, `'idealized_mid'`, `'idealized_high'`) and passes `climate` consistently into `climate.tree(...)` across all controllers without mutating `P1` `Historical` behavior.

### 1.3 Unit Tests (`tests/phase8/`)
Add explicit unit tests verifying:
1. `Regime(bare_tier2=True, soft=False)` reproduces the archived `Hard-BareTier2` bare-profit scoring (`score == partial`).
2. `Regime(bare_tier2=False, soft=False)` (`Tier2-Composite`) and `Regime(soft=True)` (`Soft-Coupled`) both apply `+200*P(active_joint) - 200*active_distance`.
3. Setting `regime.eco=False` disables `S_N` terms in `active_joint` and `active_distance`; setting `regime.econ=False` disables `NUE` terms in `active_joint` and `active_distance`; setting both `False` yields `composite_score == partial`.
4. `TreePolicy` (`open-loop`), `FiveSpecialistTeam.choose`, and `SensorlessPPOPolicy` properly propagate non-`'Historical'` `climate` (`'idealized_mid'`, `'idealized_high'`) into `candidate_features` and `climate.tree`.

---

## 2. Supplemental `P1 / P2 / G3` Native `WOFOST81-SNOMIN` Evaluation

Store all new/repaired episodes in a clean append-only directory: **`data/phase8c-supplemental-evaluation`** (never mutate `data/phase8-combined-evaluation`). Reuse identical already-executed episodes from `data/phase8-combined-evaluation` via content/config hash verification where applicable (record clearly in manifests which episodes are newly executed vs reused). Log daily N/C mass conservation for every newly run native episode (`max |N| < 1e-10`, `max |C| < 1e-9` kg/ha).

1. **`P1` (`52 Former-Held-Out + 7 Public-Reused NASA + 7 Public-Reused WUR`)**:
   - Ensure full head-to-head comparison across both `Full-Telemetry` and `Sensorless` observation modes for:
     - **`Soft-Coupled 5-Agent Tree` (`soft=True`)** — evaluate `Full-Telemetry soft` alongside the already-completed `Sensorless soft` (`26.73%` 5-region equal-weight / `26.92%` pooled on 52 seasons; `28.57%` on `NL Public-Reused`).
     - **`Tier2-Composite 5-Agent Tree` (`bare_tier2=False, soft=False`)** — evaluate both `Full-Telemetry` and `Sensorless`.
     - **`Hard-BareTier2` (`bare_tier2=True, soft=False`)** — retain immutable Phase 8B archive (`4.00%` Sensorless / `9.67%` Full-Telemetry) to isolate and quantify the Tier-2 collapse mechanism.
   - Re-evaluate **`G3` 3-Factor Orthogonal Ablations** under repaired composite scoring (`remove='eco'` / `remove='econ'` now properly isolated!):
     - **Group A (World Model)**: `TreeWeather`, `TreeExtraTrees`, `TreeLinear`, vs `5-Agent TreeMLP` (`Soft-Coupled` & `Tier2-Composite`).
     - **Group B (Coupling & Solver)**: `open-loop`, `greedy-frozen`, `hard-bare-tier2`, `tier2-composite`, `soft`.
     - **Group C (Specialist Removal & Policy Sensitivity)**: `remove-climate`, `remove-eco` across `cap={25, 35, 40}`, `remove-econ` under `price=2x` & `subsidy=50`.
2. **`P2` Causal `t-1` Benchmark (`44` site-years = `40 Former-Held-Out + 4 Public-Reused NL` across `LOYO` and `LORO`)**:
   - Re-evaluate `P2-Full64` (36-D PyTorch backbone + private 64-D PCA/Ridge adapter), `P2-Static3`, `P2-Weather`, `P2-Linear64`, and `P2-ExtraTrees64` under repaired **`Soft-Coupled`** / **`Tier2-Composite`** scoring so `AU` and `US` are no longer artificially zeroed by the `Tier 2` bare-profit bug.
   - Continue to enforce causal `t-1` non-leakage and report `LORO` `100%` OOD automatic prior-fallback rates transparently.

---

## 3. Complete `Q8.4`: Full `180`-Cell Factorial Stress Surface (+ Canonical `90`-Group Subset), Figures 1–5, Storyline, Wiki & Top-Journal Manuscript

1. **Full `180`-Cell 4D Stress Surface + Canonical `90`-Group Continuity Subset (`Q8.4`)**:
   - Execute the **approved full `180`-cell 4D factorial stress matrix**:
     - **Climate Scenarios (`3`)**: `Historical`, `idealized_mid` (`+1.8°C, 450 ppm`), `idealized_high` (`+3.5°C, 550 ppm`)
     - **Eco Caps (`4`)**: `{25, 35, 40, 50}` kg N/ha
     - **Socio-Economic Policy Regimes (`3`)**: `Standard (price=1x, sub=0)`, `N Price Shock (price=2x, sub=0)`, `Eco-Subsidy (price=1x, sub=50 EUR/ha)`
     - **Regions (`5`)**: `NL`, `FR`, `US`, `CN`, `AU` (`3 × 4 × 3 × 5 = 180` cells across all 52 `P1` `Former-Held-Out` season-years).
   - Compare the primary **5-Agent DL Controller (`Soft-Coupled` + `Tier2-Composite` sensitivity)** against `SensorlessPPO`, `LegacyV6Full`, and `DVS-N2`, saving raw episode records, summary JSON/CSV tables, and daily `WOFOST81-SNOMIN` mass conservation audit (`max |N| < 1e-10, max |C| < 1e-9` kg/ha).
   - **Dual Continuity Reporting**: In addition to the full `180`-cell factorial summary, explicitly slice and tabulate the **canonical Phase 5/6 `90`-group subset (`3 climates × 3 stress caps {25, 35, 50} × 2 price multipliers {1x, 2x} × 5 regions = 90 groups`, plus frozen `TRAIN`-selected green-subsidy diagnostics across `{0, 50, 100, 150, 200}`)** so readers and reviewers have seamless continuity with Phase 5/6 without dropping any factor level.
2. **Publication-Grade Top-Journal Figures (`Fig. 1–5`)**:
   - Generate/update clean, overlap-free vector + high-DPI figures in `reports/phase8/figures/` (and sync manuscript figure paths), visually inspect rendered outputs, and run repository diagram validators (`validate_drawio.py` / `method_diagram.py check` where `.drawio` / method diagrams are updated):
     - **Fig. 1**: Architecture — 5-Specialist Agent Team + `36-D` PyTorch World Model Backbone & Private `64-D` Low-Rank AlphaEarth Adapter + 2-Stage Non-Anticipative Scenario Tree + External Read-Only `WOFOST81-SNOMIN` Referee.
     - **Fig. 2 (`G1`)**: PyTorch World Model skill (`BSS vs ExtraTrees`, `90%` cross-year interval calibration, within-prefix ranking regret, and offline `TRAIN` C/N pool decoding vs qualified within-region `N_loss` boundary including positive `AU` $R^2$).
     - **Fig. 3 (`G2` + Mechanistic Discovery)**: 5-Region & NL Home-Turf (`NASA` vs `WUR` unpooled) Head-to-Head + **Core Mechanistic Contrast: Rigid Tail-Truncated Bare-Tier2 Zero-Dose Soil-Mining Collapse (`4.00%` Sensorless / `9.67%` Full) vs Probabilistic Soft-Coupled / Composite 5-Agent DL Planning (`26.73%` Sensorless on `P1` 52 seasons, `28.57%` on `NL Public-Reused`)**.
     - **Fig. 4 (`P2`)**: Causal `t-1` `64-D` AlphaEarth Low-Rank Spatial-Prior Bridging (`LOYO` temporal generalization vs `LORO` cross-continent OOD boundary and `100%` prior-fallback mechanism).
     - **Fig. 5 (`G3` & `Q8.4`)**: 3-Factor Orthogonal Ablations (`Group A/B/C`) + `180`-Cell 4D Climate–Eco–Policy Stress Surface (annotated with the canonical `90`-group stress slice).
3. **Documentation, Storyline, Plan CLI & Bilingual Top-Journal Manuscript**:
   - Update `reports/phase8/PHASE8_TOP_JOURNAL_REPORT.md` (and preserve `PHASE8B_CORE_EXPERIMENTS_G1_G2_G3_REPORT.md`).
   - Update `storyline-v2.0.md` (preserving `storyline-v1.0.md` untouched) and `_wiki/method.md` (accurately naming `Regime`, `36-D` backbone + `64-D` low-rank adapter, and qualified `AU` within-region `N_loss` $R^2$).
   - Update `_wiki-methodology/_top/_questions/Q8.md` using the official `plan` CLI (`sixone-cli.py` / `plan`) to mark `Q8.4` completed (while leaving `Q1–Q7` untouched) and run `plan check`.
   - Update the bilingual top-journal manuscript (`TeX` sources + compiled `PDF`, clean zero-error compilation) integrating Phase 8A–8C (`G1–G3`, `P1/P2`, `Hard-BareTier2` vs `Soft-Coupled / Tier2-Composite` mechanistic insight, `Q8.4` `180`-cell factorial stress surface & `90`-group subset, Fig. 1–5, and strict scientific honesty bounds).

---

## 4. Verification, External AI Review (`aid`), and Clean Merge Checklist

Before reporting completion back to Leader (`team-833`):
1. Run full pytest suite (`>=193` canonical tests + new Phase 8C tests) -> `0` failures, `0` skips.
2. Run future-weather perturbation invariance tests (`>=60` checks) -> `100%` pass.
3. Verify `100%` daily N/C mass conservation audit across all Phase 8B + Phase 8C native episodes (`|N| < 1e-10`, `|C| < 1e-9` kg/ha).
4. Verify asset preservation counts (`1,782` legacy assets, `242` Phase 7 assets, `2,188` tracked sources/evidence, `data/phase8-combined-evaluation` 2,017 episodes intact, `pcse` untouched).
5. Verify `plan check` passes and manuscript LaTeX compiles cleanly to PDF without unresolved references or missing figures.
6. Run independent external AI review (`aid` quorum using available models such as `gemini-4-carbon-high`, `deepseek`, `kimi`), resolve any genuine bugs or factual/formatting inconsistencies, and record council receipt JSON under `reports/phase8/`.
7. Cleanly merge `feat/phase8c-supplement-and-q84` into `NUE_PCSE-Gym` `main` and root `master`, remove temporary worktrees and feature branches, verify clean `git status` and post-merge checks on `master`/`main`, and leave a concise machine-verifiable completion report in OUTBOX with exact file paths, git SHAs, test counts, conservation max errors, and key metric tables.

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
  `agent-bus doorbell --leader team-4031428b3351 --worker team-832 --job-id lead-team-4031428b3351-team-832-20261116T050646-014887 --attempt-epoch 30 --status completed --summary "<one-line conclusion>"`
