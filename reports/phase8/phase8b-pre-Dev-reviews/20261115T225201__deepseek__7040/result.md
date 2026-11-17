# Foreign Aid Result

JOB_ID: 20261115T225201__deepseek__7040
PROVIDER: deepseek
COMPLETION_STATUS: COMPLETE
ERROR_CLASS: NONE

## Summary
Read-only pre-Dev review of the Phase8B G1 implementation at the 2026-11-15T15:05Z worktree snapshot. The causal scenario plumbing, sample reachability, actual-vs-nominal `Executed_N` bounds, 72-model/12-tree freeze, and legacy preservation are sound (177,930 samples = 59,310/stage; every `Executed_N` lies in `[committed, min(220, committed+nominal)]`; 31/59,310 genuine skip plans; 40 Phase8 tests pass in isolation). The implementation is nevertheless **not ready for the one-shot Dev access**: the Dev claim is created before prerequisite validation, the physical campaign is incomplete/non-resumable (160/250 progress records, 0 Dev books, no receipt), and the gate code has a seed/residual pairing defect, a conformal-quantile off-by-one, an unresolved one-sided-vs-joint BSS event definition, and an unimplemented OOF analog-pool clause. No Dev/Held-Out outcome labels were opened and no project source was edited.

## Work Performed
- Read `reports/phase8/continue-ef655327bd618e46.md` and `reports/phase8/phase8b-preregistered-protocol.json`.
- Read and traced all six requested scripts: `phase8-build-physical-books.py`, `phase8-fit-world-model.py`, `phase8-fit-tree-reference.py`, `phase8-evaluate-g1.py`, `phase8-audit-daily-ledgers.py`, `phase8-audit-physical-decoding.py`.
- Read the new modules `pcse_gym/agromas_v8/{data,climate,models,scoring,agents,lightning_container,ood}.py`, both new Phase8 test files, and the relevant legacy code (`season.py`, `scheduler.py`, `weekly.py`, `features.py`, `continuation.py`, `stock_diagnostics.py`, `regions.py`).
- Audited the cached TRAIN array (177,930 × 36), projection bounds, skip counts, freeze metadata, OOD freeze, and the physical-book ledgers.
- Ran the current Phase8 test suite (40 tests) and inspected the canonical test receipt and both test logs.
- Checked the physical-campaign progress, the G1 artifacts (claim/output/verdict), and the root/NUE/pcse SHAs plus the legacy diff.
- Recorded the reviewed-file SHA256 snapshot at 14:57Z so findings can be pinned to this revision.
- Wrote/updated only the two mandatory report files: `progress.md`, `result.md`.

