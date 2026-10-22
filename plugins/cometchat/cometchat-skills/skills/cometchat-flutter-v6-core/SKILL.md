---
name: cometchat-flutter-v6-core
description: "Add CometChat chat to a Flutter app end-to-end — detect the project, get & verify dashboard credentials, init→login→render, and the drop-in conversation UI. The core knowledge every other Flutter v6 skill builds on. Triggers: 'add chat to my flutter app', 'integrate cometchat flutter', 'set up cometchat credentials flutter', 'show conversations and messages in flutter'."
license: "MIT"
compatibility: "Flutter >=3.38.9; Dart >=3.10.8 <4.0.0; cometchat_chat_uikit ^6 (6.1.x, verified 6.1.0); cometchat_sdk ^5.0.6; cometchat_calls_sdk ^5.0.4 (calls only)"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat flutter core chat integration uikit v6 setup credentials"
---

> **Ground truth:** `cometchat_chat_uikit@6` (6.1.0) + `cometchat_sdk@^5.0.6`. Every `CometChat*` symbol here is in `catalogs/flutter-v6.json` — **compiler-verified** against the published package. Signatures marked **[verified]** were compiled because the docs were **wrong**, or (for `initFromSettings`) deliberately **silent** (`DOCS-BACKLOG.md` PART 4): trust this file for those, fetch the rest via `references/docs-map.md`. THIN map loaded every run; depth in `references/*`.

<!-- core is the companion the other flutter v6 skills read; it has no Companion block of its own. -->

## Use this skill when
"add chat to my Flutter app", "integrate CometChat in Flutter", "set up CometChat credentials", "show a conversations + messages screen". An unscoped **"add chat"** means a **production-ready core surface** — a `CometChatConversations` screen pushing a message screen, with **threaded replies** and **search** wired, in `Scaffold`/`SafeArea`, keyboard-safe, every screen popping back — NOT a two-widget demo, NOT the whole tab-based app (see the golden path). It **grows on request** → `cometchat-flutter-v6-placement`.

## Install
```bash
flutter pub add cometchat_chat_uikit
```
Pin the major in `pubspec.yaml` — `cometchat_chat_uikit: ^6.1.0` (a bare `any` can resolve across majors). The Chat SDK (`cometchat_sdk`) comes **transitively and is re-exported by the kit barrel** — do NOT add it separately unless you import SDK-only paths. Voice/video calling = a settings flag + native config (`cometchat_calls_sdk` is already a transitive kit dependency — see below) → `cometchat-flutter-v6-calls`.

**Platform minimums** — Android `minSdk = 26` in `android/app/build.gradle.kts`; iOS `platform :ios, '15.1'` in `ios/Podfile`. **The `getting-started` page says 24 / 13.0 and both are too low** (DOCS-BACKLOG D7). The kit's own AAR allows 21, but transitive deps set the real floor and this one is not optional: `cometchat_chat_uikit` depends on **`cometchat_calls_sdk`** unconditionally — it sits in the main `dependencies:` block — and that package pins `minSdkVersion 26` / `platform :ios, '15.1'` (5.0.7). Gradle and CocoaPods take the maximum across the graph, so a lower value is a build error whether or not the app uses calling.

## Setup & credentials (essentials — full detail: `references/setup-credentials.md`)
1. **Detect** by READING the repo — `pubspec.yaml` + lockfile (deps and the kit major), `lib/main.dart`, state management, navigation, and how config is handled. Reuse an existing `.cometchat/config.json` or settings asset (skip re-setup). Signal table: `references/setup-credentials.md`.
2. **version_conflict — STOP** if the project already has `cometchat_chat_uikit` v5 (or any non-v6 major); reconcile first, never mix majors (`RULES.md`). A v5 project that wants v6 → `cometchat-flutter-v6-migration`.
3. **Credentials — OFFER the dashboard fetch FIRST; never default to "paste it yourself."** When App ID / Region / Auth Key are missing, offer **(a) fetch from your dashboard (recommended)** — load the CLI on demand, pick an **EXISTING** app (never auto-create) — or **(b) manual paste**. Then the SKILL writes `cometchat-settings.json` (§4) from those creds; the CLI is dashboard/API-only and never writes Dart (`RULES.md` §21). Never defer credentials to a "add them yourself" TODO. Exact commands + the app-picker flow: `references/setup-credentials.md`.
4. **Write the settings asset + register it** — commit only a placeholder (no real Auth Key) and do **not** gitignore it (a registered asset must exist or a fresh-clone `flutter build` fails — see the note in §Integration ordering); never echo the Auth Key. Prod → server-minted auth token, not the Auth Key.
5. **Authorize** = `init` then `login` both hit `onSuccess`. An auth error is almost always the wrong **Region**.

