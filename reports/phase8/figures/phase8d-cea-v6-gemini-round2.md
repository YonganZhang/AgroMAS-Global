# Final Round-2 Visual QA Report (Phase 8 Figures)

## Executive Summary
Five of the six figures (**`fig2-g1`**, **`fig2-p1-regimes`**, **`figs2-g3-subsidy`**, **`fig4-factorial-stress`**, **`fig5-deployment-closure`**) pass Round-2 visual QA with no material scientific-interpretability blockers. **`fig3-p2-transfer`** has **one interpretability blocker** (an unexplained missing `LOYO` Public-NL diamond on the `Weather` row in panel **a**) and **one concrete data–text collision** (the 3-line `above 300` block overlapping high-`Grain N` markers in both panel **c** phase spaces). One minor non-blocking data–text overlap is noted in **`fig2-p1-regimes`** panel **c**.

---

## Per-Figure Verdicts

### 1. `fig2-g1.png` — **PASS**
- **Verified Round-1 fixes**: Deposition (`NH4-N` dashed purple, `NOx-N` dotted sage) cleanly separates from solid policy surplus curves; right y-axis explicitly states `Available-region surplus (kg N/ha)`; `Organic N (t N/ha)` pool/tonne units are explicit; `b` is square with aligned regional KDEs, explicit cohort/marker/shading key, `1 above 300` disclosure, and direct centroid labels; `c` Brier skill includes baseline linestyle key (`vs climatology` / `vs ExtraTrees`), and CQR/Regret bars have `Before`/`After` legend and opaque value cards without endpoint occlusion.
- **Optional micro-polish (non-blocking)**:
  - **Panel `a` (bottom-left)**: At 2025–2026, the upper uncertainty ribbon of the `Soft` curve grazes the underside of the `NOx-N` legend label at top-right. Text remains completely legible, though shifting the `NH4-N / NOx-N` legend left into the 2000–2013 upper whitespace would give full clearance. *(In `c` right bars, `After` uses a red legend swatch while `Full` `After` bars are blue to match `Full-Telemetry` on the left; self-explanatory in context.)*

### 2. `fig2-p1-regimes.png` — **PASS (1 minor follow-up)**
- **Verified Round-1 fixes**: All six 0–300 phase spaces carry clean top-left metric readouts and top-right `1 above 300` disclosures with zero marker collisions; `b` labels `PPO · seed 4`, shows staggered markers plus explicit `PPO / DVS overlap` text, removes waterfall hatching, places `+17.58` / `+3.48` off bar edges, and distinguishes `Test aggregate` in the profit–NUE tradeoff; `c` states `NUE (symlog)` and discloses `Bare` clipping (`clipped 2.2`).
- **Concrete small follow-up**:
  - **Panel `c` (bottom-left `Surplus (kg N/ha)` raincloud)**: The top-right in-axes note `Display -65 to 130 · tails cropped` (`y ≈ 118`) crosses 3–4 upper jittered dots of `Weather` and the upper half-violin tip of `Linear`. Placing this note just above the top axis spine (or adding a subtle opaque background pad) removes the data overlap.

### 3. `figs2-g3-subsidy.png` — **PASS**
- **Verified Round-1 fixes**: Panel `c` left has crisp, non-colliding rotated bar value labels, explicit `Climate · N price 1× / 2×` axis labeling, and hatched `2×` legend above the bars; `c` right maps `Joint (%) · solid` vs `Profit (EUR/ha) · dashed` on the axes with the climate legend cleanly above the plot; `d` displays explicit fixed physical scales in the 4 heatmap column headers (`0–8 t/ha`, `0–250 kg/ha`, `-60–120 kg/ha`, `0–1200 EUR/ha`) with two-decimal yields (`5.68–5.74`), preventing visual exaggeration of negligible yield differences.
- **Unresolved issues**: None.

### 4. `fig3-p2-transfer.png` — **CONDITIONAL PASS (1 material blocker, 1 small follow-up)**
- **Verified Round-1 fixes**: Panel `a` distinguishes filled `LOYO` vs open `LORO` diamonds in the legend key and explains MSE units and column abbreviations (`Grain N MSE ((kg N/ha)²)`, `LY=LOYO · LR=LORO · W=world · R=rows`); `c` uses square joint plots with aligned KDEs in matching model colors (`Full64`, `Static3`, `ExtraTrees64`) and labels `Held-out farm-years n=40`.
- **Material blocker**:
  - **Panel `a` (`Joint compliance (%)`, `Weather` row — missing Public-NL `LOYO` diamond)**: `Full64`, `Static3`, `Linear64`, and `ExtraTrees64` each show both a filled `LOYO` diamond and an open `LORO` diamond (`Public NL n=4`), whereas `Weather` shows only the open `LORO` diamond at 25% with **no visible filled `LOYO` diamond** anywhere in `0–58%`. Whether `Weather`'s Public-NL `LOYO` compliance is `75%`/`100%` (clipped past `xlim`), `0%` (occluded/unplotted), or intentionally excluded, a reader cannot tell. Plot/unclip the missing marker (extending `xlim` if `≥75%`) or state the reason briefly in the lower-left note; while touching `a`, add a thin white stroke (`edgecolor='white'`) to the filled blue `LOYO` diamonds at 25% on `Full64` and `Static3` so they stand out cleanly against the dark rose `LOYO` bars.
- **Concrete small follow-up**:
  - **Panel `c` (`LOYO` and `LORO` phase plots — data–text collision)**: The 3-line right-aligned note (`Full64: 1 above 300 / Static3: 1 above 300 / ExtraTrees64: 1 above 300`) extends leftward to `x ≈ 215` at `y ≈ 262–292`, directly colliding with the upper `ExtraTrees64` green square markers at `x ≈ 223, y ≈ 265–280` in both plots. Condensing to a single compact line (e.g., `All 3 models: 1 above 300` kept right of `x = 230` at `y ≈ 290`) or moving the disclosure beneath the top-left `LOYO/LORO · Held-out farm-years n=40` label (empty space) eliminates the collision while keeping the 0–300 axis lock.

### 5. `fig4-factorial-stress.png` — **PASS**
- **Verified Round-1 fixes**: Sub-panel headers explicitly state N-price multipliers and subsidy units (`1× · 0 EUR/ha`, `2× · 0 EUR/ha`, `1× · 50 EUR/ha`); extreme dark heatmap cells (`0`, `100`) use crisp white text; `g` win/tie/loss counts and leave-one-region-out markers/legend fit without clipping; `h` legend (`Historical`, `+1.8°C`, `+3.5°C`, `× No-econ`) sits cleanly above the top subplot away from all trajectories.
- **Unresolved issues**: None.

### 6. `fig5-deployment-closure.png` — **PASS**
- **Verified Round-1 fixes**: Panel `a` scope text (`Test region-equal · applied + soil drawdown / Selected fate: grain + native loss`) sits cleanly above the bars, `NUE (symlog)` is explicit, solid (`Organic N Δstock`) vs dashed (`Mineral N`) mappings are on the y-axes, and coincident trajectories carry staggered markers plus explicit `Organic N curves overlap` text; `b` residual traces clear the bottom-right tolerance legend and tolerance gauges/replay counts are crisp; `c` fully renders all four sides of the bold `30/30` positive-cell frame, uses white text on `-0.58` dark blue cells, and keeps the extreme bottom-left CN `Native N loss` parity triangles (`R² ≈ -0.64, -0.58`) completely unclipped inside the axes.
- **Unresolved issues**: None.
