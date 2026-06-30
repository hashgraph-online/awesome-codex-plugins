---
name: amq-cli
version: 0.39.0
description: >-
  Coordinate agents via the AMQ CLI for file-based inter-agent messaging. Use
  this skill whenever you need to send messages to another agent (codex, claude,
  or any named handle), check your inbox, drain queued messages, set up co-op
  mode between agents, join a swarm team, route messages across projects, or
  diagnose delivery issues. Also use it when you receive a message and need to
  know how to reply, inspect receipts, or handle priority. Covers any multi-agent
  coordination task where agents need to talk to each other — review requests,
  questions, status updates, decision threads, wake notifications, and
  orchestrator integration (Symphony, Kanban). For collaborative spec/design
  workflows specifically, prefer the /amq-spec skill which provides structured
  phase-by-phase guidance. Not intended for distributed systems design
  (RabbitMQ, Kafka), CI/CD pipelines, or single-agent tasks with no partner.
metadata:
  short-description: Inter-agent messaging via AMQ CLI
  compatibility: claude-code, codex-cli
---

# AMQ CLI Skill

File-based message queue for agent-to-agent coordination.

AMQ manages the conversation, not the task plan. Use it for messaging, routing, replies, and adapter-emitted lifecycle events; keep work decomposition and execution in the orchestrator above it.

## Prerequisites

Requires `amq` binary in PATH. Install:
```bash
curl -fsSL https://raw.githubusercontent.com/avivsinai/agent-message-queue/main/scripts/install.sh | bash
```

## Environment Rules

AMQ primarily uses two env vars for routing: `AM_ROOT` (which mailbox tree) and `AM_ME` (which agent). Getting these wrong means messages go to the wrong place or silently disappear, so it matters to let the CLI handle them rather than guessing.

**Inside `coop exec`** — everything is pre-configured. Just run bare commands:
```bash
amq send --to codex --body "hello"     # correct
amq send --me claude --to codex ...    # wrong — --me overrides the env
./amq send ...                         # wrong — use amq from PATH
```
The reason: `coop exec` sets `AM_ROOT` and `AM_ME` precisely for the session. Passing `--me` overrides the env, and passing `--root` intentionally overrides the current root (the CLI will note that on stderr if it differs from `AM_ROOT`). Prefer bare commands unless you mean to target a different root.

**Outside `coop exec`** — resolve the root from config, don't hardcode it:
```bash
eval "$(amq env --me claude)"          # reads .amqrc chain, sets both vars
eval "$(amq env --session auth --me claude --export)"  # pin this terminal to one session

# Or pin per-command without polluting the shell (useful in scripts):
AM_ME=claude AM_ROOT=$(amq env --json | jq -r .root) amq send --to codex --body "hello"
```
Why not hardcode? The root path depends on the config chain (project `.amqrc` → `AMQ_GLOBAL_ROOT` → `~/.amqrc`). Hardcoding skips this and breaks when the project moves or config changes.
Use `--export` only when the whole terminal should stay pinned; it exports `AM_BASE_ROOT` for session roots and prints a stderr note. Treat it as one terminal, one session.

**Global fallback**: Orchestrator-spawned agents often start outside the repo root where no project `.amqrc` exists. Set `AMQ_GLOBAL_ROOT` or `~/.amqrc` so `amq env` and `amq doctor` still resolve the correct queue.

**Session pitfall**: `coop exec` defaults to `--session collab` (i.e., `.agent-mail/collab`). Outside `coop exec`, the base root is `.agent-mail` (no session suffix). These are different mailbox trees — don't mix them up.

### Root Resolution Truth-Table

| Context | Command | AM_ROOT resolves to |
|---------|---------|---------------------|
| Outside `coop exec` | `amq env --me claude` | resolved base root from project `.amqrc`, detected `.agent-mail`, `AMQ_GLOBAL_ROOT`, or `~/.amqrc` |
| Outside `coop exec`, no project `.amqrc` | `amq env --me claude` | detected `.agent-mail` in the current tree, otherwise `AMQ_GLOBAL_ROOT` or `~/.amqrc` |
| Outside `coop exec`, isolated session | `amq env --session auth --me claude` | `<resolved-base-root>/auth` |
| Inside `coop exec` (no flags) | automatic | `.agent-mail/collab` (default session) |
| Inside `coop exec --session X` | automatic | `.agent-mail/X` |

