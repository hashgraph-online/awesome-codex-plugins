# Events in any order

Subscription events arrive late, twice, and out of order. Stripe, Paddle and Google Play say so outright; Apple says to prefer the notification with the most recent `signedDate`; RevenueCat says to call its API after any webhook. This file covers how a handler ends in the right state whatever the order: what to store, how to make a stale state lose, and the reconciliation job that repairs what no event repaired.

## The rule

The stored state of a subscription is the provider's latest object, never the effect of the last event to arrive. Two ways get there:

| Way | How | Use it when |
| --- | --- | --- |
| Fetch | Treat the event as "something changed". Fetch the subscription from the provider's API and store what it returns. | The provider has an API for the current state: Stripe (retrieve the subscription), App Store (Get All Subscription Statuses), Google Play (`purchases.subscriptionsv2.get`, which Google calls the source of truth and says to call after every notification), RevenueCat (its customer endpoints). |
| Newer wins | Store the provider's own ordering value with the state, and write an event's state only when its value is newer. | The provider documents such a value: Paddle's `occurred_at`, Apple's `signedDate`. Stripe says not to use `created` to order events, because distinct events can share a second. |

Fetching is the default. It costs one request per event and is always current. It is also the only safe choice for Stripe, whose snapshot events carry no usable order.

## Fetch, then store, with the fetch time as the version

Two deliveries can be in flight at once: each fetches, and the slower one may write last with the older answer. Record when each fetch started and let only a later fetch overwrite.

```js
// Node with the pg driver. withTransaction is the project's transaction helper.
// fetchSubscription calls the provider's API and returns its object, or null when it does not exist.
export async function refreshSubscription(pool, provider, providerId, fetchSubscription, toRow) {
  const fetchedAtMs = Date.now(); // taken before the request, so a slower, older answer loses
  const object = await fetchSubscription(providerId); // outside any transaction
  if (!object) return null;
  const row = toRow(object); // { userId, plan, status, periodStart, paidThrough, graceUntil, cancelAtPeriodEnd }
  return withTransaction(pool, async (tx) => {
    const written = await tx.query(
      `INSERT INTO subscriptions (provider, provider_id, user_id, plan, status, period_start, paid_through,
                                  grace_until, cancel_at_period_end, provider_version)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
       ON CONFLICT (provider, provider_id) DO UPDATE
          SET plan = EXCLUDED.plan, status = EXCLUDED.status, period_start = EXCLUDED.period_start,
              paid_through = EXCLUDED.paid_through, grace_until = EXCLUDED.grace_until,
              cancel_at_period_end = EXCLUDED.cancel_at_period_end,
              provider_version = EXCLUDED.provider_version, updated_at = now()
        WHERE subscriptions.provider_version <= EXCLUDED.provider_version`,
      [provider, providerId, row.userId, row.plan, row.status, row.periodStart, row.paidThrough,
       row.graceUntil, row.cancelAtPeriodEnd, fetchedAtMs],
    );
    return written.rowCount === 1 ? row : null; // null: a newer state was already stored
  });
}
```

Notes:

- **`user_id` is written once.** The update clause leaves it out. The first writer resolves the user from the app's own checkout record; nothing in a later event can move the subscription to another account.
- **`revoked_at` is not in the update.** A refund or a chargeback recorded by the app stays, whatever the provider's status says.
- **For newer-wins providers,** pass the provider's value instead of `fetchedAtMs`: Paddle's `occurred_at` in milliseconds, Apple's `signedDate`. Equal values cannot be ordered; fetch when two events share one.
- **No API call inside the transaction.** The fetch runs first. If it fails, the handler answers 5xx before storing the event id, and the provider delivers the event again.

## The webhook, step by step

