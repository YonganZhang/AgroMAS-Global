# Phase8D campaign provenance and replay boundaries

The original `scripts/phase8d-run-campaign.py` remains the sealed attempt1 entry point referenced by `phase8d-evaluation-permit.json`. It is retained as historical code, including the infrastructure-only P2 LOYO folder-name mismatch that caused the first attempt to stop. Do not use it to start another campaign.

The completed campaign used `scripts/phase8d-run-campaign-recovery1.py --execute --resume-verified --workers 16` with `phase8d-evaluation-permit-recovery1.json`. All880 P2 references were checked against245 unchanged frozen adapter files. `phase8d-manual-recovery1.json` records the1,915 previously completed hashes. That explicit recovery changed the loader mapping and accounting, not policy/model/scoring parameters. `data/phase8d-evaluation-failed-attempt1/` and `reports/phase8/phase8d-attempt1-failure/` retain failed-attempt evidence. The original sealed source has a separate `phase8d-run-campaign-attempt1.py` snapshot as well.

The campaign is complete. Do not rerun or overwrite existing result/permit files. Re-analysis uses `scripts/phase8d-analyze-results.py` against the existing18,268 immutable result files; figures and manuscripts use the derived Phase8D statistics. Actual physics reuse never substitutes an old policy decision or invents a public prefix. Newly recovered public prefixes come from native execution; every final controller decision is fresh.

The separately executed upstream compatibility suite had283 passes and9 failures outside the active canonical `tests/target` and Phase8 suites. Those failures remain visible in `phase8d-canonical-tests-after-nested-cache.log`; they were not filtered from a claimed all-tests result. The canonical active suite passed232 cases with no skips/failures.
