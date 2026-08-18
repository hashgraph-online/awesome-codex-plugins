---
name: customer-management
description: Guide for managing customer records, saved payment methods, monetary wallets, and hosted customer-portal sessions; subscription lifecycle and custom billing UI are covered separately.
---

# Customer Management

Build customer records, hosted self-service portals, saved payment methods, and real-money wallet ledgers. This skill covers the full customer lifecycle: CRUD operations, payment method management, time-bound portal sessions, and idempotent wallet transactions.

## When to use this skill

- Creating, listing, retrieving, or updating customer records
- Building a self-service customer portal for invoices, subscriptions, and payment methods
- Managing saved payment methods and customer payment history
- Implementing customer wallet balances and ledger entries for credits or refunds
- Linking your app's user records to Dodo customers
- Reading customer entitlements and credit balances

## Core concepts

**Customers** are records in Dodo that group payments, subscriptions, and portal access. Each customer has an ID (prefix `cus_`), email, name, and optional metadata.

**Customer Portal** is a hosted, time-bound session that lets customers self-serve: view invoices, cancel subscriptions, change plans, update payment methods, recover on-hold subscriptions, and download license keys. You create a session and redirect to its link.

**Payment Methods** are saved cards or other payment instruments linked to a customer. You can list and delete them; creation happens during checkout.

**Customer Wallets** hold real-money balances (USD, INR) that customers can spend on future purchases. They are NOT the same as usage credits (see `credit-based-billing` skill). Wallet ledger entries are idempotent via `idempotency_key` to prevent duplicate charges.

**Entitlements** are feature or file grants. `listCreditEntitlements` returns credit balances; `listEntitlements` returns feature/file grants; `listEntitlementGrants` lists individual grants with revocation status.

## Customer CRUD

Create, list, retrieve, and update customer records.

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: 'test_mode',
});

// Create a customer
const customer = await client.customers.create({
  email: 'alice@example.com',
  name: 'Alice Chen',
  metadata: {
    userId: 'user_12345',
    tier: 'premium',
  },
});
console.log(customer.customer_id); // cus_...

// List customers
const customers = await client.customers.list({
  page_size: 10,
});

// Retrieve a customer
const retrieved = await client.customers.retrieve('cus_abc123');

// Update a customer
await client.customers.update('cus_abc123', {
  name: 'Alice Chen-Smith',
  metadata: { tier: 'enterprise' },
});
```

## Customer Portal

Create a time-bound session that redirects customers to a hosted portal. The portal is read-only for most actions; customers can view invoices, cancel subscriptions, change plans, update payment methods, recover on-hold subscriptions, and download license keys.

```typescript
// Create a portal session
const session = await client.customers.customerPortal.create('cus_abc123', {
  return_url: 'https://yourapp.com/dashboard',
});

// Redirect the customer
window.location.href = session.link;
```

The portal session link expires after a short time. Customers cannot:
- Create new subscriptions (use checkout for that)
- Refund themselves
- Change their email or name (contact support)
- Access billing history beyond invoices

If you need to rebuild any of these, you're duplicating the portal. Use it instead.

## Saved Payment Methods

List and delete payment methods saved to a customer.

```typescript
// List payment methods for a customer
const methods = await client.customers.retrievePaymentMethods('cus_abc123');
console.log(methods);
// {
//   items: [{ payment_method_id: 'pm_xyz789', payment_method: 'card' }]
// }

// Delete a payment method
await client.customers.deletePaymentMethod('pm_xyz789', {
  customer_id: 'cus_abc123',
});
```

Payment methods are created during checkout when the customer opts to save their card. You cannot create them directly via the API.

## Customer Wallets

Wallets hold real-money balances (USD, INR) that customers can spend on future purchases. They are distinct from usage credits. List wallet balances and create idempotent ledger entries.

```typescript
// List wallets for a customer
const wallets = await client.customers.wallets.list('cus_abc123');
console.log(wallets);
// {
//   items: [
//     { currency: 'USD', balance: 5000, customer_id: 'cus_abc123', ... },
//     { currency: 'INR', balance: 100000, customer_id: 'cus_abc123', ... }
//   ],
//   total_balance_usd: 17000
// }

// List ledger entries
const entries = await client.customers.wallets.ledgerEntries.list('cus_abc123', {
  page_size: 20,
});

