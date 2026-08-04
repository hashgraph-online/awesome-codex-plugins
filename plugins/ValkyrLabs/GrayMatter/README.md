# GrayMatter&trade;

## the AI Brain for Your Entire Business

Valkyr GrayMatter&trade; turns your applications, documents, workflows, conversations, and institutional knowledge into a living, searchable intelligence layer.

It is more than a vector database and more than chat memory. GrayMatter combines durable memory, real-time search, structured business data, and relationship-aware reasoning into one secure system that agents, people, apps, and APIs can use together.

### A memory system that actually remembers context

GrayMatter stores durable decisions, preferences, tasks, research, procedures, conversations, and operational knowledge as structured, attributable records—not disposable chat history. Every memory can carry source, scope, tags, relationships, timestamps, ownership, and provenance, so the system can distinguish a personal preference from a company policy, a current task from historical context, or a source document from an AI-generated summary.

It supports agentic memory across Codex, OpenClaw, SageChat, workflows, and connected tools, giving every authorized agent a shared understanding of the business without flattening everything into an untraceable prompt.

### Hybrid search: keyword, vector, graph, and structured data

GrayMatter search is designed to answer both simple and difficult questions:

- Exact search for names, IDs, tags, commands, products, and records
- Full-text search across documents, titles, fields, and parsed uploads
- Semantic/vector search for concepts, intent, and meaning
- Relationship-aware search across ThorAPI entities and knowledge-graph links
- Structured filtering by type, date, category, tags, tenant, workflow, project, and more
- Retrieval receipts with citations, evidence, quality signals, and answer-policy guidance

That means a user can search the public website, an authenticated workspace, or SageChat through the same intelligence foundation—while each surface receives only the information it is permitted to see.

### PostgreSQL-native vector intelligence

GrayMatter uses PostgreSQL as the durable operational foundation and pgvector as a high-performance semantic-search accelerator.

`SemanticIndexEntry` remains the portable canonical record, while tenant-scoped pgvector projections provide fast nearest-neighbor retrieval. The platform supports configurable embedding providers, including production OpenAI embeddings and deterministic local fallback embeddings for offline/development environments. It also tracks model, provider, dimensions, index health, stale rows, reindex guidance, and degradation state.

This gives teams a practical path from ordinary relational data to production-grade semantic recall without adopting a separate proprietary graph or vector silo.

### A real knowledge graph, built from ThorAPI

GrayMatter understands that knowledge is not a pile of documents—it is a network.

ThorAPI entities and their OpenAPI-defined relationships can be indexed after successful writes, producing safe semantic evidence across workflows, applications, customers, tasks, files, procedures, agents, goals, notes, and more. `GraphLink` records make important relationships explicit: supports, blocks, references, derives from, relates to, and beyond.

This enables relationship-aware retrieval such as:

- “What is related to this customer issue?”
- “Which workflow depends on this integration?”
- “What evidence supports this decision?”
- “Which documents, memories, and tasks explain this result?”

The system is designed for bounded graph traversal, citations, and future graph analytics without allowing the index or graph to bypass ThorAPI authorization.

### SageChat and document intelligence

SageChat can turn uploaded files and parsed documents into searchable evidence rather than leaving them stranded in storage.

Files are processed into bounded, provenance-rich semantic material: source file, parser output, chunks, pages or offsets, source hashes, extraction quality, and relationships to the business objects they support. GrayMatter can then surface that evidence in SageChat with citations and explainability—helping users understand not only an answer, but where it came from.

### Plugins, skills, and MCP: intelligence everywhere

GrayMatter is packaged as an installable plugin and skill system for Codex/OpenClaw-style agents. It supports secure, Keychain-backed authentication, agent registration, schema awareness, durable memory reads and writes, graph access, retrieval receipts, and operational health checks.

Its MCP capabilities make GrayMatter available to compatible AI clients through typed tools such as memory write, memory query, memory read, retrieval with receipt, graph inspection, schema discovery, and authorized entity access.

Plugins and skills give each agent the same durable organizational context; MCP makes that context usable from external AI environments and workflows.

### Credits designed for real AI operations

