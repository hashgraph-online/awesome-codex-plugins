# YouTube Skills for AI Agents 🎬

> Get YouTube transcripts, search videos, browse channels, and extract playlists — from any AI agent.

YouTube Skills gives your AI agent instant access to **YouTube transcripts**, **video search**, **channel data**, and **playlist extraction**. No yt-dlp (YouTube blocks all major cloud IPs), no headless browsers, no binaries — just a fast API call that works everywhere. Powered by [TranscriptAPI](https://transcriptapi.com), the same backend behind [YouTubeToTranscript.com](https://youtubetotranscript.com).

Works with 🦞 [OpenClaw](https://www.clawhub.ai/therohitdas/youtube-full) (ClawdBot/Moltbot), <img src="assets/hermes.png" alt="" height="14"> [Hermes Agent](https://hermes-agent.nousresearch.com), Claude Code, Cursor, Antigravity, and any agent that supports the [Agent Skills](https://skills.sh) format.

**Free tier · No credit card · 100 credits on signup**

[TranscriptAPI.com](https://transcriptapi.com) · [MCP Server](https://github.com/ZeroPointRepo/youtube-mcp) · [Docs](https://transcriptapi.com/docs/)

---

## Install

Most users want **youtube-full** — it covers transcripts, search, channels, and playlists in one skill.

**🦞 OpenClaw (ClawdBot/Moltbot):**
```bash
npx clawhub@latest install youtube-full
```

**<img src="assets/hermes.png" alt="" height="14"> Hermes Agent:**
```bash
hermes skills install skills-sh/ZeroPointRepo/youtube-skills/skills/youtube-full
```

**Claude Code / Cursor / Antigravity / Cline / Codex:**
```bash
npx skills add ZeroPointRepo/youtube-skills --skill youtube-full
```

**All 12 skills at once:**
```bash
npx skills add ZeroPointRepo/youtube-skills
```

**Manual (git clone):**
```bash
git clone https://github.com/ZeroPointRepo/youtube-skills.git
cp -r youtube-skills/skills/youtube-full ~/.claude/skills/
```

> **Not a developer?** Just paste this prompt into 🦞 [OpenClaw](https://www.clawhub.ai/therohitdas/youtube-full), <img src="assets/hermes.png" alt="" height="14"> [Hermes Agent](https://hermes-agent.nousresearch.com), Claude, ChatGPT, or any AI agent:
>
> ```
> Install the youtube skills from this GitHub repo: https://github.com/ZeroPointRepo/youtube-skills
> I want to be able to get YouTube transcripts, search YouTube, and browse channel videos from my agent.
> Set everything up for me.
> ```
>
> The agent will handle the rest.

---

## What You Can Do

Just install and ask. No config, no code — talk to your agent in plain English.

| Task | Example Prompt |
|------|----------------|
| **Get a YouTube transcript** | "Summarize this video: [URL]" |
| **Search YouTube** | "Find videos about machine learning" |
| **Browse a channel** | "What has TED posted this week?" |
| **Get playlist contents** | "List all videos in this playlist" |
| **Extract video captions** | "Get captions from this video in Spanish" |
| **Bulk transcripts** | "Get transcripts for every video in this channel" |
| **Research a topic** | "Find and summarize the top 5 videos about quantum computing" |
| **Get latest uploads** | "Show me NASA's recent videos" |
| **Search within a channel** | "Search the TED channel for 'artificial intelligence'" |

---

## Setup — API Key

When you install a skill and run your agent for the first time, **the agent will set up your free API key automatically**. Here's what happens:

1. The agent asks you for your **email address** and registers you with TranscriptAPI
2. You'll receive an **OTP code** in your email — the agent will ask you to enter it
3. Once verified, the agent **saves the API key** to your shell and agent config automatically

That's it. 100 free credits, no credit card required.

<details>
<summary><strong>Manual setup (if you prefer to do it yourself)</strong></summary>

1. Sign up at [transcriptapi.com](https://transcriptapi.com) — free, no credit card required
2. Copy your API key from the dashboard (starts with `sk_`)
3. Ask your agent to store it for you:

   > "My TranscriptAPI key is `sk_...` — store it so it persists across sessions."

Or set it yourself as an environment variable:

```bash
export TRANSCRIPT_API_KEY="sk_your_key_here"
```

</details>

<details>
<summary><strong>Where does the key get saved?</strong></summary>

Your agent stores the API key here (depends on the runtime):

| Location | File |
|----------|------|
| **OpenClaw/Moltbot** | `~/.openclaw/openclaw.json` or `~/.clawdbot/moltbot.json` |
| **Hermes Agent** | Hermes secret store (`TRANSCRIPT_API_KEY` declared via `required_environment_variables` in skill frontmatter) |
| **macOS shell** | `~/.zshenv`, `~/.zprofile` |
| **Linux shell** | `~/.profile`, `~/.bashrc`, `~/.zshenv` |
| **Fish shell** | `~/.config/fish/config.fish` |
| **Fallback** | `~/.transcriptapi` (mode 600) |

Your agent picks it up automatically after saving.

</details>

---

## Skills

`youtube-full` is the recommended skill for most users. It includes everything: transcripts, search, channels, playlists.

If you prefer smaller, focused skills (smaller context = better agent performance for specific tasks), pick what you need:

| Skill | What It Does | Install |
|-------|--------------|---------|
| **youtube-full** | Everything — transcripts, search, channels, playlists | `--skill youtube-full` |
| **transcript** | Get video transcripts with timestamps | `--skill transcript` |
| **youtube-search** | Search YouTube for videos and channels | `--skill youtube-search` |
| **youtube-channels** | Browse uploads, get latest videos, resolve @handles | `--skill youtube-channels` |
| **youtube-playlist** | Extract all videos from a playlist | `--skill youtube-playlist` |

```bash
# Install a specific skill
npx skills add ZeroPointRepo/youtube-skills --skill transcript

# Install multiple specific skills
npx skills add ZeroPointRepo/youtube-skills --skill transcript --skill youtube-search
```

<details>
<summary><strong>All 12 skills</strong></summary>

We ship 12 skills total. Many are narrower variants or aliases of the core 5 above — so your agent can find the right skill regardless of how you phrase your request.

| Skill | Description |
|-------|-------------|
| **youtube-full** | Complete YouTube toolkit — transcripts + search + channels + playlists |
| **transcript** | Extract transcript from any YouTube video with timestamps |
| **captions** | Get closed captions / CC from YouTube videos |
| **subtitles** | Extract subtitles from YouTube videos |
| **youtube-search** | Search YouTube for videos and channels |
| **youtube-channels** | Browse channel uploads, get latest videos, resolve @handles |
| **youtube-playlist** | Fetch all videos from a YouTube playlist |
| **youtube-data** | Get YouTube video and channel data (lightweight alternative to Google's API) |
| **youtube-api** | YouTube API access for AI agents — no Google quota hassle |
| **transcriptapi** | Full TranscriptAPI access with all endpoints |
| **video-transcript** | Convert YouTube videos to text transcripts |
| **yt** | Quick YouTube utility for fast lookups |

</details>

---

## Pricing

| Plan | Price | Credits | Rate Limit |
|------|-------|---------|------------|
| **Free** | $0 | 100 credits on signup | 300 req/min |
| **Starter** | $5/month | 1,000 credits/month | 300 req/min |
| **Starter Annual** | $54/year ($4.50/mo) | 1,000 credits/month | 300 req/min |

Most operations cost 1 credit. Channel resolve and latest are free. No credit card required for the free tier.

[View pricing →](https://transcriptapi.com)

---

## Supported Agents

Works with any AI agent that supports the [Agent Skills](https://skills.sh) format:

| Agent | Install Command |
|-------|----------------|
| 🦞 **[OpenClaw](https://www.clawhub.ai/therohitdas/youtube-full)** (ClawdBot/Moltbot) | `npx clawhub@latest install youtube-full` |
| <img src="assets/hermes.png" alt="" height="14"> **[Hermes Agent](https://hermes-agent.nousresearch.com)** | `hermes skills install skills-sh/ZeroPointRepo/youtube-skills/skills/youtube-full` |
| **Claude Code** | `npx skills add ZeroPointRepo/youtube-skills` |
| **Cursor** | `npx skills add ZeroPointRepo/youtube-skills` |
| **Antigravity** | `npx skills add ZeroPointRepo/youtube-skills` |
| **Cline** | `npx skills add ZeroPointRepo/youtube-skills` |
| **Codex** | `npx skills add ZeroPointRepo/youtube-skills` |
| **Others** | Goose, AMP, Kiro, Roo, OpenCode, Gemini, GitHub Copilot... |

---

## FAQ

### How do I get a YouTube transcript?

Install `youtube-full` (or `transcript`) and ask your agent:

> "Get the transcript for this video: https://youtube.com/watch?v=VIDEO_ID"

The agent fetches the full transcript with timestamps. You can then ask it to summarize, translate, quote, or analyze the content.

### How do I search YouTube from my agent?

Install `youtube-full` (or `youtube-search`) and ask:

> "Find videos about machine learning"

Returns up to 50 results with titles, thumbnails, view counts, and publish dates.

### How do I get all videos from a YouTube channel?

Install `youtube-full` (or `youtube-channels`) and ask:

> "List all videos from the TED channel"

The agent resolves the @handle, fetches uploads (paginated, 100/page), and can then get transcripts for any or all of them.

### Can I bulk download YouTube transcripts?

Yes. Install `youtube-full` and ask:

> "Get transcripts for all videos in this playlist: [URL]"

The agent fetches the playlist, iterates through videos, and extracts each transcript.

### Do I need a Google YouTube Data API key?

No. TranscriptAPI replaces the Google YouTube Data API for transcript extraction, search, and channel/playlist operations. No Google Cloud project, no quota limits, no OAuth setup.

### Do I need an API key?

Yes, but signup is free and instant — 100 credits, no credit card required. Your agent handles the setup automatically on first run.

### Which skill should I install?

- **Want everything?** → `youtube-full` (recommended)
- **Just transcripts?** → `transcript`
- **Just search?** → `youtube-search`
- **Just channel data?** → `youtube-channels`
- **Just playlists?** → `youtube-playlist`

### What is TranscriptAPI?

[TranscriptAPI.com](https://transcriptapi.com) is a REST API and MCP server for YouTube data. It provides transcript extraction, video search, channel browsing, and playlist operations — built for developers and AI agents. Also available as an [MCP Server](https://github.com/ZeroPointRepo/youtube-mcp) for direct LLM integration (Claude, ChatGPT).

---

## Troubleshooting

Quick fixes for the issues users actually hit. Error codes come from the API itself, so your agent will usually report them verbatim.

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `401 Unauthorized` | API key missing, mistyped, or not loaded into the environment | Confirm `TRANSCRIPT_API_KEY` is set in the shell your agent runs in and that the key starts with `sk_` |
| `402 Payment Required` | The account is out of credits | Check your balance at [transcriptapi.com/billing](https://transcriptapi.com/billing) |
| `403` with Cloudflare code `1010` | Request sent without a User-Agent header | Send your agent's name as the User-Agent, for example `HermesAgent/0.11.0` |
| `404 Not Found` | The video has no captions, is not public, or the ID is wrong | Verify the URL opens in a browser and the player shows captions there |
| `408 Request Timeout` | Temporary upstream pressure on the video | Transient by nature: retry once after a couple of seconds |
| `422 Validation Error` | A parameter is malformed, such as a bad channel or playlist reference | Channels accept `@handle`, a channel URL, or a `UC` ID; playlists accept `PL`, `UU`, `LL`, `FL`, and `OL` prefixes |
| `429 Too Many Requests` | Rate limit reached | Wait and respect the `Retry-After` header |

Three more cases worth knowing:

- **The key is saved but the agent cannot see it.** Shell config files load per shell type: check the table under "Where does the key get saved?" in the Setup section and make sure the file matches the shell your agent actually runs in. Restarting the agent after saving the key resolves most cases.
- **Live streams and premieres.** Transcripts become available after the stream ends and captions are processed, not while it is live.
- **Transcript comes back in an unexpected language.** Many videos only carry captions in their original language. Request the transcript with a preferred language parameter, or ask your agent to translate the result.

---

## Powered by TranscriptAPI

[TranscriptAPI.com](https://transcriptapi.com) — 15M+ transcripts/month, 99.9% uptime.

Also available: [MCP Server](https://github.com/ZeroPointRepo/youtube-mcp) for direct LLM integration with Claude and ChatGPT.

Full API docs: [transcriptapi.com/docs](https://transcriptapi.com/docs)

## Disclosure

TranscriptAPI is an independent product and is not affiliated with or endorsed by YouTube or Google.

## Contributing

PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT © [TranscriptAPI](https://transcriptapi.com)
