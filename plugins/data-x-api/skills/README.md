# DataXAPI Agent Skills

Agent Skills that give Claude Code, Codex, Cursor and other agents live market data from Douyin, Xiaohongshu
(RedNote), TikTok, WeChat, X, YouTube and more through [DataXAPI](https://dataxapi.com): one response shape, paid per
call from $0.0003, failed calls free. New accounts can try it free: up to 333 calls, no card. Social media is the
largest category; creator rate cards, keyword indexes, ad libraries and shop products are the others.

Each skill is one `SKILL.md`, plain text, no scripts: its steps call the `dataxapi` command line, say how many calls a
run makes and the most it can cost, and end the output with the data's source and the time it was fetched. Planning a
run is free and needs no key; running it needs `DATAXAPI_API_KEY`.

## Install

```sh
npx skills add data-x-api/skills                 # all of them
npx dataxapi setup                             # the base skill and the MCP entry, for Claude Code, Codex and Cursor
```

Or copy a folder from `skills/` into your agent's skills directory (Claude Code: `~/.claude/skills/`). The skills need
the command line: `npm install -g dataxapi` (Node 20 or later), or `npx dataxapi`. Make a key in the
[console](https://dataxapi.com/console/keys/).

## The skills

Base skill:

| Skill | What it does |
|---|---|
| `dataxapi` | Find the right endpoint for a need, see its price, call it, read the rest of a long result |

Task skills, each across the platforms that have the data:

| Skill | The question it answers |
|---|---|
| `dataxapi-comments` | Comments and word of mouth (评论与口碑): what are people praising and complaining about under this post? |
| `dataxapi-competitors` | Competitor account monitoring (竞品账号监测) |
| `dataxapi-mentions` | Keyword search and mentions (关键词搜索与提及) |
| `dataxapi-trends` | Trends and topics (热点与选题) |
| `dataxapi-account-audit` | Account check-up (账号体检) |
| `dataxapi-viral` | Breaking down a hit (爆款拆解) |
| `dataxapi-creators` | Finding accounts and creators (找号与达人筛选) |
| `dataxapi-transcripts` | Videos to text (视频转文字) |
| `dataxapi-ads` | Ad creatives (广告素材拆解) |
| `dataxapi-products` | Products and reviews (商品与评价) |

Platform skills, one per platform, with every endpoint it has and what to watch for: `dataxapi-douyin` (抖音),
`dataxapi-xiaohongshu` (小红书 / RedNote), `dataxapi-tiktok`, `dataxapi-wechat` (微信搜一搜), `dataxapi-wechat-mp` (微信公众号),
`dataxapi-wechat-channels` (视频号), `dataxapi-kuaishou` (快手), `dataxapi-bilibili` (B站), `dataxapi-weibo` (微博),
`dataxapi-zhihu` (知乎), `dataxapi-x`, `dataxapi-youtube`, `dataxapi-instagram`, `dataxapi-facebook`,
`dataxapi-threads`, `dataxapi-reddit`, `dataxapi-linkedin`, `dataxapi-telegram`, `dataxapi-pinterest`,
`dataxapi-meta` (Meta Ad Library), `dataxapi-google` (Google Ads).

This repository is generated from our catalog and overwritten at every release; questions and bugs: open an issue.

## Links

[Skills on dataxapi.com](https://dataxapi.com/skills/) · [Pricing](https://dataxapi.com/pricing/) ·
[Docs](https://dataxapi.com/docs/) · [MCP](https://dataxapi.com/mcp/) · [SDKs and docs](https://github.com/data-x-api/dataxapi)

## 中文

给 Claude Code、Codex、Cursor 等 agent 用的 DataXAPI 技能：抖音、小红书等平台的市场数据（抖音、小红书、TikTok、微信公众号和视频号、快手、B站、微博、知乎、X、YouTube 等），一次 $0.0003 起，调用失败不收费，新账户免费试用，最多 333 次，不用绑卡。一个基础技能、10 个任务技能（评论与口碑、竞品监测、关键词与提及、热点与选题、账号体检、爆款拆解、找号与达人、视频转文字、广告素材、商品与评价）、每个平台一个平台技能。安装：`npx skills add data-x-api/skills`；技能调用 `dataxapi` 命令行，看计划免费、不用 Key，真正运行要 `DATAXAPI_API_KEY`。

## Licence

MIT