## Task Routing

Before diving in, match the task to the right workflow — this avoids wasted effort:

| Your task | What to do |
|-----------|-----------|
| **"spec", "design with", "collaborative spec"** | Use `/amq-spec` instead — it has structured phase-by-phase guidance for parallel-research workflows. |
| **Send a message, review request, question** | Use `amq send` (see Messaging below) |
| **Swarm / agent teams** | Read [references/swarm-mode.md](references/swarm-mode.md), then use `amq swarm` |
| **Received message with labels `workflow:spec`** | Follow the spec skill protocol: do independent research first, then engage on the `spec/<topic>` thread — don't skip straight to implementation. |

## Quick Start

```bash
# One-time project setup
amq coop init

# Per-session (one command per terminal — defaults to --session collab)
amq coop exec claude -- --dangerously-skip-permissions  # Terminal 1
amq coop exec codex -- --dangerously-bypass-approvals-and-sandbox  # Terminal 2
```

Without `--session` or `--root`, `coop exec` defaults to `--session collab`.

## Statusline (Claude Code)

To show the current AMQ session in your Claude Code status bar, add this snippet to your statusline script (e.g., `~/.claude/statusline.sh`):

```bash
# AMQ session segment — try CLI first, fall back to env vars for older amq versions
amq_session=""
if _amq_out=$(amq env --session-name 2>/dev/null) && [ -n "$_amq_out" ]; then
    amq_session="$_amq_out"
elif [ -n "$AM_ROOT" ] && [ -n "$AM_BASE_ROOT" ] && [ "$AM_ROOT" != "$AM_BASE_ROOT" ]; then
    amq_session=$(basename "$AM_ROOT")
fi
if [ -n "$amq_session" ]; then
    output+=$(printf " | \033[33mamq:%s\033[0m" "$amq_session")
fi
```

`amq env --session-name` (v0.27+) prints the session name and exits 0 (empty when not in a session). The env-var fallback covers older versions. `amq env --json` also includes `session_name`.

To also set the terminal tab title (works in Ghostty, iTerm2, Terminal.app):

```bash
# Set tab title to "repo | amq:session" — re-asserts on each statusline refresh.
# Manual titles (e.g. Ghostty's prompt_tab_title) take priority and won't be overwritten.
tab_title="$repo_name"
[ -n "$amq_session" ] && tab_title+=" | amq:${amq_session}"
printf '\033]0;%s\007' "$tab_title" > /dev/tty 2>/dev/null
```

## Integration & Ops Quick Reference

```bash
# Global fallback for orchestrator-spawned agents
export AMQ_GLOBAL_ROOT="$HOME/.agent-mail"

# Symphony hooks
amq integration symphony init --me codex
amq integration symphony emit --event after_run --me codex

# Cline Kanban bridge
amq integration kanban bridge --me codex
amq integration kanban bridge --me codex --workspace-id my-workspace

# Runtime diagnostics
amq doctor --ops
amq doctor --ops --json
```

## Delivery Receipts

AMQ records delivery outcomes in consumer-local receipt files. The main stages are:

- `drained` — a consumer successfully ingested the message
- `dlq` — the message was moved to the dead letter queue during ingest

Use these when you need confirmation rather than just fire-and-forget messaging:

```bash
# Block on delivery for a single-recipient send
amq send --to codex --body "please review" --wait-for drained --wait-timeout 60s

# Query receipt history later
amq receipts list --me codex --msg-id <msg_id>
amq receipts wait --me codex --msg-id <msg_id> --stage drained --timeout 60s
```

`amq read`, `amq drain`, and `amq monitor` all apply the same strict header validation. Messages in `inbox/new` that are corrupt or have malformed headers are moved to DLQ and produce a `dlq` receipt.

## Session Layout

By default, the root is `.agent-mail` (from `.amqrc` or auto-detect). Use `--session` to create isolated subdirectories:

```
.agent-mail/              ← default root (configurable in `.amqrc`)
.agent-mail/auth/         ← isolated session (via --session auth)
.agent-mail/api/          ← isolated session (via --session api)
```

