---
name: cometchat-flutter-v6-testing
description: "Test a Flutter app that uses the CometChat UI Kit — what is worth testing versus what belongs to the kit, mocking the SDK boundary, widget tests around chat screens, and integration/CI setup. Triggers: 'test my cometchat integration', 'mock cometchat in flutter tests', 'widget test chat screen', 'cometchat test setup'."
license: "MIT"
compatibility: "Flutter >=3.38.9; cometchat_chat_uikit ^6 (6.1.x, verified 6.1.0); flutter_test / integration_test"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat flutter testing widget-test mocks integration ci v6"
---

> **Ground truth:** kit symbols are catalog-verified against 6.1.0. Test tooling (`flutter_test`, `integration_test`, `mocktail`) is standard Flutter, not CometChat API.

## Companion skills (read first)
- `cometchat-flutter-v6-core` — install, credentials, `init→login→render`. This skill ASSUMES it.
- `cometchat-flutter-v6-patterns` — how init/login is gated, which is what your tests have to work around.

## Use this skill when
The user ASKS for tests. **Building a feature does not imply writing tests** (`RULES.md`) — do not volunteer a test suite as part of "add chat".

## Prerequisites & install
```bash
flutter pub add --dev mocktail integration_test
```
`flutter_test` ships with Flutter.

## Test the RIGHT boundary (the thing most people get wrong)
Do **not** test the UI Kit. `CometChatConversations` rendering a list, `CometChatMessageList` appending a message, receipts, typing — all CometChat's own tested surface. Asserting on the kit's internals produces slow tests that break on every kit upgrade and prove nothing about YOUR app.

Test what is **yours**:
| Worth testing | Why |
|---|---|
| The init/login **gate** | Your logic. Does a chat route stay unreachable until login resolves? |
| **Navigation wiring** | `onItemTap` pushes the right screen with the right `user`/`group`. |
| **Target plumbing** | The thread screen receives `parentMessageId` **and** the same user/group — the silent-never-sends trap. |
| **Config selection** | Prod flavour has no Auth Key; the right App ID per flavour. |
| **Your own slots** | Custom `listItemView` / `subtitleView` widgets render as expected. |
| **Error paths** | `onError` surfaces something to the user instead of a blank screen. |

## Widget tests — the practical constraint
A CometChat widget expects an initialized, logged-in SDK. In a unit/widget test there is none, so:
- **Test your screens' STRUCTURE and wiring**, not the kit's rendered output. Pump your screen and assert your own widgets, callbacks, and navigation.
- **Keep chat screens behind a thin seam you can substitute** — a factory/builder your test can swap for a stub. This is the single change that makes a CometChat app testable.
- **Do not try to "mock the UI Kit widgets"** — they are concrete widgets, not injectable interfaces. Swap at YOUR seam instead.

```dart
// A seam: your screen depends on a builder, so tests substitute a stub for the kit widget.
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';
import 'package:flutter/material.dart';

typedef ConversationsBuilder = Widget Function(void Function(Conversation) onTap);

class ChatsScreen extends StatelessWidget {
  final ConversationsBuilder builder;
  final void Function(Conversation) onOpen;
  const ChatsScreen({super.key, required this.builder, required this.onOpen});

  @override
  Widget build(BuildContext context) => Scaffold(body: SafeArea(child: builder(onOpen)));
}

// production wiring
Widget realConversations(void Function(Conversation) onTap) =>
    CometChatConversations(onItemTap: onTap);
```
In the test, pass a builder returning a plain `ListView` and assert that tapping a row calls `onOpen` with the right conversation — that is YOUR logic, tested fast and without a network.

## Integration tests (`integration_test`)
The only place a real end-to-end chat flow can be asserted, because it needs a real init/login.
- Use a **dedicated test CometChat app** and seeded users (`cometchat-uid-1…`), never production data.
- Credentials come from the test flavour's settings asset, generated in CI — do not commit them.
- Keep the suite small: sign in → open a conversation → send a message → assert it appears. Broad E2E over the kit's own surface is slow and re-tests CometChat.
- Some things **cannot** be automated here and should be stated rather than faked: **push delivery** and **real calls** need physical devices.

## CI
Run `flutter analyze` + unit/widget tests on every PR — they need no credentials. Gate integration tests behind a job that has the test-app secrets, and let them be non-blocking if the environment is flaky; a red build from a missing fixture teaches people to ignore CI.

## Common pitfalls (BAKED)
- **Writing tests nobody asked for** (`RULES.md`).
- **Testing the UI Kit** instead of your wiring.
- **Trying to mock kit widgets directly** — introduce a seam instead.
- **Widget-testing a screen that calls `init`/`login`** → hangs or throws; gate it behind the seam.
- **Integration tests against production** — use a test app.
- **Committing test credentials.**
- **Claiming push/calls are covered** when they need real devices.

## Verify it works
Unit/widget tests run with no network and no credentials; integration tests pass against the test app; `flutter analyze` is clean; nothing in the suite asserts on CometChat's internal rendering.
