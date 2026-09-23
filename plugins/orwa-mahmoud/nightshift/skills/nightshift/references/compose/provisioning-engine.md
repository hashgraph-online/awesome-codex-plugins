# Auto-add seatbelt (frozen)

The model installs. The helper only captures a write surface, diffs it, and restores.

## CLI

```text
provision.sh --project DIR baseline --surface PATH [PATH ...]
provision.sh --project DIR baseline --surface PATH [--surface PATH ...]
provision.sh --project DIR diff
provision.sh --project DIR rollback
provision.sh --project DIR recover
```

One `--surface` may list several paths, and the flag may be repeated instead; both name the same
surface. Windows: `ns provision` with the same verbs, taking
`-Surface PATH[,PATH...]`.

Exit: `0` ok · `1` usage or a runtime failure · `2` refused (symlink/reparse escape or locked
path) · `3` a restore that could not be proven.

`plan`, `apply`, `--recipe`, and `--capability` are gone. Unknown flags do not mutate.

## Skill loop

Inspect the package manager → choose a compatible tool → `baseline` the files that will
change → install → smoke → `diff` → record → tooling commit. On smoke or commit failure,
`rollback` must actually run. Write `$NS/capabilities.json` only after the commit succeeds.
Do not ask the owner to install Python or `jq`. No pinned recipe runner.

[`tooling-hints.md`](tooling-hints.md) names the tools commonly used per ecosystem. It is a
starting point under the owner's tooling policy, never a licence to install.

## Containment

A surface path that leaves the work target, names locked owner state, or is a symlink /
reparse point escaping the tree is refused. Rollback unlinks a planted symlink and restores
bytes in the work target — it never writes through the link.

## Recovery

Incomplete work is `$NS/provision-surface` plus `$NS/provision-baseline/`. A leftover
`provision-transaction.json` from an older engine still settles through `recover`.
Start refuses to arm on an unproven restore.
