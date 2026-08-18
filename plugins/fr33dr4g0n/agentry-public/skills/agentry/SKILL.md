---
name: agentry
description: Use for Agentry setup or use; analytics, logging, error monitoring, deploy attribution, telemetry, production investigation, or agentic automation.
---

# Agentry

Agentry provides an HTTP API for agents: errors, analytics, and deploy attribution. Docs/filtered OpenAPI are authoritative.

Route by task:

- Install or change telemetry: https://agentry.sh/install.md
- Exact onboarding schema: https://api.agentry.sh/v1/openapi.json?flow=onboarding
- Daily product/reliability questions: https://agentry.sh/agentry.md
- Product discovery: https://api.agentry.sh/
- Exact payloads: https://api.agentry.sh/v1/openapi.json?index=true; filter with `?flow=<name>`, `?tag=<name>`, or `?path=<encoded-path>&method=<method>`.
- Automations: https://api.agentry.sh/v1/docs/automation, https://api.agentry.sh/v1/openapi.json?flow=automation, and immutable versioned https://api.agentry.sh/v1/automation-playbooks
- Refresh agent adapter pointers: https://api.agentry.sh/adapters

## First installation

Read `/install.md` completely. It gives the product context and five-stage overview. Deeply inspect the repository before choosing telemetry: map the actor, entry, every material durable milestone, business result, impactful failure surfaces, and real deploy boundary. Event names and journey length are project-specific.

Show the exact source-backed plan and hash to the human before editing or placing credentials. After it is saved, read current onboarding state immediately before every onboarding state-changing POST. Execute only `next_action.instruction` and its ordered checklist, then call its exact operation. Installation ends only at `status: "verified"`, `installation_complete: true`, and `next_action: null`.

Instrument approved product outcomes after success, approved failures at their owning boundary, and deploy attribution only after provider success. Preserve existing telemetry. Browser analytics centrally add available safe page/referrer, language, browser/OS/device, viewport/screen, and UTM context without URL query or fragment data.

Before plan submission, use a fresh read-only reviewer or fresh context to try to falsify the business flow, alternate owners, indirect state writes, exact properties, failures, privacy, credential scope, and deploy ordering. Resolve every material blocker before saving the plan. Telemetry-derived state is observational: do not use it to change existing product queues, webhooks, notifications, retries, responses, or payloads.

Trace the effective runtime environment across shared service configuration, migrations, builds, and CI. Browser/server credentials belong only at their approved runtime boundary; CI, runner, and private credentials never belong in application or Compose service environments.

Keep source snapshots, plans, proof markers, receipts, and credentials outside the repo. Server verification attests marker-scoped rows plus reviewed committed/deployed source identity; it cannot infer a physical click or external actor, so the installer must exercise the source-reviewed shipped product paths.

Credentials are non-interchangeable:

- `AGENTRY_PUBLIC_API_KEY` (`agentry_pk_`): browser/client analytics and errors.
- `AGENTRY_SERVER_API_KEY` (`agentry_server_`): trusted app-server analytics and logs.
- `AGENTRY_CI_API_KEY` (`agentry_ci_`): deploys, sourcemaps, and CI proof.
- `AGENTRY_RUNNER_API_KEY` (`agentry_runner_`): exactly one automation.
- `AGENTRY_PRIVATE_API_KEY` (`agentry_sk_`): interactive owner/member only.

An owner key is never a scheduler credential. An unattended scheduler gets only its automation-scoped runner key. Do not emit deploys from browser, app startup, request handlers, or cron routes. Keep secrets out of repos, telemetry, prompts, and output.

Use a custom User-Agent for non-browser direct HTTP calls. Browser fetch uses the browser's own User-Agent and cannot set this header manually.
