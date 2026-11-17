# Foreign Aid Result

JOB_ID: 20261116T175852__deepseek__3033536
PROVIDER: deepseek
COMPLETION_STATUS: COMPLETE
ERROR_CLASS: NONE

## Review Verdict

**FAIL** — the frozen data hashes and artifact hashes are sound, and the earlier Fig. 4 text collision (18:12) and Fig. 3d equal-region/Holm omission (18:14) were fixed during review, but the redesign is still not a figure-only visual change: Fig. 3c and Fig. 5 change the underlying quantities while the frozen manuscript captions still describe the old panels.

## Summary

Independent read-only premerge review completed. The eight entries in `phase8d-redesign-source-baseline.json` match the current frozen data sources byte-for-byte; all current figure artifact hashes match `phase8d-redesign-verification.json`; the three raw Image2 candidates match the external generated images, and the `fig1-assets` crops match `asset-manifest.json`. The gate nevertheless fails. Fig. 3c now plots Full64 predictive-row/world-equal acceptance, while both frozen manuscript captions still say panel c pools closed-loop decision counts. Fig. 5 has been replaced by execution/decoding panels, while its frozen caption still describes the old compact-model/interface panels. The earlier Fig. 4 colorbar/x-axis collision was fixed at 18:12 (the latest PDF text-span check finds zero overlaps), and Fig. 3d's equal-region label and `Holm p` annotation were restored at 18:14. Fig. 2-p1's frozen caption remains generic even though its panel-d marker/fill/bubble key was added during review; Fig. 2-g1's PDF contains duplicated value labels. Metadata and audit gaps remain, including a caption source-of-truth conflict with `phase8d-build-manuscripts.py`, stale Fig. 1 provenance, a 198-vs-112 shape-count mismatch, and a baseline/verifier that do not cover the manuscript or NUE_PCSE-Gym/pcse.

## Findings

### F1 — BLOCKER: Fig. 3c changed the estimand; the frozen caption says the opposite

- Evidence: `scripts/phase8d-plot-p2.py:13-16` reads `phase8d-P2-predictive-cohort-strata.csv` and plots `prior_acceptance_rows` / `prior_acceptance_world_equal`, labelled `Predictive rows` / `World equal`. The old `scripts/phase8d-final-figures.py` at `HEAD` (lines 40-45) computed `pooled['prior_accepted']/pooled['prior_decisions']` and labelled `Accepted closed-loop decisions (%)` / `Former: closed-loop prior acceptance`.
- Frozen captions: `manuscript/phase8/en.tex:102` says “Panel c pools closed-loop decision counts within the Former cohort, distinct from predictive-row acceptance”; `manuscript/phase8/zh.tex:102` says the same in Chinese. The newly written `reports/phase8/figures/phase8d-captions.json` caption 3 says the new predictive-row quantity, but that file is not the published manuscript caption.
- Impact: a reader of the manuscript is told the reverse of what panel c plots. This is a changed underlying claim, not a visual restyling, and it violates “no prose rewrites, no changed underlying claims”.
- Reproduction: inspect `reports/phase8/figures/fig3-p2-transfer.png` panel c (bars at 88.36/77.50 and 72.02/60.00) and compare with `en.tex:102`; inspect the old panel-c code with `git show HEAD:scripts/phase8d-final-figures.py | nl -ba | sed -n '40,45p'`.

### F2 — BLOCKER: Fig. 5 panels and frozen caption describe different figures

- Evidence: the new `scripts/phase8d-plot-closure.py:5-24` produces (a) native-vs-cache execution accounting, (b) daily N/C closure, (c) the 30 required decoding cells, and (d) the 50 latent-vs-raw readout scatter. The old `HEAD` `phase8d-final-figures.py:71-74` had (a) compact backbone, (b) runtime interface, (c) configuration-day records, and (d) execution denominators.
- Frozen captions: `manuscript/phase8/en.tex:104` and `zh.tex:104` still say “Frozen compact model and interface, case-configuration daily mass closure, actual native simulation count and verified trajectory replay count. Repeated configuration-day records are not independent seasons.” They never mention the decoding panels now shown as c/d, and the “compact model and interface” panels no longer exist.
- Impact: the caption describes a figure that is no longer present; the new association-only decoding panels are not disclosed in the manuscript caption. This is a second changed underlying claim.
- Reproduction: inspect `reports/phase8/figures/fig5-deployment-closure.png` panels a-d and compare with `en.tex:104`; inspect the old `HEAD` lines 71-74.

