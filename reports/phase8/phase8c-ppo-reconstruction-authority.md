# Authorization: Deterministic `TRAIN`-Only Reconstruction of `SensorlessPPO` Checkpoints (Option A) and Full Phase 8C Completion

**Decision `phase8c_missing_frozen_ppo_recovery` -> Approved: Option A (Leader Authorization)**

You are explicitly authorized to proceed with your proposed **Option A** within the exact `rebuild_boundary` in `OUTBOX.json`:

1. **Deterministic `TRAIN`-Only Reconstruction (Versioned Separately)**:
   - Run the exact Phase 8B `TRAIN`-only recipe (`scripts/phase8-train-sensorless-ppo.py`, `seeds = [4, 17, 29]`, `151,552` decision steps per seed, `0` hyperparameter changes, CPU `torch.set_num_threads(1)`, frozen `cache/phase8b-train-sensorless-ppo-inputs.joblib`, zero Dev/evaluation label access, no checkpoint selection).
   - Save the reconstructed checkpoints in **`models/phase8c-controls/ppo-sensorless-reconstructed-seed{seed}/`** (`model.zip`, `vecnormalize.pkl`, `episodes.csv`, `receipt.json`). Do **not** overwrite or masquerade under `models/phase8-controls/PPO-Sensorless-seed{seed}/` and never claim original ZIP container SHA256 hashes were recovered.
   - Audit and record in `reports/phase8/phase8c-ppo-reconstruction-audit.json`:
     - Exact SHA256 comparison of reconstructed `episodes.csv` and `vecnormalize.pkl` and `weight_change_L2` against the tracked Phase 8B `models/phase8-controls/PPO-Sensorless-seed{seed}/receipt.json` / files, AND
     - Decision-action agreement on the `198` archived Phase 8B `SensorlessPPO` episodes in `data/phase8-combined-evaluation`.
   - Allow `SensorlessPPOPolicy` in `agromas_v8/policies.py` to accept an explicit optional `model_dir` (defaulting to `models/phase8-controls/PPO-Sensorless-seed{seed}` so existing tests/APIs remain 100% compatible) and point Phase 8C evaluations to `models/phase8c-controls/ppo-sensorless-reconstructed-seed{seed}/`.

2. **Seal `phase8c-frozen-cases-v3.json` & `phase8c-evaluation-permit.json`**:
   - Generate `reports/phase8/phase8c-frozen-cases-v3.json`: keep the `521` identical non-PPO reused cases verified by SHA256, remove the `198` old-PPO reuse entries, and evaluate all `17,747` remaining cases (`18,268` total across all `180` factorial cells + `90`-group continuity subset + `P1/P2/G3` supplements).
   - Seal `phase8c-evaluation-permit.json` (+ `.sha256`) registering the reconstructed `models/phase8c-controls/ppo-sensorless-reconstructed-seed{seed}/` files (`model.zip`, `vecnormalize.pkl`, `receipt.json`) alongside the `95` surviving model files (and explicitly noting the 3 missing gitignored Phase 8B ZIPs).

3. **Execute 16-Worker World-Grouped Native Campaign (`scripts/phase8c-run-campaign.py`)**:
   - Implement the `16`-worker partition over the `170` unique `(region, year, climate, source)` worlds with within-world stage prefix & executed `(u1, u2, u3)` native `WOFOST81-SNOMIN` trajectory caching (verifying 100% parity with `run_episode` and 100% daily N/C mass conservation `max |N| < 1e-10`, `max |C| < 1e-9` kg/ha).

4. **Complete All Phase 8C Deliverables, Review, Promotion & Clean Merge**:
   - Complete `scripts/phase8c-analyze-results.py`, `Fig. 1–5` (addressing the Gemini `Fig. 1` connector/text fixes and validating via Python / `validate_drawio.py` / `method_diagram.py check` / external `aid` — **never calling Codex `view_image`**), `reports/phase8/PHASE8_TOP_JOURNAL_REPORT.md`, `storyline-v2.0.md`, `_wiki/method.md`, `_wiki-methodology/_top/_questions/Q8.md` (`Q8.4` via `plan` CLI + `plan check`), and the bilingual top-journal manuscript (`TeX` + `PDF`).
   - Run full pytest suite (`0` failures, `0` skips), `120` future-weather invariance checks, 100% daily N/C mass audit, preservation verification, and external AI council (`aid`).
   - Merge `feat/phase8c-supplement-and-q84` cleanly into `NUE_PCSE-Gym` `main` and root `master`.
   - **CRITICAL**: Write and run an updated promotion script (`scripts/phase8c-promote-local-artifacts.py`) that explicitly promotes ALL untracked/gitignored local Phase 8C artifacts — specifically including **`models/phase8c-controls/` (with all `*.zip` and `*.pkl` files!)**, `data/phase8c-supplemental-evaluation/`, `cache/phase8c*`, and `_reports/` — into `/mnt/data/yongan-admin-2/projects/自己-智慧农业-精准施肥智能体`, verifying every SHA256 hash AFTER moving and BEFORE removing the worktree!
   - Remove temporary worktrees/branches cleanly and ring the doorbell with complete machine-verifiable results in `OUTBOX.json`.

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
  `agent-bus doorbell --leader team-4031428b3351 --worker team-832 --job-id lead-team-4031428b3351-team-832-20261116T050646-014887 --attempt-epoch 32 --status completed --summary "<one-line conclusion>"`
