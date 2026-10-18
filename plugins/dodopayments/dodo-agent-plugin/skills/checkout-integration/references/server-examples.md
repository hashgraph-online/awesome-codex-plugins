# Dodo Payments Checkout Integration: reference

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
