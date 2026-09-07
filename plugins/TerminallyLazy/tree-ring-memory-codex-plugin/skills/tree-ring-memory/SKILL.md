---
name: tree-ring-memory
description: Guides AI agents in using Tree Ring Memory for durable recall, project decisions, user preferences, warnings, future seeds, privacy-safe memory capture, and lifecycle-aware forgetting.
license: MIT
metadata:
  version: "0.15.1"
  tags: "memory, agents, recall, privacy, projects, dox, revolve, skills, cli"
  triggers: "remember this; recall what we decided; what did we learn; tree ring memory; consolidate memory; forget this; project memory; sync DOX; sync Revolve; evidence loop; multi-agent memory"
---

# Tree Ring Memory

Use Tree Ring Memory as a lifecycle-aware memory layer, not as a transcript dump.

Tree Ring Memory preserves meaningful agent learning like tree rings:

- fresh work stays detailed
- older learning compresses into stable rings
- important warnings remain visible as scars
- durable truths become heartwood
- speculative future work stays as seeds
- sensitive data is blocked, redacted, or kept out by default

## Runtime Bootstrap And Updates

Resolve the actual project root before running Tree Ring. Never initialize a
plugin cache, downloaded package directory, home directory, or arbitrary
working directory by accident.

1. If `<project-root>/.tree-ring/bin/tree-ring` exists, prefer that binary for
   this project. Otherwise check `command -v tree-ring` and run
   `tree-ring --version`.
2. Read existing `<project-root>/.tree-ring/SKILL.md` and `CLI.md` when present.
3. This package targets Tree Ring Memory CLI 0.15.0 or newer. If no compatible
   CLI is available and the user's request already authorizes Tree Ring setup,
   install the verified current release project-locally from the project root.
   Otherwise explain the exact operation and obtain permission before the
   network download or software installation. Download the official,
   version-pinned `v0.15.0/install.sh` installer to a temporary file, verify its
   SHA-256 is
   `ef0d5eb8f09cbe2e4c3abe80ee9a98a56759c89ad4ddd103d6c68314cd653ade`,
   inspect it, and only then run:

   ```bash
   cd <project-root>
   sh <verified-installer-path> --project --init --release latest --no-animation
   ```

   Do not pipe a network response directly to a shell. The installer verifies
   the selected release archive against its published SHA-256 before placing
   the binary at `<project-root>/.tree-ring/bin/tree-ring`.

4. For an existing global CLI, initialize from the project root with
   `tree-ring --root .tree-ring init`. For a project-local CLI, use
   `.tree-ring/bin/tree-ring --root .tree-ring init`. This must place
   `memory.sqlite`, `AGENTS.md`, `SKILL.md`, and `CLI.md` under that project's
   `.tree-ring/` directory.
5. Verify the created paths and run the same binary with
   `--root .tree-ring integrations status`. Initialization creates safe local
   guidance and bridge material; it is not receipt-backed activation proof.

Check for releases without changing files with `tree-ring update --check`. Run
`tree-ring update` only when the user has authorized an update. It updates the
active binary in its existing project-local, direct, or Homebrew-managed scope,
verifies official release assets, and must not create a second shadowing binary.
After an update, return to each project root and rerun `tree-ring --root
.tree-ring init` (or the project-local equivalent) to backfill managed guidance
without replacing custom files.

CLIs older than 0.15.0 do not have `tree-ring update`. Upgrade those with the
same manager or prefix that installed them: `brew upgrade tree-ring` for
Homebrew, `--project --release latest` for an existing project-local install,
or `--install-dir <existing-prefix> --release latest` for another direct
install. Check `command -v tree-ring` and `which -a tree-ring` afterward. Do not
edit a shell profile or change global installation scope without separate user
authorization.

If the current host cannot execute a local shell or access project files, use
this skill only as memory-lifecycle guidance. Do not claim that recall, capture,
audit, activation, or forgetting occurred unless the corresponding command ran
and its result was observed.

## Agent Operating Loop

Use this sequence for meaningful project work:

1. Resolve the project root and read its local Tree Ring contract when present.
2. Run the runtime preflight, then recall narrowly scoped, source-linked memory
   before making a material decision or repeating a failure-prone workflow.
