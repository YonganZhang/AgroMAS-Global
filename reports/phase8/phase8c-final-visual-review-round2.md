# Phase 8c Round-2 Bounded Visual Review

**Overall Verdict: REVISE (2 small, localized text-collision fixes in Fig 1 and Fig 3c; Figs 2, 4, 5, S2, and captions JSON PASS for author draft review)**

All Round-1 structural, semantic, and scale corrections are verified in the rendered PNGs. Only two genuine glyph-collision residuals remain (`fig1-architecture.png` around the `Private 64-D (P2)` box/connector, and `fig3-p2-transfer.png` Panel c legend-on-bar overlap).

---

## 1. Actionable Residuals (Required Fixes)

1. **`fig1-architecture.png` — `Spatial Twin` adapter text/line collisions**
   - **Sub-box top border through text**: In `"t–1 LOYO / LORO; prior OOD → / correction 0"`, the wrapped second line `"correction 0"` drops across the top border stroke of the `Private 64-D (P2)` rounded rectangle (the border line runs directly between line 1 and line 2, grazing the top of `"correction 0"`). Shift this annotation upward by ~8–10 pt (or keep it on a single line above the `Private 64-D (P2)` box).
   - **Connector shaft bisecting label**: Immediately below `Private 64-D (P2)`, the horizontal segment of the orthogonal arrow to `+` passes directly between `"Output"` and `"correction"`, touching `"correction"` (and the `36-D backbone` elbow stroke slightly overlaps the left bar of `+`). Place `"Output correction"` cleanly above or to the right of the connector shaft, and leave a small gap around the `+` glyph.

2. **`fig3-p2-transfer.png` (Panel c) — Legend overlapping `ExtraTrees64` bar**
   - In Panel c (`"Prior OOD → zero correction; backbone retained"`), the frameless upper-right legend places `"LORO"` at `y ≈ 84–89%`, directly colliding with the top of the `ExtraTrees64` `LOYO` red bar (`87.5%`). Raising Panel c's upper y-limit to `~115` (while keeping y-ticks at `0–100`) clears the bar completely.

---

## 2. Per-File Confirmation Checklist

- **`fig1-architecture.png` — REVISE (minor collision fix above; all Round-1 content items confirmed)**
  - Restored original artwork confirmed: wheat + root/soil profile on left; wheat/root/soil strip and tractor spreader inside `External referee`.
  - Native MLP (`36-D backbone`, `96 → 96 → 3`, `SiLU; dropout 0.05`, `13,155 parameters`, `Three frozen seeds`) + additive `Private 64-D (P2)` (`PCA/Ridge ≤4-D`) `+` `32 joint members` + `a₁ → a₂ → a₃` scenario tree confirmed.
  - `Climate → Agronomic Control` (`Branch weights / information partitions`) and `Climate → Spatial Twin` arrow endpoints land cleanly on box borders, as do all `Joint-distribution bus`, `Candidate-dose query`, `Eco Safety`, `Economics`, and `External referee` arrows.
  - Short `"DVS + history"` heading fits cleanly on one line.
  - Prior OOD (`prior OOD → correction 0`) vs controller OOD (`Controller OOD / empty set: dose 0, never compliance`) are explicitly separated.

- **`fig2-p1-regimes.png` — PASS**
  - Panel d (`Soft`, `Composite`, `Bare`) labels are cleanly separated with distinct color-matched leader lines and zero overlap.
  - Panels a–c typography, legends, and regional bars (including unembellished FR ceiling) are crisp and collision-free.

- **`fig3-p2-transfer.png` — REVISE (Panel c legend overlap only)**
  - Panel a cohorts/folds (`Former LOYO (40)`, `Public NL LOYO (4)`, `Former LORO (40)`) and lower-left legend have zero collisions.
  - Panel b open white-filled squares + dashed lines + horizontal jitter cleanly separate overlapping `composite` vs `soft` trajectories across all five regions.
  - Panel c fallback semantics (`Prior OOD → zero correction; backbone retained`, `Accepted prior decisions (%)`) are corrected; only the `"LORO"` legend-on-bar overlap requires adjustment.
  - Panel d `"Holm p=1"` annotations sit cleanly above and to the right of both CI lines within axes bounds.

- **`fig4-factorial-stress.png` — PASS**
  - Full `0–100` (`Joint compliance (%)`) and symmetric `-100` to `100` (`Difference (pp)`) colorbars confirmed.
  - Suptitle explicitly defines `"black outlines = 90 continuity cells; idealized climates"`, and all 90 black cell borders (`10 rows × 3 caps × 3 climates`) and 180 cell integers render cleanly without clipping.
  - Bottom 3-panel `"Historical cap40 diagnostic"` (`Joint compliance (%)`, `Partial profit (EUR ha⁻¹)`, `Native N loss (kg ha⁻¹)` across `0–200 EUR ha⁻¹` for `Complete` vs `Economics removed` at `50`) is legible and collision-free.

- **`fig5-deployment-closure.png` — PASS**
  - Panel c log y-axis (`10⁻¹²` to `~2×10⁻⁹`) fully encloses both `10⁻¹⁰` (`N tolerance`) and `10⁻⁹` (`C tolerance`) dashed lines well above the `1.927e-11` and `2.115e-10` bars and value labels.
  - Panels a, b, and d text blocks, parameter counts, `Regime` interface, and execution/independence denominators are clean and readable.

- **`figs2-g3-subsidy.png` — PASS**
  - All four panels (`Response-model ablation`, `Planning and objective ablation`, `Specialist removal (unequal cohort noted)` with `n=52 / n=31 / n=52`, and `Economic activation diagnostic`) have clear labels and zero collisions.

- **`phase8c-captions.json` — PASS**
  - English and Chinese captions for Figures 1–5 and the `scope` statement accurately match the rendered panels, including the added bottom Historical cap-40 subsidy diagnostic in Figure 4 and prior-OOD zero-correction semantics.

---

## 3. Optional Stylistic Polish (Non-Blocking)

- **`fig5-deployment-closure.png` (Panel c)**: The horizontal `10⁻⁹` (`C tolerance`) dashed line runs right between the two rows of the frameless upper-right legend (`N tolerance` above the line, `C tolerance` ~1 px below it). Raising `ylim` top slightly (e.g., `4e-9`) or enabling a white legend background avoids bisecting the legend.
- **`fig4-factorial-stress.png`**: Vertical clearance between Row 1/2 `"Surplus cap (kg N ha⁻¹)"` x-labels and the Row 2/3 subplot titles below them is non-overlapping (~3–5 px) but snug; a slight `hspace` increase is optional.
- **`phase8c-captions.json`**:
  - Fig 4 caption refers to the PPO-difference row as `"lower panels"` (`下排`) and the new Row 3 diagnostic as `"Bottom panels"` (`底排`); changing `"lower panels"` / `"下排"` to `"middle panels"` / `"中排"` is slightly clearer for a 3-row layout.
  - `"scope"` omits spaces after semicolons and before `13512` (`;P2`, `;not`, `;intervals`, `;Holm family13512.`); add spaces if rendered directly in author-facing draft pages.