### F3 — BLOCKER: caption source-of-truth conflict; a manuscript rebuild restores the wrong captions

- Evidence: `reports/phase8/figures/phase8d-captions.json` was updated at 18:08 with predictive-row Fig. 3c and decoding Fig. 5 captions, but `scripts/phase8d-build-manuscripts.py:16-17` still contains the old `caps_en`/`caps_zh` strings, including “Panel c pools closed-loop decision counts” and “Frozen compact model and interface”. The manuscript `.tex` files were generated from that build script and remain at the old text (`manuscript/phase8/en.tex:102,104`; `zh.tex:102,104`).
- Impact: the new metadata and the manuscript/build source disagree. Any future manuscript rebuild overwrites the corrected figure captions with the old, wrong text. The redesign therefore cannot be accepted as a durable figure-only change.
- Reproduction: compare `grep -n 'closed-loop decision counts\\|Frozen compact model' scripts/phase8d-build-manuscripts.py` with the current `phase8d-captions.json`; the two disagree.

### F4 — RESOLVED during review (was a blocker): Fig. 4 colorbar/x-axis text collision

- Earlier evidence: at 18:03 and 18:11, `scripts/phase8d-plot-stress.py:31-32` placed the colorbars in the narrow grid rows between heatmap rows; the `Surplus cap (kg N ha^-1)` labels collided with `Soft-Coupled − PPO (pp)` (58% box overlap) and `Joint compliance (%)` (54%), and colorbar ticks crowded the group labels.
- Current status: the 18:12 revision (`scripts/phase8d-plot-stress.py:31-32`, `fig4-factorial-stress.pdf` at 18:12:41) removes the `set_label_position('top')` placement and separates the labels; the PyMuPDF span-overlap check on the latest PDF now returns zero pairs at >20% overlap, and the PNG is legible. The earlier finding is withdrawn for the current revision.
- Residual gap: `scripts/phase8d-plot-style.py:25-38` still only checks axes `tightbbox` values, not pairwise text overlap, so the automated verifier would not catch a future regression; this is covered under F9.
- Reproduction: re-run the span-overlap check on the current `fig4-factorial-stress.pdf`; it returns zero pairs.

### F5 — RESOLVED during review (was HIGH): Fig. 3d equal-region/Holm disclosure

- Earlier evidence: the 17:49–18:11 `scripts/phase8d-plot-p2.py:18-21` plotted the `GLOBAL_EQUAL5` contrast with plain `LOYO` / `LORO` y-ticks and no Holm text. The old `HEAD` code (`phase8d-final-figures.py:50-51`) had `LOYO / equal 5-region` and `Holm p=...`.
- Current status: the 18:14 revision (`scripts/phase8d-plot-p2.py:20-21`, `fig3-p2-transfer.png` at 18:14:56) adds `Holm p={...}` to each row and changes the x-label to `Full64 − Static3, equal-region compliance (pp)`; the latest PNG shows `Holm p=1` for both strata. The contract’s equal-region-vs-sign-test disclosure is restored; the earlier finding is withdrawn for the current revision.
- Residual: the y-tick itself still reads `LOYO`/`LORO`, with the equal-region wording in the x-label; this is acceptable but could be made more explicit.
- Reproduction: inspect the current `fig3-p2-transfer.png` panel d; the `Holm p=1` text and `equal-region` x-label are visible.

### F6 — MINOR (partly resolved during review): Fig. 2-p1 caption does not describe the now-present panel-d key

