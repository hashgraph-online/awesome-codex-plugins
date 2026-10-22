# migration-guide — the v5 → v6 removed-symbol map

Everything here is **compiled against the published `cometchat_chat_uikit` 6.1.0**. Provenance:
`COVERAGE-flutter-v6.md` (the Phase-B coverage-parity diff), plus what a real v5→v6 migration of the
`cometchat-uikit-flutter` `sample_app` turned up. Grep for these; each row says what to do.

> **A removed symbol is the easy half.** The sections below the symbol tables — barrels, changed
> signatures, subclassed controllers — are what actually consume the time, because the analyzer
> reports them as ordinary type errors with no hint that a migration caused them.

## Removed — combined shells (compose instead)
| Removed | Replacement |
|---|---|
| `CometChatConversationsWithMessages` | `CometChatConversations` + a pushed message screen |
| `CometChatUsersWithMessages` | `CometChatUsers` + push |
| `CometChatGroupsWithMessages` | `CometChatGroups` + push |
| `CometChatMessages` | `CometChatMessageHeader` + `CometChatMessageList` + `CometChatMessageComposer` |
| `CometChatUI` · `CometChatMessenger` · `CometChatChat` | compose the screen (`-placement`) |
| `CometChatUserList` · `CometChatContactList` · `CometChatChatList` | `CometChatUsers` · `CometChatConversations` |
| `CometChatBannedMembers` | no widget — SDK `BannedGroupMembersRequestBuilder` + `unbanGroupMember` |
| `CometChatCallLogHistory` · `CometChatCallLogParticipants` · `CometChatCallLogRecordings` | folded into `CometChatCallLogs` (+ `guide-call-log-details`) |

## Removed — the extension architecture (DELETE, do not port)
**The builder setters are gone** — `..extensions` · `..aiFeature` · `..callingExtension` on
`UIKitSettingsBuilder` (compiler-verified vs 6.1.0: all three report `undefined_setter`). So is
`CometChatUIKitChatExtensions` · `CometChatCallingExtension` · `DataSource` · `ExtensionsDataSource` ·
`ChatConfigurator` · every `*Extension` / `*ExtensionDecorator` · `CometChatUIKit.getDataSource()`.
> **`CometChatUIKitChatAIFeatures` still resolves** and is NOT a removed symbol — an earlier revision
> of this table listed it wrongly. Delete the `..aiFeature = …` line because the *setter* is gone, not
> because the class is.
> **Calling is not simply deleted.** `..callingExtension` had a replacement, not a removal: on the
> classic builder it becomes `..enableCalls = true` + `..callingConfiguration = CallingConfiguration()`
> (`../../cometchat-flutter-v6-calls/SKILL.md`); on `initFromSettings` it is `uiKit.enableCalling`.
> Dropping the line without this pair leaves an app whose call buttons never appear, with no error.
> v6 handles extensions through `MessageTemplateUtils` with **zero** registration. Enable in the
> Dashboard and delete the code. For defaults previously read off the DataSource:
> `MessageTemplateUtils.getTextMessageOptions(...)` · `.getAllMessageTypes()` · `.getAllMessageCategories()`.

## Removed — GetX controllers (v6 is BLoC)
`CometChatMessagesController` · `CometChatOngoingCallController` · `CometChatOngoingCallView` ·
`CometChatOngoingCallService` · `CometChatRTCView` / `Builder` / `Listener` ·
`CometChatDisplayIncomingCallOverlay`.
> Widgets own their blocs. Read list state with `stateCallBack` / `onLoad`; do not re-create a controller layer.

## Renamed
| v5 | v6 |
|---|---|
| `CometChatEditPreview` | `CometChatMessagePreview` |
| `CometChatCompactMessageComposer` | `CometChatMessageComposer` |
| `CometChatAISmartReplies` | `CometChatAISmartRepliesView` |
| `CometChatAIConversationStarter` | `CometChatAIConversationStarterView` |
| `CometChatAIConversationSummary` | `CometChatAIConversationSummaryView` |

## Not public in v6 (app-sample or internal — do not emit)
`CometChatApp` · `CometChatAppState` · `CometChatBuilderRoot` · `CometChatBuilderSettings` ·
`CometChatConfig` · `CometChatService` / `Impl` · `CometChatToken` · `CometChatActionSheet` ·
`CometChatMessageView` · `CometChatCardBubble` · `CometChatImageBubbleState` · `CometChatReceiptStyle` ·
`CometChatUserOption` · `CometChatReverseListProtocol`.
> `CometChatConfig` is a name the getting-started guide tells you to create yourself — if the app has one,
> it is the app's own class and stays.

## Renamed / relocated, not removed
`CometChatSoundManager` → **`SoundManager`** (un-prefixed singleton;
`SoundManager().play(sound: Sound.incomingMessage)` / `.stop()`, compiler-verified vs 6.1.0). It looked
missing only because the catalog tracks `CometChat*` symbols; the class is public and importable.