## Integration ordering (BAKED — invariant; docs: init must complete before login, login before any widget)
`initFromSettings()` once at startup → `login(UID)` after init succeeds → only THEN render any `CometChat*` widget.

**Init via `initFromSettings` — the file-based, telemetry-attributed path (`RULES.md` §5).** It reads a `cometchat-settings.json` **asset** and persists `integrationSource="ai-agent"`. **Flutter's signature takes NO settings argument** (unlike web, which passes a settings object) — the file IS the input:

```dart
// [verified vs 6.1.0] — INTENTIONALLY undocumented upstream (@nodoc, owner decision:
// DOCS-BACKLOG F4 WONTFIX). Prefer it over the docs' UIKitSettingsBuilder + init()
// path, which loses telemetry attribution. The shape below is the contract.
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';

await CometChatUIKit.initFromSettings(
  onSuccess: (String message) => debugPrint('CometChat initialized'),
  onError: (CometChatException e) => debugPrint('Init failed: ${e.message}'),
);
```

`cometchat-settings.json` at the **project root**, registered in `pubspec.yaml` under `flutter: assets:`:
```json
{
  "appId": "APP_ID",
  "region": "REGION",
  "credentials": { "authKey": "AUTH_KEY" },
  "uiKit": { "subscribePresenceForAllUsers": true, "enableCalling": false },
  "chatSDK": { "autoEstablishSocketConnection": true }
}
```
> Keys are read exactly as above. `uiKit.enableCalling` is the **only** way to turn calling on via this path (`UIKitSettings` defaults it to false) — leave it `false` until the user asks for calls. `credentials.authKey` is **dev-only**; omit it for production and log in with a server-minted token.
> **Make a fresh clone build.** A file registered under `flutter: assets:` MUST exist at build time or `flutter build bundle` fails with *"No file or variants found for asset: cometchat-settings.json."* So do **not** gitignore the registered asset. Instead **commit a placeholder `cometchat-settings.json`** — same shape, with a placeholder/empty `authKey` (NEVER a real dev Auth Key) — and have each developer and CI overwrite it locally/at build time with real credentials. (Enforce "no real key committed" via a pre-commit check or CI, not `.gitignore`.) For production, CI generates the prod-flavoured file (no Auth Key) at build time (`cometchat-flutter-v6-production`).

```dart
// login AFTER init succeeds. CometChatUIKit.login already checks getLoggedInUser()
// internally and no-ops if that UID is signed in, so no host-side re-login guard is needed.
await CometChatUIKit.login(
  uid,
  onSuccess: (User user) => debugPrint('Logged in: ${user.name}'),
  onError: (CometChatException e) => debugPrint('Login failed: ${e.message}'),
);
```
> **Which UID?** `login()` needs a user that ALREADY EXISTS — never invent one. ASK, or take one from Dashboard → **Users**; fresh apps seed `cometchat-uid-1…`. The only tentative suggestion is `cometchat-uid-1`, labelled "if this is a fresh app." **Prod → `CometChatUIKit.loginWithAuthToken(authToken, …)`** with a token minted server-side.
> Init-once, hot-restart, and gating the first frame: `references/lifecycle.md`.

