# Entitlements and the subscription lifecycle

An entitlement answers one question at the moment a feature is used: may this account use this feature now? This file covers the data that answers it, the function that computes it, and what each step of a subscription's life does to it. The provider-specific names are in the provider references.

## Store the provider's state, compute access

Keep one row per subscription at the provider, as in `assets/subscriptions.postgres.sql`. The row holds what the provider says: its status, the current period, whether the subscription ends at the period end, and whether a payment was refunded or charged back. It does not hold a yes or no for access.

Access is computed from those rows and the current time, on the server, every time a feature is used:

```js
// The statuses that can still give access. Everything else, including any status the code
// does not know, gives none.
const KEEPS_ACCESS = new Set(['active', 'trialing', 'past_due', 'in_grace_period']);

// subscriptions: the account's rows. nowMs: Date.now() at the time of the request.
export function hasEntitlement(subscriptions, plan, nowMs) {
  return subscriptions.some((s) => {
    if (s.plan !== plan || s.revoked_at !== null) return false;
    if (!KEEPS_ACCESS.has(s.status)) return false;
    const until = s.grace_until ?? s.paid_through;
    return until !== null && nowMs < until;
  });
}
```

Why this shape:

- **Time ends access without an event.** A canceled month, a trial without payment and a grace period all end at a stored date. A check that waits for the provider's "expired" event keeps access open for as long as that event is late or lost.
- **Several subscriptions, one answer.** A user who bought twice, or who has a store subscription and a web one, keeps access until the last of them ends. A single `is_premium` column that every event overwrites loses that the moment one of them is canceled.
- **Unknown statuses deny.** Providers add statuses. A check that lists the statuses that deny lets every new one through.
- **No cached copy decides.** A plan in a session cookie, a JWT claim or the client's local storage is a display. If a token carries the plan, it expires within minutes and the server checks the row for anything that costs money.

Map each plan to the features it unlocks in one server-side table. The provider's price or product id selects the plan; the client never names it.

## The lifecycle

What each step does to the stored row, and to access. The provider references map their event names onto these rows.

| Step | What happens at the provider | Stored | Access |
| --- | --- | --- | --- |
| Checkout started | A subscription may exist, unpaid (Stripe `incomplete`, Google Play pending) | The app's own checkout row, written before the redirect | None |
| First payment succeeded | The subscription is active | Status, period, `paid_through` = period end | Yes |
| Free trial started | The provider's trial status, no payment yet | `trial` = true, `paid_through` = trial end | Yes, until the trial end |
| Renewed | A new period, paid | New period, `paid_through` = new period end | Yes |
| Renewal payment failed | The provider retries: Stripe `past_due`, App Store billing retry, Google Play grace period then account hold, Paddle `past_due` | `grace_until` = end of the last paid period plus the grace the user chose, or the store's own grace end | Yes, until `grace_until` |
| Retries exhausted | Canceled, unpaid, expired or on hold, depending on the provider and its settings | Status | None |
| Recovered after a failure | Paid again | New `paid_through`, `grace_until` cleared | Yes |
| Canceled at period end | Still active, marked to end (Stripe `cancel_at_period_end` or `cancel_at`, Apple auto-renew off, Google Play `CANCELED` with an expiry in the future, Paddle `scheduled_change`) | `cancel_at_period_end` = true, no grace | Yes, until `paid_through` |
| Ended at period end | Canceled or expired | Status | None |
| Canceled now | Canceled at once | Status | None |
| Paused | Paused, no payment collected | Status | None, unless the user decided otherwise |
| Resumed | Active again, usually after a payment | Status, period | Yes |
| Upgraded | The new plan, usually charged at once with a prorated amount | Plan, period | The new plan at once |
| Downgraded | The new plan from the next renewal, at most providers | The pending plan, if the provider reports it | The current plan until the period ends |
| Renewal refunded | Money went back; the subscription may stay active at the provider | `revoked_at`, `revoked_reason` | None from that moment, by default |
| Chargeback | The bank reversed the payment; the subscription may stay active at the provider | `revoked_at` | None from that moment |
| Revoked | The store took access away (Apple `REVOKE`, Google Play `SUBSCRIPTION_REVOKED`) | Status or `revoked_at` | None |
| Refund reversed | The store gave the money back to the app (Apple `REFUND_REVERSED`) | `revoked_at` cleared, if the refund set it | As before the refund |

Two rows need care.

**A refund does not cancel.** Stripe, Paddle and RevenueCat do not document that a refund ends the subscription; Stripe documents an optional setting that cancels on a dispute. The subscription can stay `active` at the provider while the money is gone. If the app keeps access because "the provider says active", a refund becomes a free month. Store the revocation on the subscription row, link it through the provider's own records (the charge's PaymentIntent and its invoice, the `transaction_id` of an adjustment, the purchase token of a voided purchase), and let it override the status.

**Past due keeps access for a bounded time.** During payment retry the provider usually moves the subscription to the next period even though that period is not paid. Its `period_end` is then a month away. Compute the grace from the end of the last period that was paid, not from the provider's current period end, or a failed card buys a month of access.

## Grace periods

