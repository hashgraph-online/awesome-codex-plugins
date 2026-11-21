# Unverified inbound events

**Class id:** `unverified-events`

The app credits an account because a message said so: a payment webhook, an app store notification, an offerwall postback, an ad reward callback. If anyone can send that message, anyone can credit themselves.

## Where to look

Every "in" row of the money map whose caller is another company's server, plus any page a payment provider redirects the user back to.

## Shapes that are bugs

**Verification that can be skipped.**

```js
const sig = req.headers['x-signature'];
if (sig && !verify(req.rawBody, sig, SECRET)) return res.status(400).end();   // no header, no check
```

```python
if settings.DEBUG or request.GET.get("test") == "1":      # the caller decides whether to be checked
    return credit(user, amount)
```

**A secret that is not secret.** A fallback such as `process.env.WEBHOOK_SECRET || 'changeme'`, an empty string, a value committed to the repository, or the same key used in the client.

**The signature is computed over the wrong bytes.** The provider signs the raw request body. Code that verifies `JSON.stringify(req.body)` after a JSON parser has run will either reject genuine events or, when the developer "fixed" that, skip verification. Look for a raw-body capture on that route.

**The result is ignored.** `verify(...)` is called and its return value is not used, or an exception is caught and execution continues.

**Verified, but not what matters.** The signature covers the message, yet the handler credits an amount, a user or a currency that the signature does not cover, or that is read from a query string next to the signed body. For hash-style postbacks, read the provider's formula and check that every field the handler acts on (user, reward, status) is inside the hash.

**The event is real but says something else.** A handler that credits on any event type, or on `payment.created` rather than the event that means money arrived. A handler that never compares the paid amount and currency with the order.

**Trusting the return URL.** `GET /payment/success?order=123` marks the order paid because the browser arrived there. The user controls that request. Only the server-to-server notification or a server-side API call to the provider proves payment.

**Trusting the network path.** An IP allowlist read from `X-Forwarded-For` without a trusted proxy in front, or an allowlist as the only check on an endpoint reachable from the internet.

**String comparison of signatures.** `==` on hex strings leaks timing. Alone it is low severity; report it together with a stronger flaw or on its own as low.

## What correct looks like

- Verification is unconditional and happens before parsing or any database work.
- It runs over the raw body, with a secret that has no default and is required at start-up.
- Timestamped schemes reject messages outside a short window (five minutes is common).
- Comparison is constant-time.
- After verification the handler still checks the content: known order or user, expected amount and currency, an event type that means settled money.
- Where the provider offers no signature (some store notifications), the handler treats the message as a hint and asks the provider's API for the truth.

Check the provider's current documentation for the exact scheme. For Stripe, Paddle, Lemon Squeezy, PayPal, RevenueCat, App Store and Google Play integrations, the shapes to look for are in [payment-providers.md](payment-providers.md). Common ones: an HMAC-SHA256 of `timestamp.body` in a header with `t=` and `v1=` parts; an HMAC of the raw body in a single header; a signed JWS payload whose certificate chain must be verified; a shared value in the `Authorization` header; a hash query parameter over named fields for postbacks.

## How to prove it

```bash
node scripts/probe.mjs send webhook.json --drop-header x-signature --observe me.json   # unsigned
node scripts/probe.mjs send webhook.json --set-body data.amount_cents=1                # tampered, old signature
node scripts/probe.mjs send postback.json --drop-query hash --set-query NAME=VALUE     # a bypass switch the handler reads
node scripts/probe.mjs send postback.json --set-query reward=99999                     # field outside the hash
```

A 2xx answer together with a balance change is the proof. A 2xx alone is not: some handlers acknowledge everything and act on nothing.

## Not a bug

- The signature is verified by middleware, an API gateway or the provider's SDK before the handler runs. Find it and name it.
- The endpoint acknowledges unknown event types with 200 and does nothing. That is correct behavior.
- A development-only bypass that is compiled out or guarded by a server-side environment flag the caller cannot influence. Still note it if production configuration could enable it.

## Severity

Unsigned or bypassable credit: critical. Tampering that needs one genuine event first: high. A verified event with no timestamp window, so that a captured one stays valid forever: medium. A flaw that only a partner holding the valid key can use, such as an unknown status that is credited: medium at most, or a note. Timing-unsafe comparison alone: low.
