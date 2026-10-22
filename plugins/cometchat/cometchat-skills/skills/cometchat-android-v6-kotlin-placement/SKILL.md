---
name: cometchat-android-v6-kotlin-placement
description: "Where the CometChat Android v6 chat UI goes in a Kotlin XML Views app — the default conversations→message Activity flow, growing to the tab-based app (chats/users/groups/calls + detail, thread and search screens + incoming calls), a single one-to-one screen, or chat embedded in an existing Activity/Fragment, with a correct back stack. Triggers: 'tab based chat android', 'add a chat tab to my app', 'open a chat screen for this user', 'embed cometchat in my activity', 'full chat app android kotlin'."
license: "MIT"
compatibility: "Android minSdk >=28; compileSdk >=36; Kotlin >=2.1; AGP >=8.9.1; JVM target 11; com.cometchat:chatuikit-kotlin-android ^6 (XML Views cohort) — 6.0.x, verified 6.0.5; com.cometchat:chat-sdk-android ^5"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android placement layout v6 kotlin views navigation activity"
---

> **Ground truth:** catalog `android-v6.json` + `contracts.android-v6.json` (`core-chat-surface`, `chat-experience`) + the live recipes (`conversation-message-view`, `tab-based-chat`, `one-to-one-chat`). Signatures below were verified against the INSTALLED 6.0.5 source. Fetch anything else from docs (`core` → `references/docs-map.md`).
>
> ⚠️ **Kotlin XML Views cohort.** Screens are Activities/Fragments hosting kit Views. The Compose cohort (NavHost + composables) is a separate skill.

## Companion skills (read first)
- `cometchat-android-v6-core` — install, credentials, `initFromSettings → login → render`, and **`references/layout.md` (the ONE sizing standard)**. Sizing rules live THERE; this skill places screens.
- `cometchat-android-v6-kotlin-components` — what exists in this cohort.

## Use this skill when
"put chat behind a tab", "build the full chat app", "open a chat screen for this user/group", "embed the conversation list in an existing screen", "how should I navigate between the list and the messages".

## Prerequisites & install
Same kit + `initFromSettings → login` gate as `core` — **no chat Activity is started before login resolves.** Every Activity below must be lifecycle-aware (`AppCompatActivity`/`ComponentActivity`/`FragmentActivity`) — the kit hooks lifecycle events — and **registered in `AndroidManifest.xml`**.

## The rule that governs every layout: one screen per Activity
Android composes by **navigation**, not by side-by-side panes. The list, the message screen, the thread and search are separate destinations with a real back stack. Never build a web-style two-pane split or a "side panel" on a phone.

## Placement 1 — conversations → messages (the default)
The `core-chat-surface` contract. `core` carries the full code; the structure:

```kotlin
// ConversationActivity — the list
conversations.setOnItemClick { conversation ->
    val intent = Intent(this, MessageActivity::class.java)
    when (val entity = conversation.conversationWith) {
        is User -> intent.putExtra("user", entity)
        is Group -> intent.putExtra("group", entity)
    }
    startActivity(intent)
}
conversations.setOnSearchClick { startActivity(Intent(this, SearchActivity::class.java)) }
```
`activity_message.xml` is a vertical `LinearLayout`: header `wrap_content` → list **`0dp` + `layout_weight="1"`** → composer `wrap_content`, all `match_parent` wide. The weight is what makes the list scroll instead of pushing the composer off-screen. Bind the SAME `User`/`Group` into header + list + composer, and wire `header.setOnBackPress { finish() }`.

**Thread and search are part of this default** — see Placement 3's screens; wire them or hide the affordance.

## Placement 2 — a chat tab in an existing app
Host `CometChatConversations` in a Fragment inside your existing `BottomNavigationView`/`ViewPager2`. The tab shows the LIST; tapping a row starts the message Activity **full-screen above the tab bar** (not inside the tab), so the composer isn't fighting the nav bar. Reuse the host's navigation graph — additive only, never rewrite it.

**Brownfield theming — the host Activity KEEPS its own theme.** Kit views resolve `?attr/cometchat*` tokens at inflate time: constructed with the host's context (its own Material3 theme), the list crashes on first show — `InflateException … MaterialButton` on `?attr/cometchatPrimaryColor` (verified on device). Do NOT re-parent the `<application>` theme (that's `core`'s greenfield path; it breaks a Material3 host's own screens). Scope instead:
```xml
<!-- res/values/themes.xml — your app theme stays untouched -->
<style name="Theme.YourApp.Chat" parent="CometChatTheme.DayNight">
    <item name="cometchatPrimaryColor">@color/your_brand</item>
</style>
<!-- AndroidManifest.xml: android:theme="@style/Theme.YourApp.Chat" on EACH chat Activity -->
```
```kotlin
// Fragment/tab-embedded kit views: wrap the context; the host Activity keeps its theme
val themed = android.view.ContextThemeWrapper(requireContext(), R.style.Theme_YourApp_Chat)
val conversations = CometChatConversations(themed)
```

