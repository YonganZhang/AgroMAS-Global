# Phase8B G1–G3 core experiments

Status: actual core campaign completed; scientific comparisons below are descriptive/exploratory. Q8.4 and manuscript figures/TeX/PDF remain unstarted.

## Realized verdict

G1 passes its registered prediction gates, but G2 does not support the proposed
policy-superiority claim. On52Former-Held-Out NASA site-years, five-region equal
joint compliance is9.67%for Full TreeMLP versus20.54%for the matched legacy PPO
transfer; Sensorless TreeMLP is4.00%versus23.01%for matched Sensorless PPO.
These are matched current transfers, not reproductions of historical v6rates.
The Full and Sensorless tree use zero Tier1decisions in this stratum;76.28%of
decisions use relaxed Tier2and23.72%operational Tier3. Realized joint success
must never be inferred from a fallback label. Soft penalties reach26.73%in the
same Sensorless stratum; the hard coupling is not an established benefit.

P2LOYO Full64 gives10.22%versus6.22%Static3,8.00%Weather and12.00%ExtraTrees64
on the40Former cases. The3-region paired Full64-minus-Static3 effect is+6.67pp,
95%bootstrapCI[-13.33,+26.67]pp, with only3non-tied pairs out of22(19ties, exact signp=1.0); it does not establish a robust spatial gain.
P2LORO Full64 andStatic3 both give4.00%, with every spatial/static prior rejected
asOOD. There is no demonstrated spatial-prior transfer in LORO. Historical
Phase7zero is a lower interface reference, not proof of superiority over the
strongest matched controls. Full results and all regions remain below.

G3 completes the preregistered numerical contrasts and exact monolithic parity;
it does not demonstrate an agent-count advantage. The recursion implements
nodewise conditional Tier decisions. Nonanticipativity is tested, but global
optimality under coupled non-additive chance/CVaR constraints is not proved;
this limitation and the observed fallback collapse preclude an exact globally
optimal hard-control claim. No post-outcome tuning or new native scoring pass
was used to improve these negative results. Q8.4 remains unstarted.

Bootstrap intervals are marginal exploratory intervals. No joint-compliance contrast survives the full512-test-family Holm correction. There are21Holm-significant non-joint contrasts:7higher partial-profit,7lower native-N-loss and7higherNUE>0.90rates for the primary relative to the specified controls. The last group is more soil mining, so these trade-offs do not establish joint feasibility or overall superiority. For example, the
Sensorless3-region mean joint gap versusPPO is-28.91pp, CI[-40.98,-17.68]pp,
raw exact signp=.0004883but Holm p=.23975. NL n5cannot yield exact two-sided
significance below.0625even with all five non-tied differences aligned.

## Scope and data roles

Five online specialists share a frozen numerical response tool. External WOFOST81-SNOMIN alone supplies native mechanistic outcomes and daily C/N ledgers. This is a simulator study, not field validation or an operational weather forecast. Agent count has no causal performance claim; the identical monolithic numerical controller is bit-for-bit equivalent.

P1 uses TRAIN1995–2009, exposed Dev2010–2014 and an adaptive-reused temporal benchmark. Report52 Former-Held-Out and7 Public-Reused NASA site-years separately. WUR7 public historical site-years use WUR CSV observed weather, a NASA TRAIN numerical backbone/forecast model and NASA TRAIN climate analog branches. The climate module retains its imported original regional_weather alias; only engine construction is patched to WUR. This is a limited nine-policy weather-transfer stratum, not the full P1 control/ablation matrix or exact original CEA replication. See phase8b-WUR-source-binding-proof.json. NASA and WUR are never pooled.

Historical Phase7 Satellite_bridge remains0%on each corresponding40Former/4Public cohort in both schemes, with actual subset counts saved in phase8b-Phase7-historical-cohort-reference.json; its imputation interface is not the current matched world-model policy. P2 is explicitly retrospective nested LOYO/LORO cross-fitting:44 site-years per scheme,40 Former-Held-Out and4 Public-Reused NL. Outer held labels never fit transformations, priors, regression heads, applicability thresholds or inner calibration. LOYO and LORO are separate analyses, not88 independent farms. The frozen P1 backbone is not updated and was trained on all five regions in1995–2009; LORO therefore tests adapter transfer conditional on that backbone, not whole-system zero-shot regional generalization. Annual t-1 vectors are admissible only after their calendar-year end precedes the decision date; no historical product release availability is claimed.

