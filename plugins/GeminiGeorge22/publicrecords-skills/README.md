# publicrecords skills: Agent Skills + MCP plugin for public-records data

Nine [Agent Skills](https://agentskills.io) and one hosted MCP server that let your AI assistant pull **official public data** through the [publicrecords](https://apify.com/publicrecords) Actors on Apify: US federal contracts and grants, UK and EU tenders, city council meetings, new job postings from ATS boards, company social links, Etsy market data, competitor Google ads, sports odds, Spotify play counts, forecast track records and Skool community search.

One repo, packaged for every major agent: **Claude Code / Claude, OpenAI Codex / ChatGPT, GitHub Copilot, Cursor, Gemini CLI, Kiro**, and any client that reads the [Agent Plugins](https://agent-plugins.org) format or plain `SKILL.md` folders.

> **Disclosure:** published by the publicrecords maintainer on Apify Store. Actor runs are **pay-per-event** and bill **your own** Apify account; current prices are on each Actor's Store page. This repo holds instructions and manifests only: no Actor source, no tokens.

## Skills

| Skill | What it answers | Actors |
|---|---|---|
| [`gov-tenders-and-grants`](skills/gov-tenders-and-grants/SKILL.md) | SAM.gov + Grants.gov feed, Grants.gov, USAspending awards, UK Find a Tender, EU TED, Legistar council meetings | [`govcon-opportunity-feed`](https://apify.com/publicrecords/govcon-opportunity-feed), [`grants-gov-scraper`](https://apify.com/publicrecords/grants-gov-scraper), [`usaspending-awards-scraper`](https://apify.com/publicrecords/usaspending-awards-scraper), [`uk-find-a-tender-scraper`](https://apify.com/publicrecords/uk-find-a-tender-scraper), [`eu-ted-notices-scraper`](https://apify.com/publicrecords/eu-ted-notices-scraper), [`legistar-meetings-scraper`](https://apify.com/publicrecords/legistar-meetings-scraper) |
| [`ats-job-postings`](skills/ats-job-postings/SKILL.md) | New postings since any date from Ashby, Greenhouse, Lever, SmartRecruiters boards | [`ashby-jobs-scraper`](https://apify.com/publicrecords/ashby-jobs-scraper), [`greenhouse-jobs-scraper`](https://apify.com/publicrecords/greenhouse-jobs-scraper), [`lever-jobs-scraper`](https://apify.com/publicrecords/lever-jobs-scraper), [`smartrecruiters-jobs-scraper`](https://apify.com/publicrecords/smartrecruiters-jobs-scraper) |
| [`company-social-profiles`](skills/company-social-profiles/SKILL.md) | Company website or name to LinkedIn, X, YouTube, Instagram, Facebook handles, with evidence | [`company-social-profile-finder`](https://apify.com/publicrecords/company-social-profile-finder) |
| [`etsy-market-research`](skills/etsy-market-research/SKILL.md) | Etsy search listing rows + daily/7-day/28-day shop sales | [`etsy-search-scraper`](https://apify.com/publicrecords/etsy-search-scraper), [`etsy-shop-velocity`](https://apify.com/publicrecords/etsy-shop-velocity) |
| [`google-ads-transparency`](skills/google-ads-transparency/SKILL.md) | Competitor Google ads: new, running, stopped, with shown dates | [`google-ads-transparency-scraper`](https://apify.com/publicrecords/google-ads-transparency-scraper) |
| [`sports-odds`](skills/sports-odds/SKILL.md) | Live and pre-game odds from Kambi-powered sportsbooks, best price per outcome | [`sports-odds-api`](https://apify.com/publicrecords/sports-odds-api) |
| [`spotify-play-counts`](skills/spotify-play-counts/SKILL.md) | Play counts per track, monthly listeners, followers | [`spotify-play-count-scraper`](https://apify.com/publicrecords/spotify-play-count-scraper) |
| [`forecast-track-record`](skills/forecast-track-record/SKILL.md) | Track record of an organization's forecasts (IMF, OECD, Fed, SPF, ECB SPF, issuers), beta | [`calibration-ledger`](https://apify.com/publicrecords/calibration-ledger) |
| [`skool-communities`](skills/skool-communities/SKILL.md) | Search Skool communities by keyword: members, price, rating, estimated revenue, plus daily growth tracking | [`skool-community-growth-tracker`](https://apify.com/publicrecords/skool-community-growth-tracker) |

## Install

You need an Apify account. MCP clients sign you in with OAuth; or use your own API token as `Authorization: Bearer <token>`. Never commit a token.

| Client | Command or link |
|---|---|
| Claude Code | `/plugin marketplace add GeminiGeorge22/publicrecords-skills` then `/plugin install publicrecords@publicrecords` |
| OpenAI Codex | `codex plugin marketplace add GeminiGeorge22/publicrecords-skills` |
| GitHub Copilot CLI | `copilot plugin install GeminiGeorge22/publicrecords-skills` (root `plugin.json`, Agent Plugins 1.0.0) |
| Gemini CLI | `gemini extensions install https://github.com/GeminiGeorge22/publicrecords-skills` |
| Kiro | Powers → Add Custom Power → Import power from GitHub → `https://github.com/GeminiGeorge22/publicrecords-skills` |
| Any skills client (Claude, Codex, Cursor, OpenCode, Goose…) | `npx skills add GeminiGeorge22/publicrecords-skills` |
| LM Studio, Windsurf, Cline, Zed, other MCP clients | paste the MCP JSON below into the client's MCP config |
| Cursor (MCP only) | [Add to Cursor](https://cursor.com/en/install-mcp?name=publicrecords&config=eyJ1cmwiOiAiaHR0cHM6Ly9tY3AuYXBpZnkuY29tLz90b29scz1wdWJsaWNyZWNvcmRzL2NvbXBhbnktc29jaWFsLXByb2ZpbGUtZmluZGVyLHB1YmxpY3JlY29yZHMvZ292Y29uLW9wcG9ydHVuaXR5LWZlZWQscHVibGljcmVjb3Jkcy9ncmFudHMtZ292LXNjcmFwZXIscHVibGljcmVjb3Jkcy91c2FzcGVuZGluZy1hd2FyZHMtc2NyYXBlcixwdWJsaWNyZWNvcmRzL3VrLWZpbmQtYS10ZW5kZXItc2NyYXBlcixwdWJsaWNyZWNvcmRzL2V1LXRlZC1ub3RpY2VzLXNjcmFwZXIscHVibGljcmVjb3Jkcy9sZWdpc3Rhci1tZWV0aW5ncy1zY3JhcGVyLHB1YmxpY3JlY29yZHMvYXNoYnktam9icy1zY3JhcGVyLHB1YmxpY3JlY29yZHMvZ3JlZW5ob3VzZS1qb2JzLXNjcmFwZXIscHVibGljcmVjb3Jkcy9sZXZlci1qb2JzLXNjcmFwZXIscHVibGljcmVjb3Jkcy9zbWFydHJlY3J1aXRlcnMtam9icy1zY3JhcGVyLHB1YmxpY3JlY29yZHMvZXRzeS1zZWFyY2gtc2NyYXBlcixwdWJsaWNyZWNvcmRzL2V0c3ktc2hvcC12ZWxvY2l0eSxwdWJsaWNyZWNvcmRzL2dvb2dsZS1hZHMtdHJhbnNwYXJlbmN5LXNjcmFwZXIscHVibGljcmVjb3Jkcy9zcG9ydHMtb2Rkcy1hcGkscHVibGljcmVjb3Jkcy9zcG90aWZ5LXBsYXktY291bnQtc2NyYXBlcixwdWJsaWNyZWNvcmRzL2NhbGlicmF0aW9uLWxlZGdlcixwdWJsaWNyZWNvcmRzL3Nrb29sLWNvbW11bml0eS1ncm93dGgtdHJhY2tlciJ9) |
| VS Code / Copilot Chat (MCP only) | [Install in VS Code](https://vscode.dev/redirect/mcp/install?name=publicrecords&config=%7B%22type%22%3A%20%22http%22%2C%20%22url%22%3A%20%22https%3A//mcp.apify.com/%3Ftools%3Dpublicrecords/company-social-profile-finder%2Cpublicrecords/govcon-opportunity-feed%2Cpublicrecords/grants-gov-scraper%2Cpublicrecords/usaspending-awards-scraper%2Cpublicrecords/uk-find-a-tender-scraper%2Cpublicrecords/eu-ted-notices-scraper%2Cpublicrecords/legistar-meetings-scraper%2Cpublicrecords/ashby-jobs-scraper%2Cpublicrecords/greenhouse-jobs-scraper%2Cpublicrecords/lever-jobs-scraper%2Cpublicrecords/smartrecruiters-jobs-scraper%2Cpublicrecords/etsy-search-scraper%2Cpublicrecords/etsy-shop-velocity%2Cpublicrecords/google-ads-transparency-scraper%2Cpublicrecords/sports-odds-api%2Cpublicrecords/spotify-play-count-scraper%2Cpublicrecords/calibration-ledger%2Cpublicrecords/skool-community-growth-tracker%22%7D) · [VS Code Insiders](https://insiders.vscode.dev/redirect/mcp/install?name=publicrecords&config=%7B%22type%22%3A%20%22http%22%2C%20%22url%22%3A%20%22https%3A//mcp.apify.com/%3Ftools%3Dpublicrecords/company-social-profile-finder%2Cpublicrecords/govcon-opportunity-feed%2Cpublicrecords/grants-gov-scraper%2Cpublicrecords/usaspending-awards-scraper%2Cpublicrecords/uk-find-a-tender-scraper%2Cpublicrecords/eu-ted-notices-scraper%2Cpublicrecords/legistar-meetings-scraper%2Cpublicrecords/ashby-jobs-scraper%2Cpublicrecords/greenhouse-jobs-scraper%2Cpublicrecords/lever-jobs-scraper%2Cpublicrecords/smartrecruiters-jobs-scraper%2Cpublicrecords/etsy-search-scraper%2Cpublicrecords/etsy-shop-velocity%2Cpublicrecords/google-ads-transparency-scraper%2Cpublicrecords/sports-odds-api%2Cpublicrecords/spotify-play-count-scraper%2Cpublicrecords/calibration-ledger%2Cpublicrecords/skool-community-growth-tracker%22%7D) |

### MCP server only

```json
{
  "mcpServers": {
    "publicrecords": { "type": "http", "url": "https://mcp.apify.com/?tools=publicrecords/company-social-profile-finder,publicrecords/govcon-opportunity-feed,publicrecords/grants-gov-scraper,publicrecords/usaspending-awards-scraper,publicrecords/uk-find-a-tender-scraper,publicrecords/eu-ted-notices-scraper,publicrecords/legistar-meetings-scraper,publicrecords/ashby-jobs-scraper,publicrecords/greenhouse-jobs-scraper,publicrecords/lever-jobs-scraper,publicrecords/smartrecruiters-jobs-scraper,publicrecords/etsy-search-scraper,publicrecords/etsy-shop-velocity,publicrecords/google-ads-transparency-scraper,publicrecords/sports-odds-api,publicrecords/spotify-play-count-scraper,publicrecords/calibration-ledger,publicrecords/skool-community-growth-tracker" }
  }
}
```

Each Actor becomes a tool named `publicrecords--<actor-name>` ([Apify MCP docs](https://docs.apify.com/platform/integrations/mcp)). Want only one Actor? Each has its own entry in the [Official MCP Registry](https://registry.modelcontextprotocol.io/v0/servers?search=io.github.GeminiGeorge22) under `io.github.GeminiGeorge22/*`, also indexed in [publicrecords-mcp](https://github.com/GeminiGeorge22/publicrecords-mcp).

## Checks

- `claude plugin validate .`: passed (no findings).
- `gemini extensions validate .`: passed.
- `plugin.json` / `mcp.json`: valid against Agent Plugins 1.0.0 schemas.
- HOL AI Plugin Scanner 3.61.0: 100/100.

## Layout

```
plugin.json                      Agent Plugins 1.0.0 manifest (Copilot, Codex/ChatGPT, Kiro, Cursor)
mcp.json                         Agent Plugins MCP config (streamable-http)
.claude-plugin/plugin.json       Claude Code plugin manifest
.claude-plugin/marketplace.json  Claude Code marketplace (this repo = 1 plugin)
.mcp.json                        Claude Code MCP config
.agents/plugins/marketplace.json Codex / ChatGPT repo marketplace
gemini-extension.json + GEMINI.md Gemini CLI extension
skills/<name>/SKILL.md           Agent Skills
```

## What these skills will not do

- Write to any site (no posting, no listing changes, no messages). All Actors read public data.
- Look up people. The company-social and forecast skills cover organizations only.
- Give betting, investment or legal advice.

## License

MIT, for the skills and manifests in this repo. The Actors are separate products on Apify Store.