3. Treat recalled memory as context, not authority. Recheck facts that may have
   changed and defer to current source files, tests, policies, and user input.
4. Do the work. Do not write memory merely because a session is active.
5. At a natural checkpoint or closeout, capture only durable decisions,
   corrections, validated lessons, warnings, or future seeds. Never store raw
   transcripts, secrets, or sensitive data.
6. Observe the command result and report the actual outcome. A proposed memory,
   dry run, bridge file, or generated marker is not proof that a durable write,
   sync, activation, correction, or deletion occurred.

In a Coordinated store, do not attempt persistent writes without the required
coordinator capability. If the capability is unavailable, provide a concise
candidate memory for an authorized coordinator instead of claiming it was
stored.

## When To Recall

Recall memory before:

- starting or resuming a project
- changing architecture, storage, security, privacy, or release behavior
- repeating a workflow where prior failures may matter
- responding to a user correction
- making a decision that depends on previous preferences or constraints
- editing files in a repo that has a Tree Ring Memory or `AGENTS.md` contract
- closing out meaningful work and deciding what should be remembered

Use narrow queries with project scope when possible. Prefer source-linked, high-confidence, non-superseded results.

## When To Remember

Store a memory when the information is likely to help future work:

- the user states a durable preference
- the user corrects the agent
- a decision is made and should survive the current session
- an implementation lesson is validated by tests or production behavior
- a failed approach should not be repeated
- a security, privacy, release, or data-loss warning appears
- a useful project convention is discovered
- a future idea should be revisited later

Keep memory concise. Store the lesson, decision, or warning, not the full conversation.

Use `tree-ring evidence` instead of plain `remember` when the lesson comes from
an evaluation, checkpoint, experiment, branch, incident, or reviewed run
artifact.

Use source adapters when project artifacts already contain structured guidance
or evaluated outcomes:

```bash
tree-ring dox sync --source-root . --dry-run
tree-ring revolve sync --source-root revolve --dry-run
tree-ring integrations scan --source-root .
```

Run adapter commands with `--dry-run` first. Sync only concise, source-linked
summaries; never treat imported memory as more authoritative than the source
`AGENTS.md`, Revolve record, evaluation, PR, issue, or test artifact.
In a Coordinated store, persisting an adapter result requires the coordinator
capability; dry-run discovery does not.

Use the exact CLI commands exposed by the local install:

```bash
tree-ring --help
tree-ring dox sync --help
tree-ring revolve sync --help
tree-ring evidence --help
```

If the project was initialized with a project-local binary, prefer the generated
`.tree-ring/CLI.md` reference and include `--root .tree-ring` when needed.

If this skill was loaded through a harness-native bridge file, treat that bridge
as a pointer only. Read the project-local `.tree-ring/SKILL.md` and
`.tree-ring/CLI.md` when present so commands match the installed project root.
Do not assume a global Tree Ring setup applies to the current repo unless the
user explicitly configured it.

## DOX Contract Flow

When a project uses DOX-style `AGENTS.md` contracts:

1. Read the applicable contract chain from the project root down to the working
   directory before editing files. More specific child contracts may refine the
   parent contract.
2. Treat those current source files as authoritative. A recalled DOX summary is
   only a navigation and continuity aid; it never overrides the live contract.
3. Preview the adapter output first with
   `tree-ring dox sync --source-root <path> --dry-run` and inspect every summary
   and source reference.
4. Persist only concise, useful summaries. In a Coordinated store, persistence
   requires coordinator authority; dry-run discovery does not.
5. Never use the adapter to rewrite a root or child `AGENTS.md`, copy whole
   contract trees into memory, or weaken child instructions. Re-run the dry run
   after a source contract changes and re-read the chain before the next edit.

## Harness Activation

For a new project, begin with the safe, project-local default:

```bash
tree-ring init
tree-ring integrations status
```

