# Agent Message Queue (AMQ)

[![CI](https://github.com/avivsinai/agent-message-queue/actions/workflows/ci.yml/badge.svg)](https://github.com/avivsinai/agent-message-queue/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/avivsinai/agent-message-queue)](https://github.com/avivsinai/agent-message-queue/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A local, file-based interoperability bus for agent sessions and adapters.**

AMQ manages the conversation: agent-to-agent messaging, thread continuity, cross-session and cross-project routing, handoff state, and operational visibility. It does not try to own task decomposition, worktree management, dependency scheduling, or scheduler execution; Claude Code teams, Codex, Kanban, Symphony, and similar orchestrators stay one layer above it.

## Why AMQ?

Modern AI-assisted development often involves multiple agents working on the same codebase. But without coordination:
- Agents duplicate work or create conflicts
- Reviews require human intermediation
- Context switching kills productivity

AMQ gives agents a **local interoperability bus**: they can send messages, reply in threads, share status, and optionally consume adapter-emitted events through the same queue primitives. The core product stays intentionally small: file-based messages first, lightweight adapters second.

### Key Features

- **Zero infrastructure** — Pure file-based. No server, no daemon, no database. Works anywhere files work.
- **Crash-safe** — Atomic Maildir delivery (tmp→new→cur). Messages are never partially written or lost.
- **Human-readable** — JSON frontmatter + Markdown body. Inspect with `cat`, debug with `grep`, version with `git`.
- **Real-time notifications** — `amq wake` injects terminal notifications when messages arrive (experimental).
- **Built for agents** — Priority levels, message kinds, threading, delivery receipts, and waitable handoffs.
- **Cross-project federation** — Route messages across peer repos, preserve reply routing, and run decision threads that span projects.
- **Swarm mode** — Join Claude Code Agent Teams, claim tasks, and bridge task notifications into AMQ.
- **Optional adapters** — Lightweight Symphony hooks and an experimental Kanban bridge can emit normal AMQ messages with structured metadata.
- **Operational diagnostics** — `amq doctor --ops` shows queue depth, sibling-session backlogs, DLQ state, presence freshness, and integration hints.

![AMQ Demo — Claude and Codex collaborating via split-pane terminal](docs/assets/demo.gif)

## Installation

### 1. Install Binary

**macOS (Homebrew):**
```bash
brew install avivsinai/tap/amq
```

**macOS/Linux (script):**
```bash
curl -fsSL https://raw.githubusercontent.com/avivsinai/agent-message-queue/main/scripts/install.sh | bash
```

Installs to `~/.local/bin` or `~/go/bin` (no sudo required). Verify: `amq --version`

**One-liner with skill:**
```bash
curl -fsSL https://raw.githubusercontent.com/avivsinai/agent-message-queue/main/scripts/install.sh | bash -s -- --skill
```

Review the script before running. Installation fails unless `checksums.txt` has exactly one valid entry for the selected asset and `sha256sum` or `shasum` verifies it before extraction.

### 2. Install Skill

**Via skills** (recommended):
```bash
npx skills add avivsinai/agent-message-queue -g -y
```

**Or via skild:**
```bash
npx skild install @avivsinai/amq-cli -t claude -y
```

For manual installation or troubleshooting, see [INSTALL.md](INSTALL.md).

### Updating

For Homebrew installations:
```bash
brew upgrade amq
```

For installations made with the install script or another manual binary install:
```bash
amq upgrade
```

### Keepalive companion

`amq-keepalive` is developed and released from this repository alongside AMQ.
`make build` produces both binaries, and each AMQ release includes a separate
`amq-keepalive` archive stamped with the same release version. Verify a build
with any equivalent form:

```bash
amq-keepalive -v
amq-keepalive --version
amq-keepalive version
```

See [COOP.md](COOP.md#supervisor-recipes) for the operational guide.

## Quick Start

### 1. Initialize Project

```bash
amq setup
```

Detects supported agent CLIs and launcher preferences, previews the project
declaration, then creates `.amqrc`, `.amq/launch.json`, local preferences,
the default session, and roster mailboxes.

Automation uses a stateless preview and applies only that approved digest. The
first non-interactive setup must name the roster, default session, and launcher
preference explicitly:

```bash
setup_args=(--agents claude,codex --default-session collab --launcher-preference commands)
setup_preview="$(amq setup --preview --json "${setup_args[@]}")"
setup_digest="$(printf '%s\n' "$setup_preview" | jq -r '.preview.digest')"
amq setup --apply "$setup_digest" "${setup_args[@]}"
```

`--preview` performs zero writes. `--apply` recomputes the preview and exits `6`
without writing if its `sha256:<hex>` digest differs. `-y` remains available
for callers that already own an approval gate, but it cannot be combined with
`--preview` or `--apply`.

Provider arguments belong in the committed `.amq/launch.json`, so `launch`
can validate and include them in its semantic trust digest. For example:

```json
{
  "schema": 1,
  "default_session": "collab",
  "agents": [
    {
      "handle": "claude",
      "adapter": "claude",
      "command": ["claude", "--permission-mode", "acceptEdits"],
      "resume_policy": "enabled"
    },
    {
      "handle": "codex",
      "adapter": "codex",
      "command": ["codex", "--sandbox", "workspace-write", "--ask-for-approval", "on-request"],
      "resume_policy": "enabled"
    }
  ],
  "layout": {"type": "columns"}
}
```

Dangerous permission-bypass flags are not valid committed arguments. Keep them
in an operator-controlled direct `coop exec` invocation when that low-level
path is intentionally required.

### 2. Launch or Resume a Session

```bash
amq launch
amq session create feature-x   # once, before the first named-session launch
amq launch --session feature-x
amq session resume feature-x
```

`launch` reads the committed roster, selects the declared default session when
`--session` is absent, and resumes exact provider-qualified conversation IDs.
It never uses a provider's "last" or "continue" heuristic. The first semantic
plan, and each semantic plan change, requires an interactive trust
confirmation stored outside the worktree. Non-interactive or `--json` calls
exit `6` until that digest is trusted. An unknown `session resume` name exits
`3` and writes nothing. Managed backends use a fail-closed recovery journal;
see [Managed launch recovery](docs/launch-recovery.md).

The `commands` backend prints complete `coop exec` commands and exits `6`
because executing them is the remaining operator action. Paste those emitted
lines exactly, one per terminal. Do not reconstruct them from examples: they
bind the selected session, launch nonce, provider arguments, and execution
ticket.

Each command sets up the session environment, starts wake notifications, and
launches the agent. See [COOP.md](COOP.md#running-co-op-mode) for co-op
operations and [the wake acknowledgement contract](docs/wake-doorbell-acknowledgement.md)
for notification retries.

> **First-message check:** start both agents before sending the test message.
> A newly started wake deliberately baselines messages that were already
> waiting, so they remain unread but do not trigger a notification. If you sent
> first, run `amq drain --include-body` in the target agent.

For isolated sessions (multiple pairs working on different features):

```bash
amq session create feature-a
amq launch --session feature-a
```

Again, paste the complete commands emitted by `launch` into separate terminals.

Optional aliases are a convenience, not part of the canonical quickstart.
A bare `eval "$(amq shell-setup)"` affects only the current shell. To make
aliases such as `amc`, `amx`, and `amg` available in future terminals, add the
setup command to your shell startup file:

```bash
# zsh
amq shell-setup --shell zsh >> ~/.zshrc

# bash
amq shell-setup --shell bash >> ~/.bashrc
```

Run the appropriate append command once, then open a new terminal or source
that startup file. Use the bare `eval` only when you intentionally want aliases
in one already-open shell.

`coop init` and direct `coop exec` provisioning remain available as legacy
low-level plumbing. See [COOP.md](COOP.md#low-level-provisioning) for those
paths, operator-only bypass examples, and advanced wake options; they are not a
second project-onboarding flow.

### 3. Send & Receive

```bash
# Send a message
amq send --to codex --subject "Review needed" --kind review_request \
  --body "Please review internal/cli/send.go"

# Check inbox
amq list --new

# Filter by priority or sender
amq list --new --priority urgent
amq list --new --from codex --kind review_request

# Read all messages (one-shot, moves to cur, emits drained/dlq receipts)
amq drain --include-body

# Wait for delivery on a single-recipient handoff
amq send --to codex --body "Please pick this up" \
  --wait-for drained --wait-timeout 60s

# Send between known sessions before entering coop exec
amq send --root .agent-mail --from-session feature-a --me claude \
  --to codex --session feature-b --body "Please review the setup"

# Inspect receipts for a message later
amq receipts list --me codex --msg-id <msg_id>

# Reply to a message
amq reply --id <msg_id> --kind review_response --body "LGTM with comments"
```

`read`, `drain`, and `monitor` apply the same strict message validation. Invalid
messages move to DLQ and produce a `dlq` receipt. Participating shells also pin
their exact session context and refuse mismatched mailbox operations. See
[Session routing and safety](docs/session-routing.md) for routing, raw-root
overrides, worktree isolation, doctor repair gates, and backlog discovery.

### 4. Inspect Health

```bash
amq doctor
amq doctor --ops
amq doctor --ops --json
amq wake check --me codex
amq wake check --me codex --json
amq wake check --me codex --json --json-schema=2
amq doctor --ops --json --json-schema=2
amq doctor --ops --fix-wake-locks
amq wake repair --me codex
amq wake recover-owner --me codex
amq wake retire --me codex --inject-via /absolute/injector \
  --retry-until injected --inject-arg exec --inject-arg terminal-id
```

`amq wake check` is read-only: it reports whether this process can start or
repair a wake, and a `restart_capability` of `agent_safe`, `operator_only`, or
`unavailable` with an exact next action. Automated agents may act only on
`agent_safe`; leave a live wake running otherwise, and never downgrade a
TIOCSTI refusal to attention-only. `doctor --ops` reports the same fields for
every discovered lock.

Wakes started by `coop exec` self-upgrade in place when a newer AMQ is
installed, without changing PID, terminal ownership, or unread work; disable
with `amq wake --no-self-upgrade` or `AMQ_WAKE_NO_SELF_UPGRADE=1`.
`--json-schema=2` (requires `--json`) replaces prose parsing with a closed,
machine-stable action/actor/reason contract; schema 1 remains the
byte-compatible default. See
[docs/wake-lifecycle.md](docs/wake-lifecycle.md#91-self-upgrade) for the
candidate-bounding rules and the full schema-2 contract.

Wake locks are `stale` (AMQ proved the owner is gone or mismatched —
`--fix-wake-locks` removes them after a re-check) or `unverified` (AMQ could
not prove either way, so it leaves the lock in place; confirm manually before
removing `.wake.lock`). Only a narrowly eligible artifact — an aged, malformed,
conclusively ownerless lock or orphan target of the exact shapes the invariant
doc permits — is moved to a timestamped `.quarantined` name so acquisition can
proceed; every other shape is preserved in place. `doctor --ops` reports the
count and newest age, and `amq cleanup --wake-quarantine-older-than <duration>`
removes quarantined artifacts explicitly (`--dry-run` is non-mutating). See
[docs/wake-state-invariants.md](docs/wake-state-invariants.md) for exactly
which lock/target shapes qualify for each state.

`amq wake repair` restarts an eligible `--inject-via` wake from its saved
target after a proven-stale or unverified-ownerless lock, using continuity
state (`.wake.repair-floor`) so messages that arrived while the notifier was
down remain eligible to notify. It refuses raw terminal wakes and owner-bound
claims; output goes to `agents/<agent>/.wake.repair.log`.
`amq wake recover-owner` is the separate path for an owner-bound
`--wake-inject-via` claim: a live owner releases its own claim (via the
inherited `AMQ_WAKE_OWNER` token) from the same OS session, or AMQ removes a
conclusively dead owner's claim outright — there is no force mode.
`amq wake retire` stops only an identity-confirmed live `--inject-via` wake
whose executable, arguments, and saved target all match (or removes an
exactly-bound stale lock without signaling); results are exactly `refused`,
`retired`, or `retired_with_residue` (an exit-0 warning that target/state
cleanup was incomplete). See
[docs/wake-lifecycle.md](docs/wake-lifecycle.md) and
[docs/wake-state-invariants.md](docs/wake-state-invariants.md) for the
repair-floor, ownership, and residue-convergence contracts.

The lifecycle boundaries:

- repair = replace a proven-stale inject-via wake.
- recover-owner = stop/release one owner-bound inject-via claim/artifact.
- `doctor --ops --fix-wake-locks` = remove a proven-stale lock.
- retire = stop an identity-confirmed live inject-via wake.
- launchd, systemd, or the owning shell = stop a raw wake (retire does not
  unload supervisors or promise they won't restart a wake).

`amq who` and `amq doctor --ops` distinguish `notifier_live` (a verified live
wake lock — proves notification is attached, not that messages are consumed)
from `recent_activity` (a fresh `last_seen` without that proof); see
[CLAUDE.md](CLAUDE.md#doctor--ops) for the full semantics. Consumption itself
is the job of `drain`/`monitor`, evidenced by receipts. For long-running
`wake`/`monitor` under systemd or launchd, see
[Supervisor recipes](COOP.md#supervisor-recipes).

## Message Kinds & Priority

AMQ messages support kinds (`review_request`, `question`, `todo`, etc.) and priority levels (`urgent`, `normal`, `low`). See [COOP.md](COOP.md) for the full protocol.

## Co-op Mode

For real-time Claude Code + Codex CLI collaboration patterns, roles, and phased workflows, see [COOP.md](COOP.md).

## Cross-Project Federation

AMQ can route messages across repositories, not just across agents in one checkout. Add a project name plus peer roots to `.amqrc`:

```json
{
  "root": ".agent-mail",
  "project": "app",
  "peers": {
    "infra-lib": "/Users/me/src/infra-lib/.agent-mail"
  }
}
```

Then send directly to another project:

```bash
amq send --to codex --project infra-lib --body "Can you review the shared API change?"
amq send --to codex@infra-lib:collab --thread decision/release-v0.24 --kind decision \
  --labels "decision:proposal,project:app,project:infra-lib" \
  --body "Proposal: align both repos on v0.24"
```

Replies route back automatically with the stamped `reply_project` metadata. When `from` matches your own handle, inspect `from_project` before treating the message as an echo; the same handle in a different project is a legitimate cross-project sender. This shipped in v0.22.0 and is the recommended way to coordinate multi-repo agent work without adding a broker.

## Swarm Mode (Claude Code Agent Teams)

External agents (Codex, etc.) can join Claude Code Agent Teams via `amq swarm join`, claim tasks, and receive notifications through `amq swarm bridge`. Note: the bridge delivers task notifications only; direct messages require relay through the team leader.

For the full command reference, see [CLAUDE.md](CLAUDE.md).

## Global Root Fallback

Most AMQ commands resolve the queue root from the project `.amqrc` or the
default `.agent-mail` layout in the current tree. For agents launched outside
an AMQ-enabled repo by external orchestrators, you can configure a global
root. Explicit `AMQ_GLOBAL_ROOT` does not shadow project `.amqrc`, but it does
take precedence over repo-local auto-detection:

```bash
export AMQ_GLOBAL_ROOT="$HOME/.agent-mail"
```

Or create `~/.amqrc`:

```json
{"root": ".agent-mail"}
```

Root resolution precedence is:

```text
explicit --root > AM_ROOT > project-local .amqrc > AMQ_GLOBAL_ROOT > implicit fallbacks
```

Inside a Git worktree or bare repository, the remaining eligible fallback is
repo-local detected `.agent-mail`; implicit `~/.amqrc` is refused. Outside
Git, `~/.amqrc` remains a convenience fallback and precedes detected
`.agent-mail`. Set
`AMQ_GLOBAL_ROOT` explicitly when shared routing is intentional.

`coop exec` honors that precedence before bootstrap. In a Git worktree with no
eligible root, it bootstraps `<git-top>/.agent-mail`; `--session X` creates that
named session afterward, while `--no-init` preserves the refusal. `coop init`
is the explicit local-bootstrap command and also targets the Git top. Bare
repositories do not auto-bootstrap.

If a project `.amqrc` exists but cannot be read or parsed, AMQ stops instead
of silently delivering through a lower-precedence fallback. Use an explicit
`--root` or `AM_ROOT` when you intentionally need to override that config.

For an external orchestrator or plain shell that should stay pinned to one
session, opt in explicitly:

```sh
amq_context="$(amq env --session auth --me claude --export)" && eval "$amq_context"
```

Every shell-mode `amq env` output replaces the complete context: `AM_ROOT`,
`AM_ROOT_ID`, `AM_ME`, `AM_BASE_ROOT`, `AM_BASE_ROOT_ID`, and `AM_SESSION`.
The two `_ID` values are opaque physical-identity tokens emitted or unset by
AMQ; do not set them manually. Sessionless output sets `AM_BASE_ROOT` to the
exact root and writes an empty `AM_SESSION`, so changing to another sessionless
root is detectable. `--export` additionally prints a stderr note that the
terminal is pinned. Treat this as one terminal, one session.

Auto-detect covers the default `.agent-mail` layout, including `.agent-mail/<session>` session roots without `.amqrc`. Custom root names and peer config still require `.amqrc` or explicit flags/env.
This same chain is used by `amq env`, `amq doctor`, and the integration commands, so Symphony and Kanban-launched agents can find the correct queue even when they are not started from the project directory.

## Extension Metadata

Higher-level layers can store launch records, role metadata, restore state, and indexes without writing into AMQ-owned mailbox directories. AMQ reserves these extension namespaces:

```text
<AM_ROOT>/extensions/<layer>/
<AM_ROOT>/agents/<handle>/extensions/<layer>/
```

Layer names use lowercase ASCII letters, digits, hyphen, underscore, and dot; reverse-DNS names are supported. For example, [amq-squad](https://github.com/omriariav/amq-squad) — a role-aware agent team launcher built on AMQ — stores its launch records and role state under `io.github.omriariav.amq-squad`. AMQ does not create files inside layer-owned directories, and `amq cleanup` leaves extension directories alone unless a future command explicitly targets extension metadata.

Layers may publish a passive manifest at:

```text
<AM_ROOT>/extensions/<layer>/manifest.json
```

`amq doctor --json` reports valid manifests under `extension_manifests` and malformed metadata under `extension_diagnostics`. Manifests are diagnostics-only: AMQ does not execute extension code, load callbacks, or invoke hooks from them. See [docs/adr-layer-extensions.md](docs/adr-layer-extensions.md) for the full contract.

## Integrations

AMQ transports **messages**, not remote task state. The integration layer is intentionally narrow: optional adapters convert external lifecycle or task events into normal AMQ messages. Integration messages are self-delivered (`from=<me>`, `to=<me>`) so an agent monitoring its own inbox can react without polling another tool directly.

### Symphony

Symphony support is a lightweight hook recipe for Codex workspaces orchestrated through `WORKFLOW.md`:

```bash
amq integration symphony init --me codex
amq integration symphony init --me codex --check
amq integration symphony emit --event after_run --me codex
```

`init` patches an AMQ-managed fragment into `WORKFLOW.md`. `emit` is hook-friendly and supports `after_create`, `before_run`, `after_run`, and `before_remove`. This stays intentionally small: AMQ does not try to become a Symphony control plane. Current limitation: because `WORKFLOW.md` is parsed and rewritten as structured YAML/Markdown, comments and formatting inside the frontmatter may be normalized.

### Cline Kanban Bridge

The Kanban bridge is **experimental**. Use it when you want runtime session transitions and review handoffs mirrored into AMQ, with the understanding that it depends on a fast-moving preview WebSocket surface:

```bash
amq integration kanban bridge --me codex
amq integration kanban bridge --me codex --workspace-id my-workspace
```

The bridge connects to `ws://127.0.0.1:3484/api/runtime/ws` by default, bootstraps from `snapshot`, refreshes from `workspace_state_updated`, and emits notifications only for task session transitions plus `task_ready_for_review`.

### Integration Metadata

The built-in adapters share a versioned contract under `context.orchestrator`. See [docs/adapter-contract.md](docs/adapter-contract.md) for the formal v1 envelope and stability expectations.

Integration messages also carry standard labels such as:

- `orchestrator`
- `orchestrator:symphony` or `orchestrator:kanban`
- `task-state:<state>`
- `handoff` for review-ready transitions
- `blocking` for failed or interrupted work

That makes integration traffic filterable with existing AMQ primitives such as `amq list --label orchestrator --label handoff`.

## Command Reference

Common command groups:

| Area | Commands |
|------|----------|
| Core messaging | `init`, `send`, `list`, `read`, `drain`, `reply`, `thread`, `trace`, `watch`, `monitor`, `receipts` |
| Collaboration | `setup`, `launch`, `coop init`, `coop exec`, `session create`, `session list`, `session resume`, `swarm list`, `swarm join`, `swarm tasks`, `swarm bridge` |
| Integrations | `integration symphony init`, `integration symphony emit`, `integration kanban bridge` |
| Operations | `presence set`, `presence list`, `route explain`, `who`, `doctor`, `doctor --ops`, `wake check`, `wake repair`, `wake recover-owner`, `wake retire`, `cleanup`, `dlq *`, `upgrade`, `env`, `shell-setup` |

Canonical schema-selecting diagnostic forms:

```text
amq wake check --me <agent> [--root <path>] [--strict] [--json] [--json-schema <1|2>]
amq doctor [--root <path>] [--base-root <path>] [--ignore-session-pin] [--ops] [--fix-wake-locks] [--fix-mailboxes] [--json] [--json-schema <1|2>]
amq cleanup [--tmp-older-than <duration>] [--wake-quarantine-older-than <duration>] [--launch-journal --root <session-root>] [--dry-run] [--yes]
```

`--json-schema` requires `--json`.

### Exit codes

AMQ exposes stable process exit codes for scripts and agent consumers:

| Code | Meaning |
|------|---------|
| `0` | Success. The command completed normally. |
| `1` | General error. The failure has no more specific exit-code classification. |
| `2` | Usage error. Arguments, flags, or command input are invalid. |
| `3` | Not found. A requested resource such as a mailbox, message, session, agent, or configuration does not exist. |
| `4` | Timeout. A watch, monitor, receipt wait, or delivery wait reached its deadline. |
| `5` | Context mismatch. A syntactically valid route was refused, including a pin conflict or an ineligible implicit root inside Git. |
| `6` | Action required. The command cannot proceed without an operator action (stale conversation token, unknown backend inspect, untrusted config, blocked rebind). |

The numeric meaning is the machine contract; stderr is human-readable context
and should not be parsed as a stable discriminator. `--json` does not change
these process exit codes. A read-only `list` on a mismatched session pin warns
and continues; commands that consume or mutate mailbox state fail with code
`5`.

When a command reports per-agent outcomes, whole-command failures that precede
any per-agent work keep codes `2`, `5`, and `3` and preempt mixed results. Once
per-agent work begins, the process exit code is the highest-precedence per-agent
outcome: `6` over `4` over `1` over `0`. Expected dispositions (`disabled`,
`unsupported`, and policy-consistent `fresh`) contribute `0`.

For the full CLI syntax, examples, and message schema, see [CLAUDE.md](CLAUDE.md).
For the read-only trace contract and its evidence limits, see [docs/trace.md](docs/trace.md).

## How It Works

AMQ uses the battle-tested [Maildir](https://cr.yp.to/proto/maildir.html) format:

1. **Write** — Message written to `tmp/` directory
2. **Sync** — File fsynced to disk
3. **Deliver** — Atomic rename to `new/` (never partial)
4. **Process** — Reader moves to `cur/` after reading

This guarantees crash-safety: if the process dies mid-write, no corrupt message appears in the inbox. See [CLAUDE.md](CLAUDE.md) for the full directory layout.

## Built on AMQ

AMQ is meant to be the messaging layer underneath higher-level orchestrators. Projects building on it:

- **[amq-squad](https://github.com/omriariav/amq-squad)** by [@omriariav](https://github.com/omriariav) — a role-aware agent team launcher. AMQ owns messaging between agents; amq-squad owns the layer above: who is on the team, what role each agent plays, the shared norms they follow, and how to bring the whole squad up, down, back, or into a new workstream. It builds on AMQ's [extension metadata](#extension-metadata) surface for launch records and role state.

Building something on AMQ? Open an issue or PR to be listed here.

## Documentation

- [INSTALL.md](INSTALL.md) — Alternative installation methods
- [docs/amq-keepalive.md](docs/amq-keepalive.md) — Keepalive command and safety reference
- [docs/session-routing.md](docs/session-routing.md) — Session selection, routing guards, and worktree behavior
- [docs/wake-operations.md](docs/wake-operations.md) — Wake inspection, repair, recovery, and retirement
- [docs/wake-lifecycle.md](docs/wake-lifecycle.md) — Wake lock/target state contract, self-upgrade, log retention, JSON schema, injector identity
- [docs/wake-doorbell-acknowledgement.md](docs/wake-doorbell-acknowledgement.md) — Wake retry ladder and `--retry-until` acknowledgement contract
- [docs/wake-state-invariants.md](docs/wake-state-invariants.md) — Wake artifact ownership, lock states, and quarantine invariants
- [docs/adapter-contract.md](docs/adapter-contract.md) — Formal v1 adapter contract for integration messages
- [docs/adr-layer-extensions.md](docs/adr-layer-extensions.md) — ADR for stable layer extension surfaces
- [docs/trace.md](docs/trace.md) — Read-only trace contract and evidence limits
- [COOP.md](COOP.md) — Co-op workflow and supervisor operations
- [CLAUDE.md](CLAUDE.md) — Agent instructions, CLI reference, architecture

## Development

```bash
git clone https://github.com/avivsinai/agent-message-queue.git
cd agent-message-queue
make build   # Build binary
make test    # Run tests
make ci      # Full CI: vet + lint + test + smoke
```

## FAQ

**Why not just use a database?**
Files are universal, debuggable, and work everywhere. No connection strings, no migrations, no ORM. Just files.

**Why not Redis/RabbitMQ/etc?**
Those require infrastructure. AMQ is for local inter-process communication where agents share a filesystem. No server to configure or keep running.

**What about Windows?**
Native Windows supports the core queue, but not `coop exec` or `wake`. Use WSL
with the Linux binary for the complete co-op workflow. See the explicit
[platform capability matrix](INSTALL.md#platform-capability-matrix).

**Is this production-ready?**
For local development workflows, yes. AMQ is intentionally simple—it's not trying to be a distributed message broker.

**How does AMQ compare to other multi-agent tools?**
Tools like [MCP Agent Mail](https://github.com/Dicklesworthstone/mcp_agent_mail) (server-based coordination + SQLite), [Gas Town](https://github.com/steveyegge/gastown) (tmux-based orchestration), and others offer richer features. AMQ is intentionally minimal: single binary, no server, Maildir delivery. Best for 2-3 agents on one machine.

## License

MIT
