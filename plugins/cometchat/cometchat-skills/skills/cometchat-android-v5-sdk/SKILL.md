---
name: cometchat-android-v5-sdk
description: "Build chat on Android with the headless CometChat Chat SDK v5 and your OWN UI — init/login ordering, the method map, request-builder pagination, listener lifecycle, and a production-ready app surface (optimistic updates, error states, sized shell). Use when the app needs custom UI instead of the drop-in UI Kit. Triggers: 'cometchat android sdk', 'chat with my own ui android', 'headless cometchat android', 'send message with chat-sdk-android', 'cometchat message listener kotlin'."
license: "MIT"
compatibility: "Android minSdk >=24; Kotlin >=1.9 / AGP >=8; JVM target 11; com.cometchat:chat-sdk-android ^5 (5.0.x, verified 5.0.5); optional com.cometchat:calls-sdk-android ^5"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android sdk v5 headless kotlin custom-ui chat-sdk"
---

> **Ground truth:** catalog `sdk-android-v5.json` (curated from the INSTALLED `com.cometchat:chat-sdk-android:5.0.5` AAR — the existence oracle) + `features.sdk-android-v5.json` + `contracts.sdk-android-v5.json` (`sdk-chat-surface` — the completeness floor). Docs: `references/docs-map.md`. ⚠️ **Android SDK v5 pages are VERSIONED** (`/sdk/android/v5/…`); the unversioned tree is v4. Verify symbols against the catalog; fetch signatures from docs; never trust memory.

## Companion skills (read first)
This skill is **self-contained** for headless builds — it does not depend on a UI Kit core. But: if the user wants ready-made chat UI, the **UI Kit is the better answer** — say so and route to `cometchat-android-v6-core` (drop-in components, far less code). Come here when they explicitly want their own UI, a non-chat surface, or backend-style usage.

## Use this skill when
"use the CometChat SDK directly", "build chat with my own UI/design system", "I don't want the UI Kit", "send/receive messages programmatically", "custom chat screen in Compose backed by CometChat".

## Prerequisites & install
```kotlin
// settings.gradle(.kts) → dependencyResolutionManagement.repositories
maven("https://dl.cloudsmith.io/public/cometchat/cometchat/maven/")
// app/build.gradle.kts
implementation("com.cometchat:chat-sdk-android:5.0.5")     // + calls-sdk-android:5.0.4 for calling
```
```properties
# gradle.properties — REQUIRED: chat-sdk-android 5.0.5 still pulls android.arch.lifecycle:extensions:1.1.1 → com.android.support:support-compat:26.1.0
android.useAndroidX=true
android.enableJetifier=true
```
- **Jetifier is not optional.** Without `android.enableJetifier=true` an AndroidX app fails `checkDebugDuplicateClasses` (`Duplicate class android.support.v4.app.INotificationSideChannel … androidx.core:core and com.android.support:support-compat:26.1.0`). Verified 2026-09-07 (removing the line reproduces it); `dependencyInsight --dependency support-compat` shows the chain. Calling (`calls-sdk-android:5.0.4`) additionally needs `minSdk 26` + the SoLoader init + a manifest `<service>` — `cometchat-android-v5-calls-sdk` Prerequisites.
Manifest needs `android.permission.INTERNET`. Credentials live in the **gitignored** `app/src/main/assets/cometchat-settings.json` (`appId`, `region`, `credentials.authKey` dev-only). The optional `chatSDK` section carries SDK-level overrides; init succeeds without it, so omit it for a minimal build — **BUT one override is load-bearing for a required surface:**

