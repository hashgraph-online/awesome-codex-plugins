# TypeScript Contract Examples

These examples show executable boundary handling style. Use the shape, not the domain names.

## Contents

- [API Payload To Domain Model With Explicit Missing Data](#api-payload-to-domain-model-with-explicit-missing-data)
- [SDK Status To Internal Enum With Unknown Handling](#sdk-status-to-internal-enum-with-unknown-handling)

## API Payload To Domain Model With Explicit Missing Data

`order-contract.ts`:

```ts
import assert from "node:assert/strict";

type ApiOrder = {
  order_id: string;
  status: "pending" | "paid" | "cancelled";
  total_cents: number;
  currency?: string;
};

type OrderStatus = "PendingPayment" | "Paid" | "Cancelled";

type Order = {
  id: string;
  status: OrderStatus;
  totalCents: number;
  currency: string;
};

class ContractError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ContractError";
  }
}

function mapStatus(status: ApiOrder["status"]): OrderStatus {
  switch (status) {
    case "pending":
      return "PendingPayment";
    case "paid":
      return "Paid";
    case "cancelled":
      return "Cancelled";
  }
}

export function mapApiOrder(api: ApiOrder): Order {
  if (!api.currency) {
    throw new ContractError("ApiOrder.currency is required by the Order domain contract");
  }

  return {
    id: api.order_id,
    status: mapStatus(api.status),
    totalCents: api.total_cents,
    currency: api.currency,
  };
}

function main(): void {
  assert.deepEqual(
    mapApiOrder({
      order_id: "ord_123",
      status: "paid",
      total_cents: 2599,
      currency: "USD",
    }),
    {
      id: "ord_123",
      status: "Paid",
      totalCents: 2599,
      currency: "USD",
    },
  );

  assert.throws(
    () =>
      mapApiOrder({
        order_id: "ord_124",
        status: "pending",
        total_cents: 1300,
      }),
    /currency is required/,
  );
}

main();
```

Run:

```bash
npx tsx order-contract.ts
```

Alternative without installing `tsx`:

```bash
npx ts-node order-contract.ts
```

## SDK Status To Internal Enum With Unknown Handling

`payment-contract.ts`:

```ts
import assert from "node:assert/strict";

type SdkPayment = {
  id: string;
  status: "requires_payment_method" | "processing" | "succeeded" | "failed" | string;
};

type PaymentState = "NeedsAction" | "Processing" | "Paid" | "Failed" | "UnknownProviderState";

type Payment = {
  id: string;
  state: PaymentState;
  providerState?: string;
};

function mapPaymentState(status: SdkPayment["status"]): PaymentState {
  switch (status) {
    case "requires_payment_method":
      return "NeedsAction";
    case "processing":
      return "Processing";
    case "succeeded":
      return "Paid";
    case "failed":
      return "Failed";
    default:
      return "UnknownProviderState";
  }
}

export function mapSdkPayment(payment: SdkPayment): Payment {
  const state = mapPaymentState(payment.status);

  return {
    id: payment.id,
    state,
    providerState: state === "UnknownProviderState" ? payment.status : undefined,
  };
}

function main(): void {
  assert.deepEqual(mapSdkPayment({ id: "pay_1", status: "succeeded" }), {
    id: "pay_1",
    state: "Paid",
    providerState: undefined,
  });

  assert.deepEqual(mapSdkPayment({ id: "pay_2", status: "provider_new_state" }), {
    id: "pay_2",
    state: "UnknownProviderState",
    providerState: "provider_new_state",
  });
}

main();
```

Run:

```bash
npx tsx payment-contract.ts
```
