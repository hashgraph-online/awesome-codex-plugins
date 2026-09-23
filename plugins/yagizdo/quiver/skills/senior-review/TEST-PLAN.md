# Test Plan -- /senior-review

**Trigger:** `/senior-review` (and `/quiver:senior-review`)

**Setup:** Git repo with uncommitted changes or a branch diff; `gh` CLI available for PR mode.

**Expected behavior:**
1. Shell blocks gather git context without errors.
2. `--quick` sets mode and skips context7; `#NNN`/PR URL triggers PR mode directly.
3. Empty arguments with no context prints usage and stops.
4. Diff source selection shows three buttons via AskUserQuestion.
5. Agent dispatch includes all required context items; no pipeline context passed.
6. Save report writes with correct timestamp filename format.

**Verification checklist:**
- [ ] Slash menu shows `/senior-review`.
- [ ] `--quick` skips context7 and runs single-pass; `#123` and full URL both trigger PR mode.
- [ ] No shell logic in `!` blocks; all shell blocks exit 0.
- [ ] AskUserQuestion used for diff source selection and post-review action.
- [ ] Agent dispatch does NOT include pipeline context; report path uses correct timestamp format.

**Known gotchas:**
- `gh pr diff` requires authentication; skill stops with a clear message on failure rather than continuing with an empty diff.
- Context7 may be unavailable; skill degrades gracefully. Strip `--quick` before PR number parsing to avoid misinterpretation.
