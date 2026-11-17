# Foreign Aid Result

JOB_ID: 20261116T013503__gemini__2615518
PROVIDER: gemini
COMPLETION_STATUS: COMPLETE
ERROR_CLASS: NONE

## Summary
An independent, strictly read-only code, provenance, numerical, and scientific-honesty gate audit of Phase 8B G1–G3 found **zero blocking defects, zero post-outcome tuning or data leakage, and 100% numerical agreement** across all 2,017 completed native evaluation episodes, SHA256 freezes, daily C/N conservation audits, 1,753 seed-averaged annual records, 79 summary table rows, and 512 exploratory paired contrasts; all eight pre-evaluation Gemini review findings are cleanly resolved in current `agromas_v8` code and reports, negative G2/G3 scientific outcomes and scope limits remain prominently disclosed without masking, Q8.4 and manuscript TeX/PDF/figures remain unstarted, and only four minor non-blocking editorial/telemetry hygiene items (none affecting any physical action, seasonal outcome, mass balance, or statistical conclusion) were identified.

## Work Performed
- Audited all primary Phase 8B reports, verdicts, freezes, and pre-evaluation reconciliation artifacts (`PHASE8B_CORE_EXPERIMENTS_G1_G2_G3_REPORT.md`, `PHASE8B_G1_GATE_REPORT.md`, `phase8b-G1-verdict.json`, `phase8b-core-verdict.json`, `phase8b-pre-evaluation-Gemini-reconciliation.json`, original Gemini review `20261116T003014__gemini__1437000/result.md`, `phase8b-pre-evaluation-local-reconciliation.json`, `phase8b-diagram-factual-caption.md`, `phase8b-prior-admissibility-audit.json`, `phase8b-P2-adapter-training-freeze.json`, `phase8b-P2-preparation-repair.json`, `phase8b-green-stress-TRAIN-freeze.json`, `phase8b-Phase7-historical-cohort-reference.json`, `phase8b-TRAIN-physical-decoding.json`, and `phase8b-full-TRAIN-physical-decoding.json`).
- Inspected recovery provenance and exact pre-repair source snapshots (`PHASE8B_NATIVE_HALT_AND_REPAIR_REPORT.md`, `phase8b-epoch28-recovery-authorization.md`, `phase8b-proposed-recovery-manifest.json`, `phase8b-final-evaluation-permit.json`, `recovery1/{receipt.json,phase8b-recovery-permit.json}`, `recovery2/{receipt.json,phase8b-recovery-permit.json}`, `phase8b-combined-campaign-receipt.json`, `phase8b-first-campaign-source-snapshot/policies.py`, and `phase8b-recovery1-source-snapshot/referee.py`).
- Reviewed the full `NUE_PCSE-Gym/pcse_gym/agromas_v8/` implementation (`planning.py`, `policies.py`, `prior_adapter.py`, `controller.py`, `joint_model.py`, `referee.py`, `ledger.py`, `agents.py`, `book_policy.py`, `online_features.py`, `tree_weather.py`, `climate.py`, `data.py`, `models.py`, `ood.py`, `scoring.py`), `NUE_PCSE-Gym/tests/test_phase8_planning.py`, and orchestration/analysis scripts `scripts/phase8-{run-locked-campaign,recover-locked-campaign,continue-unstarted-cases,collect-recovered-results,analyze-recovered-core-results,write-recovered-core-report}.py`.
- Executed isolated read-only Python verification (`readonly_audit.py` in conversation scratch directory, launching zero physics/fitting and accessing zero private 64-D prior vectors) across all 2,017 serialized `result.json` files, permit/model/dependency SHA256 digests, failure directories, seed-averaged CSV metrics, G2/G3 markdown tables, 5,000-draw paired bootstrap CIs, exact binomial sign tests, exact `2^n_eff` dynamic-programming Wilcoxon signed-rank p-values (cross-checked via brute-force bitmask enumeration on all 355 contrasts with `0 < n_eff <= 14`), 512-test Holm adjustments, online future-weather/Stage-2 action invariance receipts, and sealed Phase 5 physical books for finite-grid ceilings.

