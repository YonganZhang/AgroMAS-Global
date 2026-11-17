# Phase 8D Scientific & Mathematical Consultation: G1 CQR Width vs. Signed Radius and TRAIN Physical Stock Decoding

## Executive Verdict

1. **G1 Sharpness Gate (`conformal_radius` vs. Calibrated Interval Width):** Replacing `signed_radius(Full) < signed_radius(Sensorless)` (`-5.7399` vs. `-6.7813` kg/ha) with **actual calibrated interval width** (`62.5036` vs. `69.5332` kg/ha; effective calibrated half-width `31.2518` vs. `34.7666` kg/ha) is **mathematically justified and corrects a formal Conformalized Quantile Regression (CQR) specification error**. However, because `reports/phase8/phase8d-G1-verdict.json` already executed on Dev (`Dev_accesses: 1`), this must be recorded via an explicit, versioned **Protocol Amendment** on the existing frozen Dev predictions (`0` new Dev accesses, `0` model changes), retaining `G1_FAIL_HALT` in the immutable audit log.
2. **Physical Stock Decoding (`initial-weight-scale` vs. `v2`):** The collapse from **29/30** positive mandatory `(track, region, target)` cells in `phase8d-full-TRAIN-physical-decoding-initial-weight-scale.json` to **24/30** in `phase8d-full-TRAIN-physical-decoding-v2.json` is caused by an **algebraic weight-normalization bug** in `agromas_v8/decoding.py:11`. Within a single region, per-world row counts are constant (`969` in AU/FR/NL/US; `78` in CN), so `w = w / w.mean()` turns `w` into `np.ones(n_fit)`—erasing world-equal weighting, breaking CN vs. non-CN regularization parity by `12.4x`, and slashing effective Ridge regularization per independent world by **`969x`** (`lambda_eff = 10 / 34884 = 2.87e-4` instead of `10 / 36 = 0.278` for `p = 96` features on `12` harvest years).
3. **Representation Limits vs. Auxiliary Backbone Retraining:** Do **not** retrain the `13,155`-parameter frozen `WorldModel` checkpoints yet. In `initial-weight-scale.json`, `raw_OOF_R2 >= +0.2678` in **all 30/30** mandatory cells and `latent_OOF_R2 > 0` in **29/30** cells (only Sensorless `usa_kansas_wichita` `final_soil_C_kg_ha` is `-0.0808`, where fixed `alpha = 10` under-regularizes `p = 96` single-seed features relative to `p_active = 25` raw features on 12 years). Run a **strictly TRAIN-only falsification step** first: restore world-sum weights (`sum(w) = 36` worlds), decode the actual deployed **3-seed frozen ensemble** (`joint_model.py:15-17`), and select Ridge `alpha` via **inner leave-one-harvest-year-out CV strictly inside each outer fold's 12 TRAIN years**. Retrain with a `+485`-parameter (`3.69%`) auxiliary stock head *only* if that clean probe still fails.

---

## 1. G1 Gate: Mathematical Analysis of Signed CQR Radius vs. Calibrated Interval Width

### 1.1 Why `signed_radius(Full) < signed_radius(Sensorless)` Is a Category Error Under CQR

In `agromas_v8/offline_verification.py:9-13, 31-33` and `agromas_v8/scoring.py:29-34`, G1 constructs intervals via **Conformalized Quantile Regression** (Romano et al., 2019), *not* homoscedastic point-residual conformal prediction:

- `summarize_product` (`offline_verification.py:11-13`) extracts the uncalibrated `[0.05, 0.95]` quantiles $[L_0(x), U_0(x)]$ of seasonal N surplus $S_N$ under the `weather_branches x 32` TRAIN OOF residual product measure, with uncalibrated width $W_0(x) = U_0(x) - L_0(x) > 0$.
- `evaluate_summary` (`offline_verification.py:31`) computes signed conformity scores
  $$E_i = \max\big(L_0(x_i) - S_{N,i},\; S_{N,i} - U_0(x_i)\big), \qquad \hat{r} = \operatorname{conformal\_radius}(E, \alpha=0.10),$$
  forming the calibrated 90% prediction interval $\mathcal{C}_{0.90}(x) = [L_0(x) - \hat{r},\; U_0(x) + \hat{r}]$ of width:
  $$W_{\text{cal}}(x) = \max\big(W_0(x) + 2\hat{r},\; 0\big).$$