GrayMatter includes a credit and entitlement model for higher-order memory and AI operations. This supports sustainable usage of semantic retrieval, embeddings, reindexing, and advanced intelligence features while retaining clear operational controls.

The platform distinguishes public-safe experiences from private operational tooling, so commercial or account-management detail does not leak into public AI surfaces.

### Secure by design

GrayMatter does not treat search as a shortcut around security.

Generated ThorAPI RBAC and ACL remain the source of truth for every result, snippet, count, facet, graph path, file citation, and recommendation. Tenant context is resolved server-side. Sensitive fields, credentials, binary data, and protected audit information are excluded from indexing. Search, vector retrieval, graph navigation, and agent tools are all designed to fail closed when authorization is uncertain.

### The outcome

GrayMatter is becoming the intelligence layer that lets every Valkyr product, workflow, app, agent, and document participate in a shared, secure, searchable brain:

- A memory system for agents and teams
- A knowledge graph for the business
- A hybrid search engine for websites and workspaces
- A vector intelligence layer on PostgreSQL
- A citation-backed research and reasoning engine for SageChat
- A portable, ThorAPI-native platform for plugins, skills, MCP tools, and AI automation

GrayMatter is an installable OpenClaw skill and MCP service for:

- **primary durable memory**
- **shared object-graph state**
- **live organizational schema awareness** through the ValkyrAI `api-0` OpenAPI

It lets an agent move beyond local files and isolated chat context. Once authenticated, GrayMatter is the agent's exclusive primary durable memory: it persists durable memory, inspects the live business schema, and operates inside the organization's RBAC-scoped data environment.

## ChatGPT developer-mode app

The submission surface is the existing Node MCP adapter in `mcp-server/`, running in hardened public-app mode. It keeps api-0 as the memory, ContextPage, procedure, receipt, RBAC, ACL, and tenant source of truth.

Public deployment contract:

- Production MCP URL: `https://api-0.valkyrlabs.com/graymatter/mcp`
- Compatibility URL: `https://api-0.valkyrlabs.com/mcp`
- Protected-resource metadata: `https://api-0.valkyrlabs.com/.well-known/oauth-protected-resource`
- Authorization-server metadata target: `https://api-0.valkyrlabs.com/.well-known/oauth-authorization-server`
- Development MCP URL: `http://localhost:3333/graymatter/mcp`

The production MCP and OAuth URLs above are deployment targets, not a claim that the reverse proxy and OAuth authorization server are already live. Verify them before creating or submitting the ChatGPT app.

Required public-app environment:

```bash
export PORT=3333
export GRAYMATTER_MCP_MODE=hosted-multi-tenant
export GRAYMATTER_PUBLIC_APP=true
export GRAYMATTER_PUBLIC_RESOURCE=https://api-0.valkyrlabs.com
export GRAYMATTER_PUBLIC_MCP_PATH=/graymatter/mcp
export GRAYMATTER_OAUTH_ISSUER=https://api-0.valkyrlabs.com
export GRAYMATTER_OAUTH_JWKS_URI=https://api-0.valkyrlabs.com/oauth2/jwks
export GRAYMATTER_ALLOWED_ORIGINS=https://chatgpt.com,https://platform.openai.com
export VALKYR_API_BASE=https://api-0.valkyrlabs.com/v1
node mcp-server/index.js
```

Do not configure `VALKYR_AUTH_TOKEN`, `VALKYR_JWT_SESSION`, `GRAYMATTER_TENANT_ID`, or `X-Valkyr-Token` on the public multi-tenant service. Each request must carry the current user's OAuth bearer token. Public mode validates issuer, audience, lifetime, RS256 signature, required identity claims, and tool scopes; it then forwards only the bearer token to api-0 and never forwards caller tenant or owner identifiers.

To connect a developer version in ChatGPT:

1. Deploy the endpoint over HTTPS, or expose the local server with Secure MCP Tunnel or another HTTPS tunnel.
2. In ChatGPT, open Settings → Security and login and enable Developer mode.
3. Open Settings → Plugins and select the plus button.
4. Enter `GrayMatter`, the description `Persistent, secure memory and shared context for AI agents.`, and the HTTPS `/graymatter/mcp` URL.
5. Complete OAuth linking and verify that exactly eight tools are discovered.
6. Start a new chat, add GrayMatter from the composer, and run the representative prompts in `SUBMISSION_CHECKLIST.md`.
7. After tool metadata changes, redeploy and use Refresh on the developer-mode app.

