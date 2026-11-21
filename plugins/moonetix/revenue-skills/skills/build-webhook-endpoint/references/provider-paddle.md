# Paddle Billing webhooks

What Paddle's documentation said on the date at the end of this file, for Paddle Billing (not Paddle Classic). The general pattern is in [verify-signatures.md](verify-signatures.md) and [process-events-once.md](process-events-once.md). Recheck the linked pages before relying on a number.

## Authentication

- Header `Paddle-Signature`, for example `ts=1671552777;h1=eb4d0d...`. Split on `;` into elements, then on `=` into key and value.
- Signed text: the `ts` value, the character `:`, and the raw request body. HMAC-SHA256 with the destination's secret key. Paddle's samples compare lower-case hex.
- The key is the secret string as shown, not decoded.
- Paddle says there is at least one `h1`, and that during secret rotation more than one `h1` is sent. Accept the event when any `h1` matches.

```js
import { createHmac, timingSafeEqual } from 'node:crypto';

// Paddle-Signature: ts=<unix seconds>;h1=<hex HMAC-SHA256 of "<ts>:<raw body>">, h1 possibly repeated.
export function verifyPaddle(rawBody, header, secrets, toleranceSeconds = 5, nowSeconds = Date.now() / 1000) {
  let ts = null;
  const given = [];
  for (const part of String(header ?? '').split(';')) {
    const [name, value = ''] = part.trim().split('=');
    if (name === 'ts' && /^\d{1,12}$/.test(value)) ts = value;
    if (name === 'h1' && /^[a-f0-9]{64}$/i.test(value)) given.push(Buffer.from(value, 'hex'));
  }
  if (ts === null || given.length === 0 || !Buffer.isBuffer(rawBody)) return false;
  if (Math.abs(nowSeconds - Number(ts)) > toleranceSeconds) return false;
  let matched = false;
  for (const secret of secrets) {
    const expected = createHmac('sha256', secret).update(`${ts}:`).update(rawBody).digest();
    for (const signature of given) if (timingSafeEqual(signature, expected)) matched = true;
  }
  return matched;
}
```

Official SDK helpers, read from their source on the date below:

- Node: `await paddle.webhooks.unmarshal(rawBody, secretKey, signature)` throws on failure, `await paddle.webhooks.isSignatureValid(...)` returns a boolean. Both check the time in both directions (5 seconds). With two `h1` entries, @paddle/paddle-node-sdk 3.12.0 compared only the last one.
- Python: `Verifier().verify(request, Secret(key))` checks every `h1` against every secret. When the environment variable `TEST_MODE` is set to `1`, it skips the time check. Make sure production does not set it.
- PHP: `(new Verifier())->verify($psr7Request, new Secret($key))`. A `maximumVariance` of 0 or null switches the time check off.

## Secret and rotation

- Paddle generates a secret key per notification destination. It is shown when the destination is edited in the dashboard. Over the API it is `endpoint_secret_key` of the notification setting. Each destination has its own key: the key of another destination fails.
- Paddle documents no rotation procedure beyond the multiple `h1` sentence. Its guidance for a key that may be compromised is to delete the destination and create a new one. Before that, add the new destination's key to the verifier's list and deploy.

## Raw body

Paddle says not to transform the body in any way, not even whitespace. Its Node sample uses `express.raw`. See [webhook-stacks.md](webhook-stacks.md).

## Timestamp and replay

- Paddle's SDKs reject a `ts` more than five seconds from the current time. Paddle's manual samples check only "too old". Five seconds is tight: keep the clock synchronized and verify before any other work. Paddle's troubleshooting advice is to use the simulator rather than replaying saved payloads.
- The documentation does not say whether a retry carries a new `ts`. The SDKs' five-second check would refuse every retry that kept the first one. Watch a failed sandbox delivery and its retries before relying on either reading.

## Delivery

- Answer 200 within five seconds, before internal processing. Only 200 counts as delivered.
- Sandbox: 3 attempts within about two minutes. Live: up to 60 attempts over about two days, the wait before attempt n being about `60 * n^1.1` seconds.
- A failed notification can be replayed through the API (`POST /notifications/{id}/replay`) for up to 90 days.
- Order is not guaranteed. Paddle says to store `occurred_at` and compare it before changing state: the newer-wins pattern.
- Paddle also publishes IP addresses per environment, and advises letting the webhook path past WAF bot checks.

