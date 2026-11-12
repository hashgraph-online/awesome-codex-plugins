---
name: loom-optimize
description: >
  Use when the user says "optimize my loom namespace", "audit memory", "my
  memory search is bad", "loom keeps abstaining", or asks why recall over a
  namespace their agent writes to does not work, or when the mentor's
  `documents_as_memories` / `checkpoints_as_memory` /
  `records_for_identities` hint names rows to rework. Runs `namespace.audit`,
  turns each finding into a plan the owner approves, and reworks the rows
  with `memory.move` so every old key stays readable through a redirect.
  Retires nothing. NOT for deciding what to write in the first place
  (loom-memory) and NOT for client-side failures (loom-status).
allowed-tools: Bash, Read
disable-model-invocation: true
---

# loom-optimize — rework a namespace from its audit, with redirects

Run by the owner's agent over its own namespace, after the data is there.
The invariant: a writer never loses a key it still reads. Retiring old keys
by hand is how a running writer breaks (`found: false`, a local fallback,
two stores that disagree), so this skill moves rows and never deletes them.

Two ops do the work, both through `loom_op` unless your tool list shows
them (HTTP `/v1/<op>` otherwise): `namespace.audit` says what is wrong;
`memory.move` moves a row to a new key and leaves a redirect —
`memory.get(from_key)` still answers with the old value plus
`canonical_key`, `follow=true` serves the new row, and search and list show
only the new one. `keep_redirect` defaults to true; never pass `false`
(that tombstones the old key).

The store also asks for this skill by itself: a
`namespace_health` block in `context.pack` at session start, and one line
from the `loom-namespace-health` Stop hook at session end, each naming the
critical finding codes. Either one is the cue to start at Step 1.

## Step 1 — audit, and stop if there is nothing to do

```
namespace.audit {org, namespace, window_seconds: 604800, sample_limit: 5}
```

Show `summary` as one line (`live_rows`, `live_bytes`, `version_bytes`,
`unembedded_rows`, `gets` / `searches` / `sets`, `get_search_ratio`) and the
findings as a table: `code | severity | count | share | bytes | remedy`. If
`healthy` is true and no finding is `warning` or `critical`, say so and stop
— an `info` finding is a note for the writer, not a rework. A finding of kind
`system_state` (`telemetry_unavailable`, `index_backlog`) is the deployment's
state, never a rework: name it to the owner and leave it out of the plan.

## Step 2 — write the plan, one section per finding

Map each finding code the audit returned to its remedy with the tables in
`reference.md` beside this file (audit findings, and the three mentor hints
that are data changes: `documents_as_memories`, `checkpoints_as_memory`,
`records_for_identities`). Habit findings are writer changes: no data moves;
list them for the owner as a checklist.

Every section carries: the count and bytes from the finding, **three
example keys before → after** taken from the finding's `samples`, the exact
ops it will call with their arguments, and what it will **not** do:

- never `memory.delete`;
- never change a row's value in place — a rewritten value only ever lands
  under a new key through `memory.move`;
- never touch a row written in the last hour — the writer may be mid-flight.

Write the plan as a knowledge document and show it:

```
knowledge.upsert {source_uri: "loom://<org>/<namespace>/_optimize/plan-<YYYYMMDD>",
                  title: "Optimize plan <namespace> <YYYYMMDD>", content: <the plan>}
```

## Step 3 — wait for the owner

Apply nothing until the owner approves in this conversation, in words. A
plan shown is not a plan approved; "looks fine, go ahead" is. If they
approve some sections and not others, apply only those.

## Step 4 — apply, section by section

1. The first three moves of each section run with `dry_run: true`; read the
   returned `to_key`, `redirected` and `advisories` back to the owner.
2. Then real moves in batches of at most 50, in `created_at` order so
   revisions of one key land as versions of the new key.
3. Pass `if_match_sha256` from the audit sample or the `memory.get` you just
   did wherever it is available; a `409` means the row changed under you —
   pause the section, re-read the row, and ask before continuing.
4. Each reply must carry `memory_id`, `version` and `content_sha256`; a
   reply without them is a move that did not happen — say so, do not count
   it.

## Step 5 — measure again

Re-run `namespace.audit` with the same window. Append the after-numbers to
the plan document (same `source_uri`, `knowledge.upsert` again) as a
before/after table, and hand the owner the writer changes as a checklist:
one `json.dumps`, claim-first values, readable keys, `knowledge.upsert` for
anything over ~2 KB, `working_memory.*` for leases and pointers, the same
key for a revision, no index rows.

## Step 6 — retire nothing

Say plainly: every old key still answers `memory.get` with its old value
and a `canonical_key`; `follow: true` returns the new row; search and list
already show only the new rows. Once the writer has moved to the new keys,
the owner can tombstone the old ones with `memory.delete` — that is their
call, later, and not part of this skill.

## Do not

- No in-place value rewrites. A better value goes under a new key via
  `memory.move`; the old key redirects.
- No `memory.delete`, ever, from this skill, and no `keep_redirect: false`.
- No work on another agent's namespace without its owner in the
  conversation; the audit is fine to run, the plan is fine to write, the
  apply is not.
- No apply while the owner's writer is mid-run without saying so first
  (the audit's `sets` in the window says whether it is writing); rows from
  the last hour are out of scope regardless.
- No inventing findings: only codes the audit (or `mentor.brief`'s
  `evidence`) returned get a plan section, with their counts.
