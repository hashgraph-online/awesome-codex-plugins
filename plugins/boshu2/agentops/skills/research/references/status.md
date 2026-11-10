# Health checks and native status

Loaded by [Research](../SKILL.md) in a claimed-state audit when the caller asks
whether the repository is healthy, whether its checks pass, or for a status
snapshot.

## Health checks

For "is this repository healthy" or "do the checks pass", run the project's
own read-only checks (declared in its instructions or CI configuration, or
found in its build files), preferring a `--check`, dry-run or verify variant,
and record where each came from. List any step that writes tracked files,
publishes, deploys or needs credentials as not run, with the reason. Run each
separately and keep going after a failure. Report each as passed, failed, not
run (tool unavailable) or not determined (output not captured), from its exit
status rather than parsed output, and name declared checks you did not run.
Fix nothing, and fold no results into one score that hides a failure.

## Native status

Use `ao status` for the local evidence-store view, or
`ao status --evidence-root <dir>` for a protected external store. It validates
content-addressed intent and verdict artifacts before counting them, reports
corruption or unavailable sources, and shows evidence recency. Without
`--evidence-root` it reads `.agents/ao/intents/sha256` and
`.agents/ao/verdicts/sha256`; a count is not a per-artifact digest inventory.
Inspect a specific digest or timestamp only when that artifact is part of the
requested question. If `ao` is not on PATH (the plugin does not ship it),
report the snapshot as not run (tool unavailable).

Report caller-supplied subject manifests from their named location. Otherwise
mark manifests, runtime phase, elapsed execution, tool-call activity and
remaining work as not checked. An artifact's recent timestamp proves evidence
recency, not an active worker. Read other tracker, Git or factory facts only
from their own authorized source; do not blend factory completion, green checks
and a fresh verdict into one health judgment. Report unavailable evidence
explicitly.
