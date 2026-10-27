---
name: cometchat-android-v6-testing
description: "Test an Android app that integrates the CometChat v6 UI Kit — make the SDK mockable behind a repository, unit-test the init/login gate and credential hygiene, write instrumented/Compose UI tests for chat screens, and know honestly what can only be checked on a device. Triggers: 'how do I test my cometchat android app', 'mock cometchat in tests', 'compose ui test chat screen', 'unit test cometchat login'."
license: "MIT"
compatibility: "Android minSdk >=28; compileSdk >=36; Kotlin >=2.1; AGP >=8.9.1; JVM target 11; com.cometchat:chatuikit-kotlin-android ^6 OR com.cometchat:chatuikit-compose-android ^6 (6.0.x, verified 6.0.5); com.cometchat:chat-sdk-android ^5; JUnit4 · MockK/Mockito · androidx.test / compose-ui-test"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android testing v6 junit mockk compose-ui-test instrumented"
---

> **Ground truth:** the installed kit's API shape (`CometChatUIKit` static object; `CometChat` static singleton) + `contracts.android-v6.json`. **The UI Kit ships no test doubles or test APIs** — nothing below invents one; the testable seam is code YOU write around the SDK. Verify symbols against catalog `android-v6.json`.

## Companion skills (read first)
- `cometchat-android-v6-core` — install, credentials, `initFromSettings → login → render`, lifecycle, sizing. Assumed here, never repeated.
- `cometchat-android-v6-production` — the release checks these tests protect.

## Use this skill when
"how do we test this?", "mock CometChat in unit tests", "write a UI test for the chat screen", "add CometChat checks to CI", "how do I test login without hitting the network?".

## Prerequisites & install
Standard Android testing stack only — JUnit4, a mocking library (MockK for Kotlin), `androidx.test`/Espresso for Views, `androidx.compose.ui:ui-test-junit4` for Compose. **No CometChat test artifact exists**; don't look for one.

## Test setup — create the seam first
`CometChatUIKit` and `CometChat` are **static singletons**, so they can't be injected or faked directly in a JVM unit test. Wrap the calls your app makes behind a small interface and depend on THAT:
```kotlin
interface ChatSession {
    fun isLoggedIn(): Boolean
    fun login(uid: String, onResult: (Result<User>) -> Unit)
    fun logout(onResult: (Result<Unit>) -> Unit)
}

class RealChatSession : ChatSession {           // the only class that touches the SDK
    override fun isLoggedIn() = CometChatUIKit.getLoggedInUser() != null
    override fun login(uid: String, onResult: (Result<User>) -> Unit) =
        CometChatUIKit.login(uid, object : CometChat.CallbackListener<User>() {
            override fun onSuccess(user: User) = onResult(Result.success(user))
            override fun onError(e: CometChatException) = onResult(Result.failure(e))
        })
    override fun logout(onResult: (Result<Unit>) -> Unit) { /* … */ }
}
```
Your ViewModels/screens take `ChatSession`; unit tests pass a fake. This one wrapper is what makes the rest of this skill possible — without it, "mocking CometChat" means static mocking (`mockkStatic`), which is brittle and should be a last resort.

## Assertions that matter (the ones that catch real defects)
1. **Init resolves before login, login before UI** — with a fake session, assert the gate state machine never exposes the chat screen while init/login are pending, and that an `onError` path produces an ERROR state (not a permanent spinner or a blank screen).
2. **No credentials in source** — a cheap, high-value test/CI check: grep the source set for an Auth-Key-shaped literal and assert none; assert `cometchat-settings.json` is gitignored; for release, assert the packaged assets carry no `authKey` (→ `cometchat-android-v6-production`).
3. **Listener add/remove are paired** — for every `add*Listener(ID, …)` your code makes, assert the matching `remove*Listener(ID)` runs on teardown (fake session records calls; assert balanced). Leaked listeners are the classic Android CometChat bug.
4. **Navigation round-trips** — thread/search/detail screens open AND return (the contract's back-stack rule).
5. **Scoped data requests** — if the app is 1:1-only or groups-only, assert the request builder carries that scope rather than a client-side filter.

## UI tests for chat screens
- **Compose**: `createAndroidComposeRule<YourActivity>()`, then assert on YOUR wrappers/state — a header title, an error/empty state you render, a nav destination. Kit internals have no guaranteed test tags, so **don't assert on kit-internal node structure**; it will break on every kit upgrade.
- **Views**: Espresso against your Activity — assert your own view IDs and the kit view's presence/visibility (`R.id.message_list` displayed), not its internal children.
- Prefer asserting **your integration** (does the right screen show for this user? does back work? does the error state render?) over asserting the kit renders correctly — that's CometChat's job, and it's what the device check below is for.

## E2E + CI (be honest about the boundary)
- **CI can run**: JVM unit tests, the credential-hygiene checks, lint/detekt, an assembleDebug/Release **compile** — plus this pack's Kotlin fence gate (`./gradlew :app:assembleDebug   # in YOUR app (npm run verify:fences:android-v6 is a pack-repo gate)`).
- **CI can run with an emulator** (Gradle managed devices / Firebase Test Lab): instrumented + Compose UI tests against a **seeded test app** (a dedicated CometChat app ID with known users), logging in with a test uid.
- **Cannot be automated meaningfully**: real push delivery (device + Play services — manual), two-party calling (needs two devices/users), and anything gated on Dashboard state. Say so rather than pretending coverage.
- Keep test credentials out of the repo: inject the test app ID/uid via CI secrets → `local.properties`/`BuildConfig`, never committed.

## Common pitfalls
Trying to mock `CometChatUIKit` directly instead of wrapping it · asserting on kit-internal view hierarchy (breaks every upgrade) · unit tests that hit the real backend (flaky + rate-limited) · sharing one test user across parallel runs (state collisions) · no test for the error path (the most common production failure) · committing test credentials · claiming push/calling are covered by CI when they aren't.

## Verify it works
`./gradlew test` (unit, with fakes — no network) and `./gradlew connectedAndroidTest` (instrumented, seeded app) pass; the credential-hygiene check fails loudly when you deliberately plant a key; the fence gate compiles (`./gradlew :app:assembleDebug   # in YOUR app (npm run verify:fences:android-v6 is a pack-repo gate)`). State clearly in your summary which behaviors are covered by tests and which were verified manually on a device (push, calling) — never imply automation you didn't build.
