# GitHub routes

Use the existing authorized Host GitHub connection.

Resolve the owner/repository and requested branch or PR to an immutable commit
SHA. Read files and diffs at that SHA; do not combine moving branch snapshots.
For a PR, record base and head. Detect truncated results and fetch the missing
exact content. CI evidence must name the same head SHA.

Review and planning do not change source. Implementation requires explicit
authorization, an expected base, existing blob SHAs where applicable, a
non-default task branch, and a finite path scope.

Before publishing an implementation, run the applicable project checks that are
available and authorized for the task. If the user explicitly says not to run
tests, do not run tests. If a relevant check is unavailable, disallowed, or not
run, report it as unverified; never claim it passed. CI evidence is valid only
for the exact head SHA it reports.

Re-read the branch head before publishing. Refuse stale or diverged identity.
Never force-push, write the default branch, or merge automatically. Create a PR
only when requested or part of the authorized task.

If write permission is unavailable, return a patch against the pinned base
instead of claiming a remote change. Keep GitHub credentials out of packets and
MCP configuration.
