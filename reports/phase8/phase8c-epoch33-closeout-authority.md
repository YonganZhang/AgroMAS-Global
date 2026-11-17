# STEER: Phase 8C Post-Analysis Final Closeout

Your Codex pane refreshed from `%832` to `%1293` during context compaction and has now been rebound to `%1293` in `team-4031428b3351`.

## Already Complete — Do NOT Re-run
Both the native campaign and core statistical analysis have already completed cleanly (`exit_code = 0`):
- `reports/phase8/phase8c-campaign-receipt.json`: `18,268 / 18,268` cases completed (`17,747` new native + `521` SHA256-verified reused; `170` worlds; `1,917` unique trajectories; `15,830` exact trajectory cache hits; `16/16` workers exited `0`).
- `reports/phase8/phase8c-analysis.log` & `reports/phase8/phase8c-core-statistics.json`: `367` summary groups, `13,512` Holm-adjusted contrasts, `phase8c-180cell-stress-surface.csv`, `phase8c-canonical90-stress-subset.csv`, and `5,928,274` daily records audited (`all_passed: true`, `max_N = 1.927e-11`, `max_C = 2.115e-10` kg/ha).

**Do NOT re-run `scripts/phase8c-run-campaign.py` or `scripts/phase8c-analyze-results.py`.**

## Strict Operational Guardrails
1. **Never call `view_image`**: Codex `view_image` triggers `400 Bad Request` on this proxy. Use Python inspection scripts and external `aid` reviews instead.
2. **External `aid` model selection**: **Do NOT invoke `claude` or `kimi`** (their quotas are currently closed/rejected). Use **`gemini` and `deepseek`** only for visual and technical reviews.

## Remaining Deliverables (Execute in Order)
Working repo: `/mnt/data/yongan-admin-2/projects/worktrees/agromas-phase8c` (branch `feat/phase8c-supplement-and-q84`).

### 1. Finalize Figures `Fig. 1–5`
- Address all visual/layout findings in `reports/phase8/phase8c-fig1-gemini-visual-review.md` for `Fig. 1`; validate diagrams (`validate_drawio.py` / `method_diagram.py check`) and confirm layout cleanliness via `gemini`.
- Generate and polish `Fig. 2–5` directly from `reports/phase8/phase8c-core-statistics.json`, `phase8c-180cell-stress-surface.csv`, and `phase8c-canonical90-stress-subset.csv`:
  - `Fig. 2`: `P1` `Former-Held-Out` benchmark & `Soft-Coupled` vs `Tier2-Composite` vs `hard-bare-tier2` regime ablation (`26.73%` vs `25.06%` vs `4.00%`).
  - `Fig. 3`: `P2` Cross-regional `LOYO` (`Former-Held-Out` n=40 & `Public-Reused` NL n=4), attribution / regime behavior, and regional breakdown (`AU`, `US`, `NL`, `FR`, `CN`).
  - `Fig. 4`: `Q8.4` full `180`-cell factorial stress surface (`cap x N-price x subsidy x climate`) + `90`-group canonical continuity subset + `subsidy-diagnostic`.
  - `Fig. 5`: Deployment architecture (`36-D` backbone + `64-D` low-rank adapter, `Regime` class, runtime/telemetry footprint) + physical `N`/`C` mass-conservation audit across `5,928,274` daily records (`max_N <= 1.93e-11`, `max_C <= 2.12e-10` kg/ha).
- Inspect rendered PNGs/PDFs programmatically (bounds, contrast, zero overlaps/truncations, exact numeric parity with `phase8c-core-statistics.json`) and run a `gemini` visual check on `Fig. 1–5`.

### 2. Update Reports, Storyline, Wiki & `Q8.4`
- Update `reports/phase8/PHASE8_TOP_JOURNAL_REPORT.md` (strictly preserve `PHASE8B_CORE_EXPERIMENTS_G1_G2_G3_REPORT.md` intact).
- Create/update `storyline-v2.0.md` (strictly preserve `storyline-v1.0.md` intact).
- Update `_wiki/method.md` using exact locked naming (`Regime` class, `36-D` backbone + `64-D` low-rank adapter, active `climate` propagation fix, qualified `AU` within-region $N_{\text{loss}}$ $R^2$, `Tier2-Composite` / `Soft-Coupled` / `hard-bare-tier2`, `180`-cell factorial + `90`-group continuity subset).
- Complete `Q8.4` in `_wiki-methodology/_top/_questions/Q8.md` via `plan` CLI and verify `plan check` exits `0`.

### 3. Bilingual Top-Journal Manuscript (`TeX` + `PDF`)
- Update both English and Chinese top-journal manuscripts (`TeX`) with all Phase 8C `P1/P2/G3/Q8.4` statistics, `Fig. 1–5`, and tables.
- Compile PDFs cleanly (`0` undefined refs/citations, `0` missing figures, `0` fatal TeX errors) and check page/float placement programmatically.

### 4. Final Verification & External `aid` Audit
- Run the full pytest suite (`>= 217` tests, `0` failed, `0` skipped) and the `120` future-weather invariance checks (`60` soft + `60` hard-composite).
- Run external `aid` technical & manuscript consistency audit using **`gemini` and `deepseek`** only; fix any substantive factual/numerical/logic discrepancy and confirm clean re-verification.

### 5. Artifact Promotion, Clean Merge to Main/Master & Cleanup
- Commit all tracked edits cleanly inside `/mnt/data/yongan-admin-2/projects/worktrees/agromas-phase8c`.
- Verify preservation of Phase 8B archival deliverables (`PHASE8B_CORE_EXPERIMENTS_G1_G2_G3_REPORT.md`, `storyline-v1.0.md`, etc.).
- **Before deleting the worktree**, promote ALL untracked/gitignored Phase 8C artifacts via `scripts/phase8c-promote-local-artifacts.py` into `/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体`, explicitly verifying that:
  - `models/phase8c-controls/**` (`*.zip`, `*.pkl`, manifests)
  - `data/phase8c-supplemental-evaluation/`
  - `cache/phase8c*`
  - `reports/phase8/*`, `_reports/`, `figures/`
  are present on primary and pass **exact SHA256 verification**.
- Cleanly merge `feat/phase8c-supplement-and-q84` into `NUE_PCSE-Gym` `main` and root `master` in `/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体`.
- Remove temporary worktrees and feature branches cleanly after verifying primary repo status, test suite pass on primary, and promoted artifact SHA256 match.
- Write a complete closing receipt to `OUTBOX.json` (git commits, test/invariance counts, `plan check`, external `aid` paths/verdicts, SHA256 promotion audit, cleanup confirmation) and ring the leader doorbell.

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
  `agent-bus doorbell --leader team-4031428b3351 --worker team-832 --job-id lead-team-4031428b3351-team-832-20261116T050646-014887 --attempt-epoch 33 --status completed --summary "<one-line conclusion>"`
