# Foreign Aid Result

JOB_ID: 20261115T205204__claude__1671400
PROVIDER: claude
COMPLETION_STATUS: FAILED
ERROR_CLASS: QUOTA

## Summary
The provider failed or produced an invalid report; inspect the preserved result.agent.md and provider exit code.

## Work Performed
- Launched provider in tmux session: llm_20261115T205204__claude__1671400
- Captured pane output and events under this report directory.

## Evidence
- pane.log: /mnt/data/yongan-admin-2/projects/worktrees/agromas-phase8a/_reports/_foreign_aid/20261115T205204__claude__1671400/pane.log
- events.tsv: /mnt/data/yongan-admin-2/projects/worktrees/agromas-phase8a/_reports/_foreign_aid/20261115T205204__claude__1671400/events.tsv
- error_class.txt: /mnt/data/yongan-admin-2/projects/worktrees/agromas-phase8a/_reports/_foreign_aid/20261115T205204__claude__1671400/error_class.txt

## Files Changed Or Reviewed
- Unknown; the provider did not produce a valid final report.

## Errors Or Blockers
- Required: zero provider exit AND a valid strict COMPLETE report
- Provider rc: 1
- Internal classification: QUOTA_EXHAUSTED
- Public error class: QUOTA

## Next Steps
- Inspect pane.log and attach to tmux if the session is still open.
- Fix auth/quota/network/tooling issues if shown in error_class.txt, then rerun.
