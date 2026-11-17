# Google Play real-time developer notifications

What the Google Play and Cloud Pub/Sub documentation said on the date at the end of this file, for real-time developer notifications (RTDN) delivered to the app's server by a Pub/Sub push subscription. The general pattern is in [verify-signatures.md](verify-signatures.md) and [process-events-once.md](process-events-once.md). Recheck the linked pages before relying on a number.

## Authentication

A push subscription with authentication enabled sends `Authorization: Bearer <JWT>`, an OpenID Connect token signed by Google for the subscription's service account. Verify, on every request:

- the signature against Google's public keys, and the expiry,
- `aud` equals the audience configured on the subscription (when none is set, the gcloud reference says it defaults to the push endpoint URL),
- `iss` is `accounts.google.com` or `https://accounts.google.com`,
- `email` is the subscription's service account and `email_verified` is true.

```js
import { OAuth2Client } from 'google-auth-library';

const client = new OAuth2Client();

// config: { audience, serviceAccountEmail } from the push subscription, required at start-up.
export async function verifyPushToken(authorizationHeader, config) {
  const match = /^Bearer ([\w.-]+)$/.exec(String(authorizationHeader ?? ''));
  if (!match) return false;
  try {
    // Checks the signature with Google's keys, expiry, issuer and audience.
    const ticket = await client.verifyIdToken({ idToken: match[1], audience: config.audience });
    const claims = ticket.getPayload();
    return claims?.email === config.serviceAccountEmail && claims.email_verified === true;
  } catch {
    return false;
  }
}
```

Python: `google.oauth2.id_token.verify_oauth2_token(token, google.auth.transport.requests.Request(), audience=...)`, then the same `email` and `email_verified` checks. The libraries leave the email checks to the caller.

Pub/Sub's code samples also compare a `token` query parameter with a configured value. The documentation does not say whether that alone is enough. It is a shared value in a URL that ends up in logs: use it, if at all, in addition to the token.

The notification itself carries nothing that proves the purchase. Even after the token check, read the purchase from the Play Developer API.

## Configuration

- Pub/Sub topic: grant `google-play-developer-notifications@system.gserviceaccount.com` the Pub/Sub Publisher role.
- Play Console, Monetize, Monetization setup: enable real-time notifications per app, enter `projects/{project_id}/topics/{topic_name}`, and choose whether one-time product events are included. Without that option only subscription and voided purchase notifications are sent.
- Push subscription: HTTPS endpoint with a valid certificate, authentication with a service account in the same project. The Pub/Sub service agent needs the Service Account Token Creator role on it.
- The Play Developer API needs a service account with the "View financial data" permission.

## Body

The push body is `{ "message": { "data": "<base64>", "messageId", "publishTime", "attributes" }, "subscription" }`. The decoded `data` is a DeveloperNotification: `version`, `packageName`, `eventTimeMillis` (a string in the examples), and one of `subscriptionNotification`, `oneTimeProductNotification`, `voidedPurchaseNotification`, `pendingRefundReviewNotification`, `testNotification`. Parse it as JSON after the token check, and refuse a `packageName` that is not the app's. No raw body is needed; see [webhook-stacks.md](webhook-stacks.md) for the route.

## Timestamp and replay

The token has an expiry, and Pub/Sub says tokens on push requests may be up to an hour old. Google Play documents no freshness rule for notifications. The stored `messageId` and the purchase token keys below are the replay protection.

## Delivery

- Pub/Sub acknowledges a push message on 102, 200, 201, 202 or 204. Anything else is a negative acknowledgement.
- Delivery is at least once. Push subscriptions do not support exactly-once delivery. Order holds only with ordering keys, and the documentation does not say whether Google Play sets one: assume no order.
- The acknowledgement deadline defaults to 10 seconds (up to 600). Push backoff ranges from 100 milliseconds to 60 seconds. The retry policy is immediate by default, or exponential backoff when configured.
- Unacknowledged messages are kept 7 days by default (10 minutes to 31 days). A dead-letter topic after 5 to 100 attempts is optional.

## Event id

- `message.messageId`: Google Play says to check its uniqueness so that duplicates are not processed. A redelivered message keeps its id, but Pub/Sub says publish-side duplicates arrive under new ids.
- So the business key carries the weight. Google says `purchaseToken` is globally unique and safe as a primary key, and that `orderId` is not, because some purchases, such as promo code purchases, have none. For a renewal, key on the purchase token plus the order id of that renewal (`lineItems[].latestSuccessfulOrderId` in subscriptionsv2), since each renewal gets a new order id.

## Events that move money

