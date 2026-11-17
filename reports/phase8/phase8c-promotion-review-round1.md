# Foreign Aid Result

JOB_ID: 20261116T070300__deepseek__3782345
PROVIDER: deepseek
COMPLETION_STATUS: COMPLETE
ERROR_CLASS: NONE

## Summary
Read-only audit of `scripts/phase8c-promote-local-artifacts.py` at worktree SHA256 `f83167abcb794e6f26936383c2342e9dbf8a76b84b05c18a07d8f63fb483a4d4` (62 lines, mtime 2026-11-16T07:13:03+08:00). **Verdict: NO-GO for worktree deletion.** On the current clean primary the script would silently omit the two real top-level `cache/phase8c*.log` files, is not resumable after a partial copy, and can accept a pre-existing `result.json` symlink that still points at the old worktree because the inventory records only target-content SHA, not the file-symlink link text. The 521 `result.json` links do retarget correctly on a clean first run (independently verified), the 565 `reports/phase8` and 221 `figures` destination files are byte-identical, and current `_reports` regular files are correctly 0700 directories / 0600 files; no current credential leak was found. The index still holds the older `9a4b6e…` script and the staged test/log/dry-run are from that older state, so the reviewed 07:13 fixes are not yet staged.

## Work Performed
- Read the initial 54-line script, the 07:07 revision (`9a4b6e…`), and the current 07:13 revision (`f83167…`); findings below apply to `f83167…`.
- Enumerated the actual roots, file types, symlinks, and destination overlap against primary.
- Verified all 525 file symlinks and the one directory symlink resolve; independently verified all 521 `data/phase8c-supplemental-evaluation/**/result.json` links retarget to primary and preserve target content SHA.
- Verified the only existing destination trees (`reports/phase8`, `figures`) are byte-identical, so no different existing byte would be overwritten on the current clean target.
- Checked `_reports`: 183 files, 0 symlinks; 0775 source dirs contain files and are chmodded on promotion; no current credential-permission defect was found.
- Ran the current seven-check isolated promotion test against `f83167…` (passes) and four isolated fixture reproductions (no production promotion executed).
- Did not rerun the main campaign/analysis, did not modify the reviewed script or any production source.

## Evidence
- `sha256sum`: worktree `f83167ab…`; index `9a4b6eda…`; `git status` shows `AM scripts/phase8c-promote-local-artifacts.py` and `AM scripts/phase8c-test-promotion.py`; staged dry-run is `{"mode":"dry-run","files":58770,"bytes":5178722414}` while a fresh mirror of the same roots found 66,502 items / 5.57 GB.
- **Omitted data (actual):** `cache/phase8c-nue-repair-commit.log` (336 bytes) and `cache/phase8c-root-preflight-checkpoint.log` (4,441 bytes) are real files, are absent from primary, and `Path(file).rglob('*')` returns `[]`. The script includes both in `roots` but creates zero `items` for them; the receipt would list them under `roots` while `files` excludes them.
- **Symlinks:** 525 file symlinks, 0 broken, 1 directory symlink (`cache/phase8c-fig1-venv/lib64 -> lib`, resolves). All 521 `result.json` links have the old worktree prefix and were retarget-verified against primary content.
- **Overwrite check:** all 565 existing `reports/phase8` files and 221 `figures` files are byte-identical; no conflict in the current clean target.
- **`_reports` permissions:** 183 regular files, 0 symlinks; private root 0700, files 0600, per-item ancestor chmod 0700. No current credential leak found.
- **Reproductions on `f83167…` (isolated fixtures):**
  - A: a pre-existing destination link pointing to the source worktree, same content, is accepted on retry (`rc 0`), left pointing at source, and becomes broken after source deletion.
  - B: a truncated destination file from an interrupted copy makes the retry fail (`rc 1`, "Refusing different existing target") and the file remains truncated.
  - C: a dangling destination symlink plus a regular source writes the bytes outside the target tree, leaves the destination as a symlink, and still writes a `status=passed` receipt (`rc 0`).
  - D: a `_reports` directory symlink creates `cache/phase8c-raw-external-reviews/<dir>` with mode 0775 (private root remains 0700); file symlinks are handled correctly.
- **Tests:** current seven-check test passes; the staged `phase8c-promotion-isolated-tests.json`/`.log` still record only six checks, and the staged dry-run is stale versus the current tree.

## Files Changed Or Reviewed
- Reviewed: `scripts/phase8c-promote-local-artifacts.py` (`f83167…`, also `9a4b6e…`), `scripts/phase8c-test-promotion.py` (`26416f…`, index `417be0…`), `reports/phase8/phase8c-promotion-dryrun.json`, `reports/phase8/phase8c-promotion-isolated-tests.json`, `reports/phase8/phase8c-promotion-isolated-tests.log`, `reports/phase8/phase8c-promotion-review-packet.md`.
- Changed: `_reports/_foreign_aid/20261116T070300__deepseek__3782345/progress.md` and `.../result.md` only. No reviewed source or production artifact was modified.

## Errors Or Blockers
- None for the review execution itself.
- Promotion blockers found: (1) two `cache/phase8c*.log` files are silently omitted; (2) non-atomic copy leaves un-resumable partial files; (3) pre-existing source-pointing result symlinks are accepted and the receipt cannot prove retargeting because file-symlink link text is absent from the inventory; (4) a dangling destination symlink can write outside the target tree; (5) no expected-root/non-zero guard, so a zero-item run can still emit `status=passed`; (6) `_reports` directory symlinks leave 0775 parents (no current `_reports` symlinks, so latent); (7) `assert`-based checks are disabled under `python -O`; (8) index/worktree and staged test/dry-run mismatch.

## Next Steps
1. Do **not** delete the worktree or remove the branch yet.
2. Fix the file-root omission (add file roots explicitly or handle `root.is_file()`), and add an expected-root/non-zero item guard. At minimum, manually copy/verify the two cache logs (4,777 bytes total) into primary and record their SHA.
3. Make copies atomic (temp file + `os.replace`, fsync) so an interrupted/quota-limited run can resume; add a truncated-destination retry test.
4. Record and verify each file symlink's link text in the inventory, reject/rewrite pre-existing source-pointing links, and independently confirm all 521 `result.json` links resolve under primary after apply.
5. Refuse dangling destination symlinks (`os.path.lexists`/`lstat`) so `copy2` cannot write outside the target tree.
6. For `_reports` directory symlinks, chmod newly created parents 0700 (file symlinks already inherit the per-item chmod).
7. `git add` the reviewed `f83167…` script and the current seven-check test, rerun the isolated tests, rerun a fresh dry-run on the final tree, then apply. Verify receipt + inventory + primary tests, and only then delete the worktree.