## G1 actual pass and limits

Both registered13155-parameter architectures passed all prespecified G1 gates in both information tracks. First-registered MLP remained primary. No Dev-driven architecture/hyperparameter/checkpoint search followed. Exact G1 implementation is archived in phase8b-G1-source-snapshot/.

|Track/model|90% crossyear Dev coverage|Within-prefix regret EUR/ha|ExtraTrees regret EUR/ha|
|---|---:|---:|---:|
|Full-Telemetry-mlp|89.46%|3.726|8.184|
|Full-Telemetry-residual-mlp|90.29%|4.696|8.184|
|Sensorless-mlp|90.82%|4.914|8.544|
|Sensorless-residual-mlp|89.76%|5.421|8.544|

See PHASE8B_G1_GATE_REPORT.md and phase8b-G1-verdict.json for full BSS against both TRAIN climatology and fold-matched ExtraTrees at all four caps. Coverage is retrospective leave-one-Dev-year-out calibration verification, not prospective or regionwise coverage. Conditional TRAIN OOF residuals use realized TRAIN scenario descriptors; they are not operational forecastOOF. The literal BSS event is S_N<=cap; two-sided surplus and joint NUE compliance are reported separately.

TRAIN physical decoding is an association audit only. High global reconstruction can reflect region structure; within-region N-loss decodability must be read from the full TRAIN audit. It does not prove causal understanding of64 spatial axes.

Primary MLP full-TRAIN N-loss decoding is weak within regions:

|Track|Global latent R2|Global raw-feature R2|AU|CN|FR|NL|US|
|---|---:|---:|---:|---:|---:|---:|---:|
|Full-Telemetry-mlp|0.379|0.415|0.076|-67.036|-1.640|-0.266|-0.908|
|Sensorless-mlp|0.388|0.393|0.009|-54.549|-0.864|-0.307|-0.322|

These are outer-TRAIN-year association diagnostics over177930legal stage-plan rows. Negative within-region R2, especially under small regional target variance, rules out a claimed general mechanistic N-loss explanation. The side audit was performed, not declared a successful physical identification test.

## G2 and G3 realized metrics

