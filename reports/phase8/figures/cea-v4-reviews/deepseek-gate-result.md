# Foreign Aid Result

JOB_ID: 20261116T210515__deepseek__2126023
PROVIDER: deepseek
COMPLETION_STATUS: COMPLETE
ERROR_CLASS: NONE

## Summary
Read-only premerge review of the frozen figure-only CEA v4 batch. All six quantitative PNG/PDF/SVG triples match the current verification ledger and pass the 450-DPI, page-bounds, >20%-pairwise-text-overlap and Times-New-Roman/black/regular-text checks; the critical arithmetic was recomputed independently from the frozen sources, including the leader-confirmed OptionA (Sensorless cap50 = 34.4%, Full/no-eco cap50 = zero records and explicitly "Not evaluated"), 46/52 and 47/52 parity ties, matched n=31 19.39/29.03 vs 17.58/25.81, the 180/90/47 stress surface, 5.15/5.61 warming means, 18,268 configurations, 13,155 parameters, 120/120 invariance, 6,104,146 records, 30/6 closure cells and min R²=0.005571. Fig1 v4-1/v4-2 are byte-identical to their Image2 outputs, v4-2 is byte-identical to the best copy, and neither contains a mechanical fan. Frozen8 and all 43 protected manuscript/PPTX/v2-v3 files are unchanged; NUE_PCSE-Gym and pcse are clean at the expected commits. No content-blocking defect was found; one merge-process gate (v4 Gemini QA still recorded as pending) and four minor non-blocking layout/metadata/caption notes are reported.

## Work Performed
- Read the authority `task-754910f37ddf0ccd.md` and `continue-5c6220be8081cb09.md`, fixed the scope as a read-only premerge figure review, and treated OptionA as the controlling instruction for the cap50 panel.
- Inspected the nine actual PNGs natively (`candidate-b-v4-1`, `candidate-b-v4-2`, `candidate-b-v4-best`, `fig2-g1`, `fig2-p1-regimes`, `figs2-g3-subsidy`, `fig3-p2-transfer`, `fig4-factorial-stress`, `fig5-deployment-closure`) plus full-resolution crops of Agent 2, the Fig1 referee, the G1 Europe inset, the P1/gaps panel boundaries and the P2/closure insets.
- Read the six plotting scripts, `phase8d-plot-style.py`, `phase8d-update-figure-metadata.py`, `phase8d-verify-figure-redesign.py`, the render audits, `phase8d-cea-v4-data-audit.json`, `phase8d-redesign-verification.json`, the captions and the figure source/bounds ledger.
- Recomputed the critical arithmetic read-only from `phase8d-core-statistics.json`, `phase8d-G1-verdict.json`, `phase8d-G1-radius-interpretation.json`, `phase8d-root-cause-verification.json`, `phase8d-case-metrics-seed-averaged.csv`, `phase8d-P2-predictive-cohort-strata.csv`, `phase8d-180cell-stress-surface.csv`, `phase8d-canonical90-stress-subset.csv` and `phase8d-full-TRAIN-physical-decoding.json`.
- Ran independent PyMuPDF audits of all six PDFs (page count, span page bounds, pairwise overlap, fonts, colors, bold spans) and Pillow checks of the six PNG DPI values.
- Verified the Frozen8 hashes, all 43 protected-file hashes, the 22 artifact hashes, the two Image2 raw-output hashes and prompts, and the clean code repositories.
- Wrote only this report directory; no project source, figure, manuscript or data file was modified.

## Evidence

### Per-figure verdicts (actual source-PNG SHA-256)

