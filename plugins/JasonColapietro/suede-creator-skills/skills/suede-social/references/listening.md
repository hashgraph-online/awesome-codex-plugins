# Social Listening & Engagement Triage

How to surface posts that may merit an engagement draft. The goal is a short,
scorable list bounded by the user's review capacity, not a mandatory daily
count or an instruction to engage.

## Contents
- When to use this
- The daily triage loop
- Scoring rubric
- Comment quality tiers
- Sources & light tooling (curl recipes)
- Per-platform notes
- Common workflows

---

## When to Use This

Use listening when the goal is **commenting and relationships**, not posting. Typical asks:
- "Give me a ranked set of posts that may merit comment drafts"
- "Who's complaining about [competitor] right now?"
- "Find people asking for a tool like mine"
- "Surface recent posts from my approved target-account set"
- "What's the conversation around [topic] this week?"

If the user wants to **create** content, return to `suede-social`. Listening
feeds creation by surfacing angles, language, and objections, but the output is
different.

---

## The Daily Triage Loop

A repeatable triage loop sized to the user's selected lookback, source volume,
and review capacity.

1. **Pull**: fetch new posts from defined sources (target accounts, keywords, subreddits, hashtags). See [tooling](#sources--light-tooling-curl-recipes).
2. **Filter**: remove off-topic or stale items using a lookback justified by
   current platform velocity and the campaign goal.
3. **Score**: apply the [rubric](#scoring-rubric) and retain only the bounded
   review set the user can assess.
4. **Draft**: for each, draft a comment matched to the post's tier.
5. **Approval gate**: return drafts for review. Each comment is a separate
   external action and requires exact-content and identity approval before post.
6. **Log**: track what you commented on and what got replies. This is your engagement loop dataset.

Output format Suede should produce:

```
RANKED ENGAGEMENT DRAFTS: 2026-06-05

1. [Score 9/10] @author: LinkedIn: 2h ago
   "We just rolled out X and the team is loving it…"
   Why: ICP fit (B2B SaaS, 50–200 employees), buying-intent signal
   Suggested comment: [draft]
   Link: https://…
```

---

## Scoring Rubric

Score each post 1–10 across five dimensions, then sum and rank.

| Dimension | What it measures | Weight |
|-----------|------------------|--------|
| **ICP fit** | Is the author your target customer / influencer? | 2x |
| **Intent signal** | Are they expressing a problem, asking, or shopping? | 2x |
| **Reach potential** | Is the post getting traction (likes/comments rising)? | 1x |
| **Comment opportunity** | Can you say something genuinely useful, not generic? | 2x |
| **Recency** | Source falls inside the user-selected lookback and is still actionable | 1x |

**Intent signal examples (high-value):**
- "Looking for a tool that does X"
- "Why is [category] so painful?"
- "We just switched from [competitor] because…"
- "Anyone use [competitor]: is it worth it?"
- A complaint about a known competitor

**Drop if any of these are true:**
- Author isn't ICP and isn't an influencer
- The post is outside the justified lookback or current conversation volume
  makes a useful contribution unlikely; record the evidence rather than using a
  fixed age or comment-count cutoff
- Generic motivational/AI-slop post
- Self-promotion thread where a comment would not add relevant value
- You can't add anything beyond "Great post!"

---

## Comment Quality Tiers

Match the comment to the post. Don't waste a tier-1 draft on a tier-3 opportunity.

**Tier 1. Relationship builder (target accounts, ICP, high intent)**
- Add a specific insight or counter-example
- Reference your own experience with specifics (numbers, names, outcomes)
- Ask a thoughtful follow-up that invites a reply
- Length: 2–4 sentences, no link

**Tier 2. Visibility test (observed reach when visible, adjacent topic)**
- Add one sharp insight in one sentence
- Pattern: "Agreed: and the part most miss is [X]"
- Length: 1–2 sentences

**Tier 3. Light touch (relationship maintenance)**
- Specific reaction, not "Love this"
- Quote a specific line and react to it
- Length: 1 sentence

**Never:** "Great post!", emoji-only, "+1", LinkedIn-isms like "This is gold 🔥"

---

## Sources & Light Tooling (curl recipes)

These example endpoints may change and can still impose terms or rate limits.
Verify current access and source terms before use. Prefer already callable
readers; otherwise give the user a manual source checklist.

The shell examples use `jq` and, for RSS, `xmllint`. First check whether they are
already installed. If not, use a manual/RSS-reader fallback or request explicit
installation approval after confirming the current platform and package source.
Do not run these installation examples without that approval:
```bash
# macOS
brew install jq
# xmllint ships with macOS; on Linux: apt install libxml2-utils
```

### Reddit (free, scriptable)

**New posts in a subreddit:**
```bash
curl -s -A "listening/1.0" \
  "https://www.reddit.com/r/SaaS/new.json?limit=25" \
  | jq '.data.children[].data | {title, author, url: ("https://reddit.com"+.permalink), score, num_comments, created_utc, selftext: (.selftext | .[0:300])}'
```

**Search across Reddit by keyword (last day, sorted new):**
```bash
curl -s -A "listening/1.0" \
  "https://www.reddit.com/search.json?q=KEYWORD&sort=new&t=day&limit=25" \
  | jq '.data.children[].data | {subreddit, title, url: ("https://reddit.com"+.permalink), author, score, created_utc}'
```

Swap `KEYWORD` for things like `"alternative to notion"`, `"recommend a crm"`, your competitor names, or your own brand for mentions. Use quotes around multi-word phrases.

### Hacker News (Algolia search)

**Recent stories mentioning a keyword (last 24h):**
```bash
SINCE=$(($(date +%s) - 86400))
curl -s "https://hn.algolia.com/api/v1/search_by_date?query=KEYWORD&tags=story&numericFilters=created_at_i>${SINCE}" \
  | jq '.hits[] | {title, url, author, points, num_comments, created_at, story_id: .objectID, hn_url: ("https://news.ycombinator.com/item?id="+.objectID)}'
```

**Recent comments mentioning a keyword:**
```bash
curl -s "https://hn.algolia.com/api/v1/search_by_date?query=KEYWORD&tags=comment&numericFilters=created_at_i>${SINCE}" \
  | jq '.hits[] | {author, comment_text, story_title, hn_url: ("https://news.ycombinator.com/item?id="+.objectID)}'
```

### Bluesky (free, public API)

**Search posts by keyword:**
```bash
curl -s "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts?q=KEYWORD&limit=25&sort=latest" \
  | jq '.posts[] | {author: .author.handle, text: .record.text, likes: .likeCount, replies: .replyCount, url: ("https://bsky.app/profile/"+.author.handle+"/post/"+(.uri | split("/") | last))}'
```

### RSS for blogs, podcasts, YouTube channels

For target accounts that publish to RSS (most blogs, all YouTube channels):
```bash
# YouTube channel feed (replace CHANNEL_ID)
curl -s "https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID"

# Generic blog feed
curl -s "https://example.com/feed/" | xmllint --xpath "//item[position()<6]" - 2>/dev/null
```

### LinkedIn & X: discover access, then review

First discover whether an authorized browser or source-reading connector is
currently callable. Confirm the signed-in identity, user authorization, and
platform terms before opening an authenticated surface.

**Authorized-tool workflow:**
1. Confirm the visible account identity and exact research scope.
2. Open a bounded set of target URLs.
3. Read only the public or user-authorized content needed for the rubric.
4. Record source URL, timestamp, and any missing metrics.
5. Draft comments for review; never post or engage automatically.

**Manual fallback:** if no authorized browser is available, give the user the
URL checklist below and a worksheet, then work from links, screenshots, copied
post text, or exports they provide. Do not claim the feed was reviewed.

**Useful URL patterns to verify before use:**

| URL pattern | What it shows |
|-------------|---------------|
| `linkedin.com/in/HANDLE/recent-activity/all/` | A target account's recent posts |
| `linkedin.com/feed/hashtag/TOPIC/` | Hashtag feed |
| `linkedin.com/feed/` | Signed-in feed when the user authorizes access |
| `x.com/HANDLE` | A target account's profile |
| `x.com/search?q=QUERY&f=live` | Real-time search (use `f=live` for chronological) |
| `x.com/i/lists/LIST_ID` | A user-curated target-account list |

**Starting hypotheses:**
- A user-curated list may reduce irrelevant posts; compare it with keyword
  search and record which produces more rubric-qualified candidates.
- A target account's recent-activity surface may be easier to audit than a
  mixed feed; verify the URL still works and record gaps.
- Load only enough posts to cover the chosen lookback and sample. Stop at the
  authorization or platform limit; do not automate infinite scrolling.

**Possible account-owned alternatives, only if the user already has access:**

| Platform | Tools |
|----------|-------|
| LinkedIn | Sales Navigator (saved searches), Taplio (engagement) |
| X | TweetDeck/X Pro (saved columns), Typefully, Taplio, Tweet Hunter |

If a platform does not expose an authorized research path, use its native saved
searches manually or ask for a user export. Do not route around access controls.

---

## Per-Platform Notes

### LinkedIn
- Use the authorized-tool workflow or manual fallback above.
- Compare recent and older posts in the same account before assigning a recency
  score; do not assume a first-hour advantage.
- Judge draft comments on relevance, specificity, and conversation value, not a
  word-count or reach claim.
- Treat replies to other commenters as a relationship tactic to test, not a
  distribution guarantee.
- Tag the author in your reply only if it adds context

### Twitter/X
- Use the authorized-tool workflow or manual fallback above.
- Compare response windows using current account results; do not claim a
  universal first-30-minute advantage.
- Test quote posts, replies, and original commentary against the intended
  outcome rather than ranking them universally.
- Use a multi-post reply only when the content needs the space.
- Don't pile on dunks: relationships > clout

### Reddit
- Read the subreddit rules before commenting (some ban self-promotion outright)
- Earn karma in the sub before linking to anything you own
- Prefer specific answers that resolve the question; compare response quality
  rather than assuming length earns distribution.
- Never lead with your product: answer the question first

### Hacker News
- Comment quality bar is high; low-effort gets downvoted fast
- Founders commenting on threads about their product is welcomed if you're transparent
- Search past category discussions and verify that they are still current
  enough to answer.

### Bluesky
- Record volume and engagement-to-follower ratio where both are visible; do not
  assume either predicts fit.
- Tech and indie-hacker communities are active
- Compare custom feeds with topic search when both are available.

---

## Common Workflows

### "Give me a ranked set of posts that may merit comments"
1. Pull from the approved source set using a lookback justified by current
   platform velocity
2. Score with the [rubric](#scoring-rubric)
3. Output a review-capacity-bounded set with suggested comment drafts

### "Find people complaining about [competitor]"
1. Reddit search: `"competitor name" -site:competitor.com` sorted by new
2. HN comment search for competitor name
3. Bluesky search for competitor handle/name
4. Score by intent signal (high if switching language: "moving from", "alternatives to", "frustrated with")

### "Surface brand mentions from the last week"
1. Reddit search for brand name
2. HN search (stories + comments) for brand name
3. Bluesky search for brand name + handle
4. Output as: reply needed (yes/no), tone (positive/negative/neutral), suggested response

### "Find target-account posts I missed"
1. Maintain a list of target accounts with their RSS / Reddit usernames / Bluesky handles
2. Fetch each source's recent posts
3. Apply the justified lookback and output the bounded set sorted by score

---

## Setting Up the Source List

The user may maintain an approved source list at
`.agents/listening-sources.md` (or `.claude/listening-sources.md`). Suede reads
it when running the triage loop.

**A ready-to-fill template lives at [listening-sources-template.md](listening-sources-template.md).** Copy it into the project and edit. The source path depends on how the skill was installed:

```bash
# Plugin / marketplace install (most common):
cp .agents/skills/suede-social/references/listening-sources-template.md .agents/listening-sources.md
# .claude/ install:
cp .claude/skills/suede-social/references/listening-sources-template.md .agents/listening-sources.md
# Working inside the Suede creator skills repo:
cp skills/suede-social/references/listening-sources-template.md .agents/listening-sources.md
```

The template covers: brand/category, ICP (for scoring), target accounts per platform, intent keywords, subreddits, saved-search URLs, and a do-not-engage list.