|Benchmark|Source|Cohort|Scheme|Track|Policy|Cap|N price multiplier|Subsidy EUR/ha|Site-years|Region-equal joint|Pooled joint|Profit EUR/ha|Native N loss kg/ha|
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|P1|NASA|Former-Held-Out|none|Full-Telemetry|DVS-N2|40.0|1.0|0.0|52|19.91%|19.23%|882.17|23.425|
|P1|NASA|Former-Held-Out|none|Full-Telemetry|LegacyV6Full|40.0|1.0|0.0|52|20.21%|19.23%|890.84|23.073|
|P1|NASA|Former-Held-Out|none|Full-Telemetry|LegacyV6PPO|40.0|1.0|0.0|52|20.54%|19.23%|902.35|22.558|
|P1|NASA|Former-Held-Out|none|Full-Telemetry|N2-PA-calendar|40.0|1.0|0.0|5|20.00%|20.00%|1409.20|42.832|
|P1|NASA|Former-Held-Out|none|Full-Telemetry|N2-PA-matched|40.0|1.0|0.0|5|0.00%|0.00%|1445.10|40.489|
|P1|NASA|Former-Held-Out|none|Full-Telemetry|Phase4-Forest-transfer|40.0|1.0|0.0|5|40.00%|40.00%|1482.74|40.960|
|P1|NASA|Former-Held-Out|none|Sensorless|SensorlessPPO|40.0|1.0|0.0|52|23.01%|21.79%|887.50|23.375|
|P1|NASA|Former-Held-Out|none|Sensorless|TreeExtraTrees|40.0|1.0|0.0|52|0.00%|0.00%|970.74|20.884|
|P1|NASA|Former-Held-Out|none|Sensorless|TreeLinear|40.0|1.0|0.0|52|0.00%|0.00%|858.00|20.323|
|P1|NASA|Former-Held-Out|none|Full-Telemetry|TreeMLP|40.0|1.0|0.0|52|9.67%|5.77%|975.03|20.840|
|P1|NASA|Former-Held-Out|none|Sensorless|TreeMLP|25.0|1.0|0.0|52|0.00%|0.00%|975.72|20.797|
|P1|NASA|Former-Held-Out|none|Sensorless|TreeMLP|35.0|1.0|0.0|52|4.00%|1.92%|975.72|20.797|
|P1|NASA|Former-Held-Out|none|Sensorless|TreeMLP|40.0|1.0|0.0|52|4.00%|1.92%|975.72|20.797|
|P1|NASA|Former-Held-Out|none|Sensorless|TreeMLP|40.0|1.0|50.0|52|4.00%|1.92%|977.08|20.805|
|P1|NASA|Former-Held-Out|none|Sensorless|TreeMLP|40.0|2.0|0.0|52|0.00%|0.00%|841.71|20.483|
|P1|NASA|Former-Held-Out|none|Sensorless|TreeMLP-extreme-subset|40.0|1.0|0.0|31|0.00%|0.00%|963.85|21.705|
|P1|NASA|Former-Held-Out|none|Sensorless|TreeWeather|40.0|1.0|0.0|52|8.00%|3.85%|973.51|20.814|
|P1|NASA|Former-Held-Out|none|Sensorless|greedy-frozen|40.0|1.0|0.0|52|8.00%|3.85%|967.35|20.651|
|P1|NASA|Former-Held-Out|none|Sensorless|open-loop|40.0|1.0|0.0|52|8.00%|3.85%|972.43|20.640|
|P1|NASA|Former-Held-Out|none|Sensorless|remove-climate|40.0|1.0|0.0|31|0.00%|0.00%|954.71|22.280|
|P1|NASA|Former-Held-Out|none|Sensorless|remove-eco|25.0|1.0|0.0|52|3.48%|3.85%|904.68|22.294|
|P1|NASA|Former-Held-Out|none|Sensorless|remove-eco|35.0|1.0|0.0|52|12.79%|11.54%|904.68|22.294|
|P1|NASA|Former-Held-Out|none|Sensorless|remove-econ|40.0|1.0|50.0|52|5.82%|3.85%|963.53|21.082|
|P1|NASA|Former-Held-Out|none|Sensorless|remove-econ|40.0|2.0|0.0|52|5.82%|3.85%|781.84|21.082|
|P1|NASA|Former-Held-Out|none|Sensorless|soft|40.0|1.0|0.0|52|26.73%|26.92%|895.79|22.513|
|P1|NASA|Public-Reused|none|Full-Telemetry|DVS-N2|40.0|1.0|0.0|7|0.00%|0.00%|1440.62|36.520|
|P1|NASA|Public-Reused|none|Full-Telemetry|LegacyV6Full|40.0|1.0|0.0|7|0.00%|0.00%|1437.41|36.556|
|P1|NASA|Public-Reused|none|Full-Telemetry|LegacyV6PPO|40.0|1.0|0.0|7|33.33%|33.33%|1449.35|36.407|
|P1|NASA|Public-Reused|none|Full-Telemetry|N2-PA-calendar|40.0|1.0|0.0|7|14.29%|14.29%|1412.13|40.776|
|P1|NASA|Public-Reused|none|Full-Telemetry|N2-PA-matched|40.0|1.0|0.0|7|0.00%|0.00%|1433.43|36.202|
|P1|NASA|Public-Reused|none|Full-Telemetry|Phase4-Forest-transfer|40.0|1.0|0.0|7|28.57%|28.57%|1454.89|37.834|
|P1|NASA|Public-Reused|none|Sensorless|SensorlessPPO|40.0|1.0|0.0|7|19.05%|19.05%|1447.77|36.368|
|P1|NASA|Public-Reused|none|Sensorless|TreeExtraTrees|40.0|1.0|0.0|7|14.29%|14.29%|1442.23|36.362|
|P1|NASA|Public-Reused|none|Sensorless|TreeLinear|40.0|1.0|0.0|7|0.00%|0.00%|1127.27|36.144|
|P1|NASA|Public-Reused|none|Full-Telemetry|TreeMLP|40.0|1.0|0.0|7|14.29%|14.29%|1464.47|36.347|
|P1|NASA|Public-Reused|none|Sensorless|TreeMLP|25.0|1.0|0.0|7|0.00%|0.00%|1449.80|36.354|
|P1|NASA|Public-Reused|none|Sensorless|TreeMLP|35.0|1.0|0.0|7|0.00%|0.00%|1449.80|36.354|
|P1|NASA|Public-Reused|none|Sensorless|TreeMLP|40.0|1.0|0.0|7|14.29%|14.29%|1449.80|36.354|
|P1|NASA|Public-Reused|none|Sensorless|TreeMLP|40.0|1.0|50.0|7|28.57%|28.57%|1465.86|36.396|
|P1|NASA|Public-Reused|none|Sensorless|TreeMLP|40.0|2.0|0.0|7|14.29%|14.29%|1230.03|36.165|
|P1|NASA|Public-Reused|none|Sensorless|TreeMLP-extreme-subset|40.0|1.0|0.0|3|0.00%|0.00%|1518.97|36.827|
|P1|NASA|Public-Reused|none|Sensorless|TreeWeather|40.0|1.0|0.0|7|14.29%|14.29%|1452.55|36.271|
|P1|NASA|Public-Reused|none|Sensorless|greedy-frozen|40.0|1.0|0.0|7|14.29%|14.29%|1452.89|36.384|
|P1|NASA|Public-Reused|none|Sensorless|open-loop|40.0|1.0|0.0|7|28.57%|28.57%|1461.73|36.362|
|P1|NASA|Public-Reused|none|Sensorless|remove-climate|40.0|1.0|0.0|3|0.00%|0.00%|1521.25|36.853|
|P1|NASA|Public-Reused|none|Sensorless|remove-eco|25.0|1.0|0.0|7|0.00%|0.00%|1451.27|36.363|
|P1|NASA|Public-Reused|none|Sensorless|remove-eco|35.0|1.0|0.0|7|0.00%|0.00%|1451.27|36.363|
|P1|NASA|Public-Reused|none|Sensorless|remove-econ|40.0|1.0|50.0|7|28.57%|28.57%|1468.74|36.381|
|P1|NASA|Public-Reused|none|Sensorless|remove-econ|40.0|2.0|0.0|7|28.57%|28.57%|1137.31|36.381|
|P1|NASA|Public-Reused|none|Sensorless|soft|40.0|1.0|0.0|7|28.57%|28.57%|1451.40|36.402|
|P1-WUR|WUR|Public-Reused-WUR|none|Full-Telemetry|DVS-N2|40.0|1.0|0.0|7|14.29%|14.29%|1451.09|38.560|
|P1-WUR|WUR|Public-Reused-WUR|none|Full-Telemetry|LegacyV6Full|40.0|1.0|0.0|7|0.00%|0.00%|1448.54|38.599|
|P1-WUR|WUR|Public-Reused-WUR|none|Full-Telemetry|LegacyV6PPO|40.0|1.0|0.0|7|23.81%|23.81%|1462.79|38.421|
|P1-WUR|WUR|Public-Reused-WUR|none|Full-Telemetry|N2-PA-calendar|40.0|1.0|0.0|7|14.29%|14.29%|1423.01|43.070|
|P1-WUR|WUR|Public-Reused-WUR|none|Full-Telemetry|N2-PA-matched|40.0|1.0|0.0|7|0.00%|0.00%|1439.13|38.255|
|P1-WUR|WUR|Public-Reused-WUR|none|Full-Telemetry|Phase4-Forest-transfer|40.0|1.0|0.0|7|28.57%|28.57%|1464.31|39.465|
|P1-WUR|WUR|Public-Reused-WUR|none|Sensorless|SensorlessPPO|40.0|1.0|0.0|7|28.57%|28.57%|1458.11|38.410|
|P1-WUR|WUR|Public-Reused-WUR|none|Full-Telemetry|TreeMLP|40.0|1.0|0.0|7|14.29%|14.29%|1472.89|38.393|
|P1-WUR|WUR|Public-Reused-WUR|none|Sensorless|TreeMLP|40.0|1.0|0.0|7|14.29%|14.29%|1459.44|38.392|
|P2|NASA|Former-Held-Out|LORO|Sensorless|P2-ExtraTrees64|40.0|1.0|0.0|40|0.00%|0.00%|950.85|20.752|
|P2|NASA|Former-Held-Out|LORO|Sensorless|P2-Full64|40.0|1.0|0.0|40|4.00%|2.50%|955.44|20.561|
|P2|NASA|Former-Held-Out|LORO|Sensorless|P2-Linear64|40.0|1.0|0.0|40|0.00%|0.00%|839.44|20.232|
|P2|NASA|Former-Held-Out|LORO|Sensorless|P2-Static3|40.0|1.0|0.0|40|4.00%|2.50%|955.44|20.561|
|P2|NASA|Former-Held-Out|LORO|Sensorless|P2-Weather|40.0|1.0|0.0|40|6.22%|5.00%|951.43|20.666|
|P2|NASA|Former-Held-Out|LOYO|Sensorless|P2-ExtraTrees64|40.0|1.0|0.0|40|12.00%|7.50%|951.61|20.742|
|P2|NASA|Former-Held-Out|LOYO|Sensorless|P2-Full64|40.0|1.0|0.0|40|10.22%|7.50%|955.53|20.558|
|P2|NASA|Former-Held-Out|LOYO|Sensorless|P2-Linear64|40.0|1.0|0.0|40|10.22%|7.50%|940.05|20.437|
|P2|NASA|Former-Held-Out|LOYO|Sensorless|P2-Static3|40.0|1.0|0.0|40|6.22%|5.00%|955.74|20.553|
|P2|NASA|Former-Held-Out|LOYO|Sensorless|P2-Weather|40.0|1.0|0.0|40|8.00%|5.00%|952.98|20.608|
|P2|NASA|Public-Reused|LORO|Sensorless|P2-ExtraTrees64|40.0|1.0|0.0|4|0.00%|0.00%|1384.77|37.927|
|P2|NASA|Public-Reused|LORO|Sensorless|P2-Full64|40.0|1.0|0.0|4|0.00%|0.00%|1403.32|37.894|
|P2|NASA|Public-Reused|LORO|Sensorless|P2-Linear64|40.0|1.0|0.0|4|0.00%|0.00%|1091.92|37.654|
|P2|NASA|Public-Reused|LORO|Sensorless|P2-Static3|40.0|1.0|0.0|4|0.00%|0.00%|1403.32|37.894|
|P2|NASA|Public-Reused|LORO|Sensorless|P2-Weather|40.0|1.0|0.0|4|0.00%|0.00%|1403.78|37.865|
|P2|NASA|Public-Reused|LOYO|Sensorless|P2-ExtraTrees64|40.0|1.0|0.0|4|25.00%|25.00%|1385.08|37.864|
|P2|NASA|Public-Reused|LOYO|Sensorless|P2-Full64|40.0|1.0|0.0|4|0.00%|0.00%|1404.89|37.814|
|P2|NASA|Public-Reused|LOYO|Sensorless|P2-Linear64|40.0|1.0|0.0|4|25.00%|25.00%|1405.49|37.830|
|P2|NASA|Public-Reused|LOYO|Sensorless|P2-Static3|40.0|1.0|0.0|4|0.00%|0.00%|1406.61|37.859|
|P2|NASA|Public-Reused|LOYO|Sensorless|P2-Weather|40.0|1.0|0.0|4|0.00%|0.00%|1407.82|37.754|