Do not ask the user to copy a bridge or run `integrations link` for ordinary
setup. `init` configures only safe project-local adapter material by creating
absent final bridge and manifest paths. It never replaces or removes an existing
entry, including during deactivation; contested entries stay untouched and
report `needs-user-review`. A bridge, marker, generated skill, or successful
`init` is not activation proof: `active` requires a fresh, matching receipt from
a new session's scoped recall and safe context injection.
Treat `configured-awaiting-proof`, `active-isolated`, `needs-trust`,
`needs-project-mount`, `needs-plugin`, `needs-user-review`, `unsupported`,
and `failed` as their exact non-active outcomes. Never say Hermes or another
unverified runtime is active.

If publication durability becomes indeterminate, do not delete or rewrite the
published path. Preserve disk material, keep changed harnesses marked
`needs-user-review` in the returned in-memory manifest, and leave any activation
manifest already published on disk intact for explicit reconciliation.

Pi trust is the user's decision: report `needs-trust` rather than changing
global trust. Agent Zero is separate: `tree-ring init` writes only Tree Ring's
passive Agent Zero binding with `needs-plugin`. The user installs/enables the
compatible `tree_ring_memory` plugin and selects the mounted project; the plugin
then owns its absolute, non-project `activation-capability.json` descriptor and
passes it internally. Only descriptor-scoped plugin status can derive
`configured-awaiting-proof`, and only its new-session preflight receipt can
make the runtime `active`.

Never create a generic marker, copy or hand-author that descriptor, set its
internal transport, modify Agent Zero core, or call a different plugin store
shared. A missing, invalid, disabled, or release-incompatible descriptor stays
`needs-plugin`; a different reachable store is `active-isolated`; an
unavailable root is `needs-project-mount`. A passive binding, source checkout,
or stale bundled CLI is not installed capability.

Receipts prove a privacy-safe preflight check, not durable memory creation or a
security boundary. They exclude raw prompts, recalled content, secrets,
sensitive values, paths, and coordinator capabilities. Shared-store claims are
limited to same-host local-filesystem processes whose receipts match the
canonical project `store_id`; they do not apply across hosts or network
filesystems. For diagnostics use `tree-ring integrations status --verbose`;
for advanced controlled work use `integrations activate --harness <id>
--dry-run`, `integrations certify`, or `integrations deactivate --harness
<id>`.

## Certification Boundary

For an installed Tree Ring runtime, use the self-contained CLI evidence paths:

```bash
tree-ring integrations certify --source-root .
tree-ring recall-quality --source-root .
```

Harness certification is non-mutating and writes JSON/Markdown evidence under
`target/tree-ring-certification/`; it does not activate a harness or prove that
an agent used recalled context. Keep receipt-backed status as a separate gate.

`sh scripts/certify-tree-ring.sh` is the full framework release suite. Run it
only from a canonical Tree Ring Memory source checkout where that file, the Rust
workspace, `install.sh`, fixtures, and build tooling are all present. Do not
copy it into another project, download it automatically, or claim full release
certification from the smaller installed-CLI checks. In the TUI, `/evidence
refresh` only displays this external source-checkout command; it does not run
certification. If the script is absent, report that boundary and use the
self-contained CLI commands above when they fit the user's request.

Evidence outcome mapping:

- `promoted`: durable heartwood from supported evidence
- `rejected`: scar for reusable failed or rolled-back approaches
- `deferred`: seed for promising unresolved options
- `observed`: outer-ring evaluation result

## Memory Quality Gates

Use these gates before relying on or writing memory.

Recall gates:

- Before substantial project work, recall project constraints, scars, user preferences, and unresolved seeds.
- Before risky changes, recall warnings and evidence-linked prior failures.
- Before repeating a workflow, recall prior errors and accepted procedures.
- Before closeout, recall recent decisions so memory updates do not contradict already-stored lessons.

Trust gates:

- Prefer source-linked, non-superseded, high-confidence memories.
- Treat heartwood as durable only when source evidence or user confirmation supports it.
- Re-read source files, tests, explicit user instructions, DOX contracts, or Revolve evidence when memory conflicts with current sources.
- Do not treat sensitive or hidden-by-default memory as ordinary recall context.

Write gates:

- Remember only durable decisions, validated lessons, reusable warnings, corrections, future seeds, and evidence-backed outcomes.
- Reject transient planning chatter, duplicate wording, tool noise, and unsupported claims.
- Require evidence refs for promoted or rejected evaluated outcomes.
- Require user confirmation before creating or promoting broad cross-project heartwood.

