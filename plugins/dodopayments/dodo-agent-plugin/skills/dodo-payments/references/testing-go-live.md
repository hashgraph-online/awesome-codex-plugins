# Testing and go-live

## Contents

- [Test mode](#test-mode)
- [Test payment methods](#test-payment-methods)
- [Simulate a renewal](#simulate-a-renewal)
- [Dodo CLI sign-in](#dodo-cli-sign-in)
- [Webhooks on localhost](#webhooks-on-localhost)
- [Move products to live mode](#move-products-to-live-mode)
- [Go-live checklist](#go-live-checklist)
- [Common mistakes](#common-mistakes)

## Test mode

Develop with `environment: 'test_mode'` and a `dodo_test_` key from the dashboard. The SDK defaults to live mode, so always pass the option. Test mode (`https://test.dodopayments.com`) and live mode (`https://live.dodopayments.com`) share nothing: keys, products, customers, webhook endpoints and secrets are all separate.

## Test payment methods

Cards work with expiry 06/32 (or 12/34) and CVC 123.

| Card | Result |
|---|---|
| `4242 4242 4242 4242` | Succeeds |
| `4000 0000 0000 0002` | Declined |
| `4000 0000 0000 9995` | Declined, insufficient funds |
| `4000 0000 0000 0341` | Succeeds now, declines at the next subscription charge (renewal or plan change) |

To test a failed renewal, subscribe with `4242...`, switch the payment method to `...0341` in the customer portal, then simulate a renewal.

UPI (billing country `IN`, currency `INR`): `success@upi` succeeds and `failure@upi` fails. Only use methods listed on the docs Testing Process page; other card numbers are not supported.

## Simulate a renewal

Move `next_billing_date` to now to trigger the renewal:

```typescript
await client.subscriptions.update('sub_123', { next_billing_date: new Date().toISOString() });
```

```python
from datetime import datetime, timezone

client.subscriptions.update("sub_123", next_billing_date=datetime.now(timezone.utc))
```

With the `...0341` card this sends `payment.failed` and `subscription.on_hold`.

## Dodo CLI sign-in

```bash
npm i -g dodopayments-cli@latest
dodo login            # opens a Dodo Payments consent page in the browser
dodo login --device   # over SSH or with no browser: enter the code on another device
dodo whoami           # show the current sign-in
dodo logout all       # sign out (or: dodo logout test, dodo logout live)
```

`dodo login` signs in with OAuth: pick the business, the mode and the permissions on the consent page. You do not paste an API key. Review or revoke the CLI's access in the dashboard under **Settings > Connected Apps**.

## Webhooks on localhost

Forward real, signed test-mode webhooks to a local URL (needs a test-mode sign-in):

```bash
dodo wh listen http://localhost:3000/webhook
```

It relays over an outbound connection; it does not give you a public URL. Verify these with `unwrap()` as usual. The relay re-serialises the JSON body, so a rare byte difference (for example number formatting) can fail verification; that is the relay, not your code.

Send an unsigned sample payload without signing in:

```bash
dodo wh trigger payment.success http://localhost:3000/webhook
```

Trigger names differ from payload `type`: `payment.success` sends `payment.succeeded`, `refund.success` sends `refund.succeeded`, `licence.created` sends `license_key.created`. Switch on the payload `type`. These payloads are unsigned, so only a local test handler may read them with `unsafeUnwrap()`. `subscription.past_due` and `subscription.unpaused` cannot be triggered.

To register a public HTTPS URL in the dashboard instead, run a tunnel such as `ngrok http 3000`.

## Move products to live mode

Product IDs do not carry over. Recreate each product in live mode (dashboard, or read it with a test key and create it with a live key) and switch your code to the live IDs. Ask the user to confirm before creating anything in live mode.

```typescript
const testClient = new DodoPayments({ bearerToken: process.env.DODO_PAYMENTS_TEST_API_KEY, environment: 'test_mode' });
const liveClient = new DodoPayments({ bearerToken: process.env.DODO_PAYMENTS_LIVE_API_KEY, environment: 'live_mode' });

const source = await testClient.products.retrieve('pdt_test_123');
const created = await liveClient.products.create({
  name: source.name ?? 'Untitled',
  price: source.price,
  tax_category: source.tax_category,
});
console.log(created.product_id);
```

## Go-live checklist

- [ ] KYC and business verification are approved in the dashboard.
- [ ] A `dodo_live_` key is set on the server only, with `environment: 'live_mode'`.
- [ ] Products exist in live mode and the code uses their IDs.
- [ ] A live webhook endpoint (public HTTPS) is registered and `DODO_PAYMENTS_WEBHOOK_KEY` holds the live secret.
- [ ] The handler verifies signatures with `unwrap()` and no `unsafeUnwrap()` remains.
- [ ] Return URLs point at the production domain.
- [ ] One real low-value purchase and refund were tested end to end.
- [ ] Monitoring covers payment failures, webhook errors and disputes.

## Common mistakes

- Leaving `environment` unset in development, which hits live mode.
- Using a test product ID or test webhook secret in production.
- Using a test key against live mode or the reverse; it fails authentication.
- Switching on trigger names (`payment.success`) instead of payload types.