1. Verify the signature or token, as the `build-webhook-endpoint` skill builds it. A refused event changes nothing.
2. Find the subscription id the event names: the subscription object's id, an invoice's `parent.subscription_details.subscription` (Stripe), the `originalTransactionId` in the verified `signedTransactionInfo` (Apple), the purchase token (Google Play), `data.id` or `data.subscription_id` (Paddle), `app_user_id` (RevenueCat).
3. Fetch the current object (or take the event's state with its ordering value).
4. In one transaction: insert the event id under its unique key; when it was there, stop. Store the state with the version guard. Grant the period's credits under their ledger key. Commit.
5. Answer 2xx after the commit; 5xx when anything failed, so the provider retries.

The event id makes a repeat harmless for effects that are not idempotent by themselves, such as an email. The state write and the credit grant are idempotent on their own keys, so they stay right even when the same fact arrives under a second event id.

## The cases that break naive handlers

| Arrives | Naive result | With the rule above |
| --- | --- | --- |
| An old "updated" event after the cancellation | Access back | The fetch returns `canceled`; or the older version loses |
| "Invoice paid" before "subscription created" | The paid invoice is dropped for an unknown subscription, or the late "created" snapshot (`incomplete`) removes access | The invoice event fetches the subscription and stores it; the late snapshot loses |
| The same payment under two event types (`invoice.paid` and `invoice.payment_succeeded`) | Two grants | One grant: the credit key is the subscription and period |
| A retry hours later | A second grant, or access restored after a cancel | The event id is stored; the state comes from the fetch |
| Two events at the same moment | The slower write wins with an older state | The fetch-time guard keeps the newer one |
| A failed renewal followed by recovery, delivered in reverse | Access removed after the payment | Each event fetches, and the fetch returns `active` whichever event comes last |

## Linking events to the user

Resolve the account from the app's own record written before the checkout, never from an email, a customer name or a user id inside the event:

| Provider | Carry the app's checkout id or account in | Read it from |
| --- | --- | --- |
| Stripe | `client_reference_id` and `subscription_data.metadata` on the Checkout Session | The subscription's `metadata`; an invoice's `parent.subscription_details.metadata` |
| App Store | `appAccountToken` (a UUID) set at purchase | The verified transaction and renewal info |
| Google Play | `obfuscatedAccountId` set in the billing flow | `externalAccountIdentifiers.obfuscatedExternalAccountId` from `subscriptionsv2.get` |
| Paddle | `custom_data` on the checkout | `data.custom_data` |
| RevenueCat | The app user id the app logs in with | `app_user_id`, `original_app_user_id`, `aliases` |

When the value does not match a checkout the app created, store the event as unmatched and alert. Do not grant.

## Reconciliation

Webhooks get lost: an outage longer than the provider's retry window, a deploy that answered 5xx for a day, a secret rotated on one side only. A scheduled job compares the stored rows with the provider and repairs them through the same function the webhook uses.

```js
// Runs on a schedule (hourly by default) and on demand from an admin action.
// listSubscriptions pages through the provider's list; refreshFromObject stores one object with the
// same version guard as refreshSubscription, using the time the page was fetched.
export async function reconcileSubscriptions({ listSubscriptions, refreshFromObject, alert }) {
  let checked = 0;
  let changed = 0;
  for await (const { object, fetchedAtMs } of listSubscriptions()) {
    checked += 1;
    const stored = await refreshFromObject(object, fetchedAtMs);
    if (stored?.changed) changed += 1;
  }
  if (changed > 0) await alert(`subscription reconciliation repaired ${changed} of ${checked} subscriptions`);
  return { checked, changed };
}
```

- **Stripe:** `GET /v1/subscriptions?status=all`, paged with `starting_after` while `has_more` is true. Without `status` the list leaves canceled subscriptions out, which hides exactly the cancellations a lost webhook did not deliver.
- **App Store:** Get All Subscription Statuses per stored `originalTransactionId`; Get Notification History for missed notifications (180 days in production).
- **Google Play:** `subscriptionsv2.get` per stored purchase token; the Voided Purchases API (`type=1` for subscriptions) for refunds and chargebacks of the past 30 days.
- **Paddle:** `GET /subscriptions`, paged with `after` while `meta.pagination.has_more` is true.
- **RevenueCat:** the customer endpoint per stored app user id.

Also check the other direction: every row the app thinks gives access is looked up at the provider. A repaired row is a finding: alert a person, because each one is a webhook that did not arrive.

## Sources

- https://docs.stripe.com/webhooks
- https://docs.stripe.com/billing/subscriptions/webhooks
- https://docs.stripe.com/api/subscriptions/list
- https://docs.stripe.com/api/invoices/object
- https://developer.apple.com/documentation/appstoreservernotifications/signeddate
- https://developer.apple.com/documentation/appstoreserverapi/get-all-subscription-statuses
- https://developer.apple.com/documentation/appstoreserverapi/get-notification-history
- https://developer.apple.com/documentation/appstoreserverapi/appaccounttoken
- https://developer.android.com/google/play/billing/rtdn-reference
- https://developer.android.com/google/play/billing/lifecycle/subscriptions
- https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.subscriptionsv2
- https://developers.google.com/android-publisher/voided-purchases
- https://developer.paddle.com/webhooks/respond-to-webhooks
- https://developer.paddle.com/api-reference/subscriptions/list-subscriptions
- https://www.revenuecat.com/docs/integrations/webhooks

Checked 2026-11-16.
