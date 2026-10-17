# Mobile In-App Checkout: Android (native)


Use the official Android checkout SDK (`minSdk` 23, Kotlin, Java 17). It opens Chrome Custom Tabs, declares the redirect intent filter itself, and returns a typed result.

### Installation

```kotlin
// app/build.gradle.kts
dependencies {
    implementation("com.dodopayments.api:checkout-android:1.1.0")
}

android {
    defaultConfig {
        // The SDK's manifest uses this placeholder; do not add an intent filter yourself.
        manifestPlaceholders["dodoCallbackScheme"] = "myapp"
    }
}
```

### Starting checkout

```kotlin
import com.dodopayments.checkout.CheckoutParams
import com.dodopayments.checkout.CheckoutStatus
import com.dodopayments.checkout.DodoCheckout
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

// The activity-result launcher survives process death.
private val checkoutLauncher =
    registerForActivityResult(DodoCheckout.contract()) { result ->
        when (result.status) {
            CheckoutStatus.SUCCEEDED -> showSuccess(result.paymentId) // UI hint only; verify on the backend
            CheckoutStatus.FAILED -> showFailure()
            // Outcome unknown, not a failure. reconcileAbandonedSession() suspends
            // (it calls your backend), so launch it from the lifecycle scope.
            CheckoutStatus.CANCELLED, CheckoutStatus.PENDING ->
                lifecycleScope.launch { reconcileAbandonedSession() }
            CheckoutStatus.EXPIRED -> showExpired()
        }
    }

checkoutLauncher.launch(
    CheckoutParams(
        checkoutUrl = checkoutUrl, // from your backend's checkout session
        returnUrl = "myapp://checkout/return"
    )
)
```

### Abandoned sessions

```kotlin
suspend fun reconcileAbandonedSession() {
    val abandoned = DodoCheckout.getAbandonedSession(context) ?: return

    // Your backend calls GET /checkouts/{sessionId} and returns payment_status.
    when (val outcome = fetchCheckoutOutcome(abandoned.sessionId)) {
        "succeeded", "failed", "expired" -> {
            showOutcome(outcome)
            // Clear only once the outcome is final.
            DodoCheckout.clearAbandonedSession(context)
        }
        else -> showPending() // still pending - keep the record and check again later
    }
}
```