> ⚠️ **Presence is opt-in via `chatSDK.presenceSubscription` — omit it and realtime presence is silently dead.** The app-surface floor requires a presence-aware chat header + users list (`onUserOnline`/`onUserOffline`). `initFromSettings` only subscribes to presence if the asset sets `chatSDK.presenceSubscription`; **if it's absent, `onUserListener` events NEVER fire** (docs `/sdk/android/v5/user-presence`: "If none of the above methods are set, no presence will be sent"). Accepted values (verified against the AAR settings parser — bad values throw `ERR_SETTINGS_FILE_INVALID_PRESENCE_TYPE`): `ALL_USERS` · `FRIENDS` · `ROLES` (with a sibling `roles` list) · `NONE`. So whenever you wire the presence surface, ship:
> ```json
> { "appId": "…", "region": "…", "credentials": { "authKey": "…" },
>   "chatSDK": { "presenceSubscription": "ALL_USERS" } }
> ```
> Distinguish the two presence paths: `getUser(uid).status` / the `UsersRequest` list `status` field is a **one-time snapshot** (works without the subscription); the **realtime** `onUserOnline`/`onUserOffline` transitions need the subscription above.

> ⚠️ **Docs drift — `ConnectionListener`.** `/sdk/android/v5/connection-status.md` shows
> `override fun onError(e: CometChatException)`. That does not compile: the member is
> **`onConnectionError(e: CometChatException?)`**, and `ConnectionListener` is an **interface** —
> `object : CometChat.ConnectionListener` with **no parentheses**, unlike `CometChat.MessageListener()`.
> Verified against `CometChat.java:10737`.

## Init & login ordering (BAKED — invariant)
`CometChat.initFromSettings(...)` resolves → `login(...)` resolves → everything else. Any SDK call before init fails; login before init **fails silently**.
```kotlin
import com.cometchat.chat.core.CometChat
import com.cometchat.chat.exceptions.CometChatException
import com.cometchat.chat.models.User

CometChat.initFromSettings(context, object : CometChat.CallbackListener<String>() {
    override fun onSuccess(p: String) {                       // init resolved — telemetry source persisted
        if (CometChat.getLoggedInUser() == null) {
            // ⚠️ TWO DIFFERENT overloads — they are not interchangeable:
            //   dev  : login(uid, authKey, listener)   ← 3 args, uid REQUIRED
            //   prod : login(authToken, listener)      ← 2 args, NO uid (the token identifies the user)
            // Passing a token in the 3-arg form sends it as an apiKey and fails.
            // WHERE `authKey` COMES FROM (headless has no UI-Kit shortcut): read it back out of the
            // same gitignored settings asset you already ship — never hardcode it, and never add a
            // second copy in source:
            //   val cfg = JSONObject(assets.open("cometchat-settings.json").bufferedReader().readText())
            //   val authKey = cfg.getJSONObject("credentials").getString("authKey")
            // Guard the read: if the asset is missing this throws BEFORE the SDK can report its own
            // clean ERR_SETTINGS_FILE_NOT_FOUND, turning a clear error into a crash.
            CometChat.login(uid, authKey, object : CometChat.CallbackListener<User>() {
                override fun onSuccess(user: User) { /* unlock the app */ }
                override fun onError(e: CometChatException) { /* surface e.code + e.message */ }
            })
        } else { /* session already live */ }
    }
    override fun onError(e: CometChatException?) { /* surface — do NOT proceed */ }
})
```
`initFromSettings` reads the assets settings file and persists the integration source; the classic `CometChat.init(context, appId, AppSettings, callback)` still exists but is **not** the default (loses attribution). **Prod:** mint a per-user auth token server-side and log in with it; the Auth Key is dev-only. Re-logging a *different* user requires `logout` first.

