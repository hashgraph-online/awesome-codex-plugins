# X (Twitter) Scraper API Skill For AI Agents

An [AI agent skill](https://skills.sh) for [Xquik](https://docs.xquik.com), built for developers who need reliable X (Twitter) data workflows from coding agents. Use it to search tweets, get profile tweets, export followers, download media, monitor accounts, receive webhooks, use MCP, and prepare confirmation-gated publishing actions.

The skill gives Claude Code, OpenAI Codex, Cursor, GitHub Copilot, Gemini CLI, Windsurf, and other skills-compatible agents the exact API boundaries, endpoint choices, safety rules, and workflow steps they need for X data automation.

Includes 100+ REST API endpoints, 2 MCP tools, HMAC webhooks, 23 bulk extraction tools, official SDK pointers, and confirmation-gated write actions.

## Why Use This Skill

- **Find X posts faster**: search tweets, inspect replies, quotes, retweets, favoriters, trends, and article content from one skill.
- **Understand X accounts**: fetch profile data, user tweets, likes, media, followers, following, mutuals, lists, and communities.
- **Move from one-off calls to workflows**: run follower exports, tweet search exports, media downloads, giveaway draws, monitors, and HMAC webhooks.
- **Keep agents inside clear boundaries**: read-only by default, API-key only, physical untrusted-content delimiters, and explicit approval for private reads, writes, persistent resources, and metered bulk jobs.
- **Use the right integration path**: REST API, MCP, framework guides, and SDKs are all mapped for agent use.

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
│       └── references/
│           ├── api-endpoints.md          # REST API endpoint reference
│           ├── mcp-tools.md              # MCP tool selection rules and workflow patterns
│           ├── mcp-setup.md              # MCP configs for 10 platforms (v2 + v1)
│           ├── webhooks.md               # Webhook setup & verification
│           ├── extractions.md            # 23 extraction tool types
│           ├── types.md                  # TypeScript type definitions
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
