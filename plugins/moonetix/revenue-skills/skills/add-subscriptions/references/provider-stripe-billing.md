# Stripe Billing

What Stripe's documentation said on the date at the end of this file, for granting access from Stripe Billing subscriptions. The general pattern is in [events-in-any-order.md](events-in-any-order.md) and [entitlements-and-lifecycle.md](entitlements-and-lifecycle.md). Recheck the linked pages before relying on a number.

## Verification, in short

`Stripe-Signature` carries `t=<unix seconds>` and one or more `v1=` entries: an HMAC-SHA256 of `t`, a `.` and the raw body, keyed with the endpoint's `whsec_` secret. Accept the event when any `v1` matches and `t` is within the tolerance (the libraries use 300 seconds). With the official library: `stripe.webhooks.constructEvent(rawBody, header, secret)`. The `build-webhook-endpoint` skill has the full scheme in its `references/provider-stripe.md`, with the raw body in five frameworks and the rotation steps. `assets/sign-test-event.mjs stripe` in this skill signs test events the same way.

## API version

The current version is `2026-10-28.endive`. Since `2025-03-31.basil`:

- `current_period_start` and `current_period_end` are on the subscription items (`items.data[].current_period_end`), not on the subscription.
- An invoice names its subscription in `parent.subscription_details.subscription` (check `parent.type` is `subscription_details`), with `parent.subscription_details.metadata`, a snapshot of the subscription's metadata when the invoice was finalized. `invoice.subscription` is gone.
- Charges no longer name their invoice (`charge.invoice` is removed). The link is the InvoicePayment object: `GET /v1/invoice_payments?payment[type]=payment_intent&payment[payment_intent]=<pi>&status=paid`, then the invoice's parent.
- The service period of a line is `lines.data[].period`. The invoice's own `period_start` and `period_end` are not the service period.