On Dev (`reports/phase8/phase8d-G1-radius-interpretation.json`), $W_0(x) + 2\hat{r} > 0$ holds pointwise (`macro_calibrated_width == macro_uncalibrated_width + 2 * signed_radius` to $10^{-14}$ precision):

| Track | Macro $W_0$ (kg/ha) | Signed CQR Offset $\hat{r}$ (kg/ha) | Macro $W_{\text{cal}}$ (kg/ha) | Effective Calibrated Half-Width $\frac{1}{2}W_{\text{cal}}$ | Cross-Year Macro Coverage |
|---|---:|---:|---:|---:|---:|
| `Full-Telemetry-mlp` | `73.9834` | `-5.7399` | **`62.5036`** | **`31.2518`** | **`90.78%`** |
| `Sensorless-mlp` | `83.0957` | `-6.7813` | `69.5332` | `34.7666` | `90.37%` |

**Mathematical proof that $\hat{r}_{\text{Full}} < \hat{r}_{\text{Sensorless}}$ is misspecified:**
1. **Translation gauge invariance of CQR:** For any constant $c \in \mathbb{R}$, transforming $(L_0, U_0) \mapsto (L_0 - c, U_0 + c)$ shifts every score $E_i \mapsto E_i - c$ and shifts $\hat{r} \mapsto \hat{r} - c$, leaving the calibrated interval $\mathcal{C}_{0.90}(x)$ and its coverage **identically unchanged** while making $\hat{r}$ arbitrarily negative as base dispersion $W_0$ grows ($+2c$).
2. **Physical cause of $\hat{r} < 0$ and $\hat{r}_{\text{Sensorless}} < \hat{r}_{\text{Full}}$:** `build_stratified_residual_banks` (`scoring.py:63-72`) pools TRAIN OOF residuals across all three climates (`Historical`, `idealized_mid`, `idealized_high`), and `response_tensor` (`joint_model.py:55-63`) convolves 15 TRAIN weather-analog branches with those 32 OOF residuals. On single-climate `Historical` Dev (`2010–2014`), `[q05, q95]` naturally over-covers 90%, so $\hat{r} < 0$ shrinks both tracks inward. Because `Sensorless` masks `lai`, `sm`, and `n_uptake` (`data.py:82`), its TRAIN OOF residuals have larger variance, bloating $W_0$ by `+9.1123 kg/ha` (`83.0957` vs. `73.9834`) and forcing a larger inward CQR correction (`-6.7813` vs. `-5.7399`, i.e., `-13.5625` vs. `-11.4798` kg/ha width shift).
3. **Proper scoring / sharpness ordering:** Only when $W_0(x) \equiv 0$ (point-residual conformal $\hat{\mu}(x) \pm \hat{r}$) does $\hat{r}$ measure half-width. Under CQR ($W_0 > 0$), sharpness subject to calibration (Gneiting & Raftery, 2007) is $\mathbb{E}[W_{\text{cal}}(X)]$. `Full-Telemetry` achieves **both** higher cross-year macro coverage (`90.78%` vs. `90.37%`) and a **`7.0296 kg/ha` (`10.1%`) narrower** calibrated interval (`62.5036` vs. `69.5332` kg/ha), alongside strictly better BSS at all four caps and lower ranking regret (`3.666` vs. `4.757` EUR/ha).

### 1.2 Actual Code-Level Caveats in G1 & Downstream `planning.py` (Audit Disclosure)

While switching the relative sharpness gate to `macro_calibrated_width` is mathematically sound, three structural properties in `offline_verification.py`, `scoring.py`, and `planning.py` should be explicitly bounded in documentation:

1. **Unweighted CQR Quantile vs. Macro-Weighted Coverage (`offline_verification.py:28-33, 46`; `scoring.py:29-34`):**
   `conformal_radius(scores)` takes an **unweighted** quantile across `19,770` Dev rows (`rank = ceil(19771 * 0.9) = 17794`), where high basal N in `china_ncp_luancheng` leaves only `390` legal rows (`1.97%` of rows) vs. `4,845` rows (`24.5%` each) in the other four regions. Coverage, however, is evaluated with `(region, year, stage)`-equal macro `weight` (`20%` per region). Because all `390` Luancheng rows are covered (`1.0`) in both tracks while `17,404 / 19,380` non-CN rows (`323` per `(region, year, stage)`) are covered, `Dev_calibration_set_90pct_coverage` is algebraically forced to the exact same `0.8 * (17404 / 19380) + 0.2 * 1.0 = 0.9184313725490196` in both tracks (`phase8d-G1-verdict.json:43, 116`). Also, `len(scores) + 1 = 19771` treats correlated plan/stage rows within `25` `(region, year)` worlds as exchangeable, though leave-one-Dev-year-out `cross` (`offline_verification.py:32-33`) directly verifies inter-annual macro coverage (`90.78%` Full, `90.37%` Sensorless).
