# Google Play subscriptions

What the Google Play documentation said on the date at the end of this file, for granting access from Google Play subscriptions on the server. The general pattern is in [events-in-any-order.md](events-in-any-order.md) and [entitlements-and-lifecycle.md](entitlements-and-lifecycle.md). Recheck the linked pages before relying on a value.

## Verification, in short

Real-time developer notifications (RTDN) arrive through a Cloud Pub/Sub push subscription with `Authorization: Bearer <OIDC token>`. Verify the token's signature and expiry with Google's keys, its `aud`, its `iss`, and that `email` is the subscription's service account with `email_verified` true; then check `packageName`. The `build-webhook-endpoint` skill has the code in its `references/provider-google-play.md`. The notification proves nothing about the purchase: Google says it only signals that the state changed, and that the app must call the Play Developer API. A local probe cannot forge the token: test the handler with the check stubbed.

## Identity

- The purchase token identifies the subscription purchase. Google says it is globally unique and safe as a primary key. A plan change, a resubscribe before the old one lapsed, and a prepaid top-up produce a new token with `linkedPurchaseToken` pointing at the old one.
- Each renewal gets a new order id: `lineItems[].latestSuccessfulOrderId` (`latestOrderId` is deprecated). Key a period's credits on the token plus that order id. Google warns that not every purchase has an order id (purchases made with promo codes have none) and that `orderId` is no primary key: for a first period without one, key on the token alone.
- `externalAccountIdentifiers.obfuscatedExternalAccountId` is the account id the app set in the billing flow. Compare it with the account the app expects.

## Current state

`purchases.subscriptionsv2.get` is the source of truth; `purchases.subscriptions.get` is deprecated. Call it when the notification arrives, not at the expiry time.

| `subscriptionState` | Access by default |
| --- | --- |
| `SUBSCRIPTION_STATE_PENDING` | None. Google says not to grant a pending purchase |
| `SUBSCRIPTION_STATE_ACTIVE` | Yes, until `lineItems[].expiryTime` |
| `SUBSCRIPTION_STATE_IN_GRACE_PERIOD` | Yes. Google extends `expiryTime` until the grace period ends |
| `SUBSCRIPTION_STATE_ON_HOLD` | None. `expiryTime` is in the past |
| `SUBSCRIPTION_STATE_PAUSED` | None |
| `SUBSCRIPTION_STATE_CANCELED` | Yes, until `expiryTime`; none once it is past |
| `SUBSCRIPTION_STATE_EXPIRED` | None |
| `SUBSCRIPTION_STATE_PENDING_PURCHASE_CANCELED` | None for this token; read the linked token for the existing subscription |

Other fields: `acknowledgementState`, `testPurchase` (present only for test purchases), `canceledStateContext` (who canceled), `lineItems[].autoRenewingPlan.autoRenewEnabled`, `lineItems[].offerPhase` (`freeTrial`, `introductoryPrice`, `basePrice`, `prorationPeriod`).

## Notifications

`subscriptionNotification.notificationType`:

| Type | Meaning | Handler |
| --- | --- | --- |
| 4 `SUBSCRIPTION_PURCHASED` | New purchase | Get; grant when active; acknowledge |
| 2 `SUBSCRIPTION_RENEWED` | Renewed | Get; extend; credits for the new order id |
| 1 `SUBSCRIPTION_RECOVERED` | Recovered from account hold, or resumed from a pause | Get; grant |
| 7 `SUBSCRIPTION_RESTARTED` | Restored before it expired | Get; clear the cancel |
| 6 `SUBSCRIPTION_IN_GRACE_PERIOD` | Grace period started | Get; keep access |
| 5 `SUBSCRIPTION_ON_HOLD` | Account hold started | Get; access ends |
| 3 `SUBSCRIPTION_CANCELED` | Canceled; access stays until `expiryTime` | Get; do not end access early, which Google calls a policy violation |
| 13 `SUBSCRIPTION_EXPIRED` | Expired | Access ends |
| 12 `SUBSCRIPTION_REVOKED` | Revoked before its expiry, by the developer or by a chargeback; state becomes expired | Access ends at once |
| 10 `SUBSCRIPTION_PAUSED` | Pause took effect | Access ends |
| 11 `SUBSCRIPTION_PAUSE_SCHEDULE_CHANGED` | Pause scheduled; still active | Get |
| 9 `SUBSCRIPTION_DEFERRED` | Recurrence time extended | Get |
| 20 `SUBSCRIPTION_PENDING_PURCHASE_CANCELED` | A pending transaction was canceled | Get |
| 17, 18, 19, 21, 22 | Items changed, installment cancel scheduled, price change updated, plan transition updated, price step-up consent | Get |

