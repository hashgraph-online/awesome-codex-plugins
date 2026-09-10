---
name: context-guard
description: Preserve authoritative task requirements, acceptance criteria, multimodal asset contracts, bounded native-plan state, delegated-agent results, and verified evidence across Codex context compaction. Use for long or complex tasks, Goal work, resumed sessions, subagent workflows, explicit context-guard controls, redacted or successor handoff exports, or whenever completion must be checked against an immutable local requirement ledger.
---

# Context Guard

Use the plugin's private requirement ledger and verified evidence to preserve
correctness across long tasks. Codex owns Plan, Goal, compaction, subagents,
permissions, worktrees, transcripts, and memories; this Skill does not replace
those controllers.

## Preserve the current work unit

- Treat an injected recovery packet as the authoritative recovery index. Keep
  requirement and acceptance IDs in private planning and completion checks.
  Later root-user corrections are explicit supersessions, not silent rewrites.
- A whole completion must cover every non-superseded required item in the
  current work unit and its required descendants. Ancestor requirements remain
  constraints; historical unresolved work does not automatically reopen the
  current unit. Pending, failed, blocked, or unsupported required items remain
  incomplete. A passed child or subagent cannot prove parent completion.
- Cite implementation, execution, artifact creation, and verified results as
  separate facts. Prior authenticated passes carry forward when still valid;
  a new turn invalidates unused completion attempts, not durable evidence.
- Private-state integrity failures block acceptance. Reconstructed requirements
  return to pending and need fresh evidence.
- The recovered Codex plan is a read-only mirror. Update the native plan through
  Codex tools; mirror health is diagnostic and grants no execution authority.
  Memories are recall, not authority. Keep durable repository rules in checked-in
  policy unless the user makes them requirements of the current task.

## End ordinary turns normally

Ordinary verifiable completion needs no commands: the guard binds unique
successful evidence to the current unit. Progress, clarification, status, and
valid waiting/deferred replies end silently without closing unfinished work.
Continue authorized assistant work with tools before ending a turn.

Allow paths are silent. Do not wait for, narrate, or fabricate a receipt. A
Stop correction can interrupt a turn at most once; unresolved work then remains
pending. Never expose private checkpoints, commands, parameter bindings,
requirement maps, tokens, or plugin data paths in the reply.

Read [advanced-completion.md](references/advanced-completion.md) before an
explicit completion audit, ambiguous evidence selection, or an enforced
visual, result-readback, UI, or exact-scope proof. It contains the optional
`checkpoint-status`, `register-proof`, `stage-checkpoint`, and
`stage-disposition` paths. Do not invoke them merely because this Skill loaded.
A visual tool's successful return alone proves no visual fact.

## Respect responsibility boundaries

0.13 splits responsibilities explicitly. The executing agent owns whether an
action is within the user's authorization: it reads the real conversation,
repository rules, and host permissions, and proceeds without re-asking when
the user already said so. Context Guard's default path (`standard`/`strict`)
never vetoes ordinary edits, tests, commits, pushes, or tags; a Guard allow is
not authorization, and Guard never re-asks for an authorization because a
work unit, tool wrapper, or observation changed. `strict` adds enforced
current-unit proof obligations; it is not a Git-approval gate.

Release enforcement activates only through an explicit adoption of a release
execution contract or an explicit `context-guard release` declaration. Loading
Skills, installing the plugin, finding a manifest, or a release-flavored task
text never implies adoption. Under the release profile, tier-A identity
actions (tags, registry publish/yank, GitHub Releases) still need an exact
unexpired one-shot ticket, and opaque runner envelopes or unresolvable targets
fail closed. `observe` records bounded would-results without blocking; `off`
and inactive sessions gate nothing. Platform approvals remain independent,
and tools without Hook events remain outside Hook coverage.

A root-user request to push authorizes an ordinary push: resolve its exact
repository, remote, and ref from the request and unique repository state, and
execute without asking the user to repeat it. A normal push does not
authorize force-push, branch deletion, or release publication; those need
their own explicit user decision. Cleanup does not silently become product
implementation; the user's stated restrictions remain recoverable
requirements that the agent must honor.

For release tickets, profile details, migration, or adoption diagnosis, read
[authority-and-controls.md](references/authority-and-controls.md). The release
profile's exact candidate/readiness/ticket checks remain mandatory.

## Delegated results

A delegation prompt defines delegated scope, not a root-user requirement or
supersession. Its wrapper is authoritative as a delegation only when runtime
metadata or a running subagent corroborates it. Follow the injected bounded
contract and return `Outcome`, `Evidence`, `Validation`, `Limitations`, and
`Next`. Return evidence-bearing conclusions and artifacts, never transcripts
or hidden reasoning. The parent owns integration and whole-task acceptance.

## Controls and privacy

`$context-guard` or `context-guard on` activates protection;
`context-guard off` stops recovery and completion gating while journaling
continues. `context-guard status` and `context-guard diagnose` provide bounded
state and diagnostics. Read [authority-and-controls.md](references/authority-and-controls.md)
for explicit adoption, export, or successor-pack requests; read
[successor-pack.md](references/successor-pack.md) before preparing rollover input.
Creating a successor task always remains a separate authorized action.

The immutable raw prompt ledger is the fact source; summaries and checkpoints
are derived indexes. Never commit raw prompts, transcripts, private plugin
state, proofs, credentials, tokens, or caches. Multimodal state keeps bounded
metadata, hashes, dimensions, availability, and redacted facts, not image bytes.
Export only when explicitly requested, with redaction by default. Do not weaken
the advanced proof, integrity, private-control, or authority rules when moving
between ordinary and advanced paths.
