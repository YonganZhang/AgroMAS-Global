# Foreign Aid Result

JOB_ID: 20261116T230913__deepseek__4064613
PROVIDER: deepseek
COMPLETION_STATUS: COMPLETE
ERROR_CLASS: NONE

## Summary
I completed a bounded, static pre-merge review of the six Phase8D figure scripts and the shared plotting/style module. The review traced the frozen-source indexing, arithmetic, cohort handling, aggregation, captions, and visual encodings, but did not execute the scripts or inspect rendered PDFs. It found one definite visual-encoding error in the NUE target band, one definite legend/color contradiction in the CQR panel, and one caption/regime-priority mismatch; lower-risk and unverified items are listed below. The review itself succeeded.

## Work Performed
- Read all supplied scripts: `phase8d-plot-style.py`, `phase8d-plot-g1.py`, `phase8d-plot-p1.py`, `phase8d-plot-gaps.py`, `phase8d-plot-p2.py`, `phase8d-plot-stress.py`, and `phase8d-plot-closure.py`.
- Traced `query`, `val`, `cases`, `contrast`, `bootstrap_joint`, `native_case`, `long_context`, and `annual_trajectory`, including P1/P2 benchmark indexing, Former-Held-Out versus Public-Reused filters, equal-region arithmetic, seed averaging, symlog axes, exact-zero omission, and caption claims.
- Performed one targeted read-only inspection of `reports/phase8/phase8d-core-statistics.json`, a native-metrics sample, and worktree data paths.
- Wrote `progress.md` and this `result.md`; no frozen source, native result, manuscript, or simulator file was edited. No simulations or other models were used.

## Evidence
- Supplied verifier evidence, not independently rerun by me: figure verifier PASS (8 immutable, 43+7 protected, 312 native budget hashes; 450 dpi embedded Times, zero PDF text overlaps); 110 additional source SHA checks; 100 Train/Dev zero-split books; climate 1984–2026; no Full cap50 and no Bare 2× evaluation.
- Confirmed by code inspection: in `phase8d-plot-gaps.py`, `dn.axhspan(i-.28,i+.28,xmin=.5/2,xmax=.9/2,...)` uses axes-fraction bounds 0.25–0.45, but the later `dn.set(xlim=(0,2.8), xticks=[0,.5,.9,2], ...)` maps those fractions to data values 0.70–1.26. The green band therefore covers 0.70–1.26, not the stated 0.50–0.90; it includes apparent NUE above 1.0 and excludes 0.50–0.70.
- Confirmed by code inspection: in `phase8d-plot-g1.py`, `cw.barh(i-.15,u,color=GREY)` and `cw.barh(i+.15,w,color=TC[i])` use `TC=[ROSE,BLUE]`, so the Full-Telemetry “after” bar is blue. The legend is `Patch(color=GREY,label='Before')` plus `Patch(color=ROSE,label='After')`, which describes only the rose Sensorless “after” bar and contradicts the blue Full bar.
- Confirmed caption inconsistency: the `save` note in `phase8d-plot-g1.py` states priority “compliant, abstention, mining, surplus, residual low NUE”, while the masks are `[compliant, surplus, mining, low NUE, abstention]` and the legend is `Compliant, Surplus >40, NUE >0.90, Low NUE, Abstention`. As implemented, an abstention with `S_N > 40` is counted as “Surplus >40”, not “Abstention”.
- Data-index observation: the `Public-Reused` cohort contains 86 NASA rows and 10 WUR rows (`Public-Reused-WUR`); the source-`NASA` filter therefore does not by itself remove the P2 public diamonds. Sampled public rows have top-level `region` and `joint` equal to `None`; I did not verify the `region_equal` payload used by `val`, so the four public diamond values remain unverified.
- Cohort-selection risk: `long_context` globs `PRIMARY/data/phase8-physical-books/*Historical*.jsonl.gz` and checks `plan == [0,0,0]`, but does not filter or assert Train/Dev. The supplied 100-book observation suggests the current directory is Train/Dev, but the code does not enforce the stated cohort separation.
- Unverified constant linkage: `at.plot(yr,697-.339*yr,...)` and `at.plot(yr,538.868-.264*yr,...)` hard-code the deposition slopes, while `long_context` only asserts that the helper text contains `'697'` and `'538.868'`. The `.339` and `.264` slopes are not tied to `nitrogen_helpers.py` by an assertion.
- Robustness risk: `query` asserts only `len(q) <= 1` and returns `None` when no row matches; `val(None)` returns `NaN`. This is legitimate for explicitly unevaluated cells (Bare 2×, Full cap50), but required cells such as all five P2 variants/schemes, the public diamond points, and subsidy levels have no explicit presence assertion and could silently disappear.
- Environment limitation: the scripts assert cwd is this worktree but read native results and physical books from the absolute main-root `PRIMARY`. The worktree itself has no `data/phase8-physical-books/*Historical*.jsonl.gz` and no `data/phase8d-evaluation/<episode>/result.json`; my targeted native check hit those absent local paths. I therefore did not independently re-read the main-root native data, the PPO seed label, or the event-stage representation.