## Localization — use `CometChatLocalize`
Flutter localizes through **`CometChatLocalize`**, the same class as the other families: register its
delegate in `MaterialApp.localizationsDelegates` and read/override strings through it. Fetch the exact
Flutter API from the live `localize` page (`references/docs-map.md` → Localization).
> **[STAGED — needs the UI Kit change]** `CometChatLocalize` requires a `cometchat_chat_uikit` version
> that exposes it; the pinned **6.1.0 does not** (it exposes `Translations`). Bump the pin + refresh
> `catalogs/flutter-v6.json` when that kit ships — until then Flutter localization emitted this way
> will not compile. (The barrel-import notes below still describe the 6.1.0 shape.)

## Imports — expect this to break the MOST files
- `package:cometchat_uikit_shared/...` → **gone**. Everything is `package:cometchat_chat_uikit/cometchat_chat_uikit.dart`.
- `package:cometchat_calls_uikit/...` → **gone as a package**. v6 folds calling into the chat package
  behind a second barrel: `package:cometchat_chat_uikit/cometchat_calls_uikit.dart`.
- **The v5 `cometchat_calls_uikit` package RE-EXPORTED the chat kit; the v6 calls barrel does not.**
  Any file that imported only the calls package was getting `CometChatUIKit`, `CometChatThemeHelper`,
  `CometChatColorPalette`, `CometChatTypography`, `CometChatSpacing`, `Translations` … for free, and
  loses all of them the moment the import is re-pointed. Add the chat barrel to every such file.
  > Measured on the v5 `sample_app`: this one change accounted for **94 of 119** post-bump errors —
  > far more than every removed symbol combined. Re-point the imports, then immediately add the chat
  > barrel wherever the analyzer reports a chat symbol as undefined; do not chase them individually.
- **Watch prefixed imports.** `import '…/cometchat_calls_uikit.dart' as cc;` used to reach chat
  symbols through `cc.` — repoint the prefix at the chat barrel, not just the bare import.
- **`Translations` lives in the CHAT barrel.** In v5 it came from `cometchat_uikit_shared` (gone in v6);
  the live `localize` page now documents the chat-barrel `Translations` path (DOCS-BACKLOG F7 corrected
  upstream). It is not a `CometChat*` name, so it does not appear in the catalog — that absence is not
  evidence it was removed.

## Changed signatures & props (compile errors, not missing symbols)
These resolve under both majors, so nothing greps for them — the analyzer just reports a type error.
All compiler-verified vs 6.1.0.

| v5 | v6 | Note |
|---|---|---|
| `CometChatConfirmDialog(onConfirm: () {…}, onCancel: () {…})` | `onConfirm: (BuildContext c) {…}` | both callbacks gained a context; a method tear-off needs wrapping — `onConfirm: (_) => _leave()` |
| `CometChatMessageHeader(options: (user, group, context) => List<CometChatOption>)` | `trailingView: (user, group, context) => List<Widget>` | **the return type changed**; each `CometChatOption(title:, iconWidget:, onClick:)` becomes the `IconButton(tooltip:, icon:, onPressed:)` it rendered as |
| `CometChatMessageList(messageId: …)` | `goToMessageId: …` | |
| `CometChatUsers(controllerTag: …)` | *removed* | a GetX tag; v6 widgets own their bloc |
| `voiceCallButtonPadding` · `videoCallButtonPadding` | *removed* | on the call-buttons style |
| `AssetConstants` | `CometChatAssetConstants` | now an **extension**, not a class, and the member set differs — for app-owned chrome a Material `Icon` is usually the cleaner port |
| `CallStateController.instance` (`isActiveCall` / `isActiveOutgoingCall` / `isActiveIncomingCall`) | *removed, no global equivalent* | v6 owns call state internally. Track it in the host from the `CometChatCallEvents` it already subscribes to — `ccOutgoingCall` / `ccCallAccepted` set it, `ccCallEnded` / `ccCallRejected` clear it |

## If the app SUBCLASSED a kit list controller
The GetX section above covers apps that *used* the kit's controllers. An app that **extended**
`CometChatListController` / `CometChatSearchListController` fails differently and more confusingly:
the base classes still exist and still provide `list` · `isLoading` · `hasError` · `error` ·
`hasMoreItems`, so nothing looks removed — but they are **`ChangeNotifier`s in v6, not
`GetxController`s**, so every `GetBuilder<T>` around them fails the `T extends GetxController` bound.

The fix is a widget swap, not a rewrite — the builder body is untouched:
```dart
import 'package:flutter/material.dart';

Widget rebuildOn(ChangeNotifier controller, Widget Function() body) =>
    // was: GetBuilder(init: controller, builder: (value) => …)
    ListenableBuilder(listenable: controller, builder: (context, _) => body());
```
Read the controller from the enclosing scope instead of the builder's `value` argument.

## Peer dependencies the bump forces
The kit tightens transitive constraints, and `pub get` fails outright until the app matches. Seen on
the v5 `sample_app`: `permission_handler ^11.3.1` had to go to `^12.0.3` because 6.1.0 requires
`^12.0.0`. Read the solver's message — it names the package and the version to move to — and bump the
**app's** pin rather than downgrading the kit.

## Platform floors after the bump
Android `minSdk = 26`; iOS `platform :ios, '15.1'`. The docs say 24 / 13.0; both are too low, because `cometchat_chat_uikit` depends on `cometchat_calls_sdk` unconditionally and that package pins 26 / 15.1 (5.0.7). Verified against the installed packages, not the page — DOCS-BACKLOG D7.
