---
name: billing-sdk
description: Guide for building billing UI with BillingSDK - the open-source React component library for pricing tables, subscription management, usage meters, invoice history, and customer portal flows wired to Dodo Payments.
---

# BillingSDK

BillingSDK is an open-source React component library for billing interfaces, maintained by Dodo Payments
at `github.com/dodopayments/billingsdk`. Components are copied into your repository as source files
(shadcn/ui model) rather than imported from a runtime npm package.

Use this skill when building the front end. All Dodo Payments API calls belong in server-side route
handlers; the components are presentation only.

## When to use this skill

- Building a pricing page that starts a Dodo checkout.
- Building an account/billing page with subscription details and a "Manage billing" button.
- Rendering usage meters, credit balances, invoice history, or upcoming charges.
- Adding cancel / upgrade / downgrade UI to an existing React or Next.js app.
- Deciding whether to scaffold with `@billingsdk/cli init` or add individual components.

## Core concepts

**Source-installed, not a dependency.** The repository root package `billingsdk` is private. There is no
verified general-purpose runtime npm component package. You install components through the CLI or the
shadcn registry, and the `.tsx` files land in your project under `components/billingsdk/`.

**The installed file is the prop contract.** Because components are vendored into your repo, the exported
props type in `components/billingsdk/<component>.tsx` is authoritative for your version. Read it before
wiring callbacks. Do not assume prop names from another project.

