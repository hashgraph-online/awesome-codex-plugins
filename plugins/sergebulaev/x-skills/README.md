<p align="center">
  <img src="assets/hero.png" alt="X (Twitter) marketing skills for Claude Code and Codex, open source MIT licensed" width="900" />
</p>

# X (Twitter) Marketing Skills for Claude Code and Codex

<p align="center">
  <img src="https://img.shields.io/github/v/release/sergebulaev/x-skills?color=111827&label=release" alt="Latest release">
  <img src="https://img.shields.io/badge/Claude_Code-Compatible-D97757?logo=anthropic&logoColor=white" alt="Claude Code Compatible">
  <img src="https://img.shields.io/badge/Codex-Compatible-111827" alt="Codex Compatible">
  <img src="https://img.shields.io/badge/Claude-Skills-8A63D2" alt="Claude Skills">
  <img src="https://img.shields.io/badge/License-MIT-22C55E.svg" alt="MIT License">
  <img src="https://img.shields.io/github/stars/sergebulaev/x-skills?style=social" alt="GitHub stars">
  <img src="https://img.shields.io/badge/PRs-welcome-F59E0B.svg" alt="PRs Welcome">
</p>

> **Part of the [linkedin-skills](https://github.com/sergebulaev/linkedin-skills) family (400+ stars).** Same voice engine and approve-before-publish flow, now for X. Also available for [Instagram](https://github.com/sergebulaev/instagram-skills) · [YouTube](https://github.com/sergebulaev/youtube-skills) · [TikTok](https://github.com/sergebulaev/tiktok-skills) · [Threads](https://github.com/sergebulaev/threads-skills) · [Facebook](https://github.com/sergebulaev/facebook-skills).

**9 skills that turn Claude Code and Codex into your X (Twitter) content team.** They write tweets and threads in your voice with corpus-validated hooks, extract the hook from any viral tweet, draft replies and quote tweets, and plan a week of content. Every draft gets the AI tells stripped and waits for your approval before anything publishes. No coding required.

Once installed, just ask Claude Code or Codex things like:

- "Write a tweet about [topic]"
- "Turn these notes into a thread"
- "What's working in my niche on X right now? (reads real data via Apify)"
- "Rewrite this tweet so it doesn't sound like AI"

The right skill activates automatically. Then you review and approve.

## Install

Pick whichever way you use Claude Code or Codex:

### Codex CLI

```bash
codex plugin marketplace add sergebulaev/x-skills
codex plugin add x-skills@x-skills
```

To test a local clone before publishing changes:

```bash
git clone https://github.com/sergebulaev/x-skills.git
cd x-skills
codex plugin marketplace add .
codex plugin add x-skills@x-skills
```

### claude.ai (web)

1. Open https://claude.ai/code
2. Go to **Skills** in the sidebar
3. Click **Add from GitHub**
4. Paste: `sergebulaev/x-skills`
5. Done. The skills activate automatically when you ask about X or Twitter.

### Claude Desktop (Mac / Windows)

1. Open Claude Desktop
2. Open **Settings** (gear icon)
3. Go to **Skills**
4. Click **Add from GitHub**
5. Paste: `sergebulaev/x-skills`
6. Done. Start a new conversation and ask Claude to write a tweet.

### Claude Code (CLI / VS Code / JetBrains)

```
/plugin marketplace add sergebulaev/x-skills
/plugin install x-skills@x-skills
```

Or clone the repo and open it as your working directory:

```bash
git clone https://github.com/sergebulaev/x-skills.git
cd x-skills
```

### OpenClaw

1. Open your OpenClaw working directory
2. Clone the skills into it:
   ```bash
   git clone https://github.com/sergebulaev/x-skills.git
   ```
3. In OpenClaw settings, add this to your system prompt:
   ```
   You have X (Twitter) marketing skills in ./x-skills/.
   For any X (Twitter) task, read the relevant skills/*/SKILL.md first.
   Use lib/url_parser.py for URL parsing and lib/publora_client.py for publishing.
   ```
4. Done. Ask OpenClaw to write a X (Twitter) post.

### Hermes Agent

Hermes Agent (Nous Research) follows the agentskills.io open standard and loads `skills/*/SKILL.md` directly. Clone the bundle into your Hermes skills folder:

```bash
git clone https://github.com/sergebulaev/x-skills.git ~/.hermes/skills/x-skills
```

Coming from OpenClaw? `hermes claw migrate` imports these skills automatically. Then call `/<skill-name>` from any of your Hermes chat surfaces.

### Any agent (skills CLI)

One command that works across Claude Code, Codex, Cursor, and any other agent that reads SKILL.md files:

```bash
npx skills add sergebulaev/x-skills
```

> **Found this useful? [Star the repo](https://github.com/sergebulaev/x-skills).** Curated Claude Code and Codex directories rank and gate by star count, so a star is what makes these skills findable for the next person. It is the only thing we ask. No signup, no email.

## What you can do

Once installed, just ask Claude Code or Codex for help with X. The right skill activates automatically.

**Write a tweet:**
> "Write me a tweet about why most AI agents fail on retries, not reasoning. Make it sharp."

**Turn an idea into a thread:**
> "Turn my notes into a thread on how we cut agent latency from 9s to 2.1s."

**Check a draft before posting:**
> "Audit this tweet for AI tells and the 280-char limit: [paste your text]"

**Reverse-engineer a viral tweet:**
> "What hook does this thread use? https://x.com/someone/status/123 (I'll paste the text)"

**Reply to a creator:**
> "Draft a reply to this tweet, I want to add value not dunk: https://x.com/someone/status/123"

**Plan your week:**
> "Plan a week of X content. I'm building an AI agent in public for indie devs."

Every skill shows you a draft first and waits for your OK. Nothing gets posted without your approval.

## The 9 skills

| Skill | What it does |
|---|---|
| **Post Writer** | Drafts a single tweet (or short auto-thread) using a 2026 X hook formula picked by goal: replies, reposts, likes, or bookmarks. Respects the 280-char limit (25,000 on Premium) |
| **Thread Builder** | Builds long-form tweetstorms (listicle, story, curiosity-gap, how-I teardown). Structures tweet 1 as a promise plus open loop, front-loads value, closes for the repost |
| **Humanizer** | Strips em dashes, AI vocabulary ("leverage", "delve", "harness"), rule-of-three lists, and uniform tweet rhythm. Bundles a `--mode audit` pre-publish check (280-char fit, hook, hashtags, link placement) |
| **Hook Extractor** | Reverse-engineers the hook from any viral tweet or thread. Maps it to one of the 11 X formulas and returns a blank template you can fill |
| **Reply Drafter** | Drafts a reply or a value-add quote tweet for any tweet URL. Decides reply vs quote tweet. X has no LinkedIn-style thread flattening, so a reply is just a tweet |
| **Content Planner** | Creates a weekly plan with a single-to-thread mix, per-day hooks, posting times, daily reply targets, and a goal-mix balance check |
| **Repurposer** | Turns content from another platform (LinkedIn post, blog, YouTube script, newsletter) into a native X tweet or thread: re-hooks for the no-fold first line, refits to 280 or a thread, strips off-platform artifacts, runs the humanizer |
| **Profile Optimizer** | Audits and rewrites your X profile for 2026: bio (160 chars), searchable display name, header, pinned tweet, and link. Turns a default profile into one that converts visitors into followers |
| **Audience Insights** | Reads your X audience and niche from real Apify data: your/competitor tweets ranked by engagement, the pattern behind the winners, the repliers on a tweet (X gates likers), and a niche scan. No login |

## How threads work on X

X caps a standard tweet at **280 characters** (emoji count as 2 each), or **25,000** on X Premium. For anything longer, you build a thread. Doing that on the native X API means posting tweet 1, capturing its id, posting tweet 2 as a reply to it, and handling partial failures.

This bundle hands the whole chain to [Publora](https://publora.com). You write the thread as one block (or split it with `---`), and Publora auto-splits it into a numbered `(1/N)` thread at sentence boundaries, reserves room for the marker, and posts it in one call. The Thread Builder and Post Writer skills use this on approval.

## Optional: auto-post with Publora

By default, the skills draft content for you to copy-paste into X. If you want Claude Code or Codex to publish tweets and threads directly, connect Publora. It takes about 2 minutes.

### What is Publora?

[Publora](https://publora.com) is a publishing API that turns one `create-post` call into a full X thread (and can cross-post the same content to LinkedIn, Threads, and more).

### Setup (2 minutes)

**Step 1.** Sign up at https://app.publora.com/signup (free)

**Step 2.** Connect X: click **Channels** in the left sidebar, then **Add Channel**, pick **X / Twitter**, authorize.

**Step 3.** Find your Platform ID: go to **Channels**, click your X account. The ID looks like `twitter-123456789`. Copy the whole thing including `twitter-`.

**Step 4.** Get your API key: click **Settings** (gear icon, bottom-left), then **API**, then **Create Key**. Copy the `sk_...` string.

**Step 5.** Create a file called `.env` in the x-skills folder:

```
PUBLORA_API_KEY=sk_paste_your_key_here
X_PLATFORM_ID=twitter-paste_your_id_here
```

If you cloned the repo, copy the template instead:

```bash
cp .env.example .env
```

Then open `.env` and replace the placeholders with your real values.

**Step 6.** Install two small Python packages:

```bash
pip install requests python-dotenv
```

**Step 7.** Test it. Ask Claude Code or Codex:

> "Schedule a test tweet via Publora 24 hours from now: 'testing the API connection, will cancel in dashboard'."

If Publora returns a `postGroupId`, you're set. Cancel the post in the Publora dashboard before the scheduled time. If you get HTTP 401, your API key is wrong. If you get a `Invalid platform ID format` error, your `X_PLATFORM_ID` is wrong. See [Troubleshooting](#troubleshooting).

> **Note on replies:** X has no reply endpoint on Publora, so the Reply Drafter always returns its draft as a copy-paste block for you to post yourself. Single tweets and threads auto-publish.

## Optional: generate illustrations with Pixfaro

A tweet with a visual gets more engagement. The Post Writer can generate an inline image or a quote-card of your hook and attach it automatically when publishing. Without a key it drafts the image prompt and asks you to generate it yourself, so nothing breaks.

[Pixfaro](https://pixfaro.com) is a single image API over multiple models (from `flux-schnell` at $0.004 to `gpt-5-image`). It composites your handle, brand color, or logo onto the image as a **pixel-exact overlay**, so a cheap base model still renders crisp text on a quote-card. Pull those brand fields from your [Voice & Brand Profile](references/voice-profile.md) (section 6) and every asset stays on-brand.

Setup: drop `PIXFARO_TOKEN=pf_live_...` into your `.env`. The thin client at `lib/pixfaro_client.py` and the wrappers `lib.illustrate(prompt, kind="wide")` / `lib.refine(image_id, instruction)` return a hosted URL that flows straight into `lib.publish(..., media_urls=[url])`. `refine` edits a prior image by its id (cheaper than regenerating); results carry `cost`, `balance_after`, and a `premium` flag so the skills never quietly spend on a pricey model.

## Voice rules

Every skill follows these rules automatically:

1. No em dashes. Biggest AI tell in 2026.
2. Capitalize names. Always. Lowercase a brand reads as careless.
3. No AI vocabulary: "leverage", "fundamentally", "streamline", "harness", "delve", "unlock", "foster".
4. Specific numbers beat adjectives. "2.4x" beats "way better".
5. One idea per tweet. The first line carries everything (no "see more" fold on X).
6. 280 chars per tweet on a standard account (emoji = 2 each). 0-1 hashtag, 0-1 emoji.

## Troubleshooting

| Problem | Fix |
|---|---|
| Skills don't activate when I ask about X | Make sure you installed via the Skills panel, `/plugin install`, or `codex plugin add`. Try a new conversation. |
| "PUBLORA_API_KEY not set" | Your `.env` file is missing or in the wrong folder. It should be in the `x-skills/` root. |
| "401 Invalid API key" from Publora | Your API key is wrong or revoked. Go to Publora Settings > API > Create a new key. |
| "Invalid platform ID format" | Your `X_PLATFORM_ID` is wrong. Go to Publora Channels and copy the full `twitter-...` string. |
| My tweet got cut off / split unexpectedly | Emoji count as 2 chars on X. A 278-char tweet with two emoji is over 280, so Publora splits it. Tighten it or make it a deliberate thread. |
| My reply didn't auto-post | X replies have no Publora endpoint by design. The Reply Drafter returns a copy-paste block. Post it yourself. |
| `pip install` fails | Use a virtual environment: `python -m venv venv && source venv/bin/activate && pip install requests python-dotenv` |

## Cross-cutting references

- [`references/hook-formulas.md`](references/hook-formulas.md) - the 11 X hook formulas with skeletons and goal tags
- [`references/algorithm-heuristics.md`](references/algorithm-heuristics.md) - 2026 X ranking signals, timing, and limits
- [`references/voice-rules.md`](references/voice-rules.md) - the canonical voice rules every skill inherits

---

<details>
<summary><b>For developers: runtime compatibility, URL parsing, and internals</b></summary>

## Runtime compatibility

```
x-skills/
  skills/             SKILL.md frontmatter; native to Claude Code and Codex, others read as markdown
  .codex-marketplace/ generated nested Codex package (run scripts/sync_codex_marketplace.py)
  lib/                pure Python, works in any agent runtime
  references/         pure markdown, works anywhere
  scripts/            pure Python CLI, works anywhere
```

| Runtime | Auto-discovers skills? | Setup |
|---|---|---|
| **Claude Code** (CLI, Desktop, Web, IDE) | Yes | Install via plugin or clone. Skills activate on matching prompts. |
| **Codex CLI** | Yes | `codex plugin marketplace add sergebulaev/x-skills` and `codex plugin add x-skills@x-skills`. |
| **Anthropic Managed Agents** (`/v1/agents`) | Yes | Pass skill files in the agent context. |
| **Cursor / Cline / Aider** | Manual | Read `SKILL.md` files as prompt context; import `lib/` as Python. |
| **LangChain / AutoGen** | No | Use `lib/` as a package; feed `references/` as prompt context. |

## Generic Python agent quickstart

```python
import sys; sys.path.insert(0, "path/to/x-skills")
from lib import parse_x_url, PubloraClient, publish

parsed = parse_x_url("https://x.com/paulg/status/1790000000000000000?s=20")
print(parsed["handle"], parsed["tweet_id"])  # paulg 1790000000000000000

# Write side (Publora) - a single tweet or a thread (long content auto-splits)
client = PubloraClient()  # reads PUBLORA_API_KEY from env
client.create_post(
    content="First tweet of the thread\n\n---\n\nSecond tweet\n\n---\n\nThird tweet",
    platforms=["twitter-123456789"],
)

# Or use the high-level wrapper that handles manual / Publora / diy routing
publish("thread", draft_text="...", target_url="https://x.com/compose/tweet",
        platforms=["twitter-123456789"])
```

## URL handling

`lib/url_parser.py` parses X tweet and profile URLs on both hosts:

| URL fragment | Parsed |
|---|---|
| `x.com/HANDLE/status/ID` | `{handle, tweet_id, url_type: "tweet"}` |
| `twitter.com/HANDLE/status/ID` | same (normalized to x.com) |
| `x.com/i/web/status/ID` | `{tweet_id, url_type: "tweet"}` |
| `x.com/HANDLE` | `{handle, url_type: "profile"}` |

```bash
python lib/url_parser.py "https://x.com/paulg/status/1790000000000000000"
```

## Why a reply is just a tweet

LinkedIn flattens reply threads to 2 levels and needs the top-level comment URN as the parent. X does not: replies nest naturally and there is no parent-comment URN to resolve. The Reply Drafter therefore just drafts the text. Publora has no `in_reply_to` on `create-post`, so reply publishing is a copy-paste step by design.

</details>

## References

- [Publora API docs](https://docs.publora.com) - endpoint reference for the publishing layer
- [The X recommendation algorithm](https://github.com/twitter/the-algorithm) - the open-sourced ranker behind the 2026 heuristics

## Who builds this

These skills come out of [Creative Content Crafts](https://cccrafts.ai), an engineering company. We build the machinery underneath a company's public voice: ICP parsing, engagement systems, content guardrails, and posting infrastructure. We do not sell the words themselves.

We call that layer **content engineering**. Writing collapsed to the price of a chat subscription. What stayed valuable is everything below it: pulling every post your market wrote this week, keeping a live list of the people who matter, engaging on it daily with judgment in the loop, and catching the risky drafts before the platform does.

This repo is the thin top layer of that stack, open-sourced. The engine underneath is what we build for clients.

## License

MIT. Powered by [Publora](https://publora.com).

## Related open-source skill bundles

Part of a family of AI social-media marketing skill bundles for Claude Code and Codex:

- [linkedin-skills](https://github.com/sergebulaev/linkedin-skills) - LinkedIn
- **x-skills - X (Twitter) (this repo)**
- [instagram-skills](https://github.com/sergebulaev/instagram-skills) - Instagram
- [youtube-skills](https://github.com/sergebulaev/youtube-skills) - YouTube
- [threads-skills](https://github.com/sergebulaev/threads-skills) - Threads
- [tiktok-skills](https://github.com/sergebulaev/tiktok-skills) - TikTok
- [facebook-skills](https://github.com/sergebulaev/facebook-skills) - Facebook Pages

Also: [Anthropic Skills repo](https://github.com/anthropics/skills), the `awesome-claude-skills` directory.
