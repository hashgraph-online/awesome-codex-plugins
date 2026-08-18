---
name: mobile-checkout
description: Guide for implementing mobile in-app checkout with Dodo Payments across React Native, Flutter, iOS, and Android platforms.
---

# Mobile In-App Checkout

This skill covers integrating Dodo Payments hosted checkout into native and cross-platform mobile apps using secure system browser contexts.

## When to use this skill

- Building a React Native app with Turbo Module checkout integration
- Adding checkout to a Flutter app via native bridge
- Implementing native iOS or Android checkout with secure browser contexts
- Registering custom URL schemes and deep links for payment return
- Handling abandoned checkout sessions and recovery flows
- Confirming payment authority server-side before granting access

## Core principle: Backend creates, mobile opens

Your backend creates the checkout session and returns a URL. The mobile app opens that URL in a secure browser context. Your API key must never be embedded in the app binary. The mobile SDK result is informational only; always verify the payment server-side via webhook or API before unlocking features or granting access.

## Architecture overview

1. **Backend:** Create a checkout session via `client.checkoutSessions.create(...)` and return the `checkout_url` to your mobile app.
2. **Mobile app:** Call the platform-specific SDK with the checkout URL and a registered return URL scheme.
3. **Browser context:** The SDK opens the URL in a secure system browser: SFSafariViewController on iOS and Chrome Custom Tabs on Android.
4. **Return:** After payment, the browser navigates to your return URL. The SDK captures the result and passes it to your app.
5. **Verification:** Query the checkout session or listen for a webhook to confirm the payment before granting access.

## React Native (Turbo Module)

### Installation

```bash
npm install @dodopayments/react-native-checkout
```

For Expo projects, add the plugin to `app.json`:

```json
{
  "expo": {
    "scheme": "myapp",
    "plugins": [
      [
        "@dodopayments/react-native-checkout",
        { "scheme": "myappcheckout" }
      ]
    ]
  }
}
```

The plugin registers a custom URL scheme (`myappcheckout://`) that the checkout flow uses to return to your app.

### Setup

Register the URL listener at app startup:

```typescript
import { Linking } from 'react-native';
import { DodoCheckout } from '@dodopayments/react-native-checkout';

// Required for iOS return-URL handling
Linking.addEventListener('url', ({ url }) => DodoCheckout.handleOpenURL(url));
```

### Starting checkout

```typescript
const result = await DodoCheckout.start({
  checkoutUrl: 'https://checkout.dodopayments.com/...',  // from your backend
  returnUrl: 'myappcheckout://checkout/return',          // must match registered scheme
  onEvent: (e) => console.log(e.type),                   // optional event logging
});

switch (result.status) {
  case 'succeeded':
    // Payment succeeded. Verify server-side before granting access.
    await verifyPaymentOnBackend(result.paymentId);
    showSuccess();
    break;
  case 'failed':
    // Payment failed. Show error to user.
    showFailure();
    break;
  case 'cancelled':
    // User cancelled. Dismiss checkout.
    dismiss();
    break;
  case 'pending':
    // Payment is pending (e.g., awaiting 3D Secure). Show waiting state.
    showPending();
    break;
  case 'expired':
    // Checkout session expired. Prompt user to start a new checkout.
    showExpired();
    break;
}
```

### Abandoned session recovery

If the app crashes or is backgrounded during checkout, recover the session:

```typescript
import { DodoCheckout } from '@dodopayments/react-native-checkout';

const abandoned = await DodoCheckout.getAbandonedSession();
if (abandoned) {
  // Reconcile abandoned.sessionId with your backend
  // Decide whether to resume or start fresh
  await DodoCheckout.clearAbandonedSession();
}
```

### Android minSdk requirement

React Native checkout requires Android minSdk 24 or higher. Note: the general mobile documentation mentions minSdk 23, but React Native specifically requires 24.

## Flutter

### Installation

Add the Dodo Payments Flutter package to `pubspec.yaml`:

```yaml
dependencies:
  dodopayments_checkout: ^1.0.2
```

### Setup

The package uses `DodoCheckout.instance`. On iOS, register the return URL scheme and forward incoming links from your deep-link listener. Run `flutter pub add app_links` if you use the `app_links` approach shown here:

```dart
import 'dart:async';

import 'package:app_links/app_links.dart';
import 'package:dodopayments_checkout/dodopayments_checkout.dart';

late final StreamSubscription<Uri> checkoutLinkSubscription;

void listenForCheckoutReturns() {
  checkoutLinkSubscription = AppLinks().uriLinkStream.listen((uri) {
    unawaited(DodoCheckout.instance.handleOpenURL(uri.toString()));
  });
}
```

Start the listener from your root state object's `initState` and cancel `checkoutLinkSubscription` from `dispose`. `handleOpenURL` is required on iOS and safely returns `false` on Android.

### Starting checkout

