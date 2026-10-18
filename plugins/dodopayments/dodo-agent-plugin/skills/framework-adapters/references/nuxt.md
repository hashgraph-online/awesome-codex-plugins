# Framework Adapters: Nuxt


**Package:** `@dodopayments/nuxt`

Add the module to `nuxt.config.ts` and configure runtime variables:

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ["@dodopayments/nuxt"],
  runtimeConfig: {
    private: {
      bearerToken: process.env.NUXT_PRIVATE_BEARER_TOKEN,
      webhookKey: process.env.NUXT_PRIVATE_WEBHOOK_KEY,
      environment: process.env.NUXT_PRIVATE_ENVIRONMENT,
      returnUrl: process.env.NUXT_PRIVATE_RETURN_URL,
    },
  },
});
```

### Checkout

The Nuxt module registers its handlers with `addServerImportsDir`, so `checkoutHandler`, `customerPortalHandler`, and `Webhooks` are **auto-imported** inside `server/`. Do not import them from `@dodopayments/nuxt` — that entry point exports only the Nuxt module itself, and a named import from it will not resolve.

```typescript
// server/routes/api/checkout.ts
// checkoutHandler and useRuntimeConfig are auto-imported by the module.
const config = useRuntimeConfig();

export default checkoutHandler({
  bearerToken: config.private.bearerToken,
  returnUrl: config.private.returnUrl,
  environment: config.private.environment,
  type: "session",
});
```

### Webhooks

```typescript
// server/routes/api/webhook.ts
// Webhooks and useRuntimeConfig are auto-imported by the module.
const config = useRuntimeConfig();

export default Webhooks({
  webhookKey: config.private.webhookKey,
  onPayload: async (payload) => {
    console.log("Webhook:", payload.type);
  },
});
```
