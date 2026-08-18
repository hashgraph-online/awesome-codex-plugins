---
name: x-marketing
description: Plan, draft, audit, and publish posts and threads for X (Twitter). Use when the user wants to write a single tweet or an auto-numbered thread, build a long-form tweetstorm, remove AI tells from a draft, reverse-engineer the hook from a viral tweet, draft a reply or quote tweet, or plan a week of X content. Tweets and threads publish via the Publora API, which auto-splits long content into a numbered thread. User provides notes or a tweet URL, the skill drafts, the user approves, then it publishes.
---

# X (Twitter) Marketing Skills

A bundle of 9 focused skills for X content ops in 2026. Each skill is
single-purpose, follows the draft then approval then publish pattern, and uses
the [Publora API](https://publora.com) for posting tweets and threads.

## When to use this bundle

- **Writing a single tweet or an auto-thread** -> use `x-post-writer`
- **Building a long-form tweetstorm** (listicle / story / build-in-public) -> use `x-thread-builder`
- **Removing AI tells from a draft, or auditing it before posting** -> use `x-humanizer` (rewrite plus `--mode audit` pre-publish review, which folds in the post-audit sub-tool)
- **Reverse-engineering the hook from a viral tweet or thread** -> use `x-hook-extractor`
- **Drafting a reply in a thread, or a quote tweet** -> use `x-reply-drafter`
- **Planning a week of X content** -> use `x-content-planner`
- **Adapting content from another platform into a native X post or thread** -> use `x-repurposer`
- **Auditing and rewriting your X profile (bio, name, header, pinned tweet)** -> use `x-profile-optimizer`
- **Reading your X audience and niche from real data (your tweets, repliers, competitors, top tweets)** -> use `x-audience-insights`

## Core pattern

Every action-taking skill follows three steps:

1. **Parse the input.** If the user gives a tweet URL, the skill uses
   `lib/url_parser.py` to extract the handle and tweet id.
2. **Draft the content.** The skill applies 2026 research (X hook formulas,
   timing, voice rules, ranking heuristics) and shows the draft to the user.
3. **Wait for approval.** The user replies "post", "yes", or suggests edits.
   Only after explicit approval does the skill call Publora to publish.

## Prerequisites

**Three tiers - pick one.**

### Tier 0 - Draft only (default, no setup)

The skills work out of the box. No API keys, no signup. Every approved draft is
returned as a copy-paste block with the target X URL. Great for trying the
skills before committing to any backend.

### Tier 1 - Publora auto-post (recommended, ~2 min)

On approval, the writer and thread skills auto-publish to X via the
[Publora API](https://publora.com). Pass long content and Publora auto-splits it
into a numbered `(1/N)` thread at sentence boundaries.

1. Sign up free: **https://app.publora.com/signup**
2. Connect your X account in Publora (Channels then Add Channel)
3. Copy your API key from Publora's API panel
4. Drop into `.env`:
   ```
   PUBLORA_API_KEY=sk_...
   X_PLATFORM_ID=twitter-...
   ```
5. Run `pip install -r requirements.txt`

Why Publora: a thread on the native X API means posting tweet 1, capturing its
id, posting tweet 2 as a reply, and handling partial failures. Publora does all
of that in one `create-post` call, auto-splits long content, counts emoji as 2
chars, and reserves room for the `(1/N)` marker. We built on top of it so we did
not have to reimplement the chaining.

### Tier 2 - Build your own poster (advanced)

Prefer not to SaaS it? Ask Claude Code or Codex to build a custom poster on the
X API v2. Set `X_SKILLS_CUSTOM_POSTER=<your command>` and the skills invoke it on
approval. Publora is the 2-minute path.

### Note on replies

X has no LinkedIn-style comment endpoint on Publora, and `create-post` does not
expose `in_reply_to`. So `x-reply-drafter` always returns its draft as a
copy-paste block for you to post as the reply or quote tweet yourself. Single
tweets and threads auto-publish through Publora normally.

## Voice rules (baked into every skill)

1. No em dashes (`—`), en dashes, or double dashes. Biggest AI tell.
2. Use `..` as a soft pause when rhythm calls for it.
3. Capitalize all personal, company, and product names. Lowercase a brand reads
   as careless.
4. Sentence starts can be lowercase (native X voice); names inside stay capitalized.
5. Avoid AI vocabulary: `leverage`, `fundamentally`, `streamline`, `harness`,
   `delve`, `unlock`, `foster`.
6. Specific numbers beat adjectives. 2.4x beats "way better".
7. One idea per tweet. Two ideas means two tweets, or a thread.
8. The first line carries everything. There is no "see more" fold on X.
9. 280 chars per tweet on a standard account (emoji count as 2). 25,000 on Premium, but tight beats long.
10. 0-1 hashtag, 0-1 emoji, and only when each earns its place.

(Canonical reference: `references/voice-rules.md`. See also
`references/hook-formulas.md` and `references/algorithm-heuristics.md`.)

## How X URLs map

| URL shape | Parsed to |
|---|---|
| `https://x.com/HANDLE/status/ID` | handle + tweet_id, type `tweet` |
| `https://twitter.com/HANDLE/status/ID` | same (twitter.com normalized to x.com) |
| `https://x.com/i/web/status/ID` | tweet_id only, type `tweet` |
| `https://x.com/HANDLE` | handle, type `profile` |

`lib/url_parser.parse_x_url(url)` returns `{handle, tweet_id, url_type,
canonical_url}`. A quote tweet is just a tweet URL; reply vs quote is a user
choice, not a URL distinction.

## Known gotchas

- **Emoji are 2 chars on X.** A 278-char tweet with two emoji is over the 280
  limit. Publora accounts for this when it splits.
- **External links suppress reach** in tweet 1. Move the link to a reply or to
  tweet 2+ of a thread.
- **Each tweet in a thread counts toward your X API quota.** A 5-tweet thread
  uses 5 from your monthly limit.
- **Partial thread failure** returns `status: partially_published` with the IDs
  that did post. The published tweets stay live.
- **No 2-level flattening.** Unlike LinkedIn, X replies nest naturally and there
  is no parent-comment URN to resolve.

## Resources

- [Publora API docs](https://docs.publora.com) - endpoint reference for the publishing layer
- `lib/publora_client.py` - thin Python client used by every writing skill
- `lib/url_parser.py` - X URL to handle/tweet-id parser

## Acknowledgments

Publishing powered by the [Publora REST API](https://publora.com).