```dart
import 'package:dodopayments_checkout/dodopayments_checkout.dart';

final result = await DodoCheckout.instance.start(
  CheckoutParams(
    checkoutUrl: Uri.parse('https://checkout.dodopayments.com/...'),
    returnUrl: Uri.parse('myapp://checkout/return'),
    onEvent: (event) => print(event.type),
  ),
);

switch (result.status) {
  case CheckoutStatus.succeeded:
    final paymentId = result.paymentId;
    if (paymentId != null) {
      await verifyPaymentOnBackend(paymentId);
    }
    showSuccess();
    break;
  case CheckoutStatus.failed:
    showFailure();
    break;
  case CheckoutStatus.cancelled:
    dismiss();
    break;
  case CheckoutStatus.pending:
    showPending();
    break;
  case CheckoutStatus.expired:
    showExpired();
    break;
}
```

### Return URL registration

On Android, set the callback scheme in `android/app/build.gradle.kts`. The package's native checkout dependency supplies the intent filter, so do not add one manually:

```kotlin
android {
  defaultConfig {
    minSdk = 23
    manifestPlaceholders["dodoCallbackScheme"] = "myapp"
  }
}
```

Remove an empty `android:taskAffinity=""` from `MainActivity` if the generated Flutter manifest contains it; it can prevent Custom Tabs from returning correctly on some devices.

On iOS, register the same scheme in `ios/Runner/Info.plist`:

```xml
<key>CFBundleURLTypes</key>
<array>
  <dict>
    <key>CFBundleURLSchemes</key>
    <array>
      <string>myapp</string>
    </array>
  </dict>
</array>
```

## iOS (native)

### Setup

Use `SFSafariViewController` to open the checkout URL:

```swift
import SafariServices

let checkoutURL = URL(string: "https://checkout.dodopayments.com/...")!
let safariVC = SFSafariViewController(url: checkoutURL)
present(safariVC, animated: true)
```

### Deep-link handling

Register your custom URL scheme in `Info.plist`:

```xml
<key>CFBundleURLTypes</key>
<array>
  <dict>
    <key>CFBundleURLSchemes</key>
    <array>
      <string>myapp</string>
    </array>
  </dict>
</array>
```

Handle the return in your app delegate:

```swift
func application(
  _ app: UIApplication,
  open url: URL,
  options: [UIApplication.OpenURLOptionsKey: Any] = [:]
) -> Bool {
  if url.scheme == "myapp" && url.host == "checkout" {
    // Parse the result from the URL query parameters
    let components = URLComponents(url: url, resolvingAgainstBaseURL: false)
    let status = components?.queryItems?.first(where: { $0.name == "status" })?.value
    
    switch status {
    case "succeeded":
      let paymentId = components?.queryItems?.first(where: { $0.name == "payment_id" })?.value
      verifyPaymentOnBackend(paymentId: paymentId)
    case "cancelled":
      dismiss()
    case "expired":
      showExpired()
    default:
      break
    }
    return true
  }
  return false
}
```

## Android (native)

### Setup

Use Chrome Custom Tabs to open the checkout URL:

```kotlin
import androidx.browser.customtabs.CustomTabsIntent
import android.net.Uri

val checkoutUri = Uri.parse("https://checkout.dodopayments.com/...")
val customTabsIntent = CustomTabsIntent.Builder().build()
customTabsIntent.launchUrl(context, checkoutUri)
```

### Deep-link handling

Register your custom URL scheme in `AndroidManifest.xml`:

```xml
<activity android:name=".CheckoutReturnActivity">
  <intent-filter>
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="myapp" android:host="checkout" android:path="/return" />
  </intent-filter>
</activity>
```

Handle the return in your activity:

```kotlin
override fun onCreate(savedInstanceState: Bundle?) {
  super.onCreate(savedInstanceState)
  
  val uri = intent.data
  if (uri?.scheme == "myapp" && uri.host == "checkout") {
    val status = uri.getQueryParameter("status")
    val paymentId = uri.getQueryParameter("payment_id")
    
    when (status) {
      "succeeded" -> verifyPaymentOnBackend(paymentId)
      "cancelled" -> dismiss()
      "expired" -> showExpired()
    }
  }
}
```

## Backend: Creating checkout sessions

Always create checkout sessions on your backend. Never embed your API key in the mobile app.

```typescript
import DodoPayments from 'dodopayments';

const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,
  environment: 'test_mode',
});

const MOBILE_PRODUCTS = new Map([
  ['starter', 'pdt_starter123'],
  ['pro', 'pdt_pro456'],
]);

app.post('/api/mobile-checkout', requireAuth, async (req, res) => {
  const productId = MOBILE_PRODUCTS.get(req.body.plan);

  if (!productId) {
    return res.status(400).json({ error: 'Invalid plan' });
  }

  // requireAuth derives this mapping from the authenticated server-side session.
  const customerId = req.auth.dodoCustomerId;
  
  const session = await client.checkoutSessions.create({
    product_cart: [{ product_id: productId, quantity: 1 }],
    customer: { customer_id: customerId },
    return_url: 'myapp://checkout/return',
  });
  
  res.json({ checkout_url: session.checkout_url });
});
```

