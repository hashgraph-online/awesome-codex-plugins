---
name: checkout-integration
description: Guide for starting hosted Checkout Sessions, payment links, and overlay or inline checkout for one-time and recurring products; use subscription-integration for post-checkout lifecycle management.
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

**Return URL:** Where the customer lands after payment. Query parameters include `status=success` and `session_id`.

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

### API Route

```typescript
// app/api/checkout/route.ts
import { NextResponse } from 'next/server';
import DodoPayments from 'dodopayments';
import { getCurrentUser } from '@/lib/auth';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY!,
  environment: process.env.NODE_ENV === 'production' ? 'live_mode' : 'test_mode'
});

type PlanId = 'starter' | 'pro';

const PRODUCT_IDS: Record<PlanId, string> = {
  starter: 'pdt_starter_monthly',
  pro: 'pdt_pro_monthly'
};

function productIdForPlan(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  return PRODUCT_IDS[value as PlanId] ?? null;
}

export async function POST(request: Request) {
  const user = await getCurrentUser();
  if (!user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }

  if (!body || typeof body !== 'object') {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }

  const input = body as { planId?: unknown; quantity?: unknown };
  const productId = productIdForPlan(input.planId);
  const quantity = input.quantity ?? 1;

  if (!productId) {
    return NextResponse.json({ error: 'Unknown plan' }, { status: 400 });
  }

  if (!Number.isInteger(quantity) || (quantity as number) < 1) {
    return NextResponse.json(
      { error: 'Quantity must be a positive integer' },
      { status: 400 }
    );
  }

  try {
    const session = await client.checkoutSessions.create({
      product_cart: [{ product_id: productId, quantity: quantity as number }],
      customer: { email: user.email, name: user.name },
      metadata: { app_user_id: user.id },
      return_url: `${process.env.NEXT_PUBLIC_APP_URL}/checkout/success`
    });

    return NextResponse.json({
      checkoutUrl: session.checkout_url,
      sessionId: session.session_id
    });
  } catch (error) {
    console.error('Checkout error:', error);
    return NextResponse.json(
      { error: 'Failed to create checkout' },
      { status: 500 }
    );
  }
}
```

### Client Component

```typescript
// components/CheckoutButton.tsx
'use client';

import { useState } from 'react';

interface CheckoutButtonProps {
  planId: 'starter' | 'pro';
  quantity?: number;
  children: React.ReactNode;
}

export function CheckoutButton({ planId, quantity = 1, children }: CheckoutButtonProps) {
  const [loading, setLoading] = useState(false);

  const handleCheckout = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ planId, quantity })
      });

      if (!response.ok) {
        throw new Error('Failed to create checkout');
      }

      const data = (await response.json()) as { checkoutUrl?: string };
      if (!data.checkoutUrl) throw new Error('Checkout URL was not returned');
      window.location.href = data.checkoutUrl;
    } catch (error) {
      console.error('Checkout error:', error);
      alert('Failed to start checkout. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button onClick={handleCheckout} disabled={loading}>
      {loading ? 'Loading...' : children}
    </button>
  );
}
```

### Success Page

```typescript
// app/checkout/success/page.tsx
import { Suspense } from 'react';

function SuccessContent() {
  return (
    <div className="text-center py-20">
      <h1 className="text-3xl font-bold">Payment Successful</h1>
      <p className="mt-4 text-gray-600">
        Thank you for your purchase. Check your email for a confirmation.
      </p>
      <a href="/" className="mt-8 inline-block text-blue-600 hover:underline">
        Return to Home
      </a>
    </div>
  );
}

export default function SuccessPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <SuccessContent />
    </Suspense>
  );
}
```

---

## Express.js

