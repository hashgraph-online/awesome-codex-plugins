# Payment providers: what to check per integration

Provider-specific shapes for the `unverified-events`, `duplicate-credit` and `refunds-and-reversals` classes. File each finding under its class as usual; this page only says where to look in code that integrates a named provider. Facts are from each provider's documentation on the date at the end of this file. When the project's provider is not listed, or the code uses an API version newer than that date, read the provider's current documentation and say in the report's notes which version was checked.

## Shapes common to every provider

- **Parsed before verified.** A global JSON parser runs before the webhook route (`app.use(express.json())` above it, a Next.js handler calling `request.json()`, a framework that only exposes the parsed body), and the signature is computed over `JSON.stringify(body)` or skipped. Look for the raw-body capture on that exact route.
- **`==` on signatures.** `signature == expected`, `===`, `strcmp`. Low on its own; see the severity rule in [unverified-events.md](unverified-events.md).
- **Timestamp parsed and ignored,** or a tolerance of 0, which in several official libraries switches the time check off.
- **Amount from the payload.** The grant is computed from the event's `amount` instead of the app's own order or price table. Even a verified event reports what was paid, not what it buys.
- **Only the success event.** One `case` in the event switch, and the refund, dispute and revocation types fall through to `200 OK`.
- **Dedupe on the wrong id:** a delivery id that changes on replay, a timestamp, the user id, or a cache with a time-to-live.
- **Test events accepted in production:** a `livemode`, `environment` or `test_mode` field never read.

## Stripe

- Search: `constructEvent`, `construct_event`, `Stripe-Signature`, `whsec_`, `checkout.session`.
- Verification: the `Stripe-Signature` header is `t=` plus one or more `v1=` entries over `<t>.<raw body>` with HMAC-SHA256. Code that takes the first `v1` only, or splits the header by position, fails during a secret roll; code that accepts `v0` accepts a sandbox-only scheme. Debug entries such as `secret=` and `payload=` are not signed.
- `tolerance` passed as 0, or `constructEvent` wrapped in a `try` whose `catch` continues.
- Fulfillment on `checkout.session.completed` without reading `payment_status`, and no handler for `checkout.session.async_payment_succeeded` and `async_payment_failed`.
- No handler for `refund.created` or `charge.refunded`, or both handled as separate refunds. No handler for `charge.dispute.created` and `charge.dispute.closed`.
- Dedupe on `event.id` is correct. Stripe adds that two separate events can describe one change, so a business key on the object id is needed too.
- Amounts are minor units; a `/ 100` on a zero-decimal currency is a `money-arithmetic` finding.

## Paddle Billing

- Search: `Paddle-Signature`, `unmarshal`, `isSignatureValid`, `Verifier`, `pdl_ntfset`, `h1=`.
- Signed text is `<ts>:<raw body>` (colon, not dot). The SDK tolerance is five seconds. A Python service with `TEST_MODE=1` in its environment skips the time check in Paddle's Python SDK.
- A parser that requires exactly two header parts, or keeps only one `h1`, breaks rotation.
- Dedupe on `notification_id` instead of `event_id`: a replay from the dashboard or API gets a new notification id and credits again.
- `adjustment.*` not handled, or a `pending_approval` refund treated as final, or `chargeback_reverse` never giving anything back.
- Amount strings such as `"1000"` read with `parseFloat`.

## Lemon Squeezy

- Search: `X-Signature`, `X-Event-Name`, `order_created`, `meta.event_name`.
- `X-Signature` is a hex HMAC-SHA256 of the raw body. No timestamp is signed, so a captured request is valid forever: missing dedupe is the whole replay risk.
- No event id exists in the payload. A handler that credits `order_created` without a unique key on the order id credits again on a dashboard resend.
- Dispatch on the unsigned `X-Event-Name` header instead of `meta.event_name` from the verified body.
- `order_refunded`: `refunded_amount` is the total to date. Subtracting it on every event takes too much on the second partial refund.

## PayPal