## Event id

- `event_id` (`evt_...`) identifies the event: deduplicate on it. Paddle guarantees at-least-once delivery.
- `notification_id` (`ntf_...`) identifies one delivery to one destination. A replay creates a new notification with the same `event_id`. Do not deduplicate on `notification_id`.

## Events that move money

Amounts are strings that hold integers in the lowest denomination of the currency, for example `"1000"` for 10 USD. Parse them as integers, never as floats.

| Event | Meaning | What the handler does |
| --- | --- | --- |
| `transaction.paid` | Payment captured. Fees, earnings and some ids may still be missing | Grant here when access must not wait, or wait for `completed`. Pick one and key the grant on the transaction id |
| `transaction.completed` | Paddle finished its processing. `details.totals.grand_total`, `currency_code` | Grant, or confirm the grant from `paid` |
| `subscription.past_due` | A renewal is unpaid, Paddle retries per dunning settings | Apply the app's grace rule |
| `subscription.canceled` | Cancelled. With a scheduled cancel, `subscription.updated` comes first | End access at the period end the payload states |
| `adjustment.created`, `adjustment.updated` | Refund, credit or chargeback. `action`: `refund`, `credit`, `chargeback`, `chargeback_warning`, `chargeback_reverse` and reverse actions. `status`: `pending_approval`, `approved`, `rejected`, `reversed`. `type`: `full` or `partial`. `transaction_id` links the original | To the reversal code. Most live refunds start as `pending_approval` and are approved or rejected later. Paddle says to listen for `adjustment.created` so that none is missed |

The mapping of adjustments to the reversal code is in the `handle-refunds-and-reversals` skill.

## Payload or API

The `data` object is a snapshot of the entity when the event occurred. Paddle documents no rule to refetch before acting. It recommends a periodic reconciliation job that lists entities through the API and repairs drift. Grant from the app's own order; compare `grand_total` and `currency_code` with it.

## Test locally

- The webhook simulator sends signed test events, single events or scenarios, in sandbox and live. Only destinations whose traffic source is `simulation` or `all` receive them.
- In the sandbox, Paddle approves refunds every ten minutes, which lets a test see `adjustment.updated`.
- Paddle names Hookdeck CLI for reaching a local endpoint. For probes, `assets/sign-test-event.mjs paddle` signs a test event; send it within five seconds or raise the tolerance only in the test configuration.

## Bugs that ship

- Parsing the body before verifying, or verifying a re-serialized object.
- Requiring exactly two parts in the header, as Paddle's manual sample does, which fails as soon as a second `h1` arrives.
- Deduplicating on `notification_id`, so a replay credits again.
- `TEST_MODE=1` or a variance of 0 in production, which removes the time check.
- Treating `adjustment.created` with `pending_approval` as money already returned, or ignoring `adjustment.updated` and never applying the approval.
- Ignoring `chargeback` and `chargeback_reverse`.
- Reading amount strings as floats.
- Granting twice, on `transaction.paid` and again on `transaction.completed`, without a key on the transaction id.

## Sources

- https://developer.paddle.com/webhooks/about/signature-verification
- https://developer.paddle.com/webhooks/about/how-webhooks-work
- https://developer.paddle.com/webhooks/about/respond-to-webhooks
- https://developer.paddle.com/webhooks/about/notification-destinations
- https://developer.paddle.com/api-reference/notifications/replay-notification
- https://developer.paddle.com/webhooks/transactions/transaction-paid
- https://developer.paddle.com/webhooks/transactions/transaction-completed
- https://developer.paddle.com/webhooks/adjustments/adjustment-created
- https://developer.paddle.com/webhooks/adjustments/adjustment-updated
- https://developer.paddle.com/build/transactions/create-transaction-adjustments
- https://developer.paddle.com/webhooks/subscriptions/subscription-past-due
- https://developer.paddle.com/webhooks/subscriptions/subscription-canceled
- https://developer.paddle.com/webhooks/simulator
- https://github.com/PaddleHQ/paddle-node-sdk
- https://github.com/PaddleHQ/paddle-python-sdk
- https://github.com/PaddleHQ/paddle-php-sdk

Checked 2026-11-15.