## Evidence
### 1. Verified Gate Integrity, Recovery Provenance & Numerical/Statistical Reproductions (PASS)
- **Pre-Evaluation Gemini Review Reconciliation (`phase8b-pre-evaluation-Gemini-reconciliation.json`)**: All 8 prior findings are genuinely resolved:
  - `prior_adapter.py:30-42`: Site-year weights are normalized (`original[group] /= original[group].sum(); w = original / original.sum()`) and OOD cutoffs use `weighted_quantile(reconstruction, w, .99)` and `weighted_quantile(distance, w, .99)`, reducing China LOYO outer-train `Full64` rejections from 25% to `0 / 279,888` (`China_LOYO_Full64_train_rejections == 0` in `phase8b-prior-admissibility-audit.json`).
  - `joint_model.py:49-54`, `controller.py:33,44-45`, `policies.py:24,28`, `referee.py:68`: Per-decision `radius`, `prior_accepted`, `prior_timing_admissible`, `prior_ood`, `prior_kind`, and expanded `request_hash` (including `history_hash`, `tax`, `monolithic`, `adapter_tag`, `adapter_context`) are logged end-to-end.
  - `policies.py:63,70-76`: `FixedDosePolicy` checks `day < date(case['year'], month, day_of_month)` directly (preventing NH autumn year-wrap) and computes `climate.tree` / `response_tensor` once without redundant `team.choose` calls.
  - `PHASE8B_CORE_EXPERIMENTS_G1_G2_G3_REPORT.md:91,116,158` & `phase8b-diagram-factual-caption.md`: Matched `TreeMLP-extreme-subset` (`31` Former + `3` Public = `34` extreme site-years) is reported directly alongside `remove-climate`; annual-end timing (`34,986/34,986`), CN `basal=171` budget legality, 100% LORO spatial/static OOD fallback, and the distinction between the 36-D PyTorch `WorldModel` (`13,155` parameters) and fold-local 64-D `PCA<=4 / Ridge(alpha=10)` P2 adapters plus one-way offline physical decoding are explicitly documented.
- **Append-Only Recovery Provenance & Exact Code/Weight Freezes**:
  - Permit sidecar SHA256s pass for `phase8b-final-evaluation-permit.json`, `recovery1/phase8b-recovery-permit.json`, and `recovery2/phase8b-recovery-permit.json`; `0/210` files in `phase8b-external-inference-dependency-freeze.json`, `0` files in `recovery2/phase8b-recovery-permit.json`, and `0/70` P2 `.joblib` adapters in `phase8b-P2-adapter-training-freeze.json` drifted on disk; `git status` in `NUE_PCSE-Gym` and `pcse` is completely clean.
  - Diffing `phase8b-final-evaluation-permit.json` -> `recovery1` confirms **only** `NUE_PCSE-Gym/pcse_gym/agromas_v8/policies.py:101-104` changed among frozen code/models (restricting `LegacyV6Policy` `self.models[stage]` calls to `xx[legal]` while keeping legacy `fert / 3.5 / fert+3.5` placeholders on illegal rows, covered by `test_phase8_planning.py:82-96`), plus append-only `scripts/phase8-recover-locked-campaign.py` and `recovery1/phase8b-locked-campaign-cases.json`.
  - Diffing `recovery1` -> `recovery2` confirms **only** `NUE_PCSE-Gym/pcse_gym/agromas_v8/referee.py:15-21` changed among frozen code/models (`class WURHistoricalWeather(CSVWeatherDataProvider)` subclassing the identical native CSV provider to pass Engine trait validation prior to seasonal integration, covered by `test_phase8_planning.py:98-109`), plus append-only `scripts/phase8-continue-unstarted-cases.py` and `recovery2/phase8b-locked-campaign-cases.json`.
  - Directory audit confirms: `data/phase8-locked-evaluation` holds `6` completed `result.json` + `2` failed `error.json` (`6a803c766964009533af`, `7b32cf0df485272c0f29` raising `ValueError('Candidate exceeds available fertilizer budget')`, with no `result.json` / external daily audit, transparently excluded from performance) + `STOP`; `data/phase8-locked-recovery1` holds `1,454` completed `result.json` + `4` pre-integration WUR constructor `TraitError` `error.json` (`55825292afea2e97ac8e`, `712927622f97597e6edd`, `cb8bb2748fcd98c654a3`, `f2309951ce24ee2be2a9`) + `0` other incomplete prefixes + `STOP`; `data/phase8-locked-recovery2` holds the remaining `557` completed `result.json` (including both epoch28-authorized incomplete restarts and the 4 WUR cases) + `0` errors. All `6 + 1,454 + 557 = 2,017` completed IDs are pairwise disjoint, match `phase8b-locked-campaign-cases.json` (`2,017` IDs), and preserve byte-identical SHA256 hashes for the original `6` and `1,460` prior completed seasons.
