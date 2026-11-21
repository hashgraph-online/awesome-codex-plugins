# RevenueCat as an aggregator

What RevenueCat's documentation said on the date at the end of this file. RevenueCat sits between the app and the stores (App Store, Google Play, Amazon, Stripe, Paddle, its own web billing) and reports one entitlement per app user. The general pattern is in [events-in-any-order.md](events-in-any-order.md) and [entitlements-and-lifecycle.md](entitlements-and-lifecycle.md). Recheck the linked pages before relying on a value.

## Verification, in short

Check the `Authorization` header value configured on the webhook integration on every request, in constant time. Optional HMAC signing adds `X-RevenueCat-Webhook-Signature: t=<unix seconds>,v1=<hex>` over `t`, a `.` and the raw body. The `build-webhook-endpoint` skill has the details in its `references/provider-revenuecat.md`. `assets/sign-test-event.mjs revenuecat` in this skill signs test events the same way.

## Current state

RevenueCat recommends calling its REST API after receiving any webhook. v1 `GET /subscribers/{app_user_id}` returns the customer info; its `entitlements` include expired ones, so compare each entitlement's expiry with the current time. v2 `GET /projects/{project_id}/customers/{customer_id}/active_entitlements` returns the active ones with `expires_at` (null for lifetime). Note that the v1 call creates the customer when it does not exist.

Store one row per app user and entitlement, from the API's answer.

## Events

| `type` | Meaning | Handler |
| --- | --- | --- |
| `INITIAL_PURCHASE` | First purchase; `period_type` `TRIAL` for a trial start | Fetch; grant |
| `RENEWAL` | Renewed, or a lapsed user resubscribed; `is_trial_conversion` on a trial's first charge | Fetch; credits for `transaction_id` |
| `CANCELLATION` | Canceled or refunded. `cancel_reason` `UNSUBSCRIBE`, `BILLING_ERROR`, `DEVELOPER_INITIATED`, `PRICE_INCREASE`, `CUSTOMER_SUPPORT`, `UNKNOWN` | Fetch. Access continues until `EXPIRATION`, except a refund the app decided to end at once |
| `UNCANCELLATION` | Auto-renew turned back on | Fetch |
| `BILLING_ISSUE` | A renewal failed; `grace_period_expiration_at_ms` when the store has a grace period | Fetch; access until the grace end |
| `EXPIRATION` | Access should be removed. `expiration_reason` as `cancel_reason`, plus `SUBSCRIPTION_PAUSED` | Fetch; access ends |
| `PRODUCT_CHANGE` | Plan changed | Fetch |
| `SUBSCRIPTION_PAUSED` | Paused | Fetch |
| `SUBSCRIPTION_EXTENDED` | Expiry extended | Fetch |
| `TRANSFER` | Entitlements moved between app user ids (`transferred_from`, `transferred_to`); sent for the destination only | Fetch both users |
| `TEMPORARY_ENTITLEMENT_GRANT` | Access for at most 24 hours while a purchase is confirmed | Fetch; never grant credits on it |
| `REFUND_REVERSED` | A refund was reversed | Fetch; clear the revocation |
| `NON_RENEWING_PURCHASE`, `VIRTUAL_CURRENCY_TRANSACTION`, `INVOICE_ISSUANCE`, `TEST` and others | Not subscription access | Acknowledge |

`CUSTOMER_SUPPORT` as a `cancel_reason` means a refund. RevenueCat warns that a refund does not necessarily turn off auto-renew, and that for subscriptions the event fires only when the latest period is refunded. Check the current state.

## Fields

`id` (retries reuse it and `event_timestamp_ms`), `app_user_id`, `original_app_user_id`, `aliases`, `entitlement_ids` (null when the product maps to no entitlement), `expiration_at_ms`, `period_type` (`TRIAL`, `INTRO`, `NORMAL`, `PROMOTIONAL`, `PREPAID`), `environment` (`SANDBOX` or `PRODUCTION`: refuse sandbox events in production), `store`, `transaction_id`, `original_transaction_id`. `event_timestamp_ms` is not necessarily when the action happened.

## Order and duplicates

RevenueCat promises at least one delivery: deduplicate on `id`. It documents no order, apart from saying that `BILLING_ISSUE` and a billing-error `CANCELLATION`, sent together, can arrive in either order. Answer within 60 seconds; it retries up to five times over about 80 minutes, then stops, which makes the reconciliation job necessary.

## Grace periods

Users keep access during a store's grace period once the store reports it. For Stripe the grace is already in the expiration date; for Paddle the grace field is the billing period end. Amazon has no grace period.

## Transfers and restores

The project's restore behavior decides what a restore does: transfer to the new app user id (the default), transfer only if there is no active subscription, keep with the original id, or share (legacy). A transfer moves the entitlement off the first user. Choose the behavior with the user: the default lets one store account move access between app accounts.

## Trials

Apple and Amazon apply introductory offers automatically; on Google Play only eligible offers are shown. RevenueCat's own eligibility check is best effort, and the store's payment sheet decides.

## Bugs that ship

- Granting from the webhook body without fetching, so events applied in the wrong order leave the wrong state.
- Treating `CANCELLATION` as the end of access.
- Accepting `SANDBOX` events in production.
- Granting period credits on `TEMPORARY_ENTITLEMENT_GRANT` and again on `INITIAL_PURCHASE`.
- Keying the user on `app_user_id` alone when anonymous ids are later aliased: check `original_app_user_id` and `aliases`.

## Sources

- https://www.revenuecat.com/docs/integrations/webhooks
- https://www.revenuecat.com/docs/integrations/webhooks/event-types-and-fields
- https://www.revenuecat.com/docs/integrations/webhooks/event-flows
- https://www.revenuecat.com/docs/subscription-guidance/how-grace-periods-work
- https://www.revenuecat.com/docs/projects/restore-behavior
- https://www.revenuecat.com/docs/subscription-guidance/subscription-offers
- https://www.revenuecat.com/docs/api-v1/customers
- https://www.revenuecat.com/docs/api-v1/customer-info-model
- https://www.revenuecat.com/docs/api-v2/customer

Checked 2026-11-16.
