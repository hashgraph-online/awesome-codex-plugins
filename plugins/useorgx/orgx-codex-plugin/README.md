# OrgX Codex Plugin

Codex plugin package for OrgX:

- OrgX MCP server wiring via `https://mcp.useorgx.com/mcp?profile=commander`
- Operator chronicle reporting for yesterday/week/30-day decisions, PRs,
  artifacts, goals, gaps, and priorities
- Initiative-aware Codex skills for OrgX execution
- Runtime reporting guidance and passive hook templates for progress, artifacts,
  blockers, and completion
- Install-surface metadata for Codex plugin directories and local marketplaces

## Why this plugin exists

This repo packages the OrgX setup that Codex needs into the structure described
in the official Codex plugins docs:

- `.codex-plugin/plugin.json`
- `.mcp.json`
- `skills/**/SKILL.md`
- `assets/`

It is the Codex counterpart to the existing OrgX Claude Code and OpenClaw
plugin repos.

## Structure

```text
.codex-plugin/plugin.json   # Codex plugin manifest
.mcp.json                   # OrgX MCP configuration
skills/orgx-initiative-ops/SKILL.md
skills/orgx-runtime-reporting/SKILL.md
hooks/codex/hooks.json
hooks/scripts/orgx-session-hook.mjs
hooks/scripts/orgx-work-graph-reconcile.mjs
assets/icon.png
assets/logo.png
scripts/verify-plugin.mjs
```

## Included skills

### `orgx-initiative-ops`

Use OrgX MCP as the source of truth when a task is scoped to an OrgX initiative,
workstream, milestone, task, blocker, or decision.

### `orgx-runtime-reporting`

Keep OrgX updated during live Codex execution with progress, artifacts,
blockers, and completion events.

For reporting or daily-brief style questions, start with
`get_operator_chronicle` when the live OrgX MCP tool map exposes it. Its
`reportingNarrative.briefMarkdown` is the canonical concise answer for
decisions made yesterday, the past week, the past 30 days, artifacts, PR
receipts, velocity, top priorities, goals, and gaps.

If an AI client has not refreshed its callable MCP schema after OrgX publishes
the direct tool, use the existing `orgx_recommend` / `_orgx_recommend` fallback
with `mode: "morning_brief"` and present the same
`reportingNarrative.briefMarkdown`. Direct `get_operator_chronicle` calls remain
preferred when callable; the fallback prevents a stale plugin session from
blocking the report.

## Runtime hooks

The plugin now includes Codex hook templates, but the recommended install path is
through `orgx-wizard hooks install`. The wizard can merge global hook config,
preserve existing `notify` integrations such as Computer Use, and write a local
outbox under `~/.config/useorgx/wizard/hooks/events.jsonl`.

Client hook coverage is tracked in
[docs/client-hook-coverage.md](./docs/client-hook-coverage.md). Current verdict:
the Codex package covers Codex skills, MCP setup, stale-client chronicle
fallback, and passive hook templates, but it is not sufficient proof that every
AI client exposes the same hooks or direct `get_operator_chronicle` tool. Use
that matrix before claiming ChatGPT, Claude Code, or Cursor parity.

Hook events are a passive backstop. They record compact session metadata and
safe summaries so Work Graph reconciliation can answer:

- What changed yesterday, this week, and in the past 30 days?
- Which decisions, PRs, artifacts, goals, and priorities should be surfaced?
- Did the session call OrgX MCP?
- Did meaningful work happen without OrgX writeback?
- Are there decisions, blockers, artifacts, people, product surfaces, or goals
  that should become an OrgX initiative kickoff?

This package includes `orgx-codex-reconcile-hooks`, a local reconciler that
reads the hook outbox and emits a summary-only Work Graph report with a stable
`work_graph_fingerprint` and `signup_hydration.hydration_key`. That fingerprint
is the bridge between a pre-signup audit/share surface and the user's future
OrgX workspace: after signup, OrgX can claim the fingerprint, dedupe replays,
and attach the redacted Work Graph to a kickoff initiative.

The Codex `Stop` hook also invokes `orgx-reconcile-hook.mjs`, which writes the
latest local Work Graph report to
`~/.config/useorgx/wizard/hooks/reports/latest-work-graph-report.json`. This is
non-blocking and exits successfully even when the outbox is missing, credentials
are absent, or posting fails. To make Stop-hook reconciliation publish to OrgX,
set `ORGX_HOOK_RECONCILE_POST=true` or
`ORGX_WIZARD_HOOK_RECONCILE_POST=true` and provide `ORGX_API_KEY`.

