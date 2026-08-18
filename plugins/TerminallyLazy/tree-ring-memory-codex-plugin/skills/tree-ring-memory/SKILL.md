---
name: tree-ring-memory
description: Use when Codex needs local-first recall, durable project decisions, same-host multi-agent coordination, privacy-safe memory capture, evidence records, audit, consolidation, or explicit forgetting through Tree Ring Memory v0.13+.
version: 0.13.0
tags: ["memory", "agents", "recall", "privacy", "projects", "multi-agent", "idempotency", "coordinator-policy", "cli"]
triggers:
  - "remember this"
  - "recall what we decided"
  - "tree ring memory"
  - "multi-agent memory"
  - "fan-in memory"
  - "coordinator policy"
  - "upgrade tree ring"
  - "forget this"
---

# Tree Ring Memory

Use Tree Ring Memory as a lifecycle-aware memory layer, not as a transcript
dump.

Tree Ring Memory preserves meaningful agent learning:

- fresh work stays detailed
- older learning compresses into stable rings
- important warnings remain visible as scars
- durable truths become heartwood
- speculative future work stays as seeds
- sensitive data is blocked, redacted, or kept out by default

## First Check

If the current project contains Tree Ring files, read them before using global
assumptions:

```bash
.tree-ring/SKILL.md
.tree-ring/CLI.md
```

If the CLI is not installed, use the canonical project install guide:
<https://github.com/TerminallyLazy/Tree-Ring-Memory#install>

This wrapper requires Tree Ring Memory CLI >= 0.13.0. Check before using a
shared store or v0.13 policy commands:

```bash
tree-ring --version
```

On macOS ARM64:

```bash
brew tap TerminallyLazy/tree-ring
brew install tree-ring
```

## When To Recall

Recall before:

- starting or resuming a project
- changing architecture, storage, security, privacy, or release behavior
- opening or upgrading a memory root shared by multiple workers
- coordinating same-host fan-out/fan-in or retrying a worker write
- repeating a workflow where prior failures may matter
- responding to a user correction
- making a decision that depends on previous preferences or constraints
- closing meaningful work and deciding what should be remembered

Use narrow queries with project scope when possible. Prefer source-linked,
high-confidence, non-superseded results.

```bash
tree-ring recall "release behavior" --project example-service
```

## When To Remember

Store a memory only when the information is likely to help future work:

- the user states a durable preference
- the user corrects the agent
- a decision is made and should survive the current session
- a lesson is validated by tests, review, or production behavior
- a failed approach should not be repeated
- a security, privacy, release, or data-loss warning appears
- a useful project convention is discovered
- a future idea should be revisited later

Keep memory concise. Store the lesson, decision, warning, or evidence summary,
not the full conversation.

```bash
tree-ring remember "Use project-scoped recall before changing release behavior." \
  --event-type lesson \
  --scope project \
  --project example-service \
  --tag release \
  --tag workflow
```

Use `tree-ring evidence` when the lesson comes from an evaluation, checkpoint,
experiment, branch, incident, or reviewed run artifact.

```bash
tree-ring evidence "Migration smoke test passed with project-local memory." \
  --outcome promoted \
  --evidence-ref "runs/migration-smoke-001" \
  --score 0.91
```

Evidence outcome mapping:

- `promoted`: durable heartwood from supported evidence
- `rejected`: scar for reusable failed or rolled-back approaches
- `deferred`: seed for promising unresolved options
- `observed`: outer-ring evaluation result

## Source And Scope

Set project and scope deliberately:

- use project scope for repo-specific shared rules and reviewed conclusions
- use agent scope for worker-partitioned memory and always set `agent_profile`
- use workflow scope for shared fan-out/fan-in state and always set `workflow_id`
- use session scope for one execution attempt and always set `session_id`
- use global scope only for durable cross-project guidance
- include a source reference for worker results and coordinator summaries

Scope and identity fields are routing partitions, not a read ACL. A same-user
coordinator with filesystem access can recall across worker profiles.

## Multi-Agent Coordination

For workers sharing one local Tree Ring root, give every write explicit
coordination metadata:

```bash
tree-ring --root .tree-ring remember "Worker validated the storage boundary." \
  --event-type lesson \
  --scope agent \
  --project example-service \
  --agent-profile worker-storage \
  --workflow-id release-readiness \
  --session-id attempt-1 \
  --operation-id validate-storage-v1 \
  --source-ref runs/release-readiness/worker-storage.json
```

Use a unique `agent_profile` per worker, one shared `workflow_id` for the
fan-out/fan-in, one `session_id` for each genuine execution attempt, and a
stable unique `operation_id` for each logical write. An exact retry reuses both
the original session ID and operation ID with the same metadata and payload.
Changing only the session or content under the same operation key is a
conflicting reuse and fails closed. New attempts use a new session and new
operation IDs. Replaced operation namespaces and redacted memory IDs remain
claimed until explicit hard deletion.

At fan-in, omit the agent-profile filter so the coordinator sees every worker,
inspect each source reference, then publish an explicit source-linked workflow
or project summary:

```bash
tree-ring --root .tree-ring --json recall "release readiness" \
  --project example-service \
  --workflow-id release-readiness \
  --session-id attempt-1 \
  --scope agent \
  --limit 64
```

`TREE_RING_AGENT_PROFILE`, `TREE_RING_WORKFLOW_ID`, and
`TREE_RING_SESSION_ID` provide the corresponding defaults. Clear an
agent-profile environment filter before coordinator fan-in.

This shared-root contract covers concurrent processes on one host using a local
filesystem. It is not a distributed lock service and does not claim safe
cross-host, NFS, or network-filesystem database sharing. Use per-host roots plus
an explicit evidence-preserving fan-in when work spans hosts.

## Coordinated Write Policy

Stores start in backward-compatible Open mode. Enable Coordinated mode when
ordinary workers should publish only to their own agent partition:

```bash
tree-ring --root .tree-ring policy enable --coordinator release-coordinator
export TREE_RING_COORDINATOR_TOKEN='<one-time capability printed by enable>'
tree-ring --root .tree-ring policy status
tree-ring --root .tree-ring policy audit --limit 100
```

Enable prints the capability once. Put it only in
`TREE_RING_COORDINATOR_TOKEN`; never pass it as a CLI flag or place it in
memory, logs, source refs, transcripts, scripts, or committed files. Tree Ring
stores only a hash. Inject it only into coordinator processes and launch every
ordinary worker with `TREE_RING_COORDINATOR_TOKEN` unset.

In Coordinated mode, an ordinary worker may create only non-heartwood
`scope=agent` memory whose `agent_profile` matches its write context. A
coordinator capability is required for:

- project, global, workflow, session, or other shared/non-agent writes
- heartwood creation or promotion
- JSONL import and persisted DOX/Revolve sync
- persisted consolidation
- ring changes and supersede/delete/redact lifecycle operations
- maintenance with apply or repair flags

Recall, export, policy status/audit, adapter dry-runs, consolidation dry-runs,
and report-only maintenance remain read-only. TUI promotion, ring changes,
supersede, forget/redact, and persisted consolidation also require
`TREE_RING_COORDINATOR_TOKEN`.

Rotate and disable policy only while the current capability is exported.
Rotation invalidates the old capability; disabling returns the store to Open
mode. This policy is operational authorization in official Rust/CLI write
paths, not a read ACL, OS security boundary, or protection from an adversary
who controls local files or the process environment.

Before a v0.13/schema-v3 upgrade, stop all Tree Ring processes, checkpoint and
back up the store, and upgrade every CLI, plugin, and bundled worker before
reopening it. Schema v3 fences memory inserts, updates, and deletes from old
v0.12 writers; all mixed-version operation is unsupported. Roll back only by
stopping every process and restoring the complete pre-upgrade backup.

## Ring Selection

Use these rings:

- `cambium`: active or recent task context
- `outer`: recent decisions and task lessons
- `inner`: older compressed project knowledge
- `heartwood`: durable, high-confidence truths and user preferences
- `scar`: failures, regressions, rejected approaches, and warnings
- `seed`: unresolved ideas, hypotheses, follow-ups, and future work

Do not promote to `heartwood` from weak evidence. Prefer `outer` or `seed`
unless the user confirms durability or the evidence is strong.

## Privacy And Forgetting

Do not store:

- secrets
- credentials
- tokens
- coordinator capabilities
- private keys
- raw chain-of-thought
- temporary scratchpad notes
- unverified claims as durable truth
- private health, financial, legal, or personal identifier details without
  explicit user instruction
- copyrighted source text beyond short allowed snippets

If memory is wrong, private, stale, or superseded:

- redact it when the durable shape is useful but details are unsafe
- delete it when it should not be retained
- supersede it when a newer decision replaces it
- include explicit reasons for every forget operation

```bash
tree-ring forget mem_example --mode delete --reason "example cleanup"
tree-ring audit --audit-type sensitive
tree-ring consolidate --period-type manual --dry-run
tree-ring maintain --apply-expired --repair-fts
```

In Coordinated mode, forget/redact, persisted consolidation, applied
maintenance, and FTS repair require `TREE_RING_COORDINATOR_TOKEN`.

## Source Adapters

Run adapter commands with `--dry-run` first. Sync only concise, source-linked
summaries; never treat imported memory as more authoritative than the source
`AGENTS.md`, Revolve record, evaluation, PR, issue, or test artifact.
In Coordinated mode, persisting DOX/Revolve results requires the coordinator
capability; adapter dry-runs do not.

```bash
tree-ring dox sync --source-root . --dry-run
tree-ring revolve sync --source-root revolve --dry-run
tree-ring integrations scan --source-root .
```

## Closeout Habit

At the end of meaningful work, ask:

- What did we decide?
- What did we learn?
- What should future agents avoid repeating?
- Did the user state a durable preference?
- Is there a future seed worth revisiting?
- Is any memory sensitive and better left unstored?

Only remember the answers that will materially improve future work.

Canonical project:

```text
https://github.com/TerminallyLazy/Tree-Ring-Memory
```
