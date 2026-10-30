# Security

## Reporting a vulnerability

Email ops@avatar33.com with a description, steps to reproduce, and the affected URL or file. Please do not open a public issue for a security report.

Report abusive or phishing sites hosted on deed.page at https://deed.page/abuse.

## What this plugin does

This repository contains instructions, configuration, and two optional publish scripts. It ships no install scripts or hooks.

- `skills/deed-page/SKILL.md` tells the agent to run `curl` (and `tar` for folders) against `https://deed.page/v1/sites` when the user asks to publish, deploy, host, or share a link, or confirms that upload after seeing the public URL and the exact file list. A create-only request stays a local draft. An unattended run publishes only when its instructions explicitly authorize publishing.
- `skills/deed-page/scripts/publish.sh` (POSIX sh, curl, tar) publishes a file or a clean output folder to `https://deed.page/v1/sites`. It skips sensitive and repo-metadata paths (including `.env` and `.env.*`, `.git`, `.github`, `.ssh`, `node_modules`, keys, `credentials.json`, and `secrets.*`), prints what it skipped, and prefers `dist`, `build`, `out`, `public`, or `_site` when the path is a project root. A project root with none of those folders is refused unless `--allow-root` is set. Above 4 MB it runs `skills/deed-page/scripts/publish-large.mjs` (Node 18+, no dependencies), which applies the same rules, sends a file manifest to `https://deed.page/v1/uploads`, PUTs only the missing files to the upload URLs in the response, and finalizes. Both run only when the agent publishes. `scripts/check-publish-filter.sh` checks the skip list.
- `mcp.json` and `.mcp.json` point to the hosted deed.page MCP server at `https://deed.page/mcp`.

## Network endpoints

| Endpoint | Used for |
| --- | --- |
| `https://deed.page/v1/sites` | Publish, update, and delete sites (skill) |
| `https://deed.page/v1/uploads` | Large uploads over 4 MB (`publish-large.mjs`) |
| `https://vercel.com/api/blob` | Direct upload URLs returned by `/v1/uploads` (Vercel Blob, deed.page's storage) |
| `https://deed.page/mcp` | Hosted MCP server (Streamable HTTP) |
| `https://<slug>.deed.page/` | The published site |

No other hosts are contacted.

## Credentials

- No account or API key is needed to publish.
- The first publish without a token returns a site token (`deed_tok_...`) once. The skill saves it to `~/.config/deed-page/token` (file mode 600, directory mode 700), writes that file only when a response contains a non-empty token, and loads it from `DEEDPAGE_TOKEN` or that file before every publish. It sends the token only to `https://deed.page` as `Authorization: Bearer`, to keep all sites under one owner and to update or delete them. It is never written to a published page, a commit, or a log.
- deed.page stores only a SHA-256 hash of the token.

## Data

Published sites are public. Do not publish secrets or private data. See the privacy policy at https://deed.page/privacy.