- Resolved at 18:11: `scripts/phase8d-plot-p1.py:15-16` now uses `top,bottom=val(q[0]),val(q[1])` instead of the previous hardcoded `25.06`/`4`, and panel d now has an in-panel circle/triangle, open/filled, and bubble-size key. The earlier hardcoded-value finding is therefore withdrawn for the current revision.
- Residual: the frozen manuscript caption (`en.tex:101`, `zh.tex:101`) is generic and does not explain the panel-d encodings or the `S_N 0`/`S_N 20` bubble-size key; only the newly written `phase8d-captions.json` caption 1 does. Panel c still drops the farm-year counts from its x labels.
- Impact: a reader of the frozen caption cannot fully decode panel d, although the figure is now self-keyed. This is not a gate blocker on its own.
- Reproduction: inspect `scripts/phase8d-plot-p1.py:15-16,20-30` and `fig2-p1-regimes.png` panel d against `en.tex:101`.

### F7 — MEDIUM: Fig. 2-g1 duplicated value text and stale supplement caption

- Evidence: `scripts/phase8d-plot-g1.py:25-26` contains two identical `ci.text(...)` loops, so the PDF contains each value twice. PyMuPDF finds two `62.50` spans at the identical box (319.9,537.6,335.7,545.4) and two `69.53` spans at (330.8,566.8,346.5,574.6).
- `manuscript/phase8/supplement.tex:6` still captions Fig. 2g1 as “Frozen forecast skill, uncertainty coverage and physical-variable decoding”, but the new Fig. 2g1 panels are the five-testbed map, Brier skill, cross-year coverage and ranking regret; no physical-variable decoding panel remains (that content is now in Fig. 5). The updated `phase8d-captions.json` `supplement_captions['fig2-g1']` describes the new panels, but the frozen supplement caption does not.
- Impact: duplicated selectable text in the PDF and a supplement caption that describes a panel that no longer exists.
- Reproduction: count the `62.50`/`69.53` spans in `fig2-g1.pdf`; compare `supplement.tex:6` with the new figure.

### F8 — MEDIUM: Fig. 1 carries an unverified static-soil label and stale provenance metadata

- Evidence: `scripts/phase8d-build-fig1-hybrid.py:46` adds “Static3: field capacity, wilting point and conductivity”. No source in this worktree defines those three Static3 properties: the frozen manuscript only says “Static3 physical-soil Ridge correction” (`manuscript/phase8/en.md:37`), and `reports/phase8/figures/fig1-candidates/scientific-facts.md` lists no feature names. NUE_PCSE-Gym/pcse are absent from this worktree, so the label cannot be verified here.
- `reports/phase8/figures/fig1-assets/README.md` still says “The PDF contains the editable figure followed by its raw reference. Use page1 as the figure”; the current `fig1-architecture.pdf` is one page (18:08). `phase8d-fig1-edit-receipt.json` still records “source: Phase8C archived native PPTX” and `artwork_unchanged: true`, whereas the current Fig. 1 is a hybrid reconstruction from Image2. `asset-manifest.json` reports `native_shape_count: 198`, while `phase8d-redesign-verification.json` reports `native_fig1_shapes: 112` (different definitions, unreconciled in the metadata).
- Impact: a new scientific detail is asserted without a verifiable frozen source; the provenance documents do not describe the delivered hybrid.
- Reproduction: inspect builder line 46, manuscript line 37, README, receipt, manifest and verification JSON; check the current PDF page count.

### F9 — MEDIUM: the audit and baseline do not cover the full gate

