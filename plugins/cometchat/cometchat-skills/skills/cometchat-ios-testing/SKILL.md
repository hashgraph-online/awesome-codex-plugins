---
name: cometchat-ios-testing
description: "Test an iOS app that embeds CometChat — what to mock vs exercise for real, keeping the CometChatSDK off the network in unit tests, waiting out the async init→login gate, and a lean XCUITest smoke. Triggers: 'test cometchat ios', 'unit test chat swift', 'mock cometchatsdk', 'xcuitest for chat', 'how do I test cometchat swift'."
license: "MIT"
compatibility: "CometChatUIKitSwift 5.1.22 + CometChatSDK 4.1.7; Xcode 16+; iOS 15.1+; XCTest / XCUITest"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat ios swift testing xctest xcuitest mock"
---

> **Ground truth:** `CometChatUIKitSwift` 5.1.22 + `CometChatSDK` 4.1.7 (symbols verified vs `catalogs/ios-v5.json`); signatures FETCHED via `cometchat-ios-core/references/docs-map.md`. **The iOS UI Kit docs have no dedicated testing page** — this is the pack's own guidance (tracked DOCS GAP). The kit ships prebuilt view controllers/SwiftUI views; do not assert against their internal view hierarchy.

## Companion skills (read first)
- `cometchat-ios-core` — the init→login→render lifecycle and the credential flow these tests exercise.

## Use this skill when
Adding tests around a CometChat iOS integration, or a "how do I test this" question. NOT part of a normal build — only when tests are explicitly requested (`RULES.md` → Verification scope).

## Decide what you are testing
Test **your** code, not the kit. Three layers:
- **Your logic** (token fetch, UID mapping, view-model state, routing) → `XCTest` in isolation, keep the SDK off the network.
- **Your wiring** (the chat screen appears after init+login; the right IDs are passed) → a host-app test that drives the launch hook.
- **The real round-trip** (send → receive) → a thin `XCUITest` against a test app, not a unit test.

Do not unit-test that the kit's message list renders — that is the kit's own surface.

## Keep the SDK off the network in unit tests
Put your CometChat calls behind a protocol your view-models depend on, and inject a fake in tests:
```swift
protocol ChatAuthing { func login(authToken: String) async throws -> String }   // returns uid
final class FakeChatAuth: ChatAuthing { func login(authToken: String) async throws -> String { "u1" } }
```
Test your token-fetch, error handling, and UID mapping against `FakeChatAuth` — no real `CometChatUIKit.login`, no network, no Auth Key in the test target. Injecting the real implementation only in the app keeps unit tests fast and hermetic.

## The init→login gate in host-app tests
The chat screen mounts only after `initFromSettings` + `login` resolve (both async). A test that asserts immediately after presenting the screen races the gate — wait for a stable, YOUR-owned element (a title, an accessibility identifier you set), with an expectation/timeout, not a fixed sleep:
```swift
let list = app.otherElements["conversationsScreen"]   // an identifier YOU set on your container
XCTAssertTrue(list.waitForExistence(timeout: 20))
```
Set `accessibilityIdentifier`s on your own containers so UI tests have stable anchors that survive kit updates.

## XCUITest smoke
One high-value path against a **real test app** (seeded users; a test-only Auth Key supplied via the scheme's env, never the release config): launch, sign in, assert the conversation screen appears and a message can be sent. Assert on your accessibility identifiers and visible text — never the kit's internal view tree. Keep it to the happy path + one auth-failure path.

## Not worth automating
Kit view internals, exhaustive option matrices, live calls/VoIP push (device- and entitlement-dependent), and screenshot snapshots of kit UI (they churn across kit versions). Spend the budget on your token flow, UID mapping, and the init-gate wiring.

## Common pitfalls
1. **Fixed `sleep()` instead of `waitForExistence`** — flaky against the async init gate.
2. **Asserting on kit view internals** — brittle; anchor on your own `accessibilityIdentifier`s.
3. **A real login (and Auth Key) in the unit-test target** — hide it behind a protocol + fake; keep secrets out of tests.
4. **Testing on the release configuration** — use a test scheme whose env carries the dev Auth Key, so production stays token-only.

## Verify it works
Unit tests pass with a fake auth (no network, no Auth Key in the target) · a host-app/UI test waits out the init gate and finds your identified container · the XCUITest smoke signs in and shows conversations against a test app · no test asserts a kit-internal view.
