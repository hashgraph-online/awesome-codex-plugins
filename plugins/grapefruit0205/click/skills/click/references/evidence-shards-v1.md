# Evidence Shards v1

Evidence Shards lets one repository-declared broad argv suite run as stable,
independently recorded child groups. It is an optimization and provenance
layer, not a new source of test-skip authority.

## Repository manifest

The optional manifest is `.click/evidence-shards.json`. Only the blob committed
at `HEAD` is authority, and the working copy must be byte-equivalent after line
ending normalization. Each entry binds one exact parent argv group to at least
two child groups and a complete current test-file inventory:

```json
{
  "version": 1,
  "entries": [
    {
      "checks": [
        ["python3", "-m", "unittest", "discover", "-s", "tests", "-q"]
      ],
      "inventory": ["tests/test_*.py"],
      "shards": [
        {
          "id": "auth",
          "checks": [
            ["python3", "-m", "unittest", "tests.test_auth", "-q"]
          ],
          "covers": ["tests/test_auth.py"]
        },
        {
          "id": "billing",
          "checks": [
            ["python3", "-m", "unittest", "tests.test_billing", "-q"]
          ],
          "covers": ["tests/test_billing.py"]
        }
      ]
    }
  ]
}
```

`checks` values are direct argv arrays, never shell strings. `inventory` and
`covers` use the same deterministic pattern grammar as the dependency manifest:
`*` stays in one segment, `**` as a complete segment crosses directories, and
a trailing `/` is a prefix. Every current tracked or non-ignored untracked file
matched by `inventory` must be matched by exactly one shard's `covers`; a shard
must not cover a repository path outside that inventory.

The repository owner asserts that the child argv groups together are
semantically equivalent to the parent suite. Click can validate exact command
identity and complete file partitioning, but it does not parse framework output
or prove that an argv command really executes every file named by `covers`.

## Runtime behavior

The caller continues to submit the declared parent evidence id and original
broad argv group. When a valid exact entry is available, Click derives stable
internal child evidence ids, validates every child with the normal verification
command policy, and runs the children serially.

- Each child owns its own check, environment, executable, host-coverage,
  workspace, result, and reuse lineage.
- A passing child remains current when a later sibling fails.
- A failed or unexecuted child is never treated as passing.
- Submitting the parent again reruns only unresolved children at the same
  revision; the parent is complete only when every child is current.
- Child ids are internal. Direct child submission is rejected so Click can
  revalidate the complete parent plan on every request.
- Immediately before execution, the one-use runner reloads the committed map,
  working copy, and inventory. A race or changed plan executes no child.

## Reuse authority

The shard manifest authorizes decomposition only. After a mutation, a prior
child success may move to the new revision only through Click's existing reuse
rules:

- a complete runtime dependency observation plus an approved or committed
  dependency declaration; or
- an exact child entry in committed `.click/evidence-reuse.json` whose safe
  path policy covers every net change.

Without one of those authorities, all stale children rerun. The shard map,
shard id, inventory partition, or a sibling's result can never authorize a
cross-revision skip. `.click/evidence-shards.json` is itself a protected policy
path and cannot be declared safe by the safe-change policy.

## Child continuity across a reviewed refresh

New internal child identities bind the exact parent command, shard id, child
argv, coverage patterns, and resolved covered files. They do not depend on a
sibling's definition or the total shard count. Full-plan and inventory digests
still govern admission, runner revalidation, and complete receipt aggregation.

When a newly committed, complete map replaces an active map for the same
parent, Click uses its children directly. An unchanged child's prior success
may survive only as a stale candidate. Its normal current dependency,
environment, executable, host coverage, mutation-boundary and policy checks
must pass before reuse. A changed child starts fresh. Unavailable reuse
evidence reruns that child, without invalidating the valid decomposition.

Complete authoritative observations bind the child's own selection while the
runner independently binds the entire current plan. Legacy facts without this
child binding are not upgraded into narrower authority; they need a new
baseline. Safe-change policy protections still reject a changed shard policy.
Several intervening edits preserve stale candidates, never current completion.

## Fail-closed fallback

Click runs the original parent suite when the map is absent, uncommitted,
edited, malformed, oversized, duplicated, incomplete, unsupported, or no
longer covers the current inventory exactly once. If an already-active plan
loses authority, its partial child results are discarded before the original
parent is prepared. An attempted parent-command substitution remains rejected
rather than becoming a fallback escape.

Fallback is intentionally safe but can cost more time. It never turns a map
problem into a false passing aggregate.

## State and receipts

Shard children use the normal evidence ledger, so mutation invalidation,
partial batch recording, dependency receipts, safe-change receipts, crash-safe
atomic state writes, and host parity stay on the established paths. The active
state stores digests and stable shard ids, not raw parent commands or inventory
paths.

Unsharded completion receipts remain v2. A completion containing shards uses
receipt v3, which adds strict per-source shard provenance: parent source and
parent check digests, shard id and complete shard count, plan, relevant entry,
and inventory digests. Offline verification accepts legacy v1, unsharded v2,
and sharded v3, and rejects a missing or inconsistent v3 shard member.

If a later Evidence task actually reuses a requalified result, its completion
receipt uses v4. A v4 receipt that contains shards preserves every complete
per-source shard provenance field required by v3 and additionally binds the
origin Evidence task and requalification lineage. Candidate retention alone is
not reuse and does not change the receipt version.

## Deliberate exclusions

Evidence Shards v1 does not provide zero-configuration framework discovery,
arbitrary test-output parsing, parallel or distributed execution, remote or CI
caches, cross-contract/global caches, Shadow Observer authority, Evidence Map
UI, release, deployment, or installation behavior.
