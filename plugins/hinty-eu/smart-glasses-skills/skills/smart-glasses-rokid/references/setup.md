# Setup: SDK, companion app, permissions

Last checked: 2026-11-08. Verification: docs-only. Versions come from Rokid's SDK overview and the Maven metadata
read today; artifact facts (dependencies, ABIs, manifest, consumer rules) were read from the published
`client-l` 1.1.2 POM and AAR. Rokid publishes no licence for the SDK: depend on it from Rokid's Maven, never copy
its files into your repository.

## Which artifact

| Artifact | Role | Versions on Maven (2026-11-08) |
|---|---|---|
| `com.rokid.cxr:client-l` | CXR-L, phone side | release **1.1.2**; also `1.2.X-SNAPSHOT` (updated 2026-11-05) |
| `com.rokid.cxr:cxr-service-bridge` | CXR-S, glasses side; also a transitive dependency of client-l | release 1.8 (2026-10-30) |
| `com.rokid.cxr:client-m` | CXR-M, phone side, business only | 1.2.2 (2026-10-23) |

Use `client-l:1.1.2`. Snapshots change under you; our notes on the 1.2 snapshot (read from the binary, not from docs)
show a higher minimum Hi Rokid version and a changed `SessionConfig` constructor, so treat 1.2 as unreleased.

Changelog points that matter (CXR-L 1.1.2, 2026-09-08, from the SDK overview):
- the phone never connects to the glasses directly; everything goes through the Rokid AI App (Hi Rokid);
- session creation and connection are separate, with five states: Idle, Starting, Started, Paused, Terminating;
- permissions are scoped (`GlassPermission`);
- audio is PCM 16 kHz / mono / 16-bit, photos are WebP;
- the first `CUSTOM_VIEW` session no longer hits `LINK_TIMEOUT`;
- `CUSTOM_APP` can auto-install your glasses APK on connect (`glassesApkPath`);
- the sample was rewritten as `CxrlSample`; iOS moved to `RGCxrClient` 1.1.1.1 (CocoaPods trunk has 1.1.1, see iOS below).

Code written for 1.0.x (`CxrLink`, `CXRSessionType.CUSTOMVIEW`, `onCXRLConnected`) is the old API, still found in old
blog posts and community mirrors with "minSdk must be >= 31". The current quick start (English and Chinese, 1.1.2)
uses `CxrSessionManager` and says minSdk >= 28.

## Gradle

Kotlin DSL is in `SKILL.md`. Groovy, for projects whose repositories live in the root `build.gradle`
(React Native, older Android projects):

```groovy
// build.gradle (root)
allprojects {
    repositories {
        exclusiveContent {
            forRepository { maven { url = uri("https://maven.rokid.com/repository/maven-public/") } }
            filter { includeGroup("com.rokid.cxr") }
        }
    }
}
// app/build.gradle
dependencies { implementation("com.rokid.cxr:client-l:1.1.2") }
```

`exclusiveContent` keeps every other dependency off Rokid's server. Rokid's own quick start uses a plain
`maven { url = ... }` block; both resolve.

What the 1.1.2 POM pulls in: `cxr-service-bridge` as a **timestamped snapshot** (`1.0-20260715.121510-107`, resolved
from the `1.0-SNAPSHOT` folder of the same repository), `kotlin-stdlib` 1.9.0, `kotlinx-coroutines-android` 1.9.0
and `gson` 2.10.1. If Rokid ever purges old snapshot builds, a clean CI cache breaks; keep the Gradle cache or mirror
the artifact in a private repository you control (do not commit it).

## Native libraries and ABIs

The bridge AAR ships five native libraries for `arm64-v8a` and `armeabi-v7a` only, no `x86` or `x86_64`.

- Real phones are fine. x86 emulator builds install, but session creation loads the libraries and throws
  `UnsatisfiedLinkError`. Check `Build.SUPPORTED_ABIS` before offering the feature and catch `Throwable` around
  `CxrSessionManager.create()`.
- If you set `abiFilters`, keep both ARM ABIs.

## Manifest and permissions

- The AAR manifest declares `minSdkVersion 28` and `<queries>` for `com.rokid.sprite.aiapp` and
  `com.rokid.sprite.global.aiapp`. Manifest merge adds them to your app; you need nothing else for package visibility.
- It declares no permissions. Rokid's sample app declares `BLUETOOTH`, `BLUETOOTH_ADMIN`, `BLUETOOTH_CONNECT`,
  `BLUETOOTH_SCAN` and a required `android.hardware.bluetooth` feature. Hi Rokid owns the Bluetooth link, and we
  found no Bluetooth calls in client-l, so the library itself should not need them (unverified on hardware). If you
  copy the sample's list, do not copy `required="true"` for the Bluetooth feature: it hides your app on Play for
  devices without Bluetooth.
- No `INTERNET` permission is needed for CXR-L itself; it talks to Hi Rokid over Android IPC.

## R8 and logging

The AAR ships consumer rules that keep its session API and add:

```
-assumenosideeffects class android.util.Log { public static int d(...); public static int v(...); }
```

That rule applies to your whole app in minified builds: **every `Log.d` and `Log.v` disappears**. Use `Log.i` or
your own logger for glasses diagnostics.

The bridge AAR ships an empty rules file, yet its classes are called from native code. If your release build crashes
while creating a session, add broad keep rules to your own `proguard-rules.pro`:

```
-keep class com.rokid.cxr.** { *; }
-keep interface com.rokid.cxr.** { *; }
-keep class com.rokid.sprite.aiapp.externalapp.** { *; }
-dontwarn com.rokid.**
```

## Hi Rokid, the companion app

