---
name: agentry
description: Use when the user asks to install, set up, or use Agentry; add analytics, logging, error monitoring, deploy attribution, product telemetry, or production debugging; investigate a production error or case; or answer product/reliability questions from Agentry data.
---

# Agentry - agent-native analytics and logging

Agentry is agent-native analytics and logging for coding agents. It covers
product analytics, error logging, and deploy attribution through one HTTP API so
agents can answer what users did, what broke, and what changed.

Use this skill for Agentry install/setup, product analytics, logging, error
monitoring, deploy tracking, production debugging, and day-to-day Agentry reads.
Do not treat this file as an API reference; it is a compact entry point to the
live docs.

## What to fetch next

- Installing or setting up Agentry: fetch <https://agentry.sh/install.md>.
- Answering product, reliability, case, analytics, or deploy questions after
  setup: fetch <https://agentry.sh/agentry.md>.
- Discovering the API surface and 3 write / 3 read model: start at
  <https://api.agentry.sh/>.
- Checking exact request/response shapes: fetch
  <https://api.agentry.sh/v1/openapi.json>; filter with `?flow=`, `?tag=`,
  `?path=&method=`, or `?index=true`.
- Installing or refreshing future-session adapters: fetch
  <https://api.agentry.sh/adapters> and write every adapter that matches the
  detected agent harness.

Use a custom User-Agent header for non-browser direct HTTP calls; default
clients such as Python-urllib can be blocked. Browser fetch uses the browser's
own User-Agent and cannot set this header manually.

## Install workflow

When installing Agentry, fetch <https://agentry.sh/install.md> and follow that
flow. Start from the repo's important business question and funnel/business
logic flow. Let `POST /v1/install/plan` derive the events, properties, error
surfaces, and deploy proof from the actual codebase. Do not hand-write a
generic event catalog.

Before claiming success, save the signal map and implementation report, then
verify that the approved telemetry is flowing.

## Mental model

Agentry has three write paths and three read concepts.

Write app runtime data with `AGENTRY_DSN`:
- `POST /v1/logs/` for errors, exceptions, and operational failures.
- `POST /v1/analytics/` for product, user, funnel, and business events.

Write deploy attribution with the same `AGENTRY_DSN` only from CI/provider
post-deploy automation after a successful release:
- `POST /v1/deploys/` for release attribution.

Read with `AGENTRY_API_KEY`:
- **Cases:** what broke. Start with `GET /v1/projects/:project_id/cases`, then
  `GET /v1/cases/:case_id`.
- **Analytics:** what users did. Start from the saved signal map, latest verify
  report, answer contracts, event names, and property keys; then use query
  blueprints for common reads or `POST /v1/projects/:project_id/analytics/query`
  for custom HogQL.
  Table-like Agentry query reads return object-shaped `rows`; do not read
  PostHog-style `results` from agent-facing endpoints.
- **Deploys:** what changed. Use `GET /v1/projects/:project_id/deploys`.

Query blueprints, event names, public queries, health, and next-steps are helpers around
those three read concepts. Public-query URLs and dashboards are optional output
surfaces, not proof that the underlying product question is answerable.

For day-to-day questions, read the saved signal map, latest verify report,
answer contracts, event names, and property keys before choosing a query
blueprint or custom HogQL. If the needed event/property is missing, say what is
missing and wire or trigger that product flow instead of inventing a metric.

## Auth

Read `AGENTRY_API_KEY` from env or `~/.agentry/credentials.json`; read
`project_id` from `AGENTRY_PROJECT_ID` or committed `.agentry/config.json`.
With no API key, start the device flow with `POST /v1/auth/device`. Runtime ingest
uses `AGENTRY_DSN`.

## Source of truth

Do not rely on this installed file for endpoint details. Fetch the live docs
above; they are authoritative and can update independently of adapters.

## Public distribution

- Website: <https://agentry.sh/>.
- Live skill: <https://agentry.sh/skill/agentry/SKILL.md>.
- Skill repository: <https://github.com/fr33dr4g0n/agentry-skill>.
- MCP package: <https://www.npmjs.com/package/@agentrysh/mcp>.
- MCP repository: <https://github.com/fr33dr4g0n/agentry-public>.
- Codex marketplace catalog: <https://github.com/fr33dr4g0n/agentry-public/blob/main/.agents/plugins/marketplace.json>.
- Claude marketplace catalog: <https://github.com/fr33dr4g0n/agentry-public/blob/main/.claude-plugin/marketplace.json>.
- Adapter manifest: <https://api.agentry.sh/adapters>.

## Adapter coverage

The same skill and adapter manifest support Codex, Claude Code, Cursor, VS Code
and Visual Studio with GitHub Copilot, GitHub Copilot coding agent, Devin
Desktop/Windsurf Cascade, Cline, Roo Code, Continue, Zed, Gemini CLI, Aider,
OpenCode, ChatGPT custom GPT Actions, generic MCP clients, and AGENTS.md-aware
agents. The AGENTS.md adapter also covers compatible agents such as Jules,
Factory, Amp, goose, Warp, JetBrains Junie, Augment Code, Kilo Code, Phoenix,
Semgrep, Ona, and UiPath coded agents.
