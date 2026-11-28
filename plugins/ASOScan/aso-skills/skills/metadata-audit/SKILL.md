---
name: metadata-audit
description: When the user wants to audit or improve an app's store listing metadata using ASOScan (the current title, subtitle/short description, description, keyword field, and what's-new, plus ASOScan's ASO score and recommendations and the change history), then draft specific, honest improvements within the platform's character limits. Also use when the user mentions "audit my listing", "improve my metadata", "optimize my title/subtitle/description", "what's my ASO score", "rewrite my app store copy", or "what changed in my listing", or wants listing text drafted for another language ("translate my listing", "localize my listing"). For choosing which keywords to target, see keyword-opportunities.
metadata:
  version: 1.3.7
---

# Metadata Audit

Score the listing with ASOScan's ASO score, find the gaps, and draft better copy —
specific, within limits, and honest.

## When to use

- "Audit / optimize my app listing." · "What's my ASO score and how do I raise it?"
- "Rewrite my title / subtitle / description." · "What metadata changed recently?"

## Getting the data (two modes)

Pick the first mode that applies, then follow the steps below.

1. **ASOScan tools are connected** (the ASOScan plugin or connector in ChatGPT or Claude, or any MCP client): use the tool named in the table. Do not ask for an API key and do not run `curl`. Tool results have the same fields as the API responses below, and a list comes back inside `items`. If a tool answers with a message instead of data (reconnect, credits used up, plan limit, "preparing"), pass that message on and stop.
2. **No tools, but you can run shell commands and `ASOSCAN_API_KEY` is set**: make the API call in the table. Base `https://asoscan.com/api/public/v1`, header `Authorization: Bearer $ASOSCAN_API_KEY`, JSON with camelCase fields. Never print the key. Capture the HTTP status and handle errors as described at the bottom.
3. **Neither**: hand off to **asoscan-setup**. It explains how to connect ASOScan in ChatGPT or Claude, or how to create an API key.

ASOScan only sees the apps in the user's own account and the competitors they track. Reads are free; the table below gives the cost of every call that is not (failed calls are always free). Before a call that costs more than 2 API credits, or one that uses AI, tell the user the cost and wait for a yes. Before any call that changes data, ask first.

| Step | Tool (connected) | API call (key) | API credits |
|---|---|---|---|
| Find the app | `list_my_apps` | `GET /apps` | free |
| ASO score | `get_aso_score` | `GET /apps/{id}/aso-score?country=` | free |
| ASOScan recommendations | `get_aso_recommendations` | `GET /apps/{id}/recommendations` | free |
| Current listing text | `get_listing_metadata` | `GET /apps/{id}/metadata?country=` | free |
| Change history | `get_metadata_changelog` | `GET /apps/{id}/metadata/changelog?country=` | free |
| Saved drafts for other languages | `list_localized_drafts` | `GET /apps/{id}/localizations/drafts` | free |
| Draft listing text for another language (AI) | `draft_localized_metadata` | `POST /apps/{id}/localizations/{locale}/draft` | 2 + 1 AI credit, say the cost first |

## Steps

1. **Find the app** — `GET /apps` → note the `id` and `platform` (Apple vs Google —
   the rules differ).
2. **ASO score (authoritative)** — `GET /apps/{id}/aso-score?country=` (free) →
   `{ overall, metadata, ratings, conversion, conversionIsProxy, grade, platform,
   recommendations[]{ category, severity, title, description } }` (`overall` 0–100,
   each pillar 0–25; severity
   `critical|warning|info`). **Use this as the headline number; don't invent one.**
3. **Recommendations** (`get_aso_recommendations` or `GET /apps/{id}/recommendations`) → `{ items[]{ id, status, platform, category, priority, title, why, how, expectedImpact, updatedAt }, generatedAt }`. Lead with the highest priority items and use their `why` and `how` in your field-by-field advice.
4. **Current metadata**: `GET /apps/{id}/metadata?country=` (free) →
   `{ title, subtitle, promotionalText, keywords, shortDescription, description,
   whatsNew, releaseDate }`. A **404** = nothing captured yet.
5. **Change history**: `GET /apps/{id}/metadata/changelog?country=` (free) →
   `[{ field, oldValue, newValue, changedAt, oldVersion, newVersion }]`.
6. **Target keywords**: pull winners from **keyword-opportunities** / **keyword-intelligence**.

## Platform rules to enforce (Apple/Google official, current)

**Apple** — indexed search text = Title + Subtitle + hidden Keyword field (+ primary category):

- Title **30 chars**, Subtitle **30 chars**, Keyword field **100 bytes**
  (100 characters in plain English; non-Latin characters use more than one byte
  each, so Japanese, Chinese or Korean text fits far fewer characters).
