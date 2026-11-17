# Stripe webhooks

What Stripe's documentation said on the date at the end of this file, for an endpoint that credits money. The general pattern is in [verify-signatures.md](verify-signatures.md) and [process-events-once.md](process-events-once.md). Recheck the linked pages before relying on a number.

## Authentication

- Header `Stripe-Signature`, comma-separated entries: `t=<unix seconds>`, one or more `v1=<signature>`, and in a sandbox a `v0=` entry. Stripe may add `secret=`, `destination=` and `payload=` debug entries. They are not covered by the HMAC. Accept unknown entries and never depend on the count or order of entries.
- Signed text: the `t` value, the character `.`, and the raw request body. HMAC-SHA256 with the endpoint signing secret as the key. The libraries compare lower-case hex.
- Use only `t` and `v1`. Stripe says to ignore every other scheme to prevent downgrade attacks. `v0` is not valid for verification.
- `v1` can appear more than once. Accept the event when any `v1` matches.
- The `verifyTimestamped` function in [verify-signatures.md](verify-signatures.md) is this scheme. Read the header `stripe-signature`.

With the official library, give it the raw body:

```js
import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
const endpointSecret = process.env.STRIPE_WEBHOOK_SECRET; // required at start-up, no default

export function verifyStripeEvent(rawBody, signatureHeader) {
  try {
    // Checks that one v1 entry matches and that t is not older than 300 seconds.
    return stripe.webhooks.constructEvent(rawBody, signatureHeader, endpointSecret);
  } catch {
    return null; // StripeSignatureVerificationError: answer 400
  }
}
```

`constructEvent` throws on a missing header, no `v1` entry, no match, and a timestamp older than the tolerance (300 seconds unless a fourth argument changes it). stripe-node and stripe-python reject only timestamps that are too old; a timestamp an hour in the future passed stripe-node 23.1.0 on the date below. stripe-php rejects both directions. Python: `stripe.Webhook.construct_event(payload, sig_header, secret)`. PHP: `\Stripe\Webhook::constructEvent($payload, $sigHeader, $secret)`. A tolerance of 0 switches the time check off.

## Secret and rotation

- Each endpoint has its own secret, starting with `whsec_`. Workbench: open the endpoint, "Reveal secret". A test and a live endpoint have different secrets. The library uses the whole string, prefix included, as the HMAC key.
- `stripe listen` prints its own `whsec_` secret, different from the Dashboard endpoint's. It stays the same between restarts of `listen`. Using the wrong one of the two is the cause Stripe names first for failed verification.
- "Roll secret" expires the old secret at once or after up to 7 days. Until then Stripe sends one `v1` per active secret, so a verifier that holds either secret passes. Roll with a delay, deploy the new secret, and remove the old one from the configuration after it expired.

## Raw body

Stripe requires the unmodified body. Frameworks that parse, reorder keys, strip whitespace or change the encoding break verification. In Express the webhook route goes before `app.use(express.json())`. Exempt the route from CSRF protection. See [webhook-stacks.md](webhook-stacks.md).

## Timestamp and replay

- Library default tolerance: 5 minutes. Keep the server clock synchronized with NTP.
- Each retry is signed again with a new timestamp, so the tolerance does not have to cover the retry schedule.
- The stored event id is the replay protection inside the window.

## Delivery

- Live mode: retries for up to three days with exponential backoff. Sandbox: three retries over a few hours.
- Success is a 2xx. A redirect counts as a failure, as do 4xx and 5xx and a timeout. Stripe does not state the timeout in seconds. Answer quickly and defer slow work.
- A Dashboard resend works for 15 days after the event was created, `stripe events resend` for 30 days. A manual resend does not stop the automatic retries.
- Order is not guaranteed. Stripe says not to use `created` to order events or to detect duplicates.

## Event id

- Deduplicate on `event.id`. Stripe also says that two separate events can be generated for one change: then the object id in `data.object` together with `event.type` identifies the duplicate. This is the business key layer in [process-events-once.md](process-events-once.md).
- Stripe documents that each retry gets a new signature and timestamp. It does not say in so many words that the event id stays the same, but its duplicate guidance rests on it.

## Events that move money

Amounts are integers in the currency's minor unit. Zero-decimal currencies such as JPY exist: never divide by 100 by habit.

