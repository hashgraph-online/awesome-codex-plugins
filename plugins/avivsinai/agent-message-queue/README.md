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

## Quick Start

### 1. Initialize Project

```bash
amq coop init
```

Creates `.amqrc`, mailboxes for `claude`, `codex`, and the reserved `user` operator handle, and updates `.gitignore`.

### 2. Start Agent Sessions

```bash
# Terminal 1 — Claude Code
amq coop exec claude

# Terminal 2 — Codex CLI
amq coop exec codex
```

Each command sets up the environment, starts wake notifications, and launches
the agent. The wake child appends full diagnostics to the private
`agents/<agent>/.wake.log`; a separate inherited descriptor carries only
terminal-safe attention to the controlling terminal. This process boundary
keeps runtime and fatal-error text out of Codex and Claude full-screen
composers. Accumulated diagnostics are truncated when a new wake starts after
the log reaches 1 MiB and checked again on the wake's 30-second maintenance
tick, so long-lived ordinary and repair wakes bound their own logs.

Wake treats terminal notification as an attempt, not delivery, and retries on
a capped backoff until the inbox makes durable progress. The first notification
is immediate. Attempts that inject the fixed doorbell start at 5 seconds because
they drive the agent; attention-only attempts start at 30 seconds because they
alert a human. Input attempts double to a 2-minute cap; attention-only attempts
continue through 4 and 8 minutes to a 15-minute cap. Retries never give up while
the cohort remains unread. Contextual peer headers appear only in terminal
output or attention; terminal input always uses the fixed doorbell. The delay
starts after the preceding injector process exits or times out. Because
`--wake-inject-via` executes arbitrary local code, a retry can repeat
injector-side effects. Added messages join the pending cohort and share its next
notification without resetting the retry ladder. Input-delivery additions may
pull a decayed deadline forward to the delivery floor 5 seconds after the last
input attempt, or immediately if that floor has already passed; attention-only
additions retain the cohort's current decayed deadline. Bursts within the
debounce window remain one notification.
Removals or replacements immediately rearm the cohort.
A successful input attempt does not also emit attention. Transient foreground
authority or input-quiet refusals keep the input retry armed while rate-limiting
their separate attention output. Output-only delivery repeats on its slower
cadence, and a short or failed attention write stays pending on that cadence
instead of terminating the notifier. Recovery-required state never retries
uncertain terminal input; it repeats the manual drain-and-restart notice on that
same attention cadence until the unread cohort drains.

> **First-message check:** start both agents before sending the test message.
> A newly started wake deliberately baselines messages that were already
> waiting, so they remain unread but do not trigger a notification. If you sent
> first, run `amq drain --include-body` in the target agent.

For isolated sessions (multiple pairs working on different features):

```bash
amq coop exec --session feature-a claude
amq coop exec --session feature-a codex
amq coop exec --session feature-a grok     # Optional third peer
```

Pass agent flags after `--`:
```bash
amq coop exec claude -- --dangerously-skip-permissions
amq coop exec codex -- --dangerously-bypass-approvals-and-sandbox
```

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

Add `--no-gitignore` when `coop exec` should auto-initialize the project without changing `.gitignore`.
Managed launchers can add `--require-wake` to fail instead of launching the agent when the wake watcher cannot start.
When `coop exec` starts a fresh wake, it baselines messages that were already
waiting. Those messages remain unread, create no receipt, and do not trigger
that wake. `coop exec` only reuses a compatible live wake that has already
published generation-bound proof of watcher preparation. The existing wake is
not retroactively baselined; pending backlog can still notify. SessionStart
draining mitigates that residual. `--require-wake` requires a usable notifier,
not a rebased reused wake.
Launchers that use an external injector can add `--wake-inject-via /absolute/path/to/injector`
and repeated `--wake-inject-arg` values. When that invocation starts a new wake,
the wake is bound to the exact `coop exec` process identity and stores its
injector target. The claim survives an ordinary wake exit so another process
cannot silently take over the handle. If the owner or wake exits unexpectedly,
use `amq wake recover-owner` instead of the ownerless repair path. When a
required owner capability is conclusively unsupported before any claim exists,
AMQ warns and starts one ownerless wake instead.

AMQ identifies an external injector by its resolved executable and ordered
fixed arguments. Put any provider target identity needed to distinguish a pane,
window, or session in `--wake-inject-arg` (`--inject-arg` when starting
`amq wake` directly). Ambient environment variables and provider configuration
are not part of this identity, so repair, recovery, and retirement cannot
detect target changes made only through those channels.

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

