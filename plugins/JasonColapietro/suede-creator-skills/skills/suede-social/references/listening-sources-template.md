# Listening Sources: Template

Copy this file to `.agents/listening-sources.md` in your project (or
`.claude/listening-sources.md`) and fill in the brackets. Suede reads it when
running the [listening workflow](listening.md).

Delete sections you don't use. Keep this short and current: stale sources are worse than no sources.

---

## What We're Listening For

**Brand / product:** [Your product name]
**Category:** [e.g., "AI writing assistant", "Postgres GUI"]
**Goal:** [e.g., "find people switching from Notion", "engage with B2B SaaS founders 50-200 employees"]

## ICP (for scoring)

Used by the [scoring rubric](listening.md#scoring-rubric) to judge ICP fit.

- **Role:** [e.g., "founder, head of marketing, marketing ops lead"]
- **Company stage:** [e.g., "seed to Series B SaaS, 10-200 employees"]
- **Industry:** [e.g., "B2B SaaS, infra, devtools"]
- **Signals they're a fit:** [e.g., "writes about GTM, runs paid ads, recently raised"]

---

## Target Accounts

Use these accounts as a review pool. Bound each run by current source volume,
relevance, risk, and human review capacity. Draft only the highest-priority
responses; never engage automatically or treat the whole list as a quota.

### LinkedIn (authorized browser or manual review)
- [Name]: `linkedin.com/in/handle`
- [Name]: `linkedin.com/in/handle`

### X / Twitter (browser-driven)
- [@handle]
- [@handle]

### Reddit
- u/[username]
- u/[username]

### Bluesky
- [handle.bsky.social]

### Blogs / Newsletters (RSS)
- [Name]: `https://example.com/feed/`
- [Name]: `https://example.substack.com/feed`

### YouTube channels (RSS)
- [Name]: channel ID `UCxxxxxxxx`

---

## Keywords (intent signals)

Search only the platforms currently authorized and reachable. When no connector
or browser is available, use the [daily-loop](listening.md#the-daily-triage-loop)
manual query and user-supplied URL workflow.

### High-intent (someone shopping or switching)
- `"alternative to [competitor]"`
- `"looking for a [category] tool"`
- `"recommend a [category]"`
- `"switching from [competitor]"`
- `"frustrated with [competitor]"`

### Problem signals (someone in pain)
- `"[category] is so [bad/hard/expensive]"`
- `"why is [category] [problem]"`
- `"hate [pain point]"`

### Brand mentions
- `"[your brand]"`
- `"[your brand misspelling]"`
- `"[your domain]"`

### Competitor mentions (monitor for switching language)
- `"[competitor 1]"`
- `"[competitor 2]"`

---

## Subreddits

Review through a currently authorized API, browser, or manual user export.

- r/SaaS
- r/Entrepreneur
- r/[your niche, e.g., "marketing", "devtools"]
- r/[adjacent community]

---

## Saved Searches (manual / browser-driven)

URLs for an authorized browser or manual user review.

### LinkedIn Sales Navigator
- [Search name]: `https://linkedin.com/sales/search/people?...`

### LinkedIn (regular)
- Posts hashtag: `https://linkedin.com/feed/hashtag/yourtopic/`

### X advanced search
- [Search name]: `https://x.com/search?q=...&f=live`

---

## Do Not Engage

Save yourself the regret.

- Accounts known for bad-faith dunking: [@handle], [@handle]
- Blocked brands / competitors who'll screenshot: [list]
- Topics to avoid: [politics, [your founder's hot takes], etc.]

---

## Notes for the Suede agent

- When asked for a ranked set, bound the output to current source volume and
  review capacity using the format in
  [listening.md](listening.md#the-daily-triage-loop)
- For LinkedIn and X, first discover a callable authorized browser and confirm
  visible identity; otherwise use the manual URL, screenshot, or export fallback.
- For other sources, use a currently callable authorized reader or the manual
  recipes in [listening.md](listening.md#sources--light-tooling-curl-recipes).
- Ask for a lookback that matches source volume and decision urgency; if the
  user delegates, start with 24 hours and label it a starting hypothesis.
- Always ask before posting: output drafts, user approves and posts manually