2. **Marginal Pooling Under Negative $\hat{r}$ (`phase8d-G1-verdict.json:47-66, 120-139`):**
   Because $\hat{r}$ is pooled across all 5 regions (marginal rather than region-Mondrian CQR), global inward shrinkage (`-5.74` kg/ha) leaves `australia_wa_perth` under-covered at `75.19%` in `Full-Telemetry` (compensated in the macro mean by `100%` CN and `96.68%` Wichita).
3. **`conformal_upper95` Naming & Safety Floor in `planning.py:43-44, 59`:**
   `upper95 = weighted_quantile(s, w, .95) + regime.radius` (exposed as `conformal_upper95`) adds a **two-sided $\alpha = 0.10$** CQR offset to $q_{0.95}$. Without symmetry assumptions, two-sided 90% CQR bounds one-sided upper exceedance at $\le 10\%$ (matching `epsilon = 0.10`), not $5\%$. Crucially, `planning.py:43-44` protects ecological safety when `regime.radius < 0`: `cvar = upper_cvar(s, w, 0.1) + max(regime.radius, 0.)` never shrinks `CVaR_0.90` downward, and because `upper_cvar(s, w, 0.1) >= weighted_quantile(s, w, 0.9)` holds identically for all discrete non-negative weight vectors (`planning.py:13-21`), `eco_safe` (`max(q90, upper95) <= cap and cvar <= cap`) can never become looser than the uncalibrated `CVaR_0.90 <= cap` (and `q90 <= cap`) barrier.

### 1.3 Governance Protocol Recommendation (No Silent Changes)

- Keep `reports/phase8/phase8d-G1-verdict.json` (`G1_FAIL_HALT`) and `scripts/phase8d-evaluate-g1.py` unmodified as sealed evidence of the literal pre-registered run.
- Record a dedicated, user-approved **Protocol Amendment** file (before reading or running any P1/P2 campaign evaluation) specifying that `Full_radius_strictly_tighter` used a point-conformal formula incompatible with $W_0 > 0$ CQR, and adopting `macro_calibrated_width(Full) < macro_calibrated_width(Sensorless)` (`62.5036 < 69.5332` kg/ha) from `phase8d-G1-radius-interpretation.json` with **zero additional Dev touches** (`Dev_accesses` remains `1`).

---

## 2. Region-Aware TRAIN Physical Stock Decoding: Bugs vs. Representation Limits

### 2.1 Concrete Bugs & Unsupported Assumptions in the Current Diagnostics

