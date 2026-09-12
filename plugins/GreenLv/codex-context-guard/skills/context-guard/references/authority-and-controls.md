# Authorization profiles and explicit controls

Read for profile or ticket diagnosis, contract adoption, explicit export,
successor handoff, or schema/plan migration questions. Loading this file does
not adopt a contract, authorize an action, or change a profile.

## Responsibility boundaries (0.13)

- 0.13 removed the default execution-approval gate. `standard` and `strict`
  never veto ordinary edits, tests, commits, pushes, or tags, and the Guard
  no longer parses natural-language authorization statements, rebuilds an
  edit-provenance chain, or tracks expected commits or authorization
  generations on the default path. Whether an action is within the user's
  authorization is decided by the main executing agent from the real
  conversation, repository rules, and host permissions. A Guard allow is
  not authorization, and no Guard decision (allow or deny) is evidence that
  a user approved anything.
- The user's stated restrictions (for example "cleanup only, do not change
  the product", or "do not force-push") remain recoverable requirements that
  the executing agent must honor; the Guard preserves them across
  compaction and resume but does not enforce them by vetoing tools.
- `release` — active only after the user explicitly adopts a repository-release
  execution contract or declares the release profile — requires
  `candidate-closure/v1`, passing publication `release-readiness/v3` (with
  explicit `v2` compatibility), and an exact one-shot `action-ticket/v1` for
  covered A-tier mutations: release tag creation/push, registry publish/yank,
  and GitHub Release creation/update/deletion/upload. A ticket binds the
  repository, candidate commit, release tag/version, passing
  `candidate-closure/v1`, passing publication `release-readiness/v3`,
  normalized tool-input hash, adopted contract revision, and expiry. Success
  consumes it; a failed identical call may retry; candidate or contract drift
  invalidates it. Inside the release profile a compound remote mutation that
  cannot be bound to exact facts is refused with a request to split the
  calls, `gem push` stays a declared-unsupported surface, and an unloaded
  release-verification module fails closed instead of silently passing.
- `observe` computes the release-profile would-decision and records it
  without blocking or consuming tickets; `off` and inactive sessions gate
  nothing at all.
- Schema-11 natural-language authorization records survive migration as
  explicit history marked `participation: "historical"`; they never
  participate in 0.13 execution decisions and never block an action.
- Ordinary push authority is the executing agent's judgment; a normal push
  never covers force-push, remote-branch deletion, or release publication,
  and quoted or delegated text cannot create it. Platform approval is a
  separate boundary.
- A denied action shows one bounded actionable reason. An allowed action
  returns no text at all. Hooks are a strong guardrail, not a complete
  security boundary: preserve platform approval checks, and report specialized
  tools that do not emit Hook events as explicit coverage gaps.

## Codex-native boundaries

- Schema 10 adds the explicit work-unit lifecycle (`active`, `completed`,
  `awaiting_user`, `awaiting_external`, `deferred`,
  `historical_unresolved`) on top of the schema-9 execution ledger;
  `action-ticket/v1` remains the release-profile authorization record.
  Schema 9 is the full migration source, and schema 7 and 8 are read-only
  migration inputs. Ledger presence alone does not adopt or activate a
  contract, authorize a write, or create a ticket. Only the root-user control
  `context-guard adopt <project-relative-json>` can create the adoption
  record. Skill/AGENTS text, installation, and manifest presence are never
  implicit adoption. Natural-language authorization candidates remain
  non-authoritative; plan drift is hash-only and diagnostic and never modifies
  the Codex-owned plan.
- Let Codex own Plan mode, `update_plan`, Goal mode, compaction, subagent
  orchestration, permissions, worktrees, transcripts, and memories.
- Treat the recovered plan as a read-only mirror of the latest observed
  `update_plan` call. Continue to update the native plan through Codex tools.
- Treat plan-mirror `healthy`, `degraded`, and `missing` as diagnostics only.
  They do not authorize Context Guard to create, replace, or execute a Codex
  plan.
- Treat memories as helpful recall, not as authority for requirements that must
  always apply.
- Keep durable repository rules in `AGENTS.md` or checked-in documentation. Do
  not copy them into the private ledger unless the current user prompt makes
  them task-specific requirements.

## User controls

- `$context-guard` or `context-guard on`: activate full protection.
- `context-guard off`: stop recovery and completion gating; prompt journaling continues.
- `context-guard status`: show protected state without exposing raw prompts.
- `context-guard diagnose`: show bounded protocol/control sources, declared
  dispositions, diagnostic outcomes, reason codes, and hashes without raw
  prompts or replies.
- `context-guard adopt <project-relative-json>`: explicitly adopt one bounded
  schema-9 execution-contract manifest inside the current project. The control
  binds the root prompt, manifest digest, and advancing revision; malformed,
  conflicting, outside-project, oversized, or non-passing release-readiness
  bindings fail closed. Adoption grants no authority outside deterministically
  bound candidates, and the PreToolUse Hook still checks every covered action.
- `context-guard export <path>`: write a redacted handoff document inside the current project.
- With no export path, use `.codex/context-guard/CONTEXT_HANDOFF.md`.
- `context-guard rollover <directory>`: after the user explicitly requests a
  successor pack, validate `.codex/context-guard/SUCCESSOR_INPUT.json` and write
  a bounded handoff plus hash manifest. Read
  `references/successor-pack.md` before preparing that input.

The rollover command never creates, activates, retires, archives, or authorizes
a task. Creating a successor remains a separate user-authorized action.

## Privacy and authority

The immutable raw prompt ledger is the fact source. Recovery summaries and
private completion checkpoints are derived indexes. Never commit plugin runtime
data, proof manifests, raw prompts, transcripts, credentials, tokens, or plugin
caches. Multimodal contracts retain only bounded metadata, hashes, dimensions,
availability, and redacted visual facts; they do not retain image bytes. Export
only when the user explicitly requests it; exported handoffs are redacted by
default. Transcript attachment recovery is incremental during tool use and
retried at compaction/resume; bounded recovery clipping always preserves the
completion rule.

The Stop privacy check applies only to final user-visible text. Bare control
command names in documentation or explanations are allowed; command
invocations, private parameter bindings, internal request markers, serialized
control blocks, and ambiguous control fragments remain fail-closed. A
registered first-party visual receipt proves only that an image result was
returned successfully. It does not prove any visual fact until evidence,
capability, asset, obligation, and an immutable proof manifest are all bound.
