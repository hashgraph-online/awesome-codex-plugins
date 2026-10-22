---
name: cometchat-android-v6-kotlin-components
description: "The closed catalog of CometChat Android v6 UI Kit components for the Kotlin XML Views cohort — what exists, the XML tag and import for each, what each one is for, and how to swap custom UI into a component's slot instead of stacking on top. Triggers: 'which cometchat components are there android', 'is there a X component android', 'cometchat xml view tag', 'swap the message bubble android', 'custom row in conversations list'."
license: "MIT"
compatibility: "Android minSdk >=28; compileSdk >=36; Kotlin >=2.1; AGP >=8.9.1; JVM target 11; com.cometchat:chatuikit-kotlin-android ^6 (XML Views cohort) — 6.0.x, verified 6.0.5; com.cometchat:chat-sdk-android ^5"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android components v6 kotlin views xml catalog"
---

> **Ground truth:** catalog `android-v6.json` (287 symbols, generated from the INSTALLED 6.0.5 source and cross-checked against the published AAR) + the live component pages. Verify every symbol against the catalog; fetch attributes from docs (`core` → `references/docs-map.md`); never trust memory.
>
> ⚠️ **This is the Kotlin XML Views cohort.** The artifact is `chatuikit-kotlin-android`, the namespace is `com.cometchat.uikit.kotlin.presentation.*`, and components are XML tags configured with `setX(...)`. The Compose cohort (`chatuikit-compose-android`, composable params) is a **separate skill** — never mix them in one app.

## Companion skills (read first)
- `cometchat-android-v6-core` — install, credentials, `initFromSettings → login → render`, the hot-path callbacks, and the fetch map. Assumed here, never repeated.
- `cometchat-android-v6-kotlin-placement` — where these components go · `cometchat-android-v6-kotlin-customization` — how to restyle/slot them.

## Use this skill when
"which components does the Android UI Kit have?", "is there a `<X>` component?", "what's the XML tag for the message list?", "I need a component for `<intent>`", "can I replace a list row / message bubble?".

## Prerequisites & install
Same kit + init as `core`. One cohort per app: `implementation("com.cometchat:chatuikit-kotlin-android:6.0.5")`. Every component below is a `View` — put it in a layout, then configure it in `onCreate` (`findViewById` or view binding).

## Component catalog (closed list — from `catalogs/android-v6.json`)
Import/tag pattern: `com.cometchat.uikit.kotlin.presentation.<area>.ui.<Component>`. Not listed here ⇒ not in the catalog ⇒ **does not exist**.

**Conversations & lists** — `CometChatConversations` (the usual entry point) · `CometChatUsers` · `CometChatGroups` · `CometChatGroupMembers` (members + admin actions) · row items for custom rendering: `CometChatConversationListItem`, `CometChatUsersListItem`, `CometChatGroupMemberListItem`, `CometChatGroupsItem`.

**Messaging** — `CometChatMessageHeader` · `CometChatMessageList` · `CometChatMessageComposer` · `CometChatMessageBubble` · `CometChatThreadHeader` · `CometChatThreadScreen` · `CometChatMessageInformation` + `CometChatMessageInformationBottomSheet` · `CometChatMessagePopupMenu` · `CometChatMessagePreview` · `CometChatMessageInput` · `CometChatMessageReaction` · `CometChatReactionList` · `CometChatFlagMessageDialog` · `CometChatTypingIndicator` · `CometChatReceipt` / `CometChatReceipts` · models `CometChatMessageOption`, `CometChatMessageComposerAction`.

**Message bubbles by type** — `CometChatTextBubble` · `CometChatImageBubble`/`CometChatImagesBubble` · `CometChatVideoBubble`/`CometChatVideosBubble` · `CometChatAudioBubble`/`CometChatAudiosBubble` · `CometChatVoiceNoteBubble` · `CometChatFileBubble`/`CometChatFilesBubble` · `CometChatPollBubble` · `CometChatStickerBubble` · `CometChatCardBubble` · `CometChatCollaborativeBubble` · `CometChatActionBubble` · `CometChatCallActionBubble` · `CometChatMeetCallBubble` · `CometChatDeleteBubble` · `CometChatAIAssistantBubble`.

