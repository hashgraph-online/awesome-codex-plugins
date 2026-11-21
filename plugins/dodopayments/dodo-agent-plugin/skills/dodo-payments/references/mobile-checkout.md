# Mobile checkout

## Contents

- [Flow](#flow)
- [Backend route](#backend-route)
- [React Native](#react-native)
- [Flutter](#flutter)
- [iOS](#ios)
- [Android](#android)
- [Result statuses and abandoned sessions](#result-statuses-and-abandoned-sessions)
- [Digital goods on iOS](#digital-goods-on-ios)
- [Common mistakes](#common-mistakes)

## Flow

1. Your backend creates a checkout session with a custom-scheme `return_url` (for example `myapp://checkout/return`) and returns `checkout_url`.
2. The app opens it with the Dodo mobile SDK, which uses SFSafariViewController on iOS and Chrome Custom Tabs on Android.
3. The SDK returns a result when the return URL fires. The result is a UI hint only.
4. Your backend grants access from the verified webhook ([webhooks.md](webhooks.md)) or by reading the checkout session.

The app never holds a Dodo API key.

## Backend route

```typescript
const MOBILE_PRODUCTS = new Map([
  ['starter', 'pdt_starter_monthly'],
  ['pro', 'pdt_pro_monthly'],
]);

app.post('/api/mobile-checkout', requireAuth, async (req, res) => {
  const productId = MOBILE_PRODUCTS.get(req.body.plan);
  if (!productId) return res.status(400).json({ error: 'Invalid plan' });

  const session = await client.checkoutSessions.create({
    product_cart: [{ product_id: productId, quantity: 1 }],
    customer: { customer_id: req.auth.dodoCustomerId }, // from the authenticated session
    return_url: 'myapp://checkout/return',
  });
  // Remember who started this session, so only they can read its status.
  await saveCheckoutSessionOwner(session.session_id, req.auth.userId);
  res.json({ checkout_url: session.checkout_url });
});

// Called by the app to reconcile a session whose result was unknown.
app.get('/api/mobile-checkout/:sessionId', requireAuth, async (req, res) => {
  const ownerId = await getCheckoutSessionOwner(req.params.sessionId);
  if (ownerId !== req.auth.userId) return res.status(404).json({ error: 'Not found' });
  const session = await client.checkoutSessions.retrieve(req.params.sessionId);
  res.json({ payment_status: session.payment_status });
});
```

## React Native

```bash
npm install @dodopayments/react-native-checkout
```

Requires Android minSdk 24. With Expo, the config plugin registers the checkout scheme:

```json
{ "expo": { "scheme": "myapp", "plugins": [["@dodopayments/react-native-checkout", { "scheme": "myappcheckout" }]] } }
```

Then use `myappcheckout://checkout/return` as both `returnUrl` below and the backend's `return_url`. Without Expo, register the scheme in `Info.plist` and `AndroidManifest.xml`.

```typescript
import { Linking } from 'react-native';
import { DodoCheckout } from '@dodopayments/react-native-checkout';

// At startup: iOS needs the return URL forwarded.
Linking.addEventListener('url', ({ url }) => DodoCheckout.handleOpenURL(url));

export async function buy(checkoutUrl: string) {
  const result = await DodoCheckout.start({ checkoutUrl, returnUrl: 'myappcheckout://checkout/return' });
  switch (result.status) {
    case 'succeeded':
      await refreshEntitlementsFromBackend(); // backend decides
      break;
    case 'failed':
      showFailure();
      break;
    case 'cancelled':
    case 'pending':
      await reconcileAbandonedSession(); // outcome unknown, not a failure
      break;
    case 'expired':
      showExpired();
      break;
  }
}

export async function reconcileAbandonedSession() {
  const abandoned = await DodoCheckout.getAbandonedSession();
  if (!abandoned) return;
  const outcome = await fetchCheckoutOutcome(abandoned.sessionId); // calls the GET route above
  if (outcome === 'succeeded' || outcome === 'failed' || outcome === 'expired') {
    showOutcome(outcome);
    await DodoCheckout.clearAbandonedSession(); // clear only once final
  }
}
```

## Flutter

```yaml
dependencies:
  dodopayments_checkout: ^1.0.2
  app_links: ^7.2.2 # receives the checkout return URL
```

```dart
import 'dart:async';

import 'package:app_links/app_links.dart';
import 'package:dodopayments_checkout/dodopayments_checkout.dart';

// At startup: forward return URLs (required on iOS, a no-op on Android).
void listenForCheckoutReturns() {
  AppLinks().uriLinkStream.listen((uri) {
    unawaited(DodoCheckout.instance.handleOpenURL(uri.toString()));
  });
}

Future<void> buy(Uri checkoutUrl) async {
  final result = await DodoCheckout.instance.start(
    CheckoutParams(checkoutUrl: checkoutUrl, returnUrl: Uri.parse('myapp://checkout/return')),
  );
  switch (result.status) {
    case CheckoutStatus.succeeded:
      await refreshEntitlementsFromBackend();
      break;
    case CheckoutStatus.failed:
      showFailure();
      break;
    case CheckoutStatus.cancelled:
    case CheckoutStatus.pending:
      await reconcileAbandonedSession();
      break;
    case CheckoutStatus.expired:
      showExpired();
      break;
  }
}
```

Android: in `android/app/build.gradle.kts` set `minSdk = 23` and `manifestPlaceholders["dodoCallbackScheme"] = "myapp"`; the package adds the intent filter. Remove an empty `android:taskAffinity=""` from `MainActivity`. iOS: add `myapp` under `CFBundleURLTypes` in `ios/Runner/Info.plist`.

## iOS

Add the Swift package `https://github.com/dodopayments/dodopayments-mobile-sdk-ios` (product `DodoCheckout`; iOS 16+) and register `myapp` under `CFBundleURLTypes`.

```swift
import DodoCheckout

let result = try await DodoCheckout.start(
    checkoutUrl: checkoutUrl,
    returnUrl: URL(string: "myapp://checkout/return")!
)
switch result.status {
case .succeeded: await refreshEntitlementsFromBackend()
case .failed: showFailure()
case .cancelled, .pending: await reconcileAbandonedSession()
case .expired: showExpired()
}

// SwiftUI: forward every incoming URL.
// .onOpenURL { url in DodoCheckout.handleOpenURL(url) }
```

Abandoned sessions: `DodoCheckout.getAbandonedSession()` and `DodoCheckout.clearAbandonedSession()`, as in React Native.

## Android

```kotlin
// app/build.gradle.kts
dependencies { implementation("com.dodopayments.api:checkout-android:1.1.0") }
android { defaultConfig { manifestPlaceholders["dodoCallbackScheme"] = "myapp" } } // the SDK adds the intent filter
```

```kotlin
private val checkoutLauncher =
    registerForActivityResult(DodoCheckout.contract()) { result ->
        when (result.status) {
            CheckoutStatus.SUCCEEDED -> lifecycleScope.launch { refreshEntitlementsFromBackend() }
            CheckoutStatus.FAILED -> showFailure()
            CheckoutStatus.CANCELLED, CheckoutStatus.PENDING -> lifecycleScope.launch { reconcileAbandonedSession() }
            CheckoutStatus.EXPIRED -> showExpired()
        }
    }

checkoutLauncher.launch(CheckoutParams(checkoutUrl = checkoutUrl, returnUrl = "myapp://checkout/return"))
```

Abandoned sessions: `DodoCheckout.getAbandonedSession(context)` and `DodoCheckout.clearAbandonedSession(context)`. Requires minSdk 23.

## Result statuses and abandoned sessions

| Status | Meaning | App action |
|---|---|---|
| `succeeded` | Paid, per the return URL | Refresh access from the backend |
| `failed` | Declined | Show the failure |
| `cancelled` | The browser closed before the return URL | Unknown outcome: reconcile |
| `pending` | `processing`, `requires_*`, or no status | Unknown outcome: reconcile |
| `expired` | The checkout session expired | Start a new checkout session |

The SDK keeps an abandoned-session record that survives an app kill. Reconcile it on launch and after every `cancelled` or `pending` result; clear it only when the backend reports `succeeded`, `failed` or `expired`.

## Digital goods on iOS

Selling digital goods with Dodo checkout inside an iOS app is allowed only on App Store storefronts where Apple permits external purchases: the United States, the European Union (with Apple's external purchase entitlement), and Japan (with Apple's Japan entitlement). South Korea is not supported. Elsewhere, digital goods in an iOS app must use Apple in-app purchase. Check Apple's current rules for each storefront before enabling it.

## Common mistakes

- An API key in the app binary.
- Granting access from the SDK result.
- Not registering the URL scheme, so checkout never returns.
- Showing a failure on `cancelled` or `pending`; the customer may have paid.
- Package names: `@dodopayments/react-native` and `dodo_payments_flutter` do not exist. Use `@dodopayments/react-native-checkout` and `dodopayments_checkout`.
