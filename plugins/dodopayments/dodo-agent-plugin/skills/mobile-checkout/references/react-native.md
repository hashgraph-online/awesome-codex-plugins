# Mobile In-App Checkout: React Native (Turbo Module)


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
    // Sheet closed before the return URL arrived: the outcome is UNKNOWN and the
    // payment may have succeeded. Do not show a failure - reconcile instead.
    await reconcileAbandonedSession();
    break;
  case 'pending':
    // Settles later (status=processing / requires_*), or status was missing.
    await reconcileAbandonedSession();
    break;
  case 'expired':
    // Checkout session expired. Prompt user to start a new checkout.
    showExpired();
    break;
}
```

### Abandoned session recovery

The SDK keeps a record of the session until checkout ends with `succeeded`, `failed`, or `expired`. The record survives an app kill and **stays after a `cancelled` or `pending` result**. Check it on the next launch and after every `cancelled`/`pending`:

```typescript
import { DodoCheckout } from '@dodopayments/react-native-checkout';

async function reconcileAbandonedSession() {
  const abandoned = await DodoCheckout.getAbandonedSession();
  if (!abandoned) return;

  // Your backend calls GET /checkouts/{abandoned.sessionId} and returns payment_status.
  const outcome = await fetchCheckoutOutcome(abandoned.sessionId);
  if (outcome === 'succeeded' || outcome === 'failed' || outcome === 'expired') {
    showOutcome(outcome);
    // Clear only once the outcome is final; until then treat it as pending, not failed.
    await DodoCheckout.clearAbandonedSession();
  } else {
    showPending();
  }
}
```

### Android minSdk requirement

React Native checkout requires Android minSdk 24 or higher. Note: the general mobile documentation mentions minSdk 23, but React Native specifically requires 24.
