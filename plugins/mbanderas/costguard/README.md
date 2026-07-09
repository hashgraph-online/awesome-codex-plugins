# CostGuard

<p align="center">
  <img src="assets/costguard-banner.png" alt="CostGuard — a robot sea captain steering a boat named costguard through waters of dollars, CPUs, clocks, and clouds" width="720">
</p>

<p align="center">
  <a href="https://www.npmjs.com/package/@costguard/costguard-mcp"><img src="https://img.shields.io/npm/v/@costguard/costguard-mcp?label=npm&color=2E9E6B" alt="npm version"></a>
  <a href="https://github.com/mbanderas/costguard/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/mbanderas/costguard/ci.yml?branch=master&label=CI" alt="CI status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2E9E6B" alt="MIT license"></a>
  <a href="https://nodejs.org"><img src="https://img.shields.io/node/v/@costguard/costguard-mcp" alt="node version"></a>
</p>

CostGuard audits your repos and cloud providers for CI and infrastructure cost
leaks. It is built for developers who run several projects across GitHub Actions,
Vercel, Supabase, Railway, Netlify, Neon, Cloudflare, and more, and want a single
command that surfaces what is being wasted and exactly how to fix it. On repositories that have never been
optimized, the static audit alone typically reduces CI spend by 60–80%.

<p align="center">
  <img src="assets/chart-ci-savings.svg" alt="Observed CI cost reduction: 60-80% typical on repositories never optimized, up to 80% best observed" width="720">
</p>

---

## Install

CostGuard installs three ways. The plugin paths are zero-build and zero-`npm`
(they ship a prebuilt, self-contained bundle); the npm package gives you the CLI
and the MCP server anywhere.

### Claude Code

```sh
/plugin marketplace add mbanderas/costguard
/plugin install costguard@costguard
```

Adds `/costguard-audit`, `/costguard-fix`, `/costguard-live`, and the full
`costguard` skill (scan, providers, registry, report, digest). No build step, no
`npm install`.

### Codex

```sh
codex plugin marketplace add mbanderas/costguard
codex plugin add costguard@costguard
```

Adds the bundled `costguard` skill to Codex CLI and Desktop.

### npm / any MCP host

Run the MCP server directly — no install:

```sh
npx -y @costguard/costguard-mcp
```

Install the MCP server and the `costguard` CLI globally (both bins):

```sh
npm i -g @costguard/costguard-mcp
```

Run the CLI ad-hoc without installing:

```sh
npx -y -p @costguard/costguard-mcp costguard
```

`npx -y @costguard/costguard-mcp` launches the MCP server directly because the
package name matches its bin entry point — drop it straight into any MCP host's
server config.

> **Other CLIs / Desktop apps** — one command drops a thin `/costguard` adapter
> into Cursor, Gemini CLI, Cline, Windsurf, or a Codex project:
>
> ```sh
> npx -y -p @costguard/costguard-mcp costguard install --target <host|auto>
> ```
>
> `--target auto` detects the host; the adapter is no-clobber and idempotent. Run
> `costguard install --help` for the full target list.

---

## What it finds

**Static half (zero credentials).** Reads `.github/workflows/*.yml` and
application code to detect redundant CI triggers (`push` + `pull_request` on the
same branch), missing `timeout-minutes`, missing concurrency cancellation,
`paths-ignore` gaps that run CI on doc-only commits, and over-scheduled crons. No
API call, no token needed — always safe to run.

**Billing half (read-only, opt-in).** When a provider token is present,
reconciles live billed resources against a declared allowlist and flags
**orphaned** resources (billed but not listed) and **over-provisioned** resources
(larger or more capable than declared), each with a best-effort estimated monthly
cost. Covers thirteen providers: **GitHub**, **Vercel**, **Supabase**,
**Railway**, **Netlify**, **Neon**, **Cloudflare**, **Fly**, **Render**,
**Sentry**, **Upstash**, **MongoDB Atlas**, and **Datadog**.

