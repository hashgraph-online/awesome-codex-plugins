# Groundsocial research skills

Agent skills for social media research: brand mentions, competitor audits, creator vetting, subreddit research,
TikTok trends, YouTube transcripts and comment mining. They work in Claude Code, Codex, Cursor, Gemini CLI and any
agent that reads the [Agent Skills](https://agentskills.io) format.

Each skill is a workflow, not just an API reference: which calls to make, in what order, what to look for in the
results and what the final brief should contain. The data comes from [Groundsocial](https://groundsocial.dev), one
API and MCP server for public data from 80+ platforms (Reddit, X, TikTok, Instagram, YouTube, LinkedIn, Hacker News,
GitHub, Google and more).

## Skills

| Skill | Ask your agent | Typical cost |
|---|---|---|
| [brand-mention-scan](skills/brand-mention-scan/SKILL.md) | "What are people saying about Supabase this week?" | 10-40 credits |
| [competitor-social-audit](skills/competitor-social-audit/SKILL.md) | "Audit Linear's socials and tell me what content works for them" | 20-60 credits |
| [creator-vetting](skills/creator-vetting/SKILL.md) | "Is @creator's engagement real? Should we sponsor them?" | 15-70 credits |
| [subreddit-research](skills/subreddit-research/SKILL.md) | "Which subreddits should I post my self-hosted tool in, and what are their rules?" | 10-50 credits |
| [tiktok-trend-scan](skills/tiktok-trend-scan/SKILL.md) | "What's trending on TikTok in the US this week for fitness creators?" | 5-30 credits |
| [youtube-transcript-research](skills/youtube-transcript-research/SKILL.md) | "Summarize what YouTubers say about the new Pixel, with timestamps" | 10-40 credits |
| [comment-mining](skills/comment-mining/SKILL.md) | "Pull the objections and questions from the comments on this video" | 1-20 credits |
| [groundsocial-api](skills/groundsocial-api/SKILL.md) | Anything else: auth, finding endpoints, pagination, errors | - |

One credit is one standard read. New accounts get 100 free credits, then packs start at $10 for 10,000 credits.
Failed calls are not charged.

## Install

With the [skills CLI](https://github.com/vercel-labs/skills):

```bash
npx skills add shivanshmehendiratta/groundsocial-skills                 # all skills
npx skills add shivanshmehendiratta/groundsocial-skills --skill creator-vetting
```

As a Claude Code plugin (also connects the Groundsocial MCP server):

```text
/plugin marketplace add shivanshmehendiratta/groundsocial-skills
/plugin install groundsocial-skills@groundsocial-skills
```

Or copy any folder under `skills/` into `~/.claude/skills/` (or your agent's skills directory).

## Set up access

Either:

- **REST:** get a key at [groundsocial.dev](https://groundsocial.dev/app/sign-in?new=1) and
  `export GROUNDSOCIAL_API_KEY=gs_live_...`. Agents without a person around can sign themselves up; see
  [groundsocial-api](skills/groundsocial-api/SKILL.md).
- **MCP:** connect `https://api.groundsocial.dev/mcp` (OAuth or the API key as a Bearer token). The skills use the
  MCP tools when they're available.

## Check it works

```bash
GROUNDSOCIAL_API_KEY=gs_live_... ./scripts/smoke.sh   # one cheap call per skill, about 40 credits; needs curl and jq
```

## Notes

- Read-only. Nothing here posts, votes, follows or messages.
- Public, logged-out data only. Respect each platform's terms and people's privacy when you use the results.
- Issues and pull requests welcome, especially new research workflows.

## License

MIT