Raw transcripts are not sent by the hook template. The reconciler should keep
transcripts local and write only redacted summaries, hashes, evidence refs,
Work Graph fingerprints, and approved OrgX activity.

## Subscription runner autonomy

The Codex peer is interactive-only by default. To authorize OrgX to select the
user-controlled runner for unattended work, set the following in the runner's
service environment and restart it:

```bash
ORGX_AUTONOMOUS_DISPATCH_ENABLED=true
ORGX_AUTONOMOUS_REPO_PATH=/absolute/path/to/git-worktree
ORGX_RUNNER_INSTANCE_ID=<installer-persisted-service-id>
ORGX_ACTIVATION_ATTEMPT_ID=<installer-activation-attempt-id>
ORGX_RUNNER_ROLE=candidate
```

Only the exact string `true` opts in. The repo path must be a canonical,
existing git worktree root owned by the runner configuration; tasks cannot
choose or override it. Unset, misspelled, invalid, or conflicting values fail
closed. Service installers should persist the path in a mode-0600 state file
and use it as the service working directory. Heartbeats publish requested,
repo-ready, MCP-ready, and enabled states separately; enabled is true only when
all gates pass. Before any autonomous model turn, the peer also proves the
exact signed OrgX MCP tool names and schemas through Codex app-server. The
installer must configure and authenticate the hosted `orgx` server with the
official `codex mcp add` / `codex mcp login` flow; the Gateway key is not an MCP
OAuth token. Opted-in peers accept normal user-initiated work only when the
Gateway marks it `dispatch_class: interactive`; unattended work must be marked
`autonomous` and carry the complete signed context. The context contains the
actual resolved skill instructions, and the peer verifies their digests against
the runtime profile and execution envelope before adding them to the Codex
prompt. This permission applies only to the Codex runner and does not authorize
unattended use of an Anthropic subscription.

Autonomous services must export a stable `ORGX_RUNNER_INSTANCE_ID` generated by
the installer. A staged candidate and the current canonical service must use
different values. The peer binds this identity into both the Gateway heartbeat
body and WebSocket query, allowing activation to prove which durable service is
online before promotion. Interactive/manual CLI launches may omit the variable;
the CLI persists a mode-0600 identity scoped to the workspace and installation
under `~/.orgx/codex-peer/runner-instances/`.

During managed promotion, the installer also sets one activation attempt ID and
a runner role of exactly `candidate` or `canonical`. These two values are
validated as a pair and included in the presence heartbeat, but not the stream
query; the authenticated server-side binding remains authoritative. A partial
pair or any other role fails before the peer starts network activity.

A completed Codex turn is not sufficient to claim `shipped`. For autonomous
runs, the peer compiles the required evidence types, verifier independence,
minimum outcome confidence, judged score, verdict confidence, and critical
observation ceiling from the content-verified mission/work-node/quality-bar
bundle. Empty or prose-only runs become `blocked`; concrete work without a
qualified independent verifier becomes `awaiting_review`; and read-only work
cannot satisfy an artifact-producing mission. Only a trusted OrgX verifier
record meeting every signed threshold can preserve `shipped`. Verifier records
are rejected by default even when their signature field is well-shaped; a
runner-owned verifier callback must authenticate them. The packaged production
peer does not configure a permissive callback, so unverified work remains
`awaiting_review`.

Terminal completions and failures are written to a mode-0700 disk outbox before
the peer yields them to the Gateway SDK. The peer posts every terminal message
independently to the idempotent HTTP receipt endpoint and removes its file only
after an HTTP 2xx application acknowledgement. Rejected deliveries survive
peer restarts and replay on startup, reconnect/heartbeat, and shutdown. Set
`ORGX_RECEIPT_OUTBOX_PATH` to override the workspace-scoped default under
`~/.orgx/codex-peer/receipt-outbox/`.

Installers must run the one-shot gate after Codex login, OrgX MCP OAuth, and
repo selection, but before persisting autonomous opt-in:

```bash
ORGX_AUTONOMOUS_REPO_PATH=/absolute/path/to/git-worktree \
  orgx-codex-peer check-autonomous-readiness
```