- Evidence: `scripts/phase8d-verify-figure-redesign.py:6-35` verifies source/artifact hashes, PDF fonts/colours/bold spans, absence of `set_title` calls, PPTX text/action counts/shapes/fonts, and candidate presence, but it does not verify figure captions against the manuscript, duplicate text, pairwise text overlap, `phase8d-build-manuscripts.py` captions, or manuscript/pcse byte identity.
- `reports/phase8/figures/phase8d-redesign-source-baseline.json` covers only eight data files; it does not cover `manuscript/phase8/{en,zh}.{md,tex,pdf}`, `supplement.tex`, NUE_PCSE-Gym or pcse. The plotting style and the map asset are machine-specific external paths: `scripts/phase8d-plot-style.py:10` (`/mnt/data/yongan-admin-2/.ai-shared/skills/share-sci-plot/...`) and lines 27-28 (`figure_standards.py`); `scripts/phase8d-plot-g1.py:8-11` uses a local Natural Earth shapefile; `scripts/phase8d-verify-figure-redesign.py:33` reads candidates from `/mnt/data/yongan-admin-2/.codex-homes/...`. `.figure-venv` is untracked.
- Impact: `status: PASS` in `phase8d-redesign-verification.json` is narrower than the gate contract; a clean checkout cannot reproduce the figures, and the manuscript/pcse identity is not certified by the provided baseline.
- Reproduction: inspect the verifier and baseline; run the plot scripts in a clean environment without the external style/shapefile/`.codex-homes` paths.

### F10 — Minor / coverage observations

- `manuscript/phase8/supplement.tex:7` still captions Fig. s2 as “Model, solver, specialist-removal and experimental-subsidy diagnostics. Unequal cohort sizes are labelled.” The current Fig. s2 does not label cohort sizes, and the frozen caption does not disclose that DVS-N2/LegacyV6 are Full-telemetry comparators; the updated `phase8d-captions.json` supplement caption does. Panel c also has no colour legend of its own.
- `fig2-p1-regimes` panel c x-axis labels are now `AU US NL FR CN` without the farm-year counts (`AU11 US12 NL5 FR12 CN12`); the updated caption metadata carries the counts, the frozen caption does not. CN has zero bars because its joint value is 0.0 for all three modes; this is correct, not a missing cell.
- `scripts/phase8d-plot-style.py:12` defines `GREY='#C8D1D7'` and `:24` uses grid `#E8ECEF`; neither is in the recorded `PALETTE_SCI_ROSE_SLATE_10`. If “fixed palette” is strict, Fig. 3/Fig. s2 contain an off-palette neutral.
- The rendered Fig. 4 bottom-left panel g y-axis label sits at the page edge (PDF text box x0≈2.1 pt); it is present but very tight. This is secondary to the colorbar collision.

## Work Performed

- Read the complete current diff and the `HEAD` versions of the changed figure scripts; inspected all new `phase8d-plot-*.py`, `phase8d-build-fig1-hybrid.py`, `phase8d-verify-figure-redesign.py`, and `phase8d-update-figure-metadata.py`.
- Independently hashed the eight baseline sources and all audited artifacts; verified candidate and asset provenance.
- Read the seven actual PNGs with native image inspection; inspected PDF text spans and boxes with PyMuPDF; inspected PPTX text, shape/picture counts, action counts, and `a1/a2/a3` occurrences; inspected `asset-manifest.json`, `pptx-validation.json`, render audits, captions, source-bounds, and verification JSON.
- Re-read the 18:11–18:14 revisions of Fig. 2p1, Fig. 3, Fig. 4, Fig. 5, the captions, and the verification; confirmed that the Fig. 2p1 hardcoded endpoints/panel-d key, the Fig. 4 colorbar collision, and the Fig. 3d equal-region/Holm omission were fixed, while the Fig. 3c/Fig. 5 caption conflicts persist.
- Compared the new figures with the frozen manuscript captions and the caption build source.
- Checked `git status` for manuscript changes and searched for NUE_PCSE-Gym/pcse in the worktree.
- No experiments, no plotting-script execution, no project source writes, no delegation. The only writes are this report directory's `progress.md`/`result.md` and tool-generated image previews under that report directory.

## Evidence

