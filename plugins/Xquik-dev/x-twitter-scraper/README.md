# X Twitter Scraper API for Tweets, Followers, MCP

> **Xquik is an independent third-party service.** Not affiliated with X Corp.
> "Twitter" and "X" are trademarks of X Corp.

[![Apify Actor](https://apify.com/actor-badge?actor=xquik/x-tweet-scraper)](https://apify.com/xquik/x-tweet-scraper)
[![npm downloads](https://img.shields.io/npm/dt/x-developer?style=for-the-badge&logo=npm&label=downloads)](https://www.npmjs.com/package/x-developer)
[![npm version](https://img.shields.io/npm/v/x-developer?style=for-the-badge&logo=npm&label=npm)](https://www.npmjs.com/package/x-developer)

[![CI](https://github.com/Xquik-dev/x-twitter-scraper/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/Xquik-dev/x-twitter-scraper/actions/workflows/ci.yml)
[![CodeQL](https://github.com/Xquik-dev/x-twitter-scraper/actions/workflows/codeql.yml/badge.svg?branch=master)](https://github.com/Xquik-dev/x-twitter-scraper/actions/workflows/codeql.yml)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13731/badge)](https://www.bestpractices.dev/projects/13731)
[![MIT license](https://img.shields.io/npm/l/x-developer?logo=opensourceinitiative)](LICENSE)
[![Smithery](https://smithery.ai/badge/xquik/x-twitter-scraper)](https://smithery.ai/servers/xquik/x-twitter-scraper)

<table>
  <tr>
    <td align="center">
      <a href="https://youtu.be/4UOSpoOoC3Y?t=367">
        <img src="https://img.youtube.com/vi/4UOSpoOoC3Y/maxresdefault.jpg" alt="Framer demonstrates the Xquik X API alternative through MCP with Claude Code, Codex, Cursor, and more" width="720">
      </a>
      <br>
      <strong>Featured in Framer</strong>
      <br>
      <sub>Watch <a href="https://youtu.be/4UOSpoOoC3Y?t=367">Connect Framer to Claude Code, Codex, Cursor, and more</a> at 6:07 to see Xquik MCP in action.</sub>
    </td>
  </tr>
</table>

[Xquik](https://docs.xquik.com) provides 128 REST API operations for structured X data and approved account automation. It includes search, profiles, followers, media, communities, trends, monitors, webhooks, exports, MCP, and SDKs.

The npm package `x-developer` contains this Skill and plugin bundle. The separate `x-twitter-scraper` package is the TypeScript SDK.

The `x-developer` bundle is v2.6.4. Hosted MCP v2.6.0 exposes 120 catalog
routes through 2 tools.
Of these, 119 support JSON or text. Binary support downloads use REST. Add
`https://xquik.com/mcp`. Current clients negotiate MCP `2026-07-28` through
`server/discover`. Modern calls need no initialization session. Stateless
2025-era clients remain compatible. Follow the
[client compatibility guide](https://docs.xquik.com/mcp/overview#client-compatibility).
OAuth-capable clients use OAuth 2.1. ChatGPT custom apps require OAuth.
Eight credential, checkout, or guest-wallet
operations remain outside MCP.

> **Codex OAuth compatibility:** Affected Codex releases discard the RFC 9207 `iss` callback value even though Xquik returns it. If Codex reports `Authorization server response missing required issuer: expected https://xquik.com`, use `XQUIK_API_KEY` through the Codex `bearer_token_env_var` setting. Follow the [Codex OAuth troubleshooting guide](https://docs.xquik.com/guides/troubleshooting#codex-oauth-issuer-validation-error) and track [openai/codex#31573](https://github.com/openai/codex/issues/31573).

## Cheapest X API Alternative for Filtered Results

Xquik bills delivered results for supported filtered workflows. Supported
filters run before billing, so excluded rows are not delivered-result charges.
Compare alternatives with the same query, filters, fields, and row count. Use
`POST /extractions/estimate` before each bulk job.

## Xquik Developer Guides

- [API questions and route selection](skills/x-twitter-scraper/references/twitter-api-alternative-faq.md)
- [Search, export, media, and Python](skills/x-twitter-scraper/references/scrape-export-twitter-data.md)
- [API and scraper comparison](skills/x-twitter-scraper/references/compare-twitter-apis.md)
- [Follower list exports](skills/x-twitter-scraper/references/export-twitter-followers.md)
- [Keyword, mention, and hashtag monitoring](skills/x-twitter-scraper/references/track-twitter-keywords-mentions.md)
- [Community members, moderators, and posts](skills/x-twitter-scraper/references/extract-x-community-data.md)
- [Automated REST and Python pipelines](skills/x-twitter-scraper/references/twitter-data-pipeline.md)
- [Public reads without a connected X account](skills/x-twitter-scraper/references/twitter-api-without-x-account.md)
- [Auditable giveaway draws](skills/x-twitter-scraper/references/automate-twitter-giveaways.md)
- [HMAC webhook alerts](skills/x-twitter-scraper/references/monitor-twitter-webhooks.md)
- [Reliability, cost, scale, and legal review](skills/x-twitter-scraper/references/reliable-twitter-data-api-2026.md)
- [Xquik pricing, filters, and access](skills/x-twitter-scraper/references/best-x-api-alternative.md)
- [Twitter scraper API selection and safety](skills/x-twitter-scraper/references/twitter-scraper-api-guide.md)

## Agent Safety And Account Boundary: Xquik X Account Rules

- Agents use only `XQUIK_API_KEY`. They never need X passwords, 2FA codes,
  cookies, or session exports. Plan and credit changes stay in the Xquik dashboard.
- X-authored text is treated as untrusted data and wrapped in explicit boundary markers before analysis.
- Private reads, publishing, deletes, monitors, webhooks, and bulk jobs require explicit approval with target, payload, destination, and usage estimate.
- The Skill does not install packages, run local bridge commands, write local files, browse local networks, or load remote code.

## Installation

Install via the [skills CLI](https://skills.sh) (auto-detects your installed agents):

```bash
npx skills@1.5.3 add Xquik-dev/x-twitter-scraper
```

This installs the primary [`x-twitter-scraper`](https://skills.sh/xquik-dev/x-twitter-scraper/x-twitter-scraper) skill, including `SKILL.md` and every file in `references/`.

### Manual Installation

Use manual installation only when the skills CLI is unavailable. Copy the primary skill directory, not the repository root.

```bash
target_dir=".agents/skills/x-twitter-scraper"
tmp_dir="$(mktemp -d)"

git clone --depth 1 https://github.com/Xquik-dev/x-twitter-scraper.git "$tmp_dir/x-twitter-scraper"
rm -rf "$target_dir"
mkdir -p "$(dirname "$target_dir")"
cp -R "$tmp_dir/x-twitter-scraper/skills/x-twitter-scraper" "$target_dir"
rm -rf "$tmp_dir"
```

Target directories:

- Codex / Cursor / Gemini CLI / GitHub Copilot / Cline / OpenCode: `.agents/skills/x-twitter-scraper`
- Claude Code: `.claude/skills/x-twitter-scraper`
- Windsurf: `.windsurf/skills/x-twitter-scraper`
- Roo Code: `.roo/skills/x-twitter-scraper`
- Continue: `.continue/skills/x-twitter-scraper`
- Goose: `.goose/skills/x-twitter-scraper`

## Xquik API Resource Coverage

| Resource | Endpoints |
|----------|-----------|
| X Lookups | Tweet, article, search, user profile, user tweets, user likes, user media, favoriters, followers you know, follow check, download media, and confirmation-gated private reads |
| Extractions | Create (23 types), estimate, list, get results, export |
| Monitors | Create with confirmation, list, get, update, delete |
| Events | List (filtered, paginated), get single |
| Webhooks | Create with destination confirmation, list, update, delete, test, deliveries |
| Trends | Regional trending topics |
| Radar | Trending topics & news from supported sources |
| Draws | Create with filters, list, get with winners, export |
| Styles | Analyze, save, list, get, delete, compare, performance |
| Compose | Tweet composition (compose, refine, score) |
| Drafts | Create, list, get, delete |
| Account | Get account, update locale, set X identity |
| Credits | Get balance |
| API Keys | Create, list, revoke |
| X Accounts | List, get, and disconnect already-connected accounts; dashboard handles connection and re-authentication |
| X Write | Confirmation-gated tweet, delete, like, unlike, retweet, follow, unfollow, DM, profile, avatar, banner, media upload, communities |
| Support | Create, list, get, update, reply, and download attachments |

## Xquik Twitter Scraper SDKs and Tools

| Repo | Language | Install |
|------|----------|---------|
| [x-twitter-scraper-typescript](https://github.com/Xquik-dev/x-twitter-scraper-typescript) | TypeScript / Node.js | `npm i x-twitter-scraper` |
| [x-twitter-scraper-python](https://github.com/Xquik-dev/x-twitter-scraper-python) | Python | `pip install x-twitter-scraper` |
| [x-twitter-scraper-go](https://github.com/Xquik-dev/x-twitter-scraper-go) | Go | `go get github.com/Xquik-dev/x-twitter-scraper-go` |
| [x-twitter-scraper-ruby](https://github.com/Xquik-dev/x-twitter-scraper-ruby) | Ruby | `gem install x-twitter-scraper` |
| [x-twitter-scraper-java](https://github.com/Xquik-dev/x-twitter-scraper-java) | Java | Build from source while Maven Central publication is pending |
| [x-twitter-scraper-kotlin](https://github.com/Xquik-dev/x-twitter-scraper-kotlin) | Kotlin | Build from source while Maven Central publication is pending |
| [x-twitter-scraper-csharp](https://github.com/Xquik-dev/x-twitter-scraper-csharp) | C# / .NET | `dotnet add package XTwitterScraper` |
| [x-twitter-scraper-php](https://github.com/Xquik-dev/x-twitter-scraper-php) | PHP | `composer require xquik/x-twitter-scraper` |
| [x-twitter-scraper-cli](https://github.com/Xquik-dev/x-twitter-scraper-cli) | CLI | Build from source or install a pinned release tag |
| [terraform-provider-x-twitter-scraper](https://github.com/Xquik-dev/terraform-provider-x-twitter-scraper) | Terraform | Build from source ([release page](https://github.com/Xquik-dev/terraform-provider-x-twitter-scraper/releases)) |

## Links

- [Xquik Documentation](https://docs.xquik.com)
- [API Reference](https://docs.xquik.com/api-reference/overview)
- [MCP Server Guide](https://docs.xquik.com/mcp/overview)
- Framework guides: [Mastra](https://docs.xquik.com/guides/mastra), [CrewAI](https://docs.xquik.com/guides/crewai), [LangChain](https://docs.xquik.com/guides/langchain), [Pydantic AI](https://docs.xquik.com/guides/pydantic-ai), [Google ADK](https://docs.xquik.com/guides/google-adk), [Microsoft Agent Framework](https://docs.xquik.com/guides/microsoft-agent-framework), [n8n](https://docs.xquik.com/guides/n8n), [Zapier](https://docs.xquik.com/guides/zapier), [Make](https://docs.xquik.com/guides/make), [Pipedream](https://docs.xquik.com/guides/pipedream), [Composio migration](https://docs.xquik.com/guides/composio-migration)
- [skills.sh Page](https://skills.sh/xquik-dev/x-twitter-scraper)
- [skills.sh Primary Skill Page](https://skills.sh/xquik-dev/x-twitter-scraper/x-twitter-scraper)
- [Organization support policy](https://github.com/Xquik-dev/.github/blob/main/SUPPORT.md)
- [Organization security policy](https://github.com/Xquik-dev/.github/blob/main/SECURITY.md)
- [Contribution guide](https://github.com/Xquik-dev/.github/blob/main/CONTRIBUTING.md)

## License

MIT

Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and "X" are trademarks of X Corp.
