# Paddle Billing subscriptions

What Paddle's documentation said on the date at the end of this file, for granting access from Paddle Billing subscriptions (not Paddle Classic). The general pattern is in [events-in-any-order.md](events-in-any-order.md) and [entitlements-and-lifecycle.md](entitlements-and-lifecycle.md). Recheck the linked pages before relying on a value.

## Verification, in short

`Paddle-Signature: ts=<unix seconds>;h1=<hex>`: an HMAC-SHA256 of `ts`, a `:` and the raw body, keyed with the notification destination's secret. During a rotation more than one `h1` is sent; accept any match. Paddle's SDKs refuse a `ts` more than five seconds from the current time. The `build-webhook-endpoint` skill has the full scheme and the SDK notes in its `references/provider-paddle.md`. `assets/sign-test-event.mjs paddle` in this skill signs test events the same way.

## Statuses and access

| `status` | Paddle says | Access by default |
| --- | --- | --- |
| `trialing` | In trial; treat as active | Yes, until the trial end |
| `active` | Billing, not past due | Yes |
| `past_due` | A payment failed and is being retried. Paddle's guide keeps full access and shows a banner | Until the end of the last paid period plus the grace the user chose |
| `paused` | No transactions while paused | None, or read-only |
| `canceled` | Revoke access | None |

`scheduled_change` (`action` `cancel`, `pause` or `resume`, with `effective_at`) is set when a change waits for the next billing date; keep access until it takes effect. `current_billing_period` (`starts_at`, `ends_at`) is null for paused and canceled subscriptions. `custom_data` holds the app's own data from the checkout: put the app's checkout id there.

## Events

| Event | Meaning | Handler |
| --- | --- | --- |
| `subscription.created` | Created when an automatically collected transaction completes; carries the `transaction_id` | Link to the checkout row; grant |
| `subscription.activated`, `subscription.trialing` | Became active, or started a trial | Store |
| `subscription.updated` | Status, items, scheduled changes or billing period changed. Paddle says this covers renewals, plan changes and status changes | Store |
| `subscription.past_due` | An unpaid transaction | Store; record the grace end |
| `subscription.canceled` | Canceled. With a scheduled cancel, `subscription.updated` comes first and this event on the next billing date | Store; access ends |
| `subscription.paused`, `subscription.resumed` | Paused or resumed, at once or at the next billing date | Store |
| `transaction.completed` | Paddle finished processing a paid transaction; for renewals `billing_period` is set | Credits for that period |
| `transaction.payment_failed` | A payment failed | Nothing more than `past_due` gives |
| `adjustment.created`, `adjustment.updated` | Refund, credit or chargeback (`action` `refund`, `chargeback` and others; `status` `pending_approval`, `approved`, `rejected`, `reversed`) with `transaction_id` and `subscription_id` | Revoke on an approved refund or a chargeback, as decided; credits to the reversal code |

Paddle does not document that a refund or a chargeback cancels the subscription. Most live refunds start as `pending_approval`: act on the approved state.

## Order and duplicates

Paddle does not guarantee order and says to store `occurred_at` and compare it before changing state: a newer-wins value. Deduplicate on `event_id`, not `notification_id` (a replay is a new notification with the same event id). Paddle guarantees at-least-once delivery, wants a 200 within five seconds, and retries up to 60 times over about two days in live mode.

## Dunning

Without Paddle Retain, failed payments are retried up to seven times over 30 days, then the subscription is canceled. With Retain, the account chooses whether the subscription pauses or cancels after dunning. Sandbox accounts do not retry. Manually collected subscriptions become past due 24 hours after the due date, with no retries. Canceled subscriptions cannot be reinstated.

## Plan changes

`proration_billing_mode`: `prorated_immediately`, `full_immediately`, `prorated_next_billing_period`, `full_next_billing_period`, `do_not_bill`. The change arrives as `subscription.updated`.

## Trials

Free and paid trials require payment details at sign-up and become `active` after the first charge. Card-less trials, in early access, are canceled when the trial ends without payment details. The app's one-trial-per-person claim comes before the checkout.

## Reconciliation

Paddle recommends a periodic job that lists subscriptions through the API. `GET /subscriptions` takes `status`, `customer_id`, `id` and other filters, `per_page` up to 200, and pages with `after`; use `meta.pagination.has_more`, not `estimated_total`.

## Bugs that ship

- Ending access on `subscription.updated` with a scheduled cancel, which runs to the next billing date.
- Applying `subscription.updated` events in arrival order without comparing `occurred_at`.
- Granting credits on `transaction.paid` and again on `transaction.completed`.
- Treating `adjustment.created` with `pending_approval` as a refund that happened.

## Sources

- https://developer.paddle.com/build/subscriptions/provision-access-webhooks
- https://developer.paddle.com/api-reference/subscriptions/overview
- https://developer.paddle.com/api-reference/subscriptions/get-subscription
- https://developer.paddle.com/api-reference/subscriptions/list-subscriptions
- https://developer.paddle.com/webhooks/overview
- https://developer.paddle.com/webhooks/respond-to-webhooks
- https://developer.paddle.com/webhooks/subscriptions/subscription-created
- https://developer.paddle.com/webhooks/subscriptions/subscription-canceled
- https://developer.paddle.com/webhooks/subscriptions/subscription-paused
- https://developer.paddle.com/webhooks/subscriptions/subscription-past-due
- https://developer.paddle.com/webhooks/transactions/transaction-completed
- https://developer.paddle.com/webhooks/transactions/transaction-paid
- https://developer.paddle.com/build/retain/configure-payment-recovery-dunning
- https://developer.paddle.com/concepts/retain/payment-recovery-dunning
- https://developer.paddle.com/concepts/subscriptions/proration
- https://developer.paddle.com/concepts/subscriptions/trials
- https://developer.paddle.com/build/subscriptions/cardless-trials
- https://developer.paddle.com/api-reference/adjustments/overview

Checked 2026-11-16.