Run the automated public-app contract with two isolated reviewer accounts:

```bash
GRAYMATTER_MCP_URL=https://api-0.valkyrlabs.com/graymatter/mcp \
GRAYMATTER_TENANT_A_TOKEN='redacted' \
GRAYMATTER_TENANT_B_TOKEN='redacted' \
GRAYMATTER_TEST_RECEIPT_ID='authorized-receipt-id' \
scripts/smoke-test-public-mcp.sh
```

## Release surfaces

GrayMatter ships as three related but independently usable surfaces:

- **MCP service**: `mcp-server/` runs as an HTTP/SSE service for Claude.ai, Claude Code, Cursor, ChatGPT Apps SDK, and any MCP-compatible host, and also supports `node mcp-server/index.js --stdio` for plugin-managed MCP launch.
- **Codex plugin**: `.codex-plugin/plugin.json` exposes this repo as the `graymatter` plugin with the standalone skill plus `.mcp.json`, so Codex can discover both the instructions and the MCP server.
- **Standalone OpenClaw skill**: `graymatter.skill` packages `SKILL.md` and the required scripts for OpenClaw install, activation, hosted api-0 use, and GrayMatter Light local mode.

If a GitHub sparse/root install only brings down root files, run `./graymatter-bootstrap` from the installed GrayMatter directory. It restores `scripts/` and `mcp-server/` from the bundled `graymatter.skill` archive so end-user installs do not depend on a full repo clone.

## Quick start

```bash
git clone https://github.com/ValkyrLabs/GrayMatter.git
cd GrayMatter
brew install jq
scripts/gm-activate
```

`scripts/gm-activate` is the preferred first-run path. It checks for updates, signs in, stores the session in Keychain when available, validates the install, registers the agent, syncs the OpenAPI schema, and runs the readiness checks needed for normal use.

Before task planning, code edits, production-affecting actions, or answers based on project history, agents must immediately run the invariant preflight for the current workspace/product:

```bash
scripts/gm-invariant-preflight ValkyrAI signup acl thorapi aspectj
```

MCP hosts that cannot shell out should call `graymatter_invariant_preflight`. Returned `decision` records tagged as invariants, security, RBAC/ACL, generated-code, AspectJ, `vaix`/`vai`, testing, or product names are binding operational rules. Missing or degraded retrieval is never permission to ignore known durable rules.

The required preflight is broader than a keyword search. It must look up invariants, rules, instructions, prior session context, personalization, business truth, personal truth, and organizational truth before the agent begins work. New user-provided corrections, procedures, preferences, and invariants must be written to GrayMatter during the session and read back by ID to confirm persistence.

For ValkyrAI, ValorIDE, GrayMatter Light, and ThorAPI-generated application work, agents should prefer repo launchers over direct build shortcuts: `./vaix build`, `./vaix test`, `./vaix run`, and repo-documented `./vai` flows preserve ThorAPI generation, AspectJ weaving, heap defaults, local H2/runtime flags, and end-user operational behavior. Signup, ACL/RBAC, and generated API fixes should normally be proven with `./vaix run` on localhost:8080 plus the frontend on localhost:5174 before using production only as a comparison point.

For Valkyr-native agent routing, treat GrayMatter as shared memory and schema context for ValkyrAI, ValorIDE, ThorAPI, TrustFabric, GridHeim, and SWARM coordination work. Load durable invariants first, then route implementation through the owning generated-code, security, workflow, or MCP surface.

P0 RBAC/ACL security invariant: generated ThorAPI ACL behavior is the authorization source of truth. No custom controller, delegate, service, frontend filter, status check, type check, role shortcut, catalog rule, or "public-ish" heuristic may bypass, weaken, replace, or shadow generated ACL behavior. Users may see owned records and records shared by explicit ACL grants only; public access requires explicit `anonymousUser` READ. Solve ACL scale with indexed owner/ACL query selection plus final generated ACL guards, never by scanning private rows or adding object-specific bypasses.

