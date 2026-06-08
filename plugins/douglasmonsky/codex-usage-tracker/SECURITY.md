# Security Policy

## Supported Versions

Security fixes target the latest release on `main`.

## Reporting A Vulnerability

Open a private GitHub security advisory when this repository is public and advisories are enabled. Until then, contact the maintainer directly.

Do not paste real Codex logs, prompts, assistant responses, tool output, secrets, customer names, student data, private repository names, private branch names, or full local paths into public issues. If a maintainer asks for diagnostics, use `codex-usage-tracker --privacy-mode strict support-bundle --json` and review the written bundle before sharing it.

## Data Boundary

Codex Usage Tracker is designed to index aggregate token metadata from local Codex logs. Reports, CSV exports, dashboards, and the SQLite database must not contain raw prompts, assistant text, tool outputs, pasted secrets, or transcript snippets.

Project metadata is aggregate metadata, but it can still reveal private work context through cwd fragments, project names, branch names, tags, or source paths. Use `--privacy-mode redacted` or `--privacy-mode strict` before sharing dashboards, CSV exports, JSON query output, screenshots, or support bundles. Strict mode hides project-relative cwd, branch, and tags in addition to raw paths.

The optional localhost context endpoint reads one selected source JSONL record on demand, redacts common secret patterns, caps returned text size, and does not persist the loaded context.

The MCP `usage_call_context` tool is disabled unless the MCP server process explicitly sets `CODEX_USAGE_TRACKER_ALLOW_RAW_CONTEXT=1`. This keeps aggregate MCP reporting available while requiring a separate opt-in for raw local context reads.

## Localhost Dashboard Token

`serve-dashboard` creates a random per-server API token and embeds it in the generated dashboard HTML for that local server session. The token is used for localhost `/api/usage` refreshes and `/api/context` requests. Treat generated active dashboard files and URLs as local-only artifacts; do not publish them or send them to someone else.

The dashboard server rejects non-loopback hosts and cross-origin requests. This is a local hardening measure, not a reason to expose the server on a network interface.

## Support Bundles

Support bundles are intended to be safe diagnostic summaries. They include package, Python, OS, doctor, schema, parser diagnostic, pricing, allowance, threshold, and project-config status. They do not include raw logs, prompts, assistant messages, tool output, or context text.

Before sharing a bundle:

1. Generate it with strict project metadata privacy:

   ```bash
   codex-usage-tracker --privacy-mode strict support-bundle --output ~/.codex-usage-tracker/support-bundle.json
   ```

2. Open the file locally and scan for private project names, branch names, local paths, or anything else you do not want to share.

3. Share only the smallest diagnostic excerpt needed for the issue.
