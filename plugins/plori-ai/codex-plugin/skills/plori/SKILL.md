---
name: plori
description: Create and drive plori agents (each an AI agent in its own cloud environment) from any MCP client, the plori CLI, or over REST. Covers authentication (OAuth 2.1 or API key), creating agents, invoking them and reading replies, answering human-in-the-loop requests, and scheduling deferred runs.
---

# Using plori from an agent

plori (https://plori.ai) gives you AI agents. Each agent runs in its own cloud environment with a
persistent disk, a shell, developer tools, and memory. You can create agents, send them
work, and read their replies programmatically.

## Connect

MCP (recommended for a hosted client): Streamable HTTP at `https://api.plori.ai/mcp`.

- OAuth 2.1: compliant MCP clients connect with no hand-copied key. An unauthenticated
  request returns 401 with the discovery chain (RFC 9728 Protected Resource Metadata at
  https://api.plori.ai/.well-known/oauth-protected-resource, then dynamic client
  registration and authorization code + PKCE). The account owner signs in once with an
  email one-time code.
- API key: the account owner provisions a key at https://plori.ai and you send
  `Authorization: Bearer plori_sk_...`.

CLI (recommended from a terminal): install with
`curl -fsSL https://plori.ai/install.sh | sh` (one static binary, no sudo and no Node; on
Windows `irm https://plori.ai/install.ps1 | iex`), or `npm i -g @plori/cli`, or run it
without installing via `npx -y @plori/cli`. That gives you the `plori` command for the
same operations from your shell. The shell installer puts the binary in `~/.local/bin`
and edits no shell rc file, so run `export PATH="$HOME/.local/bin:$PATH"` after it
before you call `plori` (the Windows script sets the user PATH itself).
`plori login` opens the browser for the same email-OTP
OAuth flow; CI and other headless callers use `plori login --key plori_sk_...` or set
`PLORI_API_KEY`. Output is human-readable on a terminal and a single JSON document when
piped or with `--json`, so it composes in scripts. Commands are listed under "CLI
commands" below.

REST: the same operations at `https://api.plori.ai/v1` with the same bearer token.
Full authentication instructions: https://plori.ai/auth.md

## Tools

Account and agents: `list_agents`, `get_agent`, `create_agent`
(name; the Plori Router chooses the model per task), `delete_agent`, `get_credits`,
`get_usage`, `get_disk`.

Runs: `invoke_agent` sends a message and by default blocks until the turn finishes,
returning the assistant's reply. Pass `wait=false` to get a `run_id` immediately and
poll `get_run_result`; pass `max_turn_tokens` to cap the turn. `cancel_run` stops an
in-flight run asynchronously. `list_runs` lists recent runs.

Human in the loop: a run can pause on an approval or input request (status
`awaiting_input`). Read the queue with `list_pending_inputs` and reply with
`answer_pending_input` (run_id + tool_call_id, then approved=true/false for approvals
or value for input requests). A queued row carrying a `consent_tool` is an outward-facing
write held for consent: approving it with `always_allow=true` also stops the agent asking
for that tool again. That is a standing grant, so set it only when the human explicitly
said to stop being asked, never on your own judgment.

Deferred work: `schedule_run` (agent_id, prompt, and delay_seconds or an RFC3339
fire_at) invokes the agent later as an ordinary run.

Connections: `list_connections` shows the account's third-party OAuth provider status,
authorization and expiry times, and configured scopes. `status` is the re-authentication
predicate; an authorized grant with an old expiry refreshes lazily on use. It never returns
tokens or client secrets.

Workflows: `list_workflows` (optional agent_id UUID, or "none" for unassigned),
`get_workflow` (workflow_id; returns metadata plus the pinned step projection),
`get_workflow_version` (workflow_id + version; returns the full definition with parameter
values), `edit_workflow` (workflow_id + base_version + constrained ops; creates a draft
version under CAS and does not activate it),
`create_workflow` (name, optional description/trigger_kind/cron_expr),
`run_workflow` (runs a workflow now: a real execution billed like any run,
returning the execution, terminal or still `running`), `list_workflow_executions`
(workflow_id; recent execution history), and `get_workflow_execution` to poll one and read
its full per-step input/output payloads.
A workflow's steps are built by an agent; these tools manage and run the result.

## CLI commands

The CLI mirrors the tools above; an agent is addressable by name or id, and every command
accepts `--json`.

- `plori attach <name|session-id>`: open a live session in the terminal (history, a
  prompt, streaming output, and approvals answered in place). It is interactive and
  expects a human at the keyboard: as a calling agent, prefer the one-shot commands
  below, and use `--read-only` if you only need to tail a session. It writes plain
  text, never JSON, and redirecting stdin or stdout already selects read-only.
- `plori create <name>`: get or create an agent by name (reusing a name returns the
  existing agent). `plori agents`, `plori agent <name>`, `plori set-model <name> <model>`,
  `plori delete <name> --yes`.
- `plori run <name> "message"`: send a message and, by default, wait for the reply and
  print it. Add `--follow` to stream the turn live, or `--no-wait` to get a run id back
  immediately. Pass `-` as the message to read it from stdin.
- `plori result <name> <run-id>` (add `--wait` to block) and `plori runs <name>` read
  run status and history.
- `plori inputs <name>` lists runs paused on a human request; `plori answer <run-id>
  <tool-call-id> --approve|--deny|--value <v>` replies. Add `--always-allow` to an
  `--approve` (only on the human's explicit instruction) to also grant the standing
  write consent.
- `plori schedule <name> "prompt" --in <seconds>` (or `--at <rfc3339>`) defers a run;
  `plori schedules <name>` and `plori unschedule <name> <id>` manage them.
- `plori workflows list [--agent <name|id|none>]`,
  `plori workflows create <name> [--trigger cron --cron <expr>]`,
  `plori workflows run <name|id>` (run it now), `plori workflows execution <name|id> <exec-id>`.
- `plori credits`, `plori usage`, `plori disk` read account state.

## Costs and limits

Running an agent spends credits; check `get_credits` before invoking. Agent count and
model tier follow the account's plan. Every call is scoped to the account that owns the
credential; there is no cross-account access.

## More

- Integration front door: https://plori.ai/agents.md
- MCP connect guide: https://plori.ai/mcp
- CLI on npm: https://www.npmjs.com/package/@plori/cli
- Authentication detail: https://plori.ai/auth.md
- Site map for agents: https://plori.ai/llms.txt
