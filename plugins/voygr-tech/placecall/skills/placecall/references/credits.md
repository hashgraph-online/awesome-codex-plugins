# PlaceCall: Credits & top-ups

Part of the PlaceCall skill ([`SKILL.md`](../SKILL.md)). Read it for what calls and suggestions cost, and what to do on a `402`.

```sh
curl -s -H "X-API-Key: $PLACECALL_API_KEY" https://api.voygr.tech/v1/usage
# {"remaining":...,"quota_limit":...,"current_usage":...,"tier":...}
```
A call costs 10 credits when it obtains something (an answer, a refusal or
a booking), otherwise nothing; voicemails, unanswered lines and busy signals
obtain nothing. It holds 30 credits while it runs and releases the rest when
it ends. A cancel is free within 30 seconds of the callee answering and
charged from 30 seconds on. The hold is larger than the charge, so
`POST /calls` can return `402` while your balance still covers the charge
alone: keep headroom per concurrent call. Place suggestions draw on the same
balance: 5 credits per answered `POST /v1/places/suggest`, nothing for a
refusal (see [Suggest errors](suggest.md#suggest-errors)). The free tier is one shared
pot. The 250 free calls are 2,500 credits, and suggestions draw on the same
2,500, so searching before every call gets you fewer than 250 of them.
Current rates are at <https://api.voygr.tech/checkout>.

Top-ups are self-serve: <https://api.voygr.tech/checkout?src=claude-plugin>
(Stripe-hosted payment; credit packs listed at `GET /checkout/packs`).

## When credits run out

A `402` from a billed request (`POST /calls` or `POST /v1/places/suggest`)
means the balance cannot cover this request. Nothing was dialed or searched,
and nothing was charged. The body is:

```json
{"detail": {"error": "quota_exceeded", "needed_credits": N, "checkout_url": "/checkout/buy"}}
```

- `needed_credits`: the credits this request needed to hold.
- `checkout_url`: relative to `https://api.voygr.tech`. It is the API behind
  the checkout page (a `POST` that needs the key and a chosen pack), not a
  page to open. Send the user to the page below instead.
- Some responses still carry only `{"detail": {"error": "insufficient credits"}}`.
  Same meaning, same handling: branch on the `402` status, not on the text.
  That body has no `needed_credits`: for a call, use `call_credit_hold` from
  `GET /v1/usage` instead; for anything else, retry at most once (step 1).

What to do, every time:

1. **Stop. Do not retry blindly.** That covers the same request, a different
   number and the next call of a batch. One exception: holds on calls still
   in flight come back as they settle (in full on a free outcome), which can
   clear the `402` without a top-up. Wait for them, check `GET /v1/usage`,
   and retry once only if at least `needed_credits` is available. Otherwise
   every retry gets the same `402` until someone pays: go to step 2.
2. Tell the user, in plain words: they are out of PlaceCall credits, and this
   request needed `needed_credits`. They can top up at
   <https://api.voygr.tech/checkout?src=claude-plugin> (paste the key into
   **Buy credits**, pick a pack, pay on Stripe). A key saved by the
   [email-code sign-up](sign-up.md) is in `~/.codex/placecall.env`:
   tell the user the path, don't print the key. Buying credits is the user's
   decision; do not start a purchase for them.
3. Resume only after they say they topped up. Check `GET /v1/usage` (or
   `credits_available` on `GET /users/me`) first; if it still cannot cover
   the request, say so instead of retrying.
