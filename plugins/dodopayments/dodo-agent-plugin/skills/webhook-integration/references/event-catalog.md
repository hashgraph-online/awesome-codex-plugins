# Dodo Payments Webhook Integration: Webhook Event Catalog


Dodo delivers 48 event types across ten families (payment, subscription, refund, dispute, license key, entitlement grant, credit, abandoned checkout, dunning, payout). Subscribe to only the events you need.

### Payment events

| Event | When it fires | What to do |
|-------|---|---|
| `payment.succeeded` | Payment completed successfully | Grant access, send confirmation, update order status |
| `payment.failed` | Payment attempt failed | Notify customer, suggest retry or alternative payment method |
| `payment.processing` | Payment is still being processed | Acknowledge receipt, wait for `payment.succeeded` or `payment.failed` |
| `payment.cancelled` | Payment was cancelled before completion | Update order status, notify customer if applicable |

### Subscription events

| Event | When it fires | What to do |
|-------|---|---|
| `subscription.active` | Subscription becomes active; recurring charges are scheduled | Grant subscription access, send welcome email |
| `subscription.updated` | Any field on the subscription changes | Sync changes to your database |
| `subscription.past_due` | Renewal failed and the grace period opened; customer keeps access (payload has `past_due_ends_at`) | Prompt for payment before the deadline |
| `subscription.on_hold` | Failed renewal stops renewals and revokes access | Notify customer, prompt payment method update |
| `subscription.paused` | Subscription is deliberately paused | Suspend access while paused |
| `subscription.unpaused` | Paused subscription is resumed | Restore access |
| `subscription.renewed` | Subscription amount successfully deducted for a billing period | Log renewal, update next billing date |
| `subscription.plan_changed` | Plan upgraded, downgraded, or modified | Update customer's access level or feature set |
| `subscription.update_payment_method` | Payment method is updated | Sync the new payment method to your records |
| `subscription.cancelled` | Merchant or customer cancels the subscription | Revoke access, send cancellation confirmation |
| `subscription.failed` | Subscription creation fails (mandate creation failed) | Notify customer, suggest alternative payment method |
| `subscription.expired` | Subscription reaches the end of its term | Revoke access, offer renewal or upgrade |

### Refund events

| Event | When it fires | What to do |
|-------|---|---|
| `refund.succeeded` | Refund successfully processed | Update order status, revoke access if applicable |
| `refund.failed` | Refund processing fails | Alert team, investigate reason |

### Dispute events

| Event | When it fires | What to do |
|-------|---|---|
| `dispute.opened` | Customer initiates a dispute | Alert team, prepare evidence |
| `dispute.expired` | Dispute expires without resolution | Log outcome |
| `dispute.accepted` | Merchant accepts the dispute | Process refund if not already done |
| `dispute.cancelled` | Customer or system cancels the dispute | Log outcome |
| `dispute.challenged` | Merchant challenges the dispute | Prepare additional evidence |
| `dispute.won` | Merchant wins the dispute | Log outcome, retain funds |
| `dispute.lost` | Merchant loses the dispute | Process refund, log outcome |

### License key events

| Event | When it fires | What to do |
|-------|---|---|
| `license_key.created` | License key is generated | Legacy; prefer `entitlement_grant.created` with `status: "Delivered"` |

### Entitlement grant events

| Event | When it fires | What to do |
|-------|---|---|
| `entitlement_grant.created` | Grant row is created. Auto-fulfilled license keys arrive here with `status: "Delivered"` and a `license_key`; no `.delivered` follows | Grant access when `status` is `Delivered`; otherwise prepare for fulfillment |
| `entitlement_grant.delivered` | An existing grant moves to `Delivered` (manual fulfillment, or a revoked grant restored) | Grant platform, file, or license-key access |
| `entitlement_grant.failed` | Delivery fails and is no longer retried | Alert team, inspect `error_code` and `error_message` |
| `entitlement_grant.revoked` | Access is withdrawn | Revoke customer access, inspect `revocation_reason` |

### Credit events

These concern virtual credit entitlements, not monetary wallet balances.

| Event | When it fires | What to do |
|-------|---|---|
| `credit.added` | Credits granted via subscription, purchase, add-on, or API | Update internal credit balance, log grant |
| `credit.deducted` | Usage or manual debit consumes credits | Update internal credit balance |
| `credit.expired` | Unused credits reach expiry | Log expiration, notify customer if applicable |
| `credit.rolled_over` | Unused credits carried into a new grant | Update internal balance |
| `credit.rollover_forfeited` | Credits forfeited at max rollover count | Log forfeiture |
| `credit.overage_charged` | Overage charged after usage exceeds balance | Update internal balance, notify customer |
| `credit.overage_reset` | Accumulated overage reset (e.g., new billing cycle) | Update internal balance |
| `credit.manual_adjustment` | Manual credit or debit adjustment made | Update internal balance, log adjustment |
| `credit.balance_low` | Balance falls below configured threshold | Notify customer, suggest purchase |

### Recovery and dunning events

| Event | When it fires | What to do |
|-------|---|---|
| `abandoned_checkout.detected` | Failed or incomplete checkout classified as abandoned (after 60 min) | Monitor recovery link usage |
| `abandoned_checkout.recovered` | Customer pays through recovery link | Log recovery, update order status |
| `dunning.started` | Dunning attempt begins after subscription enters `on_hold` | Monitor dunning progress |
| `dunning.recovered` | Customer updates payment method and charge succeeds | Reactivate subscription, send confirmation |

### Payout events

These concern your own funds moving to your bank account - use them for bookkeeping, not customer access.

| Event | When it fires | What to do |
|-------|---|---|
| `payout.created` | Payout is created (formerly emitted as `payout.not_initiated`) | Record the pending payout |
| `payout.in_progress` | Payout processing starts | Mark as in transit |
| `payout.on_hold` | Payout is paused or under review | Check whether more information is required |
| `payout.success` | Payout settles to your bank account | Reconcile in accounting |
| `payout.failed` | Payout fails; amount and fees return to your wallet | Alert finance, check bank details |

---
