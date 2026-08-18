# TypeScript Boundary Examples

Use this only for the shape of a focused boundary: source type, receiver type, explicit validation, intentional enum mapping, and a small proof. Do not copy the domain names.

## Contents

- [Stable Receiver Mapping](#stable-receiver-mapping)

## Stable Receiver Mapping

`contract-example.ts`:

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

function requireString(value: string | undefined, name: string): string {
  if (!value) {
    throw new ContractError(`${name} is required by the receiver contract`);
  }
  return value;
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
  return {
    id: api.order_id,
    status: mapStatus(api.status),
    totalCents: api.total_cents,
    currency: requireString(api.currency, "ApiOrder.currency"),
  };
}

assert.deepEqual(
  mapApiOrder({
    order_id: "ord_123",
    status: "paid",
    total_cents: 2599,
    currency: "USD",
  }),
  { id: "ord_123", status: "Paid", totalCents: 2599, currency: "USD" },
);
assert.throws(
  () =>
    mapApiOrder({ order_id: "ord_124", status: "pending", total_cents: 1300 }),
  /ApiOrder\.currency is required/,
);
```

Run:

```bash
npx tsx contract-example.ts
```

Project use: replace the names, source type, receiver type, error type, and test framework with the project's existing patterns. If the receiver is local and display-only with identical meanings, prefer direct source fields or local aliases instead of this mapper.
