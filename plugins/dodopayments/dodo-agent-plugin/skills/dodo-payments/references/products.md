# Products

## Contents

- [Product model](#product-model)
- [One-time product](#one-time-product)
- [Subscription product](#subscription-product)
- [Usage-based product](#usage-based-product)
- [Update, archive, list](#update-archive-list)
- [Images](#images)
- [Add-ons](#add-ons)
- [Product collections](#product-collections)
- [Digital file delivery](#digital-file-delivery)
- [Short links](#short-links)
- [Common mistakes](#common-mistakes)

## Product model

- Each product has one `price` object whose `type` is `one_time_price`, `recurring_price` or `usage_based_price`. The type cannot change after creation; create a new product instead.
- `tax_category` is required: `digital_products`, `saas`, `e_book` or `edtech`.
- Amounts are in the smallest currency unit.
- There is no delete. Archive products you no longer sell.
- Products are per mode. A test-mode `pdt_` ID does not exist in live mode.

## One-time product

```typescript
const product = await client.products.create({
  name: 'Pro Bundle',
  tax_category: 'digital_products',
  price: {
    type: 'one_time_price',
    currency: 'USD',
    price: 9900, // USD 99.00
    discount: 0,
    purchasing_power_parity: false,
  },
});
console.log(product.product_id);
```

## Subscription product

```typescript
const plan = await client.products.create({
  name: 'Pro Monthly',
  tax_category: 'saas',
  price: {
    type: 'recurring_price',
    currency: 'USD',
    price: 2900, // USD 29.00 per month
    discount: 0,
    payment_frequency_count: 1,
    payment_frequency_interval: 'Month',
    subscription_period_count: 1,
    subscription_period_interval: 'Month',
    purchasing_power_parity: false,
  },
});
```

## Usage-based product

Create the meter first ([usage-billing.md](usage-billing.md)), then attach it:

```typescript
const metered = await client.products.create({
  name: 'API Calls',
  tax_category: 'saas',
  price: {
    type: 'usage_based_price',
    currency: 'USD',
    discount: 0,
    fixed_price: 0, // optional base fee per cycle
    payment_frequency_count: 1,
    payment_frequency_interval: 'Month',
    subscription_period_count: 1,
    subscription_period_interval: 'Month',
    purchasing_power_parity: false,
    meters: [{ meter_id: 'mtr_api_calls', price_per_unit: '0.01', free_threshold: 1000 }],
  },
});
```

`price_per_unit` is a decimal string in the smallest currency unit.

## Update, archive, list

```typescript
await client.products.update('pdt_pro_bundle', {
  name: 'Pro Bundle',
  description: 'Includes all pro features',
  metadata: { tier: 'premium' },
});

await client.products.archive('pdt_pro_bundle');
await client.products.unarchive('pdt_pro_bundle');

for await (const item of client.products.list()) {
  console.log(item.product_id, item.name);
}
```

`update` also accepts `price`, `tax_category`, `pricing_mode` and `entitlements`. A price change applies to new customers only; move existing subscribers with `client.subscriptions.changePlan` ([subscriptions.md](subscriptions.md)).

## Images

The upload URL is valid for 60 seconds, so upload right away:

```typescript
import fs from 'node:fs';

const upload = await client.products.images.update('pdt_pro_bundle', { force_update: true });
const response = await fetch(upload.url, {
  method: 'PUT',
  body: fs.readFileSync('./product.png'),
  headers: { 'Content-Type': 'image/png' },
});
if (!response.ok) throw new Error('Image upload failed');
```

## Add-ons

```typescript
const addon = await client.addons.create({
  name: 'Extra seat',
  tax_category: 'saas',
  currency: 'USD',
  price: 900,
});
```

Sell an add-on through `product_cart[].addons` on the checkout session ([checkout.md](checkout.md)).

## Product collections

A collection groups products for one checkout (and for plan switching in the customer portal).

```typescript
const collection = await client.productCollections.create({
  name: 'Plans',
  groups: [{ group_name: 'Monthly', products: [{ product_id: 'pdt_starter' }, { product_id: 'pdt_pro' }] }],
});

const session = await client.checkoutSessions.create({
  product_collection_id: collection.id,
  product_cart: [], // required and empty for collection checkout
  return_url: 'https://example.com/return',
});
```

## Digital file delivery

Files are delivered through a `digital_files` entitlement attached to the product. Dodo creates the grant on purchase.

```typescript
// openAsBlob needs Node.js 20+
import { openAsBlob } from 'node:fs';

const entitlement = await client.entitlements.create({
  name: 'Pro Bundle Files',
  integration_type: 'digital_files',
  integration_config: { digital_file_ids: [] },
});

const form = new FormData();
form.append('filename', 'pro-bundle.zip'); // append filename before file
form.append('file', await openAsBlob('./pro-bundle.zip'), 'pro-bundle.zip');
await client.entitlements.files.upload(entitlement.id, { body: form });

// `entitlements` replaces every entitlement on the product: send the full list.
await client.products.update('pdt_pro_bundle', { entitlements: [{ entitlement_id: entitlement.id }] });

const grants = await client.customers.listEntitlementGrants('cus_abc123');
const downloadUrl = grants.items[0]?.digital_product_delivery?.files[0]?.download_url; // expires in about 15 minutes
```

## Short links

```typescript
const shortLink = await client.products.shortLinks.create('pdt_pro_bundle', { slug: 'pro-bundle' });
console.log(shortLink.short_url);
```

## Common mistakes

- Looking for a delete endpoint, or trying to switch a product between one-time, subscription and usage-based pricing.
- Expecting a price edit to reprice existing subscribers.
- Omitting `tax_category`.
- Hardcoding prices in the client. Read the product on the server.
- A non-empty `product_cart` with `product_collection_id`.
