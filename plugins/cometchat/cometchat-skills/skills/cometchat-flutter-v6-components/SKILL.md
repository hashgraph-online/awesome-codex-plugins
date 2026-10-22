---
name: cometchat-flutter-v6-components
description: "The Flutter v6 UI Kit widget catalog — which drop-in widgets exist, which barrel each comes from, and how to compose or swap them (conversations, messages, users, groups, threads, calling, bubbles). Triggers: 'what cometchat widgets are there', 'customize the message list flutter', 'swap the message bubble flutter', 'add a users list in flutter'."
license: "MIT"
compatibility: "Flutter >=3.38.9; cometchat_chat_uikit ^6 (6.1.x, verified 6.1.0)"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat flutter widgets components uikit catalog v6"
---

> **Ground truth:** `catalogs/flutter-v6.json` — 296 symbols, **compiler-verified** against the published 6.1.0, with `symbolsByBarrel` recording which barrel each resolves from. The lists below are that catalog, grouped. If a name is not in the catalog it does not exist — do not emit it. Props come from the docs `.md` twin (`../cometchat-flutter-v6-core/references/docs-map.md`), never from memory.

## Companion skills (read first)
- `cometchat-flutter-v6-core` — install, credentials, `init→login→render`, the two barrels. This skill ASSUMES it and does not repeat it.

## Use this skill when
Choosing, composing, or swapping UI Kit widgets; "which widgets exist"; customizing a list, message, or bubble.

## Prerequisites & install
Covered by core. This skill adds no package.

## Widget catalog (BAKED closed list — from the catalog)
**Lists & screens:** `CometChatConversations` · `CometChatUsers` · `CometChatGroups` · `CometChatGroupMembers` · `CometChatSearch` · `CometChatNotificationFeed`
**Messages:** `CometChatMessageHeader` · `CometChatMessageList` · `CometChatMessageComposer` · `CometChatThreadedHeader` · `CometChatMessageInformation` · `CometChatMessagePreview` · `CometChatReactions` · `CometChatReactionList` · `CometChatMediaRecorder` · `CometChatEmojiKeyboard` · `CometChatStickerKeyboard`
**Bubbles:** `CometChatTextBubble` · `CometChatImageBubble` · `CometChatVideoBubble` · `CometChatAudioBubble` · `CometChatFileBubble` · `CometChatVoiceNoteBubble` · `CometChatDeletedBubble` · `CometChatActionBubble` · `CometChatMessageBubble` · `CometChatLinkPreviewBubble` · `CometChatPollsBubble` · `CometChatStickerBubble` · `CometChatCollaborativeBubble` · `CometChatStreamBubble` · `CometChatAIAssistantBubble` · `CometChatCallBubble`
**Groups:** `CometChatChangeScope` · `CometChatCreatePoll`
**AI:** `CometChatAISmartRepliesView` · `CometChatAIConversationStarterView` · `CometChatAIConversationSummaryView` · `CometChatAIAssistantChatHistory` · `CometChatAIAssistantEvents`
**Theme primitives:** `CometChatColorPalette` · `CometChatTypography` · `CometChatSpacing` · `CometChatThemeHelper` (→ `-customization`)
> **`CometChatMediaRecorder` and `CometChatEmojiKeyboard` are REAL in Flutter v6** even though they are phantoms in the React pack. Never carry another family's phantom list here — check `catalogs/flutter-v6.json`.
> Plural/singular matters: `CometChatPollsBubble` (not `PollBubble`), `CometChatThreadedHeader` (not `ThreadHeader`). `CometChatImagesBubble`/`CometChatAudiosBubble`/`CometChatFilesBubble`/`CometChatVideosBubble` also exist as the multi-attachment variants — the singular forms are the standard bubbles. **Exception:** `CometChatAudioBubble` is a **deprecated typedef alias** for `CometChatVoiceNoteBubble` (`audio_bubble/cometchat_voice_note_bubble.dart`) — use `CometChatVoiceNoteBubble` (single voice note) or `CometChatAudiosBubble` (multi-attachment) instead; it compiles today but rides a deprecated symbol (AUDIT-233).
> The message-translation bubble is UN-prefixed (`MessageTranslationBubble`); only its style class carries the prefix.

## Calls widgets live in the OTHER barrel (compile trap)
`CometChatIncomingCall` · `CometChatOutgoingCall` · `CometChatOngoingCall` · `CometChatCallButtons` · `CometChatCallLogs` · `CometChatCallBubble` · `CometChatCalls` resolve **only** from:
```dart
import 'package:cometchat_chat_uikit/cometchat_calls_uikit.dart';
```
That barrel does **not** re-export the chat widgets, so a calls screen imports **both**. Detail: `cometchat-flutter-v6-calls`.

