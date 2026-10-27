---
name: cometchat-android-v6-events
description: "React to what the CometChat Android v6 UI Kit is doing — the CometChatEvents SharedFlow bus (message, call, conversation, group, user and UI events), how to collect it in Compose vs XML Views with correct lifecycle scoping, and when to use UI-Kit events versus Chat SDK listeners. Triggers: 'listen for message sent android cometchat', 'cometchat events android', 'know when a call is accepted', 'react when a group is created', 'sdk listener vs uikit event'."
license: "MIT"
compatibility: "Android minSdk >=28; compileSdk >=36; Kotlin >=2.1; AGP >=8.9.1; JVM target 11; com.cometchat:chatuikit-kotlin-android ^6 OR com.cometchat:chatuikit-compose-android ^6 (6.0.x, verified 6.0.5); com.cometchat:chat-sdk-android ^5"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android events v6 sharedflow lifecycle compose views"
---

> **Ground truth:** catalog `android-v6.json` + the live pages `events` (the API reference) and `customization-events`. `CometChatEvents` lives in `chatuikit-core-android` (`com.cometchat.uikit.core.events.CometChatEvents`). Verify symbols against the catalog; fetch the exact sealed-class members from the docs page — the event lists below are a MAP, the page is the manual.

## Companion skills (read first)
- `cometchat-android-v6-core` — install, credentials, `initFromSettings → login → render`, the fetch map. Assumed here, never repeated.
- `cometchat-android-v6-{kotlin,compose}-customization` — click/selection callbacks on a single component (usually the simpler answer than the global bus).

## Use this skill when
"tell me when a message is sent/edited/deleted", "run code when a call is accepted", "update my own badge when a conversation changes", "hook into group/member changes", "what's the difference between an SDK listener and a UI Kit event?".

## Prerequisites & install
Same kit + init as `core`. `CometChatEvents` ships in `chatuikit-core-android` (already a transitive dependency of both cohort artifacts) — nothing to add.

## The event bus (BAKED map — fetch the page for each sealed class's members)
All events come from the **`CometChatEvents` singleton**; each domain exposes a **`SharedFlow`** of a sealed class:

| Flow | Sealed class | What it covers |
|---|---|---|
| `CometChatEvents.messageEvents` | `CometChatMessageEvent` | sent · edited · deleted · read · live reaction · interactive/card/form/scheduler received |
| `CometChatEvents.callEvents` | `CometChatCallEvent` | call initiated · accepted · rejected · ended |
| `CometChatEvents.conversationEvents` | `CometChatConversationEvent` | conversation deleted · updated |
| `CometChatEvents.groupEvents` | `CometChatGroupEvent` | group created/deleted · member changes |
| `CometChatEvents.userEvents` | `CometChatUserEvent` | user blocked · unblocked |
| `CometChatEvents.uiEvents` | `CometChatUIEvent` | panel visibility · active-chat changes |

Member shapes are **prefixed too** and the message ones repeat the domain: `CometChatMessageEvent.MessageSent(message, status)` (status `IN_PROGRESS`/`SUCCESS`/`ERROR`) · `MessageEdited` · `MessageDeleted` · `MessageRead` · `TextMessageReceived` · `TypingStarted` · `ReactionAdded`. There is no `.Sent` — it is `.MessageSent`. Import the sealed class from `com.cometchat.uikit.core.events`. Full list: fetch `/ui-kit/android/customization-events.md` (NOT `events.md`, which still teaches the old un-prefixed shape).

## Subscribing per cohort (lifecycle is the whole point)
**Kotlin XML Views** — collect in `lifecycleScope`; the coroutine is cancelled when the lifecycle owner is destroyed:
```kotlin
import androidx.lifecycle.lifecycleScope       // in an Activity/Fragment
import kotlinx.coroutines.launch
import com.cometchat.uikit.core.events.CometChatEvents
import com.cometchat.uikit.core.events.CometChatMessageEvent

lifecycleScope.launch {
    CometChatEvents.messageEvents.collect { event ->
        when (event) {
            is CometChatMessageEvent.MessageSent -> { /* event.message, event.status */ }
            is CometChatMessageEvent.MessageDeleted -> { /* event.message */ }
            else -> Unit
        }
    }
}
```
**Jetpack Compose** — collect in `LaunchedEffect`; cancelled when the composable leaves composition:
```kotlin
LaunchedEffect(Unit) {
    CometChatEvents.messageEvents.collect { event -> /* when (event) { … } */ }
}
```
> **No manual removal needed.** Unlike the old static-listener pattern, `SharedFlow` collection is scoped — do NOT invent an `addListener`/`removeListener` pair for `CometChatEvents`. Just don't collect outside a lifecycle-aware scope (a bare `GlobalScope.launch` IS a leak).

## UI-Kit events vs Chat SDK listeners (pick the right bus)
| | **UI-Kit events** (`CometChatEvents.*`) | **Chat SDK listeners** (`CometChat.add*Listener`) |
|---|---|---|
| Source | UI Kit components (what the UI just did) | the CometChat server (what arrived) |
| Direction | component → component | server → client |
| Registration | `.collect {}` in a lifecycle scope | `add*Listener(ID, …)` + **`remove*Listener(ID)` on teardown** |
| Use for | "the user sent/edited a message", "a call was accepted", panel/active-chat changes | incoming messages, presence, typing, connection status, incoming calls |
**Both are needed for a full app.** If you're reacting to something the server pushed while your UI didn't do it, that's an SDK listener (→ `core/references/docs-map.md` SDK section, or `cometchat-android-v5-sdk`) — and SDK listeners DO require explicit removal in `onDestroy`/`onDispose`/`onCleared`.

## Common pitfalls
Collecting on a non-lifecycle scope (leak) · inventing `CometChatEvents.addListener`/`removeListener` (doesn't exist — it's a flow) · using a UI-Kit event to detect *incoming* messages (use an SDK message listener) · registering an SDK listener and never removing it · a `when` without an `else` branch breaking on a new sealed member · re-collecting the same flow in several places and double-handling · guessing a sealed-class case name instead of fetching the events page.

## Verify it works
Compile against the pinned kit (`./gradlew :app:assembleDebug   # in YOUR app (npm run verify:fences:android-v6 is a pack-repo gate)`). On device: trigger the action (send/edit/delete a message, accept a call) and confirm your handler runs exactly once; rotate the screen / navigate away and back — no duplicate handling and no crash (proves the scope is right); for any SDK listener you added, confirm the matching remove runs on teardown.
