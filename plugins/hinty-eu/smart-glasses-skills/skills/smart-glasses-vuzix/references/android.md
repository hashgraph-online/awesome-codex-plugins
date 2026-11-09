# Android: Ultralite SDK setup and lifecycle

Last checked: 2026-11-08. Verification: docs-only (no hardware test yet). Sources: the SDK
[README](https://github.com/Vuzix/ultralite-sdk-android), the
[Javadoc](https://vuzix.github.io/ultralite-sdk-android/javadoc) and the JitPack POM for 1.9.

## Requirements

- Android 12 or later (README). The official sample app uses `minSdk = 31`, `compileSdk = 34`.
- The **Vuzix Connect** app (`com.vuzix.connect`, [Google Play](https://play.google.com/store/apps/details?id=com.vuzix.connect))
  installed, with the glasses paired in it. On Android, Connect owns the Bluetooth link and your app talks to Connect.
- A Vuzix Z100 (or a Mentra Mach1, the same hardware). Neither is sold any more (as of 2026-11-09), so you need an
  existing pair; see "Licence and publishing" in `SKILL.md`.
- Transitive dependencies of 1.9 (from its POM): `androidx.appcompat:appcompat:1.6.1` and
  `org.jetbrains.kotlin:kotlin-stdlib:1.9.24`. Newer versions in your app win during resolution.

## Dependency

The library is on JitPack, not Maven Central. Add JitPack once, scoped to the Vuzix group so JitPack is never asked
for anything else:

```kotlin
// settings.gradle.kts
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        maven {
            url = uri("https://jitpack.io")
            content { includeGroup("com.vuzix") }
        }
    }
}
```

```kotlin
// app/build.gradle.kts
dependencies {
    implementation("com.vuzix:ultralite-sdk-android:1.9")
}
```

- Use the JitPack tag **`1.9`** (latest OK build as of 2026-11-08, see
  `https://jitpack.io/api/builds/com.vuzix/ultralite-sdk-android/latest`). Earlier tags: 1.8, 1.7, 1.5, 1.4.1.
- Do not use `main-SNAPSHOT` (the official sample does): your build changes whenever the repo does.
- `1.9.0` is not a JitPack tag (unverified: expected not to resolve).
- Your build depends on jitpack.io being up. A caching proxy for your CI (for example a repository manager that
  proxies JitPack) avoids outages. Do not commit the AAR to a public repo: the licence forbids redistribution (§3.3).
- React Native: the React Native Gradle plugin adds JitPack to every project unless `includeJitpackRepository=false`
  is set in `gradle.properties` (checked in the RN 0.84 plugin source). Your scoped entry above is still fine.
- Flutter, .NET MAUI and other cross-platform stacks: no official plugin is published (as of 2026-11-08). Write a thin
  platform channel around the calls in this file.

## Manifest and permissions

- The SDK needs **no permissions** (Connect holds Bluetooth). The official sample declares none.
- To check whether Connect is installed with `PackageManager` on Android 11+, declare package visibility. The SDK's
  own manifest may already merge this entry; declaring it yourself is harmless:

```xml
<queries>
    <package android:name="com.vuzix.connect" />
</queries>
```

- Permissions for your own features still apply: `RECORD_AUDIO` if you caption from the phone microphone (the Z100
  has none), a foreground service while a long session runs with the screen off.

## Guide the user through the states

| Check | Meaning | What to show |
|---|---|---|
| Connect not installed | `PackageManager` cannot find `com.vuzix.connect` | Link to the Play listing |
| `isAvailable()` false | SDK not bound to Connect yet, or Connect missing | Wait a few seconds after start before reporting it |
| `isLinked()` false | No glasses paired in Connect | "Open Vuzix Connect and pair your glasses" |
| `isConnected()` false | Glasses off, asleep or out of range | "Turn the glasses on" |
| `isControlledByMe()` false after a request | Another app holds the display, or the request failed | Ask the user to retry; do not loop |

The README warns that the SDK "may not be available for immediate use" and can become unavailable later, so observe
`getAvailable()` instead of checking once.

```kotlin
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri

const val VUZIX_CONNECT = "com.vuzix.connect"

fun isConnectInstalled(context: Context): Boolean = try {
    context.packageManager.getPackageInfo(VUZIX_CONNECT, 0)
    true
} catch (e: PackageManager.NameNotFoundException) {
    false
}

/** Opens Vuzix Connect (to pair the glasses) or its store page when it is missing. */
fun openConnect(context: Context) {
    val intent = context.packageManager.getLaunchIntentForPackage(VUZIX_CONNECT)
        ?: Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=$VUZIX_CONNECT"))
    context.startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
}
```

## Lifecycle

- `UltraliteSDK.get(context)` returns the SDK instance; pass the application context and keep one owner per process
  (an application-scoped object or your foreground service), not an Activity.
- All status getters return `LiveData`. Observe on the main thread (a `LiveData` rule). In UI code use
  `observe(lifecycleOwner, ...)`; in a service use `observeForever` and remove the observer yourself.
- Session start (user action): observe `getConnected()` and `getControlledByMe()`, then `requestControl()` when
  connected. Configure layout, font and canvas only when `getControlledByMe()` emits `true`.
- Session end: `removeEventListener`, `releaseControl()`, then remove observers about 500 ms later so the final
  "control lost" value still reaches you (the pattern the official sample uses).
- Control lost mid-session (`getControlledByMe()` emits `false`): drop your text ids, tell the user, and request again
  only on their next action.
- Long sessions with the phone locked: keep your process alive with a foreground service of the type that matches
  your work (for captions from the phone microphone that is usually `microphone`). The SDK talks to Connect over IPC,
  so it should keep working while both processes live (unverified on hardware). Nobody has published a measured
  answer yet; see [Android #3](https://github.com/Vuzix/ultralite-sdk-android/issues/3) (open, 2026-11-07).
- `getBatteryStatus()` contains `null` while the glasses are not connected (Javadoc). Null-check every emission.
- `getName()` and `getModelIdentifier()` (1.8+) identify the linked glasses; `getModelIdentifier()` is `null` when
  nothing is linked.

## Threading

The Javadoc does not say on which thread `EventListener` callbacks or `LiveData` updates arrive, or whether draw
calls block. Treat them as follows:

- Post to the main thread before touching UI from an `EventListener` callback (cheap insurance).
- Short text updates (`updateText` + `commit`) from the main thread are fine for captions.
- Render bitmaps (for `drawBackground` or `LVGLImage.fromBitmap`) on a worker thread.
- Use `commit(CommitCallback)` or `requestAcknowledgement(AcknowledgedCallback)` (1.3+) when you need to know that
  the glasses received a frame, for example to measure latency or to pace caption updates.

```kotlin
import android.util.Log
import com.vuzix.ultralite.UltraliteSDK

fun commitAndMeasure(sdk: UltraliteSDK) {
    val sentAt = System.nanoTime()
    // CommitCallback has a single method, done(), so a Kotlin lambda works (SAM conversion)
    sdk.getCanvas().commit { Log.d("Z100", "on glasses after ${(System.nanoTime() - sentAt) / 1_000_000} ms") }
}
```

## Release builds

The SDK documents no R8 or ProGuard rules. If a minified build stops reaching the glasses while the debug build
works, add this as insurance (unverified, not an official rule):

```proguard
-keep class com.vuzix.ultralite.** { *; }
```

## Battery and screen

- `setLayout(layout, timeout, ...)`: `timeout` in seconds, `0` keeps the display on. Prefer a short timeout (for
  example 30 s); new content wakes the display (Javadoc for `onDisplayOn`).
- `screenOff()` blanks the display now; it needs control. MentraOS found it also had to wake the display before every
  later render on Android ([MentraOS #4120](https://github.com/Mentra-Community/MentraOS/pull/4120), 2026-09-20), so call
  `screenOn()` before the next draw after a `screenOff()`.
- `releaseControl()` at the end returns the glasses to notification mode and lets them sleep normally.