## Evidence
- **Sample contract:** `phase8b-train-sample-contract.json` = 177,930 samples, `x/y/meta` SHA256 match the cache; 59,310 stage-1/2/3 samples each. Years 1995–2009, 225 TRAIN books, 5 regions.
- **Projection bounds (all 177,930 TRAIN samples):** `Executed_N >= committed` always; `Executed_N <= min(220, committed+nominal_remaining)` always; `committed+nominal_remaining <= 220` always. 93 samples (31 plans × 3 stages; 31/59,310) are genuine skips, matching the brief. `outcome[5] == 3.5` and cumulative deposition is 0 across 128 completed books; engine `native_fertilizer` vs `outcome[4]` max abs diff = 2.8e-14.
- **Model freeze:** `phase8b-train-model-freeze.json` has 72 `model.pt` files, `all_models_frozen:true`, `no_Dev_selection:true`; `phase8b-ExtraTrees-freeze.json` has 12 files, `Dev_accessed:false`; `phase8b-ood-freeze.json` has 2 joblibs. 2 tracks × 2 architectures × (5 folds + final refit) × 3 seeds, fixed 80 epochs. Receipts show 13,155 parameters per architecture, RTX 5080, torch 2.10.0+cu128, Lightning 2.6.5, 80 epochs (6,960 final-refit / 5,600 fold global steps), `Dev_used:false`.
- **Tests:** command `source scripts/env.sh; cd NUE_PCSE-Gym; PYTHONDONTWRITEBYTECODE=1 python -m pytest -q tests/test_phase8_invariants.py tests/test_phase8_climate.py -p no:cacheprovider` → `40 passed in 10.14s`. `phase8b-canonical-test-receipt.json` is exit 0 with 173 tests = 134 target + 39 Phase8 and `crop_caches_restored:true`; it predates the 40th `test_twin_interface...` (test mtime 22:56, receipt 22:55). `phase8b-final-v8-tests.log` records 39 passed.
- **G1 not run:** no `reports/phase8/phase8b-dev-access-claim.json`, no `data/phase8-g1-predictions`, no `reports/phase8/phase8b-G1-verdict.json`.
- **Physical campaign at snapshot:** 160 records in `phase8b-physical-progress.jsonl`, 192 files under `data/phase8-physical-books`, **0 Dev books**, no `phase8b-physical-receipt.json`; the campaign was still writing. The 32 files beyond the 160 progress records are in-progress/partial.
- **Preservation:** root HEAD `bccb180fc3bbaf96ee25162e8b3e7a7b9142213f`; NUE HEAD `0354e3c6e53af2b5dc5fd32a40c53d2d16be840e`; pcse HEAD `d1fe6d29de828033b850ec51d994988d8d6d406f`. `git -C NUE_PCSE-Gym status` shows no `pcse_gym/agromas` or `pcse_gym/agromas_v6` diff; only the untracked new v8/tests. Crop cache restored.
- **BSS base rates from the cached TRAIN labels (`S_N = ExecN + 3.5 - GrainN`):** one-sided `S_N <= cap`: 67.94%, 71.21%, 72.76%, 75.71% for caps 25/35/40/50; China is 0% for all caps. Two-sided `0 <= S_N <= cap`: 9.18%, 12.45%, 13.99%, 16.95%. Joint `0 <= S_N <= 40 & 0.50 <= NUE <= 0.90` on the legal candidate set: **8.535%**, exactly the brief's `~8.53% legal` figure (the brief's `~6.82% overall` is the all-plan counterpart).
- **Seed/residual spread (fold-0 OOF, 3 seeds):** `std(seed prediction - seed mean) / std(mean OOF residual)` per target:
  - Full-Telemetry mlp: Yield 0.231, GrainN 0.228, ExecN 0.970.
  - Full-Telemetry residual-mlp: 0.244, 0.244, 1.269.
  - Sensorless mlp: 0.227, 0.215, 1.018.
  - Sensorless residual-mlp: 0.303, 0.288, 1.250.
- **Conformal example:** `conformal_radius(np.arange(19.))` returns 18 (the maximum); the finite-sample 90% split-conformal radius is the 18th smallest = 17.
- **Physical books:** the 128 completed book records present at snapshot (no Dev) report per-book max N/C residuals ~1e-11/~1e-10, inside the 1e-10/1e-9 bounds; spot checks of the daily ledger, nonfert/deposition, and engine-vs-outcome fertilizer were consistent; the immutable-outcome replay difference is 0.0. The separate full `phase8-audit-daily-ledgers.py` pass had not been run at snapshot.

## Files Changed Or Reviewed
Changed: only the mandatory foreign-aid report files:
- `_reports/_foreign_aid/20261115T225201__deepseek__7040/progress.md`
- `_reports/_foreign_aid/20261115T225201__deepseek__7040/result.md`

Reviewed (no edits):
- `scripts/phase8-build-physical-books.py`
- `scripts/phase8-fit-world-model.py`
- `scripts/phase8-fit-tree-reference.py`
- `scripts/phase8-evaluate-g1.py`
- `scripts/phase8-audit-daily-ledgers.py`
- `scripts/phase8-audit-physical-decoding.py`
- `scripts/phase8-freeze-ood.py`, `scripts/phase8-verify-tests.py`, `scripts/phase8-train-cv-diagnostics.py`, `scripts/phase8-sync-q8-acceptance.py`
- `NUE_PCSE-Gym/pcse_gym/agromas_v8/{data,climate,models,scoring,agents,lightning_container,ood}.py`
- `NUE_PCSE-Gym/tests/test_phase8_climate.py`, `NUE_PCSE-Gym/tests/test_phase8_invariants.py`
- `reports/phase8/phase8b-preregistered-protocol.json`
- `reports/phase8/phase8b-train-sample-contract.json`, `phase8b-train-model-freeze.json`, `phase8b-ExtraTrees-freeze.json`, `phase8b-ood-freeze.json`, `phase8b-canonical-test-receipt.json`, `phase8b-canonical-pytest.log`, `phase8b-canonical-missing-fixture-pytest.log`, `phase8b-final-v8-tests.log`, `phase8b-physical-progress.jsonl`, `phase8b-physical-campaign-claim.json`, `phase8b-pre-Dev-review-packet.md`
- Legacy context: `NUE_PCSE-Gym/pcse_gym/agromas/{season,scheduler,weekly,features,continuation,stock_diagnostics,regions}.py`

## Errors Or Blockers
No review-execution errors. The following are implementation blockers/findings found by the review.

