# Security policy

## Reporting a vulnerability
Please report vulnerabilities privately through GitHub: Security tab, "Report a vulnerability"
(https://github.com/mohamedOmar11111/growth-architect-foundry/security/advisories/new).
Do not open a public issue for security problems. Expect an acknowledgement within 7 days.

## Supported versions
Only the latest release (see CHANGELOG.md) receives security fixes.

## What the project protects
- **Live ad-account writes** (`live pause`, `live budget`) need `--confirm` and a person typing the
  campaign key at a real terminal. AI agent shells have no terminal, so they exit 3 (refused).
  Budget changes are capped at 20% per campaign per 7 days.
- **Tenant isolation**: client names must match their folder exactly; symlinks and paths that
  resolve outside the client folder are refused.
- **Secrets**: `.env` files are created with owner-only permissions and are never printed;
  API errors are scrubbed of access tokens before display.
- **Untrusted data**: campaign names and lead-form text are sanitised before they reach reports,
  logs or prompts.

## Known limits
- An agent that attaches a pseudo-terminal could in principle answer the approval prompt. Keep
  your agent's own permission prompts on for the two live-write commands.
- Live writes are covered by mocked tests. One real-account check has been done (28 Oct 2026, Meta): a budget
  change on a paused, zero-spend campaign was refused on wrong approval text (exit 3, no change), applied with the
  correct key (10 to 11), verified on Meta, reverted (11 to 10), and a 50% change was blocked by the 20% cap.
  Not yet run on a real account: `live pause` and every Google Ads write.
- The engine runs locally and sends no telemetry. `core/engine/agent_shim.py` is the only part that
  calls an LLM provider, and only when you configure a key.
