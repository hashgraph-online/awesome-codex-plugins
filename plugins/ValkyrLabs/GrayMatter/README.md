# GrayMatter

GrayMatter is an installable and immediately usable OpenClaw skill for:
- **primary durable memory**
- **shared object-graph state**
- **live organizational schema awareness** through the ValkyrAI `api-0` OpenAPI

GrayMatter lets an OpenClaw instance move beyond file memory and isolated chat context.
When properly authenticated, the agent can persist durable memory, inspect the live business schema, and operate inside the organization's RBAC-scoped data environment.

## Ready-to-rock release surfaces

GrayMatter ships as three related but independently usable surfaces:

- **MCP service**: `mcp-server/` runs as an HTTP/SSE service for Claude.ai, Claude Code, Cursor, ChatGPT Apps SDK, and any MCP-compatible host, and also supports `node mcp-server/index.js --stdio` for plugin-managed MCP launch.
- **Codex plugin**: `.codex-plugin/plugin.json` exposes this repo as the `graymatter` plugin with the standalone skill plus `.mcp.json`, so Codex can discover both the instructions and the MCP server.
- **Standalone OpenClaw skill**: `graymatter.skill` packages `SKILL.md` and the required scripts for OpenClaw install, activation, hosted api-0 use, and GrayMatter Light local mode.

If a GitHub sparse/root install only brings down root files, run `./graymatter-bootstrap` from the installed GrayMatter directory. It restores `scripts/` and `mcp-server/` from the bundled `graymatter.skill` archive so end-user installs do not depend on a full repo clone.

## What GrayMatter is for

GrayMatter is the memory and context layer for business-native agent systems.

It is designed so an OpenClaw instance can:
- read and write `GrayMatter` and `MemoryEntry` records
- coordinate through graph state using `SwarmOps`
- understand the **entire available schema** exposed by the tenant/account
- adapt to the actual business environment, for example customers, invoices, products, notes, files, workflows, tasks, CMS-like content, strategy objects, and sales records
- use file-based memory only as bootstrap or fallback

This is the core idea:

> GrayMatter is not just memory storage.
> It is the authenticated object-relational memory graph and schema-awareness layer that lets the agent inhabit the organization safely and usefully.

## Primary-memory model

Boundary rule:
This skill stays thin. It should teach usage intent, durable type selection, and operator ergonomics.
Retry behavior, auth/session refresh, fallback queueing, and replay execution belong to shared GrayMatter infrastructure contracts.
Keep this repository aligned with those contracts rather than re-implementing them.

GrayMatter should be the **primary durable memory system**.

Use local files only as:
- bootstrap context on first startup
- fallback when `api-0` is unavailable
- temporary replayable backup when a write path is blocked

### Durable memory targets

Primary targets:
- `/MemoryEntry`
- `/MemoryEntry/query`
- `/MemoryEntry/read`
- `/MemoryEntry/write`
- `/GrayMatter`
- `/SwarmOps/graph`

Typical `MemoryEntry.type` values:
- `decision`
- `todo`
- `context`
- `artifact`
- `preference`

## Entire-schema capability

GrayMatter should load the live ValkyrAI OpenAPI at startup:

- `https://api-0.valkyrlabs.com/v1/api-docs`

This gives the agent live knowledge of the environment it is operating in.

That means the agent can inspect what entities and operations actually exist for the current deployment, instead of relying on stale assumptions.

### Why this matters

Most businesses are not just “memory plus chat.”
They have structured operational data.

Examples observed in the current live schema include:
- `Organization`
- `Customer`
- `Opportunity`
- `Invoice`
- `Product`
- `Application`
- `Workbook`
- `Workflow`
- `Task`
- `Note`
- `MediaObject`
- `FileRecord`
- `SalesActivity`
- `SalesPipeline`
- `Goal`
- `StrategicPriority`
- `KeyMetric`
- `Agent`
- `Space`
- `GrayMatter`
- `MemoryEntry`
- `SwarmOps`

The current live endpoint exposes a large domain surface, including 100+ tags and hundreds of paths. The exact usable subset is still governed by the human's credentials, organization setup, and RBAC.

