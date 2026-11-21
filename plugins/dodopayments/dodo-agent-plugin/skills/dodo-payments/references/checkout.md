# Checkout

## Contents

- [Default: hosted checkout session](#default-hosted-checkout-session)
- [Next.js route and button](#nextjs-route-and-button)
- [Checkout session options](#checkout-session-options)
- [Response and return URL](#response-and-return-url)
- [Overlay and inline checkout](#overlay-and-inline-checkout)
- [Static payment links](#static-payment-links)
- [Retrieve and preview](#retrieve-and-preview)
- [Common mistakes](#common-mistakes)

## Default: hosted checkout session

Create a checkout session on the server with `client.checkoutSessions.create(...)` and redirect to `checkout_url`. This covers one-time products, subscriptions, trials, add-ons and discount codes. Grant access from the verified webhook ([webhooks.md](webhooks.md)), not from the redirect.

Exceptions: overlay or inline checkout when the payment form must stay on your page, and static payment links when there is no server at all.

## Next.js route and button

The browser sends a plan slug. The server authenticates the user, maps the slug to an allowlisted product ID, and returns only the URL.

```typescript
// app/api/checkout/route.ts
import { NextResponse } from 'next/server';
import DodoPayments from 'dodopayments';
import { getCurrentUser } from '@/lib/auth';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: process.env.DODO_PAYMENTS_ENVIRONMENT === 'live_mode' ? 'live_mode' : 'test_mode',
});

const PRODUCT_IDS: Readonly<Record<string, string>> = {
  starter: 'pdt_starter_monthly',
  pro: 'pdt_pro_monthly',
};

export async function POST(request: Request) {
  const user = await getCurrentUser();
  if (!user) return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });

  const body = (await request.json().catch(() => null)) as { planId?: unknown } | null;
  const planId = body?.planId;
  if (typeof planId !== 'string' || !Object.hasOwn(PRODUCT_IDS, planId)) {
    return NextResponse.json({ error: 'Unknown plan' }, { status: 400 });
  }

  const session = await client.checkoutSessions.create({
    product_cart: [{ product_id: PRODUCT_IDS[planId], quantity: 1 }],
    customer: user.dodoCustomerId ? { customer_id: user.dodoCustomerId } : { email: user.email, name: user.name },
    metadata: { app_user_id: user.id },
    return_url: `${process.env.NEXT_PUBLIC_APP_URL}/checkout/success`,
  });
  return NextResponse.json({ checkoutUrl: session.checkout_url });
}
```

```tsx
// components/checkout-button.tsx
'use client';

export function CheckoutButton({ planId }: { planId: 'starter' | 'pro' }) {
  async function startCheckout() {
    const response = await fetch('/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ planId }),
    });
    if (!response.ok) return;
    const { checkoutUrl } = (await response.json()) as { checkoutUrl: string };
    window.location.href = checkoutUrl;
  }
  return <button onClick={startCheckout}>Buy</button>;
}
```

Express and FastAPI follow the same shape. The Express webhook route is in [webhooks.md](webhooks.md).

## Checkout session options

Add only the fields the task needs:

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [
    { product_id: 'pdt_pro_monthly', quantity: 1, addons: [{ addon_id: 'adn_extra_seats', quantity: 3 }] },
  ],
  customer: { email: 'customer@example.com', name: 'Jane Doe' }, // or { customer_id: 'cus_...' }
  billing_address: { country: 'US', street: '1 Main St', city: 'San Francisco', state: 'CA', zipcode: '94105' },
  billing_currency: 'EUR', // needs Adaptive Currency, see localized-pricing.md
  tax_id: 'DE123456789',
  customer_business_name: 'Acme GmbH',
  discount_codes: ['WELCOME10'], // up to 20, applied in order
  subscription_data: { trial_period_days: 14 },
  custom_fields: [
    { key: 'company_size', label: 'Company size', field_type: 'dropdown', options: ['1-10', '11-50', '51+'], required: true },
  ],
  metadata: { app_user_id: 'user_123' },
  feature_flags: { allow_discount_code: true, allow_tax_id: true, allow_phone_number_collection: true },
  customization: { theme: 'dark', show_order_details: true, theme_config: { pay_button_text: 'Subscribe' } },
  return_url: 'https://example.com/checkout/success',
});
```

- A checkout session is single-use and expires after 24 hours. Create a new one for each attempt.
- With `confirm: true` the session is finalised at once and expires after 15 minutes. Use it only when you already have every customer field.
- `customer: { email }` attaches the session to an existing customer with that email. `feature_flags.always_create_new_customer: true` forces a new one; leave it off.
- `product_collection_id` sells a product collection; pass `product_cart: []` with it ([products.md](products.md)).
- Mandate-only subscriptions for on-demand charging use `subscription_data.on_demand` ([subscriptions.md](subscriptions.md)).

## Response and return URL

`checkoutSessions.create` returns `session_id` and `checkout_url`. `checkout_url` is null when the session is created with `confirm: true`; then `client_secret`, `publishable_key` and `payment_id` are set for the inline flow. `publishable_key` is a per-session value, not an API key.

After payment the customer lands on `return_url` with query parameters:

```text
https://example.com/checkout/success?payment_id=pay_xxx&status=succeeded&email=customer%40example.com
https://example.com/checkout/success?subscription_id=sub_xxx&status=active&license_key=LK-001
```

- `payment_id` (one-time) or `subscription_id` (subscription). There is no `session_id` parameter.
- `status`: `succeeded` or `active` on success, `failed`, `expired`, or `processing` and `requires_*` while it settles.
- `license_key` (comma-separated) and `email` when available.

Show a "thanks, we are confirming your payment" page and wait for the webhook. Treat a missing or `processing` status as unknown.

## Overlay and inline checkout

The `dodopayments-checkout` browser package opens the checkout session URL in a modal (`overlay`) or in an element on your page (`inline`). The server route above still creates the session; the browser never sees an API key.

```bash
npm install dodopayments-checkout
```

```typescript
import { DodoPayments } from 'dodopayments-checkout';

// Call once when the app loads, not before each checkout.
DodoPayments.Initialize({
  mode: 'test', // 'live' in production
  displayType: 'overlay', // or 'inline'
  onEvent: (event) => console.log('Checkout event:', event),
});

export async function openCheckout(planId: 'starter' | 'pro') {
  const response = await fetch('/api/checkout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ planId }),
  });
  const { checkoutUrl } = (await response.json()) as { checkoutUrl: string };
  DodoPayments.Checkout.open({ checkoutUrl }); // inline: also pass elementId: 'dodo-inline-checkout'
}
```

For inline mode, render `<div id="dodo-inline-checkout"></div>` where the form should appear.

## Static payment links

For no-code sharing, link straight to a product. No API call is involved, and access still comes from the webhook.

```text
https://checkout.dodopayments.com/buy/pdt_example?quantity=1&email=customer@example.com&redirect_url=https%3A%2F%2Fexample.com%2Fsuccess
```

Test-mode products live on `https://test.checkout.dodopayments.com/buy/{product_id}`. Other query parameters: `fullName`, `firstName`, `lastName`, `country`, `city`, `state`, `zipCode`, `addressLine`, `paymentCurrency`, and `metadata_<key>`.

## Retrieve and preview

```typescript
const status = await client.checkoutSessions.retrieve('cks_session_id');
console.log(status.payment_status, status.payment_id);

const preview = await client.checkoutSessions.preview({
  product_cart: [{ product_id: 'pdt_pro_monthly', quantity: 1 }],
  billing_currency: 'EUR',
});
console.log(preview.current_breakup.total_amount);
```

## Common mistakes

- Granting access from `return_url` query parameters. Wait for the verified webhook.
- Accepting a `pdt_` ID or a price from the browser. Map a plan slug to an allowlisted product ID on the server and reject non-positive quantities.
- Calling the SDK from browser code. The key is secret.
- Forgetting `environment: 'test_mode'` in development; the default is live mode.
- Amounts in major units. USD 10.00 is `1000`.
- Reusing a `checkout_url`. Create a new checkout session per attempt.
