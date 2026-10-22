# anti-patterns — the real bugs, Flutter v6

## Startup
1. **Rendering a `CometChat*` widget before `login` succeeds** → blank screen or a listener exception. Gate
   the first frame (`lifecycle.md`).
2. **Missing `WidgetsFlutterBinding.ensureInitialized()`** → `initFromSettings` cannot read the settings
   asset through `rootBundle`; first-run crash.
3. **`init` inside a screen's `initState`** that can be re-entered → repeated init, raced Calls-SDK routing.
4. **Using `init()` + `UIKitSettingsBuilder` instead of `initFromSettings()`** → loses
   `integrationSource="ai-agent"` telemetry attribution (`RULES.md` §5). The docs still show the old path.
5. **A REAL Auth Key committed in `cometchat-settings.json`** → the key is in your repo history. Do NOT fix this by gitignoring the file — it is a registered Flutter asset, so a fresh clone / CI `flutter build bundle` then fails with *"No file or variants found for asset."* Commit a **placeholder** `cometchat-settings.json` (empty/placeholder `authKey`) that dev and CI overwrite locally; guard the real key with a pre-commit/CI check.
6. **Auth Key in a production build** → it authenticates *any* user. Prod is `loginWithAuthToken` with a
   server-minted token.
7. **Inventing a UID.** `login` requires a user that already exists. Ask, or read Dashboard → Users.

## Layout
8. **A kit list without `Expanded`/`Flexible` in a `Column`** → unbounded-height exception or a zero-height
   list. The single most common Flutter integration failure (`layout.md`).
9. **The surface inside a `SingleChildScrollView`** → infinite height constraints; same failure.
10. **`resizeToAvoidBottomInset: false`** → the composer disappears under the keyboard.
11. **No `Scaffold`/`SafeArea`** → missing `Material` ancestor, or UI under the notch/home indicator.

## v5 carry-overs (all REMOVED in v6 — see `cometchat-flutter-v6-migration`)
12. **Registering extensions** — `UIKitSettings.extensions`, `CometChatUIKitChatExtensions`,
    `DataSource`, `ChatConfigurator`, `*ExtensionDecorator`, `CometChatUIKit.getDataSource()`. v6 deleted
    the entire pattern; a dashboard-enabled extension surfaces **automatically** with zero client code.
    Emitting registration is a defect, not a harmless no-op.
13. **Combined shell widgets** — `CometChatConversationsWithMessages`, `CometChatUsersWithMessages`,
    `CometChatGroupsWithMessages`, `CometChatMessages`, `CometChatUI`, `CometChatMessenger`,
    `CometChatUserList`, `CometChatContactList`. v6 has **no** shell widget; the host composes screens.
14. **GetX controllers** — `CometChatMessagesController`, `CometChatOngoingCallController`. v6 is BLoC.
15. **`CometChatCompactMessageComposer`** → one `CometChatMessageComposer`.

## Cross-family contamination
16. **Carrying a React name into Flutter.** `CometChatThreadHeader` does not exist here — it is
    `CometChatThreadedHeader`. Nor do `showSearchOption`/`onSearchOptionClicked` on the message header, or
    `onItemClick` on the conversation list (it is **`onItemTap`**). Equally: `CometChatMediaRecorder` DOES
    exist in Flutter though it is a React phantom. **Never reuse another family's symbol or phantom list —
    check `catalogs/flutter-v6.json`.**
17. **Importing calls widgets from the chat barrel.** `CometChatIncomingCall`, `CometChatOutgoingCall`,
    `CometChatCallButtons`, `CometChatCallLogs`, `CometChatCallBubble` and `CometChatCalls` resolve ONLY
    from `package:cometchat_chat_uikit/cometchat_calls_uikit.dart`. A calls screen imports **both** barrels.
18. **Adding `cometchat_sdk` as a direct dependency to get `User`/`Group`/`TextMessage`.** The kit barrel
    already re-exports the whole Chat SDK.

## Composition
19. **Passing `parentMessageId` without `user:`/`group:`** on a thread list/composer → replies silently
    never send. Both are required.
20. **A dead-ending affordance.** A search field that opens nothing, or a thread indicator with no
    `onThreadRepliesClick` — wire it to a destination or hide it (`hideSearch`).
21. **Hand-rolling what the widget already exposes.** Custom UI belongs in a slot
    (`auxiliaryButtonView` / `trailingView` / `appBarOptions`), never stacked on top of the widget.
22. **Client-side filtering the conversation list.** Scope `conversationsRequestBuilder` instead.
23. **Hand-rolling moderation or report UI.** Both are automatic in `CometChatMessageList`; the work is in
    the Dashboard.