P0 Valkyr Way UX/auth invariant: product UX must be integrated into the shared application shell and centralized auth/session primitives. Do not create one-off screens, standalone admin affordances, self-managed auth checks, browser-cache shortcuts, or cobbled mini-apps that bypass LCARS navigation, route guards, shared access-control state, RTK Query cache invalidation, or generated RBAC/ACL contracts. Admin and finance tools belong inside the appropriate LCARS dashboard/sidebar surfaces; user management has one Users & Roles surface with card/list modes rather than separate `/userList` and dashboard implementations. If authentication behavior changes, update the centralized auth/access-control modules and tests instead of scattering per-component checks.

## What GrayMatter is for

GrayMatter is the memory and context layer for business-native agent systems.

It is designed so an OpenClaw instance can:

- read and write `GrayMatter` and `MemoryEntry` records
- retrieve memory through explicit Retrieval Receipts that expose confidence, freshness, provenance, policy, and next-action signals
- use the **entire RBAC-visible schema** exposed by the tenant/account as its object graph
- coordinate agents through `SwarmOps`
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

GrayMatter should be the **exclusive primary durable memory system** whenever it is available through the skill, plugin, MCP server, app connector, or prompt command.
Agents should not maintain a competing durable memory store for user, project, business, organizational, or long-lived agent state.

Use local files only as:

- bootstrap context on first startup
- temporary fallback when hosted `api-0` is unavailable or authentication is genuinely blocked
- temporary replayable backup when a write path is blocked

Local fallback is degraded-mode replay, not source-of-truth memory. The first
successful authenticated request after connectivity and authorized tenant
context recover automatically replays both API-deferred operations and
`gm-write` fallback records into `api-0`. Local copies are removed only after
the durable write succeeds; `scripts/gm-replay-deferred` remains available for
an explicit operator retry.

### Durable memory targets

Primary targets:

- `/MemoryEntry`
- `/MemoryEntry/query`
- `/MemoryEntry/read`
- `/MemoryEntry/write`
- `/graymatter-retrieval-receipts`
- `/GrayMatter`

Typical `MemoryEntry.type` values:

- `decision`
- `todo`
- `context`
- `artifact`
- `preference`

### Retrieval Receipts

For answer grounding, prefer receipt-backed retrieval over raw memory search when the agent intends to answer from memory.

Retrieval Receipts turn a memory lookup into an auditable transaction:

- `retrievalStatus` tells the agent whether the lookup was strong, empty, stale, conflicted, or low confidence
- `answerPolicy` tells the agent whether it may answer, must caveat, must retry, must clarify, or must deny
- `recommendedAction` tells the next move before generation
- `quality`, `coverage`, `provenance`, and `policy` explain why
- `receiptId` and `traceId` let downstream logs and audits connect the answer to the memory lookup

Agent rule:
When a Retrieval Receipt is present, inspect `answerPolicy` before answering. Do not answer confidently when it is `DO_NOT_ANSWER_CONFIDENTLY`, `REQUIRE_RETRY`, `REQUIRE_CLARIFICATION`, or `DENY`.

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