## Swap / compose slots
- **Custom UI goes IN a widget's slot, never stacked beside it.** Every list widget exposes `listItemView` (replace the whole row) plus finer slots — `leadingStateView` · `titleView` · `subtitleView` · `trailingView` — and state slots `loadingStateView` / `emptyStateView` / `errorStateView`.
- **Check the parameter ORDER before writing a slot.** v6 slots are not uniform: `CometChatConversations.leadingView` is `(context, conversation)`, while `CometChatMessageHeader.subtitleView` is `(group, user, context)`. Fetch the widget's `.md` twin rather than assuming.
- **Prefer configuring the highest-level widget** over rebuilding it from bubbles.
- **Reuse built-in callbacks before adding your own control** — `onItemTap` · `onItemLongPress` · `onSelection` · `onBack` · `onError` · `onLoad`. Note the arity differs by widget: `CometChatUsers`/`CometChatGroups` take `onItemTap: (context, item)`, while `CometChatConversations`/`CometChatGroupMembers` take `onItemTap: (item)`.
- **Scope data with the request builder**, not a client-side filter: `conversationsRequestBuilder` · `usersRequestBuilder` · `groupsRequestBuilder` · `groupMembersRequestBuilder`.

## Swapping a bubble (message templates)
There is no per-bubble prop on the list — a custom bubble is a `CometChatMessageTemplate` whose `bubbleView` you override. Defaults come from `MessageTemplateUtils` (v6 replaced the v5 `DataSource`; `CometChatUIKit.getDataSource()` is gone).

Which prop you pass it to is NOT interchangeable (`message-list` § Message Templates; `customization-view-slots`; `customization-datasource`):
- `addTemplate:` — **merges with the defaults**. This is the one for a message type of your own.
- `templates:` — **replaces** the whole default set.

Reach for `addTemplate:` for anything the kit does not already ship, and `templates:` only when you deliberately want to drop the defaults. Templates are keyed `category_type`, so an `addTemplate:` entry matching an existing key overrides just that bubble (`customization-datasource`).

Do not try to widen the list's fetch with your own builder: `message-list` states that **`uid`, `guid`, `types` and `categories` on a `MessagesRequestBuilder` are always overridden inside the message list**.

Overriding a type the kit already ships (`templates:`):
```dart
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';
import 'package:flutter/material.dart';

final textTemplate = CometChatMessageTemplate(
  type: CometChatMessageType.text,
  category: CometChatMessageCategory.message,
  bubbleView: (message, context, alignment) =>
      message is TextMessage ? Text(message.text) : const SizedBox.shrink(),
);
```

Adding a type of your own (`addTemplate:`):
```dart
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';
import 'package:flutter/material.dart';

final diceRollTemplate = CometChatMessageTemplate(
  type: 'game_roll',                              // your own type string
  category: CometChatMessageCategory.custom,      // CustomMessage is always `custom`
  bubbleView: (message, context, alignment) => Text(
      message is CustomMessage ? '${message.customData?['value']}' : ''),
);

Widget gameChat(Group group) => CometChatMessageList(
      group: group,
      addTemplate: [diceRollTemplate],   // `templates:` here would render nothing
    );
```

## Creating a group (host-composed — no kit widget)
v6 ships no create-group widget; build the form yourself and create with the SDK. It MUST offer all **three** types — Public · Private · **Password-protected** — with the password field required for the third.
```dart
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';

Future<void> createGroup(String guid, String name, String? password) async {
  final group = Group(
      guid: guid, name: name, type: CometChatGroupType.password, password: password);
  // NOTE: `group:` is a NAMED parameter, and onSuccess/onError are both required.
  await CometChat.createGroup(group: group, onSuccess: (g) {}, onError: (e) {});
}
```

## Common pitfalls (BAKED)
- **Emitting a widget that isn't in the catalog** — the #1 hallucination. Check first.
- **Importing a calls widget from the chat barrel** — does not compile (see above).
- **Assuming a slot's parameter order or arity** — v6 is inconsistent between widgets; fetch the twin.
- **Stacking custom UI beside a widget** instead of passing it into the slot.
- **Emitting a widget below its `contracts.flutter-v6.json` minimum** — a group-details screen needs view/kick/ban/scope, not just a member list.
- **Hand-rolling moderation or report UI** — both are automatic in `CometChatMessageList`.
- **v5 shells** (`CometChatConversationsWithMessages`, `CometChatMessages`, `CometChatUI`, `CometChatUserList`) — all removed; the host composes screens (→ `-migration`).

## Verify it works
The widget renders and its data populates. Empty ⇒ confirm `init` + `login` completed before the screen built (core's gate), and that any list has a bounded height (`Expanded`).