| Figure | Source PNG SHA-256 | Verdict | Basis |
|---|---|---|---|
| `candidate-b-v4-1.png` | `0c2b6f517634d780190312c37a3947d0fe5f6fbe8e6c847e3b5e5051f8b0f4ce` | **PASS (alternate)** | No mechanical/electric fan or turbine; three discrete climate-trajectory ribbons; five agent headers, coupling 1–4, a1→a2→a3, balance meter, tractor and one-way referee preserved; composition matches v3-3 apart from the authorized Agent 2 edit. |
| `candidate-b-v4-2.png` | `cd816c3fd568f34303b5df007144c29dce4cb70f434fd3ec397dc46b224f7ed8` | **PASS (selected)** | Host-tentative choice confirmed as the cleaner variant: five-trajectory translucent probability envelope, no mechanical object, same preserved composition and sharp typography. Byte-identical to `candidate-b-v4-best.png`. |
| `candidate-b-v4-best.png` | `cd816c3fd568f34303b5df007144c29dce4cb70f434fd3ec397dc46b224f7ed8` | **PASS** | Exact byte-for-byte copy of v4-2; matching v4-2 prompt. |
| `fig2-g1.png` | `b4be0faf22342167eecb66a330f34ac9728f3a0874942a6e31e6fc19917123cb` | **PASS** | Natural Earth Robinson map with 60/30/0/−30° latitude and 120°W/0/120°E longitude labels, N arrow, 3,000 km scale bar, five separated regional markers and exact Europe inset; BSS 0.042–0.605, coverage 90.8/90.4 macro, AU Full 75.2, widths 74.0/83.1 vs 62.5/69.5, regret 4.76/3.67/8.04/7.25 and −40.8%/−49.4% all match the frozen verdict. |
| `fig2-p1-regimes.png` | `c2d530de1ffc1fa95cda143b362be8d94c76b7a242217f2c5e1da9b7ffcd20da` | **PASS** | 46/52 ties vs PPO and 47/52 vs DVS-N2 (Holm p=1.00); 25.06→21.58→4.00 with +21.06 pp/6.27×; Dev AU 0/20/40; four regional policies; archived-bare 976 EUR/ha, NUE 11.56, S_N −33.8; CN 0/36 and FR NUE 1.19 tags present; track/price/bubble keys present. |
| `figs2-g3-subsidy.png` | `936d5db441cb05f1542b1f09602d3d1245431b8f8f799a96c46b8d787d9fe013` | **PASS** | Matched n=31 inner join gives 19.4/29.0 complete vs 17.6/25.8 no-climate; cap50 shows only Sensorless 34.4 and explicitly "Full and no-eco at cap50 / Not evaluated / Binding caps 25–40 evaluated"; zero Full-cap50 and zero remove-eco-cap50 records; three climates with 1×/2× and subsidy 0/50/100/150/200 labels; group brackets and NUE/S_N columns present. |
| `fig3-p2-transfer.png` | `9411db6c8ef3727268ac42f781b1add990641568001be4441b31baa99b76a75f` | **PASS** | All five variants × four cohort/scheme strata with direct labels including 0.0 for Weather Public-NL LOYO; acceptance 88.4/72.0 rows, 77.5/60.0 world-equal, 93/120 and 72/120 closed-loop; both reference CIs and Holm p=1; world/row Grain-N MSE 445.8/452.0 (LOYO) vs 517.7/494.8 (LORO), retaining the LORO degradation. |
| `fig4-factorial-stress.png` | `70b5f9123d93531fa35a67eaa352c75b2e72a78c34a3b6971e3ecd7f2295c54d` | **PASS** | 180 complete cells and 180 matched differences; 90 canonical continuity outlines (30 per climate); 47 negative differences; signed −50…50 scale with cream at 0; no header/colorbar collision; shared colorbars centered; +5.15/+5.61 warming means computed from soft-vs-PPO only. |
| `fig5-deployment-closure.png` | `be68d9fa2c2e9c6301bb4da130335bcd4fb2817e168d1c3d8ce99fc08b5e967f` | **PASS** | 1,886 + 16,382 = 18,268; 13,155 parameters; 120/120 invariance; max N 1.904e-11 vs 1e-10 (5.25×) and C 2.115e-10 vs 1e-9 (4.73×) over 6,104,146 records; full 10×5 heatmap with black 30-cell border and six negative native-loss cells; both track-color and five-target shape legends. |

