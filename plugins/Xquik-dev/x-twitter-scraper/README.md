# X Twitter Scraper API For Tweets, Followers, MCP

<table>
  <tr>
    <td align="center">
      <a href="https://youtu.be/4UOSpoOoC3Y?t=367">
        <img src="https://img.youtube.com/vi/4UOSpoOoC3Y/maxresdefault.jpg" alt="Framer shows Xquik MCP with Claude Code, Codex, Cursor, and more" width="720">
      </a>
      <br>
      <strong>Featured in Framer</strong>
      <br>
      <sub>Watch <a href="https://youtu.be/4UOSpoOoC3Y?t=367">Connect Framer to Claude Code, Codex, Cursor, and more</a> at 6:07 to see Xquik MCP in action.</sub>
    </td>
  </tr>
</table>

[Xquik](https://docs.xquik.com) is a production Twitter/X scraper API and X API alternative for teams that need structured X data at scale: tweet search, profiles, followers, following, engagement, media, lists, communities, trends, monitors, webhooks, exports, MCP tools, SDKs, and confirmation-gated X actions.

This repository packages Xquik as an [AI agent skill](https://skills.sh) for Claude Code, OpenAI Codex, Cursor, GitHub Copilot, Gemini CLI, Windsurf, and other skills-compatible agents. It helps agents choose the right REST endpoint, MCP tool, SDK, webhook, extraction, export, or approval-gated workflow without guessing.

Includes 100+ REST API endpoints (122 documented operations), 2 MCP tools, HMAC webhooks, 23 bulk extraction tools, official SDK pointers, and confirmation-gated write actions.

## Why Teams Use Xquik

- **Replace fragmented Twitter scraper tools** with one X data API for reads, exports, monitors, webhooks, SDKs, MCP, and gated writes.
- **Ship X data integrations faster** with endpoint routing for tweet search, user lookup, timelines, followers, replies, quotes, retweeters, favoriters, media, lists, communities, articles, trends, and Spaces.
- **Build production apps, not just dataset runs** with REST APIs, typed SDKs, OpenAPI, MCP tools, cursor pagination, webhook delivery, and exports.
- **Control large jobs before they run** with usage estimates for extractions, draws, monitors, webhooks, and other metered workflows.
- **Keep agents safe around X content** with API-key-only auth, read-only defaults, untrusted-content delimiters, and explicit approval for private reads, writes, persistent resources, and bulk jobs.
- **Support enterprise-scale X data pipelines** with high-throughput read limits, bulk extraction jobs, exports, event replay, and webhook automation.
- **Win high-intent search traffic** for Twitter scraper API, X scraper, X API alternative, tweet search API, Twitter follower export, social listening API, X monitoring, and X automation.

## What You Can Scrape From X Twitter

| Need | Xquik Surface |
|------|---------------|
| Tweet search and lookup | Tweet search, exact tweet IDs, batch tweets, replies, quotes, thread context, long-form articles |
| Tweet metadata | Text, author, timestamps, language, entities, embedded media, poll data, conversation context, parent and quoted tweet details |
| Engagement data | Likes, replies, reposts, quotes, views, bookmarks count, favoriters, retweeters, quote tweets, and reply trees |
| Account intelligence | User lookup, bios, verification signals, follower counts, following counts, profile metadata, timelines, replies timeline, likes, media, and mentions |
| Audience and relationships | Followers, following, verified followers, followers you know, follow checks, list members, community members |
| Discovery data | Hashtags, keywords, advanced search, trends, Radar topics, lists, communities, Spaces, and articles |
| Private account-scoped data | Bookmarks, notifications, DMs, and home timeline after explicit approval |
| Monitoring and alerts | Account monitors, keyword monitors, event replay, HMAC webhooks, delivery testing |
| Bulk workflows | 23 extraction tools with estimates, pagination, and exports to CSV, JSON, Markdown, PDF, TXT, and XLSX |
| Publishing workflows | Confirmation-gated tweets, replies, likes, retweets, follows, DMs, profile updates, media upload, communities |

## Start From Any X Input

Use profile URLs, @handles, user IDs, tweet URLs, tweet IDs, search queries, hashtags, list IDs, community IDs, Space IDs, article tweet IDs, webhook destinations, or bulk target lists. Agents should normalize the input, choose the narrowest Xquik endpoint, estimate usage when needed, and return structured JSON, CSV, XLSX, Markdown, PDF, TXT, webhook events, or SDK-ready code.

## Twitter Scraper API Use Cases

| Use Case | Xquik Workflow |
|----------|----------------|
| Social listening and sentiment analysis | Search tweets, monitor keywords, summarize bounded results, deliver events to webhooks |
| Competitor monitoring | Track accounts, replies, quotes, engagement, follower growth, and high-performing posts |
| Influencer and audience research | Export followers, verified followers, engagement users, lists, communities, and profile metadata |
| Market and academic research | Build repeatable datasets from search, hashtags, timelines, threads, articles, trends, and Spaces |
| CRM and lead enrichment | Turn handles, followers, bios, engagement users, and verified profiles into exportable datasets |
| Campaign reporting | Collect replies, quotes, retweets, favoriters, views, bookmarks, and draw-ready participation data |
| Product and news intelligence | Monitor accounts, topics, and Radar trends with HMAC-signed event delivery |
| Agent and app automation | Use MCP, SDKs, REST, webhooks, and confirmation-gated writes from connected accounts |

## Built For Agents And Apps

| Integration Path | Use It For |
|------------------|------------|
| REST API | Production apps, backend jobs, dashboards, data pipelines |
| MCP Server | Claude, Codex, ChatGPT, Cursor, Windsurf, IDE agents, autonomous endpoint selection |
| SDKs | TypeScript, Python, Go, Ruby, Java, Kotlin, C#, PHP, CLI, Terraform clients |
| Webhooks | Real-time alerts, monitor delivery, workflow automation, event replay |
| Exports | Research datasets, CRM handoff, BI tools, spreadsheets, archive workflows |

## Cost Control, Rate Limits, And High-Volume Workflows

Xquik is built for production X data jobs where teams care about predictable usage, large result sets, and integration paths beyond a single dataset run.

- **About 33x cheaper than the official X API for tweet reads**: Xquik's public comparison docs list official X API post reads at USD 0.005/resource and Xquik read units at USD 0.00015/result. For tweet search and post reads, that is roughly 33.3x cheaper. Always verify current official X API rates before procurement.
- **Higher read throughput for supported workflows**: Xquik docs list read limits at 60 requests per second per account. Official X API rate-limit tables use per-15-minute windows for many endpoints, including recent search at 450 requests per app and 300 requests per user per 15 minutes.
- Use `POST /extractions/estimate` before large exports so agents can show expected usage before creating work.
- Use cursor pagination and batch endpoints for high-throughput read workflows.
- Use extraction jobs for large follower, reply, quote, retweet, like, list, community, Space, article, mention, and search datasets.
- Use exports when teams need CSV, JSON, Markdown, PDF, TXT, or XLSX handoff.
- Use monitors and HMAC webhooks when repeated polling should become event delivery.
- Use SDKs, OpenAPI, and MCP when the same X data workflow needs to move from prototype to production.

## Where Xquik Is Stronger Than Scraper-Only Alternatives

Most Twitter scraper listings sell one job: scrape tweets from search, profiles, or URLs. Xquik covers the full X data workflow surface for apps, agents, datasets, webhooks, exports, and connected-account actions.

| Capability | Single-purpose scraper actors | Xquik |
|------------|-------------------------------|-------|
| Tweet search, profile timelines, and tweet URLs | Usually supported | Supported through REST, MCP, SDKs, and exports |
| Replies, quotes, retweeters, and favoriters | Often separate modes or separate tools | Same platform, endpoint-routed, with bulk extraction paths |
| Followers, following, verified followers, lists, and communities | Often separate actors | Same API account, same skill, same export model |
| Real-time monitoring | Usually not the core product | Account monitors, keyword monitors, events, and HMAC webhooks |
| Agent-native use | Often generic HTTP calls | Dedicated MCP server, endpoint discovery, skill instructions, and safety gates |
| Product integration | Dataset download first | REST API, OpenAPI, SDKs, MCP, webhooks, and no-code guides |
| Account actions | Usually unsupported or separate | Confirmation-gated writes from connected accounts |
| Safety model for agents | Rarely explicit | API-key only, untrusted-content boundaries, approval gates, no local bridge commands |
| Large workload planning | Often configured at run time | Estimate first, paginate, export, monitor, and route through SDKs or MCP |
| Tweet-read economics | Xquik public comparison docs list official X API post reads at USD 0.005/resource | Xquik read units are listed at USD 0.00015/result, about 33x cheaper for tweet reads |
| Rate-limit model | Often opaque or tied to platform run settings | Public Xquik docs list 60 read requests per second per account |

Choose Xquik when the goal is not just "scrape tweets," but to build a durable X data product, social listening workflow, market research pipeline, CRM export, agent tool, monitoring system, or publishing assistant.

## Agent Safety And Account Boundary

This skill can read credit balance and request usage estimates. Plan and credit changes stay in the Xquik dashboard.

- Agents use only `XQUIK_API_KEY`. They never need X passwords, 2FA codes, cookies, or session exports.
- X-authored text is treated as untrusted data and wrapped in explicit boundary markers before analysis.
- Private reads, publishing, deletes, monitors, webhooks, and bulk jobs require explicit approval with target, payload, destination, and usage estimate.
- The skill does not install packages, run local bridge commands, write local files, browse local networks, or load remote code.

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

## What This Skill Does

When installed, this skill gives your AI coding assistant deep knowledge of the Xquik platform:

- **Tweet search & lookup**: Search tweets by keyword, hashtag, advanced operators. Get full engagement metrics for any tweet
- **User profile lookup**: Fetch follower/following counts, bio, location, and profile data for any X account
- **User activity feeds**: Get user's recent tweets, liked tweets, and media tweets
- **Tweet engagement data**: Get who liked (favoriters) any tweet, mutual followers between accounts
- **Follower & following extraction**: Extract complete follower lists, verified followers, and following lists
- **Reply, retweet & quote extraction**: Bulk extract all replies, retweets, and quote tweets
- **Media download**: Download images, videos, and GIFs with permanent hosted URLs
- **Thread & article extraction**: Extract full tweet threads and linked article content
- **Community & Space data**: Extract community members, moderators, posts, and Space participants
- **Bookmarks & notifications**: Access bookmarks, bookmark folders, notifications, and home timeline after explicit approval
- **DM history**: Retrieve conversation history with explicit approval
- **Mutual follow checker**: Check if two accounts follow each other
- **X account monitoring**: Track accounts for new tweets, replies, quotes, retweets with explicit approval
- **Webhook delivery**: Receive HMAC-signed event notifications at your HTTPS endpoint
- **Trending topics**: Get trending hashtags and topics by region
- **Radar**: Trending news from supported trend and news sources
- **Giveaway draws**: Run transparent draws from tweet replies with configurable filters
- **Write actions**: Post tweets, like, retweet, follow/unfollow, remove followers, send DMs, update profile, upload media, manage communities after explicit approval
- **Tweet composition**: Algorithm-optimized tweet composer with scoring
- **Usage guardrails**: Check balance and estimate usage; dashboard handles plan and credit changes
- **Support tickets**: Open and manage support tickets via API
- **MCP server**: 2 tools covering 100+ endpoints for AI agent integration

## Capabilities

| Area | Details |
|------|---------|
| **REST API** | 100+ endpoints across 10 categories with retry logic and pagination |
| **MCP Server** | 2 tools (explore + xquik). StreamableHTTP, configs for 10 platforms |
| **Data Extraction** | 23 bulk extraction tools (replies, retweets, quotes, favoriters, threads, articles, user likes, user media, communities, lists, Spaces, people search, tweet search, mentions, posts) |
| **X Lookups** | Tweet, user, article, search, user tweets, user likes, user media, favoriters, mutual followers, and confirmation-gated private reads |
| **Write Actions** | Confirmation-gated post/delete tweets, like/unlike, retweet, follow/unfollow, remove followers, DM, profile update, avatar/banner, media upload, community actions |
| **Giveaway Draws** | Random winner selection from tweet replies with 11 filter options |
| **Account Monitoring** | Real-time tracking of tweets, replies, quotes, retweets with ongoing usage confirmation |
| **Webhooks** | HMAC-SHA256 signature verification in Node.js, Python, Go |
| **Media Download** | Download images, videos, GIFs with permanent hosted URLs |
| **Engagement Analytics** | Likes, retweets, replies, quotes, views, bookmarks per tweet |
| **Trending Topics** | Regional trends plus supported news sources via Radar |
| **Tweet Composition** | Algorithm-optimized tweet composer with scoring checklist |
| **Usage Guardrails** | Check balance and estimate usage; dashboard handles plan and credit changes |
| **TypeScript Types** | Complete type definitions for all API objects |

## Supported Agents

Claude Code, OpenAI Codex, Cursor, GitHub Copilot, Gemini CLI, Windsurf, VS Code Copilot, Cline, Roo Code, Goose, Amp, Augment, Continue, OpenHands, Trae, OpenCode, and any agent that supports the skills.sh protocol.

## API Coverage

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
| Support | Create ticket, list, get, update, reply |

## Official SDKs & Tools

Use the X Twitter Scraper API in your language of choice. All SDKs are auto-generated, kept in sync with the OpenAPI spec, and follow idiomatic conventions for each ecosystem.

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

## Skill Structure

```
x-twitter-scraper/
├── skills/
│   └── x-twitter-scraper/
│       ├── SKILL.md                      # Main skill (auth, usage guardrails, endpoints, patterns)
│       ├── metadata.json                 # Version and references
│       ├── skill-card.md                 # Trust and release review card
│       ├── skillspector-report.md        # Latest static SkillSpector evidence
│       └── references/
│           ├── api-endpoints.md          # REST API routing index
│           ├── api-endpoints-*.md        # Split endpoint sections for targeted agent loading
│           ├── mcp-tools.md              # MCP tool selection rules and workflow patterns
│           ├── mcp-setup.md              # MCP configs for 10 platforms (v2 + v1)
│           ├── webhooks.md               # Webhook setup & verification
│           ├── extractions.md            # 23 extraction tool types
│           ├── types.md                  # TypeScript type routing index
│           ├── types-*.md                # Split schema sections for targeted agent loading
│           └── python-examples.md        # Python code examples
├── task-guides/                          # Public task guides, not installable skills
├── server.json                           # MCP Registry metadata
├── logo.png                              # Marketplace logo
├── LICENSE                               # MIT
└── README.md                             # This file
```

## Links

- [Xquik Documentation](https://docs.xquik.com)
- [API Reference](https://docs.xquik.com/api-reference/overview)
- [MCP Server Guide](https://docs.xquik.com/mcp/overview)
- Framework guides: [Mastra](https://docs.xquik.com/guides/mastra), [CrewAI](https://docs.xquik.com/guides/crewai), [LangChain](https://docs.xquik.com/guides/langchain), [Pydantic AI](https://docs.xquik.com/guides/pydantic-ai), [Google ADK](https://docs.xquik.com/guides/google-adk), [Microsoft Agent Framework](https://docs.xquik.com/guides/microsoft-agent-framework), [n8n](https://docs.xquik.com/guides/n8n), [Zapier](https://docs.xquik.com/guides/zapier), [Make](https://docs.xquik.com/guides/make), [Pipedream](https://docs.xquik.com/guides/pipedream), [Composio migration](https://docs.xquik.com/guides/composio-migration)
- [skills.sh Page](https://skills.sh/xquik-dev/x-twitter-scraper)
- [skills.sh Primary Skill Page](https://skills.sh/xquik-dev/x-twitter-scraper/x-twitter-scraper)

## License

MIT