## Widget / API map (BAKED closed list — from the catalog)
Init/session: `CometChatUIKit` (`initFromSettings` · `login` · `loginWithAuthToken` · `logout` · `loggedInUser`), `UIKitSettingsBuilder`, `CometChatSubscriptionType`, `CometChatException`.
Core surface: `CometChatConversations`, `CometChatMessageHeader`, `CometChatMessageList`, `CometChatMessageComposer`; wired affordances `CometChatThreadedHeader`, `CometChatSearch`.
Grow set (added on request): `CometChatUsers`, `CometChatGroups`, `CometChatGroupMembers`, `CometChatChangeScope`, `CometChatCallLogs`. Incoming calls need NO widget — with calling on, the kit presents the overlay itself (`-calls`).
> **TWO BARRELS — a real compile trap.** `package:cometchat_chat_uikit/cometchat_chat_uikit.dart` gives you the chat widgets **and the re-exported Chat SDK** (`User`, `Group`, `Conversation`, `BaseMessage`, `TextMessage` — no separate import). **Every calls symbol** (`CometChatIncomingCall`, `CometChatOutgoingCall`, `CometChatCallButtons`, `CometChatCallLogs`, `CometChatCallBubble`, `CometChatCalls`) lives ONLY in `package:cometchat_chat_uikit/cometchat_calls_uikit.dart`, and that barrel does NOT re-export the chat widgets — a calls screen imports **both**. Verified: using `CometChatIncomingCall` with only the chat import fails to compile.
> The v6 widget is **`CometChatThreadedHeader`** — `CometChatThreadHeader` (the React name) does NOT exist here. Never carry a name across families.