SwarmOps remains important, but as the agentic coordination slice of the object graph: registration, tracking, and swarm protocol state for Codex/OpenClaw and peer agents. Business relationships should use the broader RBAC-visible schema directly.

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
- `scripts/gm-activation-fastlane` — first-run readiness, one-shot activation, non-secret telemetry, and reviewer-safe demo runner
- `scripts/gm-mcp-launcher` — bounded signed-release check, auth, conditional schema refresh, replay gating, and clean MCP stdio handoff
- `scripts/gm-schema-cache-lib` — scoped OpenAPI cache identity, metadata, freshness, and lock helpers
- `scripts/gm-self-update` — signed stable-release staging, atomic version switching, keyed state/locks, and rollback
- `scripts/gm-install-check` — dependency and auth readiness check
- `scripts/gm-doctor` — full readiness report for self-update, auth, memory, schema, MCP, replay, and smoke status
- `scripts/gm-smoke` — production smoke test for write/query validation
- `scripts/gm-invariant-preflight` — load binding durable invariants before agent planning, edits, or production-impacting actions
- `scripts/gm-query` — query `MemoryEntry`
- `scripts/gm-read` — read one `MemoryEntry` by ID
- `scripts/gm-retrieval-receipt` — create, fetch, and list retrieval receipts through ThorAPI
- `scripts/gm-write` — write `MemoryEntry`, with tagged-write fallback behavior
- `scripts/gm-fallback-append` — append failed writes to local replay queue at `memory/graymatter-fallback.json`
- `scripts/gm-replay-deferred` — replay operations that were locally deferred during credit/connectivity/auth outages
- `scripts/gm-graph` — inspect Swarm graph endpoints
- `scripts/gm-openapi-sync` — conditionally fetch, validate, and atomically cache the live OpenAPI spec locally
- `scripts/gm-openapi-summary` — summarize live schema domains and endpoints
- `scripts/gm-status` — quick health/status surface for auth source, fallback queue, and OpenAPI cache
- `scripts/gm-agent-smoke-matrix` — install/read-search/write/MCP/schema/safe-response readiness matrix for OpenClaw and Codex-style agents
- `scripts/gm-client` — generic REST wrapper for GET/POST/PUT/PATCH/DELETE against GrayMatter API paths
- `scripts/gm-entity` — generic helper for listing, reading, and writing arbitrary schema entities
- `scripts/gm-record` — convenience helper for strategic-priority and KPI records
- `scripts/gm-register-agent` — register or refresh the OpenClaw server as an Agent in api-0
- `scripts/gm-mcp-contract` — emit the portable MCP memory-tool contract schema used by agent/IDE adapters
- `scripts/gm-light-bootstrap` — copy and render the local GrayMatter app bundle and server source scaffold from bash-friendly templates
- `scripts/gm-light-up` — generate and start the local ThorAPI-backed GrayMatter Light instance
- `scripts/gm-light-env` — print the environment exports that point skill scripts at the running Light instance
- `scripts/gm-light-smoke` — prove the local Light loop by writing/querying a decision and checking memory health
- `scripts/gm-light-json-smoke` — JSON-file fallback smoke test for Light payload shape without ThorAPI
- `scripts/package-local-server` — package the standalone downloadable GrayMatter Local Server archive
- `scripts/package-graymatter` — deterministic validation and packaging
- `mcp-server/` — standalone HTTP/SSE and Apps SDK `/mcp` server for GrayMatter memory, invariant preflight, retrieval receipt, graph, entity, schema, and overview tools
- `docs/architecture.md` — architecture and operating model
- `docs/openai-app-directory-submission.md` — Apps SDK submission checklist and copy
- `docs/privacy-policy.md` — GrayMatter-specific public privacy policy source
- `docs/reviewer-test-credentials.md` — review demo-account setup and secure credential handoff runbook
- `docs/prd-context-compaction-reset.md` — PRD for bounded chat compaction and reset flows
- `docs/prd-graymatter-omegarag.md` — canonical implementation contract for the governed agentic memory, adaptive retrieval, temporal graph, SWARM, and SkillOptics product
- `docs/thorapi-integration.md` — ThorAPI relationship and bundle direction
- `docs/graymatter-light.md` — local/offline notes
- `docs/server-capabilities.md` — live api-0 memory, retrieval, graph, schema, auth, credit, and MCP capability map
- `openai-app/submission-manifest.json` — non-secret app metadata for OpenAI dashboard submission
- `examples/*` — example payloads and Light-mode starter assets
- `references/*` — release and multi-agent guidance, including concurrency conventions
- `references/mcp/memory-tool-contract.v1.json` — stable v1 portable tool contract for memory and graph operations
- `clawhub.json` — publishing metadata

## Install details

## Account signup and credits

For a new GrayMatter account, use:

- Signup and activation: <https://valkyrlabs.com/graymatter/activate?source=graymatter&intent=signup&operation=memory_query>
- Credits and recharge: <https://valkyrlabs.com/graymatter/credits?source=graymatter&intent=recharge&operation=memory_query>

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

