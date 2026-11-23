# PlaceCall: No number? Find the place first with `POST /v1/places/suggest`

Part of the PlaceCall skill ([`SKILL.md`](../SKILL.md)). Read it for finding a place when the user has no number.

When the user names a need rather than a number ("find a florist with
peonies", "book somewhere romantic in Chicago Saturday 8pm"), suggest first.
One free-text query returns up to 4-6 ranked place cards, each ready to dial.
Billed at cost: 5 credits per answered request (half a call), from the same
balance calls use. A `degraded` answer and a short list bill in full; a
refusal bills nothing (`402`/`422`/`429`/`5xx`, `NO_PLACES_FOUND` included).
The refundable hold (15) is larger than the charge, so `402` can fire while
your balance still covers the 5. Rate limits: 10/min, 1000/UTC-day per
account, separate from all call limits. The rate is operator-set; see
<https://api.voygr.tech/checkout>. US market only, except IN, LA, MN, MT, NE;
queries and output are English.

```sh
curl -s -X POST https://api.voygr.tech/v1/places/suggest \
  -H "X-API-Key: $PLACECALL_API_KEY" -H "Content-Type: application/json" \
  -d '{
        "query": "florist in Chicago with fresh peonies in stock today",
        "location_hint": "Wicker Park",
        "booking_name": "Alex",
        "callback_phone": "+13125550188"
      }'
```

Body (only `query` is required):
- `query`: plain English, ≤500 chars, saying what, where and when.
- `location_hint`: neighborhood, city or ZIP, free text. Required in practice
  for "near me" wording (no city in query, no hint: `422 LOCATION_REQUIRED`).
  A location named in `query` always wins over the hint; sending both is fine.
- `limit`: 1-6, upper bound only (server default: 4 for mainstream queries,
  6 for niche ones).
- `booking_name`, `callback_phone`: baked into every card's `call_brief`, so
  the brief is complete before you see it. `callback_phone` is validated by
  the same normalizer as `target_phone`.

Response shape (`200`; every field, one card shown). Cards live in
`suggestions[]`, ordered by `rank`, and each card carries its own
`suggestion_id`. The body and `intent` are additive: parse leniently, never
reject an unknown key.

```json
{
  "request_id": "sugreq_7b41d0c95e8a4f2ab63d1c07f5e29a84",
  "intent": { "call_intent": "availability_check", "category": "florist",
              "geo": {"city": "Chicago", "area": null, "near_me": false},
              "place_level": [], "product_level": ["fresh peonies"],
              "moment_level": ["in stock today"], "party_size": null,
              "target_datetime": "2026-08-21", "specificity": "long_tail",
              "unsatisfiable": [] },
  "suggestions": [
    { "suggestion_id": "sug_3f9c62a1d84e47b0a15c9d2e6f80b7c3",
      "rank": 1, "name": "Fleur Chicago",
      "address": "3149 W Logan Blvd, Chicago, IL 60647",
      "phone_e164": "+17734880477", "website": "https://…",
      "confidence": "high", "price_band": "$$",
      "open_at_target": true,
      "why": "Reviewers repeatedly mention seasonal stems and peonies in spring runs",
      "product_match": {"claim": "fresh peonies", "status": "unknown"},
      "verify_on_call": ["whether fresh peonies are in stock today"],
      "verify_items": [
        {"question": "whether fresh peonies are in stock today", "state": "unknown"},
        {"question": "Do you deliver?", "state": "answered"} ],
      "call_needed": true,
      "online_route": "delivers",
      "fit_note": "in Logan Square, a few blocks northwest of Wicker Park",
      "call_brief": "Call Fleur Chicago. Ask whether they have fresh peonies available this week. Do not place an order — just report back. Also confirm: whether fresh peonies are in stock today. Callback number +13125550188.",
      "call_ready": true } ],
  "degraded": false,
  "degradation_reason": null,
  "short_list_reason": null
}
```

Each card bridges to `POST /calls` through three fields:
- `phone_e164`: pre-validated by the same normalizer `POST /calls` uses, so a
  card's number is never rejected as malformed. Aggregator call-centers
  (OpenTable/Resy), non-US numbers, and places in IN, LA, MN, MT, NE are
  filtered out before you see them.
- `call_brief`: a ready-to-send `brief`, assembled by code from templates
  (name, date/time, party, callback number, verify questions). Send it as-is
  or edit it, but read it first (see [gotcha 10](gotchas.md)).
- `suggestion_id`: send it back on `POST /calls` to link the call to the card.
  Linking changes nothing about the call; it records which card was dialed
  and how it went, which improves the ranking. Opaque string (≤40 chars),
  scoped to your account, valid 7 days. Never parse or sort by it.

Plus context to choose with:
- `rank`: 1..N, best first.
- `why`: one sentence grounded in public reviews of the venue.
- `confidence`: `high`/`medium`/`low`, an open set, rating how
  well-established the venue looks from public feedback. Cards are already
  ordered by `rank`, so read it as "how sure", not as a sort key.
- `price_band`: `$`…`$$$$`, null when unpublished. `website`: nullable.
- `open_at_target`: open at the requested time; `null` when no time or only a
  past one was asked, or the hours are unpublished.
- `product_match`: `null` unless the query named a product. `status` is
  `confirmed` only when public feedback confirms it, else `unknown`; an
  allergen or dietary-safety ask is never `confirmed`.
- `call_ready`: `false` when the venue is known to be closed at the requested
  time; the card is still returned.

Does this card need a call? These fields answer that (open vocabularies, so
branch with a default):
- `verify_items`: up to six `{question, state}`, with state `unknown` (nothing
  published answers it), `verify_published` (the listing states it; the call
  checks it) or `answered` (settled by the listing; nobody is asked).
- `verify_on_call`: the spoken half, 0-3 questions (every item not
  `answered`) in the order the call asks them. `[]` is a real answer.
- `call_needed`: `true` when at least one item still needs a person. `false`
  means "no question for you", not "do not call": the number and the brief
  are still there. Also `false` on a `rank_fallback` answer.
- `online_route`: the non-phone route (`takes reservations`, `delivers`,
  `takeout`, `showtimes and tickets online`, or `null`). Evidence, not a
  promise, so the card still offers the call.
- `fit_note`: one line that could change the choice (a caveat, or why a place
  just outside the named area is kept); `null` is common.

A past-tense ask ("was open yesterday at 3am") is never moved forward:
`intent.target_datetime` is `null`, the ask stays in `intent.moment_level`,
and only a call can answer it.

### The suggest → call handoff

```sh
# phone and brief come straight off the card you picked
curl -s -X POST https://api.voygr.tech/calls \
  -H "X-API-Key: $PLACECALL_API_KEY" -H "Content-Type: application/json" \
  -H "X-Client-Surface: claude-plugin" \
  -H "X-Client-Agent: ${CLAUDECODE:+claude-code}${CURSOR_AGENT:+cursor}${CODEX_SANDBOX:+codex}${GEMINI_CLI:+gemini-cli}" \
  -H "X-Client-Version: placecall-skill/6.7.0" \
  -H "Idempotency-Key: 3f6c2a0e-0b8e-4c55-9a51-2d7d1f0b6c11" \
  -d '{
        "target_phone": "<card phone_e164>",
        "brief": "<card call_brief — as-is, or edited>",
        "suggestion_id": "<card suggestion_id>",
        "language": "en",
        "ask_user_mode": "stream"
      }'
```

Link rules, all enforced as `422` before anything dials or reserves credits:
- `target_phone` must equal the card's `phone_e164`
  (`SUGGESTION_PHONE_MISMATCH`; the hint names the right number).
- An unknown id, another account's, or one over 7 days old gets
  `SUGGESTION_NOT_FOUND`. The remedy is always to request fresh suggestions.
The `brief` itself is yours to edit; only the phone must match the card. A
card may be called more than once (busy line, retry), and a second card from
the same response may be called too. Every linked call records its own
outcome.

### Degraded answers, short lists and the parsed intent
- `degraded: false` means a full-strength answer. `degraded: true` +
  `degradation_reason` (`relaxed_thresholds` | `few_results` | `rank_fallback`
  | `partial_timeout` | `unsatisfiable_qualifier`) means the answer is weaker in
  that way; tell your user which, don't hide it. The field holds one value
  (the strongest reason), so a weaker one may also apply; the set is open.
- `intent.unsatisfiable`: the fragments dropped as impossible ([gotcha 11](gotchas.md)).
  Non-empty always means `degraded: true`; branch on this list, not on the
  reason. Usually `[]`.
- `short_list_reason`: why you got fewer cards than `limit`. `"thin_pool"` =
  few places survived (always with `degraded: true` / `few_results`; retry
  first, since a partial search outage looks the same, then widen the area or
  accept). `"curated"` = plenty qualified and the ranker picked fewer because
  the rest fit worse; widening will not lengthen it. `null` = the list is
  full. The field is always present (nullable).
- `intent`: echo of how the query was parsed (`call_intent` is
  `reservation`, `availability_check`, `price_check` or `general_inquiry`).
  The fastest way to explain a bad list is a wrong `city` or
  `target_datetime` here.

### Suggest errors
- `402 quota_exceeded`: the balance cannot cover the request; nothing was
  searched. Stop and tell the user
  ([When credits run out](credits.md#when-credits-run-out)).
- `403 account_suspended`: stop.
- `422 QUERY_UNPARSEABLE`: the text names no findable-place task (a greeting,
  gibberish), or the whole request was impossible; the `hint` says which.
- `422 LOCATION_REQUIRED`: "near me" with no location.
- `422 NO_PLACES_FOUND`: zero cards is never a `200`. When the requested time
  emptied the list the `hint` says so: change the time, don't widen.
- `422 REGION_NOT_SUPPORTED`: places found, all in a region we do not call;
  widening cannot help.
- `422 invalid_target_phone`: bad `callback_phone`. A callback number the
  dialing policy refuses gets the same body as on `POST /calls`.
- `429 SUGGEST_RATE_LIMITED`: honor `Retry-After`; `scope` is `minute` or
  `day`.
- `502 PLACES_UPSTREAM_ERROR`: retry is safe.
- `503 PLACE_SUGGESTIONS_DISABLED`: feature off on this deployment, not
  transient.
- `503 SUGGEST_LIMIT_UNAVAILABLE` / `503 maintenance`: retry shortly.
- `504 SUGGEST_DEADLINE_EXCEEDED`: retry once.

Every one of these is free. Only an answered request bills.
