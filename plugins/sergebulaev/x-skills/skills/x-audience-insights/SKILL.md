---
name: x-audience-insights
description: Read your X (Twitter) audience and niche from real data. Pull a handle's recent tweets (yours or a competitor's) with likes, replies, and views, see which formats and hooks are working, read the repliers on a tweet (X gates likers, so repliers are the signal), and scan a niche query for top tweets. Powered by Apify, no login. Triggers on "analyze my tweets", "what is working on X", "read the replies", "competitor tweets", "who is engaging". Not for writing a tweet (use x-post-writer).
---

# X Audience Insights

Turn real X data into a read on what is working: which of your tweets landed and why, who is replying, and what the accounts in your niche are doing right now. This is the read layer, so the skill sees actual numbers instead of guessing.

One honest limit: X gates the list of who **liked** a tweet, so a full liker roster is not reliably available. The signal here is **repliers + tweet performance**, which on X carries the real conversation anyway.

## When to use

- "Analyze my last tweets / what is working for me"
- "Read the replies on this tweet"
- "What are [competitor / accounts in my niche] posting"
- "Scan the niche for top tweets on [topic]"

Not for writing a tweet (use `x-post-writer`) or a thread (use `x-thread-builder`).

## Setup (optional)

The read layer uses **Apify** (no login, no cookies). Get a free token at `https://console.apify.com/account/integrations` and set `APIFY_TOKEN`. The X actor costs about $0.15 per 1,000 tweets. No token? Paste the tweets or replies and the skill runs the same analysis on them.

## Input

- A handle (yours or a competitor's), a tweet URL, or a niche query
- Optional: the goal (what is working / competitor read / niche scan)

## Output

1. **Performance read** - the handle's recent tweets ranked by engagement, with the pattern behind the top ones (hook shape, length, format)
2. **Replier read** - who replied on a tweet, recurring questions, repliers worth a follow-back or a reply
3. **Niche scan** - top tweets for a query, the formats that travel right now
4. **Action list** - what to write more of, who to engage, what to reply to

## Steps

1. **Pull the data.** For a handle: `lib.ApifyClient().fetch_user_tweets(handle, max_items=30)`. For a tweet's repliers: `fetch_tweet_replies(tweet_url)`. For a niche: `fetch_niche_top(query, sort="Top")`. Falls back to pasted data if no token.
2. **Rank by engagement.** Sort by likes + replies + views. Normalize against the author's follower count so a small account's breakout is not buried under a big account's average.
3. **Extract the pattern.** For the top tweets, name what they share: the hook shape (one-liner, data-point, confession), the length, single vs thread, the presence of a specific number. That is the repeatable part.
4. **Read the repliers.** Cluster replies into questions, agreement, and pushback. Recurring questions are content ideas; high-follower repliers are follow-back candidates; real questions with traction are reply candidates.
5. **Scan the niche.** From `fetch_niche_top`, surface the formats and angles that are traveling now (note when search returns thin, and lean on known-account pulls instead).
6. **Build the action list.** Write-more-of (the winning pattern), engage (specific repliers/accounts), reply-now (questions with traction). Route drafts to `x-post-writer` / `x-reply-drafter`.
7. **Deliver the report** in the Output shape, with the raw ranked tweets attached.

## What the read layer exposes

| Method | Returns |
|---|---|
| `fetch_user_tweets(handle, max_items)` | recent tweets: text, likes, replies, reposts, views, author followers, url |
| `fetch_tweet_replies(tweet_url, max_items)` | replies on a tweet (the engagement signal, since likers are gated) |
| `fetch_niche_top(query, max_items, sort)` | top/latest tweets for a niche query |

## Hard rules

Global voice rules: see root `SKILL.md` Voice rules. Additional skill-specific rules:

- Be honest that this reads **repliers, not likers** (X gates like-visibility). Do not imply a full liker roster.
- **Normalize engagement by follower count** before calling a tweet a winner, or you extract "big account" effects, not "good tweet" effects.
- Never invent a tweet, a number, or a pattern. If the search returns thin, say so and pull known accounts instead.
- A pattern is only a pattern if it recurs across several top tweets, not one.

## Related skills

- `x-post-writer` - write more of what the data shows is working
- `x-reply-drafter` - reply to a high-traction question the read surfaced
- `x-hook-extractor` - reverse-engineer a hook from a top-performing tweet
- `x-content-planner` - feed the winning patterns into a weekly plan
