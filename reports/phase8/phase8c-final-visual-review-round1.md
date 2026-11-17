# Independent Visual & Scientific Review: Phase 8C Final Rendered Figures 1–5

## Overall Verdict: **REVISE BEFORE FINALIZATION (Blockers Present)**

- **Numerical & Contract Integrity vs. `phase8c-core-statistics.json`: PASS.** Every plotted bar, line, scatter coordinate, bootstrap interval, heatmap cell, parameter count (`13,155`), mass-balance residual (`1.927e-11` kg N ha⁻¹, `2.115e-10` kg C ha⁻¹), invariance count (`120 = 4 × 30`), and execution denominator (`18,268 = 17,747 new + 521 reused`; `17,747 = 1,917 unique native trajectories + 15,830 trajectory cache hits`; `5,928,274` daily closure records across the `17,747` new configurations) matches `reports/phase8/phase8c-core-statistics.json` and `phase8c-180cell-stress-surface.csv`. Zero invented runtime, latency, or prospective field-assurance claims appear in the figures.
- **Visual Rendering & Scientific Labeling: FAIL (Actionable Fixes Required).** Direct inspection of the rendered 450-DPI PNGs reveals **three hard visual collisions/occlusions** (Fig. 1 `"DVS + management"` card text overlap; Fig. 2d `"Sofmposite"` superimposed labels/markers; Fig. 3b hidden `LOYO soft` curve and Fig. 3d CI bar striking through `"Holm p=1"`), **one genuine scientific labeling error** (Fig. 3c title conflates P2 prior-adapter OOD zero-correction fallback `Δy = 0` with Tier-3 `operational dose = 0` fallback), **complete omission of `candidate-e.png` domain artwork and internal schematic diagrams** in `fig1-architecture.png`, and **colorbar saturation / unexplained subset borders** in Fig. 4.
- **Supplied Captions Check:** No standalone caption file exists yet under `reports/phase8/figures/` (manuscript/report integration pending). On-canvas titles/notes were audited directly, and mandatory caption disclosures are itemized at the end of this report.

---

## 1. Figure 1 (`fig1-architecture.png` vs. `candidate-e.png`)