- Keyword field: **commas between terms** (a space is allowed *within* a phrase but
  costs a character — most list single words and let Apple recombine them across
  name + subtitle + keywords).
- **Don't repeat** a word already in Title/Subtitle/**category**; skip **plurals**
  of included words, **generic** terms (`app`, `game`), **filler** (`the`, `to`),
  and competitor/trademarked terms.
- Long **description is NOT indexed** for Apple search — optimize it for conversion.
  Promotional text (170 chars) isn't a search signal (but updates anytime, no release).
- Screenshots: the first **1–3** appear in search results.

**Google** — indexed search text = Title + Short description + Full description:

- Title **30 chars**, Short description **80 chars**, Full description **4,000 chars**
  and it **is indexed** — weave keywords in naturally (Google penalizes stuffing).
- **Title bans:** emojis, ALL CAPS, "best/#1/free", CTAs.
- Screenshots: up to **8** per device type.

If a limit is decision-critical, verify against Apple's/Google's official docs first.

## The audit

Use ASOScan's `overall` + pillar scores as the quantitative backbone; weight your
emphasis toward the lowest pillar. Grade Title/Subtitle, Description, Keywords,
Ratings, Conversion (`conversionIsProxy: true` = estimated until store analytics are
connected), and Freshness.

**Always print a score with its denominator.** `overall` is out of **100**;
`metadata`, `ratings` and `conversion` are each out of **25**. There is no fourth
pillar: `overall` is the three pillars' sum (out of 75) rescaled to 100, so
20 + 20 + 20 = 60/75 prints as **80/100**. A bare "metadata 25"
reads as a failing grade when it is in fact a perfect one.

**Know what the pillars measure.** `metadata` scores **completeness and limit
compliance** — is each indexed field present, and does it use a sensible share of its
character budget. It does **not** judge whether the copy is any good: nothing checks that
the title carries a term users search, or that the subtitle states a benefit rather than a
slogan. `conversion` is the same shape — it counts assets like screenshots and cannot see
what is in them. So **never tell the user a 25/25 means their copy is optimal**; say the
fields are complete and in-limit, then do the quality read yourself in the field-by-field
section below. That judgement is the value you add on top of the score.

## Output template

```
### Metadata audit — {App} · {platform} ({country})   ·  credits left: {remaining}

**ASO score: {overall}/100 ({grade})**  (metadata {metadata}/25 · ratings {ratings}/25 · conversion {conversion}/25)

**Top 3 quick wins (<1h):** 1) {exact new text + char count}  2) …

**Field-by-field**
- **Title** ({used}/30): "{current}" → "{new}" ({N} chars) — {why}
- **Subtitle/Short** ({used}/{30|80}): "{current}" → "{new}" — {why}
- **Keywords** (Apple, {bytes used}/100 bytes): "{current}" → "{new}" — no dupes vs title/subtitle
- **Description / What's new:** {fix}

**ASOScan recommendations:** {surface each by severity}
```

Every suggestion must be concrete (exact text + char count) and tied to a real
keyword or conversion reason. Point the user back to ASOScan to re-score after edits.

## Listing text for another language

Use this when the user wants their listing in another language or country.

1. Read the saved drafts first. If one exists for that locale, show it before writing a new one.
2. Tell the user a new draft costs 2 API credits and 1 AI credit, then call it with the store locale (for example `de-DE`, `fr-FR`, `es-ES`).
3. If the answer says ASOScan is preparing the keyword data for that market, nothing was charged. Tell the user to ask again in a minute. Use `force` (the tool's `force` input, or `?force=true`) only when the last "preparing" answer is several minutes old.
4. Show each variant with its character counts against the platform limits above. The draft is saved in ASOScan. ASOScan does not publish listing text to the stores; the user copies it into App Store Connect or Google Play Console.

Describe the benefit only as Apple documents it: localized name, subtitle and keywords are searchable in every storefront that supports that language, so more people can find the app. Never say a translation raises keyword rank.

## Errors, credits & honesty

- `401` → asoscan-setup · `403` no API access · `402` out of credits · `404` no
  metadata yet · `503` not enabled yet. Reads here are free; only drafting a
  localized listing costs credits (2 API + 1 AI).
- No invented claims/awards/"#1" superlatives (also banned in Google titles).
  Respect limits exactly. Recommend the outcome, not a guaranteed rank.
- Full reference: <https://asoscan.com/api/developers>

## Related

- **keyword-opportunities** / **keyword-intelligence** — choose the keywords to target.
- **competitor-analysis** — benchmark against rivals.
- **review-insights** — turn recurring confusion into clearer copy.