// Create a ledger entry (credit or debit)
// Amounts are in the smallest currency unit (cents for USD, paise for INR)
await client.customers.wallets.ledgerEntries.create('cus_abc123', {
  amount: 1000, // $10.00 in USD
  currency: 'USD',
  entry_type: 'credit', // or 'debit'
  reason: 'Refund for order #12345',
  idempotency_key: 'refund_order_12345_v1',
});
```

**Idempotency is critical.** If your network fails after creating a ledger entry, retrying with the same `idempotency_key` returns the existing entry instead of creating a duplicate charge. Always use a stable, unique key per transaction.

Wallets are real money. Do not create entries without idempotency keys, and do not expose wallet balances to the client without verification.

## Reading Customer Entitlements

Entitlements are feature or file grants. There are three methods:

```typescript
// List credit entitlements (credit balances)
const credits = await client.customers.listCreditEntitlements('cus_abc123');
console.log(credits);
// {
//   items: [{
//     credit_entitlement_id: 'cred_ent_1',
//     balance: '5000',
//     name: 'API Calls',
//     overage: '0',
//     unit: 'calls'
//   }]
// }

// List feature/file entitlements
const features = await client.customers.listEntitlements('cus_abc123');
console.log(features);
// {
//   items: [
//     {
//       grant_id: 'entg_feature_1',
//       entitlement_id: 'ent_feature_1',
//       entitlement_name: 'Pro Features',
//       integration_type: 'feature_flag',
//       status: 'delivered',
//       created_at: '2026-01-01T00:00:00Z',
//       updated_at: '2026-01-01T00:00:00Z'
//     }
//   ]
// }

// List individual grants (with revocation status)
const grants = await client.customers.listEntitlementGrants('cus_abc123', {
  page_size: 50,
});
console.log(grants);
// {
//   items: [{
//     id: 'entg_feature_1',
//     entitlement_id: 'ent_feature_1',
//     status: 'Delivered',
//     revoked_at: null
//   }]
// }
```

## Linking Your App's Users to Dodo Customers

Store the Dodo customer ID in your user record, or use metadata to link them.

```typescript
// Option 1: Store the Dodo customer ID in your database
const customer = await client.customers.create({
  email: user.email,
  name: user.name,
});
await db.users.update(user.id, { dodo_customer_id: customer.customer_id });

// Option 2: Use metadata to store your user ID
const customer = await client.customers.create({
  email: user.email,
  name: user.name,
  metadata: {
    app_user_id: user.id,
  },
});

// Later, retrieve by email (not a direct API call, but common pattern)
// You must store the mapping yourself or query Dodo's list endpoint
const customers = await client.customers.list({ page_size: 100 });
const found = customers.items.find(c => c.email === user.email);
```

**Email matching pitfall:** if a user changes their email in your app, the Dodo customer email won't update automatically. Always sync email changes explicitly via `client.customers.update()`.

## Common mistakes

**Creating duplicate customers per checkout.** Each checkout should reuse an existing `customer_id` or create the customer once. Creating a new customer for every transaction fragments your customer data.

```typescript
// WRONG
const session = await client.checkoutSessions.create({
  product_cart: [...],
  customer: { email: user.email }, // Creates a new customer each time
});

// RIGHT
const customer = await client.customers.create({
  email: user.email,
  name: user.name,
});
const session = await client.checkoutSessions.create({
  product_cart: [...],
  customer: { customer_id: customer.customer_id }, // Reuse the customer
});
```

**Building a bespoke billing UI instead of using the portal.** The portal handles invoices, cancellations, plan changes, payment method updates, and on-hold recovery. If you rebuild these, you're duplicating work and missing edge cases.

**Mutating wallet balances without an idempotency key.** Retries will create duplicate entries and charge the customer twice.

```typescript
// WRONG
await client.customers.wallets.ledgerEntries.create('cus_abc123', {
  amount: 1000,
  currency: 'USD',
  entry_type: 'credit',
  reason: 'Refund',
  // No idempotency_key
});

// RIGHT
await client.customers.wallets.ledgerEntries.create('cus_abc123', {
  amount: 1000,
  currency: 'USD',
  entry_type: 'credit',
  reason: 'Refund',
  idempotency_key: 'refund_order_12345_v1',
});
```

**Exposing portal links publicly.** Portal sessions are time-bound and tied to a customer ID. Don't log them or share them in URLs; generate them server-side and redirect immediately.

**Confusing wallets with credits.** Wallets hold real money (USD, INR). Credits are usage-based entitlements. See the `credit-based-billing` skill for credit management.

## Resources

- [Customer Management](https://docs.dodopayments.com/features/customers)
- [Customer Portal](https://docs.dodopayments.com/features/customer-portal)
- [Customer Wallets](https://docs.dodopayments.com/features/customer-wallet)
- [Customers API Reference](https://docs.dodopayments.com/api-reference/customers)