### 1.1 Verified Architectural & Connector Corrections (Scientific PASS)
- **Typed numerical specialists & referee:** Five non-anthropomorphic modules (`Spatial Twin`, `Climate`, `Eco Safety`, `Economics`, `Agronomic Control`) plus `External referee` (`WOFOST81-SNOMIN`), with bottom disclaimer explicitly ruling out global chance/CVaR optimality claims (`Typed numerical specialists; nodewise nonanticipative planning, without a global chance/CVaR optimality claim.`).
- **Input modality differentiation:** Mandatory public inputs (`Observed weather`, `DVS + management`) enter `Spatial Twin` from their right edges via **solid** arrows; `Optional telemetry` (`LAI, soil moisture, plant N; Full-Telemetry only`) enters via a **dashed** arrow.
- **World-model conditioning & private adapter topology:** `Spatial Twin` specifies `36-D inputs → 96 → 96 → 3` SiLU (`13,155` parameters/network, frozen 3-seed ensemble, `32` joint members), keeps `Private 64-D → PCA/Ridge (≤4-D) → additive OUTPUT correction` inside the private boundary (`P1: weather / static soil`, `P2: causal t−1 annual features`), and receives explicit `candidate-dose query` (from `Agronomic Control`) and `weather query` (from `Climate`) arrows.
- **Independent distribution-bus taps & one-way referee:** `Joint-distribution bus` feeds `Eco Safety`, `Economics`, and `Agronomic Control` independently (eliminating `candidate-e.png`'s duplicate `Eco Safety` arrow and false `Eco Safety → Economics` left-margin jumper). `Agronomic Control → External referee` is strictly one-way (`Realized yield, surplus, NUE`, `Native N loss`, `Daily carbon / nitrogen closure`, `No hidden-state / future-truth feedback`).

### 1.2 Exact Omissions in Native Reconstruction (`fig1-architecture.png`)
1. **All domain illustrations omitted (`fig1-assets/` absent):** None of the wheat, soil-root, or tractor fertilizer-spreader illustrations from `candidate-e.png` were cropped or placed (`fig1-native-rebuild-note.json` explicitly notes decorative raster illustrations were omitted).
2. **Internal schematic diagrams collapsed to plain text:**
   - `Spatial Twin` omits `candidate-e.png`'s visual sub-diagram showing the `36-D` MLP network, separate private `64-D → PCA+Ridge → ≤4-D` path joining at an explicit post-MLP `(+)` output-summation node, `32`-member joint density graphic, and frozen padlock badge.
   - `Agronomic Control` omits the visual 2-stage non-anticipative scenario tree (`a₁` common root → `Rainfall low/high` → two `a₂` nodes → `Temp low/high` → four `a₃` leaves), replacing it with a single text line.
   - `Climate` omits the visual analog branch fan.
3. **Scientific omissions/nuances relative to `candidate-e.png` and `scientific-facts.md`:**
   - **Missing `Climate → Agronomic Control` partition link:** `Climate` connects only to `Spatial Twin` (`weather query`); the direct branch-weight / 7-day rain-then-temperature partition feed from `Climate` into `Agronomic Control` (`controller.py` L27, L43; present in `candidate-e.png`) is omitted.
   - **Dropped `TRAIN 1995–2009` analog-pool provenance:** `candidate-e.png` explicitly labeled `TRAIN 1995–2009 analogs` inside `Climate`; `fig1-architecture.png` omits the `TRAIN 1995–2009` cohort window (and omits `0.05` dropout in `Spatial Twin`, which may remain in the caption).
   - **Undifferentiated OOD fallback types:** `Agronomic Control` states `OOD / empty feasible set → operational dose 0` (`ApplicabilityDomain` / Tier-3 fallback), while `Spatial Twin` omits that **P2 prior-adapter OOD zeroes only the additive correction (`Δy = 0`, reverting to the frozen 36-D backbone)** rather than forcing `dose = 0`.
   - **Replanning cue is text-only:** `"Execute current dose; replan at next observed DVS"` has no visual return cue to updated public observations (`Observed weather` / `DVS + management`).

### 1.3 Visual / Formatting Issues in `fig1-architecture.png`
- **[BLOCKER — Text Collision]:** In the left-middle card (`DVS + management`, `x=0.3, y=1.8, w=2.7, h=1.15`), the 20-pt bold title `"DVS + management"` wraps onto two lines inside a `0.4 in` box and directly overlaps `"Mandatory public history"` (`y=2.35`), rendering `"management"` and `"Mandatory public"` illegible on top of one another. *(Fix: use single-line 18-pt title or widen card / shift body `y` down by `+0.22 in`.)*
- **[MODERATE — Spurious Mid-Bus Arrowheads & Unbridged Crossing]:** `Joint-distribution bus` uses six `arrow()` connectors (`phase8c-build-fig1-native.py` L37), placing triangular arrowheads at intermediate bus bends/junctions `(6.3, 4.55)`, `(2.4, 4.55)`, and `(4.75, 7.8)`. Plain connector segments should be used for trunks/elbows with arrowheads only at terminal card ports. In addition, the vertical bus drop to `Economics` (`x=4.75`) crosses the horizontal `Eco Safety → Agronomic Control` arrow (`y=5.8`) at `(4.75, 5.8)` with identical stroke color and no line-jump/routing separation (route `Economics` tap around `Eco Safety`'s left margin or enter `Economics` top/bottom cleanly without crossing `Eco Safety → Agronomic Control`).
- **[MINOR — Cramped Query Label & Dangling Arrow Glyph]:** `"weather\nquery"` (`11 pt`) is cramped inside the `0.60 in` gap (`x=10.55..11.17`) touching `Spatial Twin`'s right border; `"Executed action only →"` inside `External referee` ends with a dangling inline `→` pointing into blank margin.

### 1.4 Safe Pixel Bounding Boxes on `candidate-e.png` (`1536 × 1024`, 0-indexed)
Coordinates are given as PIL `crop((left, top, right, bottom))` = `(x1, y1, x2, y2)` (and `[x, y, width, height]`), verified pixel-by-pixel against baked-in text, brackets, arrows, and card borders:

1. **Left Wheat Canopy & Soil-Root Profile:**
   - **Pure single-rectangle crop (zero text, zero bracket, zero card borders):**
     `(0, 128, 103, 502)` (`[x=0, y=128, w=103, h=374]`). Stays strictly left of the black input bracket (`x = 104..128, y = 170..356`) and input cards (`x >= 129`), preserving the full wheat stalks/heads and primary root-soil column.
   - **Extended full-soil-mound crop (with top-right white mask):**
     Outer crop `(0, 128, 191, 502)` (`[x=0, y=128, w=191, h=374]`) after filling `(103, 128, 191, 412)` with white `(255, 255, 255)`. Preserves 100% of the wide lower-right soil slope beneath the `Optional LAI` card (`y >= 412`) while stopping cleanly left of the blue `Eco Safety` jumper (`x >= 194`). Zero baked-in text.
2. **Tractor Fertilizer Spreader & Crop Rows:**
   - **Pure single-rectangle crop (zero `"Current dose"` pill/text, zero arrow shafts):**
     `(1110, 668, 1255, 890)` (`[x=1110, y=668, w=145, h=222]`). Captures the red spreader hopper, tractor cab/wheels, fertilizer broadcast beneath the spreader, and underlying green rows, excluding the `"Current dose"` pill + green arrowhead (`x = 998..1109, y = 697..760`) on the left and the outgoing slate arrow (`x = 1255..1290, y = 725..741`) on the right.
   - **Full broadcast fan + full diagonal field sweep (with two small corner masks, zero text):**
     Outer crop `(990, 668, 1277, 890)` (`[x=990, y=668, w=287, h=222]`) after filling top-left `(990, 668, 1110, 768)` (removes `"Current dose"` pill + input arrow above `y = 770` crop rows) and mid-right `(1255, 720, 1277, 745)` (removes 6-px horizontal output arrow shaft while preserving right crop rows `y = 778..855`) with white `(255, 255, 255)`.
3. **External Referee Wheat & Soil Cross-Section Vignette (inside `External WOFOST81-SNOMIN`):**
   - **Pure single-rectangle crop (zero text, zero card/sub-card borders):**
     `(1304, 636, 1522, 789)` (`[x=1304, y=636, w=218, h=153]`). `"SNOMIN"` title pixels terminate at `y = 634`, the soil profile terminates at `y = 789` above the `"Yield"` sub-card (`y > 800`), and `x = 1304..1522` sits cleanly inside the outer card border (`x = 1292` and `x = 1534`). *(Note: background sky gradient inside the card starts near `#DCE8EC` / `#E7F1F5`, so frame with a thin rounded border or feathered top edge if placing on pure white.)*

---

## 2. Figure 2 (`fig2-p1-regimes.png` — P1 Benchmarks & Tier-2 Collapse Diagnostic)

- **Values vs. JSON (`P1`, `Former-Held-Out`, `NASA`, `52` site-years, `Historical`, `cap=40`, `price=1×`, `subsidy=0`): PASS.**
  - **a:** `Neural = 26.73%`, `PPO = 23.01%`, `ExtraTrees = 19.91%`, `Linear = 16.12%`, `Weather = 21.73%`.
  - **b:** `Sensorless = [26.73%, 25.06%, 4.00%]`; `Full-Telemetry = [21.42%, 21.42%, 9.67%]`.
  - **c:** `AU = [63.64, 63.64, 0.00]%`, `US = [41.67, 33.33, 0.00]%`, `NL = [20.00, 20.00, 20.00]%`, `FR = [8.33, 8.33, 0.00]%`, `CN = [0.00, 0.00, 0.00]%`.
  - **d:** `Soft = (895.79, 32.94%)`, `Composite = (895.31, 32.94%)`, `Bare = (975.72, 64.00%)`.
- **Formatting / Visual Issues:**
  - **[BLOCKER — Marker & Label Collision in Panel d]:** `Soft` `(895.79, 32.94%)` and `Composite` `(895.31, 32.94%)` differ by `0.48 EUR ha⁻¹` horizontally and `0.00%` vertically; their circles overlap almost completely and their identical `xytext=(4, 5)` annotations render on top of each other as **`"Sofmposite"`**. `"Bare"` `(975.72, 64.00%)` also crowds the upper-right margin with text extending past the x-axis. *(Fix: expand `xlim(890, 986)`, `ylim(29, 68)`, use distinct markers e.g. open vs. filled or leader arrows placing `"Soft-Coupled"` above-right and `"Tier2-Composite"` below-right.)*
  - **[MINOR — Invisible `0%` Bars in Panel c]:** Zero-height bars (`Archived bare` in AU/US/FR/CN and all three modes in CN) leave blank gaps; add `"0"` labels or a `CN (0/12 structural ceiling)` annotation so `CN` does not look like missing data.
- **Scientific / Semantic Issues:**
  - **[MODERATE — Undisclosed Mode Asymmetry in Panel a]:** `Neural`, `ExtraTrees`, `Linear`, and `Weather` are plotted in **`Soft-Coupled` (`mode='soft'`, bypassing hard-tail masks)** whereas `PPO` (`SensorlessPPO`) uses **hard 3-tier action masks (`mode='tree'`)**. Under matched hard masks (`Tier2-Composite`), `Neural` is `25.06%` (while `ExtraTrees`, `Linear`, `Weather` remain `19.91%`, `16.12%`, `21.73%`). Disclose `Soft-Coupled` vs. masked `PPO` in the panel title/labels (or show `Tier2-Composite` alongside `Soft-Coupled` on `Neural`).
  - **[MODERATE — Missing Statistical Uncertainty & Track Scope]:** Paired differences among repaired controllers in Panel **a** have 95% bootstrap CIs crossing zero (`Neural soft − PPO = +3.72 pp`, `95% CI [-6.18, +13.64] pp`, `Holm p = 1.0`), whereas `Soft-Coupled − Archived bare` is `+22.73 pp` (`95% CI [+14.09, +31.36] pp`, raw two-sided sign `p = 2.4×10⁻⁴`, `Holm p = 1.0` across the 13,512-test family). Panels **c** and **d** should also state `Sensorless` and regional `n` (`AU 11, US 12, NL 5, FR 12, CN 12`; `NL` minimum exact sign `p = 0.0625`), and the caption should note that `Public-Reused` NL (`NASA n=7: 28.57%`; `WUR n=7: 14.29%`) is reported separately and not pooled into the 52-year `Former-Held-Out` mean.

---

## 3. Figure 3 (`fig3-p2-transfer.png` — P2 Causal `t−1` Spatial-Prior Transfer)

- **Values vs. JSON (`P2`, `Sensorless`, `Historical`, `cap=40`, `price=1×`, `subsidy=0`): PASS.**
  - **a (`soft`):** `Former LOYO (40) = [25.56, 27.33, 28.83, 15.67, 18.17]%`; `Public NL LOYO (4) = [25.0, 25.0, 0.0, 25.0, 0.0]%`; `Former LORO (40) = [30.11, 30.11, 31.89, 17.89, 20.94]%`.
  - **b:** `LOYO soft = LOYO composite = [50.0, 66.67, 0.0, 11.11, 0.0]%`; `LORO soft = [75.0, 44.44, 20.0, 11.11, 0.0]%`; `LORO composite = [75.0, 33.33, 20.0, 11.11, 0.0]%`.
  - **c (`soft`):** `LOYO = [87.5, 100.0, 97.5, 87.5, 87.5]%`; `LORO = [0.0, 0.0, 72.5, 0.0, 0.0]%`.
  - **d (`soft`, `Former-Held-Out`, `GLOBAL_EQUAL5`):** `LORO = 0.00 pp [0.00, 0.00] (Holm p = 1)`; `LOYO = -1.78 pp [-13.00, +8.22] (Holm p = 1)`.
- **Scientific Errors:**
  - **[BLOCKER SCIENTIFIC ERROR — Panel c Title Misstates Fallback Semantics]:** Panel **c** is titled **`"Applicability gating; zero is operational fallback"`** above `Accepted prior decisions (%)` where `LORO` is `0%` for `Full64`, `Static3`, `Linear64`, and `ExtraTrees64`. Per `prior_adapter.py` (L44–46) and `joint_model.py` (L46), `prior_accepted = False` (`prior_ood = True`) **zeroes only the additive prior-adapter output correction (`Δy = 0`), falling back to the unadapted frozen world-model backbone** (which continues applying positive N doses and achieves `30.11%` joint compliance in Panel **a**). It does **not** trigger `ApplicabilityDomain` / Tier-3 `operational dose = 0` fallback (`planning.py` L105–106). Retitle Panel **c** to **`"Prior-adapter OOD gating; 0% reverts to backbone (Δy = 0)"`**.
  - **[MODERATE SCIENTIFIC AMBIGUITY — `LORO` Backbone Scope & `region_equal` Mix in Panel a]:** In `Former LORO (40)`, leave-one-region-out partitioning applies **only to the P2 prior adapter**, while the frozen 36-D `TreeMLP` backbone was trained on `TRAIN 1995–2009` across all 5 regions. Because `LORO` rejects `100%` of `Full64`/`Static3` priors (`Δy = 0`), `LORO Full64` (`30.11%`) exactly equals the unadapted 5-region `TreeMLP` backbone on those 40 site-years—explaining why `LORO` (`30.11%`) exceeds `LOYO` (`25.56%`, where accepted adapter shifts slightly reduce compliance). State this explicitly so `LORO > LOYO` is not misread as cross-continent backbone generalization. Also note in Panel **a**/caption that `Former (40)` is a 5-region equal mean (`n=8–9`/region, `NL n=5`) whereas `Public NL LOYO (4)` is single-region `NL` (`n=4`), and that Panels **a, c, d** use `Sensorless Soft-Coupled`.
- **Formatting / Visual Issues:**
  - **[BLOCKER — Complete Curve Occlusion in Panel b]:** `LOYO soft` (red) and `LOYO composite` (blue) are 100% identical across all 5 regions, so the blue curve completely overwrites and hides the red `LOYO soft` curve; `LORO composite` (brown) also overwrites `LORO soft` (green) at 4 of 5 regions (`AU, NL, FR, CN`). *(Fix: plot `composite` with dashed lines `--` and open markers/slight x-jitter so all four series remain visible.)*
  - **[BLOCKER — CI Line Collides with `"Holm p=1"` Text in Panel d]:** For `LOYO / GLOBAL_EQUAL5`, the horizontal blue 95% CI line (`[-13.0, +8.22] pp`) runs directly through the text `"Holm p=1"` at the right edge of the axes. *(Fix: extend `xlim(-15, 13.5)` or place `"Holm p = 1"` vertically offset above each point/CI.)*
  - **[MODERATE — Inverted `LOYO`/`LORO` Colors Across Panels c and d & Code Identifier Labels]:** Panel **c** encodes `LOYO` in **red** and `LORO` in **blue**, whereas adjacent Panel **d** encodes `LORO` in **red** (`y=0`) and `LOYO` in **blue** (`y=1`). Keep `LOYO` red and `LORO` blue in both panels, replace raw identifier `GLOBAL_EQUAL5` with `5-region equal mean (n = 40)`, and add `"0"` labels on the four zero-height `LORO` bars in Panel **c**.

---

## 4. Figure 4 (`fig4-factorial-stress.png` — 180-Cell 4D Climate–Eco–Policy Stress Surface)

- **Values vs. CSV/JSON (`phase8c-180cell-stress-surface.csv`): PASS.** All `180` (`3 × 15 × 4`) rounded compliance percentages (`TreeMLP`, `Sensorless`, `soft`) and bottom-row differences (`Soft-Coupled − SensorlessPPO`, in percentage points) match the locked CSV/JSON outputs.
- **Formatting & Semantic Clarity Issues:**
  - **[MODERATE — Colorbar Saturation Clipping (`vmax=70` & `±50`)]:** Top-row `imshow` clamps at `vmax = 70%` even though **18 `AU` cells equal `73%`, `82%`, or `91%`**, collapsing all `>70%` cells into the same ceiling color without an `extend='max'` indicator (set `vmax=100` or `95`, or `extend='max'`). Bottom-row `imshow` clamps at `[-50, +50] pp`, clipping `idealized_high | NL / 1× / 0 | cap=40` (`+53.33 pp`), and lacks cell numeric annotations so exact pp differences (including the clipped `+53` cell) cannot be read.
  - **[MODERATE — Unexplained Black Subset Rectangles & Dark-Cell Contrast]:** The 90 black cell outlines (`ri % 3 in {0, 1}`, `cap in {25, 35, 50}`) mark the canonical 90-group Phase 5/6 continuity subset, but **nothing on the figure defines what the black outlines mean**, adjacent outlines merge into thick horizontal bars, black strokes disappear against dark-navy `73–91%` cells, and they are absent on the bottom row. Add an explicit legend/note and use high-contrast styling (or clean group brackets).
  - **[MODERATE — Missing Controller Name, Y-Axis Key, Shift Specs, and Panel Letters]:**
    - Top-row column titles (`"Historical"`, `"idealized mid"`, `"idealized high"`) mix capitalization, omit the controller identity (**`Sensorless Soft-Coupled (TreeMLP)`**), and omit the shift definitions (`+1.8°C, 450 ppm` and `+3.5°C, 550 ppm`, idealized shifts rather than CMIP6 projections).
    - Y-axis row strings (`AU / 1× / 0`, `AU / 2× / 0`, `AU / 1× / 50`) need a y-axis label or key defining `Region / N-price multiplier / experimental subsidy (EUR ha⁻¹)`.
    - Add bold panel letters (`a`, `b` or `a–f`) consistent with Figures 2, 3, and 5.

---

## 5. Figure 5 (`fig5-deployment-closure.png` — Backbone, Runtime Interface & Mass-Closure Denominators)

- **Values & Scope vs. JSON: PASS.**
  - **a:** `36-D → 96 → 96 → 3`, `13,155 parameters per neural network`, `Frozen three-seed ensemble; 32 outcome members`, `Private 64-D → PCA/Ridge ≤4-D`, `Additive output correction; no raw-feature broadcast` — exact match.
  - **b:** `Regime` inputs, `Sensorless` vs. `Full-Telemetry` scope, and `"Runtime claims require a separate timing benchmark"` — exact match; **no invented timing or deployment-speed claims**.
  - **c:** `5,928,274` daily records, `Nitrogen = 1.927e-11` (`1.92699e-11`), `Carbon = 2.115e-10` (`2.11458e-10`) kg ha⁻¹ — exact match to `S['mass_new_native']`.
  - **d:** `18,268 scored configurations = 17,747 new + 521 verified reuses`, `1,917 actual unique native simulations + 15,830 exact trajectory cache hits`, `120 future-weather invariance checks passed` — exact match.
- **Formatting / Visual Issues:**
  - **[MODERATE — Bar Annotation Overflows Y-Spine & Mixed Scientific Notation in Panel c]:** `"2.115e-10"` sits above the top end of the left y-axis spine right beneath the panel title; bar labels use raw `e`-notation (`1.927e-11`, `2.115e-10`) whereas y-axis ticks use superscript math (`2 × 10⁻¹¹`, `10⁻¹⁰`, `2 × 10⁻¹⁰`); and the log y-axis starts arbitrarily near `1.75 × 10⁻¹¹` without plotting the pass thresholds (`10⁻¹⁰` kg N ha⁻¹, `10⁻⁹` kg C ha⁻¹). *(Fix: set `ylim(1e-12, 2e-9)`, draw dashed horizontal pass thresholds at `10⁻¹⁰` and `10⁻⁹`, and format annotations as `1.93 × 10⁻¹¹` / `2.11 × 10⁻¹⁰`.)*
  - **[MODERATE — Panel Label `c` Misalignment & Unframed Prose Layout]:** Because `panel()` anchors at `x = -0.10` in axes coordinates, **`c` is shifted rightward over the y-tick labels** instead of aligning vertically with `a` on the left margin (`fig.text` or consistent figure-aligned subpanel labels will fix this). Visually, Panels **a, b, d** are unboxed floating text on blank whitespace (with Panels **a–b** duplicating text from Fig. 1); enclosing **a, b, d** in structured specification/accounting cards or converting **d** into a stacked denominator breakdown bar (`18,268 → 17,747 new [1,917 unique native + 15,830 cache hits] + 521 Phase 8B reuses`) will bring Fig. 5 to top-journal visual density.
- **Scientific / Denominator Clarification:**
  - In Panel **c**, qualify `"5,928,274 checked daily records"` directly on-panel as **`"5,928,274 daily records across 17,747 new configs (1,917 unique trajectories)"`** (noting in the caption that all `18,268` scored configurations total `6,104,146` daily records, and that `5,928,274` includes replayed trajectory-cache-hit configuration records rather than `5.93M` independent physical simulations).
  - Because the file is named `fig5-deployment-closure.png`, ensure both Panel **b/d** (or the figure caption/section heading) explicitly state that **all evaluations are `WOFOST81-SNOMIN` simulator / retrospective / adaptively reused benchmarks, not prospective field deployment or assurance**.

---

## 6. Mandatory Caption Disclosures (Since Standalone Captions Were Not Yet Supplied)

When authoring manuscript/report captions for Figures 1–5, include these non-negotiable scope statements verified from `phase8c-core-statistics.json`:
1. **Evaluation scope:** All results are simulator-based (`WOFOST81-SNOMIN`), retrospective (`P2` causal `t−1`), and adaptively reused (`P1`/`Q8.4`) evaluations—never prospective field trials, operational NWP forecasts, CMIP6 projections, or enacted regional law/subsidy policy.
2. **Cohort & fold separation:** Keep `NASA` vs. `WUR`, `Former-Held-Out` (`P1 n=52`, `P2 n=40`) vs. `Public-Reused NL` (`P1 n=7` per weather source, `P2 n=4`), and `LOYO` vs. `LORO` strictly unpooled; note `NL Former-Held-Out n = 5` (minimum two-sided exact sign `p = 0.0625`) and `CN 0/12`, `FR 1/12` structural high-basal-N ceilings under `Historical cap = 40`.
3. **Multiplicity & intervals:** Bootstrap 95% CIs (`B = 5,000`, farm-year unit after within-case 3-seed averaging) are marginal descriptive intervals, and simultaneous inference uses one `13,512`-contrast Holm exact sign-test family (`Holm p = 1` for headline `P1` controller comparisons and `P2 Full64 − Static3`).
4. **Physical independence denominators:** Disclose together `18,268` scored configurations (`6,104,146` daily rows) = `17,747` new Phase 8C configurations (`5,928,274` daily rows) + `521` hash-verified Phase 8B reuses, backed by **`1,917` unique native `WOFOST81-SNOMIN` trajectories** and `15,830` exact trajectory-cache replays.