- `amq coop exec claude` → `AM_ROOT=.agent-mail/collab` (default session)
- `amq coop exec --session auth claude` → `AM_ROOT=.agent-mail/auth`

The main env vars are `AM_ROOT` (where) + `AM_ME` (who). `coop exec` may also set `AM_BASE_ROOT` for cross-session resolution. The CLI enforces correct routing — just run `amq` commands as-is.
Default `.agent-mail/<session>` layouts are recognized even without `.amqrc`; custom root names still need config or explicit flags/env.

## Cross-Project Routing

Send messages to agents in other projects via `--project` or inline `@project:session` syntax. Requires peer configuration in `.amqrc`.

**When to use `--session` vs `--project`**: `--session` = same project, different session. `--project` = different project. Change one dimension at a time.

### Peer setup

Add `project` and `peers` to your `.amqrc`:
```json
{
  "root": ".agent-mail",
  "project": "my-project",
  "peers": {
    "infra-lib": "/Users/me/projects/infra-lib/.agent-mail"
  }
}
```

Both projects must register each other as peers for round-trip messaging.

**Use `--project`/`--session` to route, not a raw `--root`.** A direct `--root` selects which tree to operate on; it carries no sender-origin metadata, so the recipient can't reply (a naive reply loops back into their own tree). `amq send` therefore **refuses** an explicit `--root` that crosses into a different base tree than your active session (`AM_ROOT`/`AM_BASE_ROOT`) when no `--project`/`--session`/`--from-session` is given. To message another project replyably, register the peer and use `--project` (or inline `@project`). If a send is genuinely local, set the target as your `AM_ROOT` instead of passing `--root`.

### Sending cross-project

```bash
# Flag syntax
amq send --to codex --project infra-lib --body "hello from here"

# Inline syntax (terser)
amq send --to codex@infra-lib:collab --body "inline syntax"

# Same session name as source (default when --session omitted)
amq send --to codex --project infra-lib --body "delivers to same session"
```

### Replies route automatically

When you receive a cross-project message, `reply_project` is set in the header. `amq reply` routes back automatically — no `--project` flag needed:
```bash
amq reply --id <msg_id> --body "got it"  # routes back via reply_project
```

### Thread naming

- **Same project P2P**: `p2p/claude__codex`
- **Cross-project P2P**: `p2p/projA:collab:claude__projB:collab:codex`
- **Topical** (cross-project): use same thread ID across projects, e.g., `decision/release-v0.24`

For full details, see [references/cross-project.md](references/cross-project.md).

### Cross-project identity (IMPORTANT)

When you receive a message where `from` matches your own handle (e.g., `from: "claude"` and you are claude), check `from_project` and `reply_project`. If either is present and names a different project, this is **NOT an echo** — it is a legitimate cross-project message from a different agent instance with the same handle. Process it normally.

### AM_ROOT scoping after cross-project sends

After sending a cross-project message (via `--project`), your `AM_ROOT` still points to YOUR project. To send to your own partner (same project), use plain `amq send --to codex` — do NOT use `--project`. The `--project` flag is ONLY for sending to agents in OTHER projects.

## Decision Threads

Decentralized decision protocol using existing AMQ primitives (no new CLI commands).

- **Thread**: `decision/<topic>`
- **Kind**: `decision` for all messages
- **Labels**: `decision:proposal`, `decision:objection`, `decision:support`, `decision:final`; plus `project:<name>` for cross-project decisions
- **Context** on proposals: `{"proposal_id": "...", "question": "...", "options": [...], "required_projects": [...], "deadline": "..."}`

**Process**: Propose → Review/Object → Resolve objections → Close when all required projects responded and no unresolved blocking objections.

```bash
amq send --to codex --project infra-lib --kind decision \
  --labels "decision:proposal,project:my-project,project:infra-lib" \
  --thread "decision/api-v2" \
  --context '{"proposal_id":"api-v2","question":"Adopt new API?","required_projects":["my-project","infra-lib"]}' \
  --body "Proposal: migrate to API v2. All tests green."
```

## Session-Aware Routing