- Baseline hashes: 8/8 entries in `reports/phase8/figures/phase8d-redesign-source-baseline.json` match the current files (including `phase8d-core-statistics.json`, `phase8d-G1-verdict.json`, `phase8d-full-TRAIN-physical-decoding.json`, `phase8d-180cell-stress-surface.csv`, `phase8d-closeout-receipt.json`, `phase8d-primary-verification.json`, `phase8d-P2-predictive-cohort-strata.csv`, `manuscript/phase8/all-summary-groups.csv`).
- Artifact hashes: all entries in `reports/phase8/figures/phase8d-redesign-verification.json` matched the current PNG/PDF/SVG/PPTX files at the 2026-11-16T18:12 +0800 snapshot (the verification was regenerated at 18:11:34 after the last figure update).
- Provenance: `candidate-b-v2-{1,2,3}.png` each match one external Image2 output; `candidate-b-v2-best.png` matches `asset-manifest.json.reference_sha256`; all nine `fig1-assets` crops match their manifest hashes.
- Fig. 4 collision (resolved): the 18:11 PDF had two >20% text-span pairs (`Surplus cap` vs `Soft-Coupled − PPO (pp)` at 58% and vs `Joint compliance (%)` at 54%); the 18:12 revision reduces this to zero pairs, and the PNG is legible. The earlier blocker is therefore withdrawn for the current revision, but the verifier still lacks a pairwise text-overlap check (F9).
- Fig. 3c: PNG panel c labels `Predictive rows` and `World equal`; CSV values 88.36/77.50 and 72.02/60.00; frozen caption says closed-loop decision counts.
- Fig. 3d (resolved): the latest PNG/PDF at 18:14:56 shows `Holm p=1` for LOYO and LORO and the x-label `Full64 − Static3, equal-region compliance (pp)`; the earlier equal-region/Holm finding is withdrawn.
- Fig. 5: PNG panels a-d are execution, mass closure, required30 decoding, and all50 readout; frozen caption describes compact model/interface and mass/execution only.
- Fig. 2g1: duplicate `62.50` and `69.53` text spans in the PDF at identical boxes, from duplicate loops at `phase8d-plot-g1.py:25-26`.
- Fig. 1: `fig1-architecture.pdf` is currently 1 page; `fig1-architecture.pptx` has 112 `p:sp` and 9 pictures; action counts are a1=1, a2=2, a3=4; `referee_outgoing_edges: 0`; four couplings are labelled; `pptx-validation.json` reports zero issues.
- Frozen paths: `git status --short manuscript` is empty; no `NUE_PCSE-Gym` or `pcse` directory exists in this worktree.
- Snapshot caveat: the worktree was updated concurrently between 17:59 and 18:15 (Fig. 2g1, Fig. s2, Fig. 2p1, Fig. 3, Fig. 4, Fig. 5, captions, source-bounds, verification). The findings above are against the latest 18:15 snapshot; re-check hashes if the worktree changes again.

## Files Changed Or Reviewed

Reviewed (not modified):

- Scripts: `scripts/phase8d-final-figures.py`, `scripts/phase8d-supplement-figures.py`, `scripts/phase8d-plot-style.py`, `scripts/phase8d-plot-g1.py`, `scripts/phase8d-plot-p1.py`, `scripts/phase8d-plot-p2.py`, `scripts/phase8d-plot-stress.py`, `scripts/phase8d-plot-closure.py`, `scripts/phase8d-plot-gaps.py`, `scripts/phase8d-build-fig1-hybrid.py`, `scripts/phase8d-verify-figure-redesign.py`, `scripts/phase8d-update-figure-metadata.py`, `scripts/phase8d-build-manuscripts.py`.
- Figures: `reports/phase8/figures/fig1-architecture.{pptx,pdf,png,svg}`, `fig2-g1.{pdf,png,svg}`, `fig2-p1-regimes.{pdf,png,svg}`, `figs2-g3-subsidy.{pdf,png,svg}`, `fig3-p2-transfer.{pdf,png,svg}`, `fig4-factorial-stress.{pdf,png,svg}`, `fig5-deployment-closure.{pdf,png,svg}`, all `fig1-assets/*`, `fig1-candidates/candidate-b-v2-*`.
- Metadata: `phase8d-redesign-source-baseline.json`, `phase8d-redesign-verification.json`, `phase8d-captions.json`, `phase8d-figure-source-and-bounds.json`, all six `*-render-audit.json`, `fig1-assets/asset-manifest.json`, `fig1-assets/pptx-validation.json`, `fig1-assets/README.md`, `phase8d-fig1-edit-receipt.json`, `phase8d-fig2-g1-source.json`, `phase8d-redesign-gate-packet.md`, `phase8d-visual-review-packet.md`.
- Manuscript: `manuscript/phase8/en.tex` (captions 102, 104), `zh.tex` (102, 104), `supplement.tex` (6-7), `en.md`/`zh.md` as needed for claims.
- Frozen data: the eight baseline sources listed above.

