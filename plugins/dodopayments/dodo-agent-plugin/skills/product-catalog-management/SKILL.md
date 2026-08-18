---
name: product-catalog-management
description: Guide for creating and managing products, pricing, add-ons, product collections, images, and digital product delivery
---

# Product Catalog Management

This skill covers the full product lifecycle: creating products with pricing models, managing add-ons and collections, uploading product images, and delivering digital files to customers.

## When to use this skill

- You need to create or update products with one-time, recurring, or usage-based pricing.
- You're building a product collection or storefront.
- You need to upload product images or deliver digital files to customers.
- You're managing add-ons or product variants.
- You need to understand why a product update failed or why pricing can't be changed.

## Core concepts

**Product model:** Every product has exactly one pricing model selected at creation. The three models are:

- `one_time_price`: charge once per purchase.
- `recurring_price`: charge on a configurable payment frequency and subscription period.
- `usage_based_price`: charge per unit consumed (see `usage-based-billing` skill for meter setup).

Pricing is nested inside the product object. There is no separate top-level Price resource.

**Pricing structure:** Each price object contains:

- `type`: one of the three models above.
- `currency`: ISO 4217 code (e.g., `USD`, `AED`, `INR`).
- `price`: amount in the smallest currency unit (cents for USD).
- `discount`: optional discount amount in the same unit.

**Tax category:** Required at product creation. Dodo uses this to calculate and collect sales tax. Supported values are `digital_products`, `saas`, `e_book`, and `edtech`.

**Lifecycle:** Products support `list`, `retrieve`, `update`, and `archive`/`unarchive`. There is no delete endpoint. Archived products remain in your history but don't appear in new checkouts.

**Images:** Presigned upload URLs expire after 60 seconds. Download the URL immediately after requesting it.

**Digital delivery:** Entitlements grant customers access to files. Download URLs expire after roughly 15 minutes.

## Creating a product

All products require a name, a pricing model, and a tax category.

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: 'test_mode',
});

// One-time purchase
const product = await client.products.create({
  name: 'Pro Bundle',
  tax_category: 'digital_products',
  price: {
    type: 'one_time_price',
    currency: 'USD',
    price: 9900, // $99.00
    discount: 0,
    purchasing_power_parity: false,
  },
});

console.log(product.product_id); // pdt_...
```

For recurring products, specify the billing cycle:

```typescript
const subscription = await client.products.create({
  name: 'Premium Plan',
  tax_category: 'saas',
  price: {
    type: 'recurring_price',
    currency: 'USD',
    price: 2999, // $29.99/month
    discount: 0,
    payment_frequency_count: 1,
    payment_frequency_interval: 'Month',
    subscription_period_count: 1,
    subscription_period_interval: 'Month',
    purchasing_power_parity: false,
  },
});
```

This skill is the canonical source for product creation request shapes. For a usage-based product, create the meter as described in the `usage-based-billing` skill, then attach it through the singular `price.meters` array:

```typescript
const metered = await client.products.create({
  name: 'API Calls',
  tax_category: 'saas',
  price: {
    type: 'usage_based_price',
    currency: 'USD',
    discount: 0,
    fixed_price: 0, // No fixed monthly charge; amounts use the smallest currency unit
    payment_frequency_count: 1,
    payment_frequency_interval: 'Month',
    subscription_period_count: 1,
    subscription_period_interval: 'Month',
    purchasing_power_parity: false,
    meters: [
      {
        meter_id: 'mtr_api_calls',
        price_per_unit: '0.01',
        free_threshold: 1000,
      },
    ],
  },
});
```

`price_per_unit` is a decimal string in the configured currency's smallest unit. The optional `free_threshold` excludes that many aggregated units before per-unit charging begins.

## Listing and retrieving products

```typescript
// List all products
const products = await client.products.list();

// Retrieve a single product
const product = await client.products.retrieve('pdt_pro_bundle');
```

## Updating a product

You can update the name, description, and metadata. You cannot change the pricing model or price of a live product. Create a new product instead.

```typescript
await client.products.update('pdt_pro_bundle', {
  name: 'Pro Bundle (Updated)',
  description: 'Includes all pro features',
  metadata: {
    category: 'software',
    tier: 'premium',
  },
});
```

## Archiving and unarchiving

Archive a product to hide it from new checkouts without deleting it:

```typescript
await client.products.archive('pdt_pro_bundle');

// Restore it later
await client.products.unarchive('pdt_pro_bundle');
```

## Product images

Upload a product image via presigned URL. The URL is valid for 60 seconds.

```typescript
import fs from 'node:fs';

