# Localized pricing

## Contents

- [Pick the mechanism](#pick-the-mechanism)
- [Adaptive Currency](#adaptive-currency)
- [Fixed localized prices](#fixed-localized-prices)
- [Purchasing power parity](#purchasing-power-parity)
- [How the price is resolved](#how-the-price-is-resolved)
- [Common mistakes](#common-mistakes)

## Pick the mechanism

| Need | Use | Price changes |
|---|---|---|
| Charge in the customer's currency, converted at live rates | **Adaptive Currency** (default) | Every transaction, with the FX rate |
| A fixed price you choose for a country or currency (for example INR 999) | **Localized prices** | Only when you edit them |
| A lower price in lower-income countries | **Purchasing power parity (PPP)** | Only when you change the country percentages |

They combine: a matching localized price wins over PPP, and PPP needs Adaptive Currency.

## Adaptive Currency

Turn it on in **Settings > Business**. Dodo then shows and charges the customer's local currency, picked from their IP address. To pin the currency on a checkout session:

```typescript
const session = await client.checkoutSessions.create({
  product_cart: [{ product_id: 'pdt_pro_monthly', quantity: 1 }],
  billing_currency: 'AED',
  billing_address: { country: 'AE' },
  return_url: 'https://example.com/return',
});
```

- Dodo adds a tiered conversion fee on top of the price by default. **Fees Inclusive** in the same settings absorbs it instead. A matching localized price is always fees-inclusive.
- Charm Pricing rounds converted prices to endings such as .99 and needs Adaptive Currency.

## Fixed localized prices

Set the product's `pricing_mode` once, then add prices. Amounts are in the smallest unit of that currency.

```typescript
await client.products.update('pdt_pro_monthly', { pricing_mode: 'by_country' }); // or 'by_currency'

const india = await client.products.localizedPrices.create('pdt_pro_monthly', {
  currency: 'INR',
  country_code: 'IN',
  amount: 99900, // INR 999.00
});

const prices = await client.products.localizedPrices.list('pdt_pro_monthly');
console.log(prices);

await client.products.localizedPrices.update(india.id, { product_id: 'pdt_pro_monthly', amount: 109900 });
await client.products.localizedPrices.archive(india.id, { product_id: 'pdt_pro_monthly' });
```

- `by_country` matches the customer's billing country to `country_code`; `by_currency` matches their billing currency to `currency`. One mode per product.
- Localized prices never follow exchange rates.
- Plan changes and proration use the new plan's localized price for the same country or currency. Tax is calculated on the localized price.

## Purchasing power parity

Set one percentage per country (30 to 100) for the business in the dashboard, then opt products in:

```typescript
await client.products.create({
  name: 'Starter',
  tax_category: 'saas',
  price: {
    type: 'one_time_price',
    currency: 'USD',
    price: 2000, // at a 30% country setting, the customer pays USD 6.00
    discount: 0,
    purchasing_power_parity: true,
  },
});
```

PPP requires Adaptive Currency; opting in without it is rejected. Discount codes apply to the PPP price.

## How the price is resolved

1. `billing_address.country` or `billing_currency` on the checkout session.
2. The customer's stored address.
3. IP geolocation.
4. Otherwise the product's base price, converted by Adaptive Currency when it is on.

A missing localized price falls back silently to step 4; it is not an error.

## Common mistakes

- Expecting localized prices to track exchange rates.
- Enabling `by_country` without creating prices for the target countries; customers there get the base price.
- Mixing up `by_country` and `by_currency`: a customer in India paying in USD matches a USD price, not an `IN` price, under `by_currency`.
- Adding a third-party PPP tool when the native setting covers it.
