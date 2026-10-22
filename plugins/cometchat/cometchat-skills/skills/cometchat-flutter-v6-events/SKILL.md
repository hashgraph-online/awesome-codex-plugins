---
name: cometchat-flutter-v6-events
description: "React to CometChat activity in a Flutter app — SDK listeners (messages, calls, users, groups, connection) versus UI Kit events (CometChatMessageEvents, CometChatGroupEvents, CometChatUserEvents, CometChatConversationEvents), and the listener lifecycle that keeps them from leaking. Triggers: 'listen for new messages', 'react when a message is sent', 'cometchat listener flutter', 'unread badge count', 'onMessageReceived'."
license: "MIT"
compatibility: "Flutter >=3.38.9; cometchat_chat_uikit ^6 (6.1.x, verified 6.1.0); cometchat_sdk ^5.0.6"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat flutter events listeners sdk uikit lifecycle v6"
---

> **Ground truth:** every listener symbol below is catalog-verified against 6.1.0. There are TWO event systems and they are not interchangeable — the exact callback set for each is FETCHED from `events` (UI events) and the SDK's `real-time-listeners` via `../cometchat-flutter-v6-core/references/docs-map.md`.

## Companion skills (read first)
- `cometchat-flutter-v6-core` — install, credentials, `init→login→render`. This skill ASSUMES it.

## Use this skill when
"do something when a message arrives", "update a badge count", "refresh my screen when a group changes", "cometchat listener" — anything reactive OUTSIDE what the kit's widgets already do for themselves.

## Prerequisites & install
Covered by core. No new package.

## First: do you actually need a listener?
The kit's widgets are already live. `CometChatConversations` updates its own unread counts, `CometChatMessageList` appends incoming messages, `CometChatMessageHeader` shows typing and presence — **all without a single listener from you.** Add one only for something OUTSIDE the kit's surface: an app-level badge, an analytics hook, a push registration, navigating on an incoming call.
> Adding a listener to "make the list update" is the most common mistake here — it already does.

## The two systems (BAKED)
| | **SDK listeners** | **UI Kit events** |
|---|---|---|
| Source | the server, via `CometChat.*` | the kit's own widgets |
| Register | `CometChat.addMessageListener(id, this)` | `CometChatMessageEvents.addMessagesListener(id, this)` |
| Mixin | `MessageListener` · `CallListener` · `UserListener` · `GroupListener` · `ConnectionListener` | `CometChatMessageEventListener` · `CometChatGroupEventListener` · `CometChatUserEventListener` · `CometChatConversationEventListener` |
| Answers | "the server says X happened" | "the user did X in the kit" |
| Use for | badges, push, incoming calls, analytics | reacting to a kit action (message sent from the composer, group left via the kit) |

**SDK listener — server-side truth:**
```dart
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';
import 'package:flutter/material.dart';

class BadgeHost extends StatefulWidget {
  const BadgeHost({super.key});
  @override
  State<BadgeHost> createState() => _BadgeHostState();
}

class _BadgeHostState extends State<BadgeHost> with MessageListener {
  static const _id = "app_badge";

  @override
  void initState() {
    super.initState();
    CometChat.addMessageListener(_id, this);
  }

  @override
  void dispose() {
    CometChat.removeMessageListener(_id);   // ALWAYS remove — see lifecycle below
    super.dispose();
  }

  @override
  void onTextMessageReceived(TextMessage message) {
    // bump an app-level unread badge
  }

  @override
  Widget build(BuildContext context) => const SizedBox.shrink();
}
```

**UI Kit event — react to what the kit did:**
```dart
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';
import 'package:flutter/material.dart';

class ComposerWatcher extends StatefulWidget {
  const ComposerWatcher({super.key});
  @override
  State<ComposerWatcher> createState() => _ComposerWatcherState();
}

class _ComposerWatcherState extends State<ComposerWatcher> with CometChatMessageEventListener {
  static const _id = "composer_watch";

  @override
  void initState() {
    super.initState();
    CometChatMessageEvents.addMessagesListener(_id, this);
  }

  @override
  void dispose() {
    CometChatMessageEvents.removeMessagesListener(_id);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => const SizedBox.shrink();
}
```

## The listener lifecycle (the rule that prevents 90% of event bugs)
1. **Register in `initState`, remove in `dispose`** — always paired.
2. **A unique, stable listener id per screen.** Reusing one id across screens means the later registration silently replaces the earlier.
3. **Removing matters more than you think in Flutter:** hot restart and route re-entry both re-run `initState`. A listener you never removed fires again, so a badge double-counts and a call dialog opens twice.
4. **Register AFTER login.** A listener added before `login` resolves receives nothing.

## Do NOT mix both message listeners on one class (compile trap — verified vs 6.1.0)
`MessageListener` (SDK) and `CometChatMessageEventListener` (UI Kit) both declare `onCardMessageReceived`, but with **two different `CardMessage` types** — one from `cometchat_sdk`, one from the kit. Mixing them on the same `State` fails to compile with `invalid_override`. Use **two separate classes** (or two `State`s) when you need both.

## Common pitfalls (BAKED)
- **Adding a listener to make a kit widget update** — it already updates itself.
- **No `dispose` removal** → duplicate events after hot restart / re-entry.
- **A shared listener id** → one screen silently unregisters another.
- **Both message mixins on one class** → does not compile (above).
- **Registering before login** → silence.
- **Expecting UI events for server activity** (or vice-versa) — pick the right system from the table.
- **v5 event APIs** — the v5 `DataSource`/`ChatConfigurator` event plumbing is gone (→ `-migration`).

## Verify it works
The reaction fires once (not twice) per event; hot-restart the app and confirm it still fires exactly once; navigate away and back and confirm no duplicate; with the app backgrounded, server-side events still arrive when it returns.