- **Daily C/N Mass Closure, Strata Separation, PPO Seed Averaging & Statistical Verification**:
  - Across all `2,017` completed `result.json` files (`679,772` daily records): `2,017/2,017` pass `mass_audit` with `max|N| = 1.716671249596402e-11 kg/ha < 1e-10` and `max|C| = 1.9736035028472543e-10 kg/ha < 1e-9`, exact `outcome[4] == native_fertilizer_N_kg_ha` (`<= 1e-6`), `<= 220 kg N/ha` total budget, and `>= 14`-day positive-event spacing on all v8-scheduled episodes (`ledger.py:3-10`, `referee.py:72-75`).
  - Every `LegacyV6PPO` and `SensorlessPPO` site-year context averages exactly seeds `(4, 17, 29)`, reproducing `phase8b-case-metrics-seed-averaged.csv` (`1,753` rows, `max_abs_diff = 0.0`) and all `79` rows of the G2/G3 markdown table (`PHASE8B_CORE_EXPERIMENTS_G1_G2_G3_REPORT.md:76-154`) with strict unpooled separation of `NASA` vs `WUR`, `Former-Held-Out` (`52` P1 NASA, `40` P2) vs `Public-Reused` (`7` P1 NASA, `7` P1-WUR, `4` P2 NL), and `LOYO` (`44`) vs `LORO` (`44`).
  - All `512` contrasts in `phase8b-core-statistics.json` exactly match independent re-computation: `B = 5000`, `seed = 20261115`, `SOLVABLE_CORE_EQUAL3` resampling paired years within each of `(NL, US, AU)` before equally averaging regional effects, exact two-sided `binomtest` sign p-values (with NL `n = 5` minimum `p = 0.0625`), exact `2^n_eff` signed-rank DP over `2 * rankdata(|nonzero|, method='average')` (matching `phase8b-recovered-statistics-analytic-check.json` at `n = 5` `p = 0.0625` and `n = 28` `p = 7.4505806e-9`, plus brute-force `2^k` verification across 355 contrasts), and full 512-family step-down Holm adjustment.
  - Sealed Phase 5 Held-Out Historical physical books (`reports/phase5/final-physical-book-receipt-v4.json`) independently confirm exact finite-GRID cap-40 joint ceilings: `AU 11/11 (basal=0)`, `US 12/12 (basal=0)`, `NL 4/5 (basal=0)`, `FR 1/12 (basal=0)`, `CN 0/12 (basal=171)`. Online future-weather perturbation receipts (`phase8b-online-action-invariance.json` and `phase8b-positive-action-invariance.json`) confirm `30/30` root and `30/30` positive-dose Stage-2 in-domain invariance checks passed.

### 2. Concrete Non-Blocking Code / Report-Script Observations (Zero Impact on Scored Outcomes)
- **Observation A — Post-Generation Edits to Primary Report Not Back-Ported to Generator Script + GFM Delimiter Mismatch (`scripts/phase8-write-recovered-core-report.py:8-22` vs `reports/phase8/PHASE8B_CORE_EXPERIMENTS_G1_G2_G3_REPORT.md:5-38,63-70`)**:
  - *Detail*: `PHASE8B_CORE_EXPERIMENTS_G1_G2_G3_REPORT.md` includes two important post-generation sections (`## Realized verdict` at lines 5–38 and the 177,930-row full-TRAIN N-loss decoding table at lines 63–70, whose values match `phase8b-core-statistics.json` and `phase8b-full-TRAIN-physical-decoding.json` to all printed decimals) that are absent from `scripts/phase8-write-recovered-core-report.py`. Re-running `phase8-write-recovered-core-report.py` would overwrite those sections. In addition, line 65 (`|Track|Global latent R2|Global raw-feature R2|AU|CN|FR|NL|US|`) has 8 header columns whereas line 66 (`|---|---:|---:|---:|---:|---:|---:|---:|---:|`) has 9 delimiter cells, causing strict GFM parsers not to render lines 65–68 as a table.
  - *Impact*: Editorial/regeneration hygiene only; zero numerical discrepancy.