**P0 — Dev one-shot claim is created before prerequisite validation.** `NUE_PCSE-Gym/pcse_gym/agromas_v8/data.py:49-52` opens `reports/phase8/phase8b-dev-access-claim.json` with `'x'` *before* it reads/validates `phase8b-physical-receipt.json` and the 25 Dev books; `scripts/phase8-evaluate-g1.py:94` also calls `O.mkdir(exist_ok=False)` only after `load_dev_once`. At the current snapshot the receipt does not exist, so running the script now would create the claim and then raise `FileNotFoundError`, permanently burning the one-shot Dev access. Minimal correction: verify the freeze docs, the physical receipt `status`, the expected 25 Dev books (5 regions × 5 years) and 225 Train books, and all file hashes; create the output dir; then atomically create the claim immediately before decoding the Dev labels. Add the 25/225 counts and `receipt['status']` assertions.

**P0 — Physical campaign is incomplete and non-resumable.** `scripts/phase8-build-physical-books.py:50,63,69-71,88` uses `path.open('xb')`, `chmod(0o444)`, `claim.open('x')`, `O.mkdir(exist_ok=False)`, and `progress.open('x')`. At snapshot: 160 progress records / 192 files, 0 Dev books, no receipt. If the campaign dies, the exclusive dirs/claims block a clean rerun, and the 32 in-progress files are not covered by the receipt. The 225 Train diagnostic replays must all complete and the 25 Dev books must be generated before G1. Minimal correction: add a resume path keyed on the progress records/hashes, remove/rewrite partial files, and write the final receipt only after all 250 jobs; do not start the Dev claim until the receipt exists and is complete. The daily-ledger audit (`scripts/phase8-audit-daily-ledgers.py:26`) has the same non-resumable `open('x')` progress log and should be resumable or given a fresh log name.

**P1 — K32 ensemble pairs single-seed predictions with the mean-of-seeds residual.** `scripts/phase8-evaluate-g1.py:34` computes OOF residuals against `np.mean([seed predictions])`, but `:48` uses `predictor.predict(candidate, k % 3)` (one seed) plus that mean residual. On TRAIN OOF, the ExecN seed spread is ≈1.0–1.27× the residual std (see Evidence), so the ensemble is not the registered "cross-model seed mixing"; it inflates the S_N spread and biases the coverage/BSS gate. Minimal correction: save per-seed OOF residuals and pair `seed = k % 3` with its own residual, or use the seed-mean prediction for every K member and vary only residuals. No Dev outcomes are needed.

**P1 — Conformal radius is off by one order statistic.** `NUE_PCSE-Gym/pcse_gym/agromas_v8/scoring.py:29-33` computes `q = ceil((n+1)(1-alpha))/n` and calls `np.quantile(scores, q, method='higher')`, which returns the `(k+1)`-th smallest, not the `k`-th. For `n=19` it returns 18 (max) instead of 17; `tests/test_phase8_invariants.py:40` enshrines the over-conservative value. This biases coverage upward and can violate the `<=0.95` gate. Minimal correction: `k = ceil((n+1)(1-alpha)); radius = sorted(scores)[k-1]` (or `np.quantile(scores, (k-1)/(n-1), method='lower')`) and update the test.

**P1 — BSS event definition is ambiguous and does not match the brief's cited base rate.** `scripts/phase8-evaluate-g1.py:70` implements one-sided `S_N <= cap`. Its TRAIN base rate is 67.9–75.7%, not the brief's `~6.82% overall / ~8.53% legal`. The `~8.53%` figure matches, to five decimals, the joint `0 <= S_N <= 40 & 0.50 <= NUE <= 0.90` event (8.535%). If the gate is meant to test the joint compliant plan (the eco + economic corridor), the code tests a much easier, different event; if one-sided is intended, the brief's low-base-rate warning is wrong. Minimal correction: freeze the exact event in the protocol before Dev. If the joint event is intended, use `truth = (S_N>=0)&(S_N<=cap)` (and optionally the NUE corridor) and `pred = ((members[...,2]>=0)&(members[...,2]<=cap)).mean(1)`; recompute the TRAIN base rate. No Dev outcomes are needed.

**P1 — Registered "OOF analog pool excludes outer validation year" is unimplemented.** `reports/phase8/phase8b-preregistered-protocol.json:50` says the OOF analog pool excludes the outer validation year, but `NUE_PCSE-Gym/pcse_gym/agromas_v8/data.py:29` uses the actual TRAIN future-weather descriptor for every training sample, and `scripts/phase8-evaluate-g1.py:34` builds residuals from those actual-weather predictions; no OOF analog pool is constructed. Protocol line 122 instead says "Conditional actual-TRAIN-weather residuals only", so the protocol contradicts itself. This is not a Dev leak, but it is a contract mismatch. Minimal correction: either implement the fold-year-excluded OOF analog pool or amend line 50 before Dev to state that the analog pool is Dev-only and OOF residuals are actual-weather conditional.

