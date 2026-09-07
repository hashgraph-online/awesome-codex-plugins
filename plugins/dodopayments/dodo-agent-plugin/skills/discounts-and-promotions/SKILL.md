---
name: discounts-and-promotions
description: Guide for implementing discount codes and promotional pricing with Dodo Payments, including CRUD operations, eligibility rules, stacking, subscription-cycle limits, and plan-change preservation.
---

# Discounts and Promotions

This skill covers discount codes, coupons, and promotional pricing in Dodo Payments. Use it when building discount management, applying codes at checkout, validating codes before showing prices, or handling discounts during subscription plan changes.

## When to use this skill

- Create, update, list, or delete discount codes
- Apply discount codes at checkout or during plan changes
- Validate a code before displaying adjusted pricing to the user
- Configure eligibility rules, usage limits, or subscription-cycle restrictions
- Handle the subtle semantics of discount preservation during plan upgrades/downgrades
- Debug why a discount isn't applying or stacking as expected

## Core concepts

**Discount types:** Dodo supports both percentage and flat-amount discounts. Percentage amounts are expressed as integers where 1500 means 15% (100 = 1%). Flat amounts are in the smallest currency unit (cents for USD).

**Discount code:** A human-readable string (e.g., `SUMMER2025`) that customers enter at checkout. Codes are case-sensitive.

**Eligibility:** Discounts can be restricted to specific products, customers, or date ranges. A discount without restrictions applies to any product and any customer.

**Stacking:** Multiple discount codes can be applied to a single checkout or subscription. They are applied in the order specified in the `discount_codes` array, up to a maximum of 20 codes.

**Subscription-cycle limits:** A discount can be configured to apply only for a specific number of billing cycles (e.g., first 3 months only).

**Preservation on plan change:** When a customer upgrades or downgrades their subscription, the `preserve_on_plan_change` setting and the `discount_codes` parameter control whether existing discounts carry forward.

## Discount CRUD

### Create a discount

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: 'test_mode',
});

// Percentage discount: 15% off
const percentageDiscount = await client.discounts.create({
  type: 'percentage',
  amount: 1500, // 15%
  code: 'SUMMER2025',
  metadata: {
    campaign: 'summer_promo',
    source: 'email_blast'
  }
});

// Flat discount: $10 off (1000 cents in currency_options)
const flatDiscount = await client.discounts.create({
  type: 'flat',
  amount: 1000,
  currency_options: [{
    currency: 'USD',
    max_amount_possible: 1000,
    is_default: true,
  }],
  code: 'WELCOME10',
});
```

### List discounts

```typescript
const discounts = await client.discounts.list({
  page_size: 50,
  page_number: 0,
});

// Paginated responses expose `items`.
for (const discount of discounts.items) {
  console.log(`${discount.code}: ${discount.type} ${discount.amount}`);
}

// Or let the SDK walk every page for you:
for await (const discount of client.discounts.list()) {
  console.log(discount.code);
}
```

### Retrieve a discount by ID

```typescript
const discount = await client.discounts.retrieve('discount_id');
console.log(discount.code, discount.type, discount.amount);
```

### Retrieve a discount by code

```typescript
try {
  const discount = await client.discounts.retrieveByCode('SUMMER2025');
  console.log('Discount found:', discount.amount);
} catch (error) {
  console.log('Code not found or expired');
}
```

### Update a discount

```typescript
await client.discounts.update('discount_id', {
  metadata: { updated_at: new Date().toISOString() }
});
```

### Delete a discount

```typescript
await client.discounts.delete('discount_id');
```

## Discount types and configuration

**Important:** The feature documentation states that only percentage discounts are currently supported. However, the current OpenAPI schema defines both `flat` and `percentage` types with currency options. Follow the API reference when implementing. If you encounter unexpected behavior with flat discounts, verify with Dodo support whether flat discounts are fully enabled in your account.

### Percentage discounts

Expressed as an integer where 100 = 1%. A 15% discount is `1500`.

```typescript
const discount = await client.discounts.create({
  type: 'percentage',
  amount: 1500, // 15%
  code: 'PERCENT15',
});
```

### Flat discounts

For flat discounts, set the deduction per currency through `currency_options`. A $10 USD deduction is `max_amount_possible: 1000` (cents).

```typescript
const discount = await client.discounts.create({
  type: 'flat',
  amount: 1000, // $10.00
  currency_options: [{
    currency: 'USD',
    max_amount_possible: 1000,
    is_default: true,
  }],
  code: 'FLAT10',
});
```

## Eligibility and restrictions

### Product restrictions

Limit a discount to specific products:

```typescript
const discount = await client.discounts.create({
  type: 'percentage',
  amount: 1500,
  code: 'PREMIUM_ONLY',
  restricted_to: ['pdt_premium', 'pdt_enterprise'],
});
```

### Customer eligibility

Restrict a discount to specific customers by creating it with `customer_eligibility: 'specific'`, then attaching customers through the discount-customer endpoint. `customer_ids` is not a `discounts.create` parameter.

```typescript
const discount = await client.discounts.create({
  type: 'percentage',
  amount: 1500,
  code: 'VIP_ONLY',
  customer_eligibility: 'specific',
});