### Independent arithmetic (read-only recomputation)
- G1: BSS ExtraTrees 0.148/0.161/0.168/0.205, climatology 0.605/0.579/0.575/0.597; Sensorless 0.042/0.069/0.061/0.065 and 0.559/0.535/0.527/0.530; coverage 90.78/90.37 macro and 75.19 AU Full; widths 73.98/62.50 Full and 83.10/69.53 Sensorless; regret 4.757/3.666 (Sensorless) and 8.042/7.250 (Full), reductions 40.84%/49.43%.
- P1: 25.0606/21.5758/4.0000; +21.06 pp and 6.27×; Dev 0.0/0.2/0.4; 46/52 and 47/52 both Holm 1.0; FR NUE 1.193; CN decisions 36/36 abstained; farm-years AU11 US12 NL5 FR12 CN12; bare 976.24 EUR/ha, NUE 11.557, S_N −33.782.
- Gaps: n=31; region-equal 19.3939/17.5758 and pooled 29.0323/25.8065; cap50 Sensorless 34.3636; cap50 Full 0 rows; cap50 remove-eco 0 rows for both tracks; remove-eco S_N 34.95/36.02.
- P2: 4 strata values including Public-NL Weather LOYO 0.0; acceptance rows 88.36/72.02, world-equal 77.5/60.0, closed-loop 93/120 and 72/120; forest means/CIs 2.22 [−5.28, 9.72], 6.94 [−5.01, 19.17], 2.50 [0.00, 7.50], −1.50 [−14.22, 9.73]; all Holm p=1.
- Stress: 180 complete unique cells; 90 canonical unique cells all present in the 180; 47 negative differences; means 5.1515 at +1.8°C and 5.6094 at +3.5°C.
- Closure: 1,886 + 16,382 = 18,268; 13,155; 120/120; 1.9042545318370685e-11 and 2.1145751816220582e-10; 5.25× and 4.73×; 6,104,146; matrix shape 10×5; 30 first-three-column positive cells; 6 negative cells all in native N loss; min 0.005571150874843278; 50 scatter points.

### Artifact, PDF and PNG audit
- The current `phase8d-redesign-verification.json` is `status: PASS`; 22/22 artifact hashes match (6 quantitative PNG/PDF/SVG plus 4 Fig1 artifacts).
- All six quantitative PDFs: one page each, zero spans outside the page rectangle, zero pairwise text overlaps above 20% of the smaller span; fonts only `TimesNewRomanPSMT` and `TimesNewRomanPS-BoldMT`; all span colours 0; bold spans only `a`–`i`.
- The small sub-20% intersections found in P1 (9), gaps (9), P2 (5) and closure (2) are adjacent multi-line/ascender boxes at ~5.2–5.6% area, not visual text collisions; G1 and stress have zero intersections.
- All six quantitative PNGs are 450.0118 DPI.
- Frozen8: 8/8 SHA-256 match. Protected baseline: 43/43 match, including the PPTX, all v2/v3 PNGs and all phase7/phase8 manuscript files. `NUE_PCSE-Gym` is at `c242b6dd62d853c5888144bab864f9a509599633` and `pcse` at `d1fe6d29de828033b850ec51d994988d8d6d406f`, both clean.
- Current `phase8d-cea-v4-data-audit.json` independently confirmed: matched n=31, Full_cap50_record_count=0, heatmap 10×5, 30 positive required cells, min 0.005571, 6 negative exploratory cells, zero >20% text overlaps and zero out-of-page spans for all six figures.
- Fig1 v4 provenance: v4-1 and v4-2 match their Image2 raw outputs byte-for-byte and their prompt hashes; v4-best matches v4-2 and its prompt. No PPTX conversion; the PPTX hash is unchanged.

### Fig1 v4 visual check and inherited simplifications
- No mechanical/electric desk fan or turbine blades remain in Agent 2 of either v4 image; the v3-3 original does contain the literal desk fan, confirming the edit was applied.
- Five agent headers, couplings 1–4, a1→a2→a3 (no a0, no fourth stage), the Nutrient-Safety Corridor balance meter (`0.50 ≤ NUE ≤ 0.90`, Soft-Coupled at the sage centre), the tractor and the isolated WOFOST81-SNOMIN referee are preserved; the referee has no outgoing arrow, only the incoming post-action arrow.
- Pixel diff against v3-3 is global, not pixel-local: mean sum-of-RGB |Δ|≈33.6/765 and 25.6% of pixels differ by >30 (25.1% outside the Agent 2 crop). The structure, text, positions and composition are visually unchanged; this is a raw Image2 re-render, consistent with the task's "local-edit" prompt but not a pixel patch.
- Inherited from v3-3 and not introduced by this fan-removal edit: the compact `15 × 32 residuals` label (native Fig1 text says `15 strata × 32 zero-mean joint residuals`), `Causal analogs` (native text says `Causal −dT analog fan`), and the balance-meter zone placement that can imply Tier2/Archived target the wrong NUE tails. These are Fig1 scientific-precision items for a later full Fig1 pass, not regressions of the authorized Agent 2 edit.
- The v4 PNGs are 1568×1003 RGB with no embedded DPI, the same raster size as v3-3; the 450-DPI requirement applies to the six quantitative figures, all of which pass.

