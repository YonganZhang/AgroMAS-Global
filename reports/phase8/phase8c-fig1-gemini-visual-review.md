# Visual & Scientific QA: `candidate-e.png`

**Reviewed files:**
- Candidate image: `reports/phase8/figures/fig1-candidates/candidate-e.png`
- Ground-truth contract: `reports/phase8/figures/fig1-candidates/scientific-facts.md`

## Verdict

`candidate-e.png` is **not usable as a raw raster figure**, primarily due to baked-in connector hallucinations and missing query/input links. However, **its macro-layout is sound and no new layout generation is needed**: an **editable native vector reconstruction** preserving Candidate E's five-panel + external-referee geometry **will suffice**, provided **connector fixes are paired with minor inline text/badge refinements** (connector re-routing *alone* with frozen verbatim text would leave several contract nuances ambiguous).

---

## Verification of Core Architectural Requirements

1. **Five typed numerical specialists (no LLM / humanoid / agent-count claims): PASS**
   - Five distinct non-anthropomorphic modules are shown: `Spatial Twin`, `Climate`, `Eco Safety`, `Economics`, and `Agronomic Control`, grounded with wheat/soil/spreader imagery and zero LLM chat bubbles or multi-agent superiority claims.
2. **36-D neural backbone + private 64-D PCA/Ridge `<=4-D` additive OUTPUT correction: PASS (internal topology) / PARTIAL (conditioning & P1/P2 scope)**
   - Inside `Spatial Twin` (marked frozen via a padlock icon), `36-D inputs` feed `36-D PyTorch MLP` (`13,155 parameters`), while `64-D AlphaEarth` → `PCA + Ridge` → `<=4-D adapter` routes along an explicit `Output correction` line into a post-MLP `(+)` summation node before `32 joint outcome members` (`Yield, grain N, executed N` and `Algebraic surplus and NUE`).
   - Raw 64-D features remain strictly enclosed within `Spatial Twin`'s dashed boundary, and the adapter is correctly depicted as an **additive output correction** rather than an input concatenation.
3. **Three actual actions `a1/a2/a3` with rain-then-temperature information sharing: PASS (tree structure) / MINOR OMISSION (horizon label)**
   - `Agronomic Control` depicts a single common-root `a₁` branching on `Rainfall low` / `Rainfall high` into two conditional `a₂` nodes, each branching on `Temp low` / `Temp high` into four conditional `a₃` leaf nodes, outputting a single `Current dose`.
4. **External `WOFOST81-SNOMIN` one-way action/referee boundary: PASS**
   - `Agronomic Control` → `Current dose` → tractor spreader → `External WOFOST81-SNOMIN` is strictly one-way. Zero arrows feed hidden soil states, future realized weather, or season-end physical outcomes back into the online decision team.

---

## Supported Connector, Scientific, and Legibility Defects

### 1. Connector & Topological Defects (Must Fix)

- **Dangling mandatory field inputs on the left (`Observed weather`, `DVS and management history`):**
  - A black bracket joins the *left* edges of all three input cards, but **nothing exits the right edges** of `Observed weather` or `DVS and management history`. The `36-D inputs` arrow into `36-D PyTorch MLP` exits *only* the right edge of `Optional LAI, SM and plant N uptake`. Visually, either only optional telemetry enters the MLP or mandatory weather/DVS must flow backward through the left bracket and through the optional sensor card. Solid (mandatory Sensorless) vs. dashed (optional Full-Telemetry) input status is also inverted/lost.
- **Missing candidate-plan and climate-branch conditioning into `Spatial Twin`:**
  - `Spatial Twin` has outgoing blue arrows only; **neither `Agronomic Control` (candidate schedules `a₁, a₂, a₃`) nor `Climate` (conditional analog weather branches) connects into `Spatial Twin`**. As drawn, `Spatial Twin` looks like an unconditioned open-loop feed-forward encoder rather than a world model queried across candidate dose schedules and climate branches.
- **Duplicate parallel blue arrow into `Eco Safety` (raster hallucination):**
  - Below `Spatial Twin`, two separate parallel horizontal blue lines run leftward from the center junction above `Agronomic Control` and both bend down to terminate in **two side-by-side downward blue arrowheads** on the top border of `Eco Safety` (one continuation of the bus from `32 joint outcome members`, plus a redundant upper parallel bridge).
- **Misrouted left-margin jumper from `Eco Safety` to `Economics`:**
  - `Economics` does not tap the `Spatial Twin` output bus cleanly; instead, an unlabeled slate-blue line exits the **mid-left wall of `Eco Safety`**, wraps down the outer-left margin, and arrows into the **left wall of `Economics`**, either falsely implying an out-the-back `Eco Safety → Economics` dependency or misattaching a shared bus.
- **`Climate` output arrow merges into its own box border:**
  - The green arrow entering the upper-right shoulder of `Agronomic Control` visually peels off `Climate`'s green perimeter stroke at its bottom-left corner rather than originating from a distinct port.

