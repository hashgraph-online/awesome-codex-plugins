# Framework Adapters: Remix


**Package:** `@dodopayments/remix`

### Checkout

```typescript
// app/routes/api.checkout.tsx
import { Checkout } from "@dodopayments/remix";
import type { LoaderFunctionArgs, ActionFunctionArgs } from "@remix-run/node";
import { dodoEnvironment } from "~/lib/dodo-env";

const checkoutHandler = Checkout({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
});

export const loader = ({ request }: LoaderFunctionArgs) => checkoutHandler(request);
export const action = ({ request }: ActionFunctionArgs) => checkoutHandler(request);
```

### Customer Portal

```typescript
// app/routes/api.customer-portal.tsx
import { CustomerPortal } from "@dodopayments/remix";
import type { LoaderFunctionArgs } from "@remix-run/node";
import { dodoEnvironment } from "~/lib/dodo-env";
// your auth helper
import { getSessionUser } from "~/lib/auth.server";

const portalHandler = CustomerPortal({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: dodoEnvironment,
});

export const loader = async ({ request }: LoaderFunctionArgs) => {
  const user = await getSessionUser(request);
  if (!user?.dodoCustomerId) return new Response("Unauthorized", { status: 401 });

  // Overwrite any client-supplied ?customer_id= with the signed-in user's ID.
  const url = new URL(request.url);
  url.searchParams.set("customer_id", user.dodoCustomerId);
  return portalHandler(new Request(url, request));
};
```

### Webhooks

```typescript
// app/routes/api.webhook.tsx
import { Webhooks } from "@dodopayments/remix";
import type { ActionFunctionArgs } from "@remix-run/node";

export const action = ({ request }: ActionFunctionArgs) =>
  Webhooks({
    webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
    onPayload: async (payload) => {
      console.log("Webhook:", payload.type);
    },
  })(request);
```