**The registry is the installability source of truth.** Use
[`registry.json`](https://github.com/dodopayments/billingsdk/blob/main/registry.json). The docs navigation
has drifted from it — for example `payment-success-dialog` appears in navigation but not in the current
registry. If `add` fails, the block is not in the registry.

**Components never call Dodo.** They receive data and fire callbacks. Every Dodo Payments call runs on your
server with `DODO_PAYMENTS_API_KEY`. That key is `dodo_test_...` or `dodo_live_...` and must never reach
the browser.

## Installation

Scaffold a new integration (framework config, API routes, `useBilling` hooks, `lib/dodopayments.ts`,
dependencies, and env vars `DODO_PAYMENTS_API_KEY`, `DODO_PAYMENTS_ENVIRONMENT`,
`DODO_PAYMENTS_WEBHOOK_KEY`):

```bash
npx @billingsdk/cli init
```

Add a single component to an existing project:

```bash
npx @billingsdk/cli add pricing-table-one
```

Or install through the shadcn registry using the `@billingsdk/` namespace:

```bash
npx shadcn@latest add @billingsdk/pricing-table-one
```

The published CLI package is `@billingsdk/cli`, most recently seen at version 0.9.0.

## Component inventory

From the current official registry, grouped by purpose:

| Group | Blocks |
|---|---|
| Pricing | `pricing-table-one` through `pricing-table-eight` |
| Subscription | `subscription-management`, `usage-based-pricing`, `invoice-history`, `update-plan-card`, `update-plan-dialog`, `proration-preview`, `cancel-subscription-card`, `cancel-subscription-dialog` |
| Usage and billing | `usage-meter-linear`, `usage-meter-circle`, `usage-table`, `detailed-usage-table`, `billing-screen`, `billing-settings`, `billing-settings-2`, `upcoming-charges` |
| Payments | `payment-details`, `payment-details-two`, `payment-method-selector`, `payment-card`, `payment-failure` |
| Promotion and trials | `banner`, `limited-offer-dialog`, `trial-expiry-card` |

`pricing-table-one` is the only block with an officially published prop example, reproduced below. For
every other block, run `add` and read the generated file's props type.

## Server client

One module, imported only by route handlers and server components.

```typescript
// lib/dodopayments.ts
import DodoPayments from 'dodopayments';

if (!process.env.DODO_PAYMENTS_API_KEY) {
  throw new Error('DODO_PAYMENTS_API_KEY is not set');
}

export const dodo = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: process.env.DODO_PAYMENTS_ENVIRONMENT === 'live_mode' ? 'live_mode' : 'test_mode',
});
```

`environment` defaults to `'live_mode'` when omitted, so set it explicitly during development. Base URLs
are `https://test.dodopayments.com` and `https://live.dodopayments.com`.

## Pricing page

### 1. Plan catalogue

Keep the product ids and the display copy in one module. The `price` here is a display number rendered by
the component — the amount actually charged comes from the Dodo product catalogue, and Dodo API amounts
are always in the smallest currency unit (cents). Treat this file as a mirror of the dashboard and
reconcile it when you change a price.

```typescript
// lib/plans.ts
export type PlanId = 'starter' | 'pro';

export interface Plan {
  id: PlanId;
  title: string;
  price: number;
  period: string;
  features: string[];
  popular: boolean;
}

export const PLANS: readonly Plan[] = [
  {
    id: 'starter',
    title: 'Starter',
    price: 9,
    period: 'month',
    features: ['100 requests', 'Basic support', '1 project'],
    popular: false,
  },
  {
    id: 'pro',
    title: 'Pro',
    price: 29,
    period: 'month',
    features: ['Unlimited requests', 'Priority support', '10 projects'],
    popular: true,
  },
];
```

### 2. Product id map — server only

Never let the browser choose an arbitrary `product_id`. Map the public plan slug to a `pdt_` id on the
server and reject anything else.

```typescript
// lib/plan-products.server.ts
import 'server-only';
import type { PlanId } from './plans';

const PRODUCT_IDS: Record<PlanId, string> = {
  starter: 'pdt_starter_monthly',
  pro: 'pdt_pro_monthly',
};

export function productIdForPlan(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  return PRODUCT_IDS[value as PlanId] ?? null;
}
```

### 3. Checkout route

```typescript
// app/api/checkout/route.ts
import { NextResponse } from 'next/server';
import { dodo } from '@/lib/dodopayments';
import { productIdForPlan } from '@/lib/plan-products.server';
import { getCurrentUser } from '@/lib/auth';

export async function POST(request: Request) {
  const user = await getCurrentUser();
  if (!user) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
  }

  const body: unknown = await request.json();
  const planId = (body as { planId?: unknown }).planId;
  const productId = productIdForPlan(planId);

  if (!productId) {
    return NextResponse.json({ error: 'Unknown plan' }, { status: 400 });
  }

  try {
    const session = await dodo.checkoutSessions.create({
      product_cart: [{ product_id: productId, quantity: 1 }],
      customer: { email: user.email, name: user.name },
      return_url: `${process.env.NEXT_PUBLIC_APP_URL}/billing/return`,
      cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/pricing`,
      metadata: { app_user_id: user.id },
    });

    if (!session.checkout_url) {
      return NextResponse.json({ error: 'No checkout URL returned' }, { status: 502 });
    }

    return NextResponse.json({ checkoutUrl: session.checkout_url });
  } catch (error) {
    console.error('Checkout session creation failed', error);
    return NextResponse.json({ error: 'Could not start checkout' }, { status: 500 });
  }
}
```

`checkout_url` is nullable — it is absent when the session is created with `payment_method_id` — so guard
it rather than redirecting to `undefined`. Checkout URLs are single-use and normally expire after 24 hours.

Use `checkoutSessions.create`. `payments.create` and `subscriptions.create` are deprecated for new
integrations. Checkout parameters are covered in depth in the `checkout-integration` skill.

### 4. Client component

```tsx
// components/pricing-plans.tsx
'use client';

import { useState } from 'react';
import { PricingTableOne } from '@/components/billingsdk/pricing-table-one';
import { PLANS } from '@/lib/plans';

export function PricingPlans() {
  const [error, setError] = useState<string | null>(null);

  async function handlePlanSelect(planId: string) {
    setError(null);
    try {
      const response = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ planId }),
      });

      if (!response.ok) {
        setError('Could not start checkout. Please try again.');
        return;
      }

      const { checkoutUrl } = (await response.json()) as { checkoutUrl: string };
      window.location.href = checkoutUrl;
    } catch {
      setError('Network error. Please try again.');
    }
  }

  return (
    <>
      <PricingTableOne
        plans={PLANS}
        title="Choose your plan"
        description="Select the plan that works best for you"
        onPlanSelect={handlePlanSelect}
        theme="classic"
        size="medium"
      />
      {error ? <p role="alert">{error}</p> : null}
    </>
  );
}
```

Render `<PricingPlans />` from `app/pricing/page.tsx`. Nothing secret crosses into the client component:
it sends a plan slug and receives a URL.

## Subscription management and customer portal

Install the block, then read its props from the generated file:

```bash
npx @billingsdk/cli add subscription-management
```

The portal route. The method is `customers.customerPortal.create(customerID, { ...params })` and the
session's URL field is `link`.

```typescript
// app/api/portal/route.ts
import { NextResponse } from 'next/server';
import { dodo } from '@/lib/dodopayments';
import { getCurrentUser } from '@/lib/auth';