## Hot-path props (BAKED — the golden path needs NO fetch)
- `CometChatConversations`: `onItemTap(Conversation)` (select → push the message screen) · `hideSearch` · `searchReadOnly` (set `true` so the field acts as a button) · `onSearchTap` (→ push `CometChatSearch`) · `conversationsRequestBuilder` (scope to `user`/`group` when the ask is DM-only or groups-only — reuse the builder, don't client-filter) · `hideAppbar` · `appBarOptions` · `onBack`.
- `CometChatMessageHeader`: `user:` / `group:` (pass the SAME target as the list) · `showBackButton` (default `true`) + `onBack` · `hideVoiceCallButton` / `hideVideoCallButton` (call buttons are built in — leave them unless calls are out of scope) · `auxiliaryButtonView` / `trailingView` (where a custom action goes — see search below).
- `CometChatMessageList`: `user:` / `group:` · `parentMessageId` (thread mode) · `onThreadRepliesClick` **[verified]** — the type is `ThreadRepliesClick = void Function(BaseMessage message, BuildContext context, {CometChatMessageTemplate? template})`; a one-argument closure does **not** compile (`DOCS-BACKLOG` F2).
- `CometChatMessageComposer`: `user:` / `group:` · `parentMessageId` (thread mode). A plain send needs nothing else.
- `CometChatSearch` **[verified]**: `onConversationClicked` / `onMessageClicked` (**not** the docs' `onConversationItemClick` / `onMessageItemClick` — `DOCS-BACKLOG` F3) · `onBack` · `user:` / `group:` / `searchIn` to scope it to one chat.
> Any OTHER widget or a rarer prop → fetch its `.md` twin via `references/docs-map.md`. Full catalog: `cometchat-flutter-v6-components`.

## Golden path — the production-ready CORE surface (default for an unscoped "add chat"; grows on request)
Setup → init/login → **gate the first frame** on both resolving (show a loader; never render a `CometChat*` widget before login succeeds) → then:

1. **Conversations screen** — `CometChatConversations` inside `Scaffold` + `SafeArea`. Wire `onItemTap` → `Navigator.push` the message screen for that conversation's `User`/`Group`. Wire the **global search** the documented way: `searchReadOnly: true` + `onSearchTap` → push a `CometChatSearch` screen, whose `onConversationClicked`/`onMessageClicked` navigate to the hit and whose `onBack` pops. (Or set `hideSearch: true` — but never leave the field dead.)
2. **Message screen** — `CometChatMessageHeader` + `Expanded(child: CometChatMessageList(...))` + `CometChatMessageComposer`, all carrying the SAME `user:`/`group:`. `Expanded` is what makes the list fill the screen; the header/composer keep their intrinsic height. Leave `Scaffold.resizeToAvoidBottomInset` at its default `true` so the composer rides above the keyboard. The header's `showBackButton` defaults to `true` — wire `onBack` to `Navigator.pop`.
3. **Thread screen (DEFAULT — include unless the user opts out)** — wire the list's `onThreadRepliesClick` to push a screen with `CometChatThreadedHeader(parentMessage:, loggedInUser:)` — both required, and it has **no `onBack`**, so the screen's own `AppBar` provides back — plus a `CometChatMessageList` + `CometChatMessageComposer` that each take `parentMessageId: parentMessage.id` **AND the same `user:`/`group:` as the parent chat**. **Passing `parentMessageId` without the user/group target makes thread replies silently never send.**
4. **In-chat scoped search** — Flutter's `CometChatMessageHeader` has **no** search prop (unlike React). Put the action in the header's `auxiliaryButtonView`/`trailingView` slot — custom UI goes IN the slot, never stacked on top — and push `CometChatSearch(user: …/group: …)` so it searches only that chat.

```dart
// [verified vs 6.1.0] the message screen — the shape the whole surface hangs off.
import 'package:cometchat_chat_uikit/cometchat_chat_uikit.dart';
import 'package:flutter/material.dart';

class MessageScreen extends StatelessWidget {
  final User? user;
  final Group? group;
  const MessageScreen({super.key, this.user, this.group});

  @override
  Widget build(BuildContext context) {
    return Scaffold(                       // resizeToAvoidBottomInset defaults to true = keyboard-safe
      body: SafeArea(
        child: Column(
          children: [
            CometChatMessageHeader(user: user, group: group, onBack: () => Navigator.pop(context)),
            Expanded(                      // REQUIRED — the list fills the remaining height
              child: CometChatMessageList(
                user: user,
                group: group,
                onThreadRepliesClick: (BaseMessage message, BuildContext context,
                    {CometChatMessageTemplate? template}) {
                  Navigator.push(context, MaterialPageRoute(
                    builder: (_) => ThreadScreen(parentMessage: message, user: user, group: group),
                  ));
                },
              ),
            ),
            CometChatMessageComposer(user: user, group: group),
          ],
        ),
      ),
    );
  }
}

// The thread screen the callback pushes — part of the DEFAULT surface, not an extra.
// NOTE: the list AND composer each take parentMessageId *and* the same user:/group:
// as the parent chat. parentMessageId alone => replies silently never send.
class ThreadScreen extends StatelessWidget {
  final BaseMessage parentMessage;
  final User? user;
  final Group? group;
  const ThreadScreen({super.key, required this.parentMessage, this.user, this.group});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      // The thread screen's back affordance is the AppBar — CometChatThreadedHeader
      // has NO onBack/onError param (the docs show one; it does not exist, DOCS-BACKLOG F5).
      // A pushed route gets the back button automatically.
      appBar: AppBar(title: const Text('Thread')),
      body: SafeArea(
        child: Column(
          children: [
            CometChatThreadedHeader(                      // note the 'ed' — see the map above
              parentMessage: parentMessage,               // NOT `message:` (DOCS-BACKLOG F1)
              loggedInUser: CometChatUIKit.loggedInUser!, // required
            ),
            Expanded(
              child: CometChatMessageList(
                user: user, group: group, parentMessageId: parentMessage.id,
              ),
            ),
            CometChatMessageComposer(
              user: user, group: group, parentMessageId: parentMessage.id,
            ),
          ],
        ),
      ),
    );
  }
}
```
> **SIZE it the mobile way — `references/layout.md`.** The kit's list widgets expand to fill their parent, so the failure mode here is an **unbounded height** error or a collapsed list, and the fix is always the same: give the list a bounded box (`Expanded`/`Flexible` inside a `Column`, or a sized parent) instead of letting content drive it. Never nest the surface in an unbounded `SingleChildScrollView`/`Column` without `Expanded`.
> **Match the data scope to the REQUEST.** Real apps ship seeded groups, so a plain `CometChatConversations` lists both 1:1s and groups. A **DM-only** ask scopes the list to user conversations via `conversationsRequestBuilder`; a **groups-only** app scopes to groups; a generic "add chat" keeps BOTH. Reuse the builder — never hand-roll a client-side filter, and don't add a Groups tab to a 1:1-only app.
> **Prod auth:** mint a per-user auth token server-side and call `loginWithAuthToken` — the Auth Key is dev-only (`references/lifecycle.md`).

## Growing on request
Add each only when asked: **Users / Groups / Calls tabs** (`CometChatUsers` · `CometChatGroups` · `CometChatCallLogs`) · **group details** (`CometChatGroupMembers` + `CometChatChangeScope`) · **calls** (→ `-calls`; incoming calls = only `navigatorKey: CallNavigationContext.navigatorKey` on the root `MaterialApp` — never mount `CometChatIncomingCall` yourself, that doubles the kit's overlay) · **features** (→ `-features`). The full tab-based app is the union of these — recipe in `-placement`. A scoped-DOWN ask (chat tab, bottom sheet, embedded panel) → the matching `-placement` variant.

## Deep references (load ONLY when the task needs them)
- `setup-credentials.md` — detect signals · version_conflict · dashboard creds · the settings asset.
- `lifecycle.md` — init-once + hot restart · gating the first frame · prod auth-token · logout.
- `layout.md` — mobile sizing (bounded height · `Expanded` · SafeArea · keyboard).
- `docs-map.md` — intent → live doc page (component twins **+ the SDK-docs section**) · DOCS-GAP protocol · the pages that are wrong.
- `anti-patterns.md` — v5 carry-overs · unbounded height · render-before-login · the two-barrel trap.
- `troubleshooting.md` — symptom → cause → fix.

## Common pitfalls (top 5 — full list in `references/anti-patterns.md`)
- **version_conflict** (v5 installed) · **wrong Region** · **Auth Key shipped to prod** · **rendering a widget before `login` succeeds**.
- **Emitting v5 architecture into a v6 app.** v6 REMOVED the extension pattern — no `UIKitSettings.extensions`, no `CometChatUIKitChatExtensions`, no `DataSource`/`ChatConfigurator`/`*ExtensionDecorator`, no `CometChatUIKit.getDataSource()`. Dashboard-enabled extensions surface **automatically** with zero client code. Also gone: the v5 combined shells (`CometChatConversationsWithMessages`, `CometChatUsersWithMessages`, `CometChatMessages`, `CometChatUI`) — v6 has no shell widget; the host composes screens. Full map: `cometchat-flutter-v6-migration`.
- **Trusting the docs on the `[verified]` signatures above.** The thread-header params, `onThreadRepliesClick`, and the search callbacks were wrong on the live pages (`DOCS-BACKLOG.md` PART 4 F1/F2/F3/F5) — **all four are now corrected upstream** (re-verified against `cometchat/docs`@`2ebb1db`, 2026-09-09), so the `[verified]` names now agree with the pages; keep them. `initFromSettings` is different: it is deliberately undocumented and stays that way (F4 WONTFIX), so this skill is its only reference.

## Verify it works
Run the app: `init` then `login` both hit `onSuccess` → the conversations screen renders **full-size** (no sliver, no unbounded-height exception) → tap a conversation → messages send/receive → **"reply in thread" opens the thread screen and back returns** → the search field pushes search, a result navigates, back pops → the composer stays visible with the keyboard open → every pushed screen pops back. Blank screen ⇒ rendered before `login` resolved, or wrong Region/App ID. No bounded height, no thread wiring, or a dead search field ⇒ **under-delivery**. Tab-based app ⇒ verify per `-placement`.
> Build the feature; do **not** write tests or run a test framework unless asked (`RULES.md`) — the above is an advisory human pass.

## Explain what you built (REQUIRED close — `RULES.md` §19)
Don't end on a silent code dump. Briefly: **(1) what I wired** (3–5 bullets, NAME the files); **(2) decisions & why**, flagging dev-only AS dev-only (Auth Key → server token for prod; the `<uid>`); **(3) what I did NOT touch** (additive — routing/state/theme intact). Then offer THREE options as a selectable choice and **WAIT** for the pick:
- **① Add another feature** — first check what's already wired, and ASK which dashboard extensions are already on (you can't read per-app state). Suggest 3–4 that are neither (**calls · push · polls · stickers · translation · AI smart replies · moderation**). **Never suggest reactions, mentions, quoted reply or threads — they are ON by default in v6**; offer to customize them instead. → `-features` / `-calls`.
- **② Customize theming** — ask for a brand/preset theme or talk through options → `-customization`.
- **③ Test it manually** — do NOTHING further; hand it back.

A capability not in this pack: say so honestly + link CometChat's docs.
