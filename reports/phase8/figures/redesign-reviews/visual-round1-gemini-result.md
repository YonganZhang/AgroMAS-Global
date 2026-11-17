# Phase 8D Upgraded Figures — Visual & Quantitative Integrity Review

Reviewed all seven actual rendered PNGs natively (`reports/phase8/figures/*.png`), alongside `scripts/phase8d-build-fig1-hybrid.py`, `scripts/phase8d-plot-*.py`, and the frozen Phase 8D JSON/CSV ledgers (`phase8d-core-statistics.json`, `phase8d-G1-verdict.json`, `phase8d-P2-predictive-cohort-strata.csv`, `phase8d-full-TRAIN-physical-decoding.json`, `phase8d-180cell-stress-surface.csv`, `phase8d-canonical90-stress-subset.csv`, `phase8d-primary-verification.json`, `phase8d-closeout-receipt.json`).

## Summary Verdicts

| Figure | Verdict | Blocking Issues |
|---|---|---|
| `fig1-architecture.png` | **FAIL** | Coupling 1 & 4 connector lines slice through their own labels; `Yield` and `Grain N` boxes in Agent 1 are left unwired from `+` (and `+` oval occludes incoming bottom arrowheads). |
| `fig2-g1.png` | **FAIL** | Panel `c` inset x-axis label `"Interval width (kg N ha⁻¹)"` collides directly with main x-tick label `"NL"`. |
| `fig2-p1-regimes.png` | **FAIL** | Hardcoded literal `(2, 25.06)` and `(2, 4)` in `phase8d-plot-p1.py:15`; panel `b` vertical `<->` arrow skewers the `(2, 9.67%)` Full-Telemetry marker and ends unanchored in mid-air; panel `d` shape/fill/size encodings are unkeyed. |
| `figs2-g3-subsidy.png` | **FAIL** | Panel `a` inset rotated y-label `"Joint (%)"` straddles panel `a`'s left vertical spine and `y = 40` tick mark. |
| `fig3-p2-transfer.png` | **FAIL** | Panel `c` frameless legend sits directly over the `#B8525A` `LOYO` bar, making the `#B8525A` `LOYO` swatch completely invisible; panel `d` `axvline(0)` protrudes above the MSE inset and cuts across the inset x-tick band. |
| `fig4-factorial-stress.png` | **FAIL** | Severe text collisions between the top colorbar (`0`, `40`, `60`, `100`, `Joint compliance (%)`) and Row 2 (`d–f`) headers (`1× · 0`, `2× · 0`, `1× · 50`); asymmetric colormap places neutral cream near `−16 pp` so `0 pp` renders as warm peach/tan. |
| `fig5-deployment-closure.png` | **PASS** | No clipping, overlap, garbling, hardcoding, or quantitative distortion (minor non-blocking note: panel `d` target marker shapes are unkeyed). |

---

## Cross-Cutting Style & Scientific Guardrails

- **Typography & palette across all 6 data figures (`fig2-g1` through `fig5-deployment-closure`)**: Verified in both rendered PNGs and SVG text trees—only lowercase bold panel letters (`a–d` or `a–i`), zero descriptive titles/suptitles, 100% pure-black (`#000000`) regular `Times New Roman` text, fixed muted rose/slate/sage palette, and zero outer-canvas border clipping.
- **Scientific scope & frozen-source fidelity**:
  - No prospective superiority claims (`Soft-Coupled` Sensorless `25.06%` vs `PPO` `27.00%` faithfully shown).
  - `Former-Held-Out` (`n=40`) and `Public-Reused` (`n=4`) cohorts as well as `LOYO` and `LORO` schemes remain strictly separated.
  - `DVS-N2` and `LegacyV6` use `Full-Telemetry` intentionally; absent cross-track bars (`PPO` Full-Telemetry, `DVS-N2` Sensorless, `cap=50` eco-removal / Full-Telemetry cells in `figs2` panel `b`) reflect absent frozen cells rather than omissions or fabrications.
  - World-equal MSE weighting is disclosed in `fig3` panel `d` and retains `LORO` MSE degradation (`517.65` vs `505.15`), separating prior acceptance from predictive accuracy.
  - `fig5` keeps all 30 required `Organic N` / `Soil C` / `Mineralization` cells positive (`0.01–0.85`), retains all 6 negative `native_Nloss_kg_ha` points across the 50-cell scatter, and separates `Native WOFOST runs` (`1,886`) from `Verified trajectory replays` (`16,382`).

---

## Per-Figure Concrete Findings

