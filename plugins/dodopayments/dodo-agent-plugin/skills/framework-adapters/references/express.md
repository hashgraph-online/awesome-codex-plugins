# Framework Adapters: Express


**Package:** `@dodopayments/express`

### Checkout

The Express adapter names its checkout export `checkoutHandler` in lowercase, unlike every other adapter. `import { Checkout } from "@dodopayments/express"` does not resolve.

```typescript
import express from "express";
import { checkoutHandler } from "@dodopayments/express";
import { dodoEnvironment } from "./lib/dodo-env";

const app = express();
// Required before the POST route: the session/dynamic handlers read req.body.
app.use(express.json());

app.get("/api/checkout", checkoutHandler({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "static",
}));

app.post("/api/checkout", checkoutHandler({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  returnUrl: process.env.DODO_PAYMENTS_RETURN_URL,
  environment: dodoEnvironment,
  type: "session",
}));
```

### Customer Portal

The adapter's `CustomerPortal` reads `customer_id` from `req.query`, which you cannot safely rewrite in Express 5. Behind your auth middleware, call the SDK directly with the session's customer ID instead:

```typescript
import DodoPayments from "dodopayments";
import { dodoEnvironment } from "./lib/dodo-env";

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: dodoEnvironment,
});

// requireAuth = your session middleware; it must set req.user.
app.get("/api/customer-portal", requireAuth, async (req, res) => {
  const customerId = req.user?.dodoCustomerId; // from the session, never from req.query
  if (!customerId) return res.status(401).send("Unauthorized");
  const session = await client.customers.customerPortal.create(customerId);
  res.redirect(session.link);
});
```

### Webhooks

```typescript
import { Webhooks } from "@dodopayments/express";

// The Express handler verifies the signature against the PARSED req.body, so it
// needs express.json() (skip this line if already registered). Do NOT use express.raw() here - the
// handler would see a Buffer and reject every request.
app.use(express.json());

app.post("/api/webhook", Webhooks({
  webhookKey: process.env.DODO_PAYMENTS_WEBHOOK_KEY,
  onPayload: async (payload) => {
    console.log("Webhook:", payload.type);
  },
}));
```
