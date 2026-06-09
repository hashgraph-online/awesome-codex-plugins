# X (Twitter) Scraper API Skill: Search Tweets, Get Profile Tweets, Followers, Posting & Replies

[![Ask DeepWiki](https://deepwiki.com/badge.svg?url=https%3A%2F%2Fgithub.com%2FXquik-dev%2Fx-twitter-scraper)](https://deepwiki.com/Xquik-dev/x-twitter-scraper)
<a href="https://nothumansearch.ai/site/xquik.com" target="_blank" rel="noopener"><img src="https://nothumansearch.ai/badge/xquik.com.svg" alt="NHS Agentic Readiness Score" height="28"></a>

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![GitHub stars](https://img.shields.io/github/stars/Xquik-dev/x-twitter-scraper)
[![npm version](https://img.shields.io/npm/v/x-developer.svg)](https://www.npmjs.com/package/x-developer)
[![npm downloads](https://img.shields.io/npm/dm/x-developer.svg)](https://www.npmjs.com/package/x-developer)
[![X Tweet Scraper on Apify](https://apify.com/actor-badge?actor=xquik/x-tweet-scraper)](https://apify.com/xquik/x-tweet-scraper)
[![x-twitter-scraper MCP server](https://glama.ai/mcp/servers/Xquik-dev/x-twitter-scraper/badges/score.svg)](https://glama.ai/mcp/servers/Xquik-dev/x-twitter-scraper)
[![smithery badge](https://smithery.ai/badge/xquik/x-twitter-scraper)](https://smithery.ai/servers/xquik/x-twitter-scraper)
[![Skills.sh x-twitter-scraper Skill](https://skills.sh/b/xquik-dev/x-twitter-scraper)](https://skills.sh/xquik-dev/x-twitter-scraper)

An [AI agent skill](https://skills.sh) for [Xquik](https://docs.xquik.com), a Twitter API alternative for developers who need to search tweets, get tweets from profiles, export followers, download media, monitor accounts, and automate posting workflows.

Use it for advanced Twitter search, tweet search API calls, profile tweet scraping, follower export to CSV, media download, tweet scheduling, send tweets, post replies, like, repost, follow, DM, webhooks, MCP, and official SDK workflows from AI coding agents.

Includes 100+ REST API endpoints, 2 MCP tools, HMAC webhooks, 23 bulk extraction tools, and confirmation-gated write actions.

Works with **40+ AI coding agents** including Claude Code, OpenAI Codex, Cursor, GitHub Copilot, Gemini CLI, Windsurf, VS Code, Cline, Roo Code, Goose, Amp, Augment, Continue, OpenHands, Trae, OpenCode, and more.

## Usage Costs

This installable skill can read credit balance and estimate usage costs. Users manage plan and credit changes in the Xquik dashboard.

### vs Official X API

| | Xquik | Official X API | Notes |
|---|---|---|---|
| **Access model** | **Dashboard-managed account + usage credits** | Usage-based account | This skill reads balance and estimates cost only |
| **Post reads** | Metered in usage credits | Pay-per-usage resource pricing | Estimate before running |
| **User lookup** | Metered in usage credits | Pay-per-usage resource pricing | Estimate before running |
| **Trend reads** | Metered in usage credits | Pay-per-usage resource pricing | Estimate before running |
| **Write actions** | Metered in usage credits | Pay-per-usage write pricing | Confirmation required |
| **Bulk extraction** | Metered per result in usage credits | Charged per returned resource | Built-in extraction jobs are included with Xquik |
| **Monitoring + webhooks** | Active monitors are metered; webhooks included | No direct monitor product in pricing table | Real-time delivery is included |
| **Giveaway draws** | Metered per entry in usage credits | No comparable draw product | Draw engine is included |
| **MCP server** | **Included** | Not listed | Agent tools are included |

Source: [official X API pricing](https://docs.x.com/x-api/getting-started/pricing), which lists current pay-per-usage rates.

### Per-Operation Usage Credits

| Operation | Credits |
|-----------|---------|
| Read (tweet, search, timeline, bookmarks, etc.) | 1 |
| Read (user profile, verified followers, followers you know) | 1 |
| Read (favoriters) | 1 |
| Read (trends) | 3 |
| Follow check, article | 5 |
| Write (tweet, like, retweet, follow, DM, etc.) | 10 |
| Extraction (tweets, replies, quotes, mentions, posts, likes, media, search, favoriters, retweeters, community members, people search, list members, list followers) | 1/result |
| Extraction (followers, following, verified followers) | 1/result |
| Extraction (articles) | 5/result |
| Draw | 1/entry |
| Active monitors | 21/hour |
| Webhooks, radar, compose, drafts | 0 |

### Skill Account Boundary

Only balance reads and usage estimates are in scope for this skill. Plan and credit changes are dashboard-only.

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
- **Radar**: Trending news from supported trend and news sources. Free
- **Giveaway draws**: Run transparent draws from tweet replies with configurable filters
- **Write actions**: Post tweets, like, retweet, follow/unfollow, remove followers, send DMs, update profile, upload media, manage communities after explicit approval
- **Tweet composition**: Algorithm-optimized tweet composer with scoring (free)
- **Usage credits**: Check balance and estimate costs; dashboard handles plan and credit changes
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
| **Account Monitoring** | Real-time tracking of tweets, replies, quotes, retweets with ongoing-cost confirmation |
| **Webhooks** | HMAC-SHA256 signature verification in Node.js, Python, Go |
| **Media Download** | Download images, videos, GIFs with permanent hosted URLs |
| **Engagement Analytics** | Likes, retweets, replies, quotes, views, bookmarks per tweet |
| **Trending Topics** | Regional trends plus supported news sources via Radar |
| **Tweet Composition** | Algorithm-optimized tweet composer with scoring checklist (free) |
| **Usage Credits** | Check balance and estimate costs; dashboard handles plan and credit changes |
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
| Radar | Trending topics & news from supported sources (free) |
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

| Repo | Language | Install | Stars |
|------|----------|---------|-------|
| [x-twitter-scraper-typescript](https://github.com/Xquik-dev/x-twitter-scraper-typescript) | TypeScript / Node.js | `npm i x-twitter-scraper` | ![Stars](https://img.shields.io/github/stars/Xquik-dev/x-twitter-scraper-typescript?style=flat-square) |
| [x-twitter-scraper-python](https://github.com/Xquik-dev/x-twitter-scraper-python) | Python | `pip install x-twitter-scraper` | ![Stars](https://img.shields.io/github/stars/Xquik-dev/x-twitter-scraper-python?style=flat-square) |
| [x-twitter-scraper-go](https://github.com/Xquik-dev/x-twitter-scraper-go) | Go | `go get github.com/Xquik-dev/x-twitter-scraper-go` | ![Stars](https://img.shields.io/github/stars/Xquik-dev/x-twitter-scraper-go?style=flat-square) |
| [x-twitter-scraper-ruby](https://github.com/Xquik-dev/x-twitter-scraper-ruby) | Ruby | `gem install x-twitter-scraper` | ![Stars](https://img.shields.io/github/stars/Xquik-dev/x-twitter-scraper-ruby?style=flat-square) |
| [x-twitter-scraper-java](https://github.com/Xquik-dev/x-twitter-scraper-java) | Java | Build from source while Maven Central publication is pending | ![Stars](https://img.shields.io/github/stars/Xquik-dev/x-twitter-scraper-java?style=flat-square) |
| [x-twitter-scraper-kotlin](https://github.com/Xquik-dev/x-twitter-scraper-kotlin) | Kotlin | Build from source while Maven Central publication is pending | ![Stars](https://img.shields.io/github/stars/Xquik-dev/x-twitter-scraper-kotlin?style=flat-square) |
| [x-twitter-scraper-csharp](https://github.com/Xquik-dev/x-twitter-scraper-csharp) | C# / .NET | `dotnet add package XTwitterScraper` | ![Stars](https://img.shields.io/github/stars/Xquik-dev/x-twitter-scraper-csharp?style=flat-square) |
| [x-twitter-scraper-php](https://github.com/Xquik-dev/x-twitter-scraper-php) | PHP | `composer require xquik/x-twitter-scraper` | ![Stars](https://img.shields.io/github/stars/Xquik-dev/x-twitter-scraper-php?style=flat-square) |
| [x-twitter-scraper-cli](https://github.com/Xquik-dev/x-twitter-scraper-cli) | CLI | Build from source or install a pinned release tag | ![Stars](https://img.shields.io/github/stars/Xquik-dev/x-twitter-scraper-cli?style=flat-square) |
| [terraform-provider-x-twitter-scraper](https://github.com/Xquik-dev/terraform-provider-x-twitter-scraper) | Terraform | Build from source ([release page](https://github.com/Xquik-dev/terraform-provider-x-twitter-scraper/releases)) | ![Stars](https://img.shields.io/github/stars/Xquik-dev/terraform-provider-x-twitter-scraper?style=flat-square) |
| [tweetclaw](https://github.com/Xquik-dev/tweetclaw) | OpenClaw plugin | `openclaw plugins install @xquik/tweetclaw` | ![Stars](https://img.shields.io/github/stars/Xquik-dev/tweetclaw?style=flat-square) |

## Skill Structure

```
x-twitter-scraper/
├── skills/
│   └── x-twitter-scraper/
│       ├── SKILL.md                      # Main skill (auth, pricing, endpoints, patterns)
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
├── glama.json                            # Glama.ai directory metadata
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
