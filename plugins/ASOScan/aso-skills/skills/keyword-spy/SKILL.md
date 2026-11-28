---
name: keyword-spy
description: When the user wants to reverse-look-up every keyword an app ranks for using ASOScan's keyword-spy (the full set of terms an app appears under, community rank pool plus discovered terms), flagged by whether you already track them. Also use when the user mentions "what keywords does this app rank for", "reverse keyword lookup", "spy on a competitor's keywords", "what search terms is X winning", or "which of their keywords am I missing". For the fuller competitive picture, see competitor-analysis.
metadata:
  version: 1.3.7
---

# Keyword Spy

See the full keyword footprint of an app — yours or a tracked competitor's — with
ASOScan, and mine it for real terms you should be targeting too.

## When to use

- "What keywords does `<app>` rank for?"
- "Spy on `<competitor>`'s keywords."
- "Which of their terms am I not tracking?"

## Getting the data (two modes)

Pick the first mode that applies, then follow the steps below.

1. **ASOScan tools are connected** (the ASOScan plugin or connector in ChatGPT or Claude, or any MCP client): use the tool named in the table. Do not ask for an API key and do not run `curl`. Tool results have the same fields as the API responses below, and a list comes back inside `items`. If a tool answers with a message instead of data (reconnect, credits used up, plan limit, "preparing"), pass that message on and stop.
2. **No tools, but you can run shell commands and `ASOSCAN_API_KEY` is set**: make the API call in the table. Base `https://asoscan.com/api/public/v1`, header `Authorization: Bearer $ASOSCAN_API_KEY`, JSON with camelCase fields. Never print the key. Capture the HTTP status and handle errors as described at the bottom.
3. **Neither**: hand off to **asoscan-setup**. It explains how to connect ASOScan in ChatGPT or Claude, or how to create an API key.

ASOScan only sees the apps in the user's own account and the competitors they track. Reads are free; the table below gives the cost of every call that is not (failed calls are always free). Before a call that costs more than 2 API credits, or one that uses AI, tell the user the cost and wait for a yes. Before any call that changes data, ask first.

| Step | Tool (connected) | API call (key) | API credits |
|---|---|---|---|
| Find the app | `list_my_apps` | `GET /apps` | free |
| Is the rival tracked? | `get_competitors` | `GET /apps/{id}/competitors` | free |
| Add the rival by store link (changes data) | `add_competitor` | `POST /apps/{id}/competitors` with `{ "storeUrl": "..." }` | 2, ask first |
| Spy | `spy_competitor_keywords` | `GET /apps/{id}/keyword-spy?country=` | 2 |

## Steps

1. **Find the app** — `GET /apps` → use the `id`.
   - **Own app** → spy it directly.
   - **A rival** → it must be a **tracked competitor** first. Check
     `GET /apps/{id}/competitors`; if absent, add it via
     `POST /apps/{id}/competitors { "storeUrl": "…" }` (2 credits, **write** key),
     then spy the returned competitor's `id`. Add-by-URL only — there's no lookup
     by app name.
2. **Spy** — `GET /apps/{id}/keyword-spy?country=` (**2 credits**) →
   `{ appName, totalKeywordsFound, communityPoolSize, discoveryStatus,
   keywords[]{ term, rank, volume, difficulty, origin, isTracked } }`.
   - `origin` = `"community"` \| `"discovered"`; `isTracked` = already in your set.
   - `discoveryStatus` = `"cached"` \| `"none"`. The public API doesn't trigger a
     fresh crawl, so a just-added competitor may be sparse until ASOScan's
     background discovery has cached results — re-calling won't add more right away.

## How to analyze

1. **Coverage** — how many terms, split by `origin`.
2. **Steal list** (the payoff) — terms the *competitor* ranks for that are relevant
   to your app AND `isTracked = false`. Filter for relevance first.
3. **Overlap** — terms you both rank for (battlegrounds).
4. Feed the best into **keyword-intelligence** (validate) then **keyword-opportunities**
   (track) — the natural next steps in ASOScan.

## Output template

```
### Keyword spy — {target app} ({country})   ·  credits left: {remaining}

Ranks for **{totalKeywordsFound}** keywords ({communityPoolSize} pooled · rest discovered).

**Terms worth stealing** (they rank, relevant, not yours yet)
| Keyword | Rank | Origin | Note |
|---|---|---|---|

**Shared battlegrounds**
| Keyword | Their rank | Origin |
|---|---|---|
```

## Errors, credits & honesty

- `401` → asoscan-setup · `403` no API access (or read-only key on the add) · `402`
  out of credits · `404` not owned/tracked · `503` not enabled yet. Spy = 2 credits,
  add-competitor = 2.
- A term appearing in spy is a ranking signal, not proof it suits your app — filter
  for relevance. Clean numbers only.
- Full reference: <https://asoscan.com/api/developers>

## Related

- **competitor-analysis** — the fuller competitive picture.
- **keyword-intelligence** — validate stolen terms.
- **keyword-opportunities** — track the winners.
