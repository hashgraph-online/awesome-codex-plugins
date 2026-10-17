---
name: checkout-integration
description: Dodo Payments checkout via hosted Checkout Sessions (client.checkoutSessions.create), static payment links, and overlay or inline checkout for one-time and subscription products. Use when building a pay button, checkout page, trial signup, custom fields, discount codes at checkout, or return_url redirects; use subscription-integration for post-checkout lifecycle.
---

# Dodo Payments Checkout Integration

Use `client.checkoutSessions.create(...)` to build hosted checkout pages or overlay checkout modals. This is the recommended path for all new payment integrations.

## When to use this skill

- Build a one-time payment checkout flow
- Create a subscription checkout with optional trial
- Embed checkout in an overlay or inline modal
- Collect customer billing info and custom fields at checkout
- Apply discount codes or handle currency selection
- Redirect customers after payment completes

---

## Checkout Methods

Dodo Payments offers three ways to collect payment:

| Method | Best For | Setup |
|--------|----------|-------|
| **Checkout Sessions** (recommended) | Most integrations; full control | Server-side SDK call |
| **Static Payment Links** | No-code sharing; reusable URLs | Dashboard or direct URL |
| **Overlay/Inline Checkout** | Checkout stays on your site | Client-side SDK |

**Legacy:** Dynamic Payment Links created via `POST /payments` or `POST /subscriptions` are deprecated. Use Checkout Sessions instead.

---

## Core Concepts

**Amounts in smallest currency unit:** All prices are in cents (or equivalent). A $10 USD charge is `1000`.

**Checkout Session:** A single-use session that generates a hosted checkout URL. Expires after 24 hours (or 15 minutes if `confirm=true`).

**Return URL:** Where the customer lands after payment. Dodo appends `payment_id` (one-time) or `subscription_id` (subscription), `status`, and when available `license_key` and `email`. It is a UI hint only, never proof of payment.

**Entitlement on webhook:** The browser redirect is not the source of truth. Always verify payment via webhook before granting access. See `webhook-integration` skill for verification.

---

## Create a Checkout Session

### Basic One-Time Payment

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: 'test_mode', // or 'live_mode'
});

const session = await client.checkoutSessions.create({
  product_cart: [
    { product_id: 'pdt_example', quantity: 1 }
  ],
  customer: {
    email: 'customer@example.com',
    name: 'Jane Doe'
  },
  return_url: 'https://yoursite.com/checkout/success'
});

console.log('Redirect to:', session.checkout_url);
```

Response fields:
- `session_id`: Unique checkout session ID
- `checkout_url`: Hosted checkout URL (redirect customer here). Nullable when `confirm=true`
- `client_secret`: Present only if `confirm=true`
- `publishable_key`: Present only if `confirm=true`. Pair it with `client_secret` for the inline SDK flow
- `payment_id`: Present only if `confirm=true`

`publishable_key` is a per-session value returned for confirm-mode inline checkout. It is not a Stripe-style
publishable *API key* — Dodo issues no such credential, and every API key is secret and server-side only.

### With Multiple Products

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [
    { product_id: 'pdt_item_1', quantity: 2 },
    { product_id: 'pdt_item_2', quantity: 1 }
  ],
  customer: { email: 'customer@example.com' },
  return_url: 'https://yoursite.com/success'
});
```

### With Existing Customer

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [
    { product_id: 'pdt_example', quantity: 1 }
  ],
  customer: { customer_id: 'cus_existing_id' },
  return_url: 'https://yoursite.com/success'
});
```

### With Billing Address and Tax ID

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [
    { product_id: 'pdt_example', quantity: 1 }
  ],
  customer: {
    email: 'customer@example.com',
    name: 'Jane Doe'
  },
  billing_address: {
    country: 'US',
    street: '123 Main St',
    city: 'San Francisco',
    state: 'CA',
    zipcode: '94105'
  },
  tax_id: 'VAT123456789',
  customer_business_name: 'Acme Corp',
  return_url: 'https://yoursite.com/success'
});
```

