---
name: click
description: Record revision-aware evidence for software work by default, or bind higher-risk execution to one human-readable approval contract in Guarded mode. Use when Click Hook context enables Evidence or Guarded mode, or when the user explicitly selects Click. Do not use for questions or explanations.
---

# Click

Click is an incremental-verification runtime. In **Evidence** mode, the default, the host authorizes work exactly as it normally does; Click records what happened and decides which checks must run again. Do not treat a question about Click as a mutation, and do not stage a contract or ask for Click approval in Evidence mode.

## What Click records on its own

- The user prompt becomes the intent lineage of the Evidence session. An in-scope or narrowing follow-up continues it; the next request after a completed session starts a fresh one.
- Every recognized file edit and every `click-gate mutate` advances the mutation revision, which invalidates earlier receipts.
- Every check submitted through `click-gate verify` gets an exact receipt bound to its argv, revision, protected tree, environment, executable, and host coverage. Supported checks also capture their inputs automatically.

None of this needs a contract, an approval, or a dependency declaration from you. Never invent one, and never create, widen, or edit `.click/evidence-reuse.json` or a shard map to skip a check.

## Run checks through `click-gate verify`

Choose concrete checks from repository evidence while you work and submit them with stable ids. Evidence registers an argv id on its first accepted use:

```text
click-gate verify '{"version":2,"workdir":"/absolute/path/to/repository","checks":[{"evidence_id":"E1","argv":["python3","-m","pytest","-q"],"class":"broad"}]}'
```

- `class` is `targeted`, `broad`, or `deep`. Include the absolute `workdir` whenever the execution tool runs outside the Hook session directory.
- After a change, resubmit the same id and argv. For a sharded broad suite, always submit the parent id and argv, never an internal shard id.
- Use `click-gate inspect` for tracked read-only argv and `click-gate mutate` for structured mutations; ordinary file edits go through the host's editors directly. Exact forms, limits, observer, dashboard, and receipt-export controls are in the [capability protocol](references/capability-protocol.md).
- Stop when every registered check is current for the final revision and no managed service remains active.
- A request that omits `reporting` uses the `actionable` format for unittest/pytest checks: a failure arrives as a bounded summary with a local log reference, not the raw stream. Pass `reporting.format: "raw"` when you need the full output.

## Read status

`click-gate status` prints at most three short lines in the dashboard language (`CLICK_LANGUAGE` or the POSIX locale; Korean by default): executed and reused counts with the estimated avoided time, the mode and revision, and the next action. Use `click-gate status --json` only when you need the full report with per-check decisions, reason codes, and actionable failure details.

## Reuse is decided by Click

Click alone decides, at execution time, whether a submitted check runs or reuses a receipt. Report a reuse only when status output or a verification result shows it; never predict, request, or claim one, and never change an observer setting, a reporting mode, or an owner policy to obtain one. Status, the dashboard, Shadow telemetry, caller-supplied observation JSON, and any `reuse_authorized: false` view are not authority. Say a check is verified only when its receipt is current; Click does not prove code correctness or test sufficiency. The final receipt reports `approval_bound: false` and `execution_authority: host`.

## Guarded mode

Only for `@Click`, `$click`, or `click-gate default guarded`: follow the [Guarded mode workflow](references/guarded-mode.md) for the approval-bound contract, staging and passing by id, and execution rules. Mode selection, resume, bypass, and cancel rules are in [operating modes](references/modes.md); bypass and cancel require the exact user-authorized first-line forms there. For code-review-only work in either mode, run `click-gate review`, stay read-only, and report findings without a build contract.

More, only when needed: [automatic sharding setup](references/automatic-sharding-setup.md) for a large suite without a shard policy, [verification efficiency](references/verification-efficiency.md) for reporting and failure-collection options, and [anti-loop policy](references/anti-loop-policy.md) for repeated reads.
