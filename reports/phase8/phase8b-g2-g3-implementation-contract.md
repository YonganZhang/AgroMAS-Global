# Frozen implementation choices before any new P1/P2 policy evaluation

G1 passes both registered architectures/tracks. Select the first registered `mlp` architecture; do not select on P1/P2 performance. No new NN architecture families. Q8.4/90-cell surface/paper figures remain unstarted.

## Non-anticipativity
Use all TRAIN1995–2009 full-season historical analog branches with their causal prefix weights. For future stage2 reveal only a TRAIN-median bin of the first7 future days' rainfall; for future stage3 reveal a nested median bin of first7 days' temperature. Those7days are known by the earliest next weekly decision, even if a stage is skipped. This deliberately conservative coarsening never reveals an analog-year identity, full remaining-weather path, or late-season weather. Full remaining-season descriptors remain uncertain across multiple analogs in every information node. At actual next stage replan from the newly observed prefix. All tree children share each information-node action. Daily DVS/14-day/220kg guards execute externally. Terminal-surrogate schedule forecasts do not assume exact future execution.

Weighted backward DP over nominalGRID schedules: current action shared across every branch, stage2 actions shared within rainfall nodes, stage3 actions shared within nested rainfall/temperature nodes. Each branch has32 conditional joint residual members around three-seed-mean predictions. Each node deterministically resamples32 joint branch/residual pairs using the exact G1 systematic-CDF recipe; the branch tensor is not480 independent calibration samples. Use those32 pairs for surplus quantile/CVaR and expected profit. Nested conditional constraints use the same declared tier function. Tier1 means active constraints, never observed compliance. Tier3 is always operational zero. Monolithic and modular five-agent forms share numerical tables and must produce identical decisions; no benefit is attributed to agent count itself.

## Matched controls
New Pure-Weather DL uses same registered MLP/config/seeds/folds with staticsoil channels19:22 zeroed, no new architecture. Static-Soil DL is the G1 Sensorless backbone. Linear and ExtraTrees use identical full-schedule inputs, folds and conditional residual construction. Sensorless PPO uses only causal sensorless prefix + frozen candidate statistics, TRAIN book rewards, seeds4/17/29,151552 decision steps/seed, same64x64/MaskablePPO hyperparameters as frozen v6; final fixed-budget checkpoint, no evaluation selection. Learned-model training remains TRAIN-only. Calibration controls are fixed before any P1 evaluation; no primary G1 refitting or retuning.

P1 five-region NASA>=2015:52Former-Held-Out and7Public-Reused kept separate; compare Full-Telemetry and Sensorless tracks. Legacy v6 Full/PPO and Phase4-Forest/N2 references are labelled frozen transfers with their original limitations; historical21.8788/23.5657/40/28.57 numbers remain historical references, never claimed reproduced without actual matching. WUR real-year>=2015 data only runs as a separate Public-Reused Dutch weather stratum (2015–2021 if complete); its v2 common-mechanism transfer setup is not an exact original-paper replication. Source/weather/budget differences disclosed. Do not pool WUR with NASA52.

## P2 retrospective nested crossfit
Only after G1 and frozen G2 protocol:44site-years(40Former+4PublicNL). OuterLOYO/LORO transformations and lowrank<=4/L2=10 adapter fit only outer-training labels. Frozen backbone. Inner grouped crossfit calibrates the adapter without outer labels. Lowrank prior inputs stay inside numerical encoder; public requests use opaque IDs. Match residual-recalibration label budget for controls: staticsoil3prior and causal-weather prior adapters use same outer/inner folds and shrinkage. Full64 compares to static, pureweather, linear andtree controls; Phase7zero is a labelled historical interface reference. P2 may use already-exposed outer-training physical labels per explicit epoch27 approval, but never feed those labels into P1 selection.

## G3 limited targeted regimes
A: common five-agent tree, Linear/ExtraTrees/PureWeather/StaticSoil/Full64(onP2).
B: independent bit-parity assertion for monolithic vs modular with identical unbundled constraints; tree vs soft environmental penalties, frozen full-season OpenLoop343, and greedy current dose with frozen future continuation. Soft ablation removes hard environmental targets by design, retains structural guards and reports its active-constraint tiers explicitly.
C: Climate removal only on TRAIN-quantile-defined wet/dry years; Eco removal only at caps25/35, retaining NUE; Econ removal only at2xNprice/TRAIN-selectedgreen, retaining surplus guard. No90cellcrossproduct. Price/subsidy are experimental controls, not actual enacted policies. Never silently replace null TRAIN subsidy with a claimed successful intervention.

## Evaluation integrity
Freeze all policies, data roles, observation schemas, objective coefficients, fold protocol, targeted-regime lists and source hashes before any new heldout policy run. Single locked native WOFOST campaign; deduplicate bit-identical policy/world/context runs by prediction/code hash instead of replaying physics. Each distinct realized episode has exact daily N/C audit. Never use final physical books as online oracles. P2 inner/outer training uses separately typed TRAIN-fold records; evaluation adapters cannot access their outer-held labels. No post-outcome tuning.

Report pooled and equal-region metrics, all5regions, Dutch sources separately, fallback1/2/3, profit/NUE/S/Nloss, feasibility ceilings as historical context, bootstrap5000seed20261115+exactsign/Wilcoxon onNL/US/AU. Thirty actual online-action future-weather perturbations plus raw64 quarantine and source proof. External result/code council and clean main/master merge/cleanup required at final closure.

P2 adapter protocol frozen before reading P2 outcome labels

For each LOYO/LORO outer split, all transformations, low-rank axes, residual
heads, prior applicability thresholds and conformal radii are fitted using the
outer training site-years only. Each site-year has total fitting weight one.
The frozen P1 numerical backbones are never updated. AE64 and weather use at
most four PCA axes, static soil at most three. Standardization is weighted;
constant coordinates are suppressed. Ridge alpha is10 with no search. Head
features are PCA axes, axes times nominal remaining/committed N divided by220,
and axes times stage divided by3. All three output residuals are standardized
before fitting. Inner year-group cross-fitting calibrates the projected K32
surplus distribution. No outer test labels enter calibration or OOD thresholds.

Equal recalibration-label controls are MLP+AE64, MLP+static3,
WeatherNN+causal weather, Linear+AE64 and ExtraTrees+AE64. Raw satellite data
never enters specialist messages. The annual t-1 product is admissible only
after its calendar-year end strictly precedes the decision date; otherwise the
unadapted frozen backbone is used. Product release availability is not claimed.
Prior OOD uses outer-training99th-percentile reconstruction and standardized
latent-distance thresholds. Rejected priors fall back to the frozen backbone
with a conservative max(base,inner-crossfit) radius, rather than claiming that
rejection is evidence for compliance. Backbone OOD still triggers Tier3zero.
This is retrospective nested cross-fitting, not untouched prospective testing.

Open-loop execution detail fixed before native evaluation: the initial nominal
schedule never re-optimizes. Later causal observations may trigger the identical
Tier1/2/3 safety rule on its fixed remaining proposal versus operational zero.
The safety rule may suppress a planned dose; initial Tier labels are never
reused as fresh compliance evidence. This separates planning from the common
execution safeguard and is reported as a guarded frozen proposal.