This is what makes GrayMatter powerful: the agent can become deeply context-aware inside the business without overreaching beyond granted permissions.

## Safety model

GrayMatter is powerful because access is authenticated and tenant-scoped.
It is also safe by design when used correctly because:
- access is bounded by the current account's RBAC
- the user and organization permissions determine what the agent can see and change
- permission failures can be surfaced cleanly
- the skill should never assume universal access just because the schema exists

Rule:
- **schema visibility does not equal permission to use everything**

## Repository contents

- `SKILL.md` — OpenClaw AgentSkill instructions
- `graymatter.skill` — packaged distributable AgentSkill
- `scripts/graymatter_api.sh` — authenticated production API transport
- `scripts/gm-login` — login helper
- `scripts/gm-activate` — one-shot auth + install + agent registration + schema sync bootstrap
- `scripts/gm-install-check` — dependency and auth readiness check
- `scripts/gm-smoke` — production smoke test for write/query validation
- `scripts/gm-query` — query `MemoryEntry`
- `scripts/gm-write` — write `MemoryEntry`, with tagged-write fallback behavior
- `scripts/gm-fallback-append` — append failed writes to local replay queue at `memory/graymatter-fallback.json`
- `scripts/gm-graph` — inspect Swarm graph endpoints
- `scripts/gm-openapi-sync` — fetch and cache the live OpenAPI spec locally
- `scripts/gm-openapi-summary` — summarize live schema domains and endpoints
- `scripts/gm-status` — quick health/status surface for auth source, fallback queue, and OpenAPI cache
- `scripts/gm-client` — generic REST wrapper for GET/POST/PUT/PATCH/DELETE against GrayMatter API paths
- `scripts/gm-entity` — generic helper for listing, reading, and writing arbitrary schema entities
- `scripts/gm-register-agent` — register or refresh the OpenClaw server as an Agent in api-0
- `scripts/gm-mcp-contract` — emit the portable MCP memory-tool contract schema used by agent/IDE adapters
- `scripts/gm-light-bootstrap` — generate the local GrayMatter app bundle and server source scaffold
- `scripts/gm-light-up` — generate and start the local ThorAPI-backed GrayMatter Light instance
- `scripts/gm-light-env` — print the environment exports that point skill scripts at the running Light instance
- `scripts/gm-light-json-smoke` — JSON-file fallback smoke test for Light payload shape without ThorAPI
- `scripts/package-local-server` — package the standalone downloadable GrayMatter Local Server archive
- `scripts/package_graymatter.py` — deterministic validation and packaging
- `mcp-server/` — standalone HTTP/SSE and Apps SDK `/mcp` server for GrayMatter memory, graph, entity, schema, and overview tools
- `docs/architecture.md` — architecture and operating model
- `docs/openai-app-directory-submission.md` — Apps SDK submission checklist and copy
- `docs/privacy-policy.md` — GrayMatter-specific public privacy policy source
- `docs/reviewer-test-credentials.md` — review demo-account setup and secure credential handoff runbook
- `docs/prd-context-compaction-reset.md` — PRD for bounded chat compaction and reset flows
- `docs/thorapi-integration.md` — ThorAPI relationship and bundle direction
- `docs/graymatter-light.md` — local/offline notes
- `openai-app/submission-manifest.json` — non-secret app metadata for OpenAI dashboard submission
- `examples/*` — example payloads and Light-mode starter assets
- `references/*` — release and multi-agent guidance, including concurrency conventions
- `references/mcp/memory-tool-contract.v1.json` — stable v1 portable tool contract for memory and graph operations
- `clawhub.json` — publishing metadata

## Install and use immediately

## Account signup and credits

For a new GrayMatter account, use:
- Signup: <https://api-0.valkyrlabs.com/v1/auth/signup>
- Credits and recharge: <https://api-0.valkyrlabs.com/v1/credits>

Commercial model:
- fresh signups should receive **500 starter credits** automatically
- GrayMatter query and some higher-order operations consume credits
- after the starter balance is exhausted, account recharge is required for full GrayMatter functionality

