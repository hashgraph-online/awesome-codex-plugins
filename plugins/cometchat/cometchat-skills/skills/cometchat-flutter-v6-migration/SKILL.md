---
name: cometchat-flutter-v6-migration
description: "Upgrade a Flutter app from CometChat UI Kit v5 → v6 (`cometchat_chat_uikit` ^5 → ^6). Reads the repo's CometChat usage, applies the breaking-change map (removed shells, the deleted extension architecture, GetX → BLoC, renamed widgets), and verifies the build. Triggers: 'upgrade my v5 uikit to v6', 'migrate cometchat flutter v5 to v6', 'cometchat flutter v5 to v6', 'bump cometchat_chat_uikit'."
license: "MIT"
compatibility: "Flutter >=3.38.9; FROM cometchat_chat_uikit ^5 → ^6 (6.1.x, verified 6.1.0); cometchat_sdk ^5.0.6"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat flutter migration upgrade v5 v6 uikit"
---

> **Ground truth:** the removed-symbol map in `references/migration-guide.md` is derived from a REAL diff — every prior-pack symbol was compiled against the published 6.1.0, and the 45 that no longer resolve are recorded with their replacement (`COVERAGE-flutter-v6.md`). v6 target symbols are catalog-verified. The prop-by-prop table is FETCHED from `upgrading-from-v5`. **Transform the user's code — never wipe it; work on a branch and confirm before bulk edits.**

## Companion skills (read first)
- `cometchat-flutter-v6-core` — the v6 init/login/render the migrated app lands on. This skill ASSUMES it.
- `cometchat-flutter-v6-components` — the v6 widget catalog (the target names).

## Use this skill when
"upgrade my v5 UI Kit to v6", "migrate CometChat Flutter v5→v6", "bump `cometchat_chat_uikit`". Precondition: the project currently has `cometchat_chat_uikit` ^5.

## Prerequisites & install
A clean branch. Then `flutter pub add cometchat_chat_uikit:^6.1.0` (and `cometchat_calls_sdk:^5.0.4` if the app calls). Remove `cometchat_uikit_shared` **and `cometchat_calls_uikit`** — neither exists as a package in v6; calling now ships inside the chat package behind a second barrel.

**Expect `pub get` to fail once on a peer constraint.** The kit tightens transitive pins (e.g. 6.1.0 needs `permission_handler ^12`, so an app on `^11` will not resolve). Bump the app's pin to what the solver names — never downgrade the kit to fit the app.