### 1. `fig1-architecture.png` — **FAIL**
- **Verified requirements**: Hybrid reconstruction of `fig1-candidates/candidate-b-v2-best.png` (`scripts/phase8d-build-fig1-hybrid.py`) preserves all 9 cropped physical/domain illustrations without baked-in raster text and keeps the asymmetric layout. Scenario tree has exact three action levels (`a1` → `Rain low` / `Rain high` → `a2` → `Temp low` / `Temp high` → `a3`); four specialist couplings feed into `Agent 5`; all five modules are numerical specialists (no LLM framing); `External WOFOST81-SNOMIN Referee` receives only a post-action incoming arrow from `Execute current dose` with zero outgoing edges (`referee_outgoing_edges = 0`) and no hidden-state feedback.
- **Concrete issues**:
  1. **Connector-over-text collisions (`scripts/phase8d-build-fig1-hybrid.py:78,81`)**:
     - *Coupling 1*: Vertical segment `(533, 407) → (533, 532)` passes straight through the middle of `"Coupling 1\nSpatial"` (`x = 470..583, y = 468..523`), slicing vertically through `"Coupling 1"` and `"Spatial"`.
     - *Coupling 4*: Vertical segment `(550, 923) → (550, 854)` passes straight through `"Coupling 4\nEconomics"` (`x = 473..584, y = 866..911`), slicing through `"4"` and `"Economics"`.
     - *(Coupling 2's horizontal segment at `y = 595` also grazes the baseline of `"Climate"`.)*
  2. **Unwired `Yield` and `Grain N` cards & occluded `+` arrowheads in Agent 1 (`scripts/phase8d-build-fig1-hybrid.py:65-68`)**:
     - `route([(1275,243),(1304,243),(1304,176),(1328,176)])` connects `+` **only** to `Executed N` (`y = 159..192`) and omits the grouping bracket present in `candidate-b-v2-best.png`, leaving `Yield` (`y = 79..112`) and `Grain N` (`y = 119..152`) as completely disconnected floating cards while `Executed N` alone connects down to `15 strata × 32 zero-mean joint residuals`.
     - The opaque white `+` oval (line 66, `y = 223..263`) is added after the `≤4-D adapter` and `Static3` connectors (line 65, ending at `y = 244` and `y = 255`), hiding both incoming bottom arrowheads beneath the oval fill.

### 2. `fig2-g1.png` — **FAIL**
- **Verified requirements**: Natural Earth Robinson map in `a`; all `b–d` values match `phase8d-G1-verdict.json` (`BSS > 0` across all caps/references, sub-target regional coverage `75.2%` AU Full and `81.9%` NL Sensorless retained, width amendment `62.50` vs `69.53 kg N ha⁻¹` explicit, ranking regret reductions `−40.8%` and `−49.4%`).
- **Concrete issue**:
  1. **Direct text-on-text collision in panel `c` (`scripts/phase8d-plot-g1.py:24`)**: `c.inset_axes([0.55, 0.05, 0.40, 0.21])` places the inset too close to panel `c`'s bottom axis, causing the inset x-label `"Interval width (kg N ha⁻¹)"` to cross below the main spine and collide directly on top of the main `"NL"` x-tick label.

### 3. `fig2-p1-regimes.png` — **FAIL**
- **Verified requirements**: NASA `Former-Held-Out` equal-region means from `phase8d-core-statistics.json`; `PPO` Full-Telemetry and `DVS-N2` Sensorless intentionally absent; `Archived bare` N-mining (`NUE = 11.56 / 9.34`, `S_N = −33.8 / −30.2`) retained.
- **Concrete issues**:
  1. **Hardcoded summary numbers in plot geometry (`scripts/phase8d-plot-p1.py:15`)**: `b.annotate('', (2, 25.06), (2, 4), ...)` hardcodes literal `25.06` and `4` instead of using `(2, val(q[0]))` and `(2, val(q[1]))` from the frozen query.
  2. **Arrow-over-marker collision & unanchored top tip in panel `b` (`scripts/phase8d-plot-p1.py:15`)**: Drawing the vertical `<->` arrow on `x = 2` (`Archived bare`) from `4` to `25.06` with no horizontal guide from `(0, 25.06)` (`Soft-Coupled` Sensorless) skewers directly through the `Full-Telemetry` `Archived bare` marker at `(2, 9.67%)` and terminates in empty space at `(2, 25.06%)`.
  3. **Unkeyed visual encodings in panel `d` (`scripts/phase8d-plot-p1.py:28`)**: Marker shape (`o` Sensorless vs `^` Full-Telemetry), fill (filled `1×` vs hollow `2×` price), and bubble area (`|S_N|`) lack any figure legend/annotation, and `DVS-N2` appears as a triangle in the policy legend while all other policies appear as circles solely due to loop order.

### 4. `figs2-g3-subsidy.png` — **FAIL**
- **Verified requirements**: Fixed NASA `Former-Held-Out` summaries; `DVS-N2` and `LegacyV6` use `Full-Telemetry`; absent `cap = 50` bars in `b` reflect absent frozen cells; subsidy trade-off inset in `c` plots only the 5 observed subsidy points (`0, 50, 100, 150, 200`).
- **Concrete issue**:
  1. **Inset y-label overlapping main y-axis spine in panel `a` (`scripts/phase8d-plot-gaps.py:9`)**: `a.inset_axes([0.05, 0.64, 0.32, 0.28])` places the rotated inset y-label `"Joint (%)"` (`x = 41.32 pt` in SVG) directly over panel `a`'s left vertical spine (`x = 41.98 pt`) and adjacent `y = 40` tick mark.

### 5. `fig3-p2-transfer.png` — **FAIL**
- **Verified requirements**: All four `{Former-Held-Out, Public-Reused} × {LOYO, LORO}` strata kept distinct in `a`; `b–d` use `Former-Held-Out` (`n = 40`); `c` reports predictive-row and world-equal acceptance from `phase8d-P2-predictive-cohort-strata.csv`; `d` discloses `World-equal MSE` and retains `LORO` MSE degradation alongside positive compliance differences.
- **Concrete issues**:
  1. **Zero-contrast legend swatch over bar in panel `c` (`scripts/phase8d-plot-p2.py:16`)**: `c.legend(loc='lower left')` places the frameless legend on top of the rose (`#B8525A`) `Predictive rows` `LOYO` bar, rendering the `#B8525A` `LOYO` legend patch completely invisible against the identical `#B8525A` bar fill (while `upper right` above `y = 80%` is empty).
  2. **Main `axvline(0)` cutting across inset in panel `d` (`scripts/phase8d-plot-p2.py:21-22`)**: `d.axvline(0)` runs the full height of `d`, sticking out above the `World-equal MSE` inset (`y = 0.96..1.00`) as a stray vertical stub and slicing through the inset's bottom x-tick band (`y = 0.54..0.62`) between `LOYO` and `LORO`.

### 6. `fig4-factorial-stress.png` — **FAIL**
- **Verified requirements**: Complete 180-cell stress surface (`phase8d-180cell-stress-surface.csv`) including all 47 negative `Soft-Coupled − PPO` cells, 90 continuity outlines (`phase8d-canonical90-stress-subset.csv`) in `a–c`, and isolated `×` markers for `remove-econ` at `subsidy = 50` in `g–i`.
- **Concrete issues**:
  1. **Severe colorbar-vs-header text collisions (`scripts/phase8d-plot-stress.py:25,30`)**: Row 2 (`d–f`) column-group headers `a.text(k, -0.75, lab)` (`1× · 0`, `2× · 0`, `1× · 50`) collide directly with the top horizontal colorbar's tick labels and title—`d`'s `"2× · 0"` overwrites `"0"`, `e`'s `"2× · 0"` collides with `"Joint compliance (%)"` (with `"40"` and `"60"` intruding into `e`'s header row), and `f`'s `"2× · 0"` overwrites `"100"`.
  2. **Misleading off-zero neutral color in signed difference panels `d–f` (`scripts/phase8d-plot-stress.py:6,15`)**: Linearly mapping the asymmetric 6-anchor `MAP_ANCHORS_ROSE_SLATE_6` ramp to `vmin = -50, vmax = 50` places the neutral pale-cream midpoint near `−16 pp` while `0.0 pp` (`FR` and `CN` zero-difference cells) renders as warm peach/tan, visually encoding zero difference as a positive `Soft-Coupled − PPO` gain.

### 7. `fig5-deployment-closure.png` — **PASS**
- **Verified requirements**: Clean layout with zero clipping, overlap, or garbling; exact frozen counts in `a` (`1,886` native WOFOST runs vs `16,382` verified trajectory replays, `13,155` TreeMLP parameters, `120/120` future-weather invariance) and `b` (`max_N = 1.90×10⁻¹¹ < 10⁻¹⁰`, `max_C = 2.11×10⁻¹⁰ < 10⁻⁹` over `6,104,146` configuration-day records); all 30 required cells in `c` positive (`0.01–0.85`); all 50 readout points in `d` plotted with all 6 negative `native_Nloss_kg_ha` control cells retained.
- **Non-blocking note**: Panel `d` legends the two track colors (`Sensorless`, `Full-Telemetry`) but leaves the five physical-target marker shapes (`o, s, ^, D, v`) unkeyed on the plot.
