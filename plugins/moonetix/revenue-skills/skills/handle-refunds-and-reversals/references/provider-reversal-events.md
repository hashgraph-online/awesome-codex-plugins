# Reversing events per provider

Step 1 of the skill, done for seven providers from their documentation on the date at the end of this file. For each: which event becomes a refund, a dispute stage or a revocation, which field says how much money went back, how a partial reversal shows, which id links it to the original credit, and what to do when it arrives before the payment. The functions named here (`recordRefund`, `recordDispute`, `settleOrder`, `takeBack`, `reverse_conversion`) are in [tie-reversals-to-originals.md](tie-reversals-to-originals.md) and [disputes-and-reporting.md](disputes-and-reporting.md).

Two rules hold for every row:

- **Store the provider's id of the payment on the order** when the order is created or paid (PaymentIntent, transaction, capture, store transaction id), or pass the app's order id to the provider as metadata. A reversal names the payment, not the order. Without the link it cannot be matched.
- **One source per fact.** Several providers report the same refund in two events. Pick one as the source and acknowledge the other, or the refund is taken twice under two keys.

The amount in a reversal message is how much money went back, used for the share of a partial refund. What is taken back is always computed from the original entry.

## Stripe

| Event | Maps to | Amount and partial | Link and key |
| --- | --- | --- | --- |
| `refund.created`, `refund.updated` | Refund | `refund.amount` in minor units, per refund. Apply when `status` is `pending` or `succeeded`. A later `failed` or `canceled` goes to a person | Key: refund id. Link: `refund.payment_intent` or `refund.charge` |
| `charge.refunded` | Refund, the other source | `charge.amount_refunded` is the running total; `charge.refunded` is true only when full | Key: charge id plus the running total. Use either this or `refund.*`, never both |
| `charge.dispute.created` | `open` for status `needs_response` or `under_review`. The `warning_*` statuses are inquiries: mark the account and decide with the user whether to take | `dispute.amount`, can differ from the charge | Key: dispute id. Link: `dispute.charge`, `dispute.payment_intent` |
| `charge.dispute.closed` | `won` for `won`, `lost` for `lost`. `warning_closed`: the inquiry closed without a chargeback | | Same dispute id |
| `charge.dispute.funds_withdrawn`, `funds_reinstated` | Money movement inside the same dispute | | Same dispute id. Not a second dispute |

Statuses the code does not know, such as `prevented` or the `appeal_*` ones, go to a person. **Arrives first:** the refund names a PaymentIntent the app has not seen paid. Store it against the order found through the PaymentIntent id or its metadata; the payment handler settles it.

## Paddle Billing

| Event | Maps to | Amount and partial | Link and key |
| --- | --- | --- | --- |
| `adjustment.created`, `adjustment.updated` with `action` `refund` | Refund, applied when `status` is `approved`. `pending_approval` is stored and waits; `rejected` closes it | `data.totals.total`, an integer string in the lowest denomination. `type` is `full` or `partial` | Key: adjustment id. Link: `data.transaction_id` |
| `action` `chargeback` or `chargeback_warning` | `open`. Paddle says the amount is refunded | `data.totals.total` | Key: adjustment id. Link: `data.transaction_id` |
| `action` `chargeback_reverse` | `won`: Paddle returns the amount held | | Link to the chargeback through `data.transaction_id` |
| `action` `credit` | A credit, not money returned to the buyer. Decide with the user | | |

Not every adjustment passes through `pending_approval`, which is why `adjustment.created` must be handled as well as `adjustment.updated`. **Arrives first:** an adjustment for a transaction not yet credited is stored against the order that holds `transaction_id`.

## Lemon Squeezy

| Event | Maps to | Amount and partial | Link and key |
| --- | --- | --- | --- |
| `order_refunded` | Refund | `refunded_amount` in cents is the total to date. `refunded` is true when full, `status` `partial_refund` or `refunded` | Key: order id plus `refunded_amount`. The new refund is the total minus what is stored |
| `subscription_payment_refunded` | Refund of one subscription invoice | `refunded_amount` on the invoice, total to date | Key: invoice id plus `refunded_amount` |

No dispute event is documented. Lemon Squeezy says it usually refunds a disputed payment itself and charges a dispute fee. Reconcile order statuses through the API. **Arrives first:** store against the order named by `meta.custom_data`, which the app sets at checkout.

## PayPal

| Event | Maps to | Amount and partial | Link and key |
| --- | --- | --- | --- |
| `PAYMENT.CAPTURE.REFUNDED` | Refund | Refund `amount.value`, a decimal string; `seller_payable_breakdown.total_refunded_amount` is the total to date | Key: refund id. Link: the capture id in the `up` link |
| `PAYMENT.CAPTURE.REVERSED` | Reversal of the capture by PayPal: treat as a dispute `open`, or as a refund if the user decides so | Fetch the capture to read what was reversed | Key: the resource id. Link: the capture |
| `CUSTOMER.DISPUTE.CREATED` | `open` once `dispute_life_cycle_stage` is `CHARGEBACK`. An `INQUIRY` marks the account | `dispute_amount`; can be part of the payment | Key: dispute id. Link: the disputed transaction's capture id |
| `CUSTOMER.DISPUTE.RESOLVED` | `dispute_outcome.outcome_code`: `RESOLVED_BUYER_FAVOUR` is `lost`, `RESOLVED_SELLER_FAVOUR` and `CANCELED_BY_BUYER` are `won`. Others go to a person | `dispute_outcome.amount_refunded` | Same dispute id |
| `PAYMENT.SALE.REFUNDED`, `PAYMENT.SALE.REVERSED` | Refund or reversal of a subscription payment (v1 resource) | `amount.total`, a decimal string | Key: resource id. Link: the sale id |

