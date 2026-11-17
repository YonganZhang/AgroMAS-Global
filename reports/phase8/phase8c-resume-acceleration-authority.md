# Resume Phase 8C Without `view_image` and Accelerate Campaign by World Grouping

You paused at the Codex prompt because calling Codex's built-in `view_image` tool on `fig2-g1.png` triggered an upstream proxy `400 {"detail":"Bad Request"}` error and aborted the turn. Do **not** call `view_image` anywhere in this job.

## Immediate Resume Checklist (in `/mnt/data/yongan-admin-2/projects/worktrees/agromas-phase8c`)

1. **Never Call `view_image`**:
   - For figure QA / overlap / whitespace / layout verification, use Python (`PIL` / `matplotlib` bounding-box & contrast checks), `validate_drawio.py` / `method_diagram.py check`, or external `aid` (`gemini-4-carbon-high` if image inspection is needed). Never invoke Codex `view_image`.
2. **Preserve Already Completed Pre-Campaign Work**:
   - Worktree `/mnt/data/yongan-admin-2/projects/worktrees/agromas-phase8c` and submodule `NUE_PCSE-Gym` (`e1f5626`, branch `feat/phase8c-supplement-and-q84`) already have the repaired composite planning & climate propagation, passing canonical tests + invariance checks, ignored models copied, and `reports/phase8/phase8c-frozen-cases-v2.json` (`18,268` cases = `17,549` new across `170` unique `(region, year, climate, source)` worlds + `719` reused).
   - Ensure `scripts/phase8c-seal-permit.py` and `reports/phase8/phase8c-evaluation-permit.json` (+ `.sha256`) are finalized cleanly.
3. **Accelerate `scripts/phase8c-run-campaign.py` via Exact World Grouping + Native Trajectory Caching (100% Exact Physics Preserved)**:
   - Partition the `170` unique `(region, year, climate, source)` worlds across `16` parallel workers (`world_index % args.workers`), instead of striding `17,549` rows independently across `8` workers.
   - Within each `(region, year, climate, source)` world, note that the `WOFOST81-SNOMIN` daily state evolution depends ONLY on `(region, year, climate, source)` and the executed 3-stage dose triple `(u1, u2, u3)` (it is independent of `policy`, `cap`, `price_multiplier`, `subsidy`, `mode`, `seed`, `track`):
     - Cache the stage-1/2/3 prefix states, `WeatherHistory` snapshots, `FiveSpecialistTeam._response_cache` (LRU across policies/contexts of that world), AND the completed native `WOFOST81-SNOMIN` trajectory outputs (`outcome`, `stock_diagnostics`, `mass_audit`, `events`, `native_weekly_steps`, `weather_source_id`) keyed by `(u1, u2, u3)` (or incremental stage prefix `(u1,)` / `(u1, u2)`).
     - Each unique executed `(region, year, climate, source, u1, u2, u3)` runs through the real `WOFOST81-SNOMIN` referee with 100% genuine daily `mass_audit` (`max |N| < 1e-10`, `max |C| < 1e-9` kg/ha), and every case still computes its own exact `trace` (`dose`, `tier`, `request_hash`, `applicable`, `OOD_score`, etc.), `joint`, and `partial_profit` against the exact `WOFOST81-SNOMIN` outcome (and verify 100% equality against `run_episode`!).
     - Record in `phase8c-campaign-receipt.json` both `total_cases`, `new_cases`, `reused_cases`, and `unique_native_trajectories_simulated` for full transparency.
4. **Complete Remaining Deliverables**:
   - Run `scripts/phase8c-analyze-results.py` covering `P1`, `NL Home-Turf` (`NASA` vs `WUR`), `P2` (`40 Former-Held-Out + 4 Public-Reused NL`, `LOYO` & `LORO`), `G3` orthogonal ablations (`Group A/B/C`), the full `180`-cell factorial stress surface, and the canonical Phase 5/6 `90`-group continuity subset + `TRAIN`-selected subsidy diagnostics.
   - Generate and validate `Fig. 1–5` (using Python + `validate_drawio.py` / `method_diagram.py check`, never `view_image`).
   - Update `reports/phase8/PHASE8_TOP_JOURNAL_REPORT.md`, `storyline-v2.0.md`, `_wiki/method.md`, `_wiki-methodology/_top/_questions/Q8.md` (via `plan` CLI / `plan check`), and the bilingual top-journal manuscript (`TeX` + compiled `PDF`).
   - Run full pytest suite, invariance checks, 100% daily N/C mass audit, preservation verification, and external AI council (`aid`), then merge cleanly to `NUE_PCSE-Gym` `main` and root `master`, remove worktrees/branches, update `OUTBOX.json`, and ring the doorbell.

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
  `agent-bus doorbell --leader team-4031428b3351 --worker team-832 --job-id lead-team-4031428b3351-team-832-20261116T050646-014887 --attempt-epoch 31 --status completed --summary "<one-line conclusion>"`