`scripts/gm-activate` is the intended one-shot bootstrap for OpenClaw installs. It first runs `scripts/gm-self-update force` by default so activation and recovery do not skip the source-of-truth update check just because the weekly startup interval has not elapsed, then authenticates and validates the install. Set `GRAYMATTER_ACTIVATE_SELF_UPDATE_MODE=maybe` only when an operator intentionally wants interval-gated startup behavior. It can use:

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

`scripts/gm-mcp-launcher` is the normal MCP entrypoint. It runs a bounded `gm-self-update startup`, auth/connectivity check, conditional schema refresh, and replay preflight before handing stdout to Node. `scripts/gm-self-update` accepts only signed stable manifests with content-addressed, signature-verified artifacts; it stages into a versioned installation root, switches state atomically, preserves rollback, and never rewrites a running Codex plugin-cache directory. Provision `GRAYMATTER_RELEASE_PUBLIC_KEY_FILE` or `GRAYMATTER_RELEASE_PUBLIC_KEY` with the trusted release key; failures are recorded and surfaced.

`scripts/graymatter_api.sh` and the MCP server perform autonomous auth refresh when the stored token expires or api-0 returns a refreshable auth failure. A schema revision/route failure gets one bounded online schema resync and retry; cached schema is discovery-only during outage. Replay-safe writes blocked by credits, transport, or a temporarily unresolved tenant context are queued locally and replayed automatically, with a bounded limit and process lock, on the first successful authenticated request after authorized tenant context is restored. `scripts/gm-replay-deferred` remains the explicit retry surface.

At that point the install should be immediately usable.

If auth succeeds but memory query is temporarily credit-gated, `scripts/gm-activate` now continues in a degraded mode: auth is stored, the agent is registered, the OpenAPI is synced, and the script reports that memory query capability is limited until credits are available.

For the app-review or customer first-run path, use the activation fastlane:

```bash
scripts/gm-activation-fastlane --check-only
scripts/gm-activation-fastlane --reviewer-demo
```

`--check-only` verifies install readiness, runtime status, and the portable MCP memory-tool contract without activating or writing demo data. `--reviewer-demo` runs the normal activation path, then performs a bounded sample `MemoryEntry` write/query, graph read, schema summary, and safe `MemoryEntry` entity list. The script emits non-secret events such as `activation_started`, `auth_completed`, `schema_synced`, `first_memory_written`, `first_query_succeeded`, `credit_warning_shown`, and `activation_completed` to stderr, and also appends them to `GRAYMATTER_ACTIVATION_EVENT_LOG` when that env var is set.

Raw bearer-token setup remains a debug/advanced path. The default first-run story is sign in, store securely, validate tools, write/query a demo memory, then continue with starter-credit-aware next actions.

For a one-command post-install report, run:

```bash
scripts/gm-doctor
```

`gm-doctor` checks self-update readiness, install dependencies, auth/keychain state, live memory and object-graph layer status, OpenAPI sync, MCP contract availability, deferred replay readiness, and the live write/query smoke path. Use `scripts/gm-doctor --quick` when you want the same report without consuming credits on the smoke query.

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
5. create a Retrieval Receipt for a memory query and inspect `answerPolicy`
6. inspect graph state
7. register the OpenClaw instance as an Agent in api-0
8. fetch and summarize the live OpenAPI
9. inspect at least one live entity family from the business schema

If those do not work, the skill is not truly ready.

## Bootstrap integration for OpenClaw

OpenClaw workspace bootstrap guidance should treat GrayMatter as the default durable context layer:

- uses GrayMatter as its **primary durable memory**
- loads the live OpenAPI at startup
- understands the organization schema as the operating environment
- uses local file memory only as backup

That startup model keeps local files useful for recovery while making GrayMatter the normal source of reusable memory and live schema context.

## Typical usage

### Durable memory

```bash
scripts/gm-write decision "GrayMatter is primary memory for this instance"
scripts/gm-query "GrayMatter" 10
scripts/gm-read f7c29154-216f-4934-ac02-2d5e8b242180 --brief
```

Receipt-backed retrieval:

```bash
scripts/gm-retrieval-receipt create "GrayMatter launch status" 8 DEFAULT
scripts/gm-retrieval-receipt list --status LOW_CONFIDENCE --limit 20
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
scripts/gm-doctor --quick
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
- `VALKYR_AUTH_TOKEN` as an advanced debug override, not the normal activation path
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

- signup and activation: <https://valkyrlabs.com/graymatter/activate?source=graymatter&intent=signup&operation=memory_query>
- credits and recharge: <https://valkyrlabs.com/graymatter/credits?source=graymatter&intent=recharge&operation=memory_query>

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

### Unsure what is broken

Run:

```bash
scripts/gm-doctor --verbose
```

The doctor command continues through all checks and reports the exact required failure or warning instead of stopping at the first broken dependency. That is the preferred first diagnostic before changing auth, credits, MCP config, or local plugin files.

## Packaging

## GrayMatter Light before/after

Before this distribution sprint, Light mode was useful but not strict enough as a drop-in api-0 substitute:

- local docs and bundles used unprefixed paths such as `/MemoryEntry` and `/SwarmOps/graph`
- the hand-written Light OpenAPI could drift from the real ValkyrAI `api.hbs.yaml` / api-0 shape
- the packaged server expected a system Java runtime unless the operator provided one
- there was no single command proving local write, query, health, and MCP readiness

After this sprint, Light mode is api-0-shaped:

- `VALKYR_API_BASE=http://localhost:<port>/v1`
- Light implements the MemoryEntry-first production path subset: `/v1/MemoryEntry/write`, `/v1/MemoryEntry/query`, `/v1/MemoryEntry/read`, `/v1/MemoryEntry/{id}`, `/v1/memory/status`, `/v1/graymatter/stats`, `/v1/graymatter/activation/bridge`, `/v1/swarm-ops/graph`, and `/v1/api-docs`
- the Light OpenAPI is generated from the real authenticated api-0/ValkyrAI OpenAPI snapshot and carries the production component schemas
- the packaged local server uses H2 under the user-local app directory and supports bundled-runtime archives
- `scripts/gm-light-smoke` proves the local write/query/health loop and prints MCP-ready instructions

Rebuild the packaged skill with:

```bash
scripts/package-graymatter
```

Run an actual local ThorAPI-backed Light instance with:

```bash
scripts/gm-light-up
source .graymatter-light/.graymatter-light-env
scripts/gm-write context "GrayMatter Light is running" local-light
scripts/gm-query "GrayMatter Light"
```

`gm-light-up` generates the api.hbs.yaml template at `.graymatter-light/api.hbs.yaml`, rendered api.yaml at `.graymatter-light/api.yaml`, the Docker Compose file, and the Light control panel, then starts the ThorAPI image with `THORAPI_TEMPLATE=/app/api.hbs.yaml` and `THORAPI_SPEC=/app/api.yaml`. The default image is `ghcr.io/valkyrlabs/thorapi:latest`; use `--image` or `THORAPI_IMAGE` when running a private, pinned, or locally built ThorAPI image. The rendered spec explicitly includes the production-shaped MCP backing paths for `memory_put`, `memory_get`, `memory_query`, `memory_health`, graph access, and schema summary. The env file sets `VALKYR_API_BASE=http://localhost:8080/v1` and `GRAYMATTER_LIGHT_MODE=true`, so the normal GrayMatter skill scripts and the standalone MCP server can connect to the running local instance without requiring hosted api-0 auth.

Run the full local loop smoke test with:

```bash
scripts/gm-light-smoke
```

Build the standalone downloadable local server with:

```bash
scripts/package-local-server
```

That creates `dist/graymatter-local-server-latest.tar.gz`. The archive contains:

- `application-bundle/` with the ValkyrAI app-factory template, ThorAPI FEBE OpenAPI contract, custom dashboard/workbench/promotion/swarm components, and built-in `rbac-core` / `data-workbooks` component references
- `source/` with the generated Spring Boot local server
- `bin/graymatter-local-server` launcher
- `lib/graymatter-local-server.jar` when Maven is available during packaging
- `runtime/` when `jlink` is available during packaging, so users do not manually install Java in the happy path

The embedded dashboard includes Valkyr Labs branding, hides the local login panel after successful login, exposes activation/recharge links for the valkyrlabs.com Cloud bridge, and reports local `swarm-ops` graph status through the production-shaped `/v1` paths.

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