`coop exec` and every shell-mode `amq env` invocation pin the terminal's exact
root context with `AM_BASE_ROOT` plus `AM_SESSION`. For named sessions,
`AM_BASE_ROOT` is the authorized parent; for sessionless contexts, it is the
exact root and `AM_SESSION` is empty. `read`, `drain`, `monitor`, `watch`,
`send`, `reply`, and all DLQ commands refuse a raw root that conflicts
with that pin before reading, moving, or delivering mailbox state. An implicit
participating command also refuses when the active pin conflicts with an
initialized cwd-local queue discovered from a project `.amqrc` or repo-local
`.agent-mail`; AMQ does not silently choose between the two roots. The narrow
exception is a live identity-bound sessionless pin: when both identity tokens
authenticate its exact root, that explicit context outranks ambient cwd
discovery. Named, legacy, incomplete, stale, or mismatched pins still refuse.
Otherwise, repin to the cwd-local queue, use deliberate `--session`/`--project`
routing, or pass an explicit `--root` to confirm the active queue. Explicit
roots remain subject to the ordinary pin checks. For deliberate raw-root access,
`--ignore-session-pin` is accepted only together with a non-empty explicit
`--root`; blank `--root` and `--session` values are usage errors. `list`
remains a non-destructive inspection path: it warns on a pin mismatch but
still lists the resolved mailbox. The exact base-backlog inspection path is
quieter: an explicit `--root` equal to the current pin's own base root does
not warn (and is identity-authenticated when identity tokens are present).
Implicit, sibling, foreign, stale, and malformed contexts still warn.
Unpinned scripts and CI retain the existing fail-open behavior.

`amq doctor --root <path>` follows the same inspection-versus-mutation split:
the explicit root selects the exact target but does not repin the shell or
waive its session pin. Read-only inspection continues with a mismatch warning.
`--fix-mailboxes` and `--ops --fix-wake-locks` refuse a mismatched target unless
`--ignore-session-pin` is also supplied; that override requires an explicit
non-empty `--root`. For a session whose roster lives only in its base, use
`amq doctor --root <session> --base-root <base> --ignore-session-pin --fix-mailboxes`.
`--base-root` is config authority only, must be the target itself or its direct
parent, and never overrides the session pin.

A missing mailbox is an error, not an empty inbox. When `drain` or `list --new`
finds an actually empty inbox, it prints a stderr-only note if the same handle
has pending messages in a sibling session, including an exact non-destructive
`amq list --session <name> --me <handle> --new` command. `doctor --ops` reports
the same condition as a `sibling_backlog` warning. When the active root is a
session, an empty `drain` or `list --new` also notes unread mail for the same
handle in the base root, while `doctor --ops` reports it as a `base_backlog`
warning. Both include an exact non-destructive `amq list --root ...` command.
In JSON output, `base_backlog` hints also include a structured `backlog` object
with `root`, `current_session`, `agent`, `pending`, and `command`.
The pin is an operational safety check, not access control: a local process can
still repin the environment or use the explicit override.

Git worktrees are isolated by default when the project root is relative (for
example `{"root":".agent-mail"}`): the same session name resolves beneath each
worktree, so two agents can appear to share `collab` while reading different
mailboxes. `amq doctor --ops` warns when a linked worktree uses this local
layout and when a peer has fresher presence in the same session under another
worktree root. A `send --wait-for` timeout names its delivery root/session and
points to that diagnostic.

If agents in several worktrees should share one mailbox, give all of them the
same absolute base root. Use an absolute, machine-local `.amqrc` value such as
`{"root":"/absolute/path/to/shared/.agent-mail"}`, or remove the project-relative
`.amqrc` and export `AMQ_GLOBAL_ROOT=/absolute/path/to/shared/.agent-mail`.
Per-worktree isolation remains the default when sharing is not intended. A Git
worktree without local AMQ configuration does not implicitly inherit
`~/.amqrc`; AMQ refuses that ambiguous route so a global default cannot
silently select a different project's mailbox.

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
  --inject-arg exec --inject-arg terminal-id