## SDK method map (BAKED closed list — catalog-verified)
**Constants & models packages** — `com.cometchat.chat.core.*` (`CometChat`, `Call`, and the `*Request`/`*RequestBuilder` types) · `com.cometchat.chat.models.*` (`User`, `Group`, `TextMessage`, `MediaMessage`, `BaseMessage`, `TypingIndicator`) · `com.cometchat.chat.constants.CometChatConstants` (**`RECEIVER_TYPE_USER`/`RECEIVER_TYPE_GROUP` live HERE, not on `CometChat`**) · `com.cometchat.chat.exceptions.CometChatException`.
**Auth overloads (do not conflate)** — `login(uid, authKey, listener)` for dev; `login(authToken, listener)` for production, which takes **no uid** because the server-minted token carries the identity. Getting this wrong is silent: the token goes through as an apiKey and auth fails.
**Session** `initFromSettings` · `init` (legacy) · `login` · `logout` · `getLoggedInUser` · `getUserAuthToken` · `addLoginListener`/`LoginListener`/`removeLoginListener`
**Messaging** `TextMessage` · `MediaMessage` · `CustomMessage` · `InteractiveMessage` · `sendMessage` · `sendMediaMessage` · `sendCustomMessage` · `sendInteractiveMessage` · `editMessage` · `deleteMessage` · `flagMessage`/`getFlagReasons` · `sendTransientMessage`/`TransientMessage` · `getMessageDetails` · `BaseMessage` · `Attachment` · `createUploadFileRequest`/`UploadFileRequest`/`UploadFileListener`
**Fetching (always via a request builder + pagination)** `MessagesRequest.MessagesRequestBuilder` · `ConversationsRequest.ConversationsRequestBuilder` · `UsersRequest.UsersRequestBuilder` · `GroupsRequest.GroupsRequestBuilder` · `GroupMembersRequest.GroupMembersRequestBuilder` · `BannedGroupMembersRequest…` · `BlockedUsersRequest…` · `ReactionsRequest…` · `NotificationFeedRequest…`
**Realtime listeners** `addMessageListener`/`MessageListener`/`removeMessageListener` · `addUserListener`/`UserListener`/… · `addGroupListener`/`GroupListener`/… · `addCallListener`/`CallListener`/… · `addConnectionListener`/`ConnectionListener`/… · `addAIAssistantListener`/`AIAssistantListener`/… · `addNotificationFeedListener`/`NotificationFeedListener`/…
**Receipts & typing** `startTyping`/`endTyping`/`TypingIndicator` · `markAsDelivered`/`markAsRead`/`markAsUnread`/`markConversationAsRead` · `MessageReceipt`/`getMessageReceipts` · unread: `getUnreadMessageCount`/`…ForUser`/`…ForGroup`
**Reactions** `addReaction`/`removeReaction`/`Reaction`/`ReactionCount`
**Users** `getUser` · `createUser`/`updateUser`/`updateCurrentUserDetails` · `blockUsers`/`unblockUsers` · `User`
**Groups** `createGroup`/`createGroupWithMembers` · `joinGroup`/`leaveGroup` · `updateGroup`/`deleteGroup`/`getGroup`/`getJoinedGroups` · `addMembersToGroup`/`kickGroupMember`/`banGroupMember`/`unbanGroupMember` · `updateGroupMemberScope`/`transferGroupOwnership` · `Group`/`GroupMember`
**Conversations** `getConversation` · `deleteConversation` · `tagConversation` · `Conversation`
**Calls** `initiateCall`/`acceptCall`/`rejectCall`/`endCall`/`startCall` · `getActiveCall`/`clearActiveCall` · `Call`/`CallSettings.CallSettingsBuilder`
**AI** `getSmartReplies` · `getConversationStarter` · `getConversationSummary` · `askBot` · `isAIFeatureEnabled` · `AIAssistantMessage` + the `AIAssistant*Event` family
**Push & feed** `registerTokenForPushNotification` · `CometChatNotifications` · `PushPlatforms` · `NotificationFeedItem`/`getNotificationFeedUnreadCount`
**Connection** `getConnectionStatus` · `connect`/`disconnect`/`ping`
Not in this map and not in the catalog ⇒ does not exist: fetch the page via `references/docs-map.md` before assuming.

## Listener lifecycle (the #1 source of Android SDK bugs)
Every `add*Listener(UNIQUE_ID, …)` **must** have a matching `remove*Listener(UNIQUE_ID)` on teardown — `onDestroy` (Activity/Fragment), `DisposableEffect`'s `onDispose` (Compose), or `onCleared` (ViewModel). Register with a stable, unique id (e.g. the screen's class name); registering the same id twice replaces silently, never removing leaks the callback and duplicates handling after rotation.
```kotlin
DisposableEffect(Unit) {
    CometChat.addMessageListener(LISTENER_ID, object : CometChat.MessageListener() {
        override fun onTextMessageReceived(message: TextMessage) { /* append to state */ }
    })
    onDispose { CometChat.removeMessageListener(LISTENER_ID) }
}
```
Realtime arrives via listeners — **never poll**.

