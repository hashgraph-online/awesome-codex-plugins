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
- **Operational diagnostics** — `amq doctor --ops` shows queue depth, DLQ state, presence freshness, and integration hints.

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

Review the script before running; it verifies release checksums when possible.

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

```bash
amq upgrade
```

## Quick Start

### 1. Initialize Project

```bash
amq coop init
```

Creates `.amqrc`, mailboxes for `claude` and `codex`, and updates `.gitignore`.

Optionally add shell aliases (`amc` for Claude, `amx` for Codex):
```bash
eval "$(amq shell-setup)"
```

### 2. Start Agent Sessions

```bash
# Terminal 1 — Claude Code
amc

# Terminal 2 — Codex CLI
amx
```

Each alias sets up the environment, starts wake notifications, and launches the agent. For isolated sessions (multiple pairs working on different features):

```bash
amc feature-a          # Claude in feature-a session
amx feature-a          # Codex in feature-a session
```

Without aliases, use `amq coop exec` directly:
```bash
amq coop exec claude -- --dangerously-skip-permissions
amq coop exec --session feature-a codex
```

Add `--no-gitignore` when `coop exec` should auto-initialize the project without changing `.gitignore`.
Managed launchers can add `--require-wake` to fail instead of launching the agent when the wake watcher cannot start.
Launchers that use an external injector can add `--wake-inject-via /absolute/path/to/injector`
and repeated `--wake-inject-arg` values. When that invocation starts a new wake,
the wake stores a repair target so `amq wake repair` can restart wake later
without restarting the agent TUI. If `--require-wake` reuses an existing wake,
that wake must already have repair metadata to be repairable.

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

`amq read`, `amq drain`, and `amq monitor` now share the same strict header validation. If a message in `inbox/new` is corrupt or has malformed headers, the command moves it to DLQ and emits a `dlq` receipt instead of leaving it in place.

### 4. Inspect Health

```bash
amq doctor
amq doctor --ops
amq doctor --ops --json
amq doctor --ops --fix-wake-locks
amq wake repair --me codex
```

Wake locks reported by `doctor --ops` can be `stale`, `unverified`, or, in JSON
output, any current lock state. With `--fix-wake-locks`, fixed and error states
can also appear. `stale` means AMQ proved the recorded owner is gone or is not
the same wake process, so `--fix-wake-locks` can remove the lock after a fresh
re-check. `unverified` means AMQ could not prove ownership either way, such as a
legacy lock with a live PID but no process-start token, a hostname mismatch, or
an unsupported platform. AMQ leaves `unverified` locks in place; inspect the PID
and remove the named `.wake.lock` manually only after confirming no matching
`amq wake` still owns that agent/root.

`amq wake repair` is an explicit live-session repair path. It only runs when
the lock is proven `stale`, the lock was created for `--inject-via`, and the
agent has a saved `agents/<agent>/.wake.target` whose digest matches the lock's
repair metadata. It refuses raw terminal wake targets, leftover targets from old
locks, and `unverified` locks to avoid double-injecting into an active session
or injecting into the wrong terminal. Repaired wake output goes to
`agents/<agent>/.wake.repair.log`; `doctor --ops` can report whether repair is
available, but it never starts a wake process.

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

Most AMQ commands resolve the queue root from the project `.amqrc` or the default `.agent-mail` layout in the current tree. For agents launched outside the repo root by external orchestrators, you can configure a global fallback instead:

```bash
export AMQ_GLOBAL_ROOT="$HOME/.agent-mail"
```

Or create `~/.amqrc`:

```json
{"root": ".agent-mail"}
```

Root resolution precedence is:

```text
flags > AM_ROOT > project .amqrc > AMQ_GLOBAL_ROOT > ~/.amqrc > auto-detect
```

For an external orchestrator or plain shell that should stay pinned to one
session, opt in explicitly:

```sh
eval "$(amq env --session auth --me claude --export)"
```

That exports `AM_ROOT`, `AM_ME`, and, for session roots, `AM_BASE_ROOT`, and
prints a stderr note that the terminal is pinned. Treat this as one terminal,
one session.

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
| Core messaging | `init`, `send`, `list`, `read`, `drain`, `reply`, `thread`, `watch`, `monitor`, `receipts` |
| Collaboration | `coop init`, `coop exec`, `swarm list`, `swarm join`, `swarm tasks`, `swarm bridge` |
| Integrations | `integration symphony init`, `integration symphony emit`, `integration kanban bridge` |
| Operations | `presence set`, `presence list`, `route explain`, `who`, `doctor`, `doctor --ops`, `wake repair`, `cleanup`, `dlq *`, `upgrade`, `env`, `shell-setup` |

For the full CLI syntax, examples, and message schema, see [CLAUDE.md](CLAUDE.md).

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
- [docs/adapter-contract.md](docs/adapter-contract.md) — Formal v1 adapter contract for integration messages
- [docs/adr-layer-extensions.md](docs/adr-layer-extensions.md) — ADR for stable layer extension surfaces
- [COOP.md](COOP.md) — Co-op mode protocol & best practices
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
The core queue works on Windows. The `amq wake` notification feature requires WSL. `doctor --ops` can still report wake lock files on unsupported platforms, but it cannot verify live wake process identity there and will not auto-fix `unverified` locks.

**Is this production-ready?**
For local development workflows, yes. AMQ is intentionally simple—it's not trying to be a distributed message broker.

**How does AMQ compare to other multi-agent tools?**
Tools like [MCP Agent Mail](https://github.com/Dicklesworthstone/mcp_agent_mail) (server-based coordination + SQLite), [Gas Town](https://github.com/steveyegge/gastown) (tmux-based orchestration), and others offer richer features. AMQ is intentionally minimal: single binary, no server, Maildir delivery. Best for 2-3 agents on one machine.

## License

MIT
