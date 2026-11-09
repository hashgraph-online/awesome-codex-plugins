# BillingSDK

## Contents

- [What it is](#what-it-is)
- [Install components](#install-components)
- [Component inventory](#component-inventory)
- [Pricing page](#pricing-page)
- [Manage billing button](#manage-billing-button)
- [Usage and credit display](#usage-and-credit-display)
- [Theming](#theming)
- [Common mistakes](#common-mistakes)

## What it is

BillingSDK (`github.com/dodopayments/billingsdk`) is an open-source set of React components for pricing and billing UI, built on Tailwind CSS and shadcn/ui. Components are copied into your repo as source, like shadcn/ui; there is no runtime npm package to install.

- Components only render data and fire callbacks. Every Dodo call happens in your server routes.
- The installed file under `components/billingsdk/` is the prop contract for your version. Read its exported props type before wiring callbacks.
- `registry.json` in the repo lists what is installable.
- React and Next.js only. For other front ends, use a framework adapter ([framework-adapters.md](framework-adapters.md)) and your own UI.

## Install components

```bash
npx @billingsdk/cli init                         # scaffold routes, hooks, lib/dodopayments.ts and env vars
npx @billingsdk/cli add pricing-table-one        # add one component
npx shadcn@latest add @billingsdk/pricing-table-one   # same, through the shadcn registry
```

The server client lives in one module that only route handlers and server components import:

```typescript
// lib/dodopayments.ts
import DodoPayments from 'dodopayments';

export const dodo = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: process.env.DODO_PAYMENTS_ENVIRONMENT === 'live_mode' ? 'live_mode' : 'test_mode',
});
```

## Component inventory

| Group | Components |
|---|---|
| Pricing | `pricing-table-one` to `pricing-table-eight` |
| Subscription | `subscription-management`, `usage-based-pricing`, `invoice-history`, `update-plan-card`, `update-plan-dialog`, `proration-preview`, `cancel-subscription-card`, `cancel-subscription-dialog` |
| Usage and billing | `usage-meter-linear`, `usage-meter-circle`, `usage-table`, `detailed-usage-table`, `billing-screen`, `billing-settings`, `billing-settings-2`, `upcoming-charges` |
| Payments | `payment-details`, `payment-details-two`, `payment-method-selector`, `payment-card`, `payment-failure` |
| Promotion and trials | `banner`, `limited-offer-dialog`, `trial-expiry-card` |

## Pricing page

`add pricing-table-one` generates `lib/billingsdk-config.ts` with a `Plan` type and a sample `plans` array. Edit that array. Prices there are display strings only; Dodo charges the product's price, so keep the two in sync. `onPlanSelect` receives the plan `id`, which the server maps to a product ID.

```tsx
// components/pricing-plans.tsx
'use client';

import { PricingTableOne } from '@/components/billingsdk/pricing-table-one';
import { plans } from '@/lib/billingsdk-config';

export function PricingPlans() {
  async function handlePlanSelect(planId: string) {
    const response = await fetch('/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ planId }),
    });
    if (!response.ok) return;
    const { checkoutUrl } = (await response.json()) as { checkoutUrl: string };
    window.location.href = checkoutUrl;
  }

  return (
    <PricingTableOne
      plans={plans}
      title="Choose your plan"
      description="Select the plan that works best for you"
      onPlanSelect={handlePlanSelect}
      theme="classic"
      size="medium"
    />
  );
}
```

The `/api/checkout` route is the Next.js route in [checkout.md](checkout.md). Its `PRODUCT_IDS` keys must equal the plan `id`s. To sell yearly plans too, create yearly products, send the billing period with the plan ID, and key the map by both.

## Manage billing button

Pair `subscription-management` (or a plain button) with the portal route in [customers.md](customers.md):

```tsx
'use client';

export function ManageBillingButton() {
  async function openPortal() {
    const response = await fetch('/api/portal', { method: 'POST' });
    if (!response.ok) return;
    const { url } = (await response.json()) as { url: string };
    window.location.href = url;
  }
  return <button type="button" onClick={openPortal}>Manage billing</button>;
}
```

Load the subscription in the server component that renders the page (`await dodo.subscriptions.retrieve(id)`) and pass plain data down.

## Usage and credit display

Read numbers on the server and pass them to `usage-meter-linear` or a related block:

```typescript
// app/api/usage/credits/route.ts
import { NextResponse } from 'next/server';
import { dodo } from '@/lib/dodopayments';
import { getCurrentUser } from '@/lib/auth';

export async function GET() {
  const user = await getCurrentUser();
  const creditEntitlementId = process.env.DODO_CREDIT_ENTITLEMENT_ID;
  if (!user?.dodoCustomerId || !creditEntitlementId) {
    return NextResponse.json({ error: 'No billing account' }, { status: 400 });
  }
  const balance = await dodo.creditEntitlements.balances.retrieve(user.dodoCustomerId, {
    credit_entitlement_id: creditEntitlementId,
  });
  return NextResponse.json({ balance: balance.balance, overage: balance.overage });
}
```

The displayed balance lags metering by about a minute. Show it; do not gate requests on it ([credits.md](credits.md)).

## Theming

Override the shadcn CSS variables in `globals.css` for colours, use component props such as `theme` and `size`, or edit the copied source for structural changes. The hosted checkout page is themed separately through `customization` on the checkout session.

## Common mistakes

- `NEXT_PUBLIC_DODO_PAYMENTS_API_KEY`. Every Dodo key is secret and must stay on the server.
- `npm install billingsdk`. The root package is private; use `@billingsdk/cli` or the shadcn registry.
- Guessing prop names instead of reading the installed component file.
- Accepting a raw `product_id` from the pricing table. Map plan IDs on the server.
- Rendering "active" from React state or `return_url` instead of the webhook-backed record in your database.