## Files Changed Or Reviewed
- Changed (report-only): `_reports/_foreign_aid/20261116T210515__deepseek__2126023/progress.md` and `_reports/_foreign_aid/20261116T210515__deepseek__2126023/result.md`.
- Reviewed read-only: the six `scripts/phase8d-plot-*.py` files, `scripts/phase8d-plot-style.py`, `scripts/phase8d-update-figure-metadata.py`, `scripts/phase8d-verify-figure-redesign.py`; the nine target PNGs; the six PDFs/SVGs and their render audits; `phase8d-cea-v4-data-audit.json`, `phase8d-redesign-verification.json`, `phase8d-captions.json`, `phase8d-figure-source-and-bounds.json`, `phase8d-cea-v4-protected-baseline.json`, `phase8d-fig1-v4-raw-receipt.json`; the Frozen8 sources; the phase7/phase8 manuscript files and PPTX/v2/v3 PNGs (hash-only); and the two read-only code repositories.
- No project source, figure, manuscript, PPTX or data file was edited.

## Errors Or Blockers
- Content: none blocking. All six quantitative figures and the Fig1 v4 edit pass the specified quantitative, visual and provenance checks.
- Merge-process gate: `reports/phase8/figures/phase8d-fig1-v4-raw-receipt.json:18` still records `selection_status: "Host provisional; Gemini QA pending"`. The authority (`task-754910f37ddf0ccd.md:77`) required external Gemini visual QA before merge, and the prior round-2 Gemini PASS in `phase8d-redesign-review-closure.json` covers the preceding batch (its hashes are d7b7/be77/…, not the current b4be/c2d5/…). The v4 snapshot should not be treated as merge-complete until v4 Gemini QA is recorded or explicitly waived. This is a process gate, not a figure defect.
- Minor non-blocking layout: (1) `scripts/phase8d-plot-g1.py:21` places the `NL 7.1 t/ha` label across the Dutch/German coastline in the Europe inset (readable but visually crossed); (2) `scripts/phase8d-plot-gaps.py:34` draws the panel-d group brackets/labels at x≈723 inside panel c's axes (panel c tight-bbox right 793.8 vs panel d left 769.1 in the render audit), so the two panels' decorations slightly interleave; no data or text-span overlap.
- Minor non-blocking metadata: `scripts/phase8d-plot-style.py:44` stores `len(fig.axes)` as `panel_count`, yielding 11 for the nine-panel Fig4 (two colorbar axes) and 5 for the four-panel Fig5 (one colorbar axis); the field is axes count, not panel count. Also `phase8d-captions.json:4` calls the P1 panel-d NUE>0.90 shading "mining-rate bands"; the plotted quantity is the percentage of decisions with NUE>0.90.
- Coverage gaps: the v4 Fig1 raster has no 450-DPI metadata (same 1568×1003 size as v3-3); the previous `phase8d-redesign-review-closure.json` hashes/statuses are historical and were not used as v4 evidence; manuscript caption synchronization remains explicitly deferred, so the unchanged old manuscript captions were not failed.

## Next Steps
- Record the v4 Gemini visual QA result (or an explicit author/leader waiver) before merging; then commit the currently untracked v4 PNGs/prompts, `phase8d-cea-v4-data-audit.json`, `phase8d-cea-v4-protected-baseline.json`, `phase8d-cea-v4-review-packet.md` and `phase8d-fig1-v4-raw-receipt.json` together with the modified quantitative artifacts/scripts.
- In a later optional layout pass, move the G1 Europe inset labels off the coastlines, widen the gaps between panels c and d, and rename `panel_count` to `axes_count` (or exclude colorbar axes).
- Keep manuscript/caption synchronization deferred until author figure selection; do not treat the unchanged manuscript captions as a v4 regression.
