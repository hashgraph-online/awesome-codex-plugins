---
name: cometchat-android-v6-compose-placement
description: "Where the CometChat Android v6 chat UI goes in a Jetpack Compose app — the default conversations→message NavHost flow, growing to the tab-based app (chats/users/groups/calls + detail, thread and search routes + incoming calls), a single one-to-one screen, or chat embedded in an existing composable, with a correct back stack and IME handling. Triggers: 'cometchat compose navigation', 'chat screen navhost', 'tab based chat compose', 'embed cometchat in a composable', 'full chat app jetpack compose'."
license: "MIT"
compatibility: "Android minSdk >=28; compileSdk >=36; Kotlin >=2.1; AGP >=8.9.1; JVM target 11; com.cometchat:chatuikit-compose-android ^6 (Jetpack Compose cohort) — 6.0.x, verified 6.0.5; com.cometchat:chat-sdk-android ^5"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android placement layout v6 compose navhost scaffold"
---

> **Ground truth:** catalog `android-v6.json` + `contracts.android-v6.json` (`core-chat-surface`, `chat-experience`) + the docs recipes (`conversation-message-view`, `tab-based-chat`, `one-to-one-chat` — Compose tab). Param shapes verified against the INSTALLED 6.0.5 Compose source.
>
> ⚠️ **Jetpack Compose cohort.** Screens are composables on a `NavHost`. The Views cohort (Activities + XML) is a separate skill.

## Companion skills (read first)
- `cometchat-android-v6-core` — install, credentials, `initFromSettings → login → render`, and **`references/layout.md`** (the ONE sizing standard). Sizing rules live THERE.
- `cometchat-android-v6-compose-components` — the param conventions (`onX` / `hideX` / `@Composable` slots).

## Use this skill when
"add a chat route to my NavHost", "build the full chat app in Compose", "open a chat screen for this user", "embed the conversation list in an existing composable", "the composer is under the keyboard".

## Prerequisites & install

> ⚠️ **Required on Compose too:** `configurations.all { exclude(group = "org.jetbrains", module = "annotations-java5") }` plus `android.useAndroidX=true` + `android.enableJetifier=true` in `gradle.properties`. The collision arrives via `chatuikit-core-android`, which BOTH cohorts pull, so a Compose-only app fails its FIRST build without them (~40 `Duplicate class` errors). Full block: `cometchat-android-v6-core` §Prerequisites & install.
Same kit + `initFromSettings → login` gate as `core` — **no chat route is shown before login resolves**; gate the NavHost (or the start destination) on it. Compose cohort artifact only.

## The rule that governs every layout: one screen per route
Compose composes by **navigation**, not side-by-side panes. List, message, thread and search are separate `NavHost` destinations with a real back stack. Never build a web-style two-pane split on a phone.

**Add Navigation Compose — the kit does not pull it in.** Every placement below uses `NavHost` / `rememberNavController`; without the dependency the app fails with `Unresolved reference: rememberNavController`:
```kotlin
// app/build.gradle.kts — 2.8.0 matches the kit's compose-bom 2024.09.00 (what the pack's Compose harness builds with)
implementation("androidx.navigation:navigation-compose:2.8.0")
```

## Placement 1 — conversations → messages (the default)
The `core-chat-surface` contract. `core` carries the full code; the structure:

```kotlin
// Two NavHost destinations, NOT an if/else swap — see the ⚠️ note below (the default surface
// includes threads). The selection is hoisted above the NavHost; Placement 3 shows the
// process-death-safe variant (route args + re-fetch by uid/guid).
@Composable
fun ChatApp() {
    val navController = rememberNavController()
    var selectedUser by remember { mutableStateOf<User?>(null) }
    var selectedGroup by remember { mutableStateOf<Group?>(null) }

    NavHost(navController, startDestination = "conversations") {
        composable("conversations") {
            CometChatConversations(
                modifier = Modifier.fillMaxSize(),
                title = "Chats",
                onItemClick = { conversation ->
                    when (val entity = conversation.conversationWith) {
                        is User -> { selectedUser = entity; selectedGroup = null }
                        is Group -> { selectedGroup = entity; selectedUser = null }
                    }
                    navController.navigate("messages")
                },
            )
        }
        composable("messages") {
            MessageScreen(selectedUser, selectedGroup) { navController.popBackStack() }
        }
        // + composable("thread") { … } — its own destination (Thread route, Placement 3)
    }
}
```
```kotlin
@Composable
fun MessageScreen(user: User?, group: Group?, onBack: () -> Unit) {
    Scaffold(contentWindowInsets = WindowInsets.statusBars) { padding ->
        Column(
            modifier = Modifier.fillMaxSize().padding(padding)
                .consumeWindowInsets(padding).navigationBarsPadding().imePadding()
        ) {
            CometChatMessageHeader(
                modifier = Modifier.fillMaxWidth(),
                user = user, group = group,
                hideBackButton = false, onBackPress = onBack,
            )
            CometChatMessageList(
                modifier = Modifier.fillMaxWidth().weight(1f),   // weight(1f) = the list scrolls
                user = user, group = group,
            )
            CometChatMessageComposer(modifier = Modifier.fillMaxWidth(), user = user, group = group)
        }
    }
}
```
> ⚠️ **Use a `NavHost`, not `if/else` — mandatory as soon as a THREAD is in play (the default
> surface includes one), so Placement 1 already uses it. This is correctness, not polish.** `CometChatMessageList` resolves its `CometChatMessageListViewModel` from the enclosing
> `ViewModelStoreOwner`. In one `if/else` composition scope both the main list and the thread list
> share the Activity's store, so the thread REUSES the main chat's ViewModel, `parentMessageId` is
> inert, and the thread screen silently renders the ENTIRE conversation — no error, no warning
> (verified on device, 6.0.6). Each `NavHost` destination is its own `ViewModelStoreOwner`, which
> is what makes the thread scope hold. A production app also gets a real back stack from it. Pass `User`/`Group` (both `Parcelable`) or re-fetch by uid/guid on the destination (Placement 5's `getUser`/`getGroup`) — safer across process death.

**`weight(1f)` on the list is load-bearing**: without it the list is unbounded and the composer is pushed off-screen. `imePadding()` keeps the composer above the keyboard.

## Placement 2 — a chat tab in an existing app
Put `CometChatConversations` inside your existing `Scaffold` + `NavigationBar` tab. The tab shows the LIST; tapping a row navigates to the message route **above** the bottom bar (full-screen), so the composer isn't fighting the nav bar. Reuse the host's `NavHost` — additive, never rewrite the graph.

## Placement 3 — grow to the full app (the tab-based recipe)
The `chat-experience` contract: a `NavigationBar` over four destinations — **Chats** (`CometChatConversations`) · **Users** (`CometChatUsers`) · **Groups** (`CometChatGroups`) · **Calls** (`CometChatCallLogs`) — each item click routing into the same message screen. Then, as the plan names them:

```kotlin
// Four-tab navigation — each tab hosts one list component; rows route into the message screen.
// Every route you navigate to MUST be declared here: a bare "messages/{id}" with no matching
// composable throws IllegalArgumentException on the first tap. Conversations/Users/Groups all
// resolve to the same two message destinations, keyed user-vs-group.
@Composable
fun AppNavigation(navController: NavHostController) {
    NavHost(navController, startDestination = "chats") {
        composable("chats") {
            CometChatConversations(onItemClick = { conv ->
                when (val e = conv.conversationWith) {   // a conversation is WITH a User or a Group
                    is User  -> navController.navigate("messages/u/${e.uid}")
                    is Group -> navController.navigate("messages/g/${e.guid}")
                }
            })
        }
        composable("users")  { CometChatUsers(onItemClick  = { user  -> navController.navigate("messages/u/${user.uid}") }) }
        composable("groups") { CometChatGroups(onItemClick = { group -> navController.navigate("messages/g/${group.guid}") }) }
        composable("calls")  { CometChatCallLogs() }

        // The message destination — re-fetch the entity by id (safe across process death), then reuse
        // MessageScreen from Placement 1. rememberUser/rememberGroup wrap the verified Placement-5 getters.
        composable("messages/u/{uid}") { back ->
            rememberUser(back.arguments?.getString("uid"))?.let { user ->
                MessageScreen(user = user, group = null) { navController.popBackStack() }
            }
        }
        composable("messages/g/{guid}") { back ->
            rememberGroup(back.arguments?.getString("guid"))?.let { group ->
                MessageScreen(user = null, group = group) { navController.popBackStack() }
            }
        }
        composable("members/{guid}") { back ->
            // Group details: CometChatGroupMembers with built-in kick/ban/scope actions
            rememberGroup(back.arguments?.getString("guid"))?.let { group ->
                CometChatGroupMembers(group = group)
            }
        }
    }
}

// Re-fetch by id with the Chat SDK (the Placement-5 getters), surfaced to Compose via produceState.
@Composable fun rememberUser(uid: String?): User? = produceState<User?>(null, uid) {
    val id = uid ?: return@produceState
    CometChat.getUser(id, object : CometChat.CallbackListener<User>() {
        override fun onSuccess(u: User) { value = u }
        override fun onError(e: CometChatException) { /* SURFACE it — ERR_UID_NOT_FOUND must not dead-end */ }
    })
}.value
@Composable fun rememberGroup(guid: String?): Group? = produceState<Group?>(null, guid) {
    val id = guid ?: return@produceState
    CometChat.getGroup(id, object : CometChat.CallbackListener<Group>() {
        override fun onSuccess(g: Group) { value = g }
        override fun onError(e: CometChatException) { /* SURFACE it */ }
    })
}.value
```

> ⚠️ **A Groups tap is NOT a Conversations tap.** `CometChatGroups` lists groups the user may not
> have joined; routing one straight to the message screen renders the kit's error state with a
> live-but-dead composer (verified on device). Gate on membership (`group.isJoined` — the field
> `hasJoined` is private; `isJoined()` is the accessor) and join first when false —
> `CometChat.joinGroup(guid, groupType, password, CallbackListener<Group>)` — the listener is REQUIRED (4 params), prompting for the password when `groupType` is
> `CometChatConstants.GROUP_TYPE_PASSWORD`. Only a Conversations row is guaranteed joined, because
> a conversation exists only once you are in it.

- **Detail routes** — user detail (block/unblock) and group detail via `CometChatGroupMembers` (kick/ban/scope, role-gated).
- **Thread route** — note Compose takes the parent as **params**, not setters:
```kotlin
CometChatThreadHeader(modifier = Modifier.fillMaxWidth(), parentMessage = parent)
CometChatMessageList(
    modifier = Modifier.fillMaxWidth().weight(1f),
    user = user, group = group,          // the SAME target, or replies silently never send
    parentMessageId = parent.id,
)
CometChatMessageComposer(
    modifier = Modifier.fillMaxWidth(),
    user = user, group = group, parentMessageId = parent.id,
)
```
- **Search route** — (import `com.cometchat.uikit.core.constants.SearchScope`) `CometChatSearch(searchScopes = listOf(SearchScope.CONVERSATIONS, SearchScope.MESSAGES), uid = …, guid = …, onConversationClick = …, onMessageClick = …, onBackPress = …)`. Omit `uid`/`guid` for global search; pass one to scope to the open chat.
- **Incoming calls at app level** — `CometChatIncomingCall` driven by a global call listener, hoisted above the NavHost so a call surfaces from any tab (→ `cometchat-android-v6-calls`).

Each tab keeps its own back stack (`navController` per tab, or `saveState`/`restoreState` on the bottom-nav items).

## Placement 4 — embed in an existing composable
Give the component a bounded box: `Modifier.weight(1f)` inside a `Column`, `Modifier.height(360.dp)`, or `fillMaxSize()` in its own pane. **Never place it in an unbounded parent** (a `Column` with `verticalScroll`, or no weight) — the kit fills what you give it, and unbounded means nothing. Never nest `CometChatMessageList` inside another scrollable.

## Placement 5 — deep entry from an arbitrary screen (known UID/GUID)
"Open a chat with THIS user" from one of your own screens (an order, an article, a ticket): gate on the same init/login, resolve the entity with the Chat SDK, then navigate to the SAME message destination from Placement 1 with it (docs: `core` → `references/docs-map.md` → `one-to-one-chat`):
```kotlin
CometChat.getUser(uid, object : CometChat.CallbackListener<User>() {   // groups: CometChat.getGroup(guid, …)
    override fun onSuccess(user: User) {
        navController.navigate(messageRouteFor(user))   // or Placement 1: set selectedUser, then navigate("messages")
    }
    override fun onError(e: CometChatException) { /* SURFACE it (snackbar) — ERR_UID_NOT_FOUND must not dead-end */ }
})
```
Verified in the installed SDK: `CometChat.getUser(@NonNull String, @NonNull CallbackListener<User>)` / `CometChat.getGroup(@NonNull String, @NonNull CallbackListener<Group>)`.

## Sizing and the keyboard
Owned by `core/references/layout.md`; the Compose specifics: `Scaffold(contentWindowInsets = WindowInsets.statusBars)` + `.consumeWindowInsets(padding)` + `.navigationBarsPadding()` + **`.imePadding()`**, and `enableEdgeToEdge()` in the host Activity. Missing `imePadding()` is the #1 Compose complaint (composer under the keyboard).

## Navigation & back-stack discipline
Every route pops correctly: `onBackPress` → `navController.popBackStack()`; thread/search/detail → back returns to the message route; predictive-back safe. Never re-`init`/`login` per screen — that happened once at startup.

## Common pitfalls
Showing a chat route before login resolves · a swallowed `getUser`/`getGroup` `onError` (Placement 5) · missing `weight(1f)` (composer pushed off-screen) · missing `imePadding()` · unbounded parent (renders nothing) · nesting the message list in a scrollable · thread route missing the `user`/`group` target · using `setParentMessageId(...)` (that's the Views cohort — Compose takes `parentMessageId =`) · rebuilding the host's nav graph instead of adding routes.

## Verify it works
Compile: `./gradlew :app:assembleDebug   # in YOUR app (native-fence.mjs is a pack-repo gate, not installed by the CLI)`. On device: list → tap → message screen for the right entity; system back returns; composer stays visible with the keyboard open; nothing under the system bars; thread and search open AND return; on the grown app each tab renders and an incoming call surfaces from any tab.
