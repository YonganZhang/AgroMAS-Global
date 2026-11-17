# Online invariance test preflight corrections

The final saved test receipt records30 completed actual-controller invariance
checks, both tracks, nontrivial in-domain models and a past-change positive
control. No native physics or final policy outcome was produced by this script.

Before the successful run, an initial test draft selected all dates after the
issue date rather than restricting perturbations to the target crop season.
That process was interrupted. The predicate was corrected to issue<date<=the
target crop-calendar end, while the target harvest year is excluded from the
analog archive. A second harness issue attempted cache_clear on branches(),
which is not decorated as a cache. The tool transcript captured the error
`AttributeError: 'function' object has no attribute 'cache_clear'`; the invalid
cache-clear call was removed. These were harness-only corrections, with all
weather mutations confined to process memory and restored/freed afterwards.

The same log filename was reused during this harness debugging, so the final
log is the successful run only; do not describe it as a raw archive of all
failed attempts. The diagnostic above is a transcription of observed tool
output, not a recreated raw failure log. No model, hyperparameter, benchmark
label, physical season or evaluation score was changed by these corrections.