export async function POST() {
  const user = await getCurrentUser();
  if (!user?.dodoCustomerId) {
    return NextResponse.json({ error: 'No billing account' }, { status: 400 });
  }

  try {
    const session = await dodo.customers.customerPortal.create(user.dodoCustomerId, {
      return_url: `${process.env.NEXT_PUBLIC_APP_URL}/account`,
    });

    return NextResponse.json({ url: session.link });
  } catch (error) {
    console.error('Customer portal session failed', error);
    return NextResponse.json({ error: 'Could not open billing portal' }, { status: 500 });
  }
}
```

Portal links expire after 24 hours, so mint one per click instead of caching it. In the portal a customer
can view and cancel subscriptions, change plans within enabled product collections, update payment
methods, download invoices, and retrieve license keys.

Client side:

```tsx
// components/manage-billing-button.tsx
'use client';

import { useState } from 'react';

export function ManageBillingButton() {
  const [pending, setPending] = useState(false);

  async function openPortal() {
    setPending(true);
    try {
      const response = await fetch('/api/portal', { method: 'POST' });
      if (!response.ok) {
        setPending(false);
        return;
      }
      const { url } = (await response.json()) as { url: string };
      window.location.href = url;
    } catch {
      setPending(false);
    }
  }

  return (
    <button type="button" onClick={openPortal} disabled={pending}>
      {pending ? 'Opening…' : 'Manage billing'}
    </button>
  );
}
```

Wire `openPortal` to whichever callback prop your installed `subscription-management.tsx` exposes, or
render the standalone button next to it. Load the subscription itself in the server component that hosts
the page — `await dodo.subscriptions.retrieve(user.dodoSubscriptionId)` — and pass plain data down.

## Usage and credit display

Install a meter block:

```bash
npx @billingsdk/cli add usage-meter-linear
```

Fetch the numbers server-side. Credit balances come from `creditEntitlements.balances.retrieve`:

```typescript
// app/api/usage/credits/route.ts
import { NextResponse } from 'next/server';
import { dodo } from '@/lib/dodopayments';
import { getCurrentUser } from '@/lib/auth';

const CREDIT_ENTITLEMENT_ID = process.env.DODO_CREDIT_ENTITLEMENT_ID;

export async function GET() {
  const user = await getCurrentUser();
  if (!user?.dodoCustomerId || !CREDIT_ENTITLEMENT_ID) {
    return NextResponse.json({ error: 'No billing account' }, { status: 400 });
  }

  try {
    const balance = await dodo.creditEntitlements.balances.retrieve(user.dodoCustomerId, {
      credit_entitlement_id: CREDIT_ENTITLEMENT_ID,
    });

    return NextResponse.json({ balance: balance.balance, overage: balance.overage });
  } catch (error) {
    console.error('Credit balance lookup failed', error);
    return NextResponse.json({ error: 'Could not read balance' }, { status: 500 });
  }
}
```

Pass the result into the meter block using the prop names in your installed
`components/billingsdk/usage-meter-linear.tsx`. Related blocks for the same surface: `usage-meter-circle`,
`usage-table`, `detailed-usage-table`, `upcoming-charges`, `invoice-history`.

Credit balances are eventually consistent — meter-to-credit deduction runs on a background worker roughly
once a minute — so the displayed balance is informational. Do not gate a request on it. Metering, credit
entitlements, and ledger entries are covered in the `usage-based-billing` and `credit-based-billing` skills.

## Theming and customization

Components are Tailwind CSS plus shadcn/ui conventions, so there are three layers:

1. **Theme tokens.** Override the shadcn CSS variables in `globals.css`; every block inherits them.

   ```css
   @layer base {
     :root {
       --primary: 220 90% 56%;
       --primary-foreground: 0 0% 100%;
     }
   }
   ```

2. **Component props.** `pricing-table-one` accepts `theme` (`"classic"` in the official example) and
   `size` (`"medium"`). Check the installed file for the full union types.

3. **Source edits.** The files are yours. Editing them is the supported path for structural changes, at
   the cost of manual reconciliation when you re-run `add`.

The hosted Dodo checkout page is themed separately, through `customization.theme_config` on the checkout
session — not by these components.

## Framework support

The components are **not** framework-agnostic. They require React or Next.js plus Tailwind CSS and
shadcn/ui conventions.

The CLI additionally ships server integration templates for Next.js, Express, Hono, Fastify, and React.
That covers the route-handler side only. Caution: Dodo's integration page and BillingSDK's own
introduction have disagreed about which server templates are shipping versus "coming soon" — confirm the
adapter you want with the current CLI before committing to it.

For non-React front ends, call Dodo through a framework adapter (`@dodopayments/nextjs`,
`@dodopayments/express`, `@dodopayments/sveltekit`, and others) and build your own UI.

## Environment variables

```bash
# .env.local — server-side only, never prefixed with NEXT_PUBLIC_
DODO_PAYMENTS_API_KEY=dodo_test_xxxxxxxxxxxxxxxx
DODO_PAYMENTS_ENVIRONMENT=test_mode
DODO_PAYMENTS_WEBHOOK_KEY=xxxxxxxxxxxxxxxx
DODO_CREDIT_ENTITLEMENT_ID=cde_xxxxxxxxxxxxxxxx