All individual-region rates, executed N, NUE, yield, surplus, profit, native loss and Tier1/2/3 are saved in phase8b-core-statistics.json; annual observations and within-case PPO seed means are in phase8b-case-metrics-seed-averaged.csv. Native descriptive NL references have no shared Tier labels. Their clocks/action budgets differ and are not called fully matched. Historical published/reported21.8788/23.5657/40/28.57% remain historical references, not reproduced results. Frozen v6/PPO actors here use the common v8 tail-safety guard, explicitly a transfer.

P1 Static-Soil DL is the Sensorless TreeMLP alias; no duplicate native physics was launched. P1 contains no64-D spatial prior. GroupA therefore spans P1 numerical families and P2 low-rank prior controls. P2 controls receive the same outer-label cohort and inner calibration protocol; all34986prepared rows pass the annual-end timing predicate; China has fewer legal rows because basal171restricts remaining nominal doses. Prior OOD rejection and effective radii are explicitly logged; LORO may reduce to frozen-backbone predictions with calibration-only differences. Pure-Weather excludes static soil and privileged telemetry.

GroupB tests tree, soft penalties, initial-plan frozen Open-Loop343 and current-action greedy80/80 continuation. Hard monolithic and five-specialist versions are exact numeric aliases; no claimed benefit from additional agent names. GroupC removes only climate branches on TRAIN-quantile wet/dry cases, only surplus constraints at caps25/35, or only NUE/dynamic valuation at price2x and TRAIN-selected subsidy. This is not the90-cell stress surface. Soft Tier1 means selection by soft score with hard Eco/NUE targets disabled; it is not an active hard-constraint tier or realized-compliance claim. Soft Tier3 means OOD zero. Numeric counts are unchanged and tier_label_semantics is explicit in every statistics row. Fourteen of177open-loop stage traces have null applicability/score/radius/hash metadata on the later-stage OOD-zero path; dose0andTier3are recorded correctly, and those original traces remain immutable.