Users refer to sessions using many words: "session", "stream", "squad", "team", "workspace", "channel", or just a bare name. When the user mentions sending to or talking to an agent in a named context (e.g., "ask codex on stream1", "send to the auth team", "talk to codex in squad-api"), you must discover sessions before routing.

**Important**: Do not confuse sessions with projects. "Project" in AMQ means a different repo/codebase (cross-project routing via `--project`). Sessions are isolated mailbox trees within the same project (via `--session`). If the user says "the infra project", that likely means `--project infra`, not `--session infra`.

```bash
# Step 1: Discover active sessions and agents
amq who --json
# Returns: [{"name":"collab","agents":[...]},{"name":"stream1","agents":[...]},{"name":"auth","agents":[...]}]

# Step 2: Match the user's name against session names in the output, then send
amq send --to codex --session stream1 --body "Message for stream1"
```

**Recognition patterns** — any of these mean "route to a specific session":
- Explicit: "on stream1", "via auth", "in the api session", "the infra squad"
- Bare name: user just says "stream1" or "auth" — could be a session or an agent handle
- Colloquial: "team", "squad", "stream", "workspace", "channel" followed by a name

Note: The `agent@name` inline syntax (e.g., `codex@infra`) is for cross-project routing, not cross-session. For same-project session routing, always use `--session <name>` explicitly.

**Rules**:
1. When the user names something that could be a session, **always run `amq who --json` first** to check if it matches a known session name
2. If the name matches a session, use `--session <name>` on the send command
3. If it matches both a session and an agent handle, prefer the session interpretation when the user's phrasing implies a group/context ("on X", "in X", "the X team"), and the agent interpretation when it implies a person ("ask X", "tell X")
4. If the target session differs from your current session (`$AM_ROOT` basename), use `--session <name>`
5. Never guess — if the name doesn't appear in `amq who --json` output, tell the user (it may need `coop exec --session <name>` to initialize)
6. For cross-project routing (different repo), use `--project` instead — see Cross-Project Routing section

## Messaging

```bash
amq send --to codex --body "Message"              # Send (uses AM_ROOT/AM_ME from env)
amq drain --include-body                          # Receive (one-shot, silent when empty)
amq reply --id <msg_id> --body "Response"          # Reply in thread
amq watch --timeout 60s                           # Block until message arrives
amq list --new                                    # Peek without side effects
```

### Send with metadata
```bash
amq send --to codex --subject "Review" --kind review_request --body @file.md
amq send --to codex --priority urgent --kind question --body "Blocked on API"
amq send --to codex --labels "bug,parser" --context '{"paths": ["src/"]}' --body "Found issue"
echo "evidence: tests green" | amq send --to codex --subject "done" --body -   # - reads stdin
```

**Body is fail-closed.** `--body -` (or `--body @-`, or omitting `--body`) reads stdin; a literal string or `@file` is used as-is. A send whose resolved body is empty/whitespace is **rejected** with a usage error instead of delivering a blank message — so `--body -` with nothing piped fails loudly rather than shipping an empty body. Pass `--allow-empty` only when you truly want a blank body (subject carries everything).

**Send file paths, not file contents.** When attaching source code, configs, or large text for review, send the file path in the message body, not the contents inline. The receiver can open the file with their local tools. If the receiver cannot access that worktree, send a short diff instead of the full source.

### Filter
```bash
amq list --new --priority urgent
amq list --new --from codex --kind review_request
amq list --new --label bug
```

## Operator Gates

Almost all coordination is agent-to-agent. Occasionally the **next required actor is a human**: an approval, a manual test, a deploy only a person can run, or sign-off that a goal is complete. AMQ has no separate "gate" feature. You represent this **structurally**: address a message to the human's mailbox instead of describing the wait in prose to another agent.

The single invariant AMQ relies on here is **recipient-as-next-actor**: a message addressed to the human handle means a human is who must act next. Everything else below (the `gate/<topic>` thread name and the `APPROVAL:` / `DONE:` subject prefixes) is a **naming convention** that downstream tools like amq-noc watch for. AMQ routing and message classification do **not** special-case thread names or subject text; those are plain strings, useful only because humans and tooling agree to read them. They are conventions, not core AMQ semantics.