1. **Bug 1 — `w = w / w.mean()` in `decoding.py:11` Slashes World-Level Regularization by `969x` and Breaks Regional Parity (`v2.json`):**
   - In `scripts/phase8d-audit-full-physical-decoding[-v2].py:13-15`, `weights[i] = 1 / unique[world_i]`. Across all `225` TRAIN worlds (`59,310` plans $\times 3$ stages $= 177,930$ rows), every world in AU/FR/NL/US has exactly `969` rows (`323` plans $\times 3$ stages) and every world in CN has `78` rows (`26` plans $\times 3$ stages).
   - Inside `fit_region_heads` (`decoding.py:9, 11`), `fit = train & (regions == region)` restricts to **one region at a time**, where `weights[fit]` is constant (`1/969` or `1/78`). Normalizing `w = w / w.mean()` therefore sets **`w == 1.0` on every row**, making `world_equal_weights` a mathematical no-op inside each regional fit!
   - On unit-variance standardized predictors $Z$, `sklearn.linear_model.Ridge(alpha=10.0)` solves $(\hat{\Sigma}_Z + \lambda_{\text{eff}} I_p)\hat{\beta} = \widehat{\operatorname{Cov}}_w(Z, \tilde{y})$ with $\lambda_{\text{eff}} = \alpha / \sum_{i \in \text{fit}_r} w_i$:
     - **World-count scaling (`initial-weight-scale.json`, $\sum w_i = 36$ training worlds = $12\text{ years} \times 3\text{ climates}$):** $\lambda_{\text{eff}} = 10 / 36 = \mathbf{0.278}$ uniformly in all 5 regions (matching the site-year-sum-1 convention documented in `agromas_v8/prior_adapter.py:41-43`).
     - **Row-count scaling (`v2.json` / current `decoding.py:11`, $\sum w_i = n_r$):** $\lambda_{\text{eff}} = 10 / 34,884 = \mathbf{2.87 \times 10^{-4}}$ in AU/FR/NL/US vs. $10 / 2,808 = \mathbf{3.56 \times 10^{-3}}$ in CN (`12.4x` regional penalty asymmetry, and `969x` weaker than world-scale).
   - **Why row-count scaling is statistically invalid here:** Terminal stock targets are identical across all 3 stage rows of a trajectory (`data.py:16-34`), and in SNOMIN (`RCORGAMTT = 0`) organic N/C stocks are virtually invariant across the `323` mineral-N plans within a `(region, year, climate)` world. Thus for the mandatory SOM targets, the effective independent sample size per region-fold is **12 harvest years (`36` correlated climate-worlds)**, not `34,884` rows. Fitting $p = 96$ dense features to `12` years at $\lambda_{\text{eff}} = 2.87 \times 10^{-4}$ inverts near-null singular directions of the 12-year covariance matrix, causing severe OOF overfitting (`Full` Perth orgN/minN: `+0.4138 -> -0.2173`; `Sensorless` Perth: `+0.3706 -> -0.3155`; `Sensorless` Wichita orgN/minN: `+0.0646 -> -0.4940`; `Sensorless` Wichita soilC: `-0.0808 -> -0.6080`; even `Sensorless` Wichita `raw_OOF_R2` collapses from `+0.2887/+0.2678` to `-0.0087/-0.0650`).

2. **Bug 2 — Exact Algebraic Redundancy in `required_positive_targets` (`stock_diagnostics.py:13, 30-31`):**
   In `Wofost81_NWLP_MLWB_SNOMIN` with zero organic N addition, mass balance gives:
   $$\text{final\_organic\_N\_kg\_ha} \equiv N_{\text{org},0}^{(\text{region})} - \text{native\_net\_mineralization\_N\_kg\_ha}.$$
   Because $N_{\text{org},0}^{(\text{region})}$ is constant within each region, within-region standardization (`decoding.py:13`) makes targets `0` and `4` exact sign flips (`-1.0` correlation), explaining why their within-region `OOF_R2` and `RMSE` agree to $10^{-9}$ in every region. The three mandatory targets actually test **two** quantities (`RNH4MINTT` and `RCORGDISTT`), and any unweighted 5-output multi-task loss double-counts N mineralization `2x`.

3. **Bug 3 — Dimensionality Penalty, Single-Seed Readout, and Unweighted Pooled $R^2$ (`phase8d-audit-full-physical-decoding.py:19-23`):**
   - Within a region, `raw` has only **`28` active columns in Full-Telemetry** and **`25` in Sensorless** (`x[:, 10:15]` are structural zeros in `online_features.py:58`; `x[:, 19:22]` are static regional `soil_context`; `x[:, [1,2,4]]` are masked in `data.py:82`), whereas `latent` has **`96` active columns** (`3.4x–3.8x` wider). Applying the same fixed $\alpha = 10$ to $p = 96$ and $p = 25$ on 12 years under-regularizes `latent` relative to `raw`.
   - Line `19` probes only `seed20261115`, whereas the deployed frozen world model (`joint_model.py:15-17`) is the **3-seed ensemble** (`20261115, 20261116, 20261117`).
   - Line `22` computes pooled `r2_score` without `sample_weight=weights` (weighting CN at `1.97%` instead of `20%`), and pooled `OOF_R2 ~ 0.99998` for `final_organic_N` and `final_soil_C` merely reflects static between-region baseline differences (`N_org0`, `C_org0`), not seasonal skill.

### 2.2 Separating Decoder Bugs, Backbone Compression, and Input-Observability Limits

Comparing `raw_OOF_R2` vs. `latent_OOF_R2` under properly world-scaled `initial-weight-scale.json` cleanly separates the three mechanisms:

1. **Decoder Regularization Artifacts:** Account for **all 6** mandatory cell failures introduced in `v2.json`, and contribute to the single remaining mandatory failure in `initial-weight-scale.json` (Sensorless `usa_kansas_wichita` `final_soil_C_kg_ha`: `latent_OOF_R2 = -0.0808` vs. `raw_OOF_R2 = +0.2678`; `final_organic_N` is already `+0.0646`).
2. **True Frozen-Backbone Task Compression (`WorldModel` supervision geometry):**
   - `WorldModel` (`models.py:9-13`, `phase8-fit-world-model.py:24-25`) is trained solely on `[Yield, GrainN, ExecutedN]` (`data.py:32`).
   - On **dose-responsive `final_mineral_N_kg_ha`** (which directly governs `GrainN` and `Yield`), `latent_OOF_R2` **exceeds** `raw_OOF_R2` in 4/5 regions in `initial-weight-scale.json` (`0.824 vs. 0.762` Perth; `0.787 vs. 0.621` FR; `0.742 vs. 0.606` NL; `0.369 vs. 0.329` CN).
   - On **dose-invariant SOM stocks (`final_organic_N`, `final_soil_C`)**, `raw_OOF_R2` exceeds `latent_OOF_R2` in all 5/5 regions (`0.268 vs. -0.081` in Sensorless Wichita `soil_C`). Because `CORGT` (`final_soil_C`) has zero causal feedback onto `[Yield, GrainN, ExecutedN]` in SNOMIN, and `WorldModel.latent` entangles weather covariates with strong within-world `(plan, stage)` dose variations across two `SiLU` layers, a linear readout on 12 years must imperfectly cancel nonlinear dose-weather cross-terms that are linearly orthogonal in `raw`.
3. **True Input-Observability Ceiling (Cannot Be Fixed by Any Decoder or Shared-Backbone Aux Head on 36-D `x`):**
   - `x` (`online_features.py:52-62`, `climate.py:31-37`) encodes only the **last 7 days** of pre-`as_of` weather plus 3 coarse post-`as_of` calendar-third summaries (`[mean_T, sum_P, sum_SW]`), omitting the 4–7 months of autumn/winter weather `[crop_start, as_of - 7d]`.
   - In `Full-Telemetry`, `lai`, `sm`, and `n_uptake` at `as_of` summarize cumulative autumn/winter water and mineralized-N history (`Wichita` `soil_C` `raw_OOF_R2 = 0.6020`). Masking `[1, 2, 4]` in `Sensorless` drops `Wichita` `soil_C` `raw_OOF_R2` to `0.2678`—the linear information ceiling of the observable prefix.
   - Likewise, non-mandatory `native_Nloss_kg_ha` (`NLOSSCUM`) is driven by unobserved pre-`as_of` winter drainage and daily extreme-rainfall threshold events smoothed out by coarse third-of-season sums, yielding `raw_OOF_R2 = -0.6650` in CN (`RMSE = 2.54` kg/ha near-zero episodic leaching) and `-0.0093` in NL. No representation learned from `x` can recover unobserved pre-`as_of` winter drainage.

---

## 3. Recommended Falsifiable TRAIN-Only Next Step

### Step A (Execute First — Zero Backbone Retraining, Zero Dev/P1/P2 Access)

Before considering any retraining of the `72` frozen neural checkpoints, run a strictly nested **TRAIN-only diagnostic** on the existing frozen `WorldModel` checkpoints:

1. **Fix `decoding.py:11` weight scaling:** Normalize regional training weights to **world-count sum** (`w = w / w.sum() * n_train_worlds_in_region`, i.e., `36.0`), eliminating the `969x` row-inflation bug and equalizing shrinkage across CN and non-CN regions.
2. **Select `alpha` via inner harvest-year CV strictly inside each outer fold's 12 TRAIN years:** Within each outer fold (`12` training harvest years) and region, run inner leave-one-harvest-year-out CV over a pre-specified world-unit grid (e.g., `alpha in [10, 25, 50, 100, 200, 500]`, analogous to `P2_anomaly_alpha_grid` in `phase8d-preregistered-protocol.json:20-26`) for both `latent` and `raw`, so `p = 96` is not forced to share the uncalibrated `p = 25` penalty.
3. **Match the deployed 3-seed representation (`joint_model.py:15-17`):** Average OOF stock predictions across the three registered frozen seeds (`20261115, 20261116, 20261117`)—each fitted with inner-LOYO `alpha` on its own outer fold—and report world-weighted `r2_score(..., sample_weight=weights)`.