| Notification | Meaning | What the handler does |
| --- | --- | --- |
| `oneTimeProductNotification` 1 `ONE_TIME_PRODUCT_PURCHASED` | A one-time product was bought | Read it with `purchases.productsv2.getproductpurchasev2`; grant only when the state is purchased, then consume or acknowledge |
| `oneTimeProductNotification` 2 `ONE_TIME_PRODUCT_CANCELED` | Canceled or revoked | Read the purchase; a pending purchase that was canceled granted nothing |
| `subscriptionNotification` 4 `PURCHASED`, 2 `RENEWED`, 1 `RECOVERED`, 7 `RESTARTED` | Started, renewed, recovered, restarted | Read with `purchases.subscriptionsv2.get`; grant when `subscriptionState` is `SUBSCRIPTION_STATE_ACTIVE` |
| 6 `IN_GRACE_PERIOD`, 5 `ON_HOLD`, 3 `CANCELED`, 13 `EXPIRED`, 10 `PAUSED` | Payment trouble, cancelled (access to period end), ended | Update from the API state |
| 12 `SUBSCRIPTION_REVOKED` | Revoked before its expiry time | End access now. To the reversal code if the app credited a balance |
| `voidedPurchaseNotification` | A purchase was refunded, charged back or otherwise voided. `purchaseToken`, `orderId`, `productType`, `refundType` 1 full or 2 quantity-based partial | To the reversal code |
| `pendingRefundReviewNotification` | A chargeback is under review (`refundReason` 7). Google says to answer through `orders.reviewrefund` within 24 hours | Hold payouts for the account and alert a person |
| `testNotification` | Sent from the Play Console | Answer 2xx, change nothing |

Other subscription types exist (9 `DEFERRED`, 11 `PAUSE_SCHEDULE_CHANGED`, 17 to 22, 8 deprecated): read the current state from the API for any of them. The mapping of voided purchases to the reversal code is in the `handle-refunds-and-reversals` skill.

## Payload or API

Google says the notification only signals that the state changed and that the app must call the Play Developer API for the complete status. `purchases.subscriptionsv2.get` is the source of truth for subscriptions; `purchases.subscriptions.get` is deprecated. Then:

- Acknowledge or consume within three days of the purchase becoming purchased, or Google refunds it and revokes it. Consuming also acknowledges. Do not grant a pending purchase.
- When `linkedPurchaseToken` is set, Google says to revoke the entitlement of the linked token so that one purchase does not entitle two users. Upgrades, downgrades, resubscribes and prepaid top-ups set it.
- Compare `obfuscatedExternalAccountId` with the account the app set at purchase, when it sets one.
- The Voided Purchases API lists voids of the past 30 days. Pass `type=1` to include subscriptions and `includeQuantityBasedPartialRefund=true` for partial refunds. Run it on a schedule as reconciliation.

## Test locally

- The Play Console "Send Test Message" button sends a `testNotification` through the topic; a success response acknowledges it.
- License testers buy with test cards, including one that approves and then charges back. Test subscriptions renew every few minutes. Unacknowledged tester purchases are refunded after 3 minutes.
- The token is signed by Google, so a local probe cannot forge it. Test the handler with the token check stubbed, and the check itself against the real push subscription.

## Bugs that ship

- A push endpoint without authentication, or a token check that ignores `aud` or `email`.
- Granting from the notification without calling the API, or granting a pending purchase.
- Never acknowledging, so Google refunds every purchase after three days while the user keeps the credits.
- Keying on `orderId`, which some purchases lack, or on `messageId` alone.
- Ignoring `linkedPurchaseToken`, so an upgrade leaves two active entitlements.
- Subscribing only to subscription events and never seeing voided one-time purchases, or not checking `packageName`.
- Treating `SUBSCRIPTION_CANCELED` as the end of access instead of the end of renewal.

## Sources

- https://developer.android.com/google/play/billing/rtdn-reference
- https://developer.android.com/google/play/billing/getting-ready
- https://developer.android.com/google/play/billing/lifecycle
- https://developer.android.com/google/play/billing/lifecycle/subscriptions
- https://developer.android.com/google/play/billing/lifecycle/one-time
- https://developer.android.com/google/play/billing/integrate
- https://developer.android.com/google/play/billing/security
- https://developer.android.com/google/play/billing/test
- https://developers.google.com/android-publisher/voided-purchases
- https://developers.google.com/android-publisher/api-ref/rest/v3/purchases.subscriptionsv2
- https://cloud.google.com/pubsub/docs/authenticate-push-subscriptions
- https://cloud.google.com/pubsub/docs/push
- https://cloud.google.com/pubsub/docs/create-push-subscription
- https://cloud.google.com/pubsub/docs/subscription-properties
- https://cloud.google.com/pubsub/docs/subscribe-best-practices
- https://cloud.google.com/pubsub/docs/exactly-once-delivery
- https://cloud.google.com/sdk/gcloud/reference/pubsub/subscriptions/create

Checked 2026-11-15.