## First-run auth, the intended OpenClaw flow

The user should **not** have to manually acquire or paste a raw auth token.

The intended first-run OpenClaw auth step is:
1. OpenClaw prompts the user for their `api-0` username
2. OpenClaw prompts for their password
3. OpenClaw exchanges those credentials for a session
4. OpenClaw stores the resulting session securely in macOS/iCloud Keychain
5. OpenClaw creates or refreshes an Agent record for itself in api-0
6. Subsequent GrayMatter use reads from Keychain automatically

That means GrayMatter should feel like:
- sign in once
- store securely
- use forever after until refresh is needed

Manual token handling is a fallback/debug path, not the primary user experience.

### Repo-based install

```bash
git clone https://github.com/ValkyrLabs/GrayMatter.git
cd GrayMatter
brew install jq
scripts/gm-activate
```

`scripts/gm-activate` is the intended one-shot bootstrap for OpenClaw installs. It can use:
- interactive username/password prompts, or
- credentials already present in environment variables

Supported env inputs:
- `GRAYMATTER_USERNAME` or `VALKYR_USERNAME`
- `GRAYMATTER_PASSWORD` or `VALKYR_PASSWORD`
- optional `VALKYR_AUTH_TOKEN`
- optional `VALKYR_KEYCHAIN_SERVICE` if a non-default macOS Keychain service name is required
- optional `OPENCLAW_INSTANCE_ID`
- optional `OPENCLAW_AGENT_NAME`
- optional `OPENCLAW_AGENT_ROLE`

`scripts/gm-login` should be treated as the standard OpenClaw login step. It prompts for username/password and stores the session in macOS/iCloud Keychain by default.

`scripts/gm-register-agent` is part of the expected startup handshake. When an OpenClaw server connects to api-0, it should create or refresh an Agent record for itself before proceeding with normal work.

At that point the install should be immediately usable.

If auth succeeds but memory query is temporarily credit-gated, `scripts/gm-activate` now continues in a degraded mode: auth is stored, the agent is registered, the OpenAPI is synced, and the script reports that memory query capability is limited until credits are available.

### Packaged-skill install

1. Import or place `graymatter.skill` in the target OpenClaw skills directory
2. Confirm the extracted folder resolves to `graymatter/`
3. Run:

```bash
scripts/gm-activate
```

If those pass, the skill is installable and usable.

## Fresh-install acceptance standard

GrayMatter counts as launch-ready only if a fresh user can:

1. install the repo or packaged skill
2. authenticate successfully
3. pass install validation
4. write and query a `MemoryEntry`
5. inspect graph state
6. register the OpenClaw instance as an Agent in api-0
7. fetch and summarize the live OpenAPI
8. inspect at least one live entity family from the business schema

If those do not work, the skill is not truly ready.

## Bootstrap integration for OpenClaw

The workspace `BOOTSTRAP.md` should be rewritten so OpenClaw:
- uses GrayMatter as its **primary durable memory**
- loads the live OpenAPI at startup
- understands the organization schema as the operating environment
- uses local file memory only as backup

That startup model is now part of the GrayMatter launch plan.

## Typical usage

### Durable memory

```bash
scripts/gm-write decision "GrayMatter is primary memory for this instance"
scripts/gm-query "GrayMatter" 10
```

### Scoped memory

Use `sourceChannel` as the retrieval scope key for chat-, workspace-, and automation-specific memory. `gm-write` can derive that key from explicit scope fields or from a local path, then writes a compact `[graymatter-scope]` header into `MemoryEntry.text` so the hierarchy remains auditable even when tags are unavailable.

```bash
scripts/gm-write context "Research complete; publish blocked" \
  --scope-path "$HOME/.codex/automations/mcp-and-skill-hunter/memory.md"

scripts/gm-query "publish blocked" 5 context \
  --scope-path "$HOME/.codex/automations/mcp-and-skill-hunter/memory.md"
```