## Least-code recipe — the production floor (contract `sdk-chat-surface`)
Because the SDK ships no UI, a generic "build chat with the SDK" must deliver a **complete, production-ready app**, not bare bubbles. The floor (full text in `contracts.sdk-android-v5.json`, UI spec in `references/app-surface.md`):
- **Data**: conversations + users + groups lists, each **searchable** (`setSearchKeyword` on the builder) and **paginated** via request builders (`setLimit` + fetch-next) — never one unbounded fetch. Scope the request to the product (1:1-only vs groups) instead of filtering client-side.
- **Messaging**: send text/media, message history, **threads** via `setParentMessageId`, edit/delete/react/report — each wired to the SDK **and** reflected in the UI, with own-message gating for edit/delete.
- **Realtime**: message/user/group/connection listeners registered and removed as above; typing indicators and receipts wired.
- **Detail screens**: user (block/unblock) and group (add/kick/ban/scope/leave), role-gated.
- **UX quality**: **optimistic updates** (show the message as sending immediately, reconcile in `onSuccess`, roll back + surface `CometChatException.message` in `onError`), **loading/empty/error states everywhere** (never a blank screen or `[object Object]`), a **sized shell** (`fillMaxSize`/`match_parent`, list scrolls internally, insets + IME handled), and your app's **existing design system** (Material3 theme or your tokens) — never ad-hoc inline styling.
- **Errors**: every `CallbackListener` implements `onError` and surfaces something actionable. An empty `onError {}` is the defect this contract exists to prevent.

## Deep references (load only when the task needs them)
- `references/docs-map.md` — intent → the exact `/sdk/android/v5/<page>.md` to fetch (+ the v5-vs-v4 URL trap and the scoped LLM index).
- `references/app-surface.md` — the own-UI production floor in detail (state model, optimistic mutations, list/pagination patterns, error/empty/loading, sizing).

## Common pitfalls
**reversed param order** — `updateGroupMemberScope(UID, GUID, scope, …)` vs `transferGroupOwnership(GUID, UID, …)` · **search-keyword casing differs per builder** — `UsersRequestBuilder.setSearchKeyword` and `ConversationsRequestBuilder.setSearchKeyword` are lowercase, but `GroupsRequestBuilder.setSearchKeyWord` has a **capital W** (SDK inconsistency; using `setSearchKeyword` on GroupsRequest is `Unresolved reference`) · **conversations search is plan-gated** — `ConversationsRequestBuilder.setSearchKeyword`/`setUnread` need the **"Conversation & Advanced Search"** feature (Advanced/Custom plan + dashboard toggle); off-plan it **silently returns the unfiltered list** (a search box that looks broken). Users/Groups search is NOT plan-gated. · passing an auth **token** into the 3-arg `login(uid, authKey, …)` (tokens use the 2-arg `login(authToken, …)`) · `CometChat.RECEIVER_TYPE_USER` (it is `CometChatConstants.RECEIVER_TYPE_USER`) · **presence never fires without `chatSDK.presenceSubscription`** in the settings asset (see Prerequisites) · importing `Call` from `chat.models` instead of `chat.core` · Any SDK call before init resolves · login before init (silent failure) · Auth Key shipped in a release build · listeners never removed (duplicate handling after rotation) · polling instead of listeners · unbounded fetches with no pagination · empty `onError` blocks · blocking the main thread waiting on callbacks · re-login without logout · using the unversioned `/sdk/android/` v4 docs · rebuilding UI the UI Kit already ships (when the user would accept drop-ins).

## Verify it works
Every symbol you emitted is in `sdk-android-v5.json` (Tier-1) and the app compiles: run `./gradlew :app:assembleDebug` in the user's app. On device: init → login succeed (logcat); the conversations/users/groups lists load and paginate; sending appears instantly and reconciles; a message from another user arrives **live** (listener, not refresh); edit/delete/react update in place; rotating the screen doesn't duplicate messages (listener lifecycle); force an error (airplane mode) → a readable error state, not a blank screen or crash. Live backend round-trip smoke for this family is **not automated yet** (parked with the Android native harness) — verify manually and say so.