- **Observation B — Omitted Metadata Keys on `open-loop` Stage 2/3 OOD Fallback (`NUE_PCSE-Gym/pcse_gym/agromas_v8/policies.py:16` & `referee.py:68`)**:
  - *Detail*: When `TreePolicy(mode='open-loop')` hits `not applicable` at Stage 2 or 3 (`self.frozen is not None`), `policies.py:16` returns `dict(dose=0., tier=3, reason='OOD_operational_zero_not_compliance', active_eco=True, active_econ=True)` without `applicable=False`, `OOD_score`, `radius`, or `request_hash` (unlike Stage 1 OOD via `policies.py:28` or in-domain Stage 2/3 via `policies.py:24`). Across 177 `open-loop` stage decisions, this branch executed 14 times (e.g., episode `454965f0092039d15568`, Stage 3 on `2021-05-10`), recording `null` for those four trace metadata fields.
  - *Impact*: Zero impact on executed physical dose (`0.0`), tier (`3`), seasonal metrics, or Tier 1/2/3 shares (`open-loop` is evaluated solely in P1 with `remove=None`); affects step-level trace telemetry completeness only.
- **Observation C — Inactive Economic-Parameter Omissions in Auxiliary Comparators (`NUE_PCSE-Gym/pcse_gym/agromas_v8/referee.py:92` & `policies.py:71,77`)**:
  - *Detail*: `run_native_nl_reference` (`referee.py:92`) omits `-case.get('tax',0)*max(m[2],0)` when computing `partial_profit` (unlike `run_episode` at `referee.py:76`), and `FixedDosePolicy.choose` (`policies.py:71,77`) instantiates `Regime(cap=case.get('cap',40), radius=self.team.model.radius)` without `price_multiplier`/`subsidy`/`tax` and omits `applicable=False`/`OOD_score` on OOD return.
  - *Impact*: Zero impact on Phase 8B G1–G3 because all 2,017 locked campaign cases have `tax == 0.0` and all `DVS-N2` / `N2-PA-matched` cases use `(price_multiplier=1.0, subsidy=0.0, tax=0.0)` while `FixedDosePolicy` scores solely by `-abs(dose - target)`. Relevant only as a preventative guard if future `Q8.4` tax surfaces ever invoke `run_native_nl_reference` with `tax > 0`.
- **Observation D — Minor Cosmetic Documentation Strings (`reports/phase8/PHASE8B_G1_GATE_REPORT.md:10`, `_codemap.md:28`)**:
  - *Detail*: `PHASE8B_G1_GATE_REPORT.md:10` prints `mlp` instead of `residual-mlp` in the `结构` column of row `Sensorless-residual-mlp` (all metrics `0.0769 | 89.76% | 5.421 / 8.544 | True` match `phase8b-G1-verdict.json`), and `_codemap.md:28` retains one stale Phase 8A sentence stating 64-D DL/audit/tool wiring is not yet implemented directly between lines 27 and 31 documenting Phase 8B `agromas_v8` completion.
  - *Impact*: Cosmetic text only; zero impact on code or results.