The dispute webhook's resource is not documented field by field on the event pages: fetch the dispute with `GET /v1/customer/disputes/{id}` and map from the answer. Convert decimal strings to minor units with the currency's exponent. **Arrives first:** store against the order that holds the capture id.

## RevenueCat

| Event | Maps to | Amount and partial | Link and key |
| --- | --- | --- | --- |
| `CANCELLATION` with `cancel_reason` `CUSTOMER_SUPPORT` | Refund | `price_in_purchased_currency` is negative. Partial refunds are not described | Key: event id. Link: `transaction_id` |
| `REFUND_REVERSED` (App Store) | Give back what the refund took | Positive price | Link: `transaction_id` |
| `VIRTUAL_CURRENCY_TRANSACTION` with a negative adjustment | Refund of RevenueCat virtual currency | `adjustments[].amount` | Key: `virtual_currency_transaction_id` |
| `EXPIRATION` | End of access, not money | | |

A subscription refund sends `CANCELLATION` only when the latest period is refunded. Refunds of earlier periods send nothing: reconcile through `GET /subscribers`. **Arrives first:** store the refund under `transaction_id` as an early reversal; the credit for that transaction then posts nothing.

## App Store Server Notifications V2

| Notification | Maps to | Amount and partial | Link and key |
| --- | --- | --- | --- |
| `REFUND` | Refund | `revocationType` `REFUND_FULL` or `REFUND_PRORATED` with `revocationPercentage` in milliunits (`40000` is 40 percent). The share is the grant times the percentage, rounded down | Key: `notificationUUID`. Link: `transactionId` of the verified `signedTransactionInfo` |
| `REFUND_REVERSED` | Give back what the refund took | `revocationPercentage` is absent after a reversal | Link: `transactionId` |
| `REVOKE` | Access revoked (`FAMILY_REVOKE`, `ASSIGNMENT_REVOKE`). Not money from this user | | Revoke the entitlement of `transactionId` |
| `REFUND_DECLINED`, `CONSUMPTION_REQUEST` | No money moved | | |

Apple does not document how two prorated refunds of one transaction are reported. Treat the percentage as the share revoked to date, read from Get Transaction Info, and post only the difference: the running-total form. **Arrives first:** a `REFUND` for a transaction the app has not credited yet is stored under `transactionId` and taken back when the credit runs.

## Google Play

| Notification | Maps to | Amount and partial | Link and key |
| --- | --- | --- | --- |
| `voidedPurchaseNotification` | Refund, chargeback or other void | `refundType` 1 full, 2 quantity-based partial. The remaining quantity is `refundableQuantity` in `purchases.productsv2`; the share is the grant times the voided quantity over the quantity bought | Key: `purchaseToken` plus `orderId`. Each subscription renewal has its own order id |
| `subscriptionNotification` 12 `SUBSCRIPTION_REVOKED` | End access now; a refund if the app credited a balance | | Link: `purchaseToken` |
| `oneTimeProductNotification` 2 `ONE_TIME_PRODUCT_CANCELED` | Canceled or revoked: read the purchase state | | Link: `purchaseToken` |
| `pendingRefundReviewNotification` | A chargeback under review, to be answered within 24 hours. No money yet | | Hold payouts, alert a person |

The Voided Purchases API lists voids of the past 30 days; run it on a schedule with `type=1` and `includeQuantityBasedPartialRefund=true`. **Arrives first:** store the void under (`purchaseToken`, `orderId`); the purchase handler settles it after it reads the purchase from the API.

## Sources

- https://docs.stripe.com/api/events/types
- https://docs.stripe.com/api/refunds/object
- https://docs.stripe.com/api/charges/object
- https://docs.stripe.com/api/disputes/object
- https://developer.paddle.com/webhooks/adjustments/adjustment-created
- https://developer.paddle.com/webhooks/adjustments/adjustment-updated
- https://developer.paddle.com/build/transactions/create-transaction-adjustments
- https://docs.lemonsqueezy.com/help/webhooks/event-types
- https://docs.lemonsqueezy.com/api/orders/the-order-object
- https://docs.lemonsqueezy.com/help/payments/refunds-chargebacks
- https://developer.paypal.com/api/rest/webhooks/event-names/
- https://developer.paypal.com/api/payments/v2/
- https://developer.paypal.com/api/customer-disputes/v1/
- https://developer.paypal.com/disputes/disputes-lifecycle
- https://www.revenuecat.com/docs/integrations/webhooks/event-types-and-fields
- https://www.revenuecat.com/docs/integrations/webhooks/sample-events
- https://developer.apple.com/documentation/appstoreservernotifications/notificationtype
- https://developer.apple.com/documentation/appstoreservernotifications/revocationtype
- https://developer.apple.com/documentation/appstoreserverapi/revocationpercentage
- https://developer.android.com/google/play/billing/rtdn-reference
- https://developers.google.com/android-publisher/voided-purchases

Checked 2026-11-15.