The selected50EUR/ha subsidy is the first prespecified candidate changing any TRAIN full three-stage plan. It is an experimental stress magnitude, not a minimum subsidy achieving compliance, an enacted policy, or proof of policy success. Legacy v6 strict null subsidy thresholds remain untouched.

## Prior usage and actual fallback

All P2 decisions log prior acceptance, annual-end admissibility, prior OOD and effective calibration radius. Per-episode counts are in phase8b-core-statistics.json prior_usage. A rejected prior yields the frozen backbone, so any difference attributable only to fallback radii is not evidence that spatial information improved decisions. In particular LORO conditions on a backbone already trained in all five regions.

## Paired inference and physical ceilings

Paired bootstrap B5000, seed20261115 resamples site-years after averaging all three PPO seeds within each case. Exact two-sided sign and Wilcoxon tests, ties, effective nonzero n and full-family Holm adjustment are saved in phase8b-core-statistics.json. NL NASA n5 has minimum exact two-sided sign p=.0625. Wilcoxon uses exact dynamic-programming counts of all2^n_eff signed-rank allocations with average tied ranks and zeros removed. Numeric tie tolerances were frozen before outcomes. These exploratory tests assume exchangeable independent site-year differences; signed-rank inference also requires a symmetric null difference distribution.

Old finite-GRID physical feasibility ceilings are AU11/11, US12/12, NL4/5 NASA, FR1/12 and CN0/12 with basal171kg/ha. They apply to specified simulated calendars/physics and discrete interventions, not a continuous field oracle. Failure on CN/FR cannot be explained away as model tuning opportunity on held labels.

