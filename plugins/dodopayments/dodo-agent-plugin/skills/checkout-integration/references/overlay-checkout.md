# Dodo Payments Checkout Integration: Overlay Checkout


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

// Call ONCE when the app loads (e.g. in your root component or entry point),
// not before every checkout. Pick the display type your page uses.
export function initCheckout(displayType: 'overlay' | 'inline'): void {
  DodoPayments.Initialize({
    mode: 'test', // or 'live'
    displayType,
    onEvent: (event) => {
      console.log('Checkout event:', event);
    }
  });
}

// Requires initCheckout('overlay') to have run at app load.
export async function openOverlayCheckout(planId: PlanId): Promise<void> {
  const checkoutUrl = await createCheckoutUrl(planId);
  DodoPayments.Checkout.open({ checkoutUrl });
}

// Requires initCheckout('inline') to have run at app load.
export async function openInlineCheckout(planId: PlanId): Promise<void> {
  const checkoutUrl = await createCheckoutUrl(planId);
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
