> Historical epoch27 snapshot. Its192-test count and "Recovery has NOT run" statement describe the pre-authorization state only. Epoch28 subsequently authorized recovery: recovery1 saved1454cases then failed its completion assertion after4pre-integration WUR constructor errors; recovery2 completed557missing cases with all-zero worker exits. Together with6original cases,2017completed cases are verified. Final regression193passed. Current results are in PHASE8B_CORE_EXPERIMENTS_G1_G2_G3_REPORT.md. The original snapshot is retained verbatim in the -epoch27-snapshot file.

# Phase8B native evaluation halt and verified repair

G1 passed. The first locked G2/G3 native campaign halted with6completed,
2incomplete and2009unstarted seasons, out of2017frozen cases. It has not been
restarted. G2/G3 performance, superiority, final statistics, final council and
main/master merge are NOT complete. Q8.4/manuscript figures remain unstarted.

## Actual completed work

- Both registered G1 architectures pass all gates in both tracks. Primary MLP
  macro Dev coverage is89.457%Full and90.819%Sensorless; ranking regret is
  3.726vs8.184 and4.914vs8.544EUR/ha against ExtraTrees. See the full G1 report
  and exact archived G1 source. Coverage is retrospective crossyear diagnostic,
  not prospective or regionwise assurance.
-225TRAIN and25Dev physical books cover85750native seasonal replays and
  28817145daily records; all strict C/N checks and native executed-N checks pass.
- PureWeather18fixedfits,Linear12fixedfits and three151552-step Sensorless PPO
  seeds completed. P2nestedLOYO/LORO70adapter fits use44worlds/34986legal rows,
  rank<=4, fixedL2=10; no heldout performance tuning.
- Gemini Carbon High pre-evaluation gate completed with real exit0 and concrete
  findings. The site-year-weighted priorOOD bug was corrected before native
  evaluation; all original review/weight artifacts retained. All34986rows pass
  annual-end timing. LOROFull64/Static3 prior acceptance is0/34986, explicitly a
  fallback/transfer limitation rather than evidence of spatial-prior benefit.
-30actual root-action and30additional nonzeroStage2-action future-weather
  perturbations passed, with past-change cache positivecontrols.
- After the budget repair,192canonical tests pass, zero skips,887warnings.
  Late-stage TRAIN real-weight checks pass for both legacyFull and legacyPPO4
  at committedN171, without any new native rollout or final policy scoring.

## Exact halt and repair

LegacyFull and legacyPPOseed4, both on the initial AU2015NASA case, queried
all seven action candidates even after remainingNbudget fell below100. The
untouched legacy project_members correctly raised Candidate exceeds available
fertilizer budget. Two seasons terminated before a complete final outcome.
The other6completed runs remain byte-identical. Their strict daily audits pass
on2094rows, max|N|=8.01492205937e-12,
max|C|=6.70752342558e-11kg/ha.

The v8-only wrapper now queries the frozen model on legal rows only. Illegal
rows retain exactly the original v6training.predict_stats placeholder means
and remain action-masked. No legacy source, model weight, hyperparameter,
objective, threshold, cohort, weather, or simulator parameter was changed.
The new regression verifies budgets160/171/210/220 and failed on the original
source before passing after the applied repair. Original failure logs remain.

- Repaired NUE feature commit: `40923aa0f1ccdc56462f3790336224e829000173`.
- Root pre-campaign feature checkpoint: `3a41365bf74c34fffc470026fae1f46b0f3f463f`.
- Original sealed source: `phase8b-first-campaign-source-snapshot/policies.py`.
- Diagnosis: `phase8b-native-halt-diagnosis.json`.
- Completed6hashes, failed2IDs, unstarted2009IDs and one-source-only drift:
  `phase8b-proposed-recovery-manifest.json`.
- Repair proof: `phase8b-legacy-budget-repair-tests-applied.log`,
  `phase8b-legacy-budget-repair-actual-model-smoke.json`,
  `phase8b-canonical-pytest-legacy-repair-applied.log`.

## Decision needed before any recovery

The original task explicitly requires a single locked read-only evaluation
pass. Both failed processes have exited with no resumable engine checkpoint;
restarting either season repeats an incomplete physical prefix. User approval
is therefore needed for this exception. No completed result would be rerun,
overwritten or used for parameter selection.

A(recommended)authorizes only the2failed restarts plus2009unstarted runs,
preserving all6completed results and both failure records. Ccontinues only
2009unstarted runs and retains2missing outcomes. Bhalts the core campaign.

The concrete append-only recovery implementation is
`scripts/phase8-recover-locked-campaign.py`. Its default dry-run performs zero
native physics. Saved dry-runs enumerate2011runs forA or2009forC, exclude all
6completed IDs, and verify their hashes. Execution requires an explicit approval
evidence file and creates a distinct recovery directory/permit; the original
STOP marker, permit, logs and results remain untouched. Recovery has NOT run.

Primary main/master and pcse remain unmerged/unchanged; temporary worktrees
are retained while this scientific-integrity decision is pending.