// Request a presigned upload URL
const uploadUrl = await client.products.images.update('pdt_pro_bundle', {
  force_update: true,
});

// Upload immediately (within 60 seconds)
const response = await fetch(uploadUrl.url, {
  method: 'PUT',
  body: fs.readFileSync('./product.png'),
  headers: { 'Content-Type': 'image/png' },
});

if (!response.ok) {
  throw new Error('Image upload failed');
}
```

## Add-ons

Add-ons are optional extras customers can purchase alongside a product. Create them independently, then reference them in checkout.

```typescript
// Create an add-on
const addon = await client.addons.create({
  name: 'Priority Support',
  tax_category: 'saas',
  currency: 'USD',
  price: 4900, // $49.00
});

// Upload an image for the add-on
const addonImageUrl = await client.addons.updateImages(addon.id);

// List add-ons
const addons = await client.addons.list();
```

## Product collections

Group products into collections for themed checkouts. Collections have nested groups and items.

```typescript
// Create a collection
const collection = await client.productCollections.create({
  name: 'Starter Bundle',
  description: 'Everything you need to get started',
  groups: [
    {
      group_name: 'Core Tools',
      products: [
        { product_id: 'pdt_tool_a' },
        { product_id: 'pdt_tool_b' },
      ],
    },
  ],
});

// Add another group later
await client.productCollections.groups.create(collection.id, {
  group_name: 'Optional Tools',
  products: [
    { product_id: 'pdt_tool_c' },
    { product_id: 'pdt_tool_d' },
  ],
});

// Checkout with a collection
const session = await client.checkoutSessions.create({
  product_collection_id: collection.id,
  product_cart: [], // Required: pass an empty array for collection checkout
  return_url: 'https://yoursite.com/return',
});

window.location.href = session.checkout_url;
```

## Digital product delivery

Entitlements grant customers access to downloadable files. Create an entitlement, upload files, and generate download links.

```typescript
// Create an entitlement
const entitlement = await client.entitlements.create({
  name: 'Pro Bundle Files',
  integration_type: 'digital_files',
  integration_config: {
    digital_file_ids: [],
  },
});

// Upload and attach a file; the response identifies the attached file
const { file_id } = await client.entitlements.files.upload(entitlement.id);

// Attach the entitlement to a product
await client.products.update('pdt_pro_bundle', {
  entitlements: [{ entitlement_id: entitlement.id }],
});

// A grant is produced by fulfillment when the customer purchases the product.
// Grants can be listed, revoked, or fulfilled with a manually managed license key;
// they cannot be created directly through the SDK.

// List grants for a customer
const grants = await client.customers.listEntitlementGrants('cus_customer_123');

// Generate a download URL (valid for roughly 15 minutes)
const grant = grants.items[0];
const downloadUrl = grant?.digital_product_delivery?.files[0]?.download_url;
```

## Short links

Create short, shareable links to products:

```typescript
const shortLink = await client.products.shortLinks.create('pdt_pro_bundle', {
  slug: 'pro-bundle-deal',
});

console.log(shortLink.short_url); // https://dodo.link/pro-bundle-deal
```

## Localized pricing

For country or currency-specific pricing, use the `localized-pricing` skill. Do not hardcode prices in the client.

## Common mistakes

**Expecting a delete endpoint:** Products don't have a delete method. Archive them instead. Archived products remain in your history for reconciliation.

**Trying to change the pricing model:** Once a product is created with `one_time_price`, you can't change it to `recurring_price`. Create a new product and migrate customers to it.

**Hardcoding prices in the client:** Always fetch the product catalog from the API. Prices change, and your client code will become stale. Read `client.products.retrieve(id)` to get the current price.

**Forgetting the tax category:** Every product requires a `tax_category`. Dodo uses this to calculate and remit sales tax. Omitting it will cause the create request to fail.

**Uploading images after the 60-second window:** Request the presigned URL and upload immediately. If the URL expires, request a new one.

**Passing a non-empty product_cart for collection checkout:** Collection checkout requires `product_cart: []`. The collection itself defines what's in the cart.

**Confusing purchasing_power_parity with localized pricing:** The OpenAPI schema includes a `purchasing_power_parity` field in examples, but it's marked unavailable. Use the `localized-pricing` skill for country and currency pricing instead.

## Resources

- [Products](https://docs.dodopayments.com/features/products)
- [Create product API](https://docs.dodopayments.com/api-reference/products/post-products)
- [Product Collections](https://docs.dodopayments.com/features/product-collections)
- [Digital Product Delivery](https://docs.dodopayments.com/features/digital-product-delivery)
- [Add-ons](https://docs.dodopayments.com/features/addons)
