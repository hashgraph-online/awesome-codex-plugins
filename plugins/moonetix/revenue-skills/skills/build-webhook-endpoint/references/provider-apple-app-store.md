# App Store Server Notifications V2

What Apple's documentation and its App Store Server Library said on the date at the end of this file. The general pattern is in [verify-signatures.md](verify-signatures.md) and [process-events-once.md](process-events-once.md). Recheck the linked pages before relying on a number.

## Authentication

- The body is `{ "signedPayload": "<JWS>" }`. The JWS is three Base64URL parts. Its header carries `alg` and an `x5c` chain: the signing certificate, an Apple intermediate with the extension `1.2.840.113635.100.6.2.1`, and an Apple root. Inside the payload, `data.signedTransactionInfo` and `data.signedRenewalInfo` are JWS of the same form, signed separately.
- Decoding is not verifying. Verify the signature, the chain up to an Apple root certificate the app holds (Apple Root CA - G3 from apple.com/certificateauthority), and then that `bundleId`, `environment` and, in production, `appAppleId` are the app's own.
- There is no shared secret. Apple also offers an optional address filter, `17.0.0.0/8`, as a second layer.

Apple's App Store Server Library (Node, Python, Java, Swift) does this. Node:

```js
import { readFileSync } from 'node:fs';
import { Environment, SignedDataVerifier } from '@apple/app-store-server-library';

const verifier = new SignedDataVerifier(
  [readFileSync('certs/AppleRootCA-G3.cer')], // downloaded from Apple PKI, shipped with the app
  true, // online checks: OCSP revocation and expiry against the current date
  Environment.PRODUCTION,
  'com.example.app', // bundle id
  1234567890, // appAppleId, required for Production
);

export async function verifyAppleNotification(jsonBody) {
  try {
    const notification = await verifier.verifyAndDecodeNotification(jsonBody.signedPayload);
    // The nested transaction is still a JWS string. Verify it as well.
    const transaction = notification.data?.signedTransactionInfo
      ? await verifier.verifyAndDecodeTransaction(notification.data.signedTransactionInfo)
      : null;
    return { notification, transaction };
  } catch {
    return null; // VerificationException: answer 400
  }
}
```

What the library checks, read from its source: an `x5c` of exactly three certificates; the intermediate signed by one of the given roots and the leaf by the intermediate; both Apple extension OIDs; validity dates; `ES256`. `verifyAndDecodeNotification` refuses another bundle id or environment, and another `appAppleId` in production. It does not verify the nested `signedTransactionInfo` and `signedRenewalInfo`; `verifyAndDecodeTransaction` and `verifyAndDecodeRenewalInfo` do. A verifier created for the `Xcode` or `LocalTesting` environment skips signature checks: never configure one in a deployed service.

Run one verifier per environment, or route sandbox notifications to their own URL. When no sandbox URL is set in App Store Connect, sandbox notifications go to the production URL, and a production verifier refuses them.

## Raw body

Not needed. `signedPayload` is signed on its own, so the JSON wrapper can be parsed normally. See [webhook-stacks.md](webhook-stacks.md) for the rest of the route.

## Timestamp and replay

`signedDate` is when the App Store signed the data and stays the same on a retry. Apple documents no freshness window, and a retry can come 72 hours after the attempt before it, so accept old notifications whatever their age. The stored `notificationUUID` is the replay protection. When several notifications concern one transaction, Apple says to use the one with the most recent `signedDate`.

## Delivery

- Success: HTTP 200 to 206. Apple retries on 40x and 50x.
- Production retries five times, at 1, 12, 24, 48 and 72 hours after the previous attempt. The sandbox sends once and does not retry.
- Order is not documented as guaranteed.
- A `TIMED_OUT` send attempt means the server took too long. Apple's advice is not to process messages inline. It states no timeout in seconds.
- Missed notifications: Get Notification History (`POST /inApps/v1/notifications/history`) covers 180 days in production and 30 in the sandbox.

## Event id

Deduplicate on `notificationUUID`. Apple says to use it to identify and ignore duplicates; that a retry keeps it is implied, not stated. Key credits on `transactionId`. `originalTransactionId` is shared by a subscription's renewals and is the wrong key for a credit.

## Events that move money

`notificationType`, sometimes with a `subtype`. `price` is in milliunits (price times 1000) with `currency`. Apple says not to use `price` and `currency` for revenue reconciliation. `appAccountToken` is the UUID the app set at purchase to name its own user; it is absent when the app did not set one.

