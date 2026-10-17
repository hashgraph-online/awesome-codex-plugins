# Mobile In-App Checkout: iOS (native)


Use the official Swift package rather than parsing the return URL yourself. It presents `SFSafariViewController`, matches the return URL, and maps `status` (including `active` for subscriptions and `processing`/`requires_*` as pending) into a typed result. Requires iOS 16+ and Swift 6.2+.

### Installation

Add `https://github.com/dodopayments/dodopayments-mobile-sdk-ios` (1.1.0 or later) in **File → Add Package Dependencies**, or in `Package.swift`:

```swift
.package(url: "https://github.com/dodopayments/dodopayments-mobile-sdk-ios", from: "1.1.0")
```

The library product is `DodoCheckout`. Register your scheme (`myapp`) under `CFBundleURLTypes` in `Info.plist`, and use the same URL as the session's `return_url`.

### Starting checkout

```swift
import DodoCheckout

let result = try await DodoCheckout.start(
    checkoutUrl: checkoutUrl,   // URL from your backend's checkout session
    returnUrl: URL(string: "myapp://checkout/return")!,
    onEvent: { event in print(event.name) }  // logging only
)

switch result.status {
case .succeeded: showSuccess(result.paymentId)          // UI hint only; verify on the backend
case .failed:    showFailure()
case .cancelled: await reconcileAbandonedSession()      // outcome unknown, not a failure
case .pending:   await reconcileAbandonedSession()
case .expired:   showExpired()
}
```

### Forwarding the return URL

`SFSafariViewController` cannot catch its own return URL, so forward every incoming URL to the SDK:

```swift
// SwiftUI
.onOpenURL { url in
    DodoCheckout.handleOpenURL(url)
}
```

`handleOpenURL` returns `true` only for the in-progress checkout's return URL; handle other URLs yourself.

### Abandoned sessions

```swift
func reconcileAbandonedSession() async {
    guard let abandoned = DodoCheckout.getAbandonedSession() else { return }

    // Your backend calls GET /checkouts/{sessionId} and returns payment_status.
    let outcome = await fetchCheckoutOutcome(abandoned.sessionId)
    switch outcome {
    case "succeeded", "failed", "expired":
        showOutcome(outcome)
        // Clear only once the outcome is final.
        DodoCheckout.clearAbandonedSession()
    default:
        showPending() // still pending - keep the record and check again later
    }
}
```
