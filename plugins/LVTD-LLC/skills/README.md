<img src="assets/app-icon.png" alt="LVTD fire heart logo" width="96" height="96">

# LVTD Skills

Reusable agent skills for LVTD projects, Django SaaS workflows, and agent-first software development.

This repository is intentionally simple: every skill lives in `skills/<skill-name>/SKILL.md`, with small validation and publishing scripts around that catalog. That shape works well for agents that read skill folders directly, and it is easy for external indexes like skills.sh to consume.

## Skills

| Skill | Use when |
| --- | --- |
| [`alpinejs-django`](skills/alpinejs-django/SKILL.md) | Adding, changing, or debugging Alpine.js behavior in Django templates, especially when HTMX partial swaps are also present. |
| [`calibredb`](skills/calibredb/SKILL.md) | Managing and querying Calibre libraries with the calibredb CLI, including metadata, formats, exports, checks, and full-text search. |
| [`cookiecutter`](skills/cookiecutter/SKILL.md) | Adding, changing, testing, or debugging Cookiecutter templates, including Jinja rendering, hooks, option cleanup, and generated-project validation. |
| [`django-htmx`](skills/django-htmx/SKILL.md) | Building and reviewing HTMX interactions in Django server-rendered apps, including partial responses, headers, swaps, triggers, forms, and tests. |
| [`django-q2`](skills/django-q2/SKILL.md) | Adding, changing, testing, or debugging Django Q2 background jobs, schedules, workers, and broker configuration. |
| [`fastmcp-django`](skills/fastmcp-django/SKILL.md) | Adding, changing, deploying, testing, or debugging FastMCP MCP servers in existing Django apps, including ASGI mounting, ORM access, auth, and Streamable HTTP deployment. |
| [`make-product-viral`](skills/make-product-viral/SKILL.md) | Making a product, landing page, pricing page, launch page, free tool, or social preview easier to understand, buy, remember, and share. |
| [`rust-api-test-harness`](skills/rust-api-test-harness/SKILL.md) | Adding, changing, testing, or debugging Rust HTTP APIs with black-box integration tests, random-port app startup, state isolation, mocks, and CI-ready cargo checks. |
| [`rust-deployable-service`](skills/rust-deployable-service/SKILL.md) | Preparing, containerizing, configuring, testing, or reviewing Rust services for deployment, including Docker, runtime config, secrets, health checks, SQLx offline builds, and startup validation. |
| [`rust-domain-boundaries`](skills/rust-domain-boundaries/SKILL.md) | Modeling, validating, refactoring, or reviewing Rust service domain boundaries with newtypes, parse-don't-validate constructors, request DTO boundaries, and property tests. |
| [`rust-error-observability`](skills/rust-error-observability/SKILL.md) | Adding, changing, debugging, or reviewing Rust service error handling and observability, including typed errors, HTTP response adapters, tracing spans, and redaction. |
| [`rust-idempotent-workflows`](skills/rust-idempotent-workflows/SKILL.md) | Designing, implementing, testing, or debugging Rust service workflows that must survive retries, duplicate requests, crashes, concurrency, queues, and side effects. |
| [`rust-service-security`](skills/rust-service-security/SKILL.md) | Adding, changing, testing, or reviewing security-sensitive Rust web service behavior, including login, password hashing, session cookies, route protection, and auth middleware. |
| [`rust-sqlx-postgres-service`](skills/rust-sqlx-postgres-service/SKILL.md) | Adding, changing, testing, or reviewing Postgres persistence in Rust services using SQLx migrations, compile-time checked queries, pools, transactions, and integration tests. |

## Repository Layout

```text
skills/
  <skill-name>/
    SKILL.md
docs/
  installation.md
scripts/
  build-marketplaces.mjs
  build-registry.mjs
  skill-utils.mjs
  validate-marketplaces.mjs
  validate-skills.mjs
tests/
  validate-skills.mjs
```

## Install A Skill Directly

Use the `skills` CLI to install from this repository:

```bash
npx skills add LVTD-LLC/skills --skill django-htmx
```

Common targets:

```bash
# Codex global skills
npx skills add LVTD-LLC/skills --skill django-htmx -g -a codex

# Claude Code global skills
npx skills add LVTD-LLC/skills --skill django-htmx -g -a claude-code

# OpenClaw global skills
npx skills add LVTD-LLC/skills --skill django-htmx -g -a openclaw

# Install from a local checkout
npx skills add . --skill django-htmx
```

More details are in [`docs/installation.md`](docs/installation.md).

## Marketplace Install

Add the marketplace in Claude Code:

```text
/plugin marketplace add LVTD-LLC/skills
/plugin install django@lvtd-skills
/reload-plugins
```

Claude Code exposes the bundled skills as `/django:django-htmx`,
`/django:django-q2`, and the other skills in that plugin.

Add the marketplace in Codex:

```bash
codex plugin marketplace add LVTD-LLC/skills
codex plugin add django@lvtd-skills
```

Codex exposes the bundled skills as `$django:django-htmx`,
`$django:django-q2`, and the other skills in that plugin.

This repository ships the marketplace files directly:

```text
.claude-plugin/marketplace.json
.agents/plugins/marketplace.json
plugins/<plugin-name>/
```

The plugin skill folders are generated copies of `skills/<skill-name>/`, so
Git-backed marketplace installs have real `SKILL.md` files while the canonical
source remains under `skills/`. Do not edit generated plugin copies directly.

Refresh generated marketplace artifacts during development:

```bash
npm run build
```

Generated marketplace plugin IDs:

- `cookiecutter`
- `django`
- `nonfiction-book-writing`
- `rust`

Marketplace plugins group related skills. Direct installs through the `skills`
CLI still use the canonical skill directory names.

## Marketplace Strategy

See [`docs/marketplace-strategy.md`](docs/marketplace-strategy.md) for the
research-backed plan to publish this catalog across Codex, Claude Code,
OpenClaw, and other Agent Skills-compatible clients.

## Development

New skills should follow [`docs/adding-skills.md`](docs/adding-skills.md).

Validate source skills only:

```bash
npm run validate
```

Build the machine-readable registry and refresh committed marketplace artifacts:

```bash
npm run build
```

The registry is written to `dist/registry.json`. Marketplace artifacts are
written to `.claude-plugin/`, `.agents/plugins/`, and `plugins/`.

Validate generated marketplace artifacts:

```bash
npm run validate:marketplaces
```

Run the full local/CI check before opening a PR:

```bash
npm run check
```

## Publishing

CI validates every push and pull request. Merging to `main` runs the release
workflow, which chooses the next unused catalog version, rebuilds marketplace
artifacts, commits any generated release updates, creates a `v*` tag, uploads a
`skills-catalog` artifact, and publishes a GitHub release.

The catalog version in `package.json` is also the generated marketplace plugin
version, so Codex installs use a new plugin cache path for every release. If you
need a non-patch release, update `package.json` before merging; otherwise the
workflow bumps patch automatically when the current version is already tagged.

Manual `v*` tags still run the publish workflow as a fallback.
