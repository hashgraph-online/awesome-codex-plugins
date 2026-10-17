---
name: localized-pricing
description: Dodo Payments multi-currency pricing, covering fixed localized prices per country or currency, Adaptive Currency live FX conversion at checkout, and purchasing power parity (PPP) percentages. Use when pricing in INR, EUR, or other local currencies, offering regional or PPP discounts, or resolving billing country and currency fallback.
---

# Localized Pricing, Adaptive Currency, and PPP

This skill covers three distinct mechanisms for pricing in multiple countries and currencies. Developers often confuse them. This skill disambiguates them, shows how to implement each, and explains their interactions with plan changes, proration, and tax.

## When to use this skill

- You need to set fixed prices for specific countries or currencies.
- You want to offer live foreign-exchange conversion at checkout.
- You're considering purchasing power parity discounts for emerging markets.
- You're unsure whether to use localized pricing or adaptive currency.
- You need to handle billing-country and currency resolution, fallback behavior, or plan changes with localized prices.

## Core concepts

### Three mechanisms, three purposes

| Mechanism | What it does | Who controls it | When prices change |
|---|---|---|---|
| **Localized Pricing** | Developer sets fixed prices per country/currency | You (via API) | Only when you update them |
| **Adaptive Currency** | Live FX conversion at checkout time | Dodo (live rates) | Every transaction, based on current rates |
| **Purchasing Power Parity (PPP)** | Charges a per-country percentage of the base price | You (business-wide country percentages in the dashboard, per-product opt-in) | Only when you change the percentages |

**Key distinction:** Localized prices are static. Adaptive currency is dynamic. PPP is a native per-country percentage applied to the base price before Adaptive Currency converts it.

### Localized Pricing

Set fixed prices for specific countries and currencies. Once created, a localized price does not change unless you update it. It does not track exchange rates.

Use localized pricing when you want predictable, region-specific pricing that you control.

### Adaptive Currency

Enable live foreign-exchange conversion at checkout. The customer sees their local currency, and Dodo converts the base price using current rates.

Use adaptive currency when you want to offer checkout in any currency without manually setting prices for each one.

### PPP (Purchasing Power Parity)

PPP is native ([docs](https://docs.dodopayments.com/features/purchasing-power-parity)). Dodo keeps one business-wide percentage per country (30 to 100, managed in the dashboard only), and the customer pays that share of your list price based on their billing country. Each product opts in with `price.purchasing_power_parity: true` (default `false`).

PPP requires Adaptive Currency: enable it under **Settings → Business** first, or product opt-in is rejected. A matching localized price always wins over PPP, and discount codes apply to the PPP-reduced price.

```typescript
await client.products.create({
  name: 'Starter Plan',
  tax_category: 'saas',
  price: {
    type: 'one_time_price',
    currency: 'USD',
    price: 2000, // $20.00; a customer in India at 30% pays $6.00
    discount: 0,
    purchasing_power_parity: true,
  },
});
```

## Product pricing mode

Every product has a `pricing_mode` that determines how prices are resolved:

- `by_country`: Dodo looks up a localized price by the customer's billing country.
- `by_currency`: Dodo looks up a localized price by the customer's billing currency.

Set the mode once per product via `client.products.update(...)`. You cannot mix modes on the same product.

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: 'test_mode',
});

// Set pricing mode to by_country
await client.products.update('pdt_premium_plan', {
  pricing_mode: 'by_country',
});

