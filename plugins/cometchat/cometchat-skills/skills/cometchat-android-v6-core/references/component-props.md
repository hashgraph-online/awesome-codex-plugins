# component-props — BAKED stable signatures for the Android v6 drop-ins

> Ground truth: `ui-kit/android/conversations.md`, `message-header.md`, `message-list.md`, `message-composer.md` (+ `threaded-messages-header.md`, `search.md`, `conversation-message-view.md` for wiring), extracted from the pages' code fences per cohort and cross-checked against installed 6.0.5 kit source, verified 2026-08-20.

The high-value, STABLE hooks for the 4 core drop-ins — baked so the golden path needs no
fetch. Both cohorts use the SAME component names; **Compose = named params on the
composable, Views = `set*` setters on the view** (XML tag = the fully-qualified class name,
package `com.cometchat.uikit.kotlin.presentation.<component>.ui.<Name>`). Exhaustive/rare
params still come from the page's `.md` twin (`docs-map.md`); anything below marked
**FETCH** is not baked.

## THE RULE — custom UI goes in the component's OWN slot, never stacked on top
A custom header row, banner, or action button belongs in the component's view slot (tables
below). Don't render it as a sibling above/beside the component.

---

## CometChatConversations
**XML tag:** `<com.cometchat.uikit.kotlin.presentation.conversations.ui.CometChatConversations />` (size it `match_parent`).
**Callbacks** (Views setter ⇄ Compose param — same lambda shape):
- `setOnItemClick { conversation -> }` ⇄ `onItemClick = { conversation -> }` — the primary navigation hook (replaces built-in behavior).
- `setOnSearchClick { }` ⇄ `onSearchClick = { }` — the toolbar search icon; wire to a `CometChatSearch` screen or hide the search affordance.
- `setOnBackPress { }` ⇄ `onBackPress = { }` — toolbar back button.
- `setOnItemLongClick { conversation -> }` ⇄ `onItemLongClick` · `setOnError { exception -> }` ⇄ `onError` · `setOnLoad { conversations -> }` ⇄ `onLoad` · `setOnEmpty { }` ⇄ `onEmpty` · `setOnSelection { selected -> }` ⇄ `onSelection` (with `setSelectionMode(UIKitConstants.SelectionMode.MULTIPLE)` ⇄ `selectionMode =`).
**Functionality:** `setTitle("Chats")` ⇄ `title =` · `setToolbarVisibility(View.GONE)` ⇄ `hideToolbar = true` · `setSearchBoxVisibility(View.GONE)` ⇄ `hideSearchBox = true` · `setBackIconVisibility(View.VISIBLE)` ⇄ `hideBackIcon = false` (back icon hidden by default in Compose) · `setDisableSoundForMessages(true)` ⇄ `disableSoundForMessages = true`.

**The request-builder scoping hook** (exact names from `conversations.md`):
- Views: `conversations.setConversationsRequestBuilder(builder)`
- Compose: `conversationsRequestBuilder = builder`
```kotlin
ConversationsRequest.ConversationsRequestBuilder()
    .setConversationType(CometChatConstants.CONVERSATION_TYPE_USER)   // 1:1-only; _GROUP for groups-only
    .setLimit(20)
```
**Pass the builder object, not `.build()`** — the component calls `.build()` internally
(docs Warning; default page size 30, infinite scroll). A DM-only ask → `CONVERSATION_TYPE_USER`
(hides seeded groups); groups-only → `CONVERSATION_TYPE_GROUP`; an unscoped "add chat" → omit the builder.