**P2 — TRAIN-only physical decoder cannot run before the Dev evaluation.** `scripts/phase8-audit-physical-decoding.py:40` writes `data/phase8-g1-predictions/...npz`, but that directory is created only by `scripts/phase8-evaluate-g1.py:94` after the Dev claim. Running the TRAIN-only audit first crashes with `FileNotFoundError`; running it after consumes the Dev access. Minimal correction: `O.mkdir(parents=True, exist_ok=True)` in the decoder or write to a separate TRAIN-only directory.

**P2 — Physical build lacks legacy finite-outcome and fertilizer-consistency assertions.** `scripts/phase8-build-physical-books.py:38-42` does not assert `np.isfinite(outcome).all()` or `engine fertilizer == scheduler.cumulative`, while the legacy `NUE_PCSE-Gym/pcse_gym/agromas/season.py:159-161` does. The 128 completed books are consistent (max diff 2.8e-14), but the new build should fail closed. Minimal correction: add both assertions in `simulate`.

**P2 — Canonical test receipt predates the current 40th Phase8 test.** `phase8b-canonical-test-receipt.json` is exit 0 with 173 = 134 target + 39 Phase8 (22:55); `test_twin_interface...` was added at 22:56, and the current suite is 40 (30 climate + 10 invariants). The 40 pass in isolation, but no canonical receipt covers the 40th. Minimal correction: rerun `scripts/phase8-verify-tests.py` and regenerate the receipt; the brief's "38 expected" is stale (actual 40).

**P3 — OOD freeze hashes are not verified.** `scripts/phase8-evaluate-g1.py:86-96` includes `phase8b-ood-freeze.json` in the digest and loads the two OOD joblibs, but never checks their `sha256` against the freeze (unlike train/ExtraTrees at `:88-89`). Minimal correction: verify `docs[2]['files']` hashes and assert 2 files.

**P3 — Agent payload validator is too strict/shallow.** `NUE_PCSE-Gym/pcse_gym/agromas_v8/agents.py:16` rejects `np.bool_`/`np.generic`, so an OOD `applicable` returned as a numpy bool will fail; `:12-13` only catches a flat 64-element sequence, not a 64×1 array. Minimal correction: accept `np.bool_`/`np.generic` and check the numpy shape. This is a G2-interface issue, not a G1 numerical blocker.

**P3 — Regret/climatology reporting is diluted.** `NUE_PCSE-Gym/pcse_gym/agromas_v8/scoring.py:35-42` includes singleton groups and `scripts/phase8-evaluate-g1.py:77` includes zero-decision (`nominal_remaining == 0`) groups in the mean regret; the TRAIN prefixes have 180 singleton groups / 10,980 (1.6%) and 10,980 zero-remaining samples. `scripts/phase8-evaluate-g1.py:71-75` also mixes all three TRAIN climates into the "region/stage climatology" although Dev is Historical-only. Minimal correction: report the number of non-degenerate groups and the regret on them (full-population number secondary), and compute/report the climatology on Historical TRAIN only or report both.

## Next Steps
1. **Do not run `scripts/phase8-evaluate-g1.py` yet.** The physical receipt does not exist and 0 Dev books have been generated; a run now would burn the one-shot Dev claim.
2. Finish/verify the physical campaign: 225 Train + 25 Dev books, no failed rows, `phase8b-physical-receipt.json` present; add the resume path or document a safe manual recovery before restarting a crashed campaign.
3. Fix the Dev-claim ordering and add the preflight assertions (25 Dev / 225 Train, receipt status, freeze/OOD hashes, output dir) in `data.py` / `evaluate-g1.py`.
4. Fix the seed/residual pairing, the conformal quantile, freeze the BSS event definition (one-sided vs joint), and resolve the OOF analog-pool protocol clause. These are pre-Dev decisions and must not be chosen from Dev outcomes.
5. Apply the P2/P3 fixes (physical-decoder output dir, build finite/fertilizer assertions, canonical suite rerun, OOD hash verification, agent payload types).
6. Rerun the canonical active+Phase8 suite (currently 134 target + 40 Phase8 = 174; the passing receipt covers 173) and regenerate the source/freeze receipts, then run the single locked Dev pass once. If neither architecture passes both parity tracks, halt G2/G3/P2 as pre-registered.