**Calling** (needs the calls artifact — `cometchat-android-v6-calls`) — `CometChatCallButtons` · `CometChatIncomingCall` · `CometChatOutgoingCall` · `CometChatOngoingCall` (+ `CometChatOngoingCallActivity`, `CometChatCallActivity`) · `CometChatCallLogs` · `CometChatCallLogsListItem`.

> ⚠️ Emitting ANY calling component requires the calls artifact **and**
> `"uiKit": { "enableCalling": true }` in `assets/cometchat-settings.json` — otherwise it crashes on
> device while **compiling fine** (the compile gate cannot catch it). Full artifact/flag/result
> matrix: docs `call-logs` page. → `cometchat-android-v6-calls`.



**Search, AI & notifications** — `CometChatSearch` · `CometChatSearchBox` · `CometChatAIAssistantChatHistory` · `CometChatAIConversationStarterView` · `CometChatAISmartRepliesView` · `CometChatAIConversationSummaryView` · `CometChatNotificationFeed`.

**Composer add-ons & media** — `CometChatStickerKeyboard` · `CometChatEmojiKeyboard` · `CometChatCreatePoll` · `CometChatAttachmentTray`/`CometChatAttachmentTile` · `CometChatMediaRecorder`/`CometChatInlineMediaRecorder`/`CometChatInlineAudioRecorder` · `CometChatAudioVisualizer`/`CometChatInlineAudioWaveform` · `CometChatRichTextToolbar` · `CometChatSuggestionList` · `CometChatImagePreview` · `CometChatImageViewerScreen`/`CometChatImageViewerActivity` · `CometChatVideoViewerScreen`/`CometChatVideoViewerActivity`.

**Building blocks** — `CometChatAvatar` · `CometChatBadgeCount` · `CometChatStatusIndicator` · `CometChatDate` · `CometChatToolbar` · `CometChatDialog`/`CometChatConfirmDialog`/`CometChatLinkEditDialog`/`CometChatLinkPopupDialog` · `CometChatPopupMenu` · `CometChatSnackBar` · `CometChatEditText`/`CometChatTextWatcher` · `CometChatScopeChange` · state views `CometChatLoadingState`/`CometChatEmptyState`/`CometChatErrorState`/`CometChatErrorAlert` · shimmer `CometChatShimmerBox`/`CometChatShimmerContainer`/`CometChatShimmerFrameLayout`/`CometChatShimmerDrawable`/`CometChatShimmerConfig`.

**Non-visual (used from code)** — `CometChatUIKit` (session) · theming `CometChatTheme`/`CometChatColorScheme`/`CometChatTypography`/`CometChatTextAppearance*` · `CometChatLocalize` · `CometChatSoundManager` · events `CometChatEvents` + `CometChatUIEvent`/`CometChatMessageEvent`/`CometChatGroupEvent`/`CometChatUserEvent`/`CometChatConversationEvent`/`CometChatCallEvent` · formatters `CometChatTextFormatter`/`CometChatMentionsFormatter`/`CometChatRichTextFormatter` · `CometChatPermissionHandler`/`CometChatPermissionActivity` · `CometChatAIStreamService`.

## Using one — XML tag + configure
```xml
<com.cometchat.uikit.kotlin.presentation.conversations.ui.CometChatConversations
    android:id="@+id/conversations"
    android:layout_width="match_parent"
    android:layout_height="match_parent" />
```
```kotlin
val conversations = findViewById<CometChatConversations>(R.id.conversations)
conversations.setTitle("Chats")
conversations.setOnItemClick { conversation -> /* navigate */ }
```
**Size it to fill.** `wrap_content` on a list or the chat surface renders a sliver — the kit fills the box you give it (`core/references/layout.md`).