## Migration workflow (BAKED)
1. **Confirm the starting point.** `pubspec.yaml` has `cometchat_chat_uikit` ^5 (already ^6 → STOP, nothing to migrate). Note platform floors (Android `minSdk 26`, iOS `15.1` — **not** the docs' 24 / 13.0; see DOCS-BACKLOG D7) and whether the app uses calls / GetX / extensions / custom templates.
2. **Update deps.** Bump the kit; drop `cometchat_uikit_shared` **and `cometchat_calls_uikit`**; bump `cometchat_sdk`/`cometchat_calls_sdk`; expect one peer-constraint bump. `flutter pub get`.
3. **Scan for removed symbols** — grep the map in `references/migration-guide.md`. Produce a concrete change list BEFORE editing.
4. **Apply the map** (below + the reference), then **re-point imports**: everything now comes from `package:cometchat_chat_uikit/cometchat_chat_uikit.dart`, plus `…/cometchat_calls_uikit.dart` for call widgets.
5. **Re-verify** — `flutter analyze` clean, no v5 symbol remains, the app builds and chat renders.

## The five breaking changes that matter (BAKED)
**1. The combined shells are GONE.** v5's all-in-one widgets have no v6 equivalent — the host composes screens now.
| v5 | v6 |
|---|---|
| `CometChatConversationsWithMessages` | `CometChatConversations` + push a message screen |
| `CometChatUsersWithMessages` / `CometChatGroupsWithMessages` | `CometChatUsers` / `CometChatGroups` + push |
| `CometChatMessages` | `CometChatMessageHeader` + `CometChatMessageList` + `CometChatMessageComposer` |
| `CometChatUI` · `CometChatMessenger` · `CometChatUserList` · `CometChatContactList` · `CometChatChatList` | compose from the catalog (`-placement`) |
This is the largest edit: a one-line v5 shell becomes a screen you assemble. Use the core golden path as the target shape.

**2. The extension architecture is DELETED.** The builder setters `..extensions` · `..aiFeature` · `..callingExtension` are gone, along with `CometChatUIKitChatExtensions` · `CometChatCallingExtension` · `DataSource` / `ExtensionsDataSource` · `ChatConfigurator` · every `*Extension` and `*ExtensionDecorator` · `CometChatUIKit.getDataSource()`.
Dashboard-enabled extensions now surface **automatically**; the replacement for `getDataSource()` defaults is `MessageTemplateUtils` (`getTextMessageOptions`, `getAllMessageTypes`, `getAllMessageCategories`).
**Two exceptions to "just delete it":**
- **Calling had a replacement, not a removal.** `..callingExtension = CometChatCallingExtension()` becomes `..enableCalls = true` + `..callingConfiguration = CallingConfiguration()` on the classic builder, or `uiKit.enableCalling` on `initFromSettings` (`-calls`). Delete it without the pair and every call affordance vanishes silently.
- **`CometChatUIKitChatAIFeatures` still resolves** — delete the `..aiFeature = …` line because the *setter* is gone, not the class.

**3. GetX controllers → BLoC.** `CometChatMessagesController`, `CometChatOngoingCallController` and friends are gone; v6 widgets own their blocs internally. Delete the controller wiring; read list state via `stateCallBack` / `onLoad` instead (`-events`).

**4. Renames.** `CometChatEditPreview` → `CometChatMessagePreview` · `CometChatCompactMessageComposer` → `CometChatMessageComposer` · the AI views gained a `View` suffix (`CometChatAISmartReplies` → `CometChatAISmartRepliesView`, and the same for conversation-starter / summary) · call-log detail widgets folded into `CometChatCallLogs`.

**5. Imports + barrels — budget for this one; it breaks the most files.** `package:cometchat_uikit_shared/...` and the whole `cometchat_calls_uikit` **package** no longer resolve. Call widgets moved behind the **calls barrel** inside the chat package — a screen using them imports both (`-calls`).
The trap: **the v5 calls package re-exported the chat kit, the v6 calls barrel does not.** Every file that imported only the calls package silently loses `CometChatUIKit`, `CometChatThemeHelper`, the theme classes and `Translations`. On the real `sample_app` this was **94 of 119** post-bump errors — more than all removed symbols combined. Re-point the imports, then add the chat barrel wherever a chat symbol reports undefined.

**Beyond the five: things that fail as ordinary type errors.** Changed callback signatures (`CometChatConfirmDialog`), a slot whose return type changed (`options` → `trailingView`), renamed props (`messageId` → `goToMessageId`), and an app that **subclassed** a kit list controller (now a `ChangeNotifier`, so `GetBuilder` rejects it). Nothing greps for these — the table in `references/migration-guide.md` lists each with its fix.

## Also check
- **Banned members** — no v6 widget; use the SDK (`BannedGroupMembersRequestBuilder` + `unbanGroupMember`) to keep the ban round-trip closed.
- **Custom message types** — v5 templates still map to `CometChatMessageTemplate`, but defaults now come from `MessageTemplateUtils` (`-components`).
- **Text formatters** — `CometChatTextFormatter` is abstract in v6 and requires `init`, `getMessageInputTextStyle`, `handlePreMessageSend`, `onChange`, `onScrollToBottom`. A v5 subclass will not compile until those exist.
- **Theming** — the v5 palette holder is gone; v6 uses `ThemeData.extensions` with `CometChatColorPalette` (`-customization`).
- **Init** — consider moving to `initFromSettings` + `cometchat-settings.json` for telemetry attribution while you are here (core). **It does not fit every app:** one that takes App ID / region / auth key at runtime (a credentials screen, multi-tenant switching) cannot express that in a static asset — keep `UIKitSettingsBuilder` there and say why.

## Common pitfalls (BAKED)
- **Porting extension registration** instead of deleting it — the #1 v5→v6 error.
- **Looking for a v6 shell** — there isn't one; compose the screens.
- **Leaving `cometchat_uikit_shared` or `cometchat_calls_uikit` in pubspec** → unresolved imports.
- **Re-pointing the calls import without adding the chat barrel** → a wave of "undefined" chat symbols that look like removals and are not.
- **Mixing majors** — never run v5 and v6 side by side; finish the migration.
- **Bulk find-and-replace without reading** — the shell→composition change is structural, not a rename.
- **Forgetting the platform floors** (`minSdk 26`, iOS `15.1` — the docs' 24 / 13.0 are too low) → the build fails after the bump, which is exactly when it is hardest to attribute.

## Verify it works
`flutter analyze` is clean; no symbol from the removed map remains (grep it); the app builds on both platforms; chat renders, messages send/receive, threads and search still work; calling (if used) still rings with both barrels imported. Then re-run the core "Verify before done".