`voidedPurchaseNotification` (with `purchaseToken`, `orderId`, `productType` 1 for subscriptions, `refundType` 1 full or 2 partial) means a refund or chargeback: record the revocation and send the credits to the reversal code. `pendingRefundReviewNotification` asks for an answer within 24 hours.

When a hold ends without payment, Google sends `SUBSCRIPTION_CANCELED` and then `SUBSCRIPTION_EXPIRED`.

## Order and duplicates

- Check `messageId` for uniqueness so that duplicates are not processed. Pub/Sub can also publish a duplicate under a new id, so the business keys (token, order id) carry the weight.
- Google documents no ordering: fetch the state for every notification.
- For reconciliation, read each stored token with `subscriptionsv2.get` (tokens stay valid until 60 days after expiry), and list voided purchases of the past 30 days with the Voided Purchases API (`type=1` includes subscriptions). Only revoked orders appear there.

## Acknowledge

Acknowledge a new subscription purchase within three days, or the user is refunded and the purchase revoked. Upgrades, downgrades and resubscribes are new purchases and need it too; renewals do not. The endpoint is `purchases.subscriptions.acknowledge`, the one method left on the old resource. A plan change is blocked while the existing purchase is not acknowledged. Google says to acknowledge right after granting, from the server: acknowledge after the grant is committed, and retry until it succeeds. A purchase that fails the app's checks is revoked with `subscriptionsv2.revoke` and `fullRefund`, not left to the three-day refund.

## Grace period, hold, pause

Grace period and account hold are on by default for auto-renewing base plans and can be changed or turned off in the Play Console. Account hold lasts 60 days minus the grace period. Before hold, Google retries for up to 48 hours while the user keeps access. Recovering in grace keeps the renewal date; recovering from hold moves it to the recovery date. Pause is on by default; during it the user loses access.

## Plan changes

A plan change is a new purchase. Google says to invalidate the token in `linkedPurchaseToken` and revoke the entitlement it granted, so that one purchase does not entitle two users. Replacement modes decide when the new price applies: `WITH_TIME_PRORATION` (the default), `CHARGE_PRORATED_PRICE`, `CHARGE_FULL_PRICE`, `WITHOUT_PRORATION`, `DEFERRED`.

## Trials

Google Play shows the user only the offers they are eligible for, and a base plan can allow one free trial per app. The server reads the trial from `offerPhase.freeTrial` and does not grant one of its own.

## Bugs that ship

- Granting from the notification without calling the API, or granting a pending purchase.
- Treating `SUBSCRIPTION_CANCELED` as the end of access.
- Keeping access on hold, or ending it in grace.
- Ignoring `linkedPurchaseToken`, so an upgrade leaves two entitled tokens, possibly on two accounts.
- Never acknowledging, so every purchase is refunded after three days while access stays.
- Keying the subscription on `orderId`, which changes at every renewal.

## Sources

- https://developer.android.com/google/play/billing/rtdn-reference
- https://developer.android.com/google/play/billing/lifecycle/subscriptions
- https://developer.android.com/google/play/billing/subscriptions
- https://developer.android.com/google/play/billing/security
- https://developer.android.com/google/play/billing/integrate
- https://developer.android.com/google/play/billing/lifecycle
- https://developer.android.com/google/play/billing/play-developer-apis-deprecations
- https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.subscriptionsv2
- https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.subscriptionsv2/revoke
- https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.subscriptions/acknowledge
- https://developers.google.com/android-publisher/voided-purchases

Checked 2026-11-16.
