# Android Architecture and Quality Baseline

Use the smallest architecture that keeps UI state observable, business logic
testable, data access replaceable, and lifecycle behavior correct. Add modules
or frameworks only when they solve a demonstrated boundary.

## Default Project Shape

```text
app/
  src/main/
    java/.../
      ui/                 Compose screens, components, navigation
      feature/<name>/     screen state, events, ViewModel
      data/               repositories and data sources
      domain/             optional use cases/domain models when complexity earns it
      platform/           billing, notifications, permissions, integrity adapters
    res/
  src/test/               local unit tests
  src/androidTest/        instrumented and Compose UI tests
benchmark/                Macrobenchmark and Baseline Profile generation
gradle/libs.versions.toml pinned plugin and library coordinates
```

One small app can keep these as packages in `:app`. Split modules when build
time, ownership, independent delivery, or dependency boundaries justify the
cost; do not modularize by fashion.

## Build Baseline

Resolve current stable Android Gradle Plugin, Kotlin, Compose BOM, and Jetpack
versions from official release sources and lock them. Avoid dynamic versions.

```kotlin
plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

android {
    namespace = "com.example.product"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.example.product"
        minSdk = 24 // product decision; verify device-market requirements
        targetSdk = 36
        versionCode = 1
        versionName = "1.0.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
    }
}
```

This is a shape, not a dependency-version manifest. Confirm plugin syntax and
SDK availability in the actual toolchain. Test release shrinking, serialization,
reflection, native libraries, and crash symbol/mapping upload.

## Architecture Contract

- Compose renders immutable UI state and emits user events.
- A screen-level ViewModel owns screen state and survives configuration change.
- State flows in one direction; do not let composables mutate repositories.
- Repositories expose application data and coordinate local/remote sources.
- Data sources own one storage/network/platform integration each.
- Coroutines use structured concurrency and injected dispatchers where tests
  need control. Do not launch unowned global work.
- Persist durable small preferences in DataStore and structured local data in
  Room when those needs exist. Do not add a database to an ephemeral tool.
- Model loading, empty, success, stale/offline, recoverable error, terminal
  error, and permission-denied states where relevant.
- Use lifecycle-aware collection and save only the minimum restorable UI state.
- Make navigation routes and deep links typed/validated; test external inputs.
- Inject time, random, network, storage, billing, and integrity boundaries so
  deterministic tests do not depend on production services.

Official architecture guidance:
<https://developer.android.com/topic/architecture/recommendations>

## Test Pyramid and Device Matrix

Minimum relevant coverage:

- pure domain and formatting unit tests;
- repository tests for cache/network ordering, errors, retries, and migrations;
- ViewModel tests for state transitions and one-shot effects;
- Compose UI tests for core tasks, semantics, focus, errors, and restoration;
- instrumented tests for Room migrations, platform APIs, deep links,
  permissions, and process recreation where risk warrants them;
- end-to-end tests for sign-in, purchase/restore, deletion, and the core outcome;
- contract tests for backend error/schema behavior when a backend exists.

Test at least:

- minimum supported API;
- target/current API 36 behavior;
- a 16 KB page-size emulator/device for releases targeting Android 15+,
  including any transitive native library paths;
- a representative mid-range device;
- compact and expanded windows, portrait/landscape, split-screen or resize when
  supported;
- offline, slow/lost network, denied permission, background/restore, low
  storage, locale, 24-hour time, and large text as relevant.

Typical evidence commands (adapt to the repo):

```bash
./gradlew testDebugUnitTest
./gradlew lintDebug
./gradlew connectedDebugAndroidTest
./gradlew assembleRelease
./gradlew bundleRelease
```

Do not claim all tests passed if a required device test was skipped. Record the
device/emulator model, API, locale, and command result.

Official testing guidance:
<https://developer.android.com/training/testing/fundamentals>

## Accessibility Gate

- Every actionable or meaningful visual has accurate Compose semantics; merge
  or clear descendant semantics only intentionally.
- TalkBack order, labels, roles, state, headings, custom actions, and error
  announcements match the visible UI.
- Touch targets and spacing follow Android/Material guidance without creating
  overlapping targets.
- Text supports user font scaling; layouts reflow without clipping or hiding
  the primary action.
- Color contrast is measured; color is not the only signal.
- Keyboard, D-pad, switch access, and focus order work for applicable form
  factors.
- Motion and animation respect system reduction/settings where applicable and
  never gate task completion.
- Run automated accessibility checks, then manually test the core flow with
  TalkBack and large text; automation alone is not evidence of usability.

Official accessibility testing guidance:
<https://developer.android.com/guide/topics/ui/accessibility/testing>

## Performance and Reliability Gate

Define budgets from product context and representative devices, then measure:

- startup time to initial display (TTID) and fully drawn/useful state (TTFD);
- frame timing/jank during the core task;
- core-task latency, network timeout/retry behavior, and offline response;
- memory growth/leaks, excessive work, battery/network impact, and ANRs;
- release size and delivery behavior.

Create a Macrobenchmark module and Baseline Profile for critical startup and
navigation paths. Generate the profile against a non-debuggable profileable
build, package it in the release, and verify profile installation/benchmark
results. Baseline Profiles optimize important code paths; they do not replace
measurement or fix network/backend latency.

Inspect Android vitals and the Play pre-launch report after a test release.
Define alert owners for crashes, ANRs, billing errors, and core-task failures.

Primary sources:

- Core app quality:
  <https://developer.android.com/docs/quality-guidelines/core-app-quality>
- Baseline Profiles:
  <https://developer.android.com/topic/performance/baselineprofiles/overview>
- Macrobenchmark:
  <https://developer.android.com/topic/performance/benchmarking/macrobenchmark-overview>

## Security Gate

- Threat-model accounts, exported components, intents/deep links, local data,
  network calls, WebViews, files/content providers, backups, notifications,
  billing, and abuse-sensitive operations.
- Export only required components and protect them with validation and
  permissions where appropriate.
- Keep credentials and authorization decisions server-side. Store only
  appropriate device-bound cryptographic material with Android Keystore.
- Redact tokens, personal data, purchase tokens, and secrets from logs, crash
  reports, screenshots, clipboard, and backups.
- Validate all external input and use HTTPS/TLS. Do not add permissive network
  security exceptions to make development traffic work in release.
- Audit dependencies and SDK behavior; remove abandoned or unnecessary SDKs.
- Use OWASP MASVS as a risk-based control catalog, not a claim of certification.

OWASP MASVS: <https://mas.owasp.org/MASVS/>
