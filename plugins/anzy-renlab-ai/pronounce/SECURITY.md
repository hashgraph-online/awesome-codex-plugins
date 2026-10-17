# Security policy

## What's in scope

This project ships:

- A Bash CLI (`bin/say-it`) that reads a TSV file and calls macOS `say` / `afplay`.
- A static website at <https://pronounce.renlab.ai> (HTML / CSS / JS / pre-rendered audio).
- A Python MCP server (`mcp-server/`) that proxies the public JSON API.

If you find a vulnerability in any of these, please report it.

## What's NOT in scope

- The macOS `say` command itself (Apple).
- Vercel's hosting platform (Vercel).
- GitHub's infrastructure (GitHub).
- General complaints about Wikipedia being a weak source — please open a regular issue or PR.

## Reporting

Report security issues via:

1. **GitHub Security Advisories** — preferred. Visit <https://github.com/anzy-renlab-ai/pronounce/security/advisories/new>.
2. **Or email the repository owner** through their GitHub profile.

Do **not** open a public issue for a real vulnerability.

## Response

We'll respond within 7 days. If the issue is real, we'll cut a fix and credit you in the release notes (unless you prefer to remain anonymous).

## Known limitations

- The CLI runs arbitrary text through `say -v <voice>` — if you pass untrusted input as the `-v` argument or the word itself, macOS `say` parses it normally (no shell escaping issues we've found, but exercise care if scripting).
- The MCP server fetches data over HTTPS from `pronounce.renlab.ai`. If you replace `SAY_IT_UPSTREAM` env var with a non-trusted server, all bets are off.
- The static site uses only public CDNs (shields.io for the GitHub star badge, your browser's Web Speech API as fallback). No third-party tracking is loaded.

## License

MIT — see [LICENSE](LICENSE).