**Falsification Gate (TRAIN-only):**
- **If all 30/30 mandatory cells (`final_organic_N`, `final_soil_C`, `native_net_mineralization_N` across 5 regions $\times$ 2 tracks) satisfy `latent_OOF_R2 > 0`:** The single `-0.0808` cell in `initial-weight-scale.json` was a fixed-`alpha`/single-seed high-dimensional readout variance artifact. **Keep the existing frozen `13,155`-parameter models and one-shot Dev G1 calibration unchanged.**
- **If Sensorless `usa_kansas_wichita` `final_soil_C_kg_ha` remains $\le 0$ despite `raw_OOF_R2 > 0`:** Frozen `[Yield, GrainN, ExecutedN]` representation compression of `CORGT` is empirically confirmed. At that point, choose between (i) documenting this bounded Sensorless-Kansas `CORGT` representation limit transparently (preferred if stock decoding is an offline mechanistic interpretability audit rather than an online controller input, per `decoding.py:1`), or (ii) executing user-authorized Step B.

### Step B (Conditional Fallback Only — Shared-Backbone Auxiliary Stock Head, `+485` Params)

If user-authorized shared-backbone training (`WorldModel` + training-only `nn.Linear(96, 5)`, `+485` params = `+3.69%` of `13,155`) is pursued after Step A fails, three mathematical traps in `scripts/phase8-fit-world-model.py` **must** be prevented, all selected exclusively via **inner TRAIN harvest-year folds**:

1. **Never standardize `final_organic_N` or `final_soil_C` globally across regions (`phase8-fit-world-model.py:24-25`):** Static regional baselines (`N_org0[r]`, `C_org0[r]`) account for `>99.9%` of global variance and caused within-region `R2 = -26,340` in Phase 8B (`reports/phase8/phase8b-full-TRAIN-physical-decoding.json:51`). Standardize auxiliary targets **per-region using only that fold's TRAIN years** (equivalently predicting seasonal deltas $-\Delta N_{\text{org}}, -\Delta C_{\text{org}}$), and weight the algebraically identical pair `(final_organic_N, native_net_mineralization_N)` by `0.5` each (or fit 4 non-redundant outputs) so N mineralization is not double-counted.
2. **Enforce world-equal loss weighting and guard against `native_Nloss` negative transfer:** Uniform row sampling (`phase8-fit-world-model.py:33-35`) under-weights CN by `12.4x` (`78` vs. `969` rows/world), and forcing the shared 96-D trunk to chase unobservable CN/NL `native_Nloss_kg_ha` spikes (`raw_OOF_R2 = -0.665` in CN) risks degrading primary `[Yield, GrainN, ExecutedN]` calibration and regret. Select auxiliary weight $\lambda_{\text{aux}}$ (and whether `native_Nloss` receives lower/zero aux weight) strictly on **inner TRAIN year folds** subject to non-degradation of inner-TRAIN primary surplus Brier and ranking regret.
3. **Full re-freeze & explicit Dev accounting:** Shared-backbone retraining alters `WorldModel` weights (`models/phase8-v8/`), requiring new `fold = 0..4` and `fold = -1` checkpoints, recomputed TRAIN OOF residual banks (`joint_model.py:17, 25`), and a re-run of Dev G1/G2 calibration explicitly logged as **`Dev_accesses: 2` (reused Dev verification)** rather than first-touch calibration.

---

## Bounded Uncertainties

- **Without running models**, we cannot state whether inner-LOYO `alpha > 10` + 3-seed averaging alone lifts Sensorless `usa_kansas_wichita` `final_soil_C_kg_ha` from `-0.0808` above `0` (Step A), only that `raw_OOF_R2 = +0.2678` proves linear signal exists in the Sensorless inputs and that `initial-weight-scale.json` already passed `29/30` cells at fixed `alpha = 10` on a single seed.
- **Regional CQR heterogeneity:** Adopting `macro_calibrated_width` resolves the CQR sharpness paradox without touching Dev again, but does not alter the marginal (region-pooled) nature of `conformal_radius`, under which `Full-Telemetry` Dev cross-year coverage is `90.78%` macro yet `75.19%` in `australia_wa_perth` (`phase8d-G1-verdict.json:48`). Any prospective guarantee claim remains bounded by `offline_verification.py:46` (`"fixed reused Dev cross-year calibration diagnostic,not prospective assurance"`).