```

`amq wake check` is read-only. It reports whether the current process can start
a full-strength wake, whether a saved inject-via target can repair the exact
stale wake, and the running and current AMQ image path and version. Its
`restart_capability` is one of `agent_safe`, `operator_only`, or `unavailable`,
with an exact `next_action`. Automated agents may act only on `agent_safe`.
They must leave a live wake running for `operator_only`, and must never turn a
TIOCSTI refusal into an attention-only downgrade. `doctor --ops` exposes the
same image and restart fields for every discovered wake lock.

JSON schema 1 remains the byte-compatible default. Schema 2 is explicit with
`--json-schema=2` and is available only with `--json`. It replaces prose
parsing with a closed action kind, actor, reason code, and an argv command
object when one action is directly executable. Missing evidence is an explicit
JSON `null`; `image.status="unknown"` remains a real classification. In doctor
schema 2, each wake-lock entry contains the same decision under `wake_check`
rather than duplicating the wake advice as flat fields. Check output is advice,
not authority: every advertised mutating command revalidates current wake state
before changing it.

Wake locks reported by `doctor --ops` can be `stale`, `unverified`, or, in JSON
output, any current lock state. With `--fix-wake-locks`, fixed and error states
can also appear. `stale` means AMQ proved the recorded owner is gone or is not
the same wake process, so `--fix-wake-locks` can remove the lock after a fresh
re-check. `unverified` means AMQ could not prove ownership either way, such as a
legacy lock with a live PID but no process-start token, a hostname mismatch, or
an unsupported platform. AMQ leaves `unverified` locks in place; inspect the PID
and remove the named `.wake.lock` manually only after confirming no matching
`amq wake` still owns that agent/root.

`amq wake repair` is an explicit live-session repair path. It runs when the lock
is proven `stale` or is an unverified ownerless generic claim, the lock was
created for `--inject-via`, and the agent has a saved
`agents/<agent>/.wake.target` whose digest matches the lock's repair metadata.
It also requires AMQ's private `.wake.repair-floor` to match the exact dead
generation, boot, physical queue root, owner state, and target.
That floor carries only the existing-message identities already suppressed by
the dead wake (device, inode, and ctime), never message IDs. A repaired wake
inherits it instead of re-snapshotting `inbox/new`, so messages delivered while
the notifier was down remain eligible to notify and same-name DLQ retries
remain eligible when their file identity changes. Missing, corrupt, or
mismatched continuity state fails closed and requires a normal wake restart.
Repair refuses raw terminal wake targets, leftover targets from old locks, and
unverified owner-bound or invalid claims. It supersedes an unverified ownerless
generic claim only after the saved target and continuity state pass the same
fail-closed validation. Repaired wake output goes to
`agents/<agent>/.wake.repair.log`; `doctor --ops` can report whether repair is
available, but it never starts a wake process.

`amq wake recover-owner` is the separate recovery path for an owner-bound
`coop exec --wake-inject-via` claim. A live owner may release only its exact
claim from the same OS session, using the inherited `AMQ_WAKE_OWNER` token.
When the exact owner is dead, recovery does not require that token. AMQ stops
only an identity-confirmed wake, re-checks the claim after every wait, and
fails closed without mutation when the owner or claim is unknown, legacy, or
corrupt. There is no force mode. The ownerless `repair`, `retire`, and
`doctor --ops --fix-wake-locks` paths refuse owner-bound claims.

`amq wake retire` is the exact managed-shutdown path. It requires the caller's
expected `--inject-via` executable and ordered `--inject-arg` values. A live
wake is retired only when its process identity, unchanged lock generation, and
saved target all match: Linux signals through its pidfd capability and macOS
uses the generation-bound cooperative control socket. An exactly-bound
proven-stale lock may be removed without signaling. The mailbox and saved
target are preserved in either case; raw and unverified wakes fail closed.

The lifecycle boundaries are:

- repair = replace a proven-stale inject-via wake.
- recover-owner = stop and release one exact owner-bound inject-via claim.
- `doctor --ops --fix-wake-locks` = remove a proven-stale lock.
- retire = stop an identity-confirmed live inject-via wake.
- launchd, systemd, or the owning shell = stop a raw wake.
- retire neither unloads supervisors nor promises that they will not restart a wake.

`amq who` and `amq doctor --ops` distinguish two activity sources:

- `notifier_live` means AMQ verified the process identity behind a valid
  `amq wake` lock. It proves prompt notification is attached; it does **not**
  prove messages are consumed.
- `recent_activity` means `last_seen` was refreshed in the last 10 minutes,
  without a verified live notifier.

Consumption remains the job of `drain` or `monitor` and is evidenced by
receipts. For long-running `wake` and `monitor` examples under systemd or
launchd, see [Supervisor recipes](COOP.md#supervisor-recipes).

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
| Collaboration | `coop init`, `coop exec`, `swarm list`, `swarm join`, `swarm tasks`, `swarm bridge` |
| Integrations | `integration symphony init`, `integration symphony emit`, `integration kanban bridge` |
| Operations | `presence set`, `presence list`, `route explain`, `who`, `doctor`, `doctor --ops`, `wake check`, `wake repair`, `wake recover-owner`, `wake retire`, `cleanup`, `dlq *`, `upgrade`, `env`, `shell-setup` |

Canonical schema-selecting diagnostic forms:

```text
amq wake check --me <agent> [--root <path>] [--strict] [--json] [--json-schema <1|2>]
amq doctor [--root <path>] [--base-root <path>] [--ignore-session-pin] [--ops] [--fix-wake-locks] [--fix-mailboxes] [--json] [--json-schema <1|2>]
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

The numeric meaning is the machine contract; stderr is human-readable context
and should not be parsed as a stable discriminator. `--json` does not change
these process exit codes. A read-only `list` on a mismatched session pin warns
and continues; commands that consume or mutate mailbox state fail with code
`5`.

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
Native Windows supports the core queue, but not `coop exec` or `wake`. Use WSL
with the Linux binary for the complete co-op workflow. See the explicit
[platform capability matrix](INSTALL.md#platform-capability-matrix).

**Is this production-ready?**
For local development workflows, yes. AMQ is intentionally simple—it's not trying to be a distributed message broker.

**How does AMQ compare to other multi-agent tools?**
Tools like [MCP Agent Mail](https://github.com/Dicklesworthstone/mcp_agent_mail) (server-based coordination + SQLite), [Gas Town](https://github.com/steveyegge/gastown) (tmux-based orchestration), and others offer richer features. AMQ is intentionally minimal: single binary, no server, Maildir delivery. Best for 2-3 agents on one machine.

## License

MIT
