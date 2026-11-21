# Account Audit

Audit one account's recent cohort without blurring three different things:
public engagement, private platform insights, and business conversion. Works for
Instagram, TikTok, LinkedIn, X, YouTube Shorts, Threads, and Facebook. Platform
specifics are at the bottom.

## Source order

1. Authenticated native analytics or a user export (Instagram Insights, TikTok
   Analytics, LinkedIn post analytics, X Analytics, YouTube Studio).
2. An authorized platform API for a professional or business account.
3. User-supplied post URLs, screenshots, content ledger, link analytics, CRM, or
   checkout data.
4. Public profile evidence, limited to what is actually visible.

Most platforms prohibit automated collection without permission, Instagram's
Terms of Use among them. With no authorized source, return the worksheet below
and ask for an export. Do not scrape.

## Default cohort

The most recent 30 feed posts and short videos, or all posts when fewer exist.
Tag boosted posts, collaborations, giveaways, launches, and news-driven spikes
as confounders. Tag them; never drop them silently.

## Post ledger (one row per post)

```text
Post ID / permalink:
Published at / timezone:
Format: short video | carousel or document | static | text | thread | collab | other
Organic / boosted / unknown:
Duration or slide count:
Topic and pillar:
Audience problem or desire:
Hook text and hook family:
Structure:
Proof used:
Search terms in caption, on-screen text, and spoken audio:
CTA and destination:
Offer proximity: none | assist | direct
Visual mode: face | faceless | product | UGC | mixed
Production burden: low | medium | high, with minutes when known
Views / impressions:
Accounts reached:
Watch time / average watch time / completion:
Likes / comments / saves / shares or sends / reposts:
Follows attributed to post:
Profile visits / profile actions / link clicks:
DM starts / keyword replies:
Attributed leads / sales / revenue:
Search-sourced views (when the platform reports traffic source):
Metric source and captured date:
Evidence class: observed-public | observed-owned | computed | inferred | unknown
Notes and confounders:
```

## Conversion classification

- **Converts:** an attributable primary action (qualified follow, DM start,
  lead, checkout, sale). Record the attribution source.
- **Assists:** measurable saves, shares, profile visits, link clicks, or
  qualified comments without a reliably attributed primary action.
- **Attention-only:** in the cohort's top reach or view quartile while its
  primary-action rate is at or below the comparable-format median.
- **Unknown:** downstream measures are missing or attribution is unreliable.

Never promote `unknown` to `attention-only` or `converts` by intuition.

## Cohort controls

- Compare like formats only: short video against short video, carousel against
  carousel.
- Compare rates only when denominators exist and match.
- Use medians when a few outliers dominate; show raw counts when `n` is small.
- Show `n=<count>` beside every pattern. One post is an anecdote, two are a
  clue, three or more comparable posts support a starting hypothesis.

## Audit output

```text
Coverage: <collected>/<target> posts | Access: public | authenticated | export | mixed
Date range: | Metrics unavailable:

What repeatedly earns attention:
- Pattern -> post IDs -> cohort result

What repeatedly earns qualified action:
- Pattern -> post IDs -> cohort result -> attribution source

Views without downstream proof:
- Pattern -> post IDs -> missing or weak action

Search discoverability:
- Which posts get search-sourced views, and which search terms they carry

Audience response:
- Recurring questions, objections, vocabulary, and requests

Conversion map: converts | assists | attention-only | unknown, with post IDs

Next controlled tests (3 to 5):
1. hypothesis / one variable / primary metric / stop rule
```

## Platform notes

- **Instagram:** Insights exposes reach, views, watch time, saves, shares,
  follows, and profile activity for professional accounts. Public views do not
  reveal saves, shares, or retention. Since July 10, 2025, public posts and
  Reels from professional accounts of adults can appear in Google and other
  search engines unless the account turns off "Allow public photos and videos
  to appear in search engine results" (Settings, then Privacy).
- **TikTok:** Analytics reports traffic source, including search, per video.
  Read the search share before calling a video's reach "algorithmic".
- **LinkedIn:** Post analytics separate impressions, members reached, and
  engagement; document posts expose page-level reach only in aggregate.
- **YouTube Shorts:** Studio reports traffic source (Shorts feed, search,
  browse, external). Shorts can run up to three minutes when uploaded on or
  after October 15, 2024.
- **X:** Analytics depends on account tier. Record which tier produced the data.

## Official checkpoints

Refresh before encoding platform behavior:

- Instagram Reel insights: https://www.facebook.com/help/instagram/202865988324236
- Instagram recommendation eligibility: https://www.facebook.com/help/instagram/653964212890722
- Instagram Terms of Use: https://www.facebook.com/help/instagram/581066165581870
- YouTube three-minute Shorts: https://support.google.com/youtube/answer/15424877
