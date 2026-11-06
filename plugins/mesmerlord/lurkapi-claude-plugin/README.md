# LurkAPI: social media research skills for AI agents

Ask for the outcome, not the endpoint. These skills teach Claude, Codex, Cursor and any agent that reads [Agent Skills](https://agentskills.io) to run whole research jobs on live public data: lurk a brand, tear down its ads across four ad libraries, mine Reddit, vet a creator, read any video, size up demand.

They run on [LurkAPI](https://lurkapi.com), which scrapes TikTok, Instagram, YouTube, Reddit, X (Twitter), Facebook, LinkedIn, Threads, Bluesky and more into clean JSON. No proxies, headless browsers or blocked IPs on your side. Public pages only: it never logs in to anyone's account.

![LurkAPI](./logo.png)

## Install

**Claude Code**: the plugin, with the skills and the LurkAPI MCP server.

```bash
claude plugin marketplace add mesmerlord/lurkapi-claude-plugin && claude plugin install lurkapi@lurkapi
```

Then run `/mcp`, pick `plugin:lurkapi:lurkapi` and choose **Authenticate**. A LurkAPI page opens: sign in with Google or your email, or create a free account in the same step, and click **Allow**. Claude gets its own API key, named after it, so there's nothing to copy or paste.

**Claude and Cowork**: add **LurkAPI** from the directory in [Customize → Plugins](https://claude.ai/customize/plugins). It reaches Claude Code too.

**Gemini CLI**: the extension, with the skills and the MCP server. Run `/mcp auth lurkapi` in Gemini CLI to sign in.

```bash
gemini extensions install https://github.com/mesmerlord/lurkapi-claude-plugin
```

**Kiro**: in the Powers panel, choose **Add Custom Power**, then **Import power from GitHub** with `https://github.com/mesmerlord/lurkapi-claude-plugin`.

**Codex, Cursor, Copilot and others**: the skills, which call the API with curl.

```bash
npx skills add mesmerlord/lurkapi-claude-plugin
export LURKAPI_API_KEY=...   # from https://lurkapi.com/dashboard
```

## Skills

| Skill | Ask it | You get |
| --- | --- | --- |
| [`lurk`](skills/lurk/SKILL.md) | "Lurk Allbirds." | Whether a brand advertises right now on Meta and Google, what its live ads push, and its Facebook, Instagram and TikTok audience. Four calls, the run behind the LurkAPI dashboard. |
| [`ad-research`](skills/ad-research/SKILL.md) | "Tear down Gymshark's ads." | Live ads from the Meta, Google, LinkedIn and TikTok libraries, the long-running winners, angles, verbatim hooks, offers, landing pages and tests to run. TikTok's EU library adds who each ad targeted and reached. |
| [`reddit-research`](skills/reddit-research/SKILL.md) | "What does Reddit say about Notion vs Obsidian?" | The communities that discuss it, the most-argued threads, and the pains, alternatives, objections and exact phrases people use, each linked. |
| [`creator-vetting`](skills/creator-vetting/SKILL.md) | "Should we sponsor @username?" | Median views, reach and engagement against the creator's own baseline, bought-follower and one-hit checks, sponsorship load, audience comments and a go or no-go. |
| [`video-transcripts`](skills/video-transcripts/SKILL.md) | "What are this channel's last 10 videos about?" | Transcripts of YouTube videos and Shorts, TikToks and Instagram reels, turned into summaries, hooks, claims, quotes and scripts. |
| [`demand-research`](skills/demand-research/SKILL.md) | "Is there demand for collagen gummies?" | What people type into Google and TikTok Shop, what sells on eBay and for how much, attention on TikTok and YouTube, Reddit's complaints and news momentum, with a verdict. |
| [`lurkapi`](skills/lurkapi/SKILL.md) | Anything else | Which of the 80+ endpoints answers a question, with its params and price. |

## Why these skills

- **Real calls, checked.** Every tool, param, value and response field a skill names is checked against LurkAPI's registry before each release, so the plan an agent follows always matches the API.
- **They know the price.** Each skill lists what its calls cost and budgets the run in calls; for big runs the agent checks your balance first and tells you the cost.
- **Ad libraries nobody else chains.** Meta's Ad Library, Google's Ads Transparency Center, LinkedIn's Ad Library and TikTok's EU library, with targeting and reach where it's published.
- **Made for agents.** Over MCP, results come trimmed (no nulls, one URL per image), long ones in parts. Over curl, the skills tell the agent which fields to keep.
- **Fast.** On the busiest endpoints, the median answer takes 0.4 to 1.2 seconds; cached ones come back in tens of milliseconds.

## Cost

Most calls cost 1 credit; each skill's table gives the price of every call it makes, and every answer shows your balance. A call that reaches the platform is charged even when the thing isn't found; failures on our side are free. New accounts get 100 free credits, a balance below 25 tops back up to 25 every day, and packs start at $9 for 10,000 credits that never expire. See [pricing](https://lurkapi.com/pricing).

## Data

The plugin has no local code. It registers one remote MCP server, `https://api.lurkapi.com/mcp`, which you connect by signing in to LurkAPI with OAuth; LurkAPI then creates an API key for Claude, which you can revoke in your [dashboard](https://lurkapi.com/dashboard) to disconnect. The skills are instructions only: when an agent follows one, the parameters of each call (a username, a video URL, a search keyword) go to LurkAPI, which fetches the matching public pages and returns them as JSON. LurkAPI returns only publicly available data.

LurkAPI logs each call (endpoint, parameters, result code, credits; never your key) and what it returned (up to its first megabyte), so you can open any recent call in your dashboard. The log is deleted after 14 days and the responses a day later. See the [privacy policy](https://lurkapi.com/privacy) and [terms](https://lurkapi.com/terms).

## Support

Email [support@lurkapi.com](mailto:support@lurkapi.com) or open an [issue](https://github.com/mesmerlord/lurkapi-claude-plugin/issues). Docs for every endpoint: [lurkapi.com/docs](https://lurkapi.com/docs). LurkAPI is made by Mesmer s.r.o.

## License

MIT
