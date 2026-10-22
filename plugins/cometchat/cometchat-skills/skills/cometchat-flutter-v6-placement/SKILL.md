---
name: cometchat-flutter-v6-placement
description: "Where CometChat chat lives in a Flutter app and how to wire each shape — a tab-based app, a chat tab inside an existing app, a full-screen route, a modal / bottom-sheet chat, or an embedded panel. Triggers: 'add a chat tab', 'full screen chat page flutter', 'chat bottom sheet', 'embed chat in my screen', 'build a full chat app in flutter'."
license: "MIT"
compatibility: "Flutter >=3.38.9; cometchat_chat_uikit ^6 (6.1.x, verified 6.1.0)"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat flutter placement layout navigation tabs bottom-sheet v6"
---

> **Ground truth:** every widget below is in `catalogs/flutter-v6.json`. The recipes follow the official guides (`flutter-tab-based-chat` · `multi-tab-chat-ui-guide` · `flutter-conversation` · `flutter-one-to-one-chat`) via `../cometchat-flutter-v6-core/references/docs-map.md`. Sizing follows the ONE mobile standard in `../cometchat-flutter-v6-core/references/layout.md` — change sizing rules THERE, not here.

## Companion skills (read first)
- `cometchat-flutter-v6-core` — install, credentials, `init→login→render`, the golden-path screens. This skill ASSUMES it.
- `cometchat-flutter-v6-components` — the widget catalog these compose.

## Use this skill when
Deciding or wiring WHERE chat lives — either (a) **growing the core surface into the full tab-based app**, or (b) a scoped-down placement: a chat tab in an existing app, a modal/bottom sheet, or an embedded panel. A plain unscoped "add chat" is NOT this skill — that is the core surface in `-core`.

## Prerequisites & install
Covered by core. No new package.

## The one invariant every placement shares
Mobile shows **one screen at a time**, so placement is a NAVIGATION problem, not a column problem:
1. **Bounded height** — every kit list needs `Expanded`/`Flexible` or a fixed height. Unbounded ⇒ exception or a zero-height list.
2. **`Scaffold` + `SafeArea`**, `resizeToAvoidBottomInset` left at `true`.
3. **Round-trip** — everything you push must pop back to the state that opened it.
4. **One init/login gate at the root**, not per screen (core's `lifecycle.md`).

## Placement patterns (BAKED)

**A. Tab-based app (the GROW target — the full app).** Bottom tabs: Chats (`CometChatConversations`) · Users (`CometChatUsers`) · Groups (`CometChatGroups`) · Calls (`CometChatCallLogs`), each pushing the message screen. **Incoming calls need NO widget from you** — once calling is enabled the kit's `CallEventService` presents the incoming-call overlay itself from any tab; you only set `navigatorKey: CallNavigationContext.navigatorKey` on your `MaterialApp` (see `-calls`). Do NOT mount `CometChatIncomingCall` at the root yourself — that plus the kit's own overlay = a double incoming screen. Build from `flutter-tab-based-chat`. Note `hideAppbar: true` on the list widgets when your own `Scaffold` already supplies one, or you get two headers.
```dart
// Tab-based placement: four list components + group details + global search
// Users tab
CometChatUsers(
  hideAppbar: true,
  onItemTap: (user) => Navigator.push(context, MaterialPageRoute(builder: (_) => MessageScreen(user: user))),
)
// Groups tab
CometChatGroups(
  hideAppbar: true,
  onItemTap: (group) => Navigator.push(context, MaterialPageRoute(builder: (_) => MessageScreen(group: group))),
)
// Group details: members + kick/ban/scope built in
CometChatGroupMembers(group: group, hideAppbar: true)
// Global search from conversations list (onSearchTap -> push this screen). Result callbacks are
// onConversationClicked/onMessageClicked — verified against kit 6.1.0 and the live search page
// (DOCS-BACKLOG F3 corrected upstream).
CometChatSearch(
  onConversationClicked: (conv) { Navigator.pop(context); openChat(conv); },
  onMessageClicked: (msg) { Navigator.pop(context); openChat(msg); },
  onBack: () => Navigator.pop(context),
)
```
```dart
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';
import 'package:flutter/material.dart';

class ChatsTab extends StatelessWidget {
  const ChatsTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Chats')),
      body: SafeArea(
        child: CometChatConversations(
          hideAppbar: true,                       // the Scaffold already has one
          onItemTap: (conversation) {
            final entity = conversation.conversationWith;
            Navigator.push(context, MaterialPageRoute(
              builder: (_) => MessageScreen(
                user: entity is User ? entity : null,
                group: entity is Group ? entity : null,
              ),
            ));
          },
        ),
      ),
    );
  }
}
```
> The Calls tab (`CometChatCallLogs`) comes from the **calls barrel** — that screen imports both barrels (`-calls`). Incoming-call presentation is handled by the kit itself; you don't mount an incoming widget at the root.

**B. Chat tab inside an existing app.** Same as (A) but only the Chats tab: drop `CometChatConversations` into your existing tab scaffold. Keep the init/login gate at YOUR app root so chat is ready before the tab is first shown.

**C. Full-screen route.** `Navigator.pushNamed('/chat')` → a `Scaffold` holding the core surface. The simplest placement; nothing extra.

**D. Modal / bottom-sheet chat.** A sheet has no intrinsic height — give it one explicitly, or the list throws.
```dart
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';
import 'package:flutter/material.dart';

void openChatSheet(BuildContext context, User user) {
  showModalBottomSheet(
    context: context,
    isScrollControlled: true,                     // REQUIRED: lets it exceed half-height
    builder: (_) => SizedBox(
      height: MediaQuery.of(context).size.height * 0.9,   // bounded — the kit fills it
      child: SafeArea(
        child: Column(
          children: [
            CometChatMessageHeader(user: user),
            Expanded(child: CometChatMessageList(user: user)),
            CometChatMessageComposer(user: user),
          ],
        ),
      ),
    ),
  );
}
```
> `isScrollControlled: true` + an explicit height are both required; without them the sheet caps at ~half screen and the composer fights the keyboard.

**E. Embedded panel (chat inside a bigger screen).** Give the region a fixed height or a sized flex cell — never let it sit inside an unbounded `SingleChildScrollView`/`Column`. If the host page scrolls, the chat needs its own `SizedBox(height: …)`.

## Choosing
| The ask | Placement |
|---|---|
| "add chat" (unscoped) | NOT here — core surface (`-core`) |
| "build the full chat app" | A — tab-based |
| "add a chat tab" | B |
| "a chat screen/page" | C |
| "popup / floating / sheet chat" | D |
| "chat inside my dashboard screen" | E |

## Common pitfalls (BAKED)
- **Over-delivering the tab app for a plain "add chat"** — that is the core surface, not this.
- **A list with no bounded height** — the most common Flutter failure (`layout.md`).
- **A bottom sheet without `isScrollControlled` + an explicit height.**
- **Two headers** — your `Scaffold` `AppBar` plus the widget's own; set `hideAppbar: true`.
- **Mounting `CometChatIncomingCall` yourself** — unnecessary and causes a double incoming-call screen. The kit presents the overlay automatically once calling is enabled; you only set `CallNavigationContext.navigatorKey` on your `MaterialApp` (`-calls`).
- **A pushed screen with no way back** (`navigation-round-trip`).
- **Re-running init/login per screen** instead of gating once at the root.

## Verify it works
Each placement renders full-size with no unbounded-height exception; item tap pushes and back pops; the composer stays above the keyboard; on the tab app an incoming call surfaces from every tab. Growing beyond this ⇒ `-calls` / `-features`.
