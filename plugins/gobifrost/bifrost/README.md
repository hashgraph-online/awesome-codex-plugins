# Bifrost Integrations

**Open-source automation platform for Integration Services** - Built to democratize best-in-class tooling before venture capital gets the chance to own something we're all incredibly passionate about.

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![CodeQL](https://github.com/gobifrost/bifrost/actions/workflows/codeql.yml/badge.svg)](https://github.com/gobifrost/bifrost/actions/workflows/codeql.yml)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/gobifrost/bifrost/badge)](https://securityscorecards.dev/viewer/?uri=github.com/gobifrost/bifrost)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/12665/badge)](https://www.bestpractices.dev/projects/12665)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)

---

## Table of Contents

-   [What is Bifrost Integrations?](#what-is-bifrost-integrations)
-   [Key Features](#key-features)
-   [Quick Start](#quick-start)
-   [Documentation](#documentation)
-   [Security & Verification](#security--verification)
-   [Usage Reporting](#usage-reporting)
-   [Contributing](#contributing)
-   [License](#license)

---

## What is Bifrost Integrations?

Bifrost Integrations is an open-source automation platform designed to democratize best-in-class tooling for the emerging Integration Services industry - **before venture capital gets the chance to own something we're all incredibly passionate about: solving problems with automation**.

Built by someone with nearly 20 years of MSP experience and a deep passion for scaling solutions for the industry and its customers, this platform addresses a fundamental gap in the market. Just as early PSA and RMM tools transformed Managed Services, the Integration Services industry needs purpose-built tooling that truly scales automation. Existing RPA platforms are great for rapid development and provide helpful abstractions like OAuth, storage, and monitoring, but **they cannot and will not keep pace with AI-powered development** and have always been constrained by limitations that traditional programming languages do not have.

Bifrost Integrations removes those limitations while preserving the light management layer that makes RPA tools valuable - abstracting OAuth workflows, monitoring, configuration, and secret management. It's architected with multi-tenancy at its core, enabling you to scale your Integration Services business without duplicating work across customers. **This is not another RPA tool trying to be everything to everyone**; it's a platform designed specifically to help you build scalable automation businesses without the vendor lock-in.

### What You Can Do with Bifrost Integrations

**Develop with Your Favorite Tools**

-   Use VS Code, Claude Code, and Git for version control
-   Build with Python and modern development workflows
-   Test locally before deploying to production

**Build Reusable Integrations**

-   Create integration modules for common platforms (NinjaOne, HaloPSA, Pax8, Microsoft CSP)
-   Abstract authentication, pagination, and API complexity
-   Share functionality across all your workflows

**Centralized Connection Management**

-   Automated OAuth refresh flows
-   Key/value configuration storage per organization
-   Secure secrets management

**Dynamic Forms and Workflows**

-   Create flexible forms for you and your customers
-   Build context-aware workflows that adapt based on organization and user
-   Generate form inputs programmatically from data providers

**Multi-Tenant Architecture**

-   Scope functionality globally or to specific organizations
-   Deliver value to customers without code duplication or redeployment
-   Complete data isolation between tenants

### Why Bifrost Integrations Exists

Traditional RPA tools lower the barrier to entry but fall short when you need the full power of a programming language, version control, modern development practices, and AI-assisted workflows. Meanwhile, no one is building a platform truly designed to scale automation in the way early PSA and RMM tools scaled Managed Services. In my opinion, these tools are all good at different things, but they lack the flexibility to deliver solutions for both you and your customers.

Bifrost Integrations bridges this gap by giving you the power and flexibility of code with the convenience of RPA-style abstractions - all in an open-source package that you control. **It's built to ensure the next chapter of Integration Services doesn't get ravaged by venture capitalists who prioritize extraction over value creation**.

### For the Non-Developer

With AI coding tools, proper instructions, a thriving community, and training, it's never been easier to build powerful automations. Traditional RPA tools still require you to understand programming primitives like loops, variables, and conditional logic - they had their own syntax you needed to learn. While Bifrost Integrations may require a slightly higher initial investment to get started, the combination of AI-assisted development and a platform that abstracts the dangerous complexities (authentication, secrets management, API security) means **the ceiling is dramatically higher**.

AI tools like Claude Code, GitHub Copilot, and GPT Codex can help you:

-   Write workflows from natural language descriptions
-   Debug errors and explain what code is doing
-   Suggest improvements and optimizations
-   Generate boilerplate code for common patterns

The platform handles the hard parts - OAuth flows, credential encryption, multi-tenant isolation, and API authentication - so you can focus on solving business problems. With the right guidance and AI assistance, you can build automations that would have required a full development team just a few years ago, **enabling limitless possibilities for your Integration Services business**.

### Migrating From Rewst

The Bifrost plugin includes [`bifrost:rewst-migration`](.claude/skills/bifrost-rewst-migration/SKILL.md)
for extracting Rewst definitions, preparing a migration plan, and verifying
integrations, workflows, forms, apps, and cutovers. Start with:

> Use bifrost:rewst-migration to inspect my Rewst setup, collect the remaining
> decisions up front, and prepare an execution-ready migration plan.

The skill includes a private GraphQL extraction helper and a fresh plan template.
Users provide their own authorized session and current read queries; credentials,
exports, and migration progress stay outside the distributed package. Private API
schemas can change, so extraction reports its actual coverage and missing data.

---

## Key Features

-   **Multi-Tenant Architecture** - Complete data isolation per organization
-   **OAuth Management** - Automated token refresh and credential storage
-   **Secrets Management** - Encrypted secrets with Fernet encryption
-   **Dynamic Workflows** - Python-based with full language capabilities
-   **Reusable Integrations** - Build once, use across all customers
-   **AI-Assisted Development** - Built for modern AI coding workflows
-   **Version Control** - Git-based workflow management
-   **Hot Reload** - Workflows and forms reload automatically on file changes
-   **Self-Hostable** - Run anywhere with Docker Compose

---

## Quick Start

### Prerequisites

-   Docker and Docker Compose
-   Git

### Running with Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/gobifrost/bifrost.git
cd bifrost

# Run setup (creates .env with secure random secrets)
./setup.sh

# Start all services
docker compose up
```

This starts:
-   **Client** (React) - http://localhost:3000
-   **API** (FastAPI) - proxied through client
-   **PostgreSQL** - Database
-   **Redis** - Caching and sessions
-   **Scheduler and Worker** - Executors that run workflows and agent runs

**Access the Platform:**

-   **Client UI**: http://localhost:3000
-   **API Docs (Swagger)**: http://localhost:3000/api/docs
-   **API Docs (ReDoc)**: http://localhost:3000/api/redoc

### Upgrading

Bifrost no longer uses RabbitMQ. If your `docker-compose.yml` predates this,
leave its `rabbitmq` service and `BIFROST_RABBITMQ_URL` settings in place for the
first start after upgrading: the API moves any runs an earlier release left
queued there into PostgreSQL, then disconnects. Once the API logs
`Drained work queued by an earlier release`, clean up: delete the `rabbitmq` service, its
`depends_on` entries, the `BIFROST_RABBITMQ_URL` lines and the `rabbitmq_data`
volume from the compose file, remove `RABBITMQ_PASSWORD` from `.env`, then run:

```bash
docker compose up -d --remove-orphans
docker volume rm bifrost_rabbitmq_data
```

The API records the drain once nothing is left queued, and later starts no
longer connect (each start warns that `BIFROST_RABBITMQ_URL` is no longer used
until it is removed). A rollback to a release that queues to RabbitMQ needs
that record deleted, so the next upgrade drains again:
`DELETE FROM system_configs WHERE category = 'runtime' AND key = 'legacy_broker_drained';`

---

## Local Development

### Starting the dev stack

The full stack runs in Docker with hot reload enabled for both API and client:

```bash
./debug.sh              # Start, print the URL, then stream logs until exit/Ctrl+C
```

This launches PostgreSQL, Redis, SeaweedFS for S3-compatible object storage, the API, the client, the scheduler, and workers. `./debug.sh` is the foreground owner: it removes its containers, networks, volumes, and locally generated debug images on normal exit, Ctrl+C (`INT`), `TERM`, `HUP`, or an essential-service stop; Docker's shared build cache remains reusable. Use `./debug.sh down` from another terminal for explicit cleanup. Access the app at the `Open:` URL it prints — Vite proxies `/api/*` to the API container, so you don't hit the API on a separate port.

Changes to files in `api/src/`, `api/shared/`, and `client/src/` automatically reload — **do not restart containers for code changes.**

```bash
# View logs
docker compose logs -f api
docker compose logs -f client
```

**VS Code debugging:**

```bash
ENABLE_DEBUG=true ./debug.sh
```

Attach VS Code to port 5678. The API waits for the debugger before starting.

For the full container-management contract (when to restart what, hot-reload rules, type-generation workflow), see [`CLAUDE.md` → Development Environment](./CLAUDE.md#development-environment-critical---read-first).

### Running Tests

The test stack runs in Docker and is separate from your dev stack. Every stateful test command boots its own per-worktree stack and removes containers, networks, volumes, and its per-worktree image tag when the command finishes, fails, or is interrupted; Docker's shared build cache remains reusable. `ci`, `pre-pr`, and `pr-preflight` share one stack for their internal stages, then remove it at the end.

```bash
# Backend tests (each command owns its stack)
./test.sh                                          # Unit tests (fast default)
./test.sh e2e                                      # Backend e2e
./test.sh all                                      # All backend tests, including slow tests
./test.sh tests/unit/test_foo.py::test_bar -v      # Passthrough to pytest

# Client tests
./test.sh client unit                              # Vitest (no stack needed)
./test.sh client e2e                               # Playwright; owns its stack
./test.sh client smoke                             # Critical zero-retry Playwright suite
./test.sh client nightly                           # Full product Playwright suite
./test.sh client docs                              # Documentation screenshot capture

# API type check + lint (one-off resources only; no full stack)
./test.sh quality api

# Broad one-shot commands share one stack internally
./test.sh pre-pr                                 # Optional: reproduce the merge gate locally
./test.sh pr-preflight                            # Local PR gate
./test.sh ci                                     # All backend + full browser suites

# Diagnostics/manual cleanup only
./test.sh stack status
./test.sh stack down
```

Parallel worktrees each get their own isolated stack, so you can run tests in several worktrees simultaneously without conflict.

For test authoring conventions, fixture layout, and debugging tips, see [`CLAUDE.md`](./CLAUDE.md#testing--quality).

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   FastAPI   │────▶│ PostgreSQL  │
│   (React)   │     │    (API)    │     │  (Database) │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              ┌─────────┐   ┌─────────────┐
              │  Redis  │   │  Executors  │
              │ (Cache) │   │ (scheduler, │
              └─────────┘   │   worker)   │
                            └─────────────┘
```

-   **FastAPI** - Async Python API with automatic OpenAPI documentation
-   **PostgreSQL** - Primary data store with SQLAlchemy ORM
-   **Redis** - Session storage and caching
-   **Executors** - Scheduler and worker containers that claim workflow and agent runs from PostgreSQL
-   **React** - Modern frontend with TypeScript

---

## Documentation

For detailed documentation on architecture, development, deployment, and usage:

-   **API Documentation**: http://localhost:8000/docs (when running)
-   **Frontend Repository**: Included in `client/` directory

---

## Security & Verification

### Zero Trust Automation

Zero Trust Automation checks each run against the run user's current roles and
organization reach. A run identity records who acts. Workflows use **Full
Access** or **Declared Permissions** only within that reach. Full Access remains
the default. See [Zero Trust Automation](docs/runbooks/zero-trust-automation.md)
for access modes, Solution approvals, and moving to narrower permissions.

### Verify Release Artifacts

Bifrost release artifacts are signed with [Sigstore](https://www.sigstore.dev/) using GitHub's keyless OIDC signing. You can verify any image or release pulled from this repo:

**Verify a Docker image:**

```bash
cosign verify ghcr.io/gobifrost/bifrost-api:TAG \
  --certificate-identity-regexp "https://github.com/gobifrost/bifrost/.*" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com
```

(Same form for `ghcr.io/gobifrost/bifrost-client`.)

**Inspect SLSA build provenance:**

```bash
gh attestation verify ghcr.io/gobifrost/bifrost-api:TAG --owner gobifrost
```

**Verify a source tarball** (attached to GitHub Releases):

```bash
cosign verify-blob \
  --bundle bifrost-VERSION-source.tar.gz.sigstore \
  --certificate-identity-regexp "https://github.com/gobifrost/bifrost/.*" \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  bifrost-VERSION-source.tar.gz
```

Install cosign: https://docs.sigstore.dev/cosign/system_config/installation/

---

## Usage Reporting

Production installations report a random installation ID, version, and daily
workflow and agent run totals to `https://reports.gobifrost.com/usage` by default.
Development, testing, and debug instances do not report. Set
`BIFROST_USAGE_REPORTING_ENABLED=false` to exclude staging or cloned instances,
or to permanently opt out. See [Usage Reporting](docs/runbooks/usage-reporting.md)
for the complete payload, schedule, and privacy details.

## Contributing

This is intended to be a community-driven project built to ensure the Integration Services industry has the tools it needs without vendor lock-in or extractive pricing. However for the time being, while I work out the kinks, contributions and issues will be closed. Stay tuned!

## License

This project is licensed under the AGPL License - see the [LICENSE](LICENSE) file for details.

The [Cloudflare MIT notice](LICENSES/cloudflare-codemode-MIT.txt) covers the adapted [capability-search ranking code](api/src/services/capabilities/search.py) used by Automatic agents and MCP discovery. Its Cloudflare copyright attribution is retained from the upstream code and does not identify Cloudflare as the copyright owner of Bifrost as a whole.

**Why AGPL?** To ensure this platform remains open and available to everyone. If you modify and deploy Bifrost, you must share those modifications with the community. This prevents proprietary forks and ensures improvements benefit everyone.

---

## Why This Matters

In my opinion, the MSP industry is at a critical juncture. We've all watched as venture capital transformed software markets and tools we use and love (loved?) - not always for the better. I believe the next frontier for MSP is in the Integration Services industry where we focus on using the automation skills we've developed over the last couple of decades and build value for new and existing customers.

**This is our chance to own the tools we build our businesses on.**
