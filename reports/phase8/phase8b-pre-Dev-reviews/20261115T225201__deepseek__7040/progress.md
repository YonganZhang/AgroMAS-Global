# Progress — Phase8B G1 pre-Dev review

JOB_ID: 20261115T225201__deepseek__7040
Started: 2026-11-15T14:52Z (22:52 local, UTC+8)
Snapshot for findings: 2026-11-15T15:05Z

## Phase 1 — Recon (complete, 14:52–14:54Z)
- Read authoritative brief `reports/phase8/continue-ef655327bd618e46.md`.
- Confirmed scope: read-only review of G1 before first Dev-label access; no code edits, no Dev/Held-Out physical labels; no G2/G3/P2 claim.
- Enumerated: six `scripts/phase8-*.py`, `pcse_gym/agromas_v8/{data,climate,models,scoring,agents,lightning_container,ood}.py`, two Phase8 test files, `reports/phase8/phase8b-preregistered-protocol.json`.

## Phase 2 — Source + protocol read (complete, 14:54–14:58Z)
- Read all listed modules and scripts, the preregistered protocol, the Phase5 `teacher-book-receipt-v2.json`, `season.py`, `scheduler.py`, `features.py`, `continuation.py`, `stock_diagnostics.py`, `weekly.py`, `regions.py`.
- Recorded reviewed-file SHA256 at 14:57Z (snapshot):
  - `phase8-evaluate-g1.py` a6aacdaf970237f1b6c17196004338cf87e6ed72f249e023463b287dce2f663a
  - `phase8-build-physical-books.py` 67e2f662219d7437a11e5bef03dcce0b5a5691a253318ed6d0a56164c80ee43a
  - `phase8-audit-physical-decoding.py` 437a339657fc9696fb7e956ef34a190ae23f58381f5ff659a79bb9aa6201ef24
  - `pcse_gym/agromas_v8/data.py` 9d2da3493ed81b18d7ec8b0d2da7d3fa5ca15d31fa25aaa69f51ee8e58c3cfcd
  - `pcse_gym/agromas_v8/scoring.py` c0ea092ab7a39bf9abb7019028819ef3c594e9950554a562e55ccb47cd6feec2
  - `pcse_gym/agromas_v8/climate.py` 8e9db1b53755af3b8bfc405999651136fae4afd310dc39307a60d8632fba3f0d
  - `pcse_gym/agromas_v8/agents.py` e206b0dc65bd80713a908eb48f99ed3e6db53e340ca9d475bc15e897c05f1af2
  - `tests/test_phase8_invariants.py` efbf9cb74e3bb1fefa255935fbb77dcb69411cdd6324e68746273172537b54ab
  - `tests/test_phase8_climate.py` bdb77ae743526d95b499963fd5e0fa553576a0b9fb4d22f51b7f3568dbaa3288
  - `phase8b-preregistered-protocol.json` b38b13c64ec2a8dba0018394bf6ef045773e98034b48c1c70f3aaf045a2d85f0
- Note: the worktree is live (other worker still writing docs/physical books); the review is pinned to the above hashes.

## Phase 3 — Evidence checks (complete, 14:58–15:05Z)
- Sample contract: 177,930 samples = 59,310 per stage; 225 TRAIN books, 1995–2009; 36 features / 3 targets; cache hashes match `phase8b-train-sample-contract.json`.
- Projection bounds: for all 177,930 samples, `Executed_N >= committed` and `Executed_N <= min(220, committed + nominal_remaining)`; 93 samples (=31 plans × 3 stages) are genuine skips, matching the brief's 31/59,310. `outcome[5]=3.5` and cumulative deposition 0 across 128 completed books; engine `native_fertilizer` vs `outcome[4]` max diff 2.8e-14.
- Models: 72 frozen MLP runs (2 tracks × 2 archs × 6 folds × 3 seeds, 80 epochs) + 12 ExtraTrees + 2 OOD; `phase8b-train-model-freeze.json` has `all_models_frozen:true`, `no_Dev_selection:true`.
- Tests: current Phase8 suite = 40 tests (30 climate perturbations + 10 invariants) and all 40 pass in isolation with `source scripts/env.sh`. Canonical receipt `phase8b-canonical-test-receipt.json` is exit 0 with 173 tests = 134 target + 39 Phase8, i.e. it predates the 40th `test_twin_interface...` (file mtime 22:56 vs receipt 22:55). `phase8b-final-v8-tests.log` records 39.
- G1 not run: no `phase8b-dev-access-claim.json`, no `data/phase8-g1-predictions`, no `phase8b-G1-verdict.json`.
- Physical campaign at snapshot: 160 progress records / 192 files, 0 Dev books, no `phase8b-physical-receipt.json`; campaign still writing.
- Preservation: root HEAD `bccb180fc3bbaf96ee25162e8b3e7a7b9142213f`; NUE HEAD `0354e3c6e53af2b5dc5fd32a40c53d2d16be840e`; pcse HEAD `d1fe6d29de828033b850ec51d994988d8d6d406f`; `git -C NUE_PCSE-Gym status` shows no `agromas`/`agromas_v6` diff and the crop cache is restored.

## Phase 4 — Findings (complete, 15:05Z)
- P0: Dev claim is created before receipt/Dev-book validation (`data.py:50–52` via `evaluate-g1.py:94`); a run now would burn the one-shot claim.
- P0: physical campaign incomplete and non-resumable (`build-physical-books.py:50,63,69–71,88`); no receipt, 0 Dev books.
- P1: seed/residual mismatch in K32 ensemble (`evaluate-g1.py:34` vs `:48`); ExecN seed spread ≈ residual spread on OOF.
- P1: conformal radius off by one order statistic (`scoring.py:32–33`; test asserts 18 for n=19 instead of 17).
- P1: BSS event ambiguity — code is one-sided `S_N<=cap` (TRAIN base 68–76%), while the brief's 8.53% legal rate exactly matches the joint `0<=S_N<=40 & 0.5<=NUE<=0.9` event (8.535%).
- P1: protocol line 50 "OOF analog pool excludes outer validation year" is not implemented; line 122 instead describes actual-weather residuals.
- P2: TRAIN-only physical decoder writes into a directory created only by the Dev evaluation (`phase8-audit-physical-decoding.py:40` vs `evaluate-g1.py:94`).
- P2: build `simulate` lacks the finite-outcome and physical-fertilizer assertions present in legacy `run_fixed_plan` (`build-physical-books.py:38–42` vs `season.py:159–161`).
- P2: canonical test receipt predates the 40th Phase8 test; rerun needed for a receipt covering the current suite.
- P3: OOD joblib hashes not verified (`evaluate-g1.py:86–96`); `validate_public_payload` rejects `np.bool_` and shallow 64-D check (`agents.py:12–16`); regret includes zero-decision/singleton groups (`scoring.py:35–42`); climatology mixes TRAIN climates (`evaluate-g1.py:71–75`).

## Phase 5 — Write result (complete, 15:07Z)
- Wrote `result.md` with the required completion marker and all required sections.
- Verified marker/section cardinality (each exactly once) and that the report directory is the only place written by this review.
- No project source edited; no Dev/Held-Out labels read; no Dev claim created.
- Review complete. The G1 implementation is **not ready** for the one-shot Dev access until the P0/P1 items in `result.md` are resolved.
