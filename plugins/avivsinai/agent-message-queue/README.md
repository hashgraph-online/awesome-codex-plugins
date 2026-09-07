# Agent Message Queue (AMQ)

[![CI](https://github.com/avivsinai/agent-message-queue/actions/workflows/ci.yml/badge.svg)](https://github.com/avivsinai/agent-message-queue/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/avivsinai/agent-message-queue)](https://github.com/avivsinai/agent-message-queue/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**A local, file-based interoperability bus for agent sessions and adapters.**

AMQ manages the conversation: agent-to-agent messaging, thread continuity, cross-session and cross-project routing, handoff state, and operational visibility. It does not try to own task decomposition, worktree management, dependency scheduling, or scheduler execution; Claude Code teams, Codex, Kanban, Symphony, and similar orchestrators stay one layer above it.

**Start here:** [Getting started](#getting-started) — install, start two agents, send one message.

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
- **Real-time notifications** — `amq wake` injects terminal notifications when messages arrive.
- **Built for agents** — Priority levels, message kinds, threading, delivery receipts, and waitable handoffs.
- **Cross-project federation** — Route messages across peer repos, preserve reply routing, and run decision threads that span projects.
- **Swarm mode** — Join Claude Code Agent Teams, claim tasks, and bridge task notifications into AMQ.
- **Optional adapters** — Lightweight Symphony hooks and an experimental Kanban bridge can emit normal AMQ messages with structured metadata.
- **Operational diagnostics** — `amq doctor --ops` shows queue depth, sibling-session backlogs, DLQ state, presence freshness, and integration hints.
- **Two-host fleets** — Companion `amq-bridge` hops signed envelopes between two local AMQ roots (`apply-file` today; HTTPS courier when an operator provisions a rendezvous).

### v1 will not

AMQ Core stays a local CLI. These stay out of the `amq` binary and out of v1
product claims (see [two-host fleets](docs/adr-two-host-fleets.md) and
[bridge protocol](docs/adr-bridge-protocol.md)):

- sockets or listeners in `amq`
- Maildir sync or remote drain of a foreign mailbox
- git as the cross-host relay
- OAuth MCP inside `amq`, ACP v2, or `--always-approve` in committed launch plans
- prompt-selected `--root` / argv / env / executable
- AMQ holding a Buzz nsec; Mac mailbox files on the Grok Bot VM
- silent inject→notify or submit→prefill; Accessibility scraping of ChatGPT

Cross-host mail is companion `amq-bridge` (alias send / local apply / same-thread reply), not Core. The proven hop is `amq-bridge apply-file` on the destination host. The HTTPS courier stays implemented for an operator-provided rendezvous; AMQ does not ship a hosted relay. See [amq-bridge](cmd/amq-bridge/README.md).

![AMQ Demo — Claude and Codex collaborating via split-pane terminal](docs/assets/demo.gif)

<a id="quick-start"></a>

## Getting started

About five minutes from install to the first delivered message. You need two
agent CLIs on `PATH`. This walkthrough uses **Claude Code** (`claude`) and
**Codex CLI** (`codex`) on one machine. `amq setup` also detects Grok Build
(`grok`) and Cursor when `agent` is on `PATH` (or legacy `cursor-agent` if
`agent` is absent).

Native Windows can run the core queue from the Windows ZIP, but this
walkthrough needs `coop exec` and `wake`, which are not supported natively.
Use WSL with the Linux binary. See the
[platform capability matrix](INSTALL.md#platform-capability-matrix).

### 1. Install the binary

**macOS (Homebrew):**

```bash
brew install avivsinai/tap/amq
```

**macOS / Linux (script):**

```bash
curl -fsSL https://raw.githubusercontent.com/avivsinai/agent-message-queue/main/scripts/install.sh | bash
```

The script installs to `~/.local/bin` or `~/go/bin` (no sudo). Review it
before running. It fails unless `checksums.txt` has exactly one valid entry
for the selected asset and `sha256sum` or `shasum` verifies it before
extraction.

Verify:

```bash
amq --version
```

Manual download, Windows ZIP, and build-from-source are in
[INSTALL.md](INSTALL.md).

### 2. Install Skill

So each agent knows the AMQ commands:

```bash
npx skills add avivsinai/agent-message-queue -g -y
```

If you used the install script instead of Homebrew, you can do binary and
skill in one step:

```bash
curl -fsSL https://raw.githubusercontent.com/avivsinai/agent-message-queue/main/scripts/install.sh | bash -s -- --skill
```

Other skill methods (skild, marketplace, manual copy) are in
[INSTALL.md](INSTALL.md). Restart the agent after installing.

### 3. Set up the project

In the repository the two agents will share:

```bash
amq setup
```

Setup probes for Claude, Codex, and Grok (and Cursor when present), previews the
roster and launcher preference, then writes `.amqrc`, `.amq/launch.json`,
local preferences, the default session, and roster mailboxes. Confirm the
preview.

If setup reports `no supported agent CLI detected`, install `claude` and
`codex`, put them on `PATH`, and run `amq setup` again.

### 4. Start both agents

```bash
amq launch
```

The first launch asks you to trust the plan. That confirmation is stored
outside the worktree.

- If launch selects `tmux`, `cmux`, or `ghostty`, both agents start in that
  app.
- If launch selects the `commands` backend, it prints one complete
  `coop exec` line per agent and exits `6`. Paste each emitted line into
  its own terminal. Do not rewrite the lines: they bind the session, launch
  nonce, provider arguments, and execution ticket.

Start both agents before sending. A newly started wake baselines messages
that were already waiting, so they stay unread but do not notify. If you
sent first, run `amq drain --include-body` in the target agent.

### 5. Send one message and see it arrive

In the Claude terminal (`AM_ME` is already set):

```bash
amq send --to codex --subject "Hello" --body "Can you see this?"
```

In the Codex terminal:

```bash
amq list --new
amq drain --include-body
```

You should see Claude's message, then the drained body. That is the loop:
`send` on one side, `list` / `drain` on the other. Reply with
`amq reply --id <msg_id> --body "..."` when you have a message ID.

Roles, phases, and troubleshooting live in [COOP.md](COOP.md). Daily
commands after this first message are in [Messaging](#messaging) below.

## Installation

The default install is in [Getting started](#getting-started). More methods
(releases ZIP, checksums, source build, skill marketplace) are in
[INSTALL.md](INSTALL.md).

### Updating

Homebrew:

```bash
brew upgrade amq
```

`amq upgrade` checks the raw and resolved executable paths against every
evidenced or executable-derived Homebrew prefix and delegates to the matched
Homebrew executable instead of overwriting the Cellar; pass `amq upgrade -y`
to run the delegate without an AMQ prompt. The package manager may still
prompt. Scoop installs on Windows are scoped as user (`$SCOOP` or the default
`%USERPROFILE%\scoop`) or global (`$SCOOP_GLOBAL` or `C:\ProgramData\scoop`);
the matched `scoop` executable receives `scoop update amq` for user scope or
`scoop update -g amq` for global scope.

Retire live wakes started by the previous Cellar binary first. If a leftover
lock's image directory is gone, `wake check` reports `binary_dir_gone`;
remove it with `amq doctor --ops --fix-wake-locks`. See
[Wake operations](docs/wake-operations.md).

GitHub Actions `verify-brew-release` confirms a published tag installs from
`avivsinai/tap/amq` and that `amq --version` matches that tag. It does not
replace `brew upgrade` on an operator machine.

Install-script or other manual binary installs outside an evidenced Homebrew
prefix keep the direct download and atomic-replace path:

```bash
amq upgrade
```

Upgrade the companion binaries (`amq-keepalive`, `amq-bridge`, `amq-acp`)
that sit in the raw or resolved executable directory of a direct-install
`amq`, or in `~/.local/bin`, from the same release tag, with checksum
verification:

```bash
amq upgrade --all
```

The command plans one verified target per companion, unique across all
companions, before any companion replacement. It verifies each target's Go
build identity. Missing companions are skipped with a line; cross-companion
aliases, wrong builds, and multiple distinct targets refuse the upgrade and
give a repair action. Same-name symlink aliases to one canonical target are
accepted; same-name hardlinks refuse. A
running `amq-keepalive` is never killed: the atomic rename swaps the path
while the running process keeps the old image.
When the upgraded path is the supervisor's path, `amq upgrade --all` notes
that self-upgrade can pick up a strictly newer image on its next supervise pass. A
supervisor started with `--no-self-upgrade` must be restarted through its
service manager; on macOS use `amq-keepalive install-launchd`, and on Linux
restart the service unit, for example
`systemctl --user restart amq-keepalive.service`. Companions are
direct-installed only; the
Homebrew formula and Scoop manifest ship `amq` itself, so `--all` under a
package-managed install is a no-op with an explanatory line. Companion links
are revalidated by their primary path; a secondary same-name alias repointed
during download is not detected.

`AMQ_CACHE_DIR` overrides the update cache location used by `amq upgrade` and
the background update notifier. When unset, the platform cache
(`~/Library/Caches` on macOS, `XDG_CACHE_HOME` or `~/.cache` on Linux and
other Unix systems, and the user's Local AppData cache on Windows) is used.
`internal/update.DefaultCachePath` is the sole authority for the platform
update-cache path. For the direct-upgrade cache-writing path, a set override
must resolve to an absolute path; AMQ fails before replacement rather than
silently falling back to the platform cache. The version cache is refreshed
after an authoritative direct check confirms the latest version (already
current, or after a successful immediate replacement). A later companion
failure does not change that result. A scheduled replacement is reflected when
the next successful check refreshes the cache (best-effort).

On Windows, `amq upgrade --all` upgrades a directly installed
`amq-keepalive.exe`; it skips `amq-bridge` and `amq-acp`, which are not
published for Windows, then continues with the core upgrade.

### Keepalive companion

`amq-keepalive` is developed and released from this repository alongside AMQ.
`make build` produces both binaries, and each AMQ release includes a separate
`amq-keepalive` archive stamped with the same release version, including a
native Windows ZIP. Verify a build
with any equivalent form:

```bash
amq-keepalive -v
amq-keepalive --version
amq-keepalive version
```

See [COOP.md](COOP.md#supervisor-recipes) for the operational guide.

## Setup and launch

`amq setup` is the one-time project configuration. `amq launch` reconciles
the committed roster and starts or resumes that session.

```bash
amq setup
amq launch
amq session create feature-x   # once, before the first named-session launch
amq launch --session feature-x
amq session resume feature-x
```

`launch` reads the committed roster, selects the declared default session
when `--session` is absent, and resumes exact provider-qualified conversation
IDs. It never uses a provider's "last" or "continue" heuristic. The first
semantic plan, and each semantic plan change, requires an interactive trust
confirmation stored outside the worktree. Non-interactive or `--json` calls
exit `6` until that digest is trusted. An unknown `session resume` name
exits `3` and writes nothing. Managed backends use a fail-closed recovery
journal; see [Managed launch recovery](docs/launch-recovery.md).

Registered launchers are `commands`, `tmux`, `cmux` (envelope `>=0.64.3 <1.0`,
protocol 2), and `ghostty` (AppleScript, envelope `>=1.3.0 <2.0`).
`--launcher auto` is the default: it walks the local launcher preference and
selects the first backend whose Detect reports Available. An explicit
`--launcher <name>` wins. When `CMUX_SURFACE_ID` is set, auto prepends
`cmux` ahead of `ghostty`; otherwise `TERM_PROGRAM=ghostty` prepends
`ghostty`. Setup lists cmux and Ghostty in `available_launchers` only after
their Detect ping succeeds, not from `LookPath` alone.

The `commands` backend prints complete `coop exec` commands and exits `6`
because executing them is the remaining operator action. Paste those emitted
lines exactly, one per terminal. Managed `tmux`, `cmux`, and `ghostty`
backends run the declared plan in-app instead of printing those lines.

Grok Build is also supported by the managed launch adapter. It mints an exact
`--session-id` from the AMQ launch nonce and resumes only with the stored
`--resume <UUID>`; `--continue`, `--always-approve`, and `--yolo` are rejected
from committed launch arguments. Grok uses `--tools` / `--disallowed-tools`
with opaque provider names (not Claude `--allowedTools`).

Each launched agent gets a session environment and wake notifications. See
[COOP.md](COOP.md#running-co-op-mode) for co-op operations.

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
      "resume_policy": "resume"
    },
    {
      "handle": "codex",
      "adapter": "codex",
      "command": ["codex", "--sandbox", "workspace-write", "--ask-for-approval", "on-request"],
      "resume_policy": "resume"
    }
  ],
  "layout": {"type": "columns"}
}
```

Dangerous permission-bypass flags are not valid committed arguments. Keep
them in an operator-controlled direct `coop exec` invocation when that
low-level path is intentionally required.

Direct `coop exec` names the provider session by default as
`<session>/<handle>` (or `<handle>` for a sessionless root). Claude and Pi
receive the name in their argv. Codex and Cursor `agent` receive a best-effort
TUI rename after AMQ verifies the newly created session. Codex supports direct
resume by name, for example `codex resume session1/codex`. Cursor `agent`
resumes through its picker only; resume-by-name is unproven. Set
`--named=false`, `AMQ_COOP_NAMED=0`, or `"named": false` in `.amq/launch.json`
to disable it. Explicit provider names and resume or continue flags remain
unchanged, including `codex resume` and `agent --resume`. Managed launches keep
naming disabled until their provider-name contract is available.

### Named sessions

For isolated pairs (multiple pairs on different features):

```bash
amq session create feature-a
amq launch --session feature-a
```

When launch uses the `commands` backend, paste the complete emitted commands
into separate terminals.

### Non-interactive setup

Automation uses a stateless preview and applies only that approved digest.
The first non-interactive setup must name the roster, default session, and
launcher preference explicitly:

```bash
setup_args=(--agents claude,codex --default-session collab --launcher-preference commands)
setup_preview="$(amq setup --preview --json "${setup_args[@]}")"
setup_digest="$(printf '%s\n' "$setup_preview" | jq -r '.preview.digest')"
amq setup --apply "$setup_digest" "${setup_args[@]}"
```

`--preview` performs zero writes. `--apply` recomputes the preview and exits
`6` without writing if its `sha256:<hex>` digest differs. `-y` remains
available for callers that already own an approval gate, but it cannot be
combined with `--preview` or `--apply`.

### Shell aliases

Optional aliases are a convenience, not part of [Getting started](#getting-started).
A bare `eval "$(amq shell-setup)"` affects only the current shell. To make
aliases such as `amc`, `amx`, and `amg` available in future terminals, add
the setup command to your shell startup file:

```bash
# zsh
amq shell-setup --shell zsh >> ~/.zshrc

# bash
amq shell-setup --shell bash >> ~/.bashrc
```

Run the appropriate append command once, then open a new terminal or source
that startup file. Use the bare `eval` only when you intentionally want
aliases in one already-open shell.

`coop init` and direct `coop exec` provisioning remain available as legacy
low-level plumbing. See [COOP.md](COOP.md#low-level-provisioning) for those
paths, operator-only bypass examples, and advanced wake options; they are
not a second project-onboarding flow.

Scripts and orchestrators that must plan and apply a session without parsing
human output should use the public launch contract in
[docs/launch-api.md](docs/launch-api.md) and
[schemas/launch-api-v1.schema.json](schemas/launch-api-v1.schema.json).

## Messaging

Inside a launched agent, identity and session are already set:

```bash
amq send --to codex --subject "Review needed" --kind review_request \
  --body "Please review internal/cli/send.go"

amq list --new
amq list --new --priority urgent
amq list --new --from codex --kind review_request

amq drain --include-body

amq send --to codex --body "Please pick this up" \
  --wait-for drained --wait-timeout 60s

amq receipts list --me codex --msg-id <msg_id>

amq reply --id <msg_id> --kind review_response --body "LGTM with comments"
```

To send between known sessions before entering `coop exec`:

```bash
amq send --root .agent-mail --from-session feature-a --me claude \
  --to codex --session feature-b --body "Please review the setup"
```

`read`, `drain`, and `monitor` apply the same strict message validation.
Invalid messages move to DLQ and produce a `dlq` receipt. Participating
shells also pin their exact session context and refuse mismatched mailbox
operations. See [Session routing and safety](docs/session-routing.md).

## Health

```bash
amq doctor
amq doctor --ops
amq wake check --me <agent>
```

`amq wake check` is read-only. It reports whether this process can start or
repair a wake, and a `restart_capability` of `agent_safe`, `operator_only`,
or `unavailable` with an exact next action. Automated agents may act only on
`agent_safe`; leave a live wake running otherwise.

Wake lock states, JSON schema 2, repair, owner recovery, retirement, and
quarantine rules are in [Wake operations](docs/wake-operations.md),
[wake lifecycle](docs/wake-lifecycle.md), and
[wake state invariants](docs/wake-state-invariants.md). Consumption itself
is `drain` / `monitor`, evidenced by receipts. Long-running `wake` /
`monitor` under systemd or launchd is in
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

`--json-schema` requires `--json`. Diagnostic schema 2 and the public launch
`--plan` / `--prepare` / `--apply` forms are in
[docs/wake-lifecycle.md](docs/wake-lifecycle.md) and
[docs/launch-api.md](docs/launch-api.md). Use `amq <command> --help` for
exact flags.

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

1. **Write** — Message written to a unique attempt file in `tmp/`
2. **Sync** — File fsynced to disk
3. **Deliver** — No-replace publication to `new/` (never overwrites a retained
   same-name message; identical bytes are idempotent)
4. **Process** — Reader moves to `cur/` after reading

If a different same-name message is already in `new/`, AMQ preserves both
copies and reports a collision. A claim never replaces a retained same-name
message in `cur/`.

This guarantees crash-safety: if the process dies mid-write, no corrupt message appears in the inbox. See [CLAUDE.md](CLAUDE.md) for the full directory layout.

## Built on AMQ

AMQ is meant to be the messaging layer underneath higher-level orchestrators. Projects building on it:

- **[amq-squad](https://github.com/omriariav/amq-squad)** by [@omriariav](https://github.com/omriariav) — a role-aware agent team launcher. AMQ owns messaging between agents; amq-squad owns the layer above: who is on the team, what role each agent plays, the shared norms they follow, and how to bring the whole squad up, down, back, or into a new workstream. It builds on AMQ's [extension metadata](#extension-metadata) surface for launch records and role state.

Building something on AMQ? Open an issue or PR to be listed here.

## Documentation

- [Getting started](#getting-started) — Install, start two agents, send one message
- [INSTALL.md](INSTALL.md) — Alternative installation methods
- [docs/amq-keepalive.md](docs/amq-keepalive.md) — Keepalive command and safety reference
- [cmd/amq-bridge/README.md](cmd/amq-bridge/README.md) — Two-host courier: identity, apply-file, HTTPS rendezvous
- [docs/adr-two-host-fleets.md](docs/adr-two-host-fleets.md) — Two-host identity, aliases, receipts, v1 kill-list
- [docs/adr-bridge-protocol.md](docs/adr-bridge-protocol.md) — Bridge envelope, auth, and transport
- [cmd/amq-acp/README.md](cmd/amq-acp/README.md) — Preview ACP v1 stdio companion and Buzz BYOH JSON
- [docs/session-routing.md](docs/session-routing.md) — Session selection, routing guards, and worktree behavior
- [docs/wake-operations.md](docs/wake-operations.md) — Wake inspection, repair, recovery, and retirement
- [docs/wake-lifecycle.md](docs/wake-lifecycle.md) — Wake lock/target state contract, self-upgrade, log retention, JSON schema, injector identity
- [docs/wake-doorbell-acknowledgement.md](docs/wake-doorbell-acknowledgement.md) — Wake retry ladder and `--retry-until` acknowledgement contract
- [docs/wake-state-invariants.md](docs/wake-state-invariants.md) — Wake artifact ownership, lock states, and quarantine invariants
- [docs/adapter-contract.md](docs/adapter-contract.md) — Formal v1 adapter contract for integration messages
- [docs/adr-layer-extensions.md](docs/adr-layer-extensions.md) — ADR for stable layer extension surfaces
- [docs/trace.md](docs/trace.md) — Read-only trace contract and evidence limits
- [docs/launch-api.md](docs/launch-api.md) — Public launch intent, Prepare/Apply flow, compatibility floor, and schema
- [COOP.md](COOP.md) — Co-op workflow and supervisor operations
- [CLAUDE.md](CLAUDE.md) — Agent instructions, CLI reference, architecture

## Development

```bash
git clone https://github.com/avivsinai/agent-message-queue.git
cd agent-message-queue
make build   # Build amq plus companion binaries
make test    # Run tests
make ci      # Full CI: vet + lint + test + smoke
```

## FAQ

**Why not just use a database?**
Files are universal, debuggable, and work everywhere. No connection strings, no migrations, no ORM. Just files.

**Why not Redis/RabbitMQ/etc?**
Those require infrastructure. AMQ is for local inter-process communication where agents share a filesystem. No server to configure or keep running.

**What about Windows?**
Native Windows supports the core queue and direct submitted injection into a
live Codex or Claude Code session through `amq-keepalive.exe`; it does not
support `coop exec`, `amq wake`, or terminal supervision. Use WSL with the
Linux binary for the complete co-op workflow. See the explicit [platform
capability matrix](INSTALL.md#platform-capability-matrix).

**Is this production-ready?**
For local development workflows, yes. AMQ is intentionally simple—it's not trying to be a distributed message broker.

**How does AMQ compare to other multi-agent tools?**
Tools like [MCP Agent Mail](https://github.com/Dicklesworthstone/mcp_agent_mail) (server-based coordination + SQLite), [Gas Town](https://github.com/steveyegge/gastown) (tmux-based orchestration), and others offer richer features. AMQ is intentionally minimal: single Core binary, no server, Maildir delivery. Best for a handful of local agents. Two machines use companion `amq-bridge`, not a shared filesystem.

## License

MIT