### 3. Scientific & Statistical Limitations Verified as Honest Disclosures (Not Code Bugs)
- **G1 Pass Without G2 Policy Superiority**: Primary `TreeMLP` passes G1 (`89.46%` / `90.82%` retrospective leave-one-Dev-year-out coverage; regret `3.726` / `4.914` EUR/ha vs ExtraTrees `8.184` / `8.544` EUR/ha), but on P1 52 Former-Held-Out NASA site-years achieves `9.67%` (`Full-Telemetry`) and `4.00%` (`Sensorless`) region-equal joint compliance versus `20.54%` (`LegacyV6PPO`), `20.21%` (`LegacyV6Full`), `19.91%` (`DVS-N2`), `23.01%` (`SensorlessPPO`; 3-region gap `-28.91pp`, CI `[-40.98, -17.68]pp`, raw sign `p = 0.00048828`, Holm `p = 0.23974609`), and `26.73%` (`soft`). In both tracks, P1 Former `TreeMLP` makes `0.00%` Tier 1, `76.28%` Tier 2, and `23.72%` Tier 3 decisions — reflecting genuine conservativeness of hard upper-tail/corridor coupling rather than an implementation error.
- **P2 Conditional Backbone & 100% LORO Spatial/Static OOD Fallback**: P2 (`40` Former + `4` Public NL per scheme, never pooled into 88 farms) conditions on a frozen 1995–2009 backbone already trained across all 5 regions. In LOYO Former, `P2-Full64` (`10.22%`, `105/120` online priors accepted) minus `P2-Static3` (`6.22%`, `120/120` accepted) yields an inconclusive 3-region paired effect of `+6.67pp` (`95% CI [-13.33, +26.67]pp`, `sign p = 1.0`), below `P2-ExtraTrees64` (`12.00%`). In LORO, `Full64` and `Static3` reject `34,986/34,986` offline outer-test rows and `132/132` online episode decisions (`accepted = 0`, `prior_ood = True`), collapsing identically to `4.00%` Former / `0.00%` Public NL with differences across P2 LORO spatial/static variants governed solely by fallback calibration radii `max(backbone_radius, adapter_radius)`.
- **Organizational Bit Parity, Unproven Global Chance/CVaR Optimality & Domain Scope**: Five-specialist modular execution is bit-for-bit identical to monolithic `CoreAgronomicAgent` (`test_phase8_planning.py:9-16`), claiming zero agent-count advantage; nodewise Tier selection over coarsened 7-day rain/temperature bins is non-anticipative (`test_phase8_planning.py:18-30`) without claiming global multi-stage chance/CVaR optimality; TRAIN OOF residuals condition on realized TRAIN weather scenario descriptors; `50 EUR/ha` is an illustrative TRAIN-responsive stress candidate (`27` TRAIN plan changes), not enacted law or a minimum-compliance subsidy; within-region TRAIN N-loss latent OOF $R^2$ is predominantly negative; and Q8.4, the 90-cell stress surface, and manuscript figures/TeX/PDF remain unstarted.

### 4. Coverage Gaps Under Read-Only Constraints
- Per task constraints, no new WOFOST/PCSE simulations, PyTorch/sklearn model fits, pytest suites invoking physics fixtures, or raw 64-D vector value inspections were executed; verification relied on cryptographic SHA256 freezes, pre-repair source snapshots, code inspection, and complete read-only re-aggregation of all 2,017 serialized episode ledgers/traces and sealed physical books.

## Files Changed Or Reviewed
- **Foreign-Aid Contract Files Written (Mandatory Report Directory Only)**:
  - `/mnt/data/yongan-admin-2/projects/worktrees/agromas-phase8b/_reports/_foreign_aid/20261116T013503__gemini__2615518/progress.md`
  - `/mnt/data/yongan-admin-2/projects/worktrees/agromas-phase8b/_reports/_foreign_aid/20261116T013503__gemini__2615518/result.md`
- **Project Source & Report Files Modified**:
  - None (strictly read-only audit; verified via `git --no-optional-locks status --short`).
