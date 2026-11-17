# App Store auto-renewable subscriptions

What Apple's documentation said on the date at the end of this file, for granting access from auto-renewable subscriptions on the server. The general pattern is in [events-in-any-order.md](events-in-any-order.md) and [entitlements-and-lifecycle.md](entitlements-and-lifecycle.md). Recheck the linked pages before relying on a value.

## Verification, in short

App Store Server Notifications V2 arrive as `{ "signedPayload": "<JWS>" }`. Verify the JWS and its `x5c` chain up to an Apple root certificate the app holds, then `bundleId`, `environment` and, in production, `appAppleId`. The nested `signedTransactionInfo` and `signedRenewalInfo` are separate JWS: verify them too. Apple's App Store Server Library does all of it (`SignedDataVerifier`, with `verifyAndDecodeNotification`, `verifyAndDecodeTransaction`, `verifyAndDecodeRenewalInfo`). The `build-webhook-endpoint` skill has the details in its `references/provider-apple-app-store.md`. Notifications are signed by Apple, so a local probe cannot forge them: test the handler with the verifier stubbed, and the verification with Apple's test notification.

## Identity

- `originalTransactionId` identifies the subscription; Apple says to save it for that purpose. Key the subscription row on it.
- `transactionId` is new for each renewal; `webOrderLineItemId` identifies each subscription purchase event across devices, including renewals. Key a period's credits on one of them.
- `appAccountToken` is the UUID the app set at purchase to name its own account; it is absent when the app never set one, and can be set later with the Set App Account Token endpoint. Compare it with the account the app expects.

## Current state

Get All Subscription Statuses: `GET https://api.storekit.apple.com/inApps/v1/subscriptions/{transactionId}` (sandbox: `api.storekit-sandbox.apple.com`), with any of the subscription's transaction ids. Apple says to call it for up-to-date status. For each subscription group, `lastTransactions[]` holds `originalTransactionId`, `status`, `signedTransactionInfo` and `signedRenewalInfo`.

| `status` | Meaning | Access by default |
| --- | --- | --- |
| 1 | Active | Yes, until `expiresDate` |
| 2 | Expired | None |
| 3 | Billing retry period | None, unless the app chose its own grace |
| 4 | Billing grace period | Yes, until `gracePeriodExpiresDate` |
| 5 | Revoked: refunded, or revoked from Family Sharing | None |

The fields that decide access:

| Field | In | Use |
| --- | --- | --- |
| `expiresDate` | transaction | End of the paid period. Each renewal is a new transaction with a new `expiresDate` |
| `revocationDate`, `revocationReason`, `revocationType` | transaction | Refunded (`REFUND_FULL`, `REFUND_PRORATED` with `revocationPercentage`) or revoked (`FAMILY_REVOKE`, `ASSIGNMENT_REVOKE`) |
| `inAppOwnershipType` | transaction | `PURCHASED`, `FAMILY_SHARED` or `ASSIGNED` |
| `isUpgraded` | transaction | The old transaction after an upgrade: look for the higher plan's transaction |
| `offerType`, `offerDiscountType` | both | An introductory offer is `offerType` 1; `FREE_TRIAL` is one of the discount types |
| `autoRenewStatus` | renewal info | 0 off (canceled at period end), 1 on |
| `autoRenewProductId` | renewal info | A pending downgrade |
| `isInBillingRetryPeriod`, `gracePeriodExpiresDate` | renewal info | Retry and grace |
| `expirationIntent` | renewal info | 1 customer canceled, 2 billing error, 3 no consent to a price increase, 4 product not available, 5 other |

## Notifications

| `notificationType` (`subtype`) | Meaning | Handler |
| --- | --- | --- |
| `SUBSCRIBED` (`INITIAL_BUY`, `RESUBSCRIBE`) | Bought, resubscribed, or first access through Family Sharing or a group | Fetch status; grant |
| `DID_RENEW` (none, `BILLING_RECOVERY`) | Renewed, or renewed after a billing failure | Fetch; extend; credits for the new transaction |
| `DID_FAIL_TO_RENEW` (`GRACE_PERIOD`) | Billing retry; with `GRACE_PERIOD`, service continues through the grace period | Fetch; access until `gracePeriodExpiresDate` |
| `DID_FAIL_TO_RENEW` (none) | Not in a grace period; Apple says service can stop | Fetch; access ends |
| `GRACE_PERIOD_EXPIRED` | Grace ended without a renewal; retry continues up to 60 days | Access ends |
| `EXPIRED` (`VOLUNTARY`, `BILLING_RETRY`, `PRICE_INCREASE`, `PRODUCT_NOT_FOR_SALE`) | Ended | Access ends |
| `DID_CHANGE_RENEWAL_STATUS` (`AUTO_RENEW_DISABLED`, `AUTO_RENEW_ENABLED`) | Canceled at period end, or restored. Also sent after a refund request | Fetch; access until `expiresDate` |
| `DID_CHANGE_RENEWAL_PREF` (`UPGRADE`, `DOWNGRADE`, none) | Upgrade at once with a prorated refund; downgrade at the next renewal; none cancels a pending downgrade | Fetch; plan |
| `OFFER_REDEEMED` (none, `UPGRADE`, `DOWNGRADE`) | An offer for an active subscription | Fetch |
| `REFUND` | Apple refunded a transaction, including a renewal; Get All Subscription Statuses then shows status 5 | Revoke; credits back through the reversal code |
| `REFUND_REVERSED` | A refund was reversed; Apple says to reinstate what the refund revoked. The renewal date stays | Clear the revocation |
| `REFUND_DECLINED` | A refund request was declined | Nothing |
| `REVOKE` | Family Sharing or group access is no longer available | Access ends for that member |
| `RENEWAL_EXTENDED`, `RENEWAL_EXTENSION` | The renewal date was extended by the developer | Fetch |
| `PRICE_INCREASE` (`PENDING`, `ACCEPTED`) | The customer was told of a price increase | Nothing for access |
| `CONSUMPTION_REQUEST` | Apple asks for consumption data about a refund request | Not access |

