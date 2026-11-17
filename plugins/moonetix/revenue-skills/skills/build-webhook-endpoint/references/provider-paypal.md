# PayPal webhooks

What PayPal's developer documentation said on the date at the end of this file, for REST webhooks (not legacy IPN). The general pattern is in [verify-signatures.md](verify-signatures.md) and [process-events-once.md](process-events-once.md). Recheck the linked pages before relying on a number.

## Authentication

PayPal signs with its own certificate. There is no shared secret: the value the app holds is the webhook id of the listener. Two documented methods.

**Self-verification**, which PayPal's webhook guide calls preferred:

- Headers: `PAYPAL-TRANSMISSION-ID`, `PAYPAL-TRANSMISSION-TIME`, `PAYPAL-TRANSMISSION-SIG`, `PAYPAL-CERT-URL`, `PAYPAL-AUTH-ALGO` (`SHA256withRSA` in PayPal's sample).
- Signed text: `<transmission id>|<transmission time>|<webhook id>|<CRC32 of the raw body, in decimal>`. The webhook id is not in the request: it is the id of the listener in the app's settings.
- The signature is base64. It is verified with the public key of the certificate at `PAYPAL-CERT-URL`, downloaded once and cached.
- PayPal's sample fetches whatever URL the header names. A caller who controls that header can point it at a certificate of their own and sign anything. Accept only `https` URLs on the PayPal host that genuine events of that environment use, under `/v1/notifications/certs/`. PayPal's guide shows `api.sandbox.paypal.com` for the sandbox. This host check is this skill's rule, not PayPal's.

```js
import { verify as verifySignature, X509Certificate } from 'node:crypto';
import { crc32 } from 'node:zlib'; // Node 20.15 or 22.2 and later

const certs = new Map();

async function paypalCertificate(certUrl, allowedHosts) {
  const url = new URL(certUrl);
  if (url.protocol !== 'https:' || !allowedHosts.includes(url.hostname) || !url.pathname.startsWith('/v1/notifications/certs/')) {
    throw new Error('certificate URL is not trusted');
  }
  let cert = certs.get(url.href);
  if (!cert) {
    const res = await fetch(url, { redirect: 'error', signal: AbortSignal.timeout(5000) });
    if (!res.ok) throw new Error(`certificate download failed: ${res.status}`);
    cert = new X509Certificate(await res.text());
    certs.set(url.href, cert);
  }
  if (Date.now() < Date.parse(cert.validFrom) || Date.now() > Date.parse(cert.validTo)) throw new Error('certificate expired');
  return cert;
}

// headers: lower-case names. config: { webhookId, certHosts: ['api.sandbox.paypal.com'] } per environment.
export async function verifyPayPal(rawBody, headers, config) {
  const id = headers['paypal-transmission-id'];
  const time = headers['paypal-transmission-time'];
  const signature = headers['paypal-transmission-sig'];
  if (!Buffer.isBuffer(rawBody) || !id || !time || !signature || headers['paypal-auth-algo'] !== 'SHA256withRSA') return false;
  try {
    const cert = await paypalCertificate(String(headers['paypal-cert-url']), config.certHosts);
    const message = `${id}|${time}|${config.webhookId}|${crc32(rawBody)}`;
    return verifySignature('sha256', Buffer.from(message), cert.publicKey, Buffer.from(signature, 'base64'));
  } catch {
    return false;
  }
}
```

**The verify-webhook-signature API.** `POST /v1/notifications/verify-webhook-signature` with an OAuth access token and `auth_algo`, `cert_url`, `transmission_id`, `transmission_sig`, `transmission_time` (from the headers), `webhook_id` and `webhook_event`. It answers 200 in both cases: read `verification_status`, `SUCCESS` or `FAILURE`. PayPal says `webhook_event` must be the event exactly as received; parsing and serializing again can fail verification. So build the request text around the raw body, after checking that the raw body parses as one JSON object, so that it cannot inject fields such as a second `webhook_id`:

```js
export function verifyRequestBody(rawBody, headers, webhookId) {
  const text = rawBody.toString('utf8');
  const parsed = JSON.parse(text); // throws on anything that is not one JSON value
  if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) throw new Error('event is not an object');
  const field = (name) => JSON.stringify(String(headers[name] ?? ''));
  return `{"auth_algo":${field('paypal-auth-algo')},"cert_url":${field('paypal-cert-url')},` +
    `"transmission_id":${field('paypal-transmission-id')},"transmission_sig":${field('paypal-transmission-sig')},` +
    `"transmission_time":${field('paypal-transmission-time')},"webhook_id":${JSON.stringify(webhookId)},"webhook_event":${text}}`;
}
```

This method adds a call to PayPal inside the request and fails when PayPal's API is unreachable: answer 5xx then, so PayPal retries. PayPal's current server SDKs have no webhook verification helper; the old SDK that had one is deprecated.

## Webhook id

- Each listener URL subscribed in an app's settings, or through `POST /v1/notifications/webhooks`, gets a webhook id. Up to 10 listeners per app. Events belong to the app whose credentials made the payment.
- Sandbox and live apps are separate, so their listeners and webhook ids are separate. Configure one per environment. Use the webhook id, not the client id: PayPal's troubleshooting names this mix-up.

## Raw body

The CRC32 is over the original bytes. PayPal's sample uses `express.raw({ type: 'application/json' })`. See [webhook-stacks.md](webhook-stacks.md).

## Timestamp and replay

The webhook guide sets no tolerance for `PAYPAL-TRANSMISSION-TIME`. PayPal's invoicing webhooks page says it must be within 5 minutes, but no page says whether a retry is signed again with a new time. A window that the retries do not fit would refuse genuine retries. Rely on the stored event id, and enforce a window only after the log shows the age of genuine retries.

## Delivery

- Success is any 2xx. Otherwise PayPal retries up to 25 times over 3 days, then marks the delivery failed. It can be resent from the Webhook Events dashboard or with `POST /v1/notifications/webhooks-events/{event_id}/resend`.
- The listener must use HTTPS on port 443.
- The general guides state no timeout and no order guarantee. The invoicing page says to answer within 30 seconds, that the same event can arrive several times, and not to assume order.

## Event id

Deduplicate on the event `id` (`WH-...`). Use the resource id (the capture or refund id) as the business key.

## Events that move money

Amounts are `{ "currency_code", "value" }` with `value` a decimal string such as `"500.00"`; some currencies have no decimals, some three. Convert to integer minor units by parsing the string with the currency's exponent, never through a float. v1 resources (subscription sales) use `{ "total", "currency" }`.

| Event | Meaning | What the handler does |
| --- | --- | --- |
| `CHECKOUT.ORDER.APPROVED` | The buyer approved the order | Not money. Capture it, then wait for the capture event |
| `PAYMENT.CAPTURE.COMPLETED` | The capture completed | Grant, after comparing amount and currency with the order |
| `PAYMENT.CAPTURE.PENDING` | Funds not yet available | Do not grant |
| `PAYMENT.CAPTURE.DECLINED`, `PAYMENT.CAPTURE.DENIED` | Capture failed. Both names appear in the documentation | Close the order |
| `PAYMENT.CAPTURE.REFUNDED` | A refund of a capture. The resource is a refund with `amount`, and `seller_payable_breakdown.total_refunded_amount` to date; its `up` link names the capture | To the reversal code |
| `PAYMENT.CAPTURE.REVERSED` | PayPal reversed a capture | To the reversal code |
| `CUSTOMER.DISPUTE.CREATED`, `.UPDATED`, `.RESOLVED` | A dispute and its outcome | To the reversal code |
| `PAYMENT.SALE.COMPLETED` | A subscription payment | Grant the period |
| `PAYMENT.SALE.REFUNDED`, `PAYMENT.SALE.REVERSED` | A subscription payment returned | To the reversal code |
| `BILLING.SUBSCRIPTION.CANCELLED`, `.EXPIRED`, `.SUSPENDED`, `.PAYMENT.FAILED` | Subscription state | Newer-wins update of the subscription row |

The mapping of refunds and disputes to the reversal code is in the `handle-refunds-and-reversals` skill.

## Payload or API

The general guides give no rule. The invoicing page says to read the current state from the API instead of trusting event order. For captures and disputes, fetch the resource with the app's credentials (`GET /v2/payments/captures/{id}`, `GET /v1/customer/disputes/{id}`) when the event's state matters, and compare the custom id or invoice id the app set at order creation with its own order.

## Test locally

- The Webhooks simulator, or `POST /v1/notifications/simulate-event`, sends mock events to a public HTTPS listener on port 443. Mock events cannot be verified with the verify-webhook-signature API. PayPal says they can be self-verified with the literal webhook id `WEBHOOK_ID`: allow that only in the test configuration.
- Sandbox payments with a sandbox app send real sandbox events that verify both ways.

## Bugs that ship

- Downloading the certificate from any URL the header names.
- Checking the HTTP status of the verify API instead of `verification_status`.
- Sending a re-serialized event to the verify API, failing, and switching verification off.
- Using the client id as the webhook id, or the sandbox webhook id in production.
- Granting on `CHECKOUT.ORDER.APPROVED` or `PAYMENT.CAPTURE.PENDING`.
- Converting `"19.99"` with `parseFloat` and multiplying by 100.
- Subtracting `total_refunded_amount` as if it were this refund's amount.
- Copying the samples on PayPal's invoicing or security pages, which hash the body with SHA-256 or re-serialize it. They contradict the webhook guide's CRC32 method.

## Sources

- https://developer.paypal.com/api/rest/webhooks/rest/
- https://developer.paypal.com/api/rest/webhooks/
- https://developer.paypal.com/api/webhooks/v1/
- https://developer.paypal.com/api/rest/webhooks/event-names/
- https://developer.paypal.com/api/rest/webhooks/simulator/
- https://developer.paypal.com/api/rest/webhooks/events-dashboard
- https://developer.paypal.com/payment-methods/webhooks
- https://developer.paypal.com/subscriptions/webhooks
- https://developer.paypal.com/api/payments/v2/
- https://developer.paypal.com/api/customer-disputes/v1/
- https://developer.paypal.com/api/invoicing/webhooks
- https://developer.paypal.com/security-guidelines

Checked 2026-11-15.
