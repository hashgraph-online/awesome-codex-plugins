# Customers

## Contents

- [Link app users to customers](#link-app-users-to-customers)
- [Customer CRUD](#customer-crud)
- [Customer portal](#customer-portal)
- [Saved payment methods](#saved-payment-methods)
- [Wallets](#wallets)
- [Entitlements on a customer](#entitlements-on-a-customer)
- [Common mistakes](#common-mistakes)

## Link app users to customers

Store the Dodo `cus_` ID on your user record. Let the first checkout session create the customer (`customer: { email }` reuses an existing customer with that email), save `customer.customer_id` from the verified webhook, and pass `customer: { customer_id }` on later checkout sessions. When a user changes email in your app, call `client.customers.update`.

## Customer CRUD

```typescript
const customer = await client.customers.create({
  email: 'alice@example.com',
  name: 'Alice Chen',
  metadata: { app_user_id: 'user_12345' },
});

await client.customers.update(customer.customer_id, { name: 'Alice Chen-Smith' });
const found = await client.customers.retrieve(customer.customer_id);

for await (const item of client.customers.list()) {
  console.log(item.customer_id, item.email);
}
```

## Customer portal

The hosted customer portal is the default billing UI: invoices, cancel or change plan, update payment method, recover an `on_hold` subscription, download license keys. Create a portal session on the server for the signed-in user and redirect:

```typescript
// app/api/portal/route.ts
import { NextResponse } from 'next/server';
import DodoPayments from 'dodopayments';
import { getCurrentUser } from '@/lib/auth';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: process.env.DODO_PAYMENTS_ENVIRONMENT === 'live_mode' ? 'live_mode' : 'test_mode',
});

export async function POST() {
  const user = await getCurrentUser();
  if (!user?.dodoCustomerId) return NextResponse.json({ error: 'No billing account' }, { status: 400 });

  const session = await client.customers.customerPortal.create(user.dodoCustomerId, {
    return_url: `${process.env.NEXT_PUBLIC_APP_URL}/account`,
  });
  return NextResponse.json({ url: session.link });
}
```

- The link lasts 24 hours. Create one per click and do not log or share it.
- Take the customer ID from the session, never from the request.
- `send_email: true` also emails the link to the customer.
- Plan switching in the portal uses product collections ([products.md](products.md)).

## Saved payment methods

Payment methods are saved during checkout. You can list and delete them:

```typescript
const methods = await client.customers.retrievePaymentMethods('cus_abc123');
console.log(methods.items);

await client.customers.deletePaymentMethod('pm_xyz789', { customer_id: 'cus_abc123' });
```

## Wallets

A wallet holds real money (for example USD or INR) that pays for future purchases. It is not a credit balance ([credits.md](credits.md)). Every ledger entry needs a stable `idempotency_key`.

```typescript
const wallets = await client.customers.wallets.list('cus_abc123');
console.log(wallets.items);

await client.customers.wallets.ledgerEntries.create('cus_abc123', {
  amount: 1000, // USD 10.00
  currency: 'USD',
  entry_type: 'credit', // or 'debit'
  reason: 'Goodwill credit for order 12345',
  idempotency_key: 'goodwill:order_12345',
});
```

## Entitlements on a customer

```typescript
const credits = await client.customers.listCreditEntitlements('cus_abc123'); // credit balances
const features = await client.customers.listEntitlements('cus_abc123'); // feature, file and license entitlements
for await (const grant of client.customers.listEntitlementGrants('cus_abc123')) {
  console.log(grant.id, grant.status); // individual grants, including revoked ones
}
console.log(credits.items, features.items);
```

## Common mistakes

- `feature_flags.always_create_new_customer: true`, or `customers.create` before every checkout session, creates duplicate customers.
- Building your own billing pages instead of the customer portal.
- Accepting `customer_id` from the browser for portal or wallet calls.
- Wallet ledger entries without an `idempotency_key`.
- `client.customers.createPortalSession` does not exist. Use `client.customers.customerPortal.create(customerId, params)` and read `.link`.
