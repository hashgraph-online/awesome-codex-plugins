# Court Rules for Codex

A Codex plugin that connects the agent to [Court Rules](https://www.courtrules.app/), a free reference for U.S. federal and state court rules, local rules and judge standing orders.

The plugin bundles two things:

- **MCP server:** the hosted Court Rules server at `https://mcp.courtrules.app/mcp` (streamable HTTP, read-only).
- **Skill:** `court-rules`, which tells the agent how to find the right court and judge, search the rules by topic, cite the court's own document, and flag what the user must verify before filing.

## What you can ask

- "What are the page limits for a summary judgment brief in EDNY?"
- "What courtesy copy rules apply to Judge Reilly in Cook County?"
- "What e-filing rules apply to civil filings in Cook County?"
- "Which days is the Southern District of New York closed in 2026?"
- "What privacy enforcement actions happened in California this year?"

## MCP tools

| Tool | Purpose |
| --- | --- |
| `list_courts` | Page through courts, or find one by name or ID |
| `search_judges` | Find a judge by district, name or type |
| `get_judge_rules` | Every extracted rule for one judge |
| `search_filing_rules` | Search e-filing, service, timing, fee, courtesy copy and formatting rules |
| `list_court_holidays` | Court holidays and closure dates, with source URLs |
| `check_compliance` | Build the request parameters for the REST compliance check |
| `search_enforcement_actions` | Search privacy and regulatory enforcement actions |
| `get_enforcement_details` | Full details of one enforcement action |
| `get_enforcement_stats` | Enforcement statistics grouped by jurisdiction, type, risk level or month |

## Install

This repository is a Codex plugin: the manifest is `.codex-plugin/plugin.json` and the MCP configuration is `.mcp.json`. Install it either way:

- From a curated marketplace that lists it, such as [Awesome Codex Plugins](https://github.com/hashgraph-online/awesome-codex-plugins).
- From a local copy: clone this repository to `~/.codex/plugins/court-rules` and add it to a personal marketplace as described in the [Codex plugin docs](https://developers.openai.com/codex/plugins/build#install-a-local-plugin-manually), then restart Codex.

## Sign in

The first tool call asks you to sign in. A browser window opens `console.courtrules.app`; sign in with Google or email and approve the connection once. The client keeps you signed in after that.

To use an API key instead (scripts, CI, clients without a browser), create one at [console.courtrules.app](https://console.courtrules.app) and send it as `Authorization: Bearer <api_key>`. Details: [Authentication](https://docs.courtrules.app/authentication).

## Notes

- All tools are read-only. The plugin contains no executable code and stores no credentials.
- Answers cite the court's own document. Confirm the cited source before you file. This is reference information, not legal advice.
- This plugin was written against the published tool list of the hosted server. It has not been run inside a live Codex session with a signed-in account by its authors at the time of writing.

## Links

- Website: https://www.courtrules.app/
- MCP guide: https://docs.courtrules.app/guides/mcp-court-rules
- REST API docs: https://docs.courtrules.app
- Support: api@courtrules.app
- Security reports: see [SECURITY.md](SECURITY.md)

## License

MIT. See [LICENSE](LICENSE).