```typescript
import express from 'express';
import DodoPayments from 'dodopayments';
import { getCurrentUser } from './auth';
import { fulfillOneTimePurchase, grantSubscriptionAccess } from './entitlements';

const app = express();

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY!,
  environment: process.env.NODE_ENV === 'production' ? 'live_mode' : 'test_mode'
});

// Mount the webhook before express.json() so verification receives signed bytes.
app.post('/webhook', express.raw({ type: 'application/json' }), async (req, res) => {
  try {
    const event = client.webhooks.unwrap(req.body.toString('utf8'), {
      headers: {
        'webhook-id': req.headers['webhook-id'] as string,
        'webhook-signature': req.headers['webhook-signature'] as string,
        'webhook-timestamp': req.headers['webhook-timestamp'] as string
      }
    });

    if (event.type === 'payment.succeeded') {
      // This branch fulfills one-time purchases only.
      await fulfillOneTimePurchase(event.data.customer.customer_id);
    } else if (event.type === 'subscription.active') {
      // Subscription access starts only after this verified event.
      await grantSubscriptionAccess(event.data);
    }

    res.json({ received: true });
  } catch (error) {
    console.error('Webhook verification failed:', error);
    res.status(401).json({ error: 'Invalid signature' });
  }
});

app.use(express.json());

type PlanId = 'starter' | 'pro';

const PRODUCT_IDS: Record<PlanId, string> = {
  starter: 'pdt_starter_monthly',
  pro: 'pdt_pro_monthly'
};

function productIdForPlan(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  return PRODUCT_IDS[value as PlanId] ?? null;
}

app.post('/api/checkout', async (req, res) => {
  const user = await getCurrentUser(req);
  if (!user) {
    res.status(401).json({ error: 'Not authenticated' });
    return;
  }

  const { planId, quantity = 1 } = req.body as {
    planId?: unknown;
    quantity?: unknown;
  };
  const productId = productIdForPlan(planId);

  if (!productId) {
    res.status(400).json({ error: 'Unknown plan' });
    return;
  }

  if (!Number.isInteger(quantity) || (quantity as number) < 1) {
    res.status(400).json({ error: 'Quantity must be a positive integer' });
    return;
  }

  try {
    const session = await client.checkoutSessions.create({
      product_cart: [{ product_id: productId, quantity: quantity as number }],
      customer: { email: user.email, name: user.name },
      metadata: { app_user_id: user.id },
      return_url: `${process.env.APP_URL}/success`
    });

    res.json({ checkoutUrl: session.checkout_url });
  } catch (error) {
    console.error('Checkout error:', error);
    res.status(500).json({ error: 'Failed to create checkout' });
  }
});

app.get('/success', (req, res) => {
  res.send('Payment successful!');
});
```

---

## Python (FastAPI)

```python
import logging
import os
from typing import Annotated, Literal

from dodopayments import DodoPayments
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.auth import User, get_current_user

app = FastAPI()
logger = logging.getLogger(__name__)
client = DodoPayments(
    bearer_token=os.environ["DODO_PAYMENTS_API_KEY"],
    environment="test_mode"
)

PRODUCT_IDS = {
    "starter": "pdt_starter_monthly",
    "pro": "pdt_pro_monthly",
}

class CheckoutRequest(BaseModel):
    plan_id: Literal["starter", "pro"]
    quantity: int = Field(default=1, gt=0)

@app.post("/api/checkout")
async def create_checkout(
    request: CheckoutRequest,
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        session = client.checkout_sessions.create(
            product_cart=[{
                "product_id": PRODUCT_IDS[request.plan_id],
                "quantity": request.quantity
            }],
            customer={
                "email": user.email,
                "name": user.name
            },
            metadata={"app_user_id": user.id},
            return_url=f"{os.environ['APP_URL']}/success"
        )
        return {"checkout_url": session.checkout_url}
    except Exception as error:
        logger.exception("Checkout session creation failed")
        raise HTTPException(status_code=500, detail="Failed to create checkout") from error
```

---

## Overlay Checkout

Use the `dodopayments-checkout` package for overlay or inline checkout that stays on your site.

### Installation

```bash
npm install dodopayments-checkout
```

### Server Route

Create the Checkout Session on the server. The browser sends a public plan slug, while the server derives
the customer from the authenticated user and maps the slug to an allowlisted product id.

