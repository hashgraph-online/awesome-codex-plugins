# Discounts

## Contents

- [Rules](#rules)
- [Create a discount](#create-a-discount)
- [Restrict a discount](#restrict-a-discount)
- [Apply codes at checkout](#apply-codes-at-checkout)
- [Validate a code before checkout](#validate-a-code-before-checkout)
- [Discounts on plan changes](#discounts-on-plan-changes)
- [Manage discounts](#manage-discounts)
- [Common mistakes](#common-mistakes)

## Rules

- `type` is `percentage` or `flat`. A percentage `amount` is in basis points: `1500` is 15%.
- A `flat` discount needs `currency_options` with a default currency; `max_amount_possible` is the deduction in the smallest currency unit. It applies once to the whole cart.
- Codes are stored uppercase, at least 3 characters. Omit `code` to get a random one.
- Several codes stack in the order given, up to 20, and each still has to be eligible.

## Create a discount

```typescript
const percent = await client.discounts.create({
  type: 'percentage',
  amount: 1500, // 15%
  code: 'SUMMER15',
  metadata: { campaign: 'summer' },
});

const flat = await client.discounts.create({
  type: 'flat',
  amount: 1000,
  currency_options: [{ currency: 'USD', max_amount_possible: 1000, is_default: true }], // USD 10.00 off
  code: 'WELCOME10',
});
console.log(percent.discount_id, flat.discount_id);
```

## Restrict a discount

```typescript
const restricted = await client.discounts.create({
  type: 'percentage',
  amount: 2000,
  code: 'PRO_LAUNCH',
  restricted_to: ['pdt_pro_monthly'], // only these products
  starts_at: '2025-06-01T00:00:00Z',
  expires_at: '2025-08-31T23:59:59Z', // hard cutoff for every use
  usage_limit: 100, // total redemptions
  subscription_cycles: 3, // first 3 billing cycles of a subscription
  preserve_on_plan_change: true,
});
```

For specific customers, create with `customer_eligibility: 'specific'` and attach customers. The SDK has no named method for that endpoint, so use the client's generic request, which keeps auth and base URL:

```typescript
await client.post(`/discounts/${restricted.discount_id}/customers`, {
  body: { customer_ids: ['cus_vip_001', 'cus_vip_002'] },
});
```

## Apply codes at checkout

Pass codes on the server-side checkout session:

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [{ product_id: 'pdt_pro_monthly', quantity: 1 }],
  discount_codes: ['WELCOME10', 'LOYALTY5'],
  customer: { email: 'customer@example.com' },
  return_url: 'https://example.com/return',
});
```

To let customers type a code on the checkout page instead, set `feature_flags: { allow_discount_code: true }`.

## Validate a code before checkout

Do this on the server before showing a discounted price:

```typescript
async function checkCode(code: string, productId: string) {
  try {
    const discount = await client.discounts.retrieveByCode(code);
    if (discount.expires_at && new Date(discount.expires_at) < new Date()) return { valid: false, reason: 'expired' };
    if (discount.usage_limit && discount.times_used >= discount.usage_limit) return { valid: false, reason: 'used up' };
    if (discount.restricted_to.length > 0 && !discount.restricted_to.includes(productId)) {
      return { valid: false, reason: 'not valid for this product' };
    }
    return { valid: true, discount };
  } catch {
    return { valid: false, reason: 'unknown code' };
  }
}
```

## Discounts on plan changes

`discount_codes` on `client.subscriptions.changePlan` decides what happens to existing discounts:

| `discount_codes` | Result |
|---|---|
| omitted | Discounts with `preserve_on_plan_change: true` carry over; others are removed |
| `[]` | All discounts are removed |
| `['NEW_CODE']` | Only the new codes apply |

```typescript
await client.subscriptions.changePlan('sub_123', {
  product_id: 'pdt_business_monthly',
  quantity: 1,
  proration_billing_mode: 'prorated_immediately',
  discount_codes: ['UPGRADE20'],
});
```

`preserve_on_plan_change` is set on the discount (`create` or `update`), not on `changePlan`.

## Manage discounts

```typescript
for await (const discount of client.discounts.list()) {
  console.log(discount.code, discount.type, discount.amount);
}
await client.discounts.update('dsc_abc123', { usage_limit: 200 });
await client.discounts.delete('dsc_abc123'); // confirm first in live mode
```

## Common mistakes

- `amount: 15` for 15%. Percentages are basis points: `1500`.
- Validating codes only in the browser.
- Passing `discount_codes: []` on a plan change when you meant to keep discounts. Omit it.
- Confusing `subscription_cycles` (how many cycles a subscription gets the discount) with `expires_at` (when the code stops working).
