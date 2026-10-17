---
name: mobile-checkout
description: Dodo Payments in-app checkout for React Native, Flutter, native iOS, and Android using SFSafariViewController or Chrome Custom Tabs. Use when a mobile app must open a backend-created checkout session, handle deep link or custom URL scheme returns, recover abandoned checkouts, and verify payment server-side before unlocking access.
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

Full guide: [references/react-native.md](references/react-native.md).

Covers:

- Installation
- Setup
- Starting checkout
- Abandoned session recovery
- Android minSdk requirement

## Flutter

Full guide: [references/flutter.md](references/flutter.md).

Covers:

- Installation
- Setup
- Starting checkout
- Return URL registration

## iOS (native)

Full guide: [references/ios.md](references/ios.md).

Covers:

- Installation
- Starting checkout
- Forwarding the return URL
- Abandoned sessions

## Android (native)

Full guide: [references/android.md](references/android.md).

Covers:

- Installation
- Starting checkout
- Abandoned sessions

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
// Mount with express.raw({ type: 'application/json' }) so req.body is the raw Buffer.
app.post('/webhook', async (req, res) => {
  let event;
  try {
    event = client.webhooks.unwrap(req.body.toString(), {
      headers: {
        'webhook-id': req.headers['webhook-id'] as string,
        'webhook-signature': req.headers['webhook-signature'] as string,
        'webhook-timestamp': req.headers['webhook-timestamp'] as string,
      },
    });
  } catch {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  try {
    // Dodo retries and may redeliver: claim webhook-id with a UNIQUE insert
    // and grant in the same transaction so a duplicate is a no-op.
    await db.$transaction(async (tx) => {
      const claim = await tx.webhookLog.createMany({
        data: [{ webhookId: req.headers['webhook-id'] as string, eventType: event.type }],
        skipDuplicates: true,
      });
      if (claim.count === 0) return; // already processed

      if (event.type === 'payment.succeeded') {
        await grantAccess(event.data.customer.customer_id, tx);
      }
    });
  } catch (error) {
    // Non-2xx makes Dodo retry; the transaction rolled back the claim.
    return res.status(500).json({ error: 'Processing failed' });
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

Dodo Payments hosted checkout can sell digital goods (subscriptions, courses, downloads, SaaS plans) in an iOS app **only on App Store storefronts where Apple allows external purchases**:

- **United States:** Guideline 3.1.1(a) allows buttons and links to other purchase methods without an entitlement (subject to the Epic v. Apple proceedings).
- **European Union:** requires Apple's EU external purchase entitlement (the StoreKit External Purchases or Offers Entitlement from October 1, 2026) and DMA compliance.
- **Japan:** allowed under the Mobile Software Competition Act, following Apple's Japan-specific entitlement requirements.
- **South Korea is not supported** (Apple requires a native, non-web-view flow through an approved Korean PSP).

On other storefronts, digital goods sold inside the iOS app must use Apple in-app purchase (StoreKit). Review Apple's region-specific entitlements before enabling Dodo checkout for a storefront; unsupported flows can get the app rejected.

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
- iOS: Add `CFBundleURLTypes` to `Info.plist` and forward URLs to `DodoCheckout.handleOpenURL`.
- Android: Set `manifestPlaceholders["dodoCallbackScheme"]`; the SDK supplies the intent filter.

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
  case 'pending':
    // Unknown outcome - reconcile, never show a failure
    reconcileAbandonedSession();
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

// CORRECT: reconcile on launch and after every cancelled/pending result,
// and clear the record only once the backend reports a final outcome.
await reconcileAbandonedSession(); // defined in references/react-native.md
```

## Package names

Use `@dodopayments/react-native-checkout` for React Native and `dodopayments_checkout` for Flutter. The similarly named `@dodopayments/react-native` and `dodo_payments_flutter` packages do not exist.

## Resources

- [Mobile Integration](https://docs.dodopayments.com/developer-resources/mobile-integration)
- [React Native SDK](https://docs.dodopayments.com/developer-resources/sdks/react-native)
- [iOS SDK](https://docs.dodopayments.com/developer-resources/sdks/ios)
- [Android SDK](https://docs.dodopayments.com/developer-resources/sdks/android)
- [Flutter SDK](https://pub.dev/packages/dodopayments_checkout)
- [Selling Digital Goods on iOS](https://docs.dodopayments.com/features/appstore-digital-goods)
- [Webhook Integration](https://docs.dodopayments.com/developer-resources/webhooks/intents) (for payment verification)
