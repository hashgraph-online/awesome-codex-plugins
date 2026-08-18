# Security Policy

## Scope

Quality-Engineering-Skills is **primarily a content repository** — structured markdown skill files and agent instructions — but it is not content-only. It also contains two deployable Cloudflare Workers under `platforms/`, which are executable code that runs as a server and relays user-submitted text to a third-party LLM API.

Treat the content and the Workers as two different risk surfaces.

## What this repository contains

**Content (no execution)**

- SKILL.md files: structured methodology instructions for AI agents
- Reference files: quality engineering tables, templates, checklists
- Platform connectors for prompt-based platforms (ChatGPT, Claude, Gemini): configuration and instruction files only

**Executable code (server-side)**

- `platforms/slack/worker.js` — Slack connector. Verifies every request with an HMAC-SHA256 Slack signature and a 5-minute timestamp window; rejects unsigned requests with `401`.
- `platforms/m365/worker.js` — M365 Copilot plugin API. Relays 8D, NCR and FMEA text to the Anthropic API.

## Security model of the M365 Worker

The M365 Worker accepts quality documents that routinely contain confidential customer, product, supplier, process and intellectual-property data. It is therefore configured to **fail closed**:

- It requires an `API_TOKEN` environment variable. If `API_TOKEN` is not set, the Worker refuses every request with `503` and never calls the LLM API. An unconfigured deployment serves nothing.
- Every request must present `Authorization: Bearer <API_TOKEN>`. Requests without a valid token are rejected with `401`.
- Cross-origin access is restricted to the origins listed in `ALLOWED_ORIGINS`. There is no wildcard default.
- Request bodies are capped; oversized payloads are rejected with `413`.

Rate limiting is **not** implemented in the Worker itself. Configure it at the Cloudflare edge before exposing the Worker to real traffic — the token check limits *who* can call the API, not *how much* they can spend.

Deploying either Worker sends the submitted text to the Anthropic API. Do not deploy them for data you are not permitted to disclose to a third-party processor.

## Reporting a vulnerability

If you identify a security concern — for example:

- A platform connector that could be misused to exfiltrate data
- A SKILL.md instruction that could cause an AI to produce harmful outputs
- A credential or sensitive value accidentally committed

Please open a GitHub Issue with the label **`security`**. Do not include credentials or sensitive details in the issue body — describe the concern and we will follow up privately.

There is no bug bounty programme for this project.

## API key management

All platform connectors that require API keys (Slack signing secret, Cloudflare Worker tokens) document them as environment variables. No API keys or tokens are committed to this repository.

If you find a token or credential accidentally committed, please report it immediately via a `security`-labelled issue.
