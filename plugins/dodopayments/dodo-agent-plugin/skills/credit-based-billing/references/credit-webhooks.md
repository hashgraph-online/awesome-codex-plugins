# Dodo Payments Credit-Based Billing: Handle credit webhooks


Webhook signature verification, raw-body handling, retries, and event deduplication are covered in the `webhook-integration` skill. Verify with `client.webhooks.unwrap()` before dispatching any event; never trust a parsed, unverified body.

All credit events except `credit.balance_low` use the full ledger payload.

| Exact event | Application action |
|---|---|
| `credit.added` | Refresh cached balance; correlate the grant or purchase and ledger entry. |
| `credit.deducted` | Refresh cached balance and usage display; reconcile the source usage/job. |
| `credit.expired` | Refresh balance; notify only if your product policy promises expiry notices. |
| `credit.rolled_over` | Refresh balance and expose the new rollover grant in account history. |
| `credit.rollover_forfeited` | Refresh balance and explain forfeiture according to the configured rollover limit. |
| `credit.overage_charged` | Reconcile the overage charge with billing and customer-visible history. |
| `credit.overage_reset` | Clear cached overage state after confirming the ledger payload. |
| `credit.manual_adjustment` | Reconcile the adjustment with its internal support/admin operation. |
| `credit.balance_low` | Deduplicate, refresh the authoritative balance, notify the customer, and offer upgrade or top-up. |

### Low-balance payload

`credit.balance_low` has a dedicated payload:

```json
{
  "business_id": "bus_H4ekzPSlcg",
  "type": "credit.balance_low",
  "timestamp": "2025-08-04T06:15:00.000000Z",
  "data": {
    "payload_type": "CreditBalanceLow",
    "customer_id": "cus_8VbC6JDZzPEqfBPUdpj0K",
    "subscription_id": "sub_7EeHq2ewQuadropD2ra",
    "credit_entitlement_id": "cent_9xY2bKwQn5MjRpL8d",
    "credit_entitlement_name": "API Credits",
    "available_balance": "15",
    "subscription_credits_amount": "100",
    "threshold_percent": 20,
    "threshold_amount": "20"
  }
}
```

### Low-balance notification flow

1. Verify the raw webhook and deduplicate by `webhook-id` as described in `webhook-integration`.
2. Confirm `type === 'credit.balance_low'` and validate the dedicated payload.
3. Map `customer_id` to the authenticated application account; do not accept a customer ID supplied by a browser.
4. Read the current balance with `balances.retrieve(...)` because another grant or deduction may have occurred since emission.
5. If the balance is still below your customer-notification policy, enqueue one notification keyed by webhook ID or threshold occurrence.
6. Link to a one-time top-up checkout or plan-upgrade flow.
7. Record notification delivery separately from the Dodo ledger; never manufacture a ledger entry for an email.
