# Framework Adapters: Convex


**Package:** `@dodopayments/convex`

Convex uses a component-based architecture. Register the component in `convex.config.ts`:

```typescript
// convex/convex.config.ts
import { defineApp } from "convex/server";
import dodopayments from "@dodopayments/convex/convex.config";

const app = defineApp();
app.use(dodopayments);
export default app;
```

Run `npx convex dev` once to generate `components.dodopayments`. `identify` needs an app-owned lookup from the signed-in user to their Dodo customer ID. This assumes a `customers` table with `authId` and `dodoCustomerId` fields and a `by_auth_id` index; adapt it to your schema:

```typescript
// convex/customers.ts
import { internalQuery } from "./_generated/server";
import { v } from "convex/values";

export const getByAuthId = internalQuery({
  args: { authId: v.string() },
  handler: async (ctx, { authId }) =>
    ctx.db
      .query("customers")
      .withIndex("by_auth_id", (q) => q.eq("authId", authId))
      .unique(),
});
```

Then create a `DodoPayments` client in a local module and export its API methods:

```typescript
// convex/dodo.ts
import { DodoPayments } from "@dodopayments/convex";
import { components, internal } from "./_generated/api";

const apiKey = process.env.DODO_PAYMENTS_API_KEY;
if (!apiKey) throw new Error("DODO_PAYMENTS_API_KEY is not set");

export const dodo = new DodoPayments(components.dodopayments, {
  // Maps the signed-in Convex user to a Dodo customer; used by customerPortal.
  identify: async (ctx) => {
    const identity = await ctx.auth.getUserIdentity();
    if (!identity) return null;
    const customer = await ctx.runQuery(internal.customers.getByAuthId, {
      authId: identity.subject,
    });
    return customer ? { dodoCustomerId: customer.dodoCustomerId } : null;
  },
  apiKey,
  environment: process.env.DODO_PAYMENTS_ENVIRONMENT === "live_mode" ? "live_mode" : "test_mode",
});

export const { checkout, customerPortal } = dodo.api();
```

Call `checkout` from an **action** (mutations cannot make network calls), passing the checkout session fields in `payload`. The client sends a plan slug; the server maps it to a product ID and owns the return URL, so a caller cannot pick an arbitrary product or redirect target:

```typescript
// convex/payments.ts
import { action } from "./_generated/server";
import { v } from "convex/values";
import { checkout } from "./dodo";

// Public plan slug -> Dodo product ID. Never accept a product_id from the client.
const PRODUCT_IDS: Readonly<Record<string, string>> = {
  starter: "pdt_starter_monthly",
  pro: "pdt_pro_monthly",
};

export const createCheckout = action({
  args: { plan: v.string() },
  handler: async (ctx, { plan }) => {
    if (!Object.hasOwn(PRODUCT_IDS, plan)) throw new Error(`Unknown plan: ${plan}`);
    // Returns { checkout_url }
    return await checkout(ctx, {
      payload: {
        product_cart: [{ product_id: PRODUCT_IDS[plan], quantity: 1 }],
        return_url: process.env.DODO_PAYMENTS_RETURN_URL,
      },
    });
  },
});
```

Convex only supports session checkout, not static or dynamic modes.
