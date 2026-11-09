# Access Ladder

> Classify the target, start at the cheapest tier that can reach it, change one axis per retry, and climb only when a tier cannot pass.

## 1. Classify the Target

Answer four questions before the first request and print them as the classification line.

| Question | Values | How to decide |
|---|---|---|
| Platform | `official-endpoint`, `media`, `generic` | `official-endpoint` when `references/public-endpoints.md` lists the host; `media` when the target is a video, audio, or podcast item; otherwise `generic` |
| Shape | `single`, `bulk` | `bulk` when the request asks for many items, pagination, "전부", "모두", "크롤링", "N개 이상", or a whole site section |
| Freshness | `live-required`, `copy-acceptable` | `copy-acceptable` when the page is dead or removed, the user asks about a past date, or the user accepts an archive copy; otherwise `live-required`. A caller that passes a freshness answer overrides this inference, because that caller owns the claim the content supports |
| Authorization | `public`, `own-account`, `outside` | `rules/access-policy.md` §1 and §2 |

A target placed `outside` stops here with terminal `needs_user` or `blocked` (`rules/access-policy.md` §2). A `bulk` target passes the bulk gate (`rules/access-policy.md` §3) before tier 1.

A request that names only a keyword ("X에서 AI 관련 글") has no target yet: get a URL from a search capability first, then classify the URL. A search result list alone is not this skill's output.

## 2. Tiers

Tiers run in this order. Skip a tier only for the reason in its row, and record the skip in the ledger.

| Tier | Method | Use when | Skip when |
|---|---|---|---|
| 0 | Official public endpoint of the same platform (JSON, Atom, oEmbed, syndication, registry API) | Platform is `official-endpoint` | No endpoint covers the requested content |
| 1 | Headless request grid: plain curl with browser-like headers, then URL variants, referer strategies, device classes, client fingerprint impersonation (curl_cffi when installed), readers, structured-metadata extraction, feed discovery, and the media extractor for `media` | Always for `generic` and `media`, and after tier 0 fails | The previous tier was accepted; or freshness is `copy-acceptable` and the page is already known dead, removed, or changed, so the run starts at tier 2 |
| 2 | Archive copy: Wayback availability lookup, then other archives | Freshness is `copy-acceptable` | Freshness is `live-required`; when tiers 3 and 4 then fail or are skipped, offer the copy once and run tier 2 only if the user accepts it |
| 3 | Owned browser: a browser the run launches with a fresh task-owned profile, headless first, through the runtime's own browser capability | Tier 1 and tier 2 failed or were skipped, or the content needs JavaScript, clicks, scrolling, media playback, or a screenshot | No browser-automation capability: mark `skipped`, terminal `blocked` or `fetched_partial` |
| 4 | Attached browser: the user's own signed-in browser, driven through the runtime's attach capability | Authorization is `own-account`, or the host blocks every owned browser and the user agrees to open it in their own browser | No attach capability, or the user is not present for a login or challenge step |

`references/headless-recipes.md` holds the tier 1 and tier 2 commands; `references/public-endpoints.md` holds tier 0; `references/browser-tier.md` holds tiers 3 and 4.

## 3. Budgets

| Tier | Attempt budget | Leave the tier early when |
|---|---|---|
| 0 | 2 endpoint calls per target | The endpoint returns 401, 403, or a documented "auth required" error twice |
| 1 | 12 attempts per target | Three attempts in a row, each changing a different axis, return the same challenge for a product whose row in `references/block-signals.md` is `needs_js` or `needs_real_browser`; a `needs_real_tls` product leaves only after every impersonation family was tried |
| 2 | 1 Wayback lookup plus 1 snapshot fetch, then 1 attempt per other archive | Every archive returns no snapshot, a timeout, or a stub |
| 3 | 1 browser session, at most 3 navigations | The rendered page still shows a challenge after one reload and a 10-second wait |
| 4 | 1 attached session | The user declines, or a login or challenge step needs them and they are not present |

A `bulk` run applies the budget per item and adds the page cap and rate from `rules/access-policy.md` §3. Never raise a budget to force a pass; report the spent budget instead.

## 4. Retry Axes

Each retry inside a tier changes exactly one axis from the previous attempt and records it in the ledger's `method` column.

| Axis | Values | Notes |
|---|---|---|
| URL variant | original, mobile host (`www.` to `m.`), drop `www.`, AMP or print path only when the page links to it | A variant counts only when it serves the same content; check the title or canonical link |
| Client fingerprint | curl default, then curl_cffi impersonation targets by family (Safari, Safari iOS, Chrome, Chrome Android, Firefox) | Use curl_cffi only when it is already installed, or install it into a task-owned virtual environment; never into the system or user Python |
| Referer | none, the site's own root, a search-engine referer | A referer is a header choice, not an identity claim; never add cookies |
| Device class | desktop, mobile | Mobile pairs with mobile user agents and the mobile host variant |
| Reader | a reader service that renders the page as text | Its result is provenance `reader`; send no cookies or authorization to it |

## 5. Escalation Rules

- An HTTP 200 starts the proof check; it never ends the tier by itself (`rules/evidence-and-report.md` §1).
- A `challenge` verdict from a product whose row in `references/block-signals.md` says `needs_js` or `needs_real_browser` ends tier 1 after the early-leave condition in §3; go to tier 2 when freshness allows a copy, otherwise tier 3.
- A `stub` verdict (redirect page, interstitial, cache shell that points back to the origin) never counts as success and never ends a tier early.
- In tier 3, read the page's own JSON calls before the DOM when the content is data (product lists, feeds, search results): capture the network requests, then re-request the JSON URL in tier 1. API layers are often less guarded than HTML.
- For a `bulk` target, find one working route on the first item, then reuse that route for the rest; climb again only for items that fail.
- Stop at the first `strong_ok` attempt. A `weak_ok` attempt is kept while one more axis in the same tier, or the next tier, runs within budget; the better result is accepted, and a `weak_ok` result left at the end gives `fetched_partial`.

## 6. No-Site-Name Rule

This package stores no site-specific selectors, byte sizes, cookie values, or quirks in its rules. A site's success selector, preferred referer, or working variant is a runtime input for the current run only. Platform names may appear in the references as examples and as the index of official endpoints.

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| The tier order, the 12-attempt grid, the retry axes (URL transform, TLS impersonation, referer, device class), the API-first branch through captured network requests, and the no-site-name rule | The `ultimate-browsing` skill in `code-yeongyu/oh-my-openagent` (branch `dev`), read 2026-11-07 |
| curl_cffi browser impersonation targets | <https://pypi.org/project/curl-cffi/>, version 0.17.0 observed 2026-11-07 |
| Per-tier budgets, the one-axis retry rule, and the early-leave conditions | this package's chosen design, not a validated optimum |