await fetch(
  `https://test.dodopayments.com/discounts/${discount.discount_id}/customers`,
  {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.DODO_PAYMENTS_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      customer_ids: ['cus_vip_001', 'cus_vip_002'],
    }),
  },
);
```

### Date range

Set activation and expiration dates:

```typescript
const discount = await client.discounts.create({
  type: 'percentage',
  amount: 1500,
  code: 'SUMMER2025',
  starts_at: '2025-06-01T00:00:00Z',
  expires_at: '2025-08-31T23:59:59Z',
});
```

### Usage limits

Limit the total number of times a code can be used:

```typescript
const discount = await client.discounts.create({
  type: 'percentage',
  amount: 1500,
  code: 'LIMITED_100',
  usage_limit: 100,
});
```

### Subscription-cycle limits

Apply a discount only for the first N billing cycles:

```typescript
const discount = await client.discounts.create({
  type: 'percentage',
  amount: 1500,
  code: 'FIRST_3_MONTHS',
  subscription_cycles: 3, // applies to first 3 billing cycles only
});
```

## Applying codes at checkout

### Single code

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [{ product_id: 'pdt_abc', quantity: 1 }],
  discount_codes: ['SUMMER2025'],
  customer: { email: 'user@example.com' },
  return_url: 'https://yoursite.com/return'
});

window.location.href = session.checkout_url;
```

### Multiple codes (stacking)

Codes are applied in the order specified. Maximum 20 codes per checkout:

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [{ product_id: 'pdt_abc', quantity: 1 }],
  discount_codes: ['WELCOME10', 'BLACKFRIDAY20', 'LOYALTY5'],
  customer: { email: 'user@example.com' },
  return_url: 'https://yoursite.com/return'
});
```

## Validating codes before checkout

Validate a code and check its eligibility before showing adjusted pricing:

```typescript
async function validateDiscount(code, productId) {
  try {
    const discount = await client.discounts.retrieveByCode(code);
    
    // Check expiration
    if (discount.expires_at && new Date(discount.expires_at) < new Date()) {
      return { valid: false, reason: 'Code expired' };
    }
    
    // Check usage limit
    if (discount.usage_limit && discount.times_used >= discount.usage_limit) {
      return { valid: false, reason: 'Code exhausted' };
    }
    
    // Check product eligibility
    if (discount.restricted_to.length > 0) {
      if (!discount.restricted_to.includes(productId)) {
        return { valid: false, reason: 'Code not valid for this product' };
      }
    }
    
    return { valid: true, discount };
  } catch (error) {
    return { valid: false, reason: 'Code not found or unavailable' };
  }
}

// Usage
const result = await validateDiscount('SUMMER2025', 'pdt_abc');
if (result.valid) {
  console.log('Discount applies:', result.discount.amount);
} else {
  console.log('Cannot apply:', result.reason);
}
```

## Discounts on plan changes

When a customer changes their subscription plan, discounts can be preserved, replaced, or cleared depending on the `discount_codes` parameter and each discount's `preserve_on_plan_change` setting. Set `preserve_on_plan_change` through `discounts.create` or `discounts.update`; it is not a `subscriptions.changePlan` parameter.

### Behavior matrix

| Scenario | `discount_codes` | Discount's `preserve_on_plan_change` | Result |
|---|---|---|---|
| Upgrade with no change | `undefined` | `true` | Existing discounts carry forward |
| Upgrade with no change | `undefined` | `false` | Existing discounts are removed |
| Upgrade with no change | `[]` (empty array) | any | Existing discounts are removed |
| Upgrade with replacement | `['NEW_CODE']` | any | Only `NEW_CODE` applies; old discounts removed |

### Example: preserve existing discounts

```typescript
await client.discounts.update('dsc_existing', {
  preserve_on_plan_change: true,
});