# Safe to expose
NEXT_PUBLIC_APP_URL=https://yoursite.com
```

Switch to `dodo_live_...` and `DODO_PAYMENTS_ENVIRONMENT=live_mode` together. A live key against
`test_mode` fails, and a test key against `live_mode` fails.

## Common mistakes

**Exposing the API key to the browser.** `NEXT_PUBLIC_DODO_PAYMENTS_API_KEY` inlines the secret into the
JS bundle for anyone to read. There is no publishable key in Dodo Payments — every key is secret. Import
`lib/dodopayments.ts` only from route handlers and server components.

**Calling `customers.createPortalSession`.** That method does not exist. Use
`client.customers.customerPortal.create(customerID, { ...params })` and read `.link`, not `.url`.

**Trusting client-rendered plan state.** The selected plan in React state, or the fact that the user
returned to `return_url`, does not mean the subscription is active. Grant entitlements only from
webhook-confirmed subscription events persisted in your database, then render UI from that. Webhook
signature verification is covered in the `webhook-integration` skill.

**Accepting a raw `product_id` from the request body.** A caller can then check out against any product in
your catalogue, including internal or discounted ones. Map an opaque plan slug to a `pdt_` id server-side.

**Hardcoding prices in the client.** `PLANS[].price` is display text. When you change a price in the Dodo
dashboard, the checkout charges the new amount while the pricing page keeps advertising the old one.
Reconcile `lib/plans.ts` with the dashboard as part of any pricing change.

**`npm install billingsdk`.** The root repository package is private. Install through
`@billingsdk/cli` or the shadcn registry instead.

**Guessing prop names.** `pricing-table-one` is the only block with a published prop example. Open the
generated file under `components/billingsdk/` and read the exported props type before wiring anything else.

**Using `DODO_PAYMENTS_WEBHOOK_SECRET`.** The SDK reads `DODO_PAYMENTS_WEBHOOK_KEY` for the `webhookKey`
option.

**Gating requests on the displayed credit balance.** Deduction is asynchronous, so the reported balance
lags. Dodo explicitly warns against using it as strict per-request authorization.

**Using `payments.create` or `subscriptions.create` for a purchase.** Both are deprecated. Use
`checkoutSessions.create`.

## Resources

- [BillingSDK on Dodo docs](https://docs.dodopayments.com/developer-resources/billingsdk)
- [BillingSDK quick start](https://billingsdk.com/docs/quick-start)
- [Component catalogue](https://billingsdk.com/docs/components)
- [`registry.json` — installability source of truth](https://github.com/dodopayments/billingsdk/blob/main/registry.json)
- [Checkout Sessions guide](https://docs.dodopayments.com/developer-resources/checkout-session)
- [Customer Portal](https://docs.dodopayments.com/features/customer-portal)
- [Credit-based billing](https://docs.dodopayments.com/features/credit-based-billing)