## Placement 3 — grow to the full app (the tab-based recipe)
The `chat-experience` contract, from the docs `tab-based-chat` page: a `BottomNavigationView` over four destinations — **Chats** (`CometChatConversations`) · **Users** (`CometChatUsers`) · **Groups** (`CometChatGroups`) · **Calls** (`CometChatCallLogs`) — each item click routing into the same message Activity.

> ⚠️ **A Groups tap is NOT a Conversations tap.** `CometChatGroups` lists groups the user may not
> have joined; routing one straight into the message screen renders the kit's error state with a
> live-but-dead composer (verified on device). Before navigating, check membership
> (`group.isJoined` — the field `hasJoined` is private; `isJoined()` is the accessor) and, when false, join first — `CometChat.joinGroup(guid, groupType, password, CallbackListener<Group>)` — the listener is REQUIRED (4 params)
> — prompting for the password when `groupType` is `CometChatConstants.GROUP_TYPE_PASSWORD`. Only a
> Conversations row is guaranteed joined, because a conversation only exists once you are in it.

Then, as the plan names them:
- **Detail screens** — user detail (block/unblock) and group detail via `CometChatGroupMembers` (kick/ban/scope, role-gated).
- **Thread screen** — `CometChatThreadHeader` + a parent-scoped list/composer:
```kotlin
// ThreadActivity — header takes the parent MESSAGE, list + composer take its ID (Long)
threadHeader.setParentMessage(parent)
threadList.setParentMessageId(parent.id)
threadComposer.setParentMessageId(parent.id)
// AND the conversation target, or replies silently never send:
user?.let { threadList.setUser(it); threadComposer.setUser(it) }
group?.let { threadList.setGroup(it); threadComposer.setGroup(it) }
```
- **Search screen** — `CometChatSearch`; global by default, or scoped to the open chat with `setUid(...)`/`setGuid(...)`, plus `setSearchIn(listOf(SearchScope.CONVERSATIONS, SearchScope.MESSAGES))` (import `com.cometchat.uikit.core.constants.SearchScope`) and `setOnConversationClick`/`setOnMessageClick`.
- **Incoming calls at app level** — `CometChatIncomingCall` driven by a global call listener so a call rings from any tab (→ `cometchat-android-v6-calls`).

Each tab keeps its own back stack.

## Placement 4 — embed in an existing screen
Drop a component into a slice of your own layout: `0dp` + constraints inside a `ConstraintLayout`, or a fixed `dp` height — **never `wrap_content`**. The kit fills the box you give it, so an unsized box renders nothing. Useful for a support widget or a chat panel inside a larger screen.

## Placement 5 — deep entry from an arbitrary screen (known UID/GUID)
"Open a chat with THIS user" from one of your own screens (an order, an article, a ticket): gate on the same init/login, resolve the entity with the Chat SDK, then start the SAME message Activity from Placement 1 with the entity extra (docs: `core` → `references/docs-map.md` → `one-to-one-chat`):
```kotlin
CometChat.getUser(uid, object : CometChat.CallbackListener<User>() {   // groups: CometChat.getGroup(guid, …)
    override fun onSuccess(user: User) {
        startActivity(Intent(this@YourActivity, MessageActivity::class.java).putExtra("user", user))
    }
    override fun onError(e: CometChatException) { /* SURFACE it (toast/snackbar) — ERR_UID_NOT_FOUND must not dead-end */ }
})
```
Verified in the installed SDK: `CometChat.getUser(@NonNull String, @NonNull CallbackListener<User>)` / `CometChat.getGroup(@NonNull String, @NonNull CallbackListener<Group>)`.

## Sizing and the keyboard
Owned by `core/references/layout.md`; the two that bite in Views: `android:windowSoftInputMode="adjustResize"` on the message Activity (or the composer hides under the IME), and `enableEdgeToEdge()` + inset padding (or the header/composer sit under the system bars). Never nest `CometChatMessageList` in a `ScrollView`.

## Navigation & back-stack discipline
Every pushed screen pops correctly: header `setOnBackPress` → `finish()`; thread/search/detail → back returns to the message screen; predictive-back safe. Pass `User`/`Group` as Parcelable extras (or re-fetch by uid/guid on the destination — Placement 5's `getUser`/`getGroup` — safer across process death). Never re-`init`/`login` per Activity; that happened once at startup.

## Common pitfalls
Starting a chat Activity before login resolves · inflating a kit view under the host's own theme (brownfield: scoped theme + `ContextThemeWrapper`, Placement 2 — never re-parent the application theme of an app with its own design system) · a swallowed `getUser`/`getGroup` `onError` (Placement 5) · a non-lifecycle host Activity · Activity missing from the manifest · `wrap_content`/unsized parent · missing `layout_weight="1"` on the list (composer pushed off-screen) · composer under the IME · thread screen missing the `user`/`group` target · thread/search opened with no way back · nesting the message list in another scrollable.

## Verify it works
Compile: `./gradlew :app:assembleDebug   # in YOUR app (native-fence.mjs is a pack-repo gate, not installed by the CLI)`. On device: list → tap → message screen for the right entity; back returns; composer stays visible with the keyboard open; nothing under the system bars; thread and search open AND return; on the grown app each tab renders and an incoming call surfaces from any tab. A sliver or a top-left cram is a HOST sizing defect → `core/references/layout.md`.