// Or by_currency
await client.products.update('pdt_premium_plan', {
  pricing_mode: 'by_currency',
});
```

## Localized Pricing CRUD

Localized prices are nested under products. All amounts are in the smallest currency unit (cents for USD, paise for INR).

### Create a localized price

```typescript
// ₹999.00 for customers in India
const localizedPrice = await client.products.localizedPrices.create('pdt_premium_plan', {
  currency: 'INR',
  country_code: 'IN',
  amount: 99900, // 999.00 in paise
});
```

### List localized prices for a product

```typescript
const prices = await client.products.localizedPrices.list('pdt_premium_plan');
console.log(prices);
```

### Retrieve a specific localized price

```typescript
const price = await client.products.localizedPrices.retrieve('lp_abc123', {
  product_id: 'pdt_premium_plan',
});
console.log(price.amount, price.currency, price.country_code);
```

### Update a localized price

```typescript
await client.products.localizedPrices.update('lp_abc123', {
  product_id: 'pdt_premium_plan',
  amount: 109900, // Update to ₹1099.00
});
```

### Archive a localized price

```typescript
await client.products.localizedPrices.archive('lp_abc123', {
  product_id: 'pdt_premium_plan',
});
```

Archived prices are soft-deleted. They no longer apply to new checkouts but remain in your history.

## Adaptive Currency at checkout

Enable Adaptive Currency in the dashboard under **Settings → Business** ([docs](https://docs.dodopayments.com/features/adaptive-currency)). Dodo then converts the base product price at live rates. Passing `billing_currency` and `billing_address.country` on a checkout session only pins the currency you charge in; if you omit them, Adaptive Currency picks the currency and country from the customer's IP address.

```typescript
// Server route (e.g. POST /api/checkout): create the session and return its URL
export async function POST() {
  const session = await client.checkoutSessions.create({
    product_cart: [
      {
        product_id: 'pdt_premium_plan',
        quantity: 1,
      },
    ],
    billing_currency: 'AED', // Pin the charge currency (requires Adaptive Currency)
    billing_address: { country: 'AE' },
    return_url: 'https://example.com/return',
  });

  return Response.json({ checkout_url: session.checkout_url });
}
```

Never call the SDK or expose the API key in browser code. The browser only receives the URL and redirects:

```typescript
// Browser
const res = await fetch('/api/checkout', { method: 'POST' });
const { checkout_url } = (await res.json()) as { checkout_url: string };
window.location.href = checkout_url;
```

**Fees:** Adaptive Currency adds a tiered conversion fee (4% under $500, 3% from $500 to $1,500, 2% above $1,500) on top of the displayed price by default. Turn on **Fees Inclusive** in **Settings → Business** to absorb the fee from your settlement instead. When a localized price matches, the transaction is always treated as fees-inclusive.

**Charm Pricing:** With Adaptive Currency on, [Charm Pricing](https://docs.dodopayments.com/features/charm-pricing) can round the converted price to a clean ending such as 49.99. It requires Adaptive Currency.

Adaptive currency is also available on subscription creation and plan changes. Check the API reference for `billing_currency` support on the specific endpoint you're using.

## Billing country and currency resolution

Dodo resolves the customer's billing country and currency in this order:

1. Explicit `billing_address.country` or `billing_currency` passed to checkout.
2. Customer's stored address (if the customer exists in Dodo).
3. IP geolocation (if available).
4. Fallback to your product's base price and currency.

If no localized price exists for the resolved country or currency, Dodo falls back to the base price. This fallback is automatic and does not raise an error.

## Interaction with plan changes and proration

When a customer changes plans, localized prices apply to the new plan using the same billing country or currency as the original subscription.

Proration is calculated using the new plan's localized price (if one exists for the customer's country/currency).

```typescript
await client.subscriptions.changePlan('sub_abc123', {
  product_id: 'pdt_enterprise_plan',
  quantity: 1,
  proration_billing_mode: 'prorated_immediately',
});
```

The new plan's localized price is used for the prorated amount.

## Tax behavior with localized pricing

Tax is calculated on the localized price, not the base price. If you set a localized price of ₹999.00 for India, tax is applied to that amount.

Tax-inclusive pricing works the same way: the localized price is treated as the tax-inclusive total.

## Common mistakes

### Mistake 1: Assuming localized prices auto-update with exchange rates

Localized prices are fixed. If you set INR 999.00 today, it remains 999.00 until you manually update it. It does not track USD/INR rates.

If you want live FX conversion, use adaptive currency instead.

### Mistake 2: Confusing `by_country` and `by_currency`

- `by_country`: Dodo matches the customer's billing country to a localized price's `country_code`.
- `by_currency`: Dodo matches the customer's billing currency to a localized price's `currency`.

A customer in India using a USD card will match `by_currency: USD` but not `by_country: IN` (unless you also set a USD price for India).

### Mistake 3: Forgetting a fallback price

If you set `pricing_mode: by_country` but don't create a localized price for a customer's country, Dodo falls back to the base price: charged directly if the customer is already in your base currency, or converted through Adaptive Currency when that is enabled ([docs](https://docs.dodopayments.com/features/localized-pricing)). Without Adaptive Currency, that is the base price in the base currency, which is usually not what you want.

Always create localized prices for your target markets before enabling the mode.

### Mistake 4: Mixing localized pricing and adaptive currency

You can use both on the same product, but they serve different purposes. Localized pricing is for fixed, region-specific prices. Adaptive currency is for live FX conversion.

If you set a localized price for India and also enable adaptive currency, the localized price takes precedence for customers in India.

### Mistake 5: Reaching for a third-party tool for PPP

PPP is native: opt products in with `price.purchasing_power_parity: true` and set country percentages in the dashboard (Adaptive Currency must be on). Third-party tools like ParityDeals are only an alternative if you want their site banners; their codes are passed as ordinary `discount_codes` at checkout.

### Mistake 6: Not handling missing localized prices in production

Always test your fallback behavior. If a customer's country or currency has no localized price, they see the base price. Decide whether that's acceptable or whether you need to block checkout for unsupported regions.

## Resources

- [Localized Pricing](https://docs.dodopayments.com/features/localized-pricing)
- [Adaptive Currency](https://docs.dodopayments.com/features/adaptive-currency)
- [Purchasing Power Parity](https://docs.dodopayments.com/features/purchasing-power-parity)
- [Checkout Sessions API](https://docs.dodopayments.com/developer-resources/checkout-session)
- [Products API](https://docs.dodopayments.com/api-reference/products/post-products)