| Build | Package | Where |
|---|---|---|
| Global (EU, US, rest of world) | `com.rokid.sprite.global.aiapp` | [Google Play](https://play.google.com/store/apps/details?id=com.rokid.sprite.global.aiapp), versions shown as `G1.x.y` |
| China ("Rokid AI App") | `com.rokid.sprite.aiapp` | Chinese app stores |
| iPhone | "Hi Rokid - Rokid Glasses", Rokid International Limited | [App Store](https://apps.apple.com/us/app/id6749669942), 1.16.0 on 2026-10-30, iOS 16+ |

The App Store also lists an older app called "Rokid" (id6478204777, Shanghai Lingban) for Rokid's tethered AR
glasses. It is not the companion for Rokid Glasses.

Prerequisites your onboarding must check or explain:
1. Hi Rokid installed with versionCode 10110000 (1.11.0) or newer for client-l 1.1.2 (the constant in the artifact;
   the docs note that the SDK's own message prints a lower minimum, a known flaw). `checkRokidAppCompatibility()`
   returns `Compatible`, `VersionTooLow` or `NotInstalled` (the last two carry a download URL).
2. The user is signed in to Hi Rokid. When not signed in, authorisation fails with `NOT_AUTHENTICATED`.
3. The glasses are connected inside Hi Rokid.
4. Hi Rokid is allowed to run in the background (battery optimisation off on phones that kill background apps).

### Global vs China

Early community wrappers exist because client-l 1.0.1 and 1.0.2 only knew the China package, so EU and US units
could not connect: [TakanariShimbo/CxrGlobal](https://github.com/TakanariShimbo/CxrGlobal) and the fork
[Anezium/CxrGlobal](https://github.com/Anezium/CxrGlobal) bind to Hi Rokid's service directly with an explicit
package. Their READMEs still say the official SDK is hard-coded to China.

That is no longer true: the published 1.1.2 artifact contains the Global package in its authorisation and connection
code (checked 2026-11-08). In our reading of it:
- `requestAuthorization` checks the China build first and uses the Global build when the China build is missing or
  too old, and remembers the choice **in memory for the current process**. That is why you authorise again after
  every process start before `connect`.
- If both builds are installed and the China build is new enough, the China build wins.

When to still look at CxrGlobal: only if the official path fails on a specific Hi Rokid build and you need to bind to
a chosen package. The Anezium fork adds the `auth_package` extra that newer Global builds require
([claude-mobile-hud #4](https://github.com/TakanariShimbo/claude-mobile-hud/issues/4), Hi Rokid G1.12.10).
It relies on undocumented action names and has no licence file, so read it, do not vendor it.

## Authorisation details

- Scopes: `GlassPermission.CAMERA`, `MICROPHONE`, `MEDIA`, `DEVICE_MANAGE` (the docs say external developers
  usually do not need `DEVICE_MANAGE`). Ask only for what you use.
- `requestAuthorization(activity, scopes) { result -> }` either answers at once (already granted) or opens Hi Rokid's
  consent screen and answers after `parseAuthorizationResult(resultCode, data)`, which you call from
  `onActivityResult`. Rokid's sample forwards every activity result; the SDK picks its own request codes.
- If no compatible Hi Rokid is installed, the callback may never fire. Check compatibility first and add a timeout.
- Rokid's sample keeps the token in memory only; the docs say to use the Android Keystore if you persist it.
- Hi Rokid may ask the user to trust an "unverified" app the first time (community report,
  [ARDings/RokidAIGlassesUnityBridge](https://github.com/ARDings/RokidAIGlassesUnityBridge)). Mention it in onboarding.
  The iOS Hi Rokid 1.14.0 release notes add "third-party app permission management".

## Credentials and registration

- Android, CXR-L: no app key, client secret, device licence file or Rokid review appears in the docs (as of 2026-11-08).
- CXR-M (not this skill): business onboarding through `Glasses.BD@rokid.com`; community projects that use it store a
  client secret and a per-device SN file.

## iOS

As of 2026-11-09 the CXR-L doc set covers iOS, and the SDK overview and Rokid's sample project use
`pod 'RGCxrClient', '1.1.1.1'`.
- `RGCxrClient` 1.1.1 (2026-08-27) is on public CocoaPods trunk, published by a Rokid account
  ([trunk API](https://trunk.cocoapods.org/api/v1/pods/RGCxrClient)); its podspec says "Copyright 2026 Rokid", iOS 13+,
  and excludes arm64 simulators. Version 1.1.1.1 needs Rokid's private CocoaPods specs source; the alternative is the
  source modules inside Rokid's iOS sample (`CXRClientDemo.zip`, linked from the CXR-L docs).
- Flow: `CxrClient.makeLink(appDisplayName:)` (a class method), `authenticate(scopes:)`, then a custom view session;
  forward the auth callback URL with `CxrClient.shared.handleOpenURL(url)`. The overview describes the iOS state
  machine as available / started / paused / unavailable.
- Info.plist (community, [fasaiph/rokid-cxr-glasses](https://github.com/fasaiph/rokid-cxr-glasses)): a URL type for the
  auth callback, `LSApplicationQueriesSchemes` with `rokidai`, a Bluetooth usage string and the `bluetooth-central`
  background mode.
- The same project reports the pods have no Apple Silicon simulator slice: keep a device-only target for the SDK.
- After a process restart the stored auth is not restored; authenticate again
  ([rokid/community #19](https://github.com/rokid/community/issues/19), open).
- Registration: the docs ask for a registered Rokid developer account plus bundle ID and URL scheme; the community
  project above says auth worked with an arbitrary app name and no registration. Unverified.
