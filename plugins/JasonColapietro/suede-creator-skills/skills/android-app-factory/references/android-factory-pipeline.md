# Android Factory Pipeline

## Phase Map and Evidence

| Phase | Required artifact | Exit evidence |
| --- | --- | --- |
| Product | `product/brief.md` with user, core outcome, demand evidence, non-goals | one testable v1 outcome and owner approved |
| Policy | copied release gate + dated official-source receipt | target SDK/form factor and applicable declarations identified |
| Architecture | architecture/data/threat-model note | boundaries, state, data, permissions, failure modes, test seams agreed |
| Scaffold | Gradle Kotlin DSL Android project | debug build and tests run in named environment |
| Core loop | complete vertical slice | deterministic demo/real flow passes on device matrix |
| Quality | test report, accessibility notes, benchmark/profile results | no launch-critical failures; release build verified |
| Trust | data inventory, privacy/deletion evidence, SDK audit | code/runtime/Console answers reconcile |
| Billing | entitlement state model and test receipt, or explicit N/A | purchase lifecycle proven on Play test track |
| Store | listing, icon, feature graphic, screenshots, support/privacy URLs | claims match release build; asset/character checks pass |
| Release | signed AAB, Play App Signing and track evidence | explicit upload/promotion approval and staged rollout plan |
| Observe | monitoring and rollback record | crash/ANR/core-task/billing owners and thresholds active |

Keep artifacts in the app repo, not inside this installed skill. Paths are
suggestions; adapt them to the project without losing evidence.

## Human Touchpoints

Pause for confirmation before any external mutation at least at:

1. application ID and Play app creation;
2. product scope, target devices, and data/permission posture;
3. icon/brand direction and published statements;
4. Billing product/base-plan/offer creation or pricing change;
5. privacy policy, Data Safety, account deletion, target audience, content
   rating, ads, and restricted-permission declarations;
6. signing credential use or Play API/service-account use;
7. AAB upload, track promotion, rollout percentage change, halt, resume, and
   full production release.

Local code and artifact generation do not authorize a Play Console mutation.

## Product and ASO Discovery

Use search terms, competitor listings, support pain, reviews, existing audience,
and first-party product data to shape the opportunity. Record source, region,
language, date, and evidence limits. Do not call a phrase "winnable" from an
autocomplete result or infer volume/difficulty without a dated source that
defines those metrics. `suede-aso` owns keyword research and listing
optimization; run it here so the product name and core loop match how people
search, not after the build.

The product brief must include:

- target user and job;
- current alternative and pain;
- core loop and activation event;
- reason to return;
- offline/account/sync expectation;
- accessibility and form-factor needs;
- monetization hypothesis or free-v1 rationale;
- risk/data/permission inventory;
- v1 non-goals and success metrics.

## Scaffold and Build

Use an Android application module, not a Kotlin/JVM `main()` module. Native
Kotlin + Jetpack Compose is the default; a Trusted Web Activity, Capacitor, or
other wrapper must be an explicit product choice with offline, navigation,
policy, performance, accessibility, and store-value risks assessed.

For a general phone/tablet build on the 2026-10-23 baseline, target API 36:

```kotlin
android {
    namespace = "com.example.product"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.example.product"
        minSdk = 24 // choose from product/device evidence
        targetSdk = 36
        versionCode = 1
        versionName = "1.0.0"
    }
}
```

Pin current stable toolchain/library versions in a version catalog, check the
Android 16 behavior-change migration, and commit Gradle wrapper files but not
machine-local SDK paths or credentials.

Prove each rung before adding the next:

```bash
./gradlew tasks
./gradlew testDebugUnitTest lintDebug assembleDebug
./gradlew connectedDebugAndroidTest
./gradlew assembleRelease bundleRelease
```

Use actual repo tasks when names differ. Record skipped device tests explicitly.

## Core Loop Definition

A vertical slice is not only a happy-path screen. It includes:

- launch/deep-link entry and navigation;
- loading, empty, success, validation, recoverable error, terminal error, and
  offline/stale state as applicable;
- state restoration after rotation/window change, background, and process loss;
- accessibility semantics, focus, large text, and adaptive layout;
- deterministic test data or a verified live backend contract;
- telemetry needed to detect core-task failure without collecting unnecessary
  personal data.

Read `architecture-and-quality.md` before declaring the loop complete.

## Store Listing and Assets

Recheck current Play Console limits before final generation. On the dated
baseline, common listing fields are:

- app name: 30 characters;
- short description: 80 characters;
- full description: 4,000 characters;
- feature graphic: 1024×500 pixels;
- phone screenshots: at least the Play-required count and within current
  dimension/aspect rules; provide only declared form-factor sets.

Play has no Apple-style hidden keyword field. Write natural, truthful copy that
explains the user outcome. Do not stuff repeated search terms, manufacture
awards/reviews, claim "#1," or show unshipped UI.

Asset gate:

- screenshots come from the release candidate or an accurately localized
  deterministic build;
- text remains legible on store surfaces and does not misrepresent system UI;
- login, purchase, permission, and account requirements are not concealed;
- every declared device/form factor has a real supported experience;
- support email/site, privacy policy, deletion URL, and reviewer instructions
  work without privileged internal access;
- reviewer credentials are temporary, least-privileged, and shared only through
  the designated Console field.

Official listing guidance:
<https://support.google.com/googleplay/android-developer/answer/9859152>

## Signing and Artifact Integrity

- Enroll the production app in Play App Signing.
- Keep the upload keystore and passwords outside the repo and normal handoffs.
- Use a distinct upload key; document ownership, recovery, rotation, and backup
  without exposing material.
- Build an Android App Bundle (`.aab`) for Play distribution.
- Verify package ID, version code/name, target SDK, supported ABIs, permissions,
  exported components, debuggable/profileable state, signing certificate, and
  release shrinker behavior from the actual artifact.
- Inspect the final artifact for native libraries and prove 16 KB page-size
  compatibility for Android 15+ targets in both tooling and a 16 KB test
  environment; confirm the Play release detail.
- Preserve mapping/native debug symbols according to crash tooling and Console
  requirements without publishing secrets.

Example inspection tools depend on the installed SDK/toolchain:

```bash
./gradlew bundleRelease
bundletool validate --bundle app-release.aab
apkanalyzer manifest permissions app-release.apk
apksigner verify --print-certs app-release.apk
```

If an APK is needed for inspection, generate it from the AAB with `bundletool`
under a controlled signing/test setup. Do not claim AAB signature verification
from an APK that came from a different build.

## Test Tracks and Production Rollout

Recommended progression:

1. local/emulator and physical-device matrix;
2. Play internal app sharing or internal testing for delivery/signing behavior;
3. closed testing with representative users and license testers;
4. open testing only when product/support/privacy posture permits;
5. staged production rollout with named health metrics and halt authority;
6. full rollout only after the observation window passes.

At each Play rung, inspect install/update, App Bundle delivery, pre-launch report,
Android vitals, review/access behavior, Billing, Data Safety/listing rendering,
and crash/ANR/core-task telemetry. Passing review is not proof that the app is
correct or policy-complete.

## Release Gate Output

Return:

```text
Repo/branch:
Package / Play app / version code:
Target track and rollout:
Policy checked at + URLs:
16 KB page-size / developer verification evidence:
Build/test/device matrix:
Accessibility evidence:
Performance/profile evidence:
Privacy/Data Safety/account deletion reconciliation:
Billing/Integrity evidence or N/A rationale:
Listing/assets evidence:
Signing/secret scan:
Console/pre-launch evidence:
User confirmation for external mutation:
Gate: ship | ship-with-caveats | hold
Blockers/caveats with owner:
Exact next step:
```