await client.subscriptions.changePlan('sub_123', {
  product_id: 'pdt_pro',
  quantity: 1,
  proration_billing_mode: 'prorated_immediately',
  // Omit discount_codes. Existing discounts configured with
  // preserve_on_plan_change: true carry forward.
});
```

### Example: replace discounts on upgrade

```typescript
await client.subscriptions.changePlan('sub_123', {
  product_id: 'pdt_pro',
  quantity: 1,
  proration_billing_mode: 'prorated_immediately',
  discount_codes: ['UPGRADE20'], // replaces old discounts
});
```

### Example: remove all discounts on downgrade

```typescript
await client.subscriptions.changePlan('sub_123', {
  product_id: 'pdt_basic',
  quantity: 1,
  proration_billing_mode: 'prorated_immediately',
  discount_codes: [], // empty array removes all discounts
});
```

## Common mistakes

### Validating discounts client-side only

Never trust client-side validation. Always validate on the server before applying a discount at checkout. A user can modify the discount code in the browser.

```typescript
// WRONG: client-side only
if (code.length > 0) {
  applyDiscount(code);
}

// CORRECT: server-side validation
try {
  const discount = await client.discounts.retrieveByCode(code);
  if (isEligible(discount)) {
    // proceed with checkout
  }
} catch (error) {
  // Unknown or unavailable code; reject the checkout request.
}
```

### Assuming codes stack unconditionally

Discounts stack in order, but eligibility rules still apply. If a code is restricted to a product not in the cart, it won't apply even if other codes do.

```typescript
// Both codes may not apply if they have conflicting restrictions
const session = await client.checkoutSessions.create({
  product_cart: [{ product_id: 'pdt_basic', quantity: 1 }],
  discount_codes: ['PREMIUM_ONLY', 'BASIC_ONLY'], // one or both may fail
  return_url: 'https://yoursite.com/return'
});
```

### Losing a discount on upgrade by passing an empty array

Passing `discount_codes: []` explicitly removes all discounts, even if `preserve_on_plan_change` is true. Omit the parameter entirely if you want to preserve existing discounts.

```typescript
// WRONG: removes all discounts
await client.subscriptions.changePlan('sub_123', {
  product_id: 'pdt_pro',
  quantity: 1,
  proration_billing_mode: 'prorated_immediately',
  discount_codes: [], // this clears discounts
});

// CORRECT: preserves discounts whose preserve_on_plan_change property is true
await client.subscriptions.changePlan('sub_123', {
  product_id: 'pdt_pro',
  quantity: 1,
  proration_billing_mode: 'prorated_immediately',
  // omit discount_codes
});
```

### Not handling expired or exhausted codes

A code can expire by date or by reaching its redemption limit. Always check both before showing a discount to the user.

```typescript
// WRONG: assumes code is always valid
const discount = await client.discounts.retrieveByCode(code);
applyDiscount(discount);

// CORRECT: catch unknown codes, then check expiration and usage
try {
  const discount = await client.discounts.retrieveByCode(code);
  if (discount.expires_at && new Date(discount.expires_at) < new Date()) {
    showError('Code expired');
  } else if (discount.usage_limit && discount.times_used >= discount.usage_limit) {
    showError('Code exhausted');
  } else {
    applyDiscount(discount);
  }
} catch (error) {
  showError('Code not found');
}
```

### Confusing subscription-cycle limits with expiration dates

`subscription_cycles` applies only to subscriptions and controls how many billing cycles the discount applies. `expires_at` is a hard cutoff for all uses of the code.

```typescript
// Applies to first 3 billing cycles of any subscription
const discount = await client.discounts.create({
  type: 'percentage',
  amount: 1500,
  code: 'FIRST_3_MONTHS',
  subscription_cycles: 3,
});

// Expires on a specific date, regardless of billing cycles
const discount2 = await client.discounts.create({
  type: 'percentage',
  amount: 1500,
  code: 'SUMMER_ONLY',
  expires_at: '2025-08-31T23:59:59Z',
});
```

## Resources

- [Discounts feature guide](https://docs.dodopayments.com/features/discount-codes)
- [Create discount API](https://docs.dodopayments.com/api-reference/discounts/create-discount)
- [Checkout Sessions API](https://docs.dodopayments.com/developer-resources/checkout-session)
- [Subscription plan changes](https://docs.dodopayments.com/api-reference/subscriptions/change-plan)
