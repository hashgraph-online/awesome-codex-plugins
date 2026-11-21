# Lemon Squeezy webhooks

What Lemon Squeezy's documentation said on the date at the end of this file. The general pattern is in [verify-signatures.md](verify-signatures.md) and [process-events-once.md](process-events-once.md). Recheck the linked pages before relying on a number.

## Authentication

- Header `X-Signature`: the hex HMAC-SHA256 of the raw request body, keyed with the webhook's signing secret. No timestamp, no prefix, one signature.
- The request also carries `X-Event-Name` with the event name. It is not signed: dispatch on `meta.event_name` from the verified body.
- The official JS SDK has no verification helper. The documentation shows code for Node, PHP, Python and Ruby. Its Node sample passes the two hex strings to `timingSafeEqual`, which throws when the lengths differ. Decode and check the length first:

```js
import { createHmac, timingSafeEqual } from 'node:crypto';

// X-Signature: hex HMAC-SHA256 of the raw body. secrets: one, or two during a change.
export function verifyLemonSqueezy(rawBody, header, secrets) {
  if (!Buffer.isBuffer(rawBody) || !/^[a-f0-9]{64}$/i.test(String(header ?? ''))) return false;
  const given = Buffer.from(header, 'hex');
  let matched = false;
  for (const secret of secrets) {
    if (timingSafeEqual(given, createHmac('sha256', secret).update(rawBody).digest())) matched = true;
  }
  return matched;
}
```

PHP, as in the documentation: `hash_equals(hash_hmac('sha256', file_get_contents('php://input'), $secret), $_SERVER['HTTP_X_SIGNATURE'] ?? '')`.

## Secret and rotation

- The secret is chosen when the webhook is created, in the dashboard or with `POST /v1/webhooks`. The documentation describes it as a random string, normally 6 to 40 characters. Generate a long random one; six characters can be guessed offline from one captured request.
- `PATCH /v1/webhooks/:id` replaces the secret. The API never returns it; the dashboard shows it.
- No overlap period is documented: after a change, every event is signed with the new secret. Deploy a verifier that accepts both, then change the secret, then remove the old one.
- Test mode and live mode webhooks are separate. Use a different secret for each.

## Raw body

The documentation's samples sign the raw bytes: `request.rawBody` in Express, `php://input`, `request.body` in Django, `request.raw_post` in Rails, `await request.text()` in its Next.js guide. See [webhook-stacks.md](webhook-stacks.md).

## Timestamp and replay

Nothing in the signature is time-bound, and the documentation gives no replay guidance. A captured request verifies forever. The stored keys below are the only replay protection, so never delete them while the secret is in use.

## Delivery

- Return 200. Any other status is retried up to three more times with exponential backoff, the documented example being 5, 25 and 125 seconds. After the fourth attempt the event is not sent again automatically. Recent deliveries can be resent from the webhook settings.
- The documentation recommends storing the event, answering 200 quickly and processing outside the request.
- The response timeout and the delivery order are not documented. Assume no order.
- The SSL certificate of the URL is verified before sending.

## Event id

The documentation describes no event id or delivery id. The body is `{ "meta": { "event_name", "custom_data" }, "data": { "type", "id", "attributes" } }`. Deduplicate on what the event does, with a business key:

| Event | Key |
| --- | --- |
| `order_created` | (`order`, `data.id`) |
| `subscription_payment_success` | (`subscription_invoice`, `data.id`) |
| `order_refunded` | (`order`, `data.id`, `refunded_amount`), the running-total form |
| `subscription_payment_refunded` | (`subscription_invoice`, `data.id`, `refunded_amount`) |

A resend from the dashboard repeats the same body, so these keys stop it.

## Events that move money

Amounts on orders and subscription invoices are integers in cents of the order currency (`total`, `subtotal`, `refunded_amount`), with `_usd` variants.

| Event | Meaning | What the handler does |
| --- | --- | --- |
| `order_created` | A new order. `status`: `pending`, `failed`, `paid`, `refunded`, `partial_refund`, `fraudulent` | Grant only when `status` is `paid` |
| `subscription_created` | Sent together with `order_created` | Do not grant a second time |
| `subscription_payment_success` | A subscription invoice was paid. `billing_reason`: `initial`, `renewal`, `updated` | Grant renewals here. The initial payment also has an `order_created`: key both on the same fact |
| `subscription_payment_failed`, `subscription_payment_recovered` | Renewal failed; recovered | The app's grace rule. A recovered event comes with a success event |
| `subscription_cancelled`, `subscription_expired` | Cancelled, access until the period end; ended | End access at expiry |
| `order_refunded` | A full or partial refund. `refunded` is true only when full, `refunded_amount` is the total to date | To the reversal code |
| `subscription_payment_refunded` | A subscription payment was refunded | To the reversal code |

Lemon Squeezy documents no dispute or chargeback event. Its help page says it usually refunds a disputed payment on the merchant's behalf and deducts the amount and a dispute fee from the payout. Whether that sends `order_refunded` is not documented: reconcile orders through the API.

## Payload or API

No rule to refetch is documented. The payload has links to related objects that can be read with the API key. Pass the app's own order id in checkout custom data; it comes back in `meta.custom_data` for order, subscription and license key events. Then compare `total` and `currency` with that order before granting, and check `test_mode` on the object against the environment.

## Test locally

- Test mode handles webhooks with test cards. Test events go only to test mode webhooks.
- The dashboard can simulate several order and subscription events for a test mode object. `subscription_payment_*` events need a real renewal first: use a test product with a daily interval.
- For probes, `assets/sign-test-event.mjs lemonsqueezy` signs a test event with the local test secret.

## Bugs that ship

- No deduplication, because there is no event id, so a resend credits again.
- Granting on `order_created` without checking `status`, or granting a subscription twice through `order_created` and `subscription_payment_success`.
- Subtracting `refunded_amount` as if it were the amount of this refund. It is the total to date.
- Dispatching on the unsigned `X-Event-Name` header.
- A short signing secret, which a captured request lets anyone test guesses against.

## Sources

- https://docs.lemonsqueezy.com/help/webhooks/signing-requests
- https://docs.lemonsqueezy.com/help/webhooks/webhook-requests
- https://docs.lemonsqueezy.com/help/webhooks/event-types
- https://docs.lemonsqueezy.com/help/webhooks/simulate-webhook-events
- https://docs.lemonsqueezy.com/guides/developer-guide/webhooks
- https://docs.lemonsqueezy.com/guides/tutorials/webhooks-nextjs
- https://docs.lemonsqueezy.com/api/webhooks/update-webhook
- https://docs.lemonsqueezy.com/api/orders/the-order-object
- https://docs.lemonsqueezy.com/api/subscription-invoices/the-subscription-invoice-object
- https://docs.lemonsqueezy.com/help/payments/refunds-chargebacks
- https://docs.lemonsqueezy.com/help/getting-started/test-mode
- https://github.com/lmsqueezy/lemonsqueezy.js

Checked 2026-11-15.