| Event | Meaning | What the handler does |
| --- | --- | --- |
| `checkout.session.completed` | Checkout finished. `payment_status` is `paid`, `unpaid` or `no_payment_required` | Grant only when `payment_status` is not `unpaid` |
| `checkout.session.async_payment_succeeded` | A delayed payment method succeeded later | Grant. Without it, bank debits and similar methods are never credited |
| `checkout.session.async_payment_failed` | The delayed payment failed | Close the order, grant nothing |
| `payment_intent.succeeded` | PaymentIntent paid. `amount_received` | Grant, when the app does not use Checkout events for the same order |
| `invoice.paid` | Invoice payment succeeded or marked paid out of band. `amount_paid` | Extend the period. Stripe says to retrieve the subscription and confirm it is `active` |
| `invoice.payment_failed` | Renewal payment failed | Start the app's grace rule, do not revoke at once unless decided |
| `customer.subscription.updated`, `customer.subscription.deleted` | Plan or status changed; subscription ended | Newer-wins update of the subscription row |
| `refund.created`, `refund.updated`, `refund.failed` | A refund and its status | To the reversal code. Stripe recommends at least `refund.created` |
| `charge.refunded` | A charge was refunded, also partially. `amount_refunded` is the running total, `refunded` is true only when full | Use either this or the `refund.*` events as the refund source, not both |
| `charge.dispute.created`, `charge.dispute.closed` | Dispute opened; closed as `won`, `lost` or `warning_closed` | To the reversal code |
| `charge.dispute.funds_withdrawn`, `charge.dispute.funds_reinstated` | Money left or came back for a dispute | Same dispute id as above, not a second dispute |

The mapping of refund and dispute events to the reversal code is in the `handle-refunds-and-reversals` skill.

## Payload or API

The object in a snapshot event can be outdated by the time it is processed. Stripe's guidance is to fetch the current object from the API before acting on it. Stripe's Checkout fulfillment guide retrieves the session before fulfilling. Stripe now recommends thin events for new integrations: they carry only ids, are verified with `parseEventNotification()` instead of `constructEvent()`, and the handler fetches the object. Check `livemode` against the environment. If the handler compares it with a setting, production needs the matching value or every live event is refused, so list that setting as a visible deploy step next to the signing secret. The payload of a snapshot destination uses the API version fixed when the destination was created.

## Test locally

```bash
stripe listen --forward-to localhost:3000/webhooks/stripe --events checkout.session.completed,refund.created
stripe trigger payment_intent.succeeded
```

The CLI reference says `--forward-to` needs `--events`, `--all-snapshot` or `--all-thin`. `stripe trigger` creates real test-mode objects. For probes without the CLI, `assets/sign-test-event.mjs stripe` signs a test event with the local test secret.

## Bugs that ship

- `express.json()` or a framework parser runs before verification, verification fails, and someone switches it off.
- The CLI secret in production, or the live secret in a test environment.
- Granting on `checkout.session.completed` without checking `payment_status`, and never handling `async_payment_succeeded` or `async_payment_failed`.
- Handling only the success event: `refund.*`, `charge.refunded` and `charge.dispute.*` answered 200 and dropped.
- Taking a refund back twice, once from `charge.refunded` and once from `refund.created`.
- Crediting `amount` from the payload instead of the order's price, or dividing by 100 for a zero-decimal currency.
- Deduplicating on `created` or on the PaymentIntent id alone, which stops a second legitimate event type for the same object.
- Parsing the header by position, which breaks when Stripe adds a debug entry or a second `v1`.
- Treating the `secret=` or `payload=` debug entry as proof of anything.

## Sources

- https://docs.stripe.com/webhooks
- https://docs.stripe.com/events/manage-webhook-endpoints
- https://docs.stripe.com/events/how-events-work
- https://docs.stripe.com/api/events/types
- https://docs.stripe.com/api/charges/object
- https://docs.stripe.com/api/refunds/object
- https://docs.stripe.com/api/disputes/object
- https://docs.stripe.com/refunds
- https://docs.stripe.com/checkout/fulfillment
- https://docs.stripe.com/billing/subscriptions/webhooks
- https://docs.stripe.com/currencies
- https://docs.stripe.com/cli/listen
- https://docs.stripe.com/cli/trigger
- https://github.com/stripe/stripe-node/blob/master/src/Webhooks.ts

Checked 2026-11-15.