## Verification, failure preservation and reproducibility

The original attempt completed6seasons then stopped on2incomplete legacy-wrapper failures. Epoch28 authorized only2incomplete restarts plus2009unstarted cases. Recovery1 was not a clean pass: it saved1454of2011expected results, then all8workers exited1 and the supervisor failed its final completion assertion after4WUR pre-integration constructor errors. Recovery2 completed557of557missing IDs with all8worker exits0. The disjoint union is6+1454+557=2017, including exactly2authorized incomplete-season restarts. Earlier receipts, failed assertions and both old STOP markers remain intact. Four additional WUR constructor failures occurred before physical integration and were repaired by retaining the identical CSV data in a native-compatible provider subclass. Those startup records remain preserved. The original two incomplete physical prefixes ended before serialized external daily audit; only completed, scored seasons enter the2017-run audit. The combined audit saved2017of2017native episodes. Daily conservation passed on all2017runs/679772daily records: max|N|=1.7166712496e-11kg/ha below1e-10; max|C|=1.97360350285e-10kg/ha below1e-9.

Thirty actual online-controller target-future perturbations passed in both tracks with actual frozen in-domain numerical models. Positive-control past weather changes invalidate the response cache. The target season was excluded from TRAIN analogs. An additional30actual nonzero Stage2-action perturbations passed both tracks. Tests do not rely on trivial OOD-zero actions.

P2 saved70outer-fold adapter fits with inner year exclusions, fixed ranks<=4 and Ridgealpha10. Full fold membership, hashes and calibration radii are saved in phase8b-P2-adapter-training-freeze.json. Raw64 numeric vectors remain private binary tool artifacts and never enter specialist messages or human decision rules.

The P2 preprocessing assertion caught an omitted basal171 budget filter before adapter weights/native evaluation. Superseded arrays and the failed fit log are retained; the corrected predicate is committed N plus remaining nominal doses<=220. No outcome-based model/hyperparameter selection resulted.

See canonical test receipt, external review originals/reconciliation, preservation receipts and final runtime pins for verified commands/SHAs. Review availability and actual served providers must be reported from their actual receipts, never inferred from dispatch.