## Custom UI goes IN a slot, not on top
Every list component exposes **ViewHolder-listener slots** rather than requiring a fork:
- `CometChatConversations`: `setItemView` · `setLeadingView` · `setTitleView` · `setSubtitleView` · `setTrailingView` (each takes a `ConversationsViewHolderListener`), plus `setEmptyView`/`setErrorView`/`setLoadingView` (plain `View`) and `setOptions`/`setAddOptions` for the long-press menu.
- `CometChatMessageList`: per-region providers — `setLeadingViewProvider` · `setHeaderViewProvider` · `setContentViewProvider` · `setReplyViewProvider` · `setBottomViewProvider` · `setStatusInfoViewProvider` · `setThreadViewProvider` · `setFooterViewProvider` (each a `BubbleViewProvider`).
- **Custom message TYPES** use `setBubbleFactories(listOf(...))` with a `BubbleFactory` subclass — *not* a message template (see below).

Rule: put custom UI in the slot; never overlay your own view on a kit component, and never re-implement a list the kit already ships. Mechanism detail: `cometchat-android-v6-kotlin-customization`.

> ⚠️ **A slot with default CONTENT replaces it — `CometChatMessageHeader` `setAuxiliaryViewListener` vs
> `setTrailingView`** (verified vs installed 6.0.5 source: `Utils.handleView` calls `removeAllViews()`
> on `messageHeaderAuxiliaryView`, whose default child in `cometchat_message_header.xml` is
> `CometChatCallButtons`; `messageHeaderTailView` is a default-empty `FrameLayout`). Setting an
> auxiliary view removes the voice/video call buttons — that is the intended way to take over that
> area. Extra header icons belong in `setTrailingView`, which keeps the call buttons intact. Same
> contract as the Compose cohort's `auxiliaryView`/`trailingView` params.

## Group member permissions — the kit enforces them, don't re-implement
`CometChatGroupMembers` gates its own long-press menu (verified vs 6.0.5). Rely on it:

| Logged-in user | Menu opens on | Cannot act on |
|---|---|---|
| **Owner** (`uid == group.owner`) | anyone but themselves | — |
| **Admin** (`group.scope`) | participants, moderators | other admins, owner |
| **Moderator** | participants only | moderators, admins, owner |
| **Participant** | nobody | everyone |

A moderator also cannot assign the **admin** role (disabled in the scope sheet). Scope strings:
`CometChatConstants.SCOPE_ADMIN` / `SCOPE_MODERATOR` / `SCOPE_PARTICIPANT`. Never hand-roll these
checks or hide the component behind your own role logic — you will drift from the kit.

⚠️ **Reversed parameter order between the two ownership APIs:**
`CometChat.updateGroupMemberScope(UID, GUID, scope, listener)` but
`CometChat.transferGroupOwnership(GUID, UID, listener)`.

## Components that do NOT exist in v6 (never emit these)
v6 ships **no combined shell**: `CometChatConversationsWithMessages`, `CometChatUsersWithMessages`, `CometChatGroupsWithMessages`, `CometChatUI` are v4-era names — you compose the screens yourself (`…-kotlin-placement`). `CometChatContacts` is not a v6 symbol.

⚠️ **`CometChatMessageTemplate` is absent from the shipped 6.0.5 artifact** (verified against the published AAR; logged internally). The old v5 API — `setTemplates`, `setType`, `setCategory`, `setBubbleView`, `setMessageReceipt` — all fail to compile. The docs `message-template` page was corrected upstream (verified 2026-09-09): it is now "Message Bubble Factory" and teaches `BubbleFactory` + `setBubbleFactories`. **Use `BubbleFactory` + `setBubbleFactories`.** The compile gate rejects the old form.

## Common pitfalls
Mixing cohorts (Compose artifact in a Views app) · assuming a v4/v5 combined shell exists · emitting `CometChatMessageTemplate` from the docs page · `wrap_content` on a list · overlaying custom UI instead of using a slot · a custom header icon via `setAuxiliaryViewListener` (replaces the call-button host — use `setTrailingView`) · using the Compose namespace (`…uikit.compose.…`) in an XML tag · guessing attributes instead of fetching the component's `.md` twin.

## Verify it works
Every component you emitted is in the list above (Tier-1 catalog) and the app compiles against the pinned kit — `./gradlew :app:assembleDebug   # in YOUR app (native-fence.mjs is a pack-repo gate, not installed by the CLI)`. On device: the component renders at full size with its own loading/empty state, and any slotted custom view appears INSIDE the component. Unsure about an attribute → fetch the page's `.md` twin; never read kit source for signatures.