### With Discount Codes

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [
    { product_id: 'pdt_example', quantity: 1 }
  ],
  customer: { email: 'customer@example.com' },
  discount_codes: ['PROMO10', 'WELCOME5'], // max 20, ordered
  feature_flags: {
    allow_discount_code: true
  },
  return_url: 'https://yoursite.com/success'
});
```

### With Subscription and Trial

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [
    { product_id: 'pdt_monthly_subscription', quantity: 1 }
  ],
  subscription_data: {
    trial_period_days: 14
  },
  customer: { email: 'subscriber@example.com' },
  return_url: 'https://yoursite.com/success'
});
```

### With Custom Fields

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [
    { product_id: 'pdt_example', quantity: 1 }
  ],
  customer: { email: 'customer@example.com' },
  custom_fields: [
    {
      key: 'company_size',
      label: 'Company Size',
      field_type: 'dropdown',
      options: ['1-10', '11-50', '51-200', '200+'],
      required: true
    },
    {
      key: 'use_case',
      label: 'Primary Use Case',
      field_type: 'text',
      placeholder: 'e.g., analytics, reporting',
      required: false
    }
  ],
  return_url: 'https://yoursite.com/success'
});
```

### With Metadata

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [
    { product_id: 'pdt_example', quantity: 1 }
  ],
  customer: { email: 'customer@example.com' },
  metadata: {
    order_id: 'order_12345',
    referral_code: 'FRIEND20',
    campaign: 'summer_sale'
  },
  return_url: 'https://yoursite.com/success'
});
```

---

## Next.js App Router

Full guide: [references/server-examples.md](references/server-examples.md).

Covers:

- API Route
- Client Component
- Success Page

## Express.js

Full guide: [references/server-examples.md](references/server-examples.md).

## Python (FastAPI)

Full guide: [references/server-examples.md](references/server-examples.md).

## Overlay Checkout

Full guide: [references/overlay-checkout.md](references/overlay-checkout.md).

Covers:

- Installation
- Server Route
- Browser Overlay and Inline Modes

## Static Payment Links

No-code shareable links. No server-side API call needed.

### Basic Format

```text
https://checkout.dodopayments.com/buy/{productid}
```

In test mode the host is `test.checkout.dodopayments.com` (for example `https://test.checkout.dodopayments.com/buy/{productid}`); a test-mode product does not exist on the live host.

Example:
```text
https://checkout.dodopayments.com/buy/pdt_example
```

### With Query Parameters

```text
https://checkout.dodopayments.com/buy/pdt_example?quantity=2&email=customer@example.com&redirect_url=https%3A%2F%2Fyoursite.com%2Fsuccess
```

Supported parameters:
- `quantity`: Item quantity
- `redirect_url`: Success redirect URL
- `email`: Prefill customer email
- `fullName`, `firstName`, `lastName`: Prefill name
- `country`, `city`, `state`, `zipCode`, `addressLine`: Prefill address
- `paymentCurrency`: Force currency
- `metadata_*`: Custom metadata (e.g., `metadata_orderId=123`)

---

## Retrieve and Preview Sessions

### Retrieve Session Status

```typescript
const status = await client.checkoutSessions.retrieve('cks_session_id');

console.log(status.id);
console.log(status.payment_status);
```

### Preview Session (without creating)

```typescript
const preview = await client.checkoutSessions.preview({
  product_cart: [
    { product_id: 'pdt_example', quantity: 1 }
  ],
  customer: { email: 'customer@example.com' },
  billing_currency: 'EUR'
});

console.log('Preview total:', preview.current_breakup.total_amount);
```

---

## Customization