The readiness gate reads Codex app-server `mcpServerStatus/list`, whose current
v2 success value is `authStatus: "oAuth"`. Installers that separately inspect
`codex mcp list --json` must handle that CLI's snake-case surface
(`auth_status: "o_auth"`) instead of reusing the app-server literal.

The command needs no Gateway key. It exits zero only when the checkout is
valid, Codex is ChatGPT-authenticated, current app-server RPC works, and a
read-only, shell-disabled app-server thread proves the authenticated OrgX server
exposes exactly the bounded `orgx_bootstrap` MCP tool. This is an MCP inventory
proof, not a claim that Codex has no other non-shell native tools. Real runs
still compare every MCP tool schema to the signed per-run manifest.

Dry-run reconciliation does not require OrgX credentials:

```bash
orgx-codex-reconcile-hooks \
  --outbox ~/.config/useorgx/wizard/hooks/events.jsonl \
  --output /tmp/orgx-work-graph-report.json
```

To publish the report to OrgX, provide an API key and opt in explicitly:

```bash
ORGX_API_KEY=oxk_... orgx-codex-reconcile-hooks --post
```

For automatic publish on Codex session stop:

```bash
ORGX_HOOK_RECONCILE_POST=true ORGX_API_KEY=oxk_... codex
```

## Local verification

```bash
npm run check
```

To preview the runtime wiring without editing Codex config:

```bash
orgx-wizard hooks doctor
```

To install the passive Codex/Claude Code hook backstop:

```bash
orgx-wizard hooks install --targets all
```

## Install locally in Codex

### Repo-local marketplace

This repo now includes a marketplace file at
`.agents/plugins/marketplace.json` that points directly at the plugin repo
root. To test it in Codex:

1. Open `/Users/hopeatina/Code/orgx-codex-plugin` in Codex.
2. Restart Codex.
3. Open `/plugins` and select the repo marketplace `orgx-local`.

This is the fastest way to verify the plugin during development because it
avoids copying the plugin into a separate plugins directory.

The official docs recommend using the built-in `@plugin-creator` skill to
scaffold local plugins and marketplace entries. That skill was not available in
the environment used to create this repo, so this plugin was scaffolded
manually against the current published Codex plugin spec.

### Personal marketplace

1. Copy the plugin to your personal Codex plugins directory:

```bash
mkdir -p ~/.codex/plugins
cp -R /absolute/path/to/orgx-codex-plugin ~/.codex/plugins/orgx-codex-plugin
```

2. Add or update `~/.agents/plugins/marketplace.json`:

```json
{
  "name": "useorgx-local",
  "interface": {
    "displayName": "OrgX Local"
  },
  "plugins": [
    {
      "name": "orgx-codex-plugin",
      "source": {
        "source": "local",
        "path": "./.codex/plugins/orgx-codex-plugin"
      },
      "policy": {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL"
      },
      "category": "Productivity"
    }
  ]
}
```

3. Restart Codex and open `/plugins`.

Because `~/.agents/plugins/marketplace.json` is resolved relative to your home
directory, the plugin entry must point at `./.codex/plugins/...` if the plugin
was copied under `~/.codex/plugins/`.

## MCP server behavior

The bundled `.mcp.json` config uses the hosted OrgX streamable HTTP endpoint:

```json
{
  "mcpServers": {
    "orgx": {
      "type": "http",
      "url": "https://mcp.useorgx.com/mcp?profile=commander"
    }
  }
}
```

This follows current OrgX MCP docs and lets OAuth happen in-browser on first
use. After bootstrap, the preferred reporting first call is
`get_operator_chronicle` with `period: "30d"` when the client exposes it.
When the hosted MCP bootstrap advertises `get_operator_chronicle` but a client
session still exposes only older OrgX tools, call `orgx_recommend` with
`mode: "morning_brief"` as the compatibility path. Passive runtime hooks are a
reconciliation backstop for session evidence; they are not a substitute for MCP
read/write calls during the live operator report.

## Sources used

- Official Codex plugin docs:
  `https://developers.openai.com/codex/plugins`
- OrgX MCP docs:
  `https://docs.useorgx.com/docs/api/overview`
- Existing OrgX references:
  - `orgx-claude-code-plugin`
  - `orgx-openclaw-plugin`
