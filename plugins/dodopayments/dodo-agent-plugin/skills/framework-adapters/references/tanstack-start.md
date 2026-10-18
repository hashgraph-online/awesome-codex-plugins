# Framework Adapters: TanStack Start


**Package:** `@dodopayments/tanstack`

### Checkout

`Checkout(config)` returns a plain `(request: Request) => Promise<Response>`, so export it directly as the route's method handler. The adapter's own documented usage is `export const GET = Checkout(config)`.

```typescript
// src/routes/api/checkout.ts
import { Checkout } from "@dodopayments/tanstack";
// src/lib/dodo-env.ts
import { dodoEnvironment } from "../../lib/dodo-env";

export const GET = Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "static",
});

export const POST = Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
});
```

TanStack Start's server-route definition API has changed across releases (`createServerFileRoute` was removed). Wrap these exports in whatever route helper your installed version provides; the adapter handlers themselves are unaffected.
