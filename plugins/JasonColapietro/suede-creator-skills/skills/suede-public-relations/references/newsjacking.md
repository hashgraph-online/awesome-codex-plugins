# Newsjacking: Reactive PR Workflow

Injecting your POV into a story that's already trending. Done well: free distribution off a wave of attention. Done badly: cringe at best, brand damage at worst.

## Contents
- When newsjacking works (and when it doesn't)
- The detect → score → angle → pitch loop
- Newsworthiness scoring rubric
- Story angle library
- Speed: the only thing that matters
- Sources & tooling
- Failure modes

---

## When Newsjacking Works

- **Tech/regulatory news in your category**: new law, new platform launch, competitor pivot, big acquisition
- **Industry data drops**: a major report drops, you have a sharper take or contradicting data
- **Public conversation**: a debate or controversy where your expertise is genuinely relevant
- **Seasonal/cyclical moments**: earnings season, year-end reviews, conference weeks

## When to Skip

- **Tragedies, accidents, deaths**: no exceptions. Don't.
- **Politically charged stories** unless your brand explicitly takes political stances
- **You have no genuine expertise** in the area
- **The window is already closed**: if a story is 48h+ old and you weren't first, you're late
- **The angle is "we have a product for this"**: that's marketing, not journalism

---

## The Loop

A repeatable draft-and-review workflow Suede can run on demand.

1. **Detect**: surface trending stories in your category (see [Sources & Tooling](#sources--tooling))
2. **Score**: apply the [newsworthiness rubric](#newsworthiness-scoring-rubric); drop anything below threshold
3. **Angle**: generate 2–3 angles per story using the [angle library](#story-angle-library)
4. **Validate**: sanity-check: do you actually have the expertise/data to back this angle?
5. **Pitch draft**: prepare a bounded, source-matched recipient set and a
   separate draft for each (see
   [journalist-pitching.md](journalist-pitching.md))
6. **Owned-channel draft**: when current evidence supports a public trail,
   prepare a blog or social draft; do not publish it

Sending or publishing anything produced here runs the send-approval handover in
SKILL.md ("Quick Reference: Pitch Quality Bar"), which is the canonical
statement of this gate.

Output format Suede should produce:

```
NEWSJACK CANDIDATE: 2026-06-10

Story: "EU passes AI Act amendment requiring agent registration"
Source: TechCrunch, 3h ago
Score: 8/10 (high relevance, fresh, you have proprietary data)

Angles:
1. Data hot take: "Our analysis of 12,000 agent deployments shows 73% would fail this requirement"
2. Contrarian: "Why the registration rule will hurt safety, not improve it"
3. Customer story: "How [customer] is preparing: interview offer"

Recommended: #1 (you have unique data, strongest hook)
Pitch draft: [see journalist-pitching.md for template]
Target journalists: [list with rationale]
```

---

## Newsworthiness Scoring Rubric

Score each candidate 1–10 on five dimensions, multiply by the weight, then sum. Max possible: 80 (10 × the 8x weight total).

| Dimension | What it measures | Weight |
|-----------|------------------|--------|
| **Timeliness** | Is the story inside the justified current-coverage window? | 2x |
| **Relevance** | Genuinely in your expertise area? | 2x |
| **Angle uniqueness** | Can you say something no one else is saying? | 2x |
| **Authority** | Do you have data, customers, or experience to back it? | 1x |
| **Reach potential** | Will this story keep growing or has it peaked? | 1x |

**Threshold:** weighted total ≥ 50/80. Below that, skip.

**Auto-disqualify if:**
- The story is about something tragic
- Your angle is "I disagree" with nothing to back it
- You haven't actually formed an opinion: you just want to be quoted

---

## Story Angle Library

Use these templates to generate angles fast.

### 1. Data hot take
*"We analyzed [N] [things] after [event]. Here's what we found."*

Best when you have proprietary data. The journalist gets a stat, you get the citation.

### 2. Contrarian
*"Everyone says [popular take]. Here's why they're wrong."*

Best when you can defend the position with specifics. Weak when it's just contrarianism for attention.

### 3. "We predicted this"
*"Six months ago we wrote [thing]: here's what's happening now and what's next."*

Best when you actually did predict it. Lethal to your credibility if you didn't.

### 4. Customer impact
*"Here's a [customer type] who's directly affected. We can put you in touch."*

Best for B2B. Reporters love named customers willing to talk.

### 5. Insider explainer
*"This story is complicated. Here's what's actually happening."*

Best when most coverage is missing nuance. You're not arguing: you're educating.

### 6. Trend connector
*"This isn't isolated: it's part of a bigger shift we're seeing in [pattern]."*

Best when you have several data points or examples to connect.

### 7. Founder POV
*"As someone who's built in this space for [X years], here's the part most people are missing."*

Best for opinion pieces / op-eds. Weak as a soundbite pitch.

---

## Timing as a Current-Story Variable

Coverage curves vary by story and outlet. Use these only as starting research
windows when current source timestamps and outlet deadlines are unavailable:

| Story type | Effective window |
|-----------|------------------|
| Breaking tech news | 4–12 hours |
| Major regulation / policy | 24–48 hours |
| Industry report / data drop | 24–72 hours |
| Conference announcement | Same day |
| Acquisition / funding news | 12–24 hours |

Use observed coverage velocity, the journalist's current deadline, source
confidence, and review capacity to decide whether the angle remains timely.
Timeliness never bypasses the send-approval handover in SKILL.md.

---

## Sources & Tooling

Reuses the `suede-social` listening model. First inspect which source readers and
parsers are already installed and callable. If a dependency is missing, use a
manual/RSS-reader fallback or request explicit installation approval after
confirming the current platform and package source. Do not run package-manager
commands from this reference without that approval.

### Google News RSS (no auth)

```bash
# Replace QUERY with topic (use + for spaces, %22 for quotes)
curl -s "https://news.google.com/rss/search?q=QUERY&hl=en-US&gl=US&ceid=US:en" \
  | xmllint --xpath "//item[position()<11]" - 2>/dev/null
```

### Hacker News (Algolia) for tech stories

```bash
SINCE=$(($(date +%s) - 86400))
curl -s "https://hn.algolia.com/api/v1/search_by_date?query=QUERY&tags=story&numericFilters=created_at_i>${SINCE}" \
  | jq '.hits[] | {title, url, points, num_comments, created_at, hn_url: ("https://news.ycombinator.com/item?id="+.objectID)}'
```

### Reddit (for category-specific subs)

```bash
curl -s -A "newsjack/1.0" \
  "https://www.reddit.com/r/SUBREDDIT/top.json?t=day&limit=15" \
  | jq '.data.children[].data | {title, url, score, num_comments, created_utc}'
```

### Journalist research (browser-driven)

For finding *which* journalists are covering the story right now:
- First discover whether an authorized browser or research connector is
  currently callable, authenticated, and permitted for the intended sources.
- If available, search current news results, open the underlying articles, and
  record bylines, dates, URLs, and the evidence supporting beat fit.
- If unavailable, ask for article URLs or an export and provide a manual
  worksheet. Do not claim current coverage was reviewed from snippets alone.
- Confirm beat and recent coverage from public professional profiles or
  first-party outlet pages; never bypass a login or access control.

See also [journalist-pitching.md](journalist-pitching.md) for the full discovery workflow.

### Source list

For repeatable monitoring, add a "Newsjacking topics" section to `.agents/listening-sources.md` (template in the `suede-social` skill's references):

```markdown
## Newsjacking topics (Google News RSS)
- "AI agent regulation"
- "[your category] funding"
- "[your competitors] OR [adjacent competitors]"

## Industry data drops (RSS / manual)
- Pitchbook reports
- a16z state of [industry] reports
- [your category] benchmark reports
```

---

## Failure Modes

Things that have ended careers and brands.

- **Tragedy-jacking**: Oreo's 2013 Super Bowl tweet worked. Most attempts since have not. Wartime, disasters, deaths: don't.
- **The forced fit**: "Here's our take on [trending story]: it's actually about [our product]." Journalists see through this instantly.
- **The empty take**: pitching "we have an opinion" without specifics. Journalists need a quote-worthy line, not "we're closely watching this."
- **Speed without judgment**: being first with a bad take is worse than being late with a good one. The 30-minute "is this brand-appropriate?" gut check exists for a reason.
- **Undifferentiated bulk pitching**: duplicate outreach ignores recipient fit
  and can damage relationships.
- **No response plan**: if a journalist replies, use the stated deadline and
  approved team service level; do not assume a universal reaction window.

---

## Companion Practice: The Public Trail

An existing public trail can help a journalist verify the position. Before
proposing a pitch:

1. Check whether a current owned source already documents the verified position.
2. If not, draft an owned-channel post only when it would add useful evidence.
3. Reference a live owned source only after it has been separately approved and
   published by the user.

A public post is optional. Do not manufacture one merely to imply authority.
