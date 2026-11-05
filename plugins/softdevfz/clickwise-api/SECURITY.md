# Security policy

## Reporting a vulnerability

Report security issues in this repository, the Clickwise API or the Clickwise MCP server to **partnerships@clickwise.net** with the subject `Security`. Include the affected endpoint or file, steps to reproduce and the impact you observed.

- Do not open a public issue for a security report.
- Never include a real API key, access secret or personal data in a report. If one was exposed, say so and we will revoke it.
- Test only against your own account and keys. Do not access other users' data or degrade the service.

## Scope

- Code in this repository: the `main` branch.
- API v1 at `https://partners.clickwise.net/api/v1/` and the MCP server at `https://partners.clickwise.net/api/v1/mcp`.

## Handling keys in your integration

- Keep `CLICKWISE_API_KEY` on your server or in your agent's environment. Never commit it or ship it to a browser.
- The plugin and extension configs in this repo read the key from the environment and send no key when it is not set.