### 2. Scientific Contract Omissions & Ambiguities (`scientific-facts.md`)

- **Unconditional P2 spatial path & missing applicability/OOD fallback:**
  - `64-D AlphaEarth` → `Output correction` is drawn with solid always-on connectors, without noting that **P1 uses weather/static soil only**, **P2 uses retrospective causal `t-1` annual embeddings (`LOYO`/`LORO`)**, and **OOD or an empty hard-feasible set returns operational `dose = 0` (never counted as compliance)**.
- **Objective-mode visual grouping inside `Agronomic Control`:**
  - Placing `Hard composite`, `Soft composite`, and `Archived bare` directly beneath the single formula bar `Partial profit + 200 P(active joint) - 200 distance` suggests all three share that objective. Per `scientific-facts.md`, `Archived bare` uses partial profit only, `Hard composite` enforces 3-tier masks + composite ranking (`- 200 active distance`), and `Soft composite` bypasses hard-tail masks (not physical outcomes). Also, nodewise DP's non-guaranteed global optimality under coupled chance/CVaR is unstated (keep labels free of "optimal" claims).
- **Missing rolling-horizon replanning cue:**
  - `Current dose` shows single-stage execution, but there is no annotation/arrow indicating **replanning at the next observed DVS stage** from updated public weather/management prefix (distinct from the isolated post-season referee).
- **Incomplete qualifier labels across specialist/referee boxes:**
  - `Climate` / tree boxes omit **`first 7-day`** on the revealed rain/temperature partitions, **"not operational NWP"**, and non-revelation of analog identity or late-season weather.
  - `Eco Safety` (`0 <= surplus <= cap`) omits **upper-tail checks** and cap levels (`25/35/40/50 kg N/ha`).
  - `Economics` (`Price and subsidy`) omits **partial fertilizer-management budget**, `1x/2x` N-price multipliers, and the **`experimental`** qualifier on green subsidies.
  - `External WOFOST81-SNOMIN` lists `Yield`, `Native N loss`, and `Daily C and N closure`, omitting realized **`Surplus` and `NUE`** (needed for true joint-compliance evaluation).

### 3. Typography & Visual Polish Defects

- **Raw ASCII math operators:** `<=4-D adapter`, `0 <= surplus <= cap`, `0.5 <= NUE <= 0.9`, and `- 200 distance` use plain ASCII `<=` and hyphens `-` instead of `≤` and `−`; `TRAIN1995-2009` lacks a space and en-dash (`TRAIN 1995–2009`).
- **Cramped label placement:** `36-D inputs` is squeezed tightly between the bottom border of the `64-D AlphaEarth` card and the black input routing line.
- **Container & icon artifacts:** `Agronomic Control` has an awkward pinched-waist/mushroom-base silhouette around the bottom three mode pills; the `64-D AlphaEarth` sub-box uses pseudo-topographic terrain art (stylized embedding/grid layers in vector rebuild will better honor the "no fabricated maps" rule); vertical connectors between AlphaEarth tiles, `PCA + Ridge`, and `<=4-D adapter` are double tick bars without directional arrowheads.

---

## Would Minor Connector Fixes in an Editable Native Reconstruction Suffice?

**Yes — with inline label updates included in the same native pass:**

1. **Connector fixes alone (if box text were kept 100% verbatim) would fix topology but leave minor scientific over-implications** (always-on AlphaEarth in P1, undifferentiated `Archived bare` vs. `Hard/Soft composite` formulas, missing `dose = 0` non-compliant fallback, missing `7-day` partition horizon, and missing realized `Surplus/NUE` on the referee).
2. **In an editable native reconstruction where text, strokes, and connectors are naturally co-authored, Candidate E's exact layout blueprint suffices without redesign:**
   - **Re-route left inputs:** Join `Observed weather` + `DVS and management history` (solid) and `Optional LAI, SM, plant N uptake` (dashed) from their *right* edges into `36-D inputs`.
   - **Close the world-model query interface:** Add conditioning inputs from `Climate` (analog scenarios) and `Agronomic Control` (candidate `a₁, a₂, a₃` schedules) into `Spatial Twin`.
   - **Clean the `Spatial Twin` output bus:** Replace the double blue arrow into `Eco Safety` and the left-wall `Eco Safety → Economics` jumper with one clean 32-member distribution bus feeding `Eco Safety`, `Economics`, and `Agronomic Control`.
   - **Tighten badges & math glyphs:** Convert `<=` to `≤`, badge the `64-D AlphaEarth` adapter as `P2 causal t−1 (LOYO/LORO; OOD → dose 0)`, label `7-day rain` / `7-day temp`, add `upper-tail; cap 25/35/40/50`, mark subsidies `experimental`, differentiate the three objective pills + `dose = 0 (non-compliant)` fallback, note stagewise causal replanning, add `Surplus & NUE` to `External WOFOST81-SNOMIN`, and smooth `Agronomic Control` into a clean geometric container.