For that path, GrayMatter derives `sourceChannel=codex:automation:mcp-and-skill-hunter`. For Codex project folders under `Documents/Codex/<date>/<slug>`, it derives `sourceChannel=codex:workspace:<date>/<slug>`. Use `--chat-key`, `--session-key`, `--workspace-key`, or `--automation-id` when a host can provide stronger identifiers than a file path.

### Tagged write with automatic fallback

```bash
scripts/gm-write context "launch handoff" discord "launch,graymatter"
```

If tag persistence is broken on the backend, the script retries without tags instead of failing the whole write.

If the API call still fails, `gm-write` appends the attempted write to `memory/graymatter-fallback.json` when `scripts/gm-fallback-append` is present.

### One-shot activation

```bash
scripts/gm-activate
```

This is the preferred OpenClaw install/bootstrap entrypoint.

### Agent self-registration

```bash
scripts/gm-register-agent
```

This should run when an OpenClaw server first connects to api-0 so the system has an explicit Agent record for that instance.

### Graph state

```bash
scripts/gm-graph GET
```

### Live schema sync

```bash
scripts/gm-openapi-sync
scripts/gm-openapi-summary
scripts/gm-status
```

### Arbitrary schema entity access

```bash
# list visible organizations
scripts/gm-entity Organization

# fetch one customer
scripts/gm-entity Customer 123

# create a note if authorized
scripts/gm-entity Note POST '{"title":"Launch","content":"GrayMatter launch work"}'
```

## Auth

GrayMatter uses:
- `VALKYR_API_BASE`, default `https://api-0.valkyrlabs.com/v1`
- macOS/iCloud Keychain lookup for `VALKYR_AUTH`
- `VALKYR_AUTH_TOKEN` as the primary env override/debug path
- `VALKYR_JWT_SESSION` as a compatible env fallback for downstream tooling

Preferred auth flow:
- check Keychain for `VALKYR_AUTH` first
- if present, reuse it automatically
- otherwise prompt for username and password once
- exchange for a `VALKYR_AUTH` token
- store that token securely in Keychain for future runs

Do not hardcode secrets into the repo or skill.
Do not print tokens.
Do not make manual token handling the normal user workflow.

## OpenClaw operating guidance

In a GrayMatter-native workspace, the agent should:

1. query GrayMatter for durable context first
2. inspect relevant live business entities second
3. fall back to local files only if GrayMatter is unavailable or incomplete
4. keep durable writes concise and reusable
5. treat the live schema as the organization's environment model

This is how the agent becomes the right operator for a business, not just a chatbot with a diary.

## Local fallback behavior

If `api-0` is unavailable or a write path is temporarily broken:
- write the smallest safe local backup
- keep it replayable
- retry later when GrayMatter is healthy again

Typical fallback files:
- `memory/YYYY-MM-DD.md`
- `MEMORY.md`
- `memory/graymatter-fallback.json`

## Troubleshooting

### `VALKYR_AUTH_TOKEN is required`

No env token is set and no matching macOS Keychain secret was found.

Fix:
- run `scripts/gm-login` and complete username/password sign-in, or
- export `VALKYR_AUTH_TOKEN`, or
- ensure Keychain secret `VALKYR_AUTH` exists

### `jq: command not found`

Install `jq`.

On macOS:

```bash
brew install jq
```

### Tagged write fails

Some deployments still have a `MemoryEntry.tags` persistence mismatch.

Fix:
- use `scripts/gm-write`
- let it retry automatically without tags

### Query fails with a credits or billing error

If writes and reads succeed but `/MemoryEntry/query` fails with a credit error, that is usually an account billing configuration issue rather than a GrayMatter auth failure.

Observed requirement:
- query currently consumes credits
- a fresh signup should auto-provision **500 credits** so GrayMatter query works immediately
- after starter credits are exhausted, the user must recharge credits to continue full GrayMatter functionality

Useful links:
- signup: <https://api-0.valkyrlabs.com/v1/auth/signup>
- credits and recharge: <https://api-0.valkyrlabs.com/v1/credits>
- buy credits: <https://valkyrlabs.com/buy-credits>
- human signup form: <https://valkyrlabs.com/funnel/white-paper>

