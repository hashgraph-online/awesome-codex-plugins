---
name: costguard
description: Find and quantify CI/cron and cloud-spend waste. Audit repos, run read-only provider billing checks, preview or apply CI auto-fixes, and render a monthly cost digest.
license: MIT
---

Drive **Costguard** — a read-only cost auditor for CI minutes, cron schedules,
and cloud provider billing (GitHub Actions, Vercel, Supabase, Railway, Netlify, Neon, Cloudflare, and more).
It finds waste, estimates the monthly dollar cost, and can surgically auto-fix
CI workflow files. It never writes to provider accounts, never pushes git, and
never prints tokens.

Map the user's request to one Costguard CLI call and run it from the repo root.

## Command launcher

Costguard reads a `workspaces.json` registry from the **current working
directory**, so run it from a project that has one (or run `registry init`
first). Pick the launcher that matches your context; below, `costguard
<subcommand>` means whichever you use.

### If installed via plugin

When this skill is loaded from the Costguard plugin, run the bundled build — it
ships a prebuilt `dist/cli/index.js`, so no build step is needed. Locate the
plugin root (the dir containing `dist/cli/index.js`):

- **Claude Code** — it is `${CLAUDE_PLUGIN_ROOT}`:

  ```bash
  node "${CLAUDE_PLUGIN_ROOT}/dist/cli/index.js" <subcommand> ...
  ```

- **Codex** — walk up from this `SKILL.md` to the dir holding
  `.codex-plugin/plugin.json`:

  ```bash
  node "<plugin-root>/dist/cli/index.js" <subcommand> ...
  ```

### If using npx (no plugin)

No checkout and no build — run the published CLI directly:

```bash
npx -y -p @costguard/costguard-mcp costguard <subcommand> ...
```

Or, if `costguard` is on `PATH` (`npm i -g @costguard/costguard-mcp`), use it
directly: `costguard <subcommand> ...`. Heads-up: `npx -y @costguard/costguard-mcp`
(no `-p`, no subcommand) starts the MCP **server**, whereas `npx -y -p
@costguard/costguard-mcp costguard <subcommand>` runs the **CLI**.

## 1. Audit for waste (the main action)

```bash
costguard audit <workspace...>            # named workspaces
costguard audit --all                     # every registered workspace
costguard audit <ws> --providers all      # + read-only cloud billing checks
costguard audit <ws> --ci-only            # static CI checks only
costguard audit <ws> --crons-only         # cron checks only
costguard audit <ws> --site               # + read-only live-site checks (site URL from registry)
costguard audit <ws> --substitutions      # + cross-tool cheaper-alternative suggestions
costguard audit <ws> --json               # JSON instead of Markdown
```

Prints a report: each finding has a severity, an estimated monthly USD cost, a
detail, and a fix suggestion. Report stdout verbatim.

## 2. Scan / registry / report

```bash
costguard scan                # discover CI + cron files under the registry root
costguard registry list       # show registered workspaces
costguard registry init       # create a workspaces.json in the cwd
costguard report              # re-render the last saved audit run
```

## 3. Auto-fix CI files (dry-run first)

```bash
costguard fix <ws>            # dry-run: print a unified-diff preview, write nothing
costguard fix <ws> --apply    # write the surgical edits to disk (idempotent)
costguard fix <ws> --pr       # also emit local PR artifacts (no push)
```

Default is dry-run. Only deterministic ADD-rule fixers run (timeout,
concurrency, paths-ignore). Costguard never pushes; `--open-pr` is gated and
refuses without an explicit token.

## 4. Monthly cost digest

```bash
costguard digest             # render the digest from the last run (dry-run)
costguard digest --post      # delivery adapter (inert unless configured)
```

## 5. Auto-discover providers

Detect which providers a repo uses — from config files, `package.json` deps, and
env-var **names** (never values, never secrets). Covers all 13 wired providers
plus inngest.

```bash
costguard discover [dir]     # list detected providers + evidence (default dir: .)
costguard discover . --json  # JSON: { dir, providers, detections }
costguard discover . --write # union-merge detected providers into ./workspaces.json (non-destructive)
```

## 6. Live-site cost checks

Read-only, GET-only checks on a live URL (no browser, no form submit, no auth
replay). Flags transfer weight, oversized images, missing compression, weak cache
headers, and render-blocking scripts. The `$/mo` headline is the single
`site/transfer-weight` line — sourced when the host bills transfer (Vercel/Netlify),
or an explicit `$0` performance note (Cloudflare Pages static / unknown host).
Per-asset findings (`oversized-image`, `missing-compression`) put their dollar share
in `detail` and carry `estMonthlyUsd: 0` (no double-count); a `$0` performance-only
page never raises a `high` finding, so it never fails CI on cost alone.

