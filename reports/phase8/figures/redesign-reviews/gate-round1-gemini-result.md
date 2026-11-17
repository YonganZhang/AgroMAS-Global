# Foreign Aid Result

JOB_ID: 20261116T175853__gemini__3033535
PROVIDER: gemini
COMPLETION_STATUS: FAILED
ERROR_CLASS: TIMEOUT

## Summary
The provider failed or produced an invalid report; inspect the preserved result.agent.md and provider exit code.

## Work Performed
- Launched provider in tmux session: llm_20261116T175853__gemini__3033535
- Captured pane output and events under this report directory.

## Evidence
- pane.log: /mnt/data/yongan-admin-2/worktrees/team-team-4031428b3351-team-832/_reports/_foreign_aid/20261116T175853__gemini__3033535/pane.log
- events.tsv: /mnt/data/yongan-admin-2/worktrees/team-team-4031428b3351-team-832/_reports/_foreign_aid/20261116T175853__gemini__3033535/events.tsv
- error_class.txt: /mnt/data/yongan-admin-2/worktrees/team-team-4031428b3351-team-832/_reports/_foreign_aid/20261116T175853__gemini__3033535/error_class.txt

## Files Changed Or Reviewed
- Unknown; the provider did not produce a valid final report.

## Errors Or Blockers
- Required: zero provider exit AND a valid strict COMPLETE report
- Provider rc: 124
- Internal classification: TIMEOUT
- Public error class: TIMEOUT

## Next Steps
- Inspect pane.log and attach to tmux if the session is still open.
- Fix auth/quota/network/tooling issues if shown in error_class.txt, then rerun.