The event payload uses the API version of the webhook endpoint, fixed when it was created. Fetch with the same version (`Stripe-Version` header, or the library's `apiVersion`) so that fetched objects and payloads have one shape.

## Statuses and access

`status` is one of `incomplete`, `incomplete_expired`, `trialing`, `active`, `past_due`, `canceled`, `unpaid`, `paused`.

| Status | Stripe says | Access by default |
| --- | --- | --- |
| `incomplete` | The first payment has 23 hours to succeed | None |
| `incomplete_expired` | The first payment never succeeded; create a new subscription to re-enable access | None |
| `trialing` | You can safely provision | Until the trial end |
| `active` | In good standing | Until the period end |
| `past_due` | The latest invoice failed or was not attempted; retries may happen | Until the end of the last paid period plus the grace the user chose. Stripe states no rule |
| `unpaid` | Only when the settings say so; revoke access | None |
| `canceled` | Terminal; revoke access | None |
| `paused` | No invoices are created | None |

`active` does not mean every open invoice is paid: with the default status resolution ("Latest invoice") it follows the latest one. A delayed payment method such as ACH can make a subscription `active` and fail later; Stripe then voids the invoice and the subscription stays `active`.

## Events

| Event | What Stripe says | What the handler does |
| --- | --- | --- |
| `checkout.session.completed` (mode `subscription`) | Provision, store the subscription and customer ids | Link the subscription to the checkout row; fetch the subscription |
| `customer.subscription.created` | May arrive with status `incomplete` | Fetch and store |
| `customer.subscription.updated` | Start or change, including renewals, plan changes and scheduled cancels | Fetch and store |
| `customer.subscription.deleted` | The subscription ended: canceled now, or `cancel_at_period_end` reached the period end | Fetch and store; access ends |
| `customer.subscription.paused`, `customer.subscription.resumed` | Status `paused` began or ended. Not sent for `pause_collection` | Fetch and store |
| `customer.subscription.trial_will_end` | Three days before the trial ends by default, or at once for shorter trials | A reminder only |
| `invoice.paid` | Provision when this arrives and the subscription is `active`; retrieve the subscription to confirm | Fetch the subscription; grant the period's credits for `subscription_create` and `subscription_cycle` |
| `invoice.payment_succeeded` | A payment attempt succeeded | The same payment as `invoice.paid` when both are enabled: let the credit key decide, or subscribe to one |
| `invoice.payment_failed` | Notify the customer, collect a new payment method | Fetch; record the grace end from the last paid period |
| `invoice.payment_action_required` | The customer must authenticate | Notify; access follows the status |
| `charge.refunded`, `charge.dispute.created` | A refund (including partial) or a dispute | Find the invoice through `invoice_payments`, then the subscription; record the revocation the user decided on |
| `entitlements.active_entitlement_summary.updated` | Stripe Entitlements: grant or disable features | An alternative source of features, see below |

Stripe's minimum for Checkout subscriptions is `checkout.session.completed`, `invoice.paid` and `invoice.payment_failed`. Subscribe to `customer.subscription.*` as well, or a cancel from the Customer Portal reaches the app only through reconciliation.

## Order, duplicates, fetching

- Stripe does not guarantee order. Do not use `created` to order events or to detect duplicates: distinct events can share a second.
- Deduplicate on `event.id`. Two separate events can describe one change; `data.object.id` with `event.type` identifies them.
- Snapshot events can be outdated by the time they are processed. Retrieve the subscription, the invoice or the charge from the API for the current state.
- Live mode retries for up to three days; sandboxes three times over a few hours.

## Retries and dunning

Smart Retries is on by default for new accounts: up to 8 retries within 2 weeks; the window can be 1 week to 2 months. When retries run out, the subscription is canceled, marked `unpaid`, left `past_due` or paused, as set under Billing, Revenue recovery. Smart Retries do not retry the first payment of an `incomplete` subscription. `invoice.payment_failed` carries `attempt_count` and `next_payment_attempt`.

## Cancel, pause, change

- `DELETE /v1/subscriptions/{id}` cancels at once by default. A canceled subscription cannot be reactivated. Canceling does not refund: `prorate` and `invoice_now` produce a credit to the customer balance, and a refund is a separate call.
- `cancel_at_period_end: true` keeps the subscription until the period ends; setting it back to `false` before then undoes it. `cancel_at` cancels at a set time and can shorten the current period. Subscriptions in flexible billing mode scheduled to cancel from the Customer Portal show `cancel_at` with `cancel_at_period_end` false: check both.
- `canceled_at` is when the cancel was requested, not when access ends. `ended_at` is when the subscription ended. `cancellation_details.reason` is `cancellation_requested`, `payment_failed`, `payment_disputed` or `canceled_by_retention_policy`.
- `pause_collection` (`keep_as_draft`, `mark_uncollectible`, `void`) keeps the subscription `active` and keeps access; no `paused` event is sent. The pause endpoint and a trial that ends without a payment method set status `paused`, truncate the period and send `customer.subscription.paused`.
- Price changes apply at once. `proration_behavior` is `create_prorations` (the default), `always_invoice` or `none`. A change whose payment fails moves the subscription to `past_due`; `payment_behavior=pending_if_incomplete` applies the change only after payment.

## Disputes and refunds

A refund does not cancel the subscription; no page says it does. On disputes, the subscription keeps cycling by default; a Dashboard setting can cancel it at once or at period end, with `cancellation_details.reason` `payment_disputed`. Without that setting, the app's own rule ends access, as in [entitlements-and-lifecycle.md](entitlements-and-lifecycle.md). The credits of a refunded period go back through the `handle-refunds-and-reversals` skill.

## Customer Portal

Customers update payment methods, change plans, pause, resume and cancel, at once or at period end as configured (`features.subscription_cancel.mode`). Every change arrives as `customer.subscription.updated` or `.deleted`. Nothing in the portal talks to the app directly: the events and the reconciliation job are the only way the app learns about it.

## Entitlements API

Stripe Entitlements attaches features to products and keeps active entitlements while a customer has an active subscription; they drop out on cancellation, including after failed payments, and on pause. `GET /v1/entitlements/active_entitlements?customer=` lists them, and `entitlements.active_entitlement_summary.updated` carries the full summary (up to 10 entries inline). Stripe recommends storing them in the app. Stripe does not document which statuses, such as `past_due`, keep entitlements, so an app with its own grace rule computes access itself.

## Reconciliation

`GET /v1/subscriptions?status=all&limit=100`, paged with `starting_after` while `has_more` is true. Without `status`, canceled subscriptions are left out. Subscriptions on test clocks are listed only with `test_clock` or `customer`.

## Test locally

- Test clocks move a sandbox customer's time forward: create one, create the customer with `test_clock`, advance with `POST /v1/test_helpers/test_clocks/{id}/advance`. They cover renewals, failed payments and trial ends.
- `assets/sign-test-event.mjs stripe <type> '<object json>'` signs an event with the local test secret for the probe. A handler that fetches from the API needs the sandbox, a test clock or a local stand-in that returns the same objects.

## Bugs that ship

- Reading `subscription.current_period_end` on a current API version: it is undefined, and access ends at once or never.
- Granting on `customer.subscription.created`, which arrives `incomplete` before payment.
- Granting a new period on every `invoice.paid`, so a `subscription_update` proration invoice grants a second allowance in the same period.
- Keying the period's credits on the event id, so `invoice.paid` and `invoice.payment_succeeded` for one invoice grant twice.
- Keeping access while `past_due` until the item's `current_period_end`, which already points a month ahead.
- Removing access on `cancel_at_period_end`, which the user paid through.
- Never subscribing to `customer.subscription.deleted`, so canceled subscriptions keep access.
- Listing subscriptions without `status=all` in the reconciliation job.
- Treating `charge.refunded` for a subscription charge as an unknown order and answering 4xx, so Stripe retries it for days.

## Sources

- https://docs.stripe.com/billing/subscriptions/overview
- https://docs.stripe.com/billing/subscriptions/webhooks
- https://docs.stripe.com/billing/subscriptions/build-subscriptions
- https://docs.stripe.com/webhooks
- https://docs.stripe.com/upgrades
- https://docs.stripe.com/changelog/basil/2025-03-31/deprecate-subscription-current-period-start-and-end
- https://docs.stripe.com/changelog/basil/2025-03-31/adds-new-parent-field-to-invoicing-objects
- https://docs.stripe.com/changelog/basil/2025-03-31/add-support-for-multiple-partial-payments-on-invoices
- https://docs.stripe.com/api/subscriptions/object
- https://docs.stripe.com/api/subscriptions/list
- https://docs.stripe.com/api/invoices/object
- https://docs.stripe.com/api/invoice-line-item/object
- https://docs.stripe.com/api/events/types
- https://docs.stripe.com/billing/revenue-recovery/smart-retries
- https://docs.stripe.com/billing/subscriptions/cancel
- https://docs.stripe.com/billing/subscriptions/pause-payment
- https://docs.stripe.com/billing/subscriptions/pause
- https://docs.stripe.com/billing/subscriptions/prorations
- https://docs.stripe.com/billing/subscriptions/change-price
- https://docs.stripe.com/billing/subscriptions/billing-mode/compare
- https://docs.stripe.com/customer-management
- https://docs.stripe.com/customer-management/configure-portal
- https://docs.stripe.com/billing/entitlements
- https://docs.stripe.com/billing/testing/test-clocks/api-advanced-usage

Checked 2026-11-16.
