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

Pay per call, no subscription; a call that ends in an error is not charged. Every skill states its prices and opens
with a recorded answer, so your agent knows what comes back before it spends anything.

**Jobs**: each makes a table and a report from it, across the platforms that have the data:

| Skill | Use it when you want... | You get |
|---|---|---|
| `comment-analysis` | what people praise, complain about and ask under a video, note or post (评论分析) | Comment table; themes, questions, buying intent, quotes |
| `competitor-monitoring` | what competitors posted lately and which post took off (竞品账号监测) | Posts table; medians, posts that beat them, patterns |
| `brand-mentions` | what is said about a brand or keyword on several platforms (品牌与关键词舆情) | Posts table; volume by platform, themes, tone |
| `trending-topics` | what is trending now on Douyin, Weibo, Xiaohongshu, Bilibili and more (各平台热榜) | Board table; cross-platform topics, angles |
| `account-audit` | how one account is doing (账号体检) | Profile and posts table; pace, engagement, best and worst posts |
| `viral-post-breakdown` | why a post took off (爆款拆解) | Figures and transcript; hook, structure, a template |
| `influencer-search` | creators to work with in a category (达人筛选) | Accounts table; shortlist with fit scores |
| `video-transcripts` | what videos say, as text (视频转文字) | Transcript table; summaries, hooks, quotes |
| `ad-library-research` | the ads a brand or category runs on Meta, TikTok, LinkedIn (广告素材拆解) | Ads table; longest running, angles, offers, tests |
| `product-research` | what sells and what buyers say (选品与评价分析) | Products and reviews table; praise, complaints, the opening |

**One job on one platform**: the endpoints customers call most, each with its parameters, prices and calls:

| Skill | What it does |
|---|---|
| `xiaohongshu-note-search` | 小红书笔记搜索: search Xiaohongshu (RedNote) notes by keyword, then the full text |
| `xiaohongshu-comments` | 小红书评论采集: a note's comments and replies |
| `xiaohongshu-creator` | 小红书博主资料与笔记: find accounts, a creator's profile and notes |
| `xiaohongshu-trends` | 小红书热点话题: the hot topics right now |
| `xiaohongshu-keyword-index` | 小红书关键词搜索指数: a keyword's search index by day, and related keywords (PGY) |
| `douyin-video-search` | 抖音视频搜索: search Douyin videos by keyword |
| `douyin-video-detail` | 抖音视频详情与播放量: one video's figures and play count |
| `douyin-comments` | 抖音评论采集: a video's comments and replies |
| `douyin-creator` | 抖音博主资料与作品: find accounts, a creator's profile and videos |
| `douyin-index` | 抖音巨量算数指数: keyword index by day, related words, hot videos |
| `douyin-hot-search` | 抖音热搜榜与视频榜: the hot search board and video boards |
| `wechat-article-export` | 公众号文章导出: an Official Account's articles, any article's full text and reads |
| `wechat-search` | 微信搜一搜: articles and videos by keyword, Official Accounts by name |
| `wechat-channels-videos` | 视频号视频搜索与作品: search Channels videos, an account's videos |
| `weibo-search` | 微博实时搜索: Weibo posts by keyword, newest first |
| `bilibili-video-search` | B站视频搜索: Bilibili videos by keyword |

**Every endpoint of a platform**: `dataxapi-douyin` (抖音), `dataxapi-xiaohongshu` (小红书 / RedNote),
`dataxapi-tiktok`, `dataxapi-wechat` (微信搜一搜), `dataxapi-wechat-mp` (微信公众号), `dataxapi-wechat-channels` (视频号),
`dataxapi-kuaishou` (快手), `dataxapi-bilibili` (B站), `dataxapi-weibo` (微博), `dataxapi-zhihu` (知乎), `dataxapi-x`,
`dataxapi-youtube`, `dataxapi-instagram`, `dataxapi-facebook`, `dataxapi-threads`, `dataxapi-reddit`,
`dataxapi-linkedin`, `dataxapi-telegram`, `dataxapi-pinterest`, `dataxapi-meta` (Meta Ad Library), `dataxapi-google`
(Google Ads).

**The base skill**, `dataxapi`: find the right endpoint for any need, see its price, call it, read the rest of a long
result.

One skill: `npx skills add data-x-api/skills --skill douyin-comments`.

This repository is generated from our catalog and overwritten at every release; questions and bugs: open an issue.

## Links

[Skills on dataxapi.com](https://dataxapi.com/skills/) · [Pricing](https://dataxapi.com/pricing/) ·
[Docs](https://dataxapi.com/docs/) · [MCP](https://dataxapi.com/mcp/) · [SDKs and docs](https://github.com/data-x-api/dataxapi)

## 中文

给 Claude Code、Codex、Cursor 等 agent 用的 DataXAPI 技能：抖音、小红书等平台的市场数据（抖音、小红书、TikTok、微信公众号和视频号、快手、B站、微博、知乎、X、YouTube 等），一次 $0.0003 起，调用失败不收费，新账户免费试用，最多 333 次，不用绑卡。按次付费，不用订阅，出错不收费。10 个办事技能（评论分析、竞品账号监测、品牌与关键词舆情、各平台热榜、账号体检、爆款拆解、达人筛选、视频转文字、广告素材拆解、选品与评价分析），每个交回一张表和一份报告；16 个单平台技能（小红书笔记搜索、抖音评论采集、公众号文章导出、巨量算数指数等）；每个平台一个全接口技能；一个基础技能。安装：`npx skills add data-x-api/skills`；技能调用 `dataxapi` 命令行，看计划免费、不用 Key，真正运行要 `DATAXAPI_API_KEY`。

## Licence

MIT