### The human handle is `user`

By convention the human/operator mailbox is `user`. AMQ reserves this handle for validation in configured projects, so `--to user` is accepted wherever the project has a configured agent list. New co-op projects include `user` in the default agent set. For explicit `amq init --agents ...` projects or older roots, initialize the mailbox layout before relying on human drain/receipt/DLQ ergonomics:

```bash
# Seed the human mailbox alongside the agents (one-time, per project)
amq init --root .agent-mail --agents claude,codex,user
# or, for a coop project:
amq coop init --agents claude,codex,user
```

Throughout this section, `user` means "the conventional human handle." In configured projects it is warning-free for strict handle validation; in older or explicitly seeded roots, make sure the `agents/user/` mailbox exists before expecting a human to drain and reply from it.

### Raising a gate

Use a stable `gate/<topic>` thread so a gate and its resolution stay together:

```bash
# Approval / choice / manual test a human must perform
amq send --to user --thread gate/<topic> --kind question \
  --subject "APPROVAL: <decision>" \
  --body "<what you need a human to approve or run, and why>"

# Human closeout of a completed goal (sign-off that the goal is done)
amq send --to user --thread gate/<topic> --kind decision \
  --subject "DONE: <goal>" \
  --body "<what was completed; what the human should confirm or close>"
```

The human answers on the **same** thread from their own terminal or client, e.g. `amq send --me user --to <agent> --thread gate/<topic> --kind answer --subject "APPROVED: <decision>" --body "<approval / answer text>"` (use `DENIED:` or `ANSWER:` for a rejection or a plain answer). Reusing the `gate/<topic>` thread is what lets a watcher pair the answer with the open gate and clear it.

### When NOT to raise a gate

Keep ordinary coordination agent-to-agent. Do **not** send to `user` for:

- FYIs and status updates -> `status` on a normal thread
- Acknowledgements
- Routine code review between agents -> `review_request` / `review_response`
- Agent-owned blockers (waiting on another agent, a build, or a flaky test)

If the escalation owner is a lead/CTO agent, **they** decide whether to escalate, and that decision is agent-to-agent. But once a human action is actually required, it still becomes a `to:user` gate so tooling can observe it.

### Anti-pattern

Prose like `operator-held`, `pending operator`, or `manual approval` **inside an agent-to-agent message is not a gate**. It is body text a human or tool has to guess at. If a human must act, address the human.

### What a gate is, and is not

- **It is an observability / handoff signal, not authorization or security.** AMQ sender identity is local convention, not authenticated approval. A `to:user` gate records that a human is the next actor; it does **not** grant permission or prove a human approved anything. Do not treat it as an access-control boundary.
- **Cross-session / cross-project gates must be intentional.** Default examples target the human mailbox in the **current** session/project. Routing a gate to another session's or project's `user` is a deliberate act (`--session` / `--project`), never the default. Gate-clearing is a consumer/orchestrator convention unless AMQ later adds explicit gate state.

## Priority Handling

| Priority | Action |
|----------|--------|
| `urgent` | Interrupt current work, respond now |
| `normal` | Add to TODOs, respond after current task |
| `low` | Batch for session end |

## Message Kinds

| Kind | Reply Kind | Default Priority |
|------|------------|------------------|
| `review_request` | `review_response` | normal |
| `question` | `answer` | normal |
| `decision` | — | normal |
| `todo` | — | normal |
| `status` | — | low |
| `brainstorm` | — | low |

## References

For detailed protocols, read the reference file FIRST, then follow its instructions:

- [references/coop-mode.md](references/coop-mode.md) — Co-op protocol: roles, phased flow, collaboration modes
- [references/swarm-mode.md](references/swarm-mode.md) — Swarm mode: agent teams, bridge, task workflow
- [references/integrations.md](references/integrations.md) — Symphony + Kanban integration commands, global root fallback, ops checks
- [references/message-format.md](references/message-format.md) — Message format: frontmatter schema, field reference
- [references/cross-project.md](references/cross-project.md) — Cross-project routing: peer config, addressing, decision threads
- [references/review-loop.md](references/review-loop.md) — Token-efficient review cycles: delegate multi-round reviews to background agents