## Files Changed Or Reviewed
- Changed: `_reports/_foreign_aid/20261116T230913__deepseek__4064613/progress.md`; `_reports/_foreign_aid/20261116T230913__deepseek__4064613/result.md`.
- Reviewed, not edited: `scripts/phase8d-plot-style.py`, `scripts/phase8d-plot-g1.py`, `scripts/phase8d-plot-p1.py`, `scripts/phase8d-plot-gaps.py`, `scripts/phase8d-plot-p2.py`, `scripts/phase8d-plot-stress.py`, `scripts/phase8d-plot-closure.py`.
- Read-only inspected: `reports/phase8/phase8d-core-statistics.json`; `reports/phase8/phase8d-native-episode-metrics.csv` (sample); worktree glob `data/phase8-physical-books/*Historical*.jsonl.gz` (zero files).
- Not present locally: `data/phase8d-evaluation/eb0a84dc690399cde170/result.json` (main-root path not re-read).

## Errors Or Blockers
No review-execution error; the review completed. Code findings, ordered by severity:

1. **Definite visual-encoding error — NUE corridor band (gaps panel d).** The band is shifted to 0.70–1.26 because `xmin/xmax` are divided by 2 while the final xlim is 0–2.8. This is scientifically misleading: it shades part of the soil-mining range above NUE 1.0 and leaves 0.50–0.70 outside the apparent target. Fix with `xmin=.5/2.8, xmax=.9/2.8` or compute the fractions from the final xlim; alternatively draw the band with data-coordinate transforms.
2. **Definite legend/color contradiction — CQR before/after (g1).** The “After” legend swatch is rose, but the Full-Telemetry after bars are blue. This is the same class of model/color contradiction previously fixed in the P2 marginals. Use separate “Sensor after” and “Full after” patches, or a neutral after encoding with track labels.
3. **Caption versus implemented priority — abstention regimes (g1).** The note says abstention is second in priority; the masks assign it last. As implemented, abstentions with surplus above 40 are reported as surplus. Align the note with the code/legend, or, if abstention is intended to be high priority, reorder the masks and regenerate the stack.
4. **Cohort-selection risk — zero-split baseline.** The `*Historical*.jsonl.gz` glob is not restricted to Train/Dev, so the stated separation from Held-Out policies depends on directory convention rather than an explicit filter/assert. The supplied 100-book check supports the current data but does not make the code enforce it.
5. **Unverified linkage — deposition slopes.** Only the two intercept strings are asserted; `.339` and `.264` are not checked against `nitrogen_helpers.py`. If the helper’s trend differs, the panel’s deposition trajectory is wrong even though the caption says it follows the helper.
6. **Lower-severity visual encoding — unlabeled inter-model fills.** `g1` panel d fills between the two BSS tracks, `p2` panel b fills between variant curves, and `gaps` panel a fills between Soft and each comparator. These bands have no legend and can be read as uncertainty intervals rather than inter-model gaps; label them or remove them.
7. **Lower-severity keying — paired win/tie/loss bars (p1 panel ct).** The green/grey/rose segments are not explained by a legend; only the tie count is printed. Add a compact win/tie/loss key.
8. **Lower-severity duplication — typology panel (gaps panel d).** `TreeMLP/soft` appears as both “I. MLP” and “II. Soft-Coupled” with identical data and CIs. If this is an intentional repeated anchor, mark it as the same reference; otherwise it looks like two independent estimates.
9. **Hardening — silent missing configurations.** Required `query` results are not asserted non-`None`; `val(None)` silently yields `NaN`. Keep `None` for explicitly unevaluated cells, but assert presence for every cell the caption claims exists.

## Next Steps
- Correct the `dn.axhspan` bounds to the final 0–2.8 scale, rerender `figs2-g3-subsidy`, and visually confirm the green band aligns with the 0.5 and 0.9 ticks.
- Replace the `cw` “After” legend with model-matched Sensor/Full entries; check the adjacent regret panel for the same before/after ambiguity.
- Reconcile the `g1` regime-priority note with the masks/legend; reregenerate the stack if abstention is meant to outrank surplus.
- Add an explicit Train/Dev filter or assertion to `long_context`, and add required-cell presence assertions to `query` call sites while preserving intentional `None` cells.
- Verify the deposition slopes and the native PPO seed/event-stage representation against the main-root `nitrogen_helpers.py` and native results; then rerun the supplied SHA, 450 dpi, and text-overlap verifier.
- No broad recomputation of frozen sources is needed beyond these targeted checks.