---

## Proof

Tested on production repositories. Patterns found and fixed across repositories
like `my-app`, `web-app`, and `api-service`:

- **Redundant CI triggers.** A workflow wired to both `push` and `pull_request`
  on the same branch runs CI twice per commit. Dropping the redundant trigger
  halves runner-minute consumption for every push.
- **Missing timeouts.** Jobs without `timeout-minutes` burn minutes up to
  GitHub's 6-hour cap on hung runs. Adding a sane timeout is a one-line fix with
  no functional impact.
- **Missing concurrency cancellation.** Without a `concurrency` block, rapid
  pushes queue up and run sequentially instead of cancelling superseded runs.
  Adding `cancel-in-progress: true` eliminates the queue.
- **`paths-ignore` gaps.** Workflows without `paths-ignore` for documentation
  paths run full CI on commit-message and README edits. Excluding `**.md` and
  `docs/**` removes a class of runs entirely.
- **Orphaned preview branches.** A Supabase preview branch left running after a
  feature ships keeps accruing compute cost each billing cycle.

On repositories that have accumulated these patterns over time, fixing all of
them has reduced observed CI spend by up to 80%. The typical range on
repositories never previously optimized is 60–80%. Results vary by workflow
structure and push cadence; these are observed, directional outcomes, not a
guarantee.

<p align="center">
  <img src="assets/chart-before-after-minutes.svg" alt="Redundant CI runs before vs after CostGuard across my-app, web-app, and api-service" width="720">
</p>

---

## Using CostGuard

Every host drives the same read-only engine — reach for it the native way. Each
block below is self-contained; use the one for your host.

### Claude Code

Three slash commands plus the full `costguard` skill (scan, providers, registry,
report, digest):

- `/costguard-audit` — audit a workspace for CI/cron and cloud-spend waste.
- `/costguard-fix` — preview or apply the safe in-repo CI fixes (dry-run first).
- `/costguard-live` — opt-in, consent-gated live billing read for a provider.

### Codex

Invoke the bundled `costguard` skill by name, then say what you want:

- "Use the costguard skill to audit my-app for CI waste."
- "With costguard, show a dry-run fix for web-app's workflows."
- "Run a costguard provider billing check across api-service."

### Cursor / Gemini CLI / Cline / Windsurf

Install the `/costguard` adapter once for your host:

```sh
costguard install --target cursor
costguard install --target gemini
costguard install --target cline
costguard install --target windsurf
```

Then drive it with any `costguard` arguments:

```text
/costguard audit my-app
/costguard fix my-app --apply
```

(If `costguard` is not yet on your PATH, prefix the install command with
`npx -y -p @costguard/costguard-mcp `.)

### Any MCP host

Copy-paste CostGuard's MCP server into your host's config — no checkout:

```json
{
  "mcpServers": {
    "costguard": {
      "command": "npx",
      "args": ["-y", "@costguard/costguard-mcp"],
      "env": {
        "GITHUB_TOKEN": "…",
        "SUPABASE_ACCESS_TOKEN": "…",
        "RAILWAY_TOKEN": "…",
        "NETLIFY_AUTH_TOKEN": "…",
        "NEON_API_KEY": "…"
      }
    }
  }
}
```