Apple's `REFUND` entry does not say in so many words to end access; `REFUND_REVERSED` says to reinstate what a refund revoked, and the status API reports a refunded subscription as revoked. End access on `REFUND` by default.

## Order and duplicates

- Deduplicate on `notificationUUID`.
- `signedDate` is when the App Store signed the data and stays the same on a retry. When several notifications concern one transaction, Apple says to use the one with the most recent `signedDate`: a newer-wins value. Fetching the status is simpler and always current.
- Production retries five times, at 1, 12, 24, 48 and 72 hours after the previous attempt; the sandbox sends once. Answer 200 to 206.
- After an outage: Get Notification History (180 days in production, 30 in the sandbox), Get Transaction History and Get All Subscription Statuses. Get Refund History (`GET /inApps/v2/refund/lookup/{transactionId}`) recovers missed refunds.

## Grace period and retry

The billing grace period is set per app in App Store Connect, for all its subscriptions: 3, 16 or 28 days, with weekly subscriptions capped at 6. It can apply to all renewals or only paid-to-paid renewals, and changes take up to 24 hours and apply to upcoming renewals. Billing retry continues for up to 60 days. Recovery inside the grace period keeps the billing date; recovery after it sets a new billing date from the recovery.

## Family Sharing

Each family member gets their own transactions with `inAppOwnershipType` `FAMILY_SHARED`, `SUBSCRIBED` when access starts and `REVOKE` when it ends; Apple expects access to stop at once when sharing stops. Up to five family members share. Family Sharing cannot be turned off once on.

## Trials

One introductory offer per subscription group per person; existing subscribers are not eligible when they change plans. The store decides eligibility; Apple documents no server API for it.

## Bugs that ship

- Keying the subscription on `transactionId`, so every renewal looks like a new subscription, or keying a period's credits on `originalTransactionId`, so no renewal grants.
- Trusting the client's receipt or StoreKit result for access instead of the server's verified state.
- Ending access on `DID_FAIL_TO_RENEW` with the `GRACE_PERIOD` subtype, or keeping it after `GRACE_PERIOD_EXPIRED`.
- Ending access on `AUTO_RENEW_DISABLED`, which is a cancel at period end.
- Ignoring `REFUND` and `REVOKE` for subscriptions, or ignoring `REFUND_REVERSED`.
- A production verifier that refuses sandbox notifications sent to the same URL, so TestFlight purchases never grant; or a sandbox verifier in production.

## Sources

- https://developer.apple.com/documentation/appstoreservernotifications/notificationtype
- https://developer.apple.com/documentation/appstoreservernotifications/subtype
- https://developer.apple.com/documentation/appstoreservernotifications/data
- https://developer.apple.com/documentation/appstoreservernotifications/notificationuuid
- https://developer.apple.com/documentation/appstoreservernotifications/signeddate
- https://developer.apple.com/documentation/appstoreservernotifications/responding-to-app-store-server-notifications
- https://developer.apple.com/documentation/appstoreserverapi/get-all-subscription-statuses
- https://developer.apple.com/documentation/appstoreserverapi/status
- https://developer.apple.com/documentation/appstoreserverapi/jwstransactiondecodedpayload
- https://developer.apple.com/documentation/appstoreserverapi/jwsrenewalinfodecodedpayload
- https://developer.apple.com/documentation/appstoreserverapi/originaltransactionid
- https://developer.apple.com/documentation/appstoreserverapi/weborderlineitemid
- https://developer.apple.com/documentation/appstoreserverapi/appaccounttoken
- https://developer.apple.com/documentation/appstoreserverapi/expiresdate
- https://developer.apple.com/documentation/appstoreserverapi/revocationtype
- https://developer.apple.com/documentation/appstoreserverapi/inappownershiptype
- https://developer.apple.com/documentation/appstoreserverapi/expirationintent
- https://developer.apple.com/documentation/appstoreserverapi/isupgraded
- https://developer.apple.com/documentation/appstoreserverapi/offertype
- https://developer.apple.com/documentation/appstoreserverapi/offerdiscounttype
- https://developer.apple.com/documentation/appstoreserverapi/get-notification-history
- https://developer.apple.com/documentation/appstoreserverapi/get-refund-history
- https://developer.apple.com/documentation/storekit/reducing-involuntary-subscriber-churn
- https://developer.apple.com/documentation/storekit/supporting-family-sharing-in-your-app
- https://developer.apple.com/help/app-store-connect/manage-subscriptions/enable-billing-grace-period-for-auto-renewable-subscriptions
- https://developer.apple.com/help/app-store-connect/manage-subscriptions/set-up-introductory-offers-for-auto-renewable-subscriptions
- https://developer.apple.com/help/app-store-connect/reference/in-app-purchases-and-subscriptions/auto-renewable-subscription-information
- https://developer.apple.com/help/app-store-connect/configure-in-app-purchase-settings/turn-on-family-sharing-for-in-app-purchases

Checked 2026-11-16.
