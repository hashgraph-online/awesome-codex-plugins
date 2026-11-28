---
name: review-insights
description: When the user wants to understand what users say about an app using ASOScan (overall review sentiment plus the top topics, feature requests, and bugs mentioned, and the raw reviews behind them). Also use when the user mentions "what are users saying", "review sentiment", "top complaints", "what features are people asking for", "what bugs are mentioned", or "summarize my reviews". Also use to draft a reply to a review and, after the user approves the exact text, post it ("reply to this review", "write a reply"). Works for your app or a tracked competitor.
metadata:
  version: 1.3.7
---

# Review Insights

Turn ASOScan's analyzed review stream into the few things that matter: how users
feel, what they keep asking for, and what's breaking.

## When to use

- "What are users saying about my app?"
- "Top complaints / feature requests / bugs."
- "Summarize the latest reviews." (also for a tracked competitor)

## Getting the data (two modes)

Pick the first mode that applies, then follow the steps below.

1. **ASOScan tools are connected** (the ASOScan plugin or connector in ChatGPT or Claude, or any MCP client): use the tool named in the table. Do not ask for an API key and do not run `curl`. Tool results have the same fields as the API responses below, and a list comes back inside `items`. If a tool answers with a message instead of data (reconnect, credits used up, plan limit, "preparing"), pass that message on and stop.
2. **No tools, but you can run shell commands and `ASOSCAN_API_KEY` is set**: make the API call in the table. Base `https://asoscan.com/api/public/v1`, header `Authorization: Bearer $ASOSCAN_API_KEY`, JSON with camelCase fields. Never print the key. Capture the HTTP status and handle errors as described at the bottom.
3. **Neither**: hand off to **asoscan-setup**. It explains how to connect ASOScan in ChatGPT or Claude, or how to create an API key.

ASOScan only sees the apps in the user's own account and the competitors they track. Reads are free; the table below gives the cost of every call that is not (failed calls are always free). Before a call that costs more than 2 API credits, or one that uses AI, tell the user the cost and wait for a yes. Before any call that changes data, ask first.

| Step | Tool (connected) | API call (key) | API credits |
|---|---|---|---|
| Find the app | `list_my_apps` | `GET /apps` | free |
| Insights | `get_review_insights` | `GET /apps/{id}/reviews/insights` | free |
| Raw reviews | `get_reviews` | `GET /apps/{id}/reviews?page=1&pageSize=20&rating=&sort=newest` | free |
| Saved reply templates | `list_reply_templates` | `GET /apps/{id}/reviews/reply-templates` | free |
| Draft a reply (AI) | `draft_review_reply` | `POST /apps/{id}/reviews/{reviewId}/reply-draft` with `{ "instructions": "...", "autoSelectKeyword": true }` | 2 + 1 AI credit, say the cost first |
| Post a reply (goes to the store) | `post_review_reply` | `POST /apps/{id}/reviews/{reviewId}/reply` with `{ "text": "..." }` | 2, exact text and a clear yes first |

## Steps

1. **Find the app** — `GET /apps` → use the `id`. For a rival, it must be a tracked
   competitor first (see **competitor-analysis**).
2. **Insights** — `GET /apps/{id}/reviews/insights` (free) →
   `{ totalAnalyzed, totalPending, sentiment{ positive, neutral, negative,
   averageScore }, topTopics[]{ label, count }, topFeatureRequests[]{ label, count },
   topBugs[]{ label, count } }`.
3. **Raw reviews** (for evidence) — `GET /apps/{id}/reviews?page=1&pageSize=20&rating=&sort=newest`
   (free; pageSize 1–100; `rating=1..5` to isolate detractors/promoters) →
   `{ items[]{ id, author, rating, title, body, version, country, postedAt,
   developerResponse, developerResponseAt }, page, pageSize, totalCount, totalPages }`.

Lead with insights; pull raw reviews only to quote real examples. If `totalPending`
is high, note that more reviews are still being analyzed.

## How to analyze

- **Sentiment** — the positive/neutral/negative split + `averageScore` (pair with
  the rating trajectory from **competitor-analysis** for trend).
  `averageScore` runs **−1.00 (very negative) to +1.00 (very positive)**, 0 being
  neutral. **Always print it with that range** — a bare "0.38" reads as a bad score
  when it is in fact mildly positive.
- **Themes** — cluster `topTopics`/`topFeatureRequests`/`topBugs` into *love*,
  *friction*, and *requests*, ranked by `count`.
- **Actionability** — for the top 3, name the concrete response: bugs → engineering;
  recurring confusion → onboarding/screenshots; frequent requests → roadmap or
  "What's New".
- **Quote real reviews** verbatim from `body` — never invent or paraphrase into
  something the user didn't write.

## Output template

```
### Review insights — {App}   ·  credits left: {remaining}

**Sentiment:** {positive}/{neutral}/{negative}  (avg {averageScore} on −1 to +1)  ·  {totalAnalyzed} analyzed

**Love**              | **Friction**            | **Most-requested**
- {topic} ({count})   | - {bug} ({count})       | - {request} ({count})

**Top 3 to act on:** 1) {theme} → {response}  2) …
**Evidence:** > "{verbatim review body}" — {rating}★
```

## Replying to a review

Use this when the user wants a reply written or posted for one of their reviews.

1. Get the review id from the raw reviews call. If the user has saved templates, read them and offer one as a starting point.
2. Draft: tell the user the draft costs 2 API credits and 1 AI credit, then draft. The draft is saved in ASOScan only. Nothing goes to the store. The answer has `replyText` (and `keywordUsed` when the draft uses one of their keywords).
3. Show the full reply text and let the user edit it.
4. Post only after the user says yes to that exact text. Send exactly the approved text. If the answer says the app has no store connection, tell the user to connect App Store Connect or Google Play Console in ASOScan (the answer includes the link) and stop.
5. Never post a reply the user has not approved word for word, and never post several replies from one yes.

Replies help users and show the app is cared for. They are not a search-ranking signal, so never present them as a way to rank higher.

## Errors, credits & honesty

- `401` → asoscan-setup · `403` no API access · `402` out of credits · `404` not
  tracked · `503` not enabled yet. Reads here are free; drafting or posting a
  reply costs credits.
- **Never fabricate reviews.** Replying to reviews builds trust/retention but is
  **not** a search-ranking signal — don't frame replies as an ASO lever.
- Full reference: <https://asoscan.com/api/developers>

## Related

- **competitor-analysis** — rating trajectory + compare sentiment across rivals.
- **metadata-audit** — turn recurring confusion into clearer copy/screenshots.