- **Repository Files Reviewed**:
  - `reports/phase8/PHASE8B_CORE_EXPERIMENTS_G1_G2_G3_REPORT.md`
  - `reports/phase8/PHASE8B_G1_GATE_REPORT.md`
  - `reports/phase8/phase8b-G1-verdict.json`
  - `reports/phase8/phase8b-core-verdict.json`
  - `reports/phase8/phase8b-core-statistics.json`
  - `reports/phase8/phase8b-case-metrics-seed-averaged.csv`
  - `reports/phase8/phase8b-combined-campaign-receipt.json`
  - `reports/phase8/phase8b-locked-campaign-cases.json`
  - `reports/phase8/phase8b-pre-evaluation-Gemini-reconciliation.json`
  - `reports/phase8/phase8b-pre-evaluation-Gemini-review/20261116T003014__gemini__1437000/result.md`
  - `reports/phase8/phase8b-pre-evaluation-local-reconciliation.json`
  - `reports/phase8/PHASE8B_NATIVE_HALT_AND_REPAIR_REPORT.md`
  - `reports/phase8/phase8b-epoch28-recovery-authorization.md`
  - `reports/phase8/phase8b-proposed-recovery-manifest.json`
  - `reports/phase8/phase8b-final-evaluation-permit.json`
  - `reports/phase8/recovery1/receipt.json`
  - `reports/phase8/recovery1/phase8b-recovery-permit.json`
  - `reports/phase8/recovery2/receipt.json`
  - `reports/phase8/recovery2/phase8b-recovery-permit.json`
  - `reports/phase8/phase8b-first-campaign-source-snapshot/policies.py`
  - `reports/phase8/phase8b-recovery1-source-snapshot/referee.py`
  - `reports/phase8/phase8b-prior-admissibility-audit.json`
  - `reports/phase8/phase8b-P2-adapter-training-freeze.json`
  - `reports/phase8/phase8b-P2-preparation-repair.json`
  - `reports/phase8/phase8b-diagram-factual-caption.md`
  - `reports/phase8/phase8b-daily-ledger-audit.json`
  - `reports/phase8/phase8b-recovered-statistics-analytic-check.json`
  - `reports/phase8/phase8b-canonical-test-receipt.json`
  - `reports/phase8/phase8b-green-stress-TRAIN-freeze.json`
  - `reports/phase8/phase8b-Phase7-historical-cohort-reference.json`
  - `reports/phase8/phase8b-TRAIN-physical-decoding.json`
  - `reports/phase8/phase8b-full-TRAIN-physical-decoding.json`
  - `reports/phase8/phase8b-online-action-invariance.json`
  - `reports/phase8/phase8b-positive-action-invariance.json`
  - `reports/phase8/phase8b-preregistered-protocol.json`
  - `reports/phase8/README.md`
  - `reports/phase6/PHASE6_TOP_JOURNAL_REPORT.md`
  - `reports/phase5/final-physical-book-receipt-v4.json`
  - `_wiki-methodology/_wiki/method.md`
  - `_wiki-methodology/_wiki/paper-storyline/_current.yml`
  - `_codemap.md`
  - `NUE_PCSE-Gym/pcse_gym/agromas_v8/{planning,policies,prior_adapter,controller,joint_model,referee,ledger,agents,book_policy,online_features,tree_weather,climate,data,models,ood,scoring}.py`
  - `NUE_PCSE-Gym/tests/test_phase8_planning.py`
  - `scripts/phase8-{run-locked-campaign,recover-locked-campaign,continue-unstarted-cases,collect-recovered-results,analyze-recovered-core-results,write-recovered-core-report}.py`
  - `data/phase8-locked-{evaluation,recovery1,recovery2}/*/result.json` and `*/error.json` (2,017 completed + 6 preserved error records)

## Errors Or Blockers
None

## Next Steps
- Treat the Phase 8B G1–G3 core experimental and provenance gate as **verified ready for closeout/archive**, preserving the prominent negative G2/G3 conclusions, 100% LORO spatial/static OOD fallback disclosure, and two-stage append-only recovery records without post-outcome retuning.
- Optionally (without re-scoring any season or touching frozen evaluation permits): sync `scripts/phase8-write-recovered-core-report.py` with the `## Realized verdict` and 177,930-row N-loss decoding sections of `PHASE8B_CORE_EXPERIMENTS_G1_G2_G3_REPORT.md`, remove the extra 9th delimiter cell on `PHASE8B_CORE_EXPERIMENTS_G1_G2_G3_REPORT.md:66`, correct the `residual-mlp` label typo in `PHASE8B_G1_GATE_REPORT.md:10`, and update the stale Phase 8A placeholder line in `_codemap.md:28`.
- Before launching any separately authorized `Q8.4` 90-cell stress surface in the future, include `-case.get('tax', 0) * max(m[2], 0)` in `run_native_nl_reference` (`referee.py:92`) if native NL descriptive references will be evaluated at `tax > 0`, and populate `applicable`/`OOD_score` in `TreePolicy` `open-loop` Stage 2/3 OOD returns (`policies.py:16`) if trace metadata parity is desired.