**The selection flows into the message screen via `conversationWith`:**
```kotlin
onItemClick = { conversation ->
    when (val entity = conversation.conversationWith) {   // User OR Group
        is User -> navigateToUserChat(entity)
        is Group -> navigateToGroupChat(entity)
    }
}
```
The SAME `User`/`Group` is then handed to header + list + composer (below). Views cohort
passes it through Intent extras (`intent.putExtra("user", entity)` — the guide's pattern);
Compose holds it in state / a nav route.

## CometChatMessageHeader
**XML tag:** `<com.cometchat.uikit.kotlin.presentation.messageheader.ui.CometChatMessageHeader />` (height `wrap_content`/`56dp`).
**Target (required):** `setUser(user)` ⇄ `user =` OR `setGroup(group)` ⇄ `group =`.
**Callbacks:** `setOnBackPress { }` ⇄ `onBackPress = { }` (REQUIRED on phones — pop back to the list) · `setOnError { exception -> }` ⇄ `onError`.
**Functionality:** `setBackButtonVisibility(View.VISIBLE)` ⇄ `hideBackButton = false`. Presence/typing/member-count update automatically (SDK events handled internally).

## CometChatMessageList
**XML tag:** `<com.cometchat.uikit.kotlin.presentation.messagelist.ui.CometChatMessageList />` (`0dp` + `layout_weight="1"` between header and composer — `layout.md`).
**Target (required):** `setUser(user)` ⇄ `user =` OR `setGroup(group)` ⇄ `group =` — without one the list shows only its loading indicator (docs Warning).
**Callbacks:**
- `setOnThreadRepliesClick { message -> }` ⇄ `onThreadRepliesClick = { message -> }` — receives the parent `BaseMessage`; navigate to the thread screen (default-on; hide only on explicit opt-out via `setReplyInThreadOptionVisibility(View.GONE)` / Compose hide-option param — FETCH the Compose name from `message-list.md` if needed).
  ⚠️ **Signature note:** the installed 6.0.5 kit takes a single `BaseMessage` in BOTH cohorts (`fun setOnThreadRepliesClick(callback: ((BaseMessage) -> Unit)?)`); the docs page's `{ context, baseMessage, template -> }` fence is stale — bake the single-arg shape.
- `setOnError { exception -> }` ⇄ `onError` · `setOnLoad { messages -> }` ⇄ `onLoad` · `setOnEmpty { }` ⇄ `onEmpty`.
**Functionality:** `setMessagesRequestBuilder(MessagesRequest.MessagesRequestBuilder()...)` ⇄ `messagesRequestBuilder =` (same pass-the-builder-not-`.build()` rule) · `setStartFromUnreadMessages(true)` ⇄ `startFromUnreadMessages = true` · `setEnableMultipleAttachments(true)` ⇄ `enableMultipleAttachments = true` (default true).
**Thread mode:** `setParentMessageId(id)` (Views, `Long`) ⇄ `parentMessageId = message.id` (Compose, default `-1` = main conversation) — a parent-scoped list for the thread screen. ⚠️ The `guide-threaded-messages.md` Views fence calls `messageList.setParentMessage(it.id)` — that setter doesn't exist on the list; the real one is `setParentMessageId` (verified in kit source + master app).

## CometChatMessageComposer
**XML tag:** `<com.cometchat.uikit.kotlin.presentation.messagecomposer.ui.CometChatMessageComposer />` (height `wrap_content`; create it in the Activity's `onCreate` — it registers an `ActivityResultLauncher` for permissions, docs Warning).
**Target (required):** `setUser(user)` ⇄ `user =` OR `setGroup(group)` ⇄ `group =`.
**Works with no extra wiring** for plain send/attachments/voice/emoji.
**Callbacks (intercept-only):**
- Compose: `onSendButtonClick = { context, baseMessage -> }` (docs + source agree) · `onError = { ... }` — ⚠️ the Compose source takes `(CometChatException) -> Unit` (one arg); the docs fence shows `{ context, exception -> }` — prefer the one-arg shape, verify on compile.
- Views: ⚠️ installed 6.0.5 source is `setOnSendButtonClick(callback: (String) -> Unit)` (the typed text), NOT the docs' `{ context, baseMessage -> }` — treat the Views intercept as **FETCH/verify-on-compile**; for the golden path you don't wire it at all.
**Thread mode:** `setParentMessageId(id)` ⇄ `parentMessageId = message.id` — replies land in the thread.

## The thread screen (how the pieces compose — from `guide-threaded-messages.md` + `threaded-messages-header.md`)
Takes BOTH the conversation target AND the parent message: `CometChatThreadHeader` —
`setParentMessage(parentMessage)` ⇄ `parentMessage =` (a `BaseMessage`; display-only, no
callbacks) — above a parent-scoped `CometChatMessageList` + `CometChatMessageComposer`
(same `user`/`group` + `parentMessageId = parentMessage.id` on both).

## CometChatSearch (the `onSearchClick` destination)
Views `setOnBackPressListener { }` ⇄ Compose `onBackPress = { }` — you opened it, you close
it (round-trip). Scope to one conversation with `setUid("...")`/`setGuid("...")` ⇄
`uid =`/`guid =`; global search = neither. Full params: FETCH `search.md`.

---

## Slot / custom-view map (where custom UI goes)
| Component | Views setter | Compose param | Region |
|---|---|---|---|
| Conversations | `setLeadingView(ConversationsViewHolderListener)` / `setTitleView(...)` / `setSubtitleView(...)` / `setTrailingView(...)` | `leadingView = { conversation, typingIndicator -> }` / `titleView` / `subtitleView` / `trailingView` | per-row sections |
| Conversations | `setLoadingView(v)` / `setEmptyView(v)` / `setErrorView(v)` | `loadingView = { }` / `emptyView = { }` / `errorView = { onRetry -> }` | list states |
| Conversations | `setOverflowMenu(view)` · `setOptions { ctx, conv -> }` / `setAddOptions { ctx, conv -> }` | `overflowMenu = { }` · `options = { ctx, conv -> }` / `addOptions` | toolbar menu · long-press menu (`CometChatPopupMenu.MenuItem`) |
| MessageHeader | `setLeadingView(MessageHeaderViewHolderListener)` / `setSubtitleView(...)` / `setTrailingView(...)` / `setItemView(...)` | `leadingView = { user, group -> }` / `subtitleView` / `trailingView` / `itemView` (replaces whole header) | avatar · status line · right-side actions · whole row |
| MessageList | `setHeaderView(view)` / `setFooterView(view)` · state views as above | `headerView = { }` / `footerView = { }` · state views | banner above / below the scroll |
| MessageList | `set*ViewProvider(BubbleViewProvider)` (leading/header/reply/content/bottom/statusInfo/thread/footer) · `setBubbleFactories(list)` | per-bubble slot params `leadingView/headerView/.../footerView = { message, alignment -> }` · `bubbleFactories =` | inside every bubble / per message type — depth: FETCH `message-list.md` |
| MessageComposer | `setHeaderView(view)` / `setSendButtonView(view)` / `setAuxiliaryButtonView(view)` / `setAttachmentOptions(list)` | `headerView = { }` / `sendButtonView = { }` / `auxiliaryButtonView = { }` / `attachmentOptions = listOf(CometChatMessageComposerAction(...))` | above input · send button · sticker/AI area · attach sheet |

> Overriding `setAuxiliaryButtonView` REPLACES the sticker/AI buttons entirely — in 6.0.5 there is
> **no accessor to re-fetch the defaults**: `CometChatUIKit.getDataSource()` and
> `getAuxiliaryOption(...)` do **not** exist (the v4-era `ChatConfigurator.getDataSource()` /
> `getAuxiliaryOptions()` slot architecture was removed — verified against chatuikit-core/kotlin 6.0.5).
> If you must keep the defaults, add them into your custom view yourself; otherwise don't override the
> whole auxiliary slot. (Styling and ViewModel injection: FETCH the page.)

---

## Import paths (verified against 6.0.5)

Views components live at `com.cometchat.uikit.kotlin.presentation.<area>.ui.<Component>` —
`conversations.ui.CometChatConversations`, `messagelist.ui.CometChatMessageList`,
`search.ui.CometChatSearch`, `threadheader.ui.CometChatThreadHeader`, `users.ui.CometChatUsers`,
`groups.ui.CometChatGroups`, `calllogs.ui.CometChatCallLogs`,
`notificationfeed.ui.CometChatNotificationFeed`.

**The three calling components have NO `.ui` segment** (verified against 6.0.5) — inferring the
pattern gives `Unresolved reference 'ui'`:

| Component | Import |
|---|---|
| `CometChatIncomingCall` | `…presentation.incomingcall.CometChatIncomingCall` |
| `CometChatOutgoingCall` | `…presentation.outgoingcall.CometChatOutgoingCall` |
| `CometChatCallButtons` | `…presentation.callbuttons.CometChatCallButtons` |

SDK types the golden path also emits (not UI-Kit components, and not under `presentation`):

| Type | Import |
|---|---|
| `AppEntity` (the `User`/`Group` supertype the search + conversation taps switch on) | `com.cometchat.chat.models.AppEntity` |
| `CometChatConstants` (`RECEIVER_TYPE_*`, `GROUP_TYPE_*`, `CATEGORY_*`) | `com.cometchat.chat.constants.CometChatConstants` |

Formatters are not under `presentation` at all: `com.cometchat.uikit.kotlin.shared.formatters.*`
(`CometChatTextFormatter`, `CometChatMentionsFormatter`, `CometChatRichTextFormatter`). `SearchScope`
is `com.cometchat.uikit.core.constants.SearchScope`. Compose swaps `kotlin` for `compose`.

---

## Callback shapes (Views, verified vs 6.0.5)

| Component | Views setter | Shape |
|---|---|---|
| `CometChatConversations` | `setOnItemClick` | `(Conversation) -> Unit` |
| `CometChatConversations` | `setOnSearchClick` | `() -> Unit` |
| `CometChatMessageHeader` | `setOnBackPress` | `() -> Unit` |
| `CometChatMessageList` | `setOnThreadRepliesClick` | `((BaseMessage) -> Unit)?` — **ONE arg** |
| `CometChatMessageList` / `Composer` | `setParentMessageId` | `(Long)` |
| `CometChatThreadHeader` | `setParentMessage` | `(BaseMessage)` |
| `CometChatSearch` | `setOnConversationClick` | `((Conversation) -> Unit)?` — **ONE arg** |
| `CometChatSearch` | `setOnMessageClick` | `((BaseMessage) -> Unit)?` — **ONE arg** |
| `CometChatSearch` | `setSearchIn` | `(List<SearchScope>)` — import `com.cometchat.uikit.core.constants.SearchScope` |
| `CometChatMessageHeader` | `setOnNewChatClick` | `(() -> Unit)` — **on the HEADER, not `CometChatConversations`**; a list-first app owns its own new-chat entry (tab/FAB) → `CometChatUsers` + `CometChatGroups` |
| all four | `setUser` / `setGroup` | `(User)` / `(Group)` |

---

## Component / API map (BAKED closed list — from `catalogs/android-v6.json`)
Session: `CometChatUIKit`, `UIKitSettings` (`com.cometchat.uikit.core`).
Core surface: `CometChatConversations` · `CometChatMessageHeader` · `CometChatMessageList` · `CometChatMessageComposer` · `CometChatThreadHeader` · `CometChatSearch`.
Grow set (on request): `CometChatUsers` · `CometChatGroups` · `CometChatGroupMembers` · `CometChatCallLogs` · `CometChatIncomingCall` · `CometChatNotificationFeed` · `CometChatAIAssistantChatHistory`.
Namespaces: Views `com.cometchat.uikit.kotlin.presentation.<area>.ui.*` · Compose `com.cometchat.uikit.compose.presentation.<area>.ui.*`.
**Not in the catalog ⇒ does not exist.** v6 ships **no combined shell** — `CometChatConversationsWithMessages`/`CometChatUI` are v4-era names. `CometChatMessageTemplate` is documented but **absent from 6.0.5** — verify before use. Full catalog: `cometchat-android-v6-{kotlin,compose}-components`.

> ⚠️ **Docs drift — trust the reference table, not the docs.** `guide-threaded-messages` (Views tab) shows a **3-arg**
> `setOnThreadRepliesClick { context, baseMessage, template -> }` and `messageList.setParentMessage(id)`.
> Neither exists in 6.0.5: the callback takes **one** `BaseMessage`, and the list setter is
> **`setParentMessageId(Long)`**. Logged internally.
