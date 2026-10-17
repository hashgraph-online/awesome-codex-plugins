# Mobile In-App Checkout: Flutter


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
  case CheckoutStatus.pending:
    // Outcome unknown (the payment may have succeeded): reconcile the
    // abandoned session with your backend instead of showing a failure.
    await reconcileAbandonedSession();
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