- Search: `verify-webhook-signature`, `PAYPAL-TRANSMISSION-SIG`, `paypal-cert-url`, `crc32`, `WEBHOOK_ID`.
- Self-verification that downloads the certificate from the `PAYPAL-CERT-URL` header without restricting the host. Anyone can then sign with their own certificate: a bypassable check, rated by the rule in [unverified-events.md](unverified-events.md).
- The verify API answers 200 for both outcomes: code that checks the HTTP status and not `verification_status === 'SUCCESS'` accepts every event.
- The event sent to the verify API is built from a parsed object, so genuine events fail and someone adds a fallback.
- The client id used where the webhook id belongs, or the literal simulator webhook id `WEBHOOK_ID` accepted in production.
- Credit on `CHECKOUT.ORDER.APPROVED` or `PAYMENT.CAPTURE.PENDING`; no handler for `PAYMENT.CAPTURE.REFUNDED`, `PAYMENT.CAPTURE.REVERSED`, `CUSTOMER.DISPUTE.*`.
- Decimal strings such as `"9.99"` converted through a float.

## RevenueCat

- Search: `RevenueCat`, `X-RevenueCat-Webhook-Signature`, `INITIAL_PURCHASE`, `NON_RENEWING_PURCHASE`, `app_user_id`.
- The `Authorization` header checked only when present, compared with `==`, or not checked. With HMAC signing off, that header is the only proof of the sender.
- `environment` never compared, so sandbox purchases credit in production.
- Credits on every `NON_RENEWING_PURCHASE`, including promotional grants made from the RevenueCat dashboard (`store` `PROMOTIONAL`).
- `CANCELLATION` with `cancel_reason` `CUSTOMER_SUPPORT` (a refund) ignored, or every `CANCELLATION` treated as a refund.
- User looked up by `app_user_id` only, not `original_app_user_id` and `aliases`.

## App Store Server Notifications V2

- Search: `signedPayload`, `SignedDataVerifier`, `verifyAndDecodeNotification`, `signedTransactionInfo`, `jwt.decode`, `jose.decodeJwt`.
- `signedPayload` decoded without verification (`jwt.decode`, `decodeJwt`, a manual base64 split), or verified with the public key taken from `x5c` without checking the chain to an Apple root. Anyone can then send a notification.
- The outer payload verified and `signedTransactionInfo` decoded without verification.
- `bundleId` and `environment` not compared, or a verifier configured for the `Xcode` or `LocalTesting` environment in a deployed service.
- Credits keyed on `originalTransactionId` (renewals collide) or on `notificationUUID` alone (two notification types for one transaction both credit).
- No branch for `REFUND`, `REVOKE` or `EXPIRED`; `REFUND_PRORATED` treated as full.

## Google Play real-time developer notifications

- Search: `purchaseToken`, `subscriptionNotification`, `voidedPurchaseNotification`, `verifyIdToken`, `pubsub`, `androidpublisher`.
- The push endpoint accepts requests without a verified OIDC token, or verifies the token without checking `aud` and `email`. A shared token in the push URL alone is not documented as sufficient.
- Credit granted from the notification without calling `purchases.subscriptionsv2.get` or the products API. The notification carries no purchase details, and a pending purchase must not grant.
- No acknowledgement or consumption: Google refunds after three days while the credits stay.
- `voidedPurchaseNotification` not handled, or one-time product notifications not enabled in the Play Console, so voids of credit packs never arrive.
- Dedupe on `orderId` (absent for some purchases) or `messageId` alone; `linkedPurchaseToken` ignored on upgrades.

## Not a bug

- The provider's official SDK verifies the event before the handler runs: name the call in the report.
- A handler that answers 2xx and does nothing for event types the app does not use.
- No timestamp check for Apple and Google Play: their authentication is a signed token, and Apple's retries can come days later.
- A refund handled by a scheduled reconciliation against the provider's API instead of the webhook. Check that job the same way.

## Sources

- https://docs.stripe.com/webhooks
- https://docs.stripe.com/events/manage-webhook-endpoints
- https://developer.paddle.com/webhooks/about/signature-verification
- https://developer.paddle.com/webhooks/about/how-webhooks-work
- https://docs.lemonsqueezy.com/help/webhooks/signing-requests
- https://developer.paypal.com/api/rest/webhooks/rest/
- https://www.revenuecat.com/docs/integrations/webhooks
- https://developer.apple.com/documentation/appstoreservernotifications/responsebodyv2
- https://github.com/apple/app-store-server-library-node
- https://developer.android.com/google/play/billing/rtdn-reference
- https://developer.android.com/google/play/billing/security
- https://cloud.google.com/pubsub/docs/authenticate-push-subscriptions

Checked 2026-11-15.