## Ring Selection

Use these rings:

- `cambium`: active or recent task context
- `outer`: recent decisions and task lessons
- `inner`: older compressed project knowledge
- `heartwood`: durable, high-confidence truths and user preferences
- `scar`: important negative memory, failures, regressions, rejected approaches, and warnings
- `seed`: unresolved ideas, hypotheses, follow-ups, and future work

Do not promote to `heartwood` from weak evidence. Prefer `outer` or `seed` unless the user confirms durability or the evidence is strong.

## Event Types

Prefer specific event types:

- `user_preference`
- `decision`
- `lesson`
- `warning`
- `correction`
- `file_change`
- `tool_result`
- `summary`
- `hypothesis`

If a host integration has stricter event type names, use the closest local equivalent.

## What Not To Store

Do not store:

- secrets
- credentials
- tokens
- private keys
- raw chain-of-thought
- temporary scratchpad notes
- unverified claims as durable truth
- private health, financial, legal, or personal identifier details without explicit user instruction
- copyrighted source text beyond short allowed snippets

If a useful memory contains sensitive material, store a redacted summary with enough context to be useful.

## Source And Scope

Set project and scope deliberately:

- use project scope for repo-specific rules, decisions, warnings, and lessons
- use agent scope for agent-partitioned behavior and always set `agent_profile`
- use workflow scope for one coordinated fan-out/fan-in and always set `workflow_id`
- use session scope for one execution attempt and always set `session_id`
- use global scope only for durable user preferences or cross-project guidance
- include source references such as file paths, issue ids, PR ids, run ids, or docs paths
- use `tree-ring evidence ... --evidence-ref <ref>` for evaluated outcomes
- use `tree-ring dox sync` for concise `AGENTS.md` summaries
- use `tree-ring revolve sync` for promoted, rejected, deferred, or observed evaluation records
- use `tree-ring integrations scan` before configuring a new agent harness

Memory does not replace source documents. If a repo has `AGENTS.md`, project docs, tests, architectural records, or host-specific instruction files, read those sources directly and treat them as authoritative.

When DOX or Revolve source records change, re-run the matching sync adapter with
`--dry-run`, inspect the generated memories, then run the write command only
when the summaries are useful and source-linked.

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
fan-out/fan-in, one `session_id` for each genuine execution attempt, and a stable
unique `operation_id` for each logical write. An exact retry reuses both the
original session ID and operation ID; changing only the session is a conflicting
reuse. Start a new session and use new operation IDs only for a genuinely new
attempt. Exact retries with the same operation metadata and payload return the
original memory. Reusing that operation key for a different payload fails
closed. Replacing a stored memory keeps its old operation namespace claimed.
Redaction also tombstones the memory ID; only an explicit hard delete releases
those claims.

At fan-in, recall the shared workflow and session without an agent-profile
filter, inspect the source refs, then write a source-linked workflow or project
summary:

```bash
tree-ring --root .tree-ring recall "release readiness" \
  --project example-service \
  --workflow-id release-readiness \
  --session-id attempt-1 \
  --scope agent
```

`TREE_RING_AGENT_PROFILE`, `TREE_RING_WORKFLOW_ID`, and
`TREE_RING_SESSION_ID` provide the same defaults as their CLI flags. Do not
leave an agent-profile environment filter set when the coordinator intends to
recall every worker.

This shared-root pattern is for concurrent processes on one host using a local
filesystem. It is not a distributed lock service and does not claim safe
cross-host or NFS operation. Scope and identity fields remain routing metadata,
not a read ACL; a same-user coordinator can recall across profiles. Use
per-host stores plus an explicit, evidence-preserving fan-in process when work
spans hosts.

## Coordinated Write Policy

Stores default to backward-compatible Open mode. For a shared root where only a
designated coordinator should publish or mutate shared memory, enable the
optional Coordinated policy:

```bash
tree-ring --root .tree-ring policy enable --coordinator release-coordinator
# Set and export TREE_RING_COORDINATOR_TOKEN with a history-safe, no-echo prompt
# supported by your shell, or inject it through an approved secret manager.
tree-ring --root .tree-ring policy status
tree-ring --root .tree-ring policy audit --limit 100
```

