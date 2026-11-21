# RevenueCat webhooks

What RevenueCat's documentation said on the date at the end of this file. RevenueCat forwards purchases made in the app stores, on the web and through its own billing, so one endpoint sees events from several stores. The general pattern is in [verify-signatures.md](verify-signatures.md) and [process-events-once.md](process-events-once.md). Recheck the linked pages before relying on a number.

## Authentication

Two mechanisms, both set on the webhook integration in the dashboard.

- **Authorization header.** A value the app chooses, sent unchanged in the `Authorization` header of every request. RevenueCat says to check it on every notification. It proves the sender, not the body. Compare in constant time, after hashing both sides so the lengths match.
- **HMAC signing**, optional, switched on per integration. Header `X-RevenueCat-Webhook-Signature: t=<unix seconds>,v1=<hex HMAC-SHA256>`. Signed text: the `t` value, `.`, and the raw body. This is the scheme of `verifyTimestamped` in [verify-signatures.md](verify-signatures.md); read the header `x-revenuecat-webhook-signature`.

Use both: the HMAC covers the body, the header covers the integration being the one configured.

```js
import { createHash, timingSafeEqual } from 'node:crypto';

const digest = (value) => createHash('sha256').update(String(value ?? '')).digest();

// expected: the authorization value configured in RevenueCat, required at start-up.
export function authorizationMatches(received, expected) {
  return timingSafeEqual(digest(received), digest(expected));
}
```

RevenueCat documents no source IP ranges for webhooks and no server library that verifies them. Its webhook page has verification snippets in Python, Node.js, Ruby, Go and PHP.

## Secret and rotation

- The HMAC signing secret is shown once, when signing is switched on or the secret is rotated, and cannot be read again. Store it then.
- "Rotate secret" invalidates the old secret immediately. There is no overlap: requests signed during the switch fail and are retried. Deploy the new secret within the retry window (about 80 minutes), then retry the failed deliveries from the dashboard.
- The authorization header value can be changed at any time in the integration settings. No overlap is documented for it either.

## Raw body

Not needed for the authorization header. Needed for the HMAC: RevenueCat says to compute it over the raw bytes before any JSON parsing. See [webhook-stacks.md](webhook-stacks.md).

## Timestamp and replay

- `t` is the time RevenueCat signed this HTTP request, recomputed on every attempt, including retries and a manual retry. RevenueCat suggests refusing requests where it differs from now by more than a tolerance, for example 5 minutes, and says not to size the tolerance to the retry window.
- `event.event_timestamp_ms` is when the event was generated, and retries reuse it. It is not a freshness check.
- With only the authorization header, a captured request can be sent again at any time. The stored event id is then the only replay protection.

## Delivery

- Success is exactly 200. Any other status is a failure.
- Up to 5 retries with exponential backoff, about 2.5, 5, 10, 20 and 40 minutes with jitter, about 80 minutes in all. Then RevenueCat stops.
- RevenueCat disconnects after 60 seconds and recommends answering quickly and processing after the response.
- Delivery is at least once. Order is not guaranteed: RevenueCat says `BILLING_ISSUE`, `CANCELLATION` and `EXPIRATION` are sent at the same time and can arrive in a different order.
- A failed delivery can be retried from the dashboard. Events that happen while the integration is disabled are never sent.

## Event id

Deduplicate on `event.id`. RevenueCat says retries reuse the same id, and recommends tracking it so each event is processed once. Use `transaction_id` as the business key of a purchase.

## Events that move money

The body is `{ "api_version": "1.0", "event": { ... } }`. `price` is in USD, `price_in_purchased_currency` in `currency`. Both can be null, 0 for free trials, and negative for refunds. Many fields are present only sometimes: parse defensively. `environment` is `SANDBOX` or `PRODUCTION`.

| Event type | Meaning | What the handler does |
| --- | --- | --- |
| `INITIAL_PURCHASE`, `RENEWAL` | A subscription was bought or renewed | Grant the period. Google Play resubscribes can arrive as `RENEWAL` |
| `NON_RENEWING_PURCHASE` | A purchase that does not renew, such as a credit pack | Grant. Entitlements granted from the RevenueCat dashboard also arrive as this type, with `store` and `period_type` set to `PROMOTIONAL` |
| `PRODUCT_CHANGE` | A plan change, not necessarily in effect yet | Do not grant from this event alone |
| `CANCELLATION` | Cancelled or refunded. `cancel_reason` `CUSTOMER_SUPPORT` means a refund | A refund goes to the reversal code. Other reasons end access at expiry |
| `EXPIRATION` | Access should be removed | End access |
| `BILLING_ISSUE` | A renewal payment failed | The app's grace rule. Not expiry |
| `SUBSCRIPTION_PAUSED` | Google Play pause scheduled | Do not revoke. Revoke on `EXPIRATION` with reason `SUBSCRIPTION_PAUSED` |
| `REFUND_REVERSED` | App Store refund reversed | Give back what the refund took |
| `VIRTUAL_CURRENCY_TRANSACTION` | RevenueCat virtual currency moved; purchases and refunds both send it | Apply `adjustments[].amount` (positive or negative) under `virtual_currency_transaction_id` |
| `TRANSFER` | Purchases moved to another app user | Move entitlements, not money |
| `TEMPORARY_ENTITLEMENT_GRANT` | Access for at most 24 hours during a store outage | Temporary access only. Expect `INITIAL_PURCHASE` or `EXPIRATION` after it |

RevenueCat says a subscription refund sends `CANCELLATION` only when the latest period is refunded; refunds of earlier periods send nothing. Reconcile with the API for those. The mapping to the reversal code is in the `handle-refunds-and-reversals` skill.

## Payload or API

RevenueCat recommends calling `GET /subscribers/{app_user_id}` after receiving any webhook, and storing what it returns. That makes every event a signal to sync, with one data shape. Credits for consumables still need a once-only key: `transaction_id`.

Find the user by `original_app_user_id` and the `aliases` array, as RevenueCat advises. After an anonymous user logs in, `original_app_user_id` is the anonymous id. Check `environment`: by default sandbox purchases also grant entitlements in RevenueCat (Project settings, sandbox access), and one customer can have both kinds of transaction.

## Test locally

The integration's "Send test event" sends a `TEST` event, also while the integration is disabled. Sandbox purchases send real events with `environment` `SANDBOX`. A separate integration can be filtered to sandbox events and pointed at a test backend. For probes, `assets/sign-test-event.mjs revenuecat` signs a test event with the local test secret.

## Bugs that ship

- Checking the authorization header with `==`, or only when it is present.
- Granting sandbox purchases in production because `environment` is never read.
- Crediting a pack on every `NON_RENEWING_PURCHASE`, including promotional grants from the dashboard.
- Looking users up by `app_user_id` only, so purchases of a user who logged in after buying go to nobody or to the anonymous id.
- Treating every `CANCELLATION` as a refund, or none of them.
- Revoking on `BILLING_ISSUE` or `SUBSCRIPTION_PAUSED`.
- Doing the work before answering and exceeding 60 seconds, so the event is retried while it is still running.

## Sources

- https://www.revenuecat.com/docs/integrations/webhooks
- https://www.revenuecat.com/docs/integrations/webhooks/event-types-and-fields
- https://www.revenuecat.com/docs/integrations/webhooks/sample-events
- https://www.revenuecat.com/docs/integrations/webhooks/event-flows
- https://www.revenuecat.com/docs/customers/identifying-customers
- https://www.revenuecat.com/docs/projects/sandbox-access
- https://www.revenuecat.com/docs/dashboard-and-metrics/customer-profile

Checked 2026-11-15.