```bash
costguard site <url>         # Markdown report
costguard site <url> --json  # JSON findings
```

`audit --site` runs the same checks for any workspace whose `workspaces.json`
entry has a `site` URL. `audit --substitutions` adds cross-tool
`<provider>/cheaper-alternative` suggestions (e.g. a static Vercel/Netlify Pro
site → Cloudflare Pages), each with a sourced saving, migration effort, and
lock-in caveat.

## Provider billing checks

`--providers <ids|all>` adds read-only billing checks for the providers listed
on each workspace in `workspaces.json`. Tokens are read from the environment /
`.env` only. A provider whose token env var is absent is **skipped**, not
failed. Supported: `github`, `supabase`, `railway`, `netlify`, `neon`, `vercel`,
`sentry`, `upstash`, `atlas`, `cloudflare`, `fly`, `render`, `datadog` (+ inngest
detection).

## 7. MCP tools (for AI coding agents)

Costguard also ships a bundled **MCP server** that exposes the same engine over a
host-agnostic tool surface (Claude Code, Codex, any MCP host). It wraps the same
read-only engine functions — no new behavior, same posture. In Claude Code it is
declared by `.claude-plugin/.mcp.json` and launched from the bundled build:

```json
{ "mcpServers": { "costguard": { "command": "node",
  "args": ["${CLAUDE_PLUGIN_ROOT}/dist/mcp/server.js"] } } }
```

In the plugin, the server runs from the committed `dist/mcp/server.js` — no
install step.

### Codex MCP config

For **Codex**, add one of these to `~/.codex/config.toml`. Use npx for a
no-checkout install (pulls the published package), or the bundled build if you
run Codex from the plugin:

```toml
# npx — no checkout
[mcp_servers.costguard]
command = "npx"
args = ["-y", "@costguard/costguard-mcp"]
```

```toml
# bundled plugin build
[mcp_servers.costguard]
command = "node"
args = ["<plugin-root>/dist/mcp/server.js"]
```

Tools:

| Tool | Posture |
|---|---|
| `audit_workspace` | read-only; returns a Findings envelope (`includeSite` adds site checks) |
| `discover_providers` | read-only; env-var NAMES only, never values |
| `audit_site` | read-only, GET-only |
| `plan_fix` | dry-run; returns unified diffs only, writes nothing |
| `apply_fix` | writes local CI files; REFUSES unless `confirmApply:true`; never pushes git |
| `plan_live_checks` | plans a live billing read (see below); emits a snippet only with consent |
| `ingest_live_reading` | parses a returned billing figure into a Finding |

## 8. Live billing checks (`--live`) — opt-in, consent-gated

`--live` **extends** the read-only posture above: it adds **browser-driven reads
over your already-logged-in session**, performed by the **playwriter** MCP server
under the agent's orchestration. This is a genuine posture change and is treated
as one — **off by default, opt-in, and consent-gated.** costguard's own tools
still never drive a browser and never see credentials: `plan_live_checks` only
emits a **read-only** snippet (navigation + reading rendered billing figures — no
clicks, typing, form submits, credential replay, cookies, localStorage,
sessionStorage, or screenshots), and `ingest_live_reading` only parses the
returned figure. The browser action is performed by playwriter, authorized by you.

**API-first / browser-fallback:** `plan_live_checks` is API-first when a provider
module exists and its API token resolves from the environment (a deterministic
env-NAME check, no network probe) — in that case prefer `audit_workspace`. Only
when there is no usable API token does it fall back to a browser playbook.

**Three consent gates (all required):** (1) the host's MCP tool-call consent;
(2) costguard's own per-run confirmation — `plan_live_checks` returns a
`consentNotice` the agent MUST surface, and emits the actionable snippet only when
called with `confirmLive:true`; (3) playwriter's own consent before it executes.

**Graceful degrade:** if playwriter is not connected, the agent cannot run the
snippet; `ingest_live_reading` returns a `kind:"diagnostic"` Finding (excluded
from cost totals) and the audit never blocks.

## Notes

- All provider calls are read-only (GET / read-only GraphQL). No POST/PUT/PATCH/
  DELETE to provider accounts.
- Estimated dollar costs are best-effort and depend on plan/tier; treat them as
  directional, not invoices.
- Requires `node` on `PATH`. The bare `costguard` command is optional when the
  skill runs from the plugin — use the plugin-root `node` launcher above.