### Theme and Appearance

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [{ product_id: 'pdt_example', quantity: 1 }],
  customer: { email: 'customer@example.com' },
  customization: {
    theme: 'dark', // 'light', 'dark', or 'system'
    force_language: 'en',
    show_order_details: true,
    theme_config: {
      font_size: 'md',
      font_weight: 'normal',
      radius: '8px',
      pay_button_text: 'Complete Purchase',
      light: {
        bg_primary: '#ffffff',
        text_primary: '#000000',
        button_primary: '#0066ff'
      }
    }
  },
  return_url: 'https://yoursite.com/success'
});
```

### Feature Flags

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [{ product_id: 'pdt_example', quantity: 1 }],
  customer: { email: 'customer@example.com' },
  feature_flags: {
    allow_discount_code: true,
    allow_currency_selection: true,
    allow_customer_editing_email: true,
    allow_phone_number_collection: true,
    require_phone_number: false,
    allow_tax_id: true
  },
  return_url: 'https://yoursite.com/success'
});
```

---

## Post-Payment Flow

### Return URL Handling

After payment, the customer is redirected to your `return_url` with query parameters:

```text
# One-time payment
https://yoursite.com/success?payment_id=pay_xxx&status=succeeded&email=customer%40example.com

# Subscription (with license keys)
https://yoursite.com/success?subscription_id=sub_xxx&status=active&license_key=LK-001,LK-002&email=customer%40example.com
```

Query parameters:
- `payment_id` (one-time payments) or `subscription_id` (subscriptions)
- `status`: `succeeded` (one-time) or `active` (subscription) on success; `failed` if declined; `processing` (or a `requires_*` value) if it settles later; `expired` if the session expired
- `license_key`: present when the product issues license keys (comma-separated if several)
- `email`: present when the customer has an email on record

There is no `session_id` parameter. Treat `processing`/missing status as "unknown" and wait for the webhook.

### Verify Payment Server-Side

Do not trust the browser redirect. Use the Express webhook route in
[references/server-examples.md](references/server-examples.md#expressjs): it receives the raw signed body
before `express.json()`, fulfills one-time purchases on verified `payment.succeeded` using
`event.data.customer.customer_id`, and grants subscription access only on verified `subscription.active`.

Webhook signature verification is covered in the `webhook-integration` skill.

---

## Common Mistakes

**1. Granting access from the return URL**
The return URL redirect is not proof of payment. Never grant access or fulfill an order from its query
parameters; wait for a verified webhook event.

**2. Using deprecated APIs**
Do not use `client.payments.create()` or `client.subscriptions.create()` for new integrations. Both are deprecated. Use `client.checkoutSessions.create()`.

**3. Forgetting the `environment` flag**
The default is `live_mode`. Always set `environment: 'test_mode'` during development to avoid charging real cards.

**4. Using the deprecated `discount_code`**
Use `discount_codes` (an array). The singular `discount_code` string is deprecated (still accepted for backward compatibility) and cannot be combined with `discount_codes` in the same request.

**5. Amounts in wrong unit**
All amounts are in the smallest currency unit (cents for USD). $10 is `1000`, not `10`.

**6. Reusing checkout URLs**
Checkout URLs are single-use. Create a new session for each checkout attempt.

**7. Ignoring `confirm=true` behavior**
When `confirm=true`, the session is finalized immediately and the checkout URL expires in 15 minutes instead of 24 hours. Use only when you have all required customer data.

**8. Forgetting raw body for webhooks**
Webhook signature verification requires the raw request body, not a re-serialized JSON object. Mount the
webhook route with `express.raw({ type: 'application/json' })` before `express.json()`.

**9. Trusting a client-supplied product id**
Do not accept an arbitrary `pdt_` id from the browser. Authenticate the user, accept a public plan slug,
map it to an allowlisted product id on the server, and reject quantities that are not positive integers.

---

## Resources

- [Checkout Sessions Integration Guide](https://docs.dodopayments.com/developer-resources/integration-guide)
- [Checkout Sessions API Reference](https://docs.dodopayments.com/api-reference/checkout-sessions/create)
- [Overlay Checkout](https://docs.dodopayments.com/developer-resources/overlay-checkout)
- [Inline Checkout](https://docs.dodopayments.com/developer-resources/inline-checkout)
- [Static Payment Links](https://docs.dodopayments.com/developer-resources/integration-guide)
- [Webhook Integration](https://docs.dodopayments.com/developer-resources/webhooks)