Enable prints the capability once. Put it only in
`TREE_RING_COORDINATOR_TOKEN`; never pass it as a CLI flag or place it in a
memory, log, source ref, transcript, or committed file. Tree Ring stores only a
hash. `policy status` and `policy audit` are read-only and do not reveal the
capability. Do not paste it into an `export` command; use a history-safe,
no-echo prompt supported by the current shell or approved secret-manager
injection. Inject it only into coordinator processes, and launch every ordinary
worker with `TREE_RING_COORDINATOR_TOKEN` unset so fan-out does not inherit
coordinator authority.

In Coordinated mode, an ordinary worker may only create non-heartwood
`scope=agent` memory whose `agent_profile` matches its write context. Supply the
same identity with `--agent-profile <worker>` or
`TREE_RING_AGENT_PROFILE=<worker>`. A coordinator capability is required for:

- project, global, workflow, session, or other shared/non-agent writes
- heartwood creation or promotion
- JSONL import and persisted DOX/Revolve sync
- persisted consolidation
- ring changes and supersede/delete/redact lifecycle operations
- maintenance with apply or repair flags

Recall, export, policy status/audit, adapter dry-runs, consolidation dry-runs,
and report-only maintenance remain read-only. In the TUI, start with
`--agent-profile <worker>` (or `TREE_RING_AGENT_PROFILE`) so `/remember`
defaults to agent scope. TUI promote/scar/seed, supersede, forget/redact, and
persisted consolidation actions require `TREE_RING_COORDINATOR_TOKEN`.

Rotate the capability while the current one is exported, then immediately
replace the environment value with the newly printed capability:

```bash
tree-ring --root .tree-ring policy rotate --coordinator release-coordinator-next
# Replace TREE_RING_COORDINATOR_TOKEN through the same history-safe, no-echo
# input path before using the new capability.
tree-ring --root .tree-ring policy disable
unset TREE_RING_COORDINATOR_TOKEN
```

Rotation invalidates the old capability. Disabling returns the store to Open
mode and also requires the current capability.

This is operational write authorization enforced by official Rust/CLI store
paths. It is not a read ACL, an operating-system security boundary, or
protection from an adversary who controls the local database files or process
environment.

Before opening an existing store with v0.13/schema v3, stop every Tree Ring
process, checkpoint and back up the database, and upgrade every CLI, plugin, and
bundled worker. Do not reopen the upgraded root with v0.12: schema v3 fences
memory inserts, updates, and deletes from old writers, and all mixed-version
operation is unsupported. Roll back only by stopping all processes and
restoring the pre-upgrade backup.

## Agent-Mediated Updates

Tree Ring Memory does not autonomously scrape chats or write durable memory in
the background. The active agent is responsible for deciding when a Tree Ring
command is warranted, then calling the CLI deliberately.

Use bridge files only to discover Tree Ring and its command reference:

- project-level bridges should point to `.tree-ring/SKILL.md` and
  `.tree-ring/CLI.md`
- global bridges should be treated as opt-in user configuration
- TUI event-stream pulses are display signals, not durable memories

Before writing memory, verify the lesson is durable, useful, privacy-safe, and
grounded in user instruction or source evidence.

## Forgetting And Correction

If memory is wrong, private, stale, or superseded:

- redact it when the durable shape is useful but details are unsafe
- delete it when it should not be retained
- supersede it when a newer decision replaces it
- prefer explicit reasons for every forget operation

In Coordinated mode these lifecycle writes require the coordinator capability.

Treat redaction as monotonic. Do not try to restore a redacted ID through
replacement import; create a new reviewed memory only if the user deliberately
reintroduces safe content.

Never keep known-wrong memory merely because it was previously recalled.

## Closeout Habit

At the end of meaningful work, ask:

- What did we decide?
- What did we learn?
- What should future agents avoid repeating?
- Did the user state a durable preference?
- Is there a future seed worth revisiting?
- Is any memory sensitive and better left unstored?

Only remember the answers that will materially improve future work.
