# PostEverywhere for OpenAI Codex: Social Media Scheduler Plugin

[PostEverywhere](https://posteverywhere.ai) is a [social media scheduler](https://posteverywhere.ai/social-media-scheduler). This OpenAI Codex plugin lets you write, schedule and publish social media posts to [Instagram](https://posteverywhere.ai/instagram-scheduler), [TikTok](https://posteverywhere.ai/tiktok-scheduler), [YouTube](https://posteverywhere.ai/youtube-scheduler), [LinkedIn](https://posteverywhere.ai/linkedin-scheduler), [Facebook](https://posteverywhere.ai/facebook-scheduler), [X](https://posteverywhere.ai/x-scheduler), [Threads](https://posteverywhere.ai/threads-scheduler), [Pinterest](https://posteverywhere.ai/pinterest-scheduler), [Bluesky](https://posteverywhere.ai/bluesky-scheduler), Telegram, Discord and WordPress from OpenAI Codex, plan a [content calendar](https://posteverywhere.ai/content-calendar), cross-post video and see how every post performed.

No API key and nothing to install: it connects to the hosted PostEverywhere MCP server, and you sign in once in your browser.

## What you can ask OpenAI Codex

- "Post this announcement to LinkedIn and X tomorrow at 9am."
- "Turn this changelog into a week of posts for X, Threads and Bluesky."
- "Cross-post this video to TikTok, Instagram Reels and YouTube Shorts."
- "What did I post last week, and which post did best?"
- "Why didn't my TikTok post go out? Fix it."

## Install

- **Codex plugin:** add this repository (`posteverywhere/codex-plugin`) as a plugin source in Codex, then install **posteverywhere**.
- **Agent Skills only:** `npx skills add posteverywhere/codex-plugin`.
- **MCP server:** add a remote MCP server named `posteverywhere` with the URL `https://mcp.posteverywhere.ai/mcp`.

The first time you use it, sign in to PostEverywhere to connect. You need a PostEverywhere account with a plan or an active free trial: [start here](https://posteverywhere.ai/pricing).

## What's included

**The PostEverywhere MCP server** (`https://mcp.posteverywhere.ai/mcp`) gives OpenAI Codex tools to list your social accounts, create, schedule and publish posts, upload media from a link, manage campaigns and the posting queue, read analytics and retry failed posts. Every tool is annotated as read-only or destructive, and posts can be saved as drafts so nothing goes live until you approve it.

**15 skills** that teach OpenAI Codex how to use those tools well:

| Skill | What it does |
|---|---|
| [`schedule-social-posts`](skills/schedule-social-posts/SKILL.md) | Writes a post for each platform's rules, shows you a draft, and schedules or publishes it after you confirm |
| [`plan-content-calendar`](skills/plan-content-calendar/SKILL.md) | Plans a week or month of posts around a goal and creates them as drafts for review |
| [`review-post-performance`](skills/review-post-performance/SKILL.md) | Summarises how your posts performed and suggests what to try next |
| [`fix-failed-posts`](skills/fix-failed-posts/SKILL.md) | Finds posts that failed, explains why, fixes the cause and retries |
| [`connect-social-accounts`](skills/connect-social-accounts/SKILL.md) | Connects a new social account or reconnects one that stopped working |
| [`repurpose-content`](skills/repurpose-content/SKILL.md) | Turns a blog post, article, transcript or notes into a set of posts for each platform |
| [`brand-voice`](skills/brand-voice/SKILL.md) | Learns how you write from your published posts and writes a short voice guide for you to confirm |
| [`launch-announcement`](skills/launch-announcement/SKILL.md) | Plans a launch, event or offer as a multi-day campaign: teaser, launch day, reminder and last call |
| [`cross-post-video`](skills/cross-post-video/SKILL.md) | Posts one video to TikTok, Instagram Reels, YouTube Shorts, LinkedIn and Facebook Reels, with a caption for each |
| [`recycle-top-posts`](skills/recycle-top-posts/SKILL.md) | Finds your best past posts and schedules fresh versions of them, spaced out |
| [`approval-workflow`](skills/approval-workflow/SKILL.md) | Saves posts as drafts for review, makes the changes asked for, and schedules them after approval |
| [`weekly-report`](skills/weekly-report/SKILL.md) | Writes a short weekly or monthly report, ready to paste into an email |
| [`agency-clients`](skills/agency-clients/SKILL.md) | Keeps each client's accounts and posts apart, and confirms the client before every action |
| [`write-x-thread-or-article`](skills/write-x-thread-or-article/SKILL.md) | Writes an X thread or a long-form X Article (X Premium) |
| [`write-blog-post`](skills/write-blog-post/SKILL.md) | Writes a WordPress blog post with a title, tags, categories and images, as a draft or live |

## Supported networks

[Instagram](https://posteverywhere.ai/instagram-scheduler), [TikTok](https://posteverywhere.ai/tiktok-scheduler), [YouTube](https://posteverywhere.ai/youtube-scheduler), [LinkedIn](https://posteverywhere.ai/linkedin-scheduler), [Facebook](https://posteverywhere.ai/facebook-scheduler), [X](https://posteverywhere.ai/x-scheduler), [Threads](https://posteverywhere.ai/threads-scheduler), [Pinterest](https://posteverywhere.ai/pinterest-scheduler), [Bluesky](https://posteverywhere.ai/bluesky-scheduler), Telegram, Discord and WordPress. See all [features](https://posteverywhere.ai/features) and [integrations](https://posteverywhere.ai/integrations).

## Other ways to use PostEverywhere with AI

- **Claude (Claude.ai, Desktop, Claude Code):** [posteverywhere/claude-plugin](https://github.com/posteverywhere/claude-plugin)
- **Cursor:** [posteverywhere/cursor-plugin](https://github.com/posteverywhere/cursor-plugin)
- **Gemini CLI:** [posteverywhere/gemini-cli-extension](https://github.com/posteverywhere/gemini-cli-extension)
- **Grok:** [posteverywhere/grok-plugin](https://github.com/posteverywhere/grok-plugin)
- **GitHub Copilot and VS Code:** [posteverywhere/copilot-plugin](https://github.com/posteverywhere/copilot-plugin)
- **MCP server (any MCP client):** [posteverywhere/mcp](https://github.com/posteverywhere/mcp)
- **CLI:** [posteverywhere/cli](https://github.com/posteverywhere/cli)
- **Node.js SDK:** [posteverywhere/sdk](https://github.com/posteverywhere/sdk)
- **Python SDK:** [posteverywhere/posteverywhere-python](https://github.com/posteverywhere/posteverywhere-python)
- **n8n:** [posteverywhere/n8n-nodes-posteverywhere](https://github.com/posteverywhere/n8n-nodes-posteverywhere)
- **Zapier:** [posteverywhere/zapier-posteverywhere](https://github.com/posteverywhere/zapier-posteverywhere)
- **Examples:** [posteverywhere/examples](https://github.com/posteverywhere/examples)

Docs: [posteverywhere.ai/mcp](https://posteverywhere.ai/mcp) and [posteverywhere.ai/docs](https://posteverywhere.ai/docs).

## Data and privacy

This plugin contains only instructions (skills) and the address of the PostEverywhere MCP server. It runs no code on your computer. When you use it, OpenAI Codex sends the text, links and media you ask to post to PostEverywhere at `mcp.posteverywhere.ai`, over HTTPS, signed in as you. PostEverywhere publishes to the social networks you choose, only when you ask. Read the [privacy policy](https://posteverywhere.ai/privacy) and [terms](https://posteverywhere.ai/terms).

## Support

Email support@posteverywhere.ai or read the [documentation](https://posteverywhere.ai/docs).

## License

MIT. See [LICENSE](LICENSE).