| Provider | What the provider does | What the app sets |
| --- | --- | --- |
| Stripe Billing | Smart Retries: up to 8 retries within 2 weeks by default; then cancel, mark unpaid, leave past due or pause, as configured | The grace length: a number of days after the last paid period |
| App Store | Billing retry for up to 60 days. A billing grace period of 3, 16 or 28 days (6 at most for weekly plans) if enabled in App Store Connect; `gracePeriodExpiresDate` gives its end | Use the store's grace end. Without a store grace period, Apple says service can stop when the renewal fails |
| Google Play | Grace period, then account hold, both on by default and adjustable; hold is 60 days minus the grace period | Use the store's state: access in grace, none on hold |
| Paddle Billing | Retries up to seven times over 30 days by default, then cancels; `past_due` meanwhile | The grace length. Paddle's own guide keeps full access while past due |
| RevenueCat | Reports the store's grace with `BILLING_ISSUE` and `grace_period_expiration_at_ms` | The store's grace end |

Store the grace end as a date when the failure is recorded. Do not compute it later from "now".

## Cancel, end, pause, resume

- **Cancel at period end** keeps access until `paid_through`, with no grace added: there is no payment to wait for.
- **Cancel now** ends access at once. Whether money is returned is a separate decision: Stripe does not refund on cancel unless asked to prorate and refund.
- **A canceled subscription that is restored before its end** (Stripe `cancel_at_period_end` set back to false, Apple `AUTO_RENEW_ENABLED`, Google Play `SUBSCRIPTION_RESTARTED`) is the same subscription. Clear the flag; keep the row.
- **Resubscribing after the end** is a new subscription at Stripe and Paddle, whose canceled subscriptions cannot be reactivated, and a new purchase token at Google Play. Apple reports it as `SUBSCRIBED` with the subtype `RESUBSCRIBE`. Key each as its provider identifies it, and give each its own row.
- **Pause:** Stripe has two different things. `pause_collection` leaves the subscription `active` and keeps access while invoices are not collected; the `paused` status (a trial that ended without a payment method, or the pause endpoint) stops invoices, and Stripe sends events so that the app can remove access. Google Play's `SUBSCRIPTION_PAUSED` means the user should lose access. Paddle's `paused` creates no transactions.

## Upgrades and downgrades

- The new plan's access starts when the provider charges for it. Stripe applies a price change at once and, with `create_prorations` (the default), invoices the prorated amount on the next invoice; `always_invoice` invoices at once; a change can fail to collect and move the subscription to `past_due`. Apple: an upgrade takes effect at once with a prorated refund of the old plan; a downgrade at the next renewal. Google Play: a plan change is a new purchase with a `linkedPurchaseToken` that points at the old one.
- Keep one row per subscription and update its plan. On Google Play, end the old purchase token's entitlement when the new one arrives, so that one payment does not entitle two accounts.
- Credits that come with the plan follow the rules in [period-credits-and-trials.md](period-credits-and-trials.md): a plan change in the middle of a period does not grant a second full allowance.

## Family sharing and transfers

- App Store Family Sharing gives family members their own transactions, with `inAppOwnershipType` `FAMILY_SHARED`, and sends `REVOKE` when sharing stops. Each family member's app account gets its own row; the purchaser's refund revokes theirs too.
- RevenueCat's `TRANSFER` moves entitlements from one app user id to another, depending on the project's restore behavior. Move the row's `user_id` only from the provider's record, and log the move: it is how one purchase gets shared across accounts.
- Restoring purchases on a new device must not attach one store subscription to several app accounts. Decide with the user whether a restore moves the subscription or is refused while another account holds it.

## What to show the user

- The plan, the date access ends or renews, and whether it renews.
- During a failed payment: that access continues until a stated date, and a link to update the payment method (Stripe Customer Portal, the store's subscription page).
- After a cancel: the date access ends.

Read every value from the stored rows. The client never computes access, only displays it.

## Sources

- https://docs.stripe.com/billing/subscriptions/overview
- https://docs.stripe.com/billing/subscriptions/cancel
- https://docs.stripe.com/billing/subscriptions/pause-payment
- https://docs.stripe.com/billing/subscriptions/pause
- https://docs.stripe.com/billing/subscriptions/prorations
- https://docs.stripe.com/billing/subscriptions/change-price
- https://docs.stripe.com/billing/revenue-recovery/smart-retries
- https://developer.apple.com/documentation/appstoreservernotifications/notificationtype
- https://developer.apple.com/documentation/appstoreserverapi/inappownershiptype
- https://developer.apple.com/help/app-store-connect/manage-subscriptions/enable-billing-grace-period-for-auto-renewable-subscriptions
- https://developer.apple.com/help/app-store-connect/reference/in-app-purchases-and-subscriptions/auto-renewable-subscription-information
- https://developer.android.com/google/play/billing/lifecycle/subscriptions
- https://developer.android.com/google/play/billing/subscriptions
- https://developer.paddle.com/build/subscriptions/provision-access-webhooks
- https://developer.paddle.com/build/retain/configure-payment-recovery-dunning
- https://developer.paddle.com/api-reference/adjustments/overview
- https://www.revenuecat.com/docs/integrations/webhooks/event-types-and-fields
- https://www.revenuecat.com/docs/subscription-guidance/how-grace-periods-work
- https://www.revenuecat.com/docs/projects/restore-behavior

Checked 2026-11-16.
