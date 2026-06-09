# Domain Pack: Payments And Billing

Use this when a plan touches checkout, subscriptions, invoices, entitlements,
webhooks, payment provider adapters, plan changes, trials, or billing portals.

## Evidence To Gather

- Existing account, organization, customer, and subscription models.
- Payment provider config and secret handling.
- Webhook verification and idempotency patterns.
- Entitlement checks and feature gates.
- Existing billing tests and fixtures.
- Rollback process for disabled checkout or provider incidents.

## Plan Must Decide

- Provider boundary and local subscription source of truth.
- Checkout creation contract.
- Webhook verification and replay protection.
- Idempotency keys and event ordering behavior.
- Entitlement read API consumed by product features.
- Failure behavior for payment failure, cancellation, and provider outage.

## Tests First

- Checkout creation requires authenticated account context.
- Invalid webhook signatures are rejected.
- Duplicate webhook events are idempotent.
- Subscription state transitions are correct.
- Entitlement reads reflect active, trialing, canceled, and past-due states.
- Logs exclude provider secrets and payment payloads beyond safe IDs.
