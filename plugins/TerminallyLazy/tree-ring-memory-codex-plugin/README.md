# Tree Ring Memory Codex Plugin

Tree Ring Memory is a local-first memory lifecycle practice for Codex agents.

This plugin packages one Codex skill that teaches agents when to recall, write,
audit, consolidate, and forget project memory using the open-source
[Tree Ring Memory](https://github.com/TerminallyLazy/Tree-Ring-Memory) CLI.

Plugin `0.2.0` requires Tree Ring Memory CLI **>= 0.13.0**. The minimum is
intentional: v0.13 adds schema v3, coordinated-write authorization, and the
writer-protocol fence used by this guidance.

It does not run a background service, scrape chats, or capture transcripts.
The active agent chooses when a memory action is useful, source-linked, and
privacy-safe.

## What It Adds

- Recall before context-dependent project work.
- Concise memory writes for validated decisions, lessons, warnings, and user
  preferences.
- Evidence-backed outcomes through `tree-ring evidence`.
- Same-host worker identity, scoped fan-out/fan-in, and idempotent retries.
- Optional coordinator-authorized shared publication and protected lifecycle
  writes.
- Explicit forgetting, redaction, and supersession guidance.
- DOX and Revolve adapter usage with dry-run-first guardrails.

## Install Tree Ring Memory

macOS ARM64 with Homebrew:

```bash
brew tap TerminallyLazy/tree-ring
brew install tree-ring
```

For other install paths, use the canonical project README:
<https://github.com/TerminallyLazy/Tree-Ring-Memory#install>

Verify the installed core before using this wrapper:

```bash
tree-ring --version
```

The result must be `tree-ring 0.13.0` or newer.

## Use

After installing this plugin in Codex, ask:

```text
Use Tree Ring Memory to recall durable project context before editing.
Use Tree Ring Memory to capture this validated lesson without storing a transcript.
Use Tree Ring Memory to audit stale or sensitive memory before closeout.
```

The skill will look for project-local `.tree-ring/SKILL.md` and
`.tree-ring/CLI.md` files first. If they are absent, it falls back to the public
CLI commands documented in the main framework repository.

## Same-Host Multi-Agent Contract

Tree Ring supports concurrent workers sharing one root only when they run on
the same host and use a local filesystem. It is not a distributed lock service
and does not claim safe cross-host, NFS, or network-filesystem database sharing.
Use separate per-host roots and an explicit evidence-preserving fan-in when
work spans hosts.

Give every worker a unique agent profile and operation ID, while sharing the
workflow and session for one fan-out attempt:

```bash
tree-ring --root .tree-ring remember "Storage worker validated WAL behavior." \
  --event-type lesson \
  --scope agent \
  --project example-service \
  --agent-profile worker-storage \
  --workflow-id release-readiness \
  --session-id attempt-1 \
  --operation-id validate-storage-v1 \
  --source-ref runs/release-readiness/worker-storage.json
```

An exact retry reuses the original session and operation IDs and the same
payload. Reusing the operation key with changed metadata or content fails
closed. At fan-in, the coordinator recalls the shared workflow/session without
an agent-profile filter, inspects source references, and writes an explicit
source-linked summary.

## Coordinated Write Policy

Stores start in Open mode. Enable Coordinated mode when ordinary workers should
write only non-heartwood memories to their own agent partition and a designated
coordinator should own shared publication:

```bash
tree-ring --root .tree-ring policy enable --coordinator release-coordinator
export TREE_RING_COORDINATOR_TOKEN='<one-time capability printed by enable>'
tree-ring --root .tree-ring policy status
tree-ring --root .tree-ring policy audit --limit 100
```

The capability is printed once. Put it only in
`TREE_RING_COORDINATOR_TOKEN`; never pass it as a CLI flag or retain it in
memory, logs, source refs, transcripts, scripts, or committed files. Inject it
only into coordinator processes and launch ordinary workers with the variable
unset.

In Coordinated mode, the coordinator capability is required for shared or
non-agent writes, heartwood creation/promotion, import, persisted DOX/Revolve
sync, persisted consolidation, ring changes, supersede/delete/redact, and
maintenance with apply or repair flags. Recall, export, policy status/audit,
adapter and consolidation dry-runs, and report-only maintenance remain
read-only.

## v0.13 Schema-v3 Upgrade Fence

Before opening an existing store with v0.13:

1. Stop every Tree Ring CLI, TUI, plugin, and bundled worker using the root.
2. Checkpoint SQLite WAL state and make a verified backup.
3. Upgrade every CLI, plugin, and bundled worker.
4. Reopen with v0.13 to migrate the store to schema v3.

Do not reopen the upgraded root with v0.12. Schema v3 fences old memory
inserts, updates, and deletes, and all mixed-version operation is unsupported.
Rollback requires stopping every process and restoring the complete pre-upgrade
backup.

## Canonical Project

- Framework repo: <https://github.com/TerminallyLazy/Tree-Ring-Memory>
- Canonical v0.13 skill: <https://github.com/TerminallyLazy/Tree-Ring-Memory/blob/v0.13.0/skills/tree-ring-memory/SKILL.md>
- Launch page: <https://terminallylazy.github.io/Tree-Ring-Memory/>
- Homebrew tap: <https://github.com/TerminallyLazy/homebrew-tree-ring>

## Security

This plugin ships instructions only. It does not include remote MCP servers,
webhooks, analytics, credentials, or networked runtime code.

See [SECURITY.md](SECURITY.md) for disclosure and privacy guidance.