CLI behavior on `INSUFFICIENT_FUNDS`:
- prints both buy and signup links in stderr
- attempts a popup prompt on macOS (`osascript`) and Windows (`powershell.exe`)
- opens the buy-credits URL as a last-resort fallback when popup tooling is unavailable

Optional overrides for custom deployments:
- `VALKYR_BUY_CREDITS_URL`
- `VALKYR_HUMAN_SIGNUP_URL`

If a new account has `0.00` balance, activation may still succeed for write/read operations while query fails until credits are provisioned.

### Login succeeds but no session is found

Some api-0 deployments return auth in headers or cookies rather than in the JSON response body.

Fix:
- use the latest `scripts/gm-login`
- it now treats `VALKYR_AUTH` as the primary auth contract
- downstream API calls send the recovered token back as bearer auth, `VALKYR_AUTH`, and cookie auth

### OpenAPI fetch fails

Check:
- outbound network access
- `api-0` availability
- whether the environment blocks the docs endpoint

If the live docs cannot be fetched, use the last cached copy temporarily, but treat it as stale.

## Packaging

Rebuild the packaged skill with:

```bash
python3 scripts/package_graymatter.py
```

Run an actual local ThorAPI-backed Light instance with:

```bash
scripts/gm-light-up
source .graymatter-light/.graymatter-light-env
scripts/gm-write context "GrayMatter Light is running" local-light
scripts/gm-query "GrayMatter Light"
```

`gm-light-up` generates the api.hbs.yaml template at `.graymatter-light/api.hbs.yaml`, rendered api.yaml at `.graymatter-light/api.yaml`, the Docker Compose file, and the Light control panel, then starts the ThorAPI image with `THORAPI_TEMPLATE=/app/api.hbs.yaml` and `THORAPI_SPEC=/app/api.yaml`. The default image is `ghcr.io/valkyrlabs/thorapi:latest`; use `--image` or `THORAPI_IMAGE` when running a private, pinned, or locally built ThorAPI image. The rendered spec explicitly includes the MCP backing paths for `memory_write`, `memory_read`, `memory_query`, `graph_get`, entity tools, and `schema_summary`. The env file sets `VALKYR_API_BASE=http://localhost:8080` and `GRAYMATTER_LIGHT_MODE=true`, so the normal GrayMatter skill scripts and the standalone MCP server can connect to the running local instance without requiring hosted api-0 auth.

Build the standalone downloadable local server with:

```bash
scripts/package-local-server
```

That creates `dist/graymatter-local-server-latest.tar.gz`. The archive contains:
- `application-bundle/` with the ValkyrAI app-factory template, ThorAPI FEBE OpenAPI contract, custom dashboard/workbench/promotion/swarm components, and built-in `rbac-core` / `data-workbooks` component references
- `source/` with the generated Spring Boot local server
- `bin/graymatter-local-server` launcher
- `lib/graymatter-local-server.jar` when Maven is available during packaging

The embedded dashboard includes Valkyr Labs branding, hides the local login panel after successful login, exposes `Promote / Synchronize` for the valkyrlabs.com mothership bridge, and reports the local `graymatter-swarm-v0.1` light-node status.

## awesome-codex-plugins listing kit

GrayMatter ships a ready-to-submit listing packet for `awesome-codex-plugins`.

- Listing markdown block: `docs/awesome-codex-plugins.md`
- Source metadata: `.codex-plugin/plugin.json`

Quick copy flow:

```bash
cat docs/awesome-codex-plugins.md
```

Then open a PR against `hashgraph-online/awesome-codex-plugins` and paste the generated block into `README.md` using that repository's contribution format.

## Launch position

The launch target is simple:

- GrayMatter installs cleanly as an OpenClaw skill
- OpenClaw boots into GrayMatter-first memory behavior
- the agent loads the live OpenAPI schema at startup
- the agent understands both durable memory and the broader organization object graph
- file memory remains backup, not the center of gravity

That is the version of GrayMatter worth shipping.