| Type and subtype | Meaning | What the handler does |
| --- | --- | --- |
| `ONE_TIME_CHARGE` | A consumable, non-consumable or non-renewing subscription was bought | Grant, keyed on `transactionId`. Available in production since 2025-05-27 |
| `SUBSCRIBED` (`INITIAL_BUY`, `RESUBSCRIBE`) | A subscription started | Grant the period |
| `DID_RENEW` (`BILLING_RECOVERY`) | Renewed, or recovered after a billing failure | Extend the period |
| `DID_FAIL_TO_RENEW` (`GRACE_PERIOD`) | Renewal failed; with `GRACE_PERIOD` service continues | The app's grace rule |
| `EXPIRED` (`VOLUNTARY`, `BILLING_RETRY`, `PRICE_INCREASE`, `PRODUCT_NOT_FOR_SALE`), `GRACE_PERIOD_EXPIRED` | Access ended | End access |
| `REFUND` | Apple refunded a transaction. `revocationDate`, `revocationReason`, `revocationType` (`REFUND_FULL`, `REFUND_PRORATED`, `FAMILY_REVOKE`, `ASSIGNMENT_REVOKE`), `revocationPercentage` in milliunits | To the reversal code |
| `REFUND_REVERSED` | A refund was reversed | Reinstate what the refund took, as Apple says |
| `REFUND_DECLINED` | A refund request was declined | Nothing to undo |
| `REVOKE` | Access revoked, for example through Family Sharing | Revoke the entitlement. Not a refund to this user |
| `CONSUMPTION_REQUEST` | Apple asks for consumption data about a refund request | Not money. Answer through the API if the app takes part |

The list is longer (`DID_CHANGE_RENEWAL_STATUS`, `OFFER_REDEEMED`, `PRICE_INCREASE`, `RENEWAL_EXTENDED`, `METADATA_UPDATE`, `MIGRATION`, `RESCIND_CONSENT`, `UNCLAIM_SEATS` and others): acknowledge the types the app does not use. The mapping of refunds to the reversal code is in the `handle-refunds-and-reversals` skill.

## Payload or API

Apple says that after an outage, Get Transaction History and Get All Subscription Statuses give current information. Get Transaction Info (`GET /inApps/v1/transactions/{transactionId}`) returns one transaction. Verify what those return with the same verifier. Check that `appAccountToken`, when the app sets it, names the user the app expects.

## Test locally

- Request a Test Notification (`POST /inApps/v1/notifications/test` on the production or sandbox API host) sends a `TEST` notification to the matching URL. Get Test Notification Status reports the result.
- Sandbox and TestFlight purchases send sandbox notifications once, without retries. Sandbox refund testing can produce `REFUND`, `REFUND_DECLINED` and prorated refunds.
- These notifications are signed by Apple, so a local probe cannot forge them. Test the handler logic with a verifier stub injected in tests, and the verification with Apple's test notification.

## Bugs that ship

- Decoding `signedPayload` with a JWT library without verifying, or verifying the JWS with the key from `x5c` without checking the chain to an Apple root.
- Verifying the outer payload and trusting the nested `signedTransactionInfo` unverified.
- No check of `bundleId` and `environment`, so sandbox purchases grant in production.
- Keying credits on `originalTransactionId`, so every renewal after the first is a duplicate, or on `notificationUUID` alone, so a second notification type for one transaction credits again.
- Handling `SUBSCRIBED` and `DID_RENEW` but not `REFUND`, `REVOKE` and `EXPIRED`.
- Doing the work inline and timing out, so Apple's next try comes an hour later.

## Sources

- https://developer.apple.com/documentation/appstoreservernotifications/responsebodyv2
- https://developer.apple.com/documentation/appstoreservernotifications/jwsdecodedheader
- https://developer.apple.com/documentation/appstoreservernotifications/responding-to-app-store-server-notifications
- https://developer.apple.com/documentation/appstoreservernotifications/enabling-app-store-server-notifications
- https://developer.apple.com/documentation/appstoreservernotifications/notificationtype
- https://developer.apple.com/documentation/appstoreservernotifications/jwstransactiondecodedpayload
- https://developer.apple.com/documentation/appstoreservernotifications/revocationtype
- https://developer.apple.com/documentation/appstoreservernotifications/signeddate
- https://developer.apple.com/documentation/appstoreservernotifications/notificationuuid
- https://developer.apple.com/documentation/appstoreservernotifications/app-store-server-notifications-changelog
- https://developer.apple.com/documentation/appstoreserverapi/get-notification-history
- https://developer.apple.com/documentation/appstoreserverapi/request-a-test-notification
- https://developer.apple.com/documentation/appstoreserverapi/get-transaction-info
- https://developer.apple.com/documentation/storekit/testing-refund-requests
- https://developer.apple.com/help/app-store-connect/configure-in-app-purchase-settings/enter-server-urls-for-app-store-server-notifications
- https://www.apple.com/certificateauthority/
- https://github.com/apple/app-store-server-library-node

Checked 2026-11-15.