Changed:

- `_reports/_foreign_aid/20261116T175852__deepseek__3033536/progress.md`
- `_reports/_foreign_aid/20261116T175852__deepseek__3033536/result.md`

No project source, figure, manuscript, or frozen data file was modified by this review.

## Errors Or Blockers

- Review verdict **FAIL**. Blockers: F1 (Fig. 3c estimand/caption), F2 (Fig. 5 panels/caption), F3 (caption source-of-truth conflict). Medium: F7 (Fig. 2g1 duplicate text/stale supplement caption), F8 (Fig. 1 unverified Static3 label/stale provenance), F9 (audit/baseline coverage and external dependencies). Minor: F6 (Fig. 2p1 caption; its hardcoded endpoints and missing key were fixed at 18:11) and F10. Resolved during review: F4 (Fig. 4 text collision fixed at 18:12; latest PDF span-overlap check is zero) and F5 (Fig. 3d equal-region/Holm disclosure restored at 18:14).
- No quota, auth, network, timeout, tooling, or model-refusal errors occurred.
- Coverage limitations: NUE_PCSE-Gym and pcse are not present in this worktree, so their byte identity and the actual Static3 feature names could not be independently verified. The baseline manifest does not cover the manuscript `.md/.tex/.pdf` files, NUE_PCSE-Gym or pcse. No plotting script was executed; the review uses the delivered artifacts and static code. The companion visual review is separate; this gate read the seven PNGs but did not perform a full independent Gemini visual review.
- The worktree was live-updated during the review; the findings apply to the 2026-11-16T18:12 +0800 snapshot. Fig. 2p1's hardcoded endpoints and missing panel-d key were fixed at 18:11 and are no longer blockers; the remaining findings persist. If the author updates the figures/captions again, the audit hashes and visual checks should be rerun.

## Next Steps

- Resolve the blockers before merge: either restore Fig. 3c to the frozen caption’s closed-loop decision-count quantity and restore Fig. 5 to the frozen caption’s panels, or obtain explicit authorization to rewrite the manuscript/build-script captions. Do not leave `phase8d-captions.json` and `scripts/phase8d-build-manuscripts.py:16-17`/`manuscript/phase8/en.tex:102,104` in conflict.
- Retain the fixed Fig. 4 layout (the 18:12 revision has zero text-span overlaps) and add a pairwise text-overlap assertion to the figure verifier so a future regression is caught automatically.
- Retain the 18:14 Fig. 3d `Holm p=...` and `equal-region compliance` annotation; optionally put `equal-region` in the y-ticks as well.
- Add the Fig. 2p1 panel-d key and panel-c farm-year counts (or equivalent wording) to the frozen caption, or restore the old caption-compatible panel; the hardcoded endpoints were already fixed at 18:11.
- Remove the duplicate `ci.text` loop in `phase8d-plot-g1.py:25-26`; reconcile the Fig. 2g1 supplement caption with the actual panels.
- Verify the Static3 feature names against NUE_PCSE-Gym/pcse; update `fig1-assets/README.md` and `phase8d-fig1-edit-receipt.json` to describe the current hybrid, and reconcile the 198-vs-112 shape counts.
- Expand `phase8d-redesign-source-baseline.json` to the manuscript `.md/.tex/.pdf` files and the NUE_PCSE-Gym/pcse trees if those are in scope; pin or vendor the external style, `figure_standards.py`, and Natural Earth shapefile; record their hashes.
- Re-run `scripts/phase8d-verify-figure-redesign.py` and an independent visual pass after every change; treat the current `status: PASS` as an artifact/font check only, not a gate pass.