## Verifying payment server-side

Never grant access based on the mobile SDK result alone. Always verify via webhook or API.

### Via webhook

Listen for `payment.succeeded` webhooks. Webhook signature verification is covered in the `webhook-integration` skill.

```typescript
app.post('/webhook', async (req, res) => {
  const event = client.webhooks.unwrap(req.body.toString(), {
    headers: {
      'webhook-id': req.headers['webhook-id'] as string,
      'webhook-signature': req.headers['webhook-signature'] as string,
      'webhook-timestamp': req.headers['webhook-timestamp'] as string,
    },
  });
  
  if (event.type === 'payment.succeeded') {
    const paymentId = event.data.payment_id;
    const customerId = event.data.customer.customer_id;
    
    // Grant access to the customer
    await grantAccess(customerId);
  }
  
  res.json({ received: true });
});
```

### Via API

Query the checkout session to confirm payment:

```typescript
const session = await client.checkoutSessions.retrieve(sessionId);

if (session.payment_status === 'succeeded' && session.payment_id) {
  const payment = await client.payments.retrieve(session.payment_id);
  await grantAccess(payment.customer.customer_id);
}
```

## Selling digital goods on iOS

If you're selling digital goods (software, in-app features, subscriptions) on iOS, Apple requires you to use in-app purchase APIs for certain categories. Dodo Payments can handle the payment processing, but you must comply with App Store guidelines:

- Digital content (ebooks, music, software) must use in-app purchase.
- Physical goods and services can use alternative payment methods.
- Subscriptions for digital content must use in-app purchase.

Consult Apple's App Store Review Guidelines and consider whether your product category requires in-app purchase. If it does, integrate StoreKit 2 alongside Dodo Payments for compliance.

## Common mistakes

### Embedding the API key in the app

Never include your API key in the app binary or client-side code. Always create checkout sessions on your backend.

```typescript
// WRONG
const client = new DodoPayments({
  bearerToken: 'dodo_live_abc123...',  // Never hardcode
});

// CORRECT
const client = new DodoPayments({
  bearerToken: process.env.DODO_PAYMENTS_API_KEY,  // Backend only
});
```

### Trusting the mobile SDK result

The SDK result is informational. Always verify server-side before granting access.

```typescript
// WRONG
if (result.status === 'succeeded') {
  grantAccess();  // No verification
}

// CORRECT
if (result.status === 'succeeded') {
  const verified = await verifyPaymentOnBackend(result.paymentId);
  if (verified) {
    grantAccess();
  }
}
```

### Forgetting URL scheme registration

If you don't register the custom URL scheme, the app won't receive the return callback and checkout will appear to hang.

- React Native: Use the Expo plugin or manually register in `Info.plist` and `AndroidManifest.xml`.
- Flutter: Register in both `Info.plist` and `AndroidManifest.xml`.
- iOS: Add `CFBundleURLTypes` to `Info.plist`.
- Android: Add an intent filter with the scheme in `AndroidManifest.xml`.

### Not handling all result statuses

Always handle all five statuses: `succeeded`, `failed`, `cancelled`, `pending`, and `expired`. Each requires different UX.

```typescript
// WRONG
if (result.status === 'succeeded') {
  showSuccess();
}

// CORRECT
switch (result.status) {
  case 'succeeded':
    showSuccess();
    break;
  case 'failed':
    showFailure();
    break;
  case 'cancelled':
    dismiss();
    break;
  case 'pending':
    showPending();
    break;
  case 'expired':
    showExpired();
    break;
}
```

### Ignoring abandoned sessions

If the app crashes or is backgrounded during checkout, the session is abandoned. Always check for and recover abandoned sessions on app startup.

```typescript
// WRONG
// No recovery logic

// CORRECT
const abandoned = await DodoCheckout.getAbandonedSession();
if (abandoned) {
  // Reconcile and clear
  await DodoCheckout.clearAbandonedSession();
}
```

## Package names

Use `@dodopayments/react-native-checkout` for React Native and `dodopayments_checkout` for Flutter. The similarly named `@dodopayments/react-native` and `dodo_payments_flutter` packages do not exist.

## Resources

- [Mobile Integration](https://docs.dodopayments.com/developer-resources/mobile-integration)
- [React Native SDK](https://docs.dodopayments.com/developer-resources/sdks/react-native)
- [Flutter SDK](https://pub.dev/packages/dodopayments_checkout)
- [Selling Digital Goods on iOS](https://docs.dodopayments.com/features/appstore-digital-goods)
- [Webhook Integration](https://docs.dodopayments.com/developer-resources/webhooks/intents) (for payment verification)
