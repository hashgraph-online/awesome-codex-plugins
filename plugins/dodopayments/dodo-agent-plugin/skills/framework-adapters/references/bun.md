# Framework Adapters: Bun


**Package:** `@dodopayments/bun`

### Checkout and Portal

```typescript
import { Checkout, CustomerPortal } from "@dodopayments/bun";
import { dodoEnvironment } from "./lib/dodo-env";
// your auth helper
import { getSessionUser } from "./lib/auth";

const checkoutHandler = Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
});

const portalHandler = CustomerPortal({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: dodoEnvironment,
});

Bun.serve({
  port: 3000,
  async fetch(request) {
    const url = new URL(request.url);

    if (url.pathname === "/api/checkout") {
      return checkoutHandler(request);
    }
    if (url.pathname === "/api/customer-portal" && request.method === "GET") {
      const user = await getSessionUser(request);
      if (!user?.dodoCustomerId) return new Response("Unauthorized", { status: 401 });
      // Overwrite any client-supplied ?customer_id= with the signed-in user's ID.
      url.searchParams.set("customer_id", user.dodoCustomerId);
      return portalHandler(new Request(url, request));
    }

    return new Response("Not Found", { status: 404 });
  },
});
```
