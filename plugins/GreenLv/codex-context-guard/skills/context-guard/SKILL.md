---
name: context-guard
description: Preserve requirements and verified evidence across Codex compaction, resume, and delegation. Use $context-guard, context-guard on, or for long, complex, or resumed tasks requiring an immutable private completion ledger.
---

# Context Guard

Codex retains Plan, Goal, compaction, subagents, permissions, and memories.

## Completion scope

- An injected recovery packet is the authoritative recovery index. Keep
  requirement and acceptance IDs in private planning. Later root-user
  corrections supersede explicitly, never silently.
- A whole completion covers every non-superseded required item in the current
  work unit and its required descendants. Ancestor requirements remain
  constraints; historical unresolved work does not reopen the unit;
  pending/failed/blocked/unsupported items stay incomplete. A passed child or
  subagent cannot prove parent completion.
- Implementation, execution, artifacts, and verified results are separate
  facts. Prior authenticated passes carry forward; a new turn invalidates
  unused completion attempts, not durable evidence.
- Private-state integrity failures block acceptance; reconstructed
  requirements return to pending and need fresh evidence. Missing evidence or
  unknown ability never becomes success.
- The recovered Codex plan is a read-only mirror (update it through Codex
  tools); memories are recall, not authority.

## Ordinary turns

Ordinary verifiable completion binds unique successful evidence
automatically — no commands. Progress, clarification, status, and valid
waiting or deferred replies end silently without closing unfinished work;
continue authorized work with tools before ending a turn. Allow paths are
silent — do not narrate or fabricate a receipt. A Stop correction interrupts
a turn at most once; unresolved work then stays pending. Never expose private
checkpoints, commands, parameter bindings, tokens, or plugin paths in a
reply.

For the explicit advanced path only — visual facts, human evidence selection,
ambiguous evidence, or troubleshooting — read
[advanced-completion.md](references/advanced-completion.md). The injected
turn-bound status command (append `--commands`) discovers the exact staging
and proof commands; do not invoke them merely because this Skill loaded. A
visual tool's successful return alone proves no visual fact.

## User and host authority

The executing agent reads the real conversation, repository rules, and host
permissions, and proceeds without re-asking when the user already authorized
an action. The default path (`standard`/`strict`) never vetoes ordinary
edits, tests, commits, pushes, or tags, and a Guard allow is not
authorization. Release enforcement activates only through an explicit
adopted release contract or `context-guard release` — loading Skills,
installing the plugin, or release-flavored task text never implies adoption.
A root-user request to push authorizes that ordinary push, not force-push,
branch deletion, or publication. Cleanup does not silently become product
implementation; stated user restrictions remain recoverable requirements.

For release tickets, profiles, adoption, exports, and rollover, read
[authority-and-controls.md](references/authority-and-controls.md).

## Delegated results, side answers, controls, privacy

- A delegation prompt defines delegated scope only, never a root-user
  requirement or supersession; corroborate it with runtime metadata or a
  running subagent, return `Outcome`, `Evidence`, `Validation`,
  `Limitations`, and `Next`, and let the parent own integration.
- Only for adopted independent answer review: after delivering a side
  answer, run `review-pending` once with the session's private-control
  arguments and `--execute`, then continue work. If the reviewer route is
  unavailable, keep coverage unknown and proceed; no missing review closes
  the main task. Contract:
  [answer-review.md](references/answer-review.md).
- `context-guard on` activates protection; `off` stops recovery and
  completion gating while journaling continues; `status` and `diagnose` are
  bounded. Read [successor-pack.md](references/successor-pack.md) before
  preparing rollover input; creating a successor task is a separate
  authorized action.
- The immutable raw prompt ledger is the fact source; summaries are derived
  indexes. Never commit raw prompts, transcripts, private state, proofs,
  credentials, tokens, or caches. Multimodal state keeps bounded metadata
  and hashes, not image bytes. Export only on explicit request, redacted by
  default.