Every token is optional and read-only; a provider with no token is skipped. See
[Environment variables](#environment-variables) for the full list and aliases.

`npx -y @costguard/costguard-mcp` (no `-p`, no subcommand) starts the MCP
**server** for this config; `npx -y -p @costguard/costguard-mcp costguard
<subcommand>` runs the **CLI**.

---

## Environment variables

Provider tokens are read **only** from the process environment or a gitignored
`.env` in the CostGuard workspace. They are never printed, logged, or committed.
Each provider module runs only when one of its tokens is present; offline, the
modules are fully exercised by fixtures. All tokens are used **read-only**.

| Variable (any one of) | Provider | Used for |
|-----------------------|----------|----------|
| `GITHUB_TOKEN` / `GH_TOKEN` | github | Actions usage per repo (read-only billing PAT) |
| `SUPABASE_ACCESS_TOKEN` / `SUPABASE_TOKEN` | supabase | Projects, compute size, PITR, branches |
| `RAILWAY_TOKEN` / `RAILWAY_API_TOKEN` | railway | Services, deploys, usage (read-only GraphQL) |
| `NETLIFY_AUTH_TOKEN` / `NETLIFY_TOKEN` | netlify | Sites, build minutes, bandwidth |
| `NEON_API_KEY` / `NEON_API_TOKEN` | neon | Projects, branches, compute hours |
| `VERCEL_TOKEN` / `VERCEL_API_TOKEN` | vercel | Team deploying seats vs deploy activity |
| `SENTRY_AUTH_TOKEN` / `SENTRY_TOKEN` | sentry | Monthly error events vs plan quota |
| `UPSTASH_API_KEY` / `UPSTASH_TOKEN` | upstash | Redis DB commands + storage |
| `ATLAS_API_KEY` / `MONGODB_ATLAS_TOKEN` | atlas | Cluster tiers + data size |
| `CLOUDFLARE_API_TOKEN` / `CF_API_TOKEN` | cloudflare | R2 buckets, storage, class A/B ops |
| `FLY_API_TOKEN` / `FLY_ACCESS_TOKEN` | fly | Apps + dedicated IPv4 addresses |
| `RENDER_API_KEY` / `RENDER_TOKEN` | render | Service instance plans |
| `DD_API_KEY` / `DATADOG_API_KEY` | datadog | Enables the module (declaration-only; APM host counts read from config) |
| `COSTGUARD_DIGEST_WEBHOOK` | — | Optional `digest --post` destination (inert in this build) |

Use `providers --check` to confirm which tokens the environment exposes without
revealing any value.

---

## Provider modules

CostGuard ships **thirteen** read-only, opt-in provider modules, and the roster
is actively expanding. Each reads live billed resources, reconciles them against
the registry `active{}` allowlist, and emits `orphaned` and `over-provisioned`
findings with a best-effort `$/mo`.

| Module | Reads | Flags |
|--------|-------|-------|
| **github** | Actions usage per repo | top minute-burners; repos over budget |
| **supabase** | Projects, compute size, PITR/add-ons, branches | running preview branches; compute/PITR drift vs registry |
| **railway** | Services, deploys, usage (read-only GraphQL queries) | idle services; deploys never torn down |
| **netlify** | Sites, build minutes, bandwidth | build-minute spend; runaway bandwidth |
| **neon** | Projects, branches, compute hours | idle branches; orphaned (defunct but billed) projects |
| **vercel** | Team deploying seats vs deploy activity | idle paid deploying seats |
| **sentry** | Monthly error events | error-event overage vs plan quota |
| **upstash** | Redis DB commands + storage | pay-as-you-go cost above a fixed plan |
| **atlas** | Cluster tiers + data size | oversized cluster for its data |
| **cloudflare** | R2 buckets, storage, class A/B ops | operation-heavy R2 spend |
| **fly** | Apps + dedicated IPv4 addresses | dedicated IPv4 on non-critical apps |
| **render** | Service instance plans | oversized instance for its environment |
| **datadog** | APM host counts (declared in config) | excess provisioned APM hosts |

All live provider access is HTTP `GET`; the railway module uses GraphQL
**queries** only, guarded against mutations. The datadog module is
declaration-only — it reconciles operator-declared host counts offline and makes
no network call. No module ever issues a write or delete call. A module
activates only when its token (above) is present; otherwise it is skipped.

More providers are on the way — coverage is expanding as new billing surfaces are
researched and sourced.

---

## Security / read-only posture

CostGuard is built to be safe to run anywhere, including on a schedule:

- **Read-only provider access only.** No write or mutating API call is ever issued. Provider tokens are read-only and are never printed, logged, or committed.
- **Secrets stay out of the repo.** Tokens are read from the environment or a gitignored `.env*` only. `providers --check` reports presence by variable name, never by value.
- **The static half needs no credentials.** `audit` (without `--providers`) and `scan` read only local files and are always safe to run.
- **`fix` is in-repo and dry-run by default.** It edits only `.github/workflows/*` files in the target workspace, never provider or cloud state, and writes nothing until `--apply`.
- **Outward actions are inert and gated.** `fix --open-pr` and `digest --post` refuse to act without an explicit opt-in flag *and* the matching credential, and even then perform no git push or network post in this build.

---

## How workspaces.json works

`workspaces.json` is the registry of projects CostGuard tracks. `registry --init`
scans `workspacesRoot` (default: `~/Workspaces`) and writes a fresh file with
auto-detected `providers` arrays (GitHub, Netlify, Supabase, etc.) and blank
`active{}` blocks. A starter [`workspaces.example.json`](workspaces.example.json)
ships with this repo.

```json
{
  "root": "~/Workspaces",
  "workspaces": {
    "my-app": {
      "providers": ["github", "netlify"],
      "active": {}
    }
  }
}
```

The `active{}` block is the allowlist used by the provider checks: any live
resource not listed there is flagged as **orphaned**, and any resource larger or
more capable than declared is flagged as **over-provisioned**. Leave it empty if
you only run the static half; the provider modules then have nothing to reconcile
against.

---

## Configuration

Create `costguard.config.json` in the project root to override defaults:

```json
{
  "workspacesRoot": "~/Workspaces",
  "defaults": {
    "cronThresholdMinutes": 15,
    "ciMinuteRate": 0.008,
    "assumedPushesPerDay": 10,
    "assumedMinutesPerRun": 5
  },
  "perWorkspace": {
    "my-app": {
      "cronThresholdMinutes": 30
    }
  }
}
```

| Key | Default | Description |
|-----|---------|-------------|
| `cronThresholdMinutes` | `15` | Crons running more often than this threshold are flagged |
| `ciMinuteRate` | `0.008` | USD per runner-minute (GitHub-hosted Linux) |
| `assumedPushesPerDay` | `10` | Estimated daily push cadence for cost projection |
| `assumedMinutesPerRun` | `5` | Assumed wasted minutes per redundant CI run |

Per-workspace overrides in `perWorkspace` merge on top of `defaults`.

---

## Scheduler template

A monthly digest can be wired to GitHub Actions via the documented, **inert**
scheduler template `templates/costguard-digest.yml`.

- It lives under `templates/` — **not** `.github/workflows/` — so it never runs automatically and is not enabled by this project.
- **To activate:** a human copies it into `.github/workflows/` in the target repo and supplies the required secrets (e.g. `COSTGUARD_DIGEST_WEBHOOK`).
- **To roll back:** delete the copy from `.github/workflows/`.

Activating the template is a deliberate human action outside CostGuard's own runtime.

---

## CLI reference

These flags apply to the `costguard` CLI, available via `npm i -g @costguard/costguard-mcp` or `npx -y -p @costguard/costguard-mcp costguard <subcommand>`.

All commands operate on the `workspaces.json` registry in the project root.
Workspace selection is by directory name; `--all` selects every registered
workspace. Examples use the global `costguard` command; from a checkout you can
equivalently run `node dist/cli/index.js <command>`.

### audit

Run the static CI/cron audit, optionally adding read-only provider billing
checks, and print a report to stdout.

```sh
# Audit a single workspace (static checks only)
costguard audit my-app

# Audit everything at once
costguard audit --all

# CI-minutes check only
costguard audit my-app --ci-only

# Cron check only, JSON output
costguard audit my-app --crons-only --json

# Add provider billing checks for specific providers (only those whose token is present)
costguard audit --all --providers github,supabase

# Add provider checks for every provider whose token is present
costguard audit --all --providers all
```

| Option | Effect |
|--------|--------|
| `--all` | Audit all registered workspaces |
| `--ci-only` | Run only the CI-minute checks |
| `--crons-only` | Run only the cron-frequency checks |
| `--site` | Also run read-only live-site checks for workspaces whose registry entry has a `site` URL (see [site](#site)) |
| `--substitutions` | Add cross-tool `<provider>/cheaper-alternative` suggestions (e.g. a static Vercel/Netlify Pro site → Cloudflare Pages), each with a sourced saving, migration effort, and lock-in caveat |
| `--providers <list>` | Add read-only provider billing checks. Comma-separated ids (`github,supabase,railway,netlify,neon`) or `all`. A provider is only contacted when its token is present (see [Environment variables](#environment-variables)); others are silently skipped. |
| `--json` | Emit JSON instead of Markdown |

### scan

Static-only audit across all workspaces. A convenience alias intended for a
single catch-all CI step; it never touches provider credentials.

```sh
costguard scan
costguard scan --ci      # CI minutes only
costguard scan --crons   # Cron schedules only
```

### providers

Report which provider tokens are present in the environment, by
environment-variable **name** only. Secret values are never read into output,
printed, or logged.

```sh
costguard providers --check
```

`--check` is the default action.

### discover

Detect which providers a repo actually uses — from config files, `package.json`
dependencies, and environment-variable **names** (never values, never secrets).
Covers all 13 wired providers plus inngest, so you don't hand-edit the registry.

```sh
# List detected providers + the evidence for each (default dir: .)
costguard discover ./my-app

# JSON: { dir, providers, detections }
costguard discover ./my-app --json

# Union-merge detected providers into ./workspaces.json (non-destructive)
costguard discover ./my-app --write
```

`--write` preserves any existing providers, the `active{}` block, and every other
workspace; it only adds newly detected providers for `basename(dir)`.

### site

Audit a **live URL** for cost-relevant waste — read-only and GET-only (no
browser, no form submit, no credential replay). It flags transfer weight,
oversized images, missing compression, weak cache headers, and render-blocking
scripts. The page's `$/mo` headline is the single `site/transfer-weight` line
(sourced when the host bills transfer — Vercel/Netlify — or an explicit `$0`
performance note when it doesn't, e.g. Cloudflare Pages static / unknown host;
never a fabricated number). Per-asset findings (`oversized-image`,
`missing-compression`) report their dollar share in the `detail` text and carry
`estMonthlyUsd: 0` so the headline isn't double-counted. A `$0` performance-only
page never raises a `high` finding, so it never fails CI on cost alone.

```sh
costguard site https://example.com
costguard site https://example.com --json
```

Use `audit --site` to run the same checks for every workspace whose
`workspaces.json` entry declares a `site` URL.

### registry

Manage the workspace registry (`workspaces.json`).

```sh
# List all registered workspaces and detected providers
costguard registry --list

# Validate the registry against the filesystem
costguard registry --validate

# Scan ~/Workspaces and write a fresh workspaces.json
costguard registry --init
```

`--list` is the default when no option is given.

### report

Re-render the most recent saved audit run without re-scanning.

```sh
costguard report --last
costguard report --last --json
```

### fix

Deterministically auto-fix the safe CI rules in-repo: `paths-ignore`,
`concurrency`, and `timeout-minutes`. It only edits `.github/workflows/*` files
inside the target workspace and **never** touches provider or cloud state. It
**defaults to a dry run** — it prints a unified diff and writes nothing until you
pass `--apply`.

```sh
# Dry run: print the unified diff for a workspace, write nothing (default)
costguard fix my-app

# Dry run across all workspaces
costguard fix --all

# Write the edits to disk (idempotent — safe to re-run)
costguard fix my-app --apply

# Write local PR artifacts (branch name, patch, PR body) under ~/.costguard/pr/
costguard fix my-app --pr
```

| Option | Effect |
|--------|--------|
| `--all` | Fix all registered workspaces |
| `--apply` | Write the edits to disk. Idempotent. Omit for a dry-run preview. |
| `--pr` | Write local PR artifacts (`branch.txt`, `fix.patch`, `pr-body.md`) under `~/.costguard/pr/<workspace>/`. No network or git action. |
| `--open-pr` | **Gated and inert.** Refuses unless **both** the `--open-pr` flag and a non-empty `GITHUB_TOKEN` are present, and even then performs **no** git branch, commit, or push — this build is dry-run only. |

### digest

Produce a concise **monthly** summary — total `$/mo`, a per-provider breakdown,
and the top findings — distinct from the full `report`. It **defaults to printing
to stdout** (a dry run). The digest deliberately omits per-finding `detail`/`fix`
text; run `report --last` for the full breakdown.

```sh
# Print the monthly digest to stdout (default)
costguard digest --all

# Render from the last saved run
costguard digest --last

# JSON output
costguard digest --all --json

# Write it to a local file instead of stdout
costguard digest --all --out digest-2026-05.md
```

| Option | Effect |
|--------|--------|
| `--all` | Build the digest across all registered workspaces |
| `--last` | Render the digest from the last saved run instead of re-scanning |
| `--json` | Emit JSON instead of Markdown |
| `--out <file>` | Write the digest to a local file instead of stdout |
| `--post` | **Gated and inert.** Requires **both** the `--post` flag and a `COSTGUARD_DIGEST_WEBHOOK` env var; even then it performs **no** network post. It only reports the message it *would* post. |

---

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | All checks passed (or only INFO/WARN findings) |
| `1` | At least one HIGH severity finding (CI gate signal) |
| `1` | Error loading registry, config, or invalid arguments |

---

## From source

The plugin and npm installs are prebuilt — you only need a build when developing
from a checkout:

```sh
pnpm install
pnpm build      # emits dist/cli/index.js and dist/mcp/server.js
pnpm test
```

### Local checks (run CI without GitHub minutes)

GitHub Actions is metered on private repos, so CI is gated to run only when the
repo is public or via manual dispatch. Run the exact same checks locally instead:

```sh
pnpm verify     # typecheck + lint + test + check:dist (mirrors .github/workflows/ci.yml)
```

Enable the pre-push hook to run `pnpm verify` automatically before every push:

```sh
git config core.hooksPath .githooks   # once per clone
git push --no-verify                  # bypass for a single push (e.g. docs-only)
```

#### Run the real workflow in Docker (act)

To execute the actual `ci.yml` locally in a container — the closest thing to
GitHub's runner without spending minutes — use [`act`](https://github.com/nektos/act)
with Docker Desktop running:

```sh
gh extension install nektos/gh-act    # once per machine
pnpm ci:docker                        # runs the ubuntu-latest leg via .actrc
```

`act` runs Linux containers only, so it covers the **ubuntu-latest** matrix leg;
the **windows-latest** leg is covered by `pnpm verify` on the host. The first run
pulls the runner image (~1GB), then caches it.

---

## Related Projects

- **[Maestro](https://github.com/mbanderas/maestro)**: Frontier multi-CLI fusion engine and orchestration discipline layer for AI coding agents. CostGuard finds the cost leaks; Maestro keeps the agents that fix them disciplined — verified done-claims, surgical scope, and a research-backed multi-agent gate.
- **[Govyn](https://govynai.com)**: Open-source AI agent governance proxy — your agents never hold real API keys, stay within budget, and follow policy. CostGuard audits the spend; Govyn enforces the guardrails at runtime.

---

## Links

- **GitHub:** https://github.com/mbanderas/costguard
- **Issues:** https://github.com/mbanderas/costguard/issues
- **License:** [MIT](LICENSE)
