# Dodo Payments Credit-Based Billing: End-to-end AI token example


Assume the dashboard/API configuration already has:

- a custom-unit entitlement named `AI Token Credits`, precision `0`;
- a subscription product that issues credits each cycle;
- a `sum` meter whose case-sensitive event name is `ai.tokens` and key is `tokens`;
- that meter linked through `credit_entitlement_id` and `meter_units_per_credit`;
- a one-time product `pdt_ai_token_topup` with credits attached.

The following server-side script records actual model usage, reads the credit balance, and creates a top-up checkout when your verified low-balance webhook flow prompts the customer:

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments({
  bearerToken: process.env['DODO_PAYMENTS_API_KEY'],
  environment: 'test_mode',
});

async function recordTokenUsage(
  customerId: string,
  generationId: string,
  model: string,
  promptTokens: number,
  completionTokens: number,
): Promise<number> {
  const tokens = promptTokens + completionTokens;
  const response = await client.usageEvents.ingest({
    events: [
      {
        event_id: `generation:${generationId}`,
        customer_id: customerId,
        event_name: 'ai.tokens',
        timestamp: new Date().toISOString(),
        metadata: {
          tokens,
          prompt_tokens: promptTokens,
          completion_tokens: completionTokens,
          model,
        },
      },
    ],
  });

  return response.ingested_count;
}

async function readTokenBalance(
  customerId: string,
  creditEntitlementId: string,
): Promise<string> {
  const response = await client.creditEntitlements.balances.retrieve(
    customerId,
    { credit_entitlement_id: creditEntitlementId },
  );
  return response.balance;
}

async function createTopUpCheckout(customerEmail: string) {
  return client.checkoutSessions.create({
    product_cart: [
      { product_id: 'pdt_ai_token_topup', quantity: 1 },
    ],
    customer: { email: customerEmail },
    return_url: 'https://app.example.com/credits',
  });
}

async function main(): Promise<void> {
  const customerId = 'cus_8VbC6JDZzPEqfBPUdpj0K';
  const creditEntitlementId = 'cde_ztxm5XJsKxWucRWA3rjdM';

  const ingested = await recordTokenUsage(
    customerId,
    'gen_01JZAIEXAMPLE',
    'example-model',
    1800,
    700,
  );
  console.log({ ingested });

  // Meter deduction is asynchronous; this read may still show the prior balance.
  const balance = await readTokenBalance(customerId, creditEntitlementId);
  console.log({ balance });

  // Call this after a verified credit.balance_low event and customer action.
  const topUp = await createTopUpCheckout('customer@example.com');
  console.log(topUp);
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : error);
  process.exitCode = 1;
});
```

The lifecycle is:

1. The model returns actual prompt and completion token counts.
2. The app ingests one uniquely identified `ai.tokens` event.
3. The meter aggregates the `tokens` metadata value.
4. The worker converts units into credits and deducts from non-expired grants, earliest-expiring first.
5. Dodo emits `credit.deducted`; when configured threshold conditions are met, it emits `credit.balance_low`.
6. The app notifies the customer and offers checkout for the attached top-up product.

Do not poll every minute to synthesize your own threshold event. Use the verified webhook and keep polling only for user-interface freshness.