```typescript
// app/api/overlay-checkout/route.ts
import { NextResponse } from 'next/server';
import DodoPayments from 'dodopayments';
import { getCurrentUser } from '@/lib/auth';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY!,
  environment: process.env.NODE_ENV === 'production' ? 'live_mode' : 'test_mode'
});

type PlanId = 'starter' | 'pro';

const PRODUCT_IDS: Record<PlanId, string> = {
  starter: 'pdt_starter_monthly',
  pro: 'pdt_pro_monthly'
};

export async function POST(request: Request) {
  const user = await getCurrentUser();
  if (!user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }

  if (!body || typeof body !== 'object') {
    return NextResponse.json({ error: 'Invalid request body' }, { status: 400 });
  }

  const { planId, quantity = 1 } = body as {
    planId?: unknown;
    quantity?: unknown;
  };
  const productId = typeof planId === 'string'
    ? PRODUCT_IDS[planId as PlanId]
    : undefined;

  if (!productId) {
    return NextResponse.json({ error: 'Unknown plan' }, { status: 400 });
  }

  if (!Number.isInteger(quantity) || (quantity as number) < 1) {
    return NextResponse.json(
      { error: 'Quantity must be a positive integer' },
      { status: 400 }
    );
  }

  try {
    const session = await client.checkoutSessions.create({
      product_cart: [{ product_id: productId, quantity: quantity as number }],
      customer: { email: user.email, name: user.name },
      metadata: { app_user_id: user.id },
      return_url: `${process.env.NEXT_PUBLIC_APP_URL}/checkout/success`
    });

    if (!session.checkout_url) {
      return NextResponse.json({ error: 'Checkout URL was not returned' }, { status: 502 });
    }

    return NextResponse.json({ checkoutUrl: session.checkout_url });
  } catch (error) {
    console.error('Overlay checkout error:', error);
    return NextResponse.json({ error: 'Failed to create checkout' }, { status: 500 });
  }
}
```

### Browser Overlay and Inline Modes

Browser code calls the server route and receives only the checkout URL. The Dodo Payments API bearer token
stays in the server route and is never sent to the browser.

```typescript
// lib/open-checkout.ts
import { DodoPayments } from 'dodopayments-checkout';

type PlanId = 'starter' | 'pro';

async function createCheckoutUrl(planId: PlanId, quantity = 1): Promise<string> {
  const response = await fetch('/api/overlay-checkout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ planId, quantity })
  });

  if (!response.ok) throw new Error('Failed to create checkout');

  const data = (await response.json()) as { checkoutUrl?: string };
  if (!data.checkoutUrl) throw new Error('Checkout URL was not returned');
  return data.checkoutUrl;
}

export async function openOverlayCheckout(planId: PlanId): Promise<void> {
  const checkoutUrl = await createCheckoutUrl(planId);

  DodoPayments.Initialize({
    mode: 'test', // or 'live'
    displayType: 'overlay',
    onEvent: (event) => {
      console.log('Checkout event:', event);
    }
  });

  DodoPayments.Checkout.open({ checkoutUrl });
}

export async function openInlineCheckout(planId: PlanId): Promise<void> {
  const checkoutUrl = await createCheckoutUrl(planId);

  DodoPayments.Initialize({
    mode: 'test', // or 'live'
    displayType: 'inline',
    onEvent: (event) => {
      console.log('Checkout event:', event);
    }
  });

  DodoPayments.Checkout.open({
    checkoutUrl,
    elementId: 'dodo-inline-checkout'
  });
}
```

```html
<div id="dodo-inline-checkout"></div>
```

---

## Static Payment Links

No-code shareable links. No server-side API call needed.

### Basic Format

```text
https://checkout.dodopayments.com/buy/{productid}
```

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
https://yoursite.com/success?status=success&session_id=cks_123
```

Query parameters:
- `status`: `success` or `failed`
- `session_id`: Checkout session ID

### Verify Payment Server-Side

Do not trust the browser redirect. Use the Express webhook route above: it receives the raw signed body
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

**4. Assuming only one discount-code form is valid**
Both `discount_code` (a string) and `discount_codes` (an array) are valid Checkout Session parameters.

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
