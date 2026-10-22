---
name: cometchat-android-v6-compose-components
description: "The closed catalog of CometChat Android v6 UI Kit components for the Jetpack Compose cohort — what exists, the composable import for each, the param shape (onX lambdas, hideX booleans, @Composable slots), and how to pass custom UI into a slot instead of stacking on top. Triggers: 'cometchat compose components', 'is there a X composable', 'cometchat jetpack compose list', 'custom row compose cometchat', 'swap the message bubble compose'."
license: "MIT"
compatibility: "Android minSdk >=28; compileSdk >=36; Kotlin >=2.1; AGP >=8.9.1; JVM target 11; com.cometchat:chatuikit-compose-android ^6 (Jetpack Compose cohort) — 6.0.x, verified 6.0.5; com.cometchat:chat-sdk-android ^5"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat android components v6 compose jetpack catalog"
---

> **Ground truth:** catalog `android-v6.json` (287 symbols, from the INSTALLED 6.0.5 source, cross-checked against the published AAR). Param shapes below were read from the Compose source. Fetch anything else from docs (`core` → `references/docs-map.md`); never trust memory.
>
> ⚠️ **This is the Jetpack Compose cohort.** Artifact `chatuikit-compose-android`, namespace `com.cometchat.uikit.compose.presentation.*`, components are **composables configured by named params**. The Views cohort (`chatuikit-kotlin-android`, `setX(...)` setters) is a **separate skill** — never install both.

## Companion skills (read first)
- `cometchat-android-v6-core` — install, credentials, `initFromSettings → login → render`, the fetch map. Assumed here, never repeated.
- `cometchat-android-v6-compose-placement` — where these go · `cometchat-android-v6-compose-customization` — theming and slots.

## Use this skill when
"which composables does the kit have?", "is there a `<X>` composable?", "what params does the conversations list take?", "can I replace a row / bubble region in Compose?".

## Prerequisites & install

> ⚠️ **Required on Compose too:** `configurations.all { exclude(group = "org.jetbrains", module = "annotations-java5") }` plus `android.useAndroidX=true` + `android.enableJetifier=true` in `gradle.properties`. The collision arrives via `chatuikit-core-android`, which BOTH cohorts pull, so a Compose-only app fails its FIRST build without them (~40 `Duplicate class` errors). Full block: `cometchat-android-v6-core` §Prerequisites & install.
`implementation("com.cometchat:chatuikit-compose-android:6.0.5")` + `buildFeatures { compose = true }` + the Kotlin Compose plugin. Same init/login gate as `core`.

## Component catalog (closed list)
The component NAMES are identical to the Views cohort — only the wiring differs. Import pattern: `com.cometchat.uikit.compose.presentation.<area>.ui.<Component>`. Not listed ⇒ not in the catalog ⇒ **does not exist**.

> ⚠️ **Three exceptions to that path** (verified vs 6.0.6): the calling trio DOES carry `.ui` in Compose — `…compose.presentation.callbuttons.ui.CometChatCallButtons` — which is the OPPOSITE of the Views cohort, so do not carry the Views exception across. And the `presentation.shared.*` family drops `.ui` entirely: `…presentation.shared.searchbox.CometChatSearchBox`, `…presentation.shared.baseelements.avatar.CometChatAvatar`, `…presentation.shared.toolbar.CometChatToolbar`. `CometChatScopeChange` ships in **Views only** — there is no Compose composable for it.

**Conversations & lists** — `CometChatConversations` · `CometChatUsers` · `CometChatGroups` · `CometChatGroupMembers` (+ row composables `CometChatConversationListItem`, `CometChatUsersListItem`, `CometChatGroupMemberListItem`, `CometChatGroupsItem`).
**Messaging** — `CometChatMessageHeader` · `CometChatMessageList` · `CometChatMessageComposer` · `CometChatMessageBubble` · `CometChatThreadHeader` · `CometChatThreadScreen` · `CometChatMessageInformation` · `CometChatMessageOption` · `CometChatMessageComposerAction` · `CometChatReactionList` · `CometChatMessageReaction` · `CometChatFlagMessageDialog` · `CometChatTypingIndicator` · `CometChatReceipt`/`CometChatReceipts`.
**Bubbles by type** — `CometChatTextBubble` · `CometChatImageBubble`/`CometChatImagesBubble` · `CometChatVideoBubble`/`CometChatVideosBubble` · `CometChatAudioBubble`/`CometChatAudiosBubble` · `CometChatVoiceNoteBubble` · `CometChatFileBubble`/`CometChatFilesBubble` · `CometChatPollBubble` · `CometChatStickerBubble` · `CometChatCardBubble` · `CometChatCollaborativeBubble` · `CometChatActionBubble` · `CometChatCallActionBubble` · `CometChatMeetCallBubble` · `CometChatDeleteBubble` · `CometChatAIAssistantBubble`.
**Calling** — `CometChatCallButtons` · `CometChatIncomingCall` · `CometChatOutgoingCall` · `CometChatOngoingCall` · `CometChatCallLogs` · `CometChatCallLogsListItem`.
**Search, AI & notifications** — `CometChatSearch` · `CometChatSearchBox` · `CometChatAIAssistantChatHistory` · `CometChatAIConversationStarterView` · `CometChatAISmartRepliesView` · `CometChatAIConversationSummaryView` · `CometChatNotificationFeed`.
**Composer add-ons & media** — `CometChatStickerKeyboard` · `CometChatEmojiKeyboard` · `CometChatCreatePoll` · `CometChatAttachmentTray`/`CometChatAttachmentTile` · `CometChatMediaRecorder`/`CometChatInlineMediaRecorder`/`CometChatInlineAudioRecorder` · `CometChatAudioVisualizer`/`CometChatInlineAudioWaveform` · `CometChatRichTextToolbar` · `CometChatSuggestionList` · `CometChatImagePreview` · `CometChatImageViewerScreen` · `CometChatVideoViewerScreen`.
**Building blocks** — `CometChatAvatar` · `CometChatBadgeCount` · `CometChatStatusIndicator` · `CometChatDate` · `CometChatToolbar` · `CometChatDialog`/`CometChatConfirmDialog` · `CometChatPopupMenu` · `CometChatSnackBar` · state views `CometChatLoadingState`/`CometChatEmptyState`/`CometChatErrorState` · shimmer `CometChatShimmerBox`/`CometChatShimmerContainer`.
**Non-visual** — `CometChatUIKit` · theming `CometChatTheme`/`CometChatColorScheme`/`CometChatTypography` · `CometChatLocalize` · `CometChatSoundManager` · events `CometChatEvents` + the `*Event` family · formatters `CometChatTextFormatter`/`CometChatMentionsFormatter`/`CometChatRichTextFormatter`.

> ⚠️ Emitting ANY calling component requires the calls artifact **and**
> `"uiKit": { "enableCalling": true }` in `assets/cometchat-settings.json` — otherwise it crashes on
> device while **compiling fine** (the compile gate cannot catch it). Full artifact/flag/result
> matrix: docs `call-logs` page. → `cometchat-android-v6-calls`.



## Param shape — how a Compose component is configured
Three conventions, consistent across the cohort (verified vs 6.0.5):
- **`onX` lambdas** for events — `onItemClick: ((Conversation) -> Unit)?`, `onSearchClick: (() -> Unit)?`, `onBackPress: (() -> Unit)?`, `onItemLongClick`, `onError: ((CometChatException) -> Unit)?`, `onLoad`, `onEmpty`, `onSelection`.
- **`hideX` booleans** for affordances — `hideSearchBox`, `hideToolbar`, `hideBackIcon`, `hideUserStatus`, `hideReceipts`, `hideDeleteOption`, `hideLoadingState`, `hideEmptyState`, `hideErrorState`. (Views uses visibility setters; Compose hides.)
- **`@Composable` slots** for custom UI — e.g. `itemView`, `leadingView`, `subtitleView`, `trailingView`, each `(@Composable (Conversation, TypingIndicator?) -> Unit)?`.
Plus `modifier: Modifier`, `style: CometChat<X>Style = …default()`, and request-builder params (`conversationsRequestBuilder`).

```kotlin
import com.cometchat.uikit.compose.presentation.conversations.ui.CometChatConversations

CometChatConversations(
    modifier = Modifier.fillMaxSize(),
    title = "Chats",
    onItemClick = { conversation -> /* navigate */ },
    onSearchClick = { /* open search route */ },
)
```
**Size it to fill.** The kit fills the box you give it — a `wrap_content`-equivalent (unbounded height, or a `Column` without `weight`) renders a sliver (`core/references/layout.md`).

## Key param differences from the Views cohort
| Concern | Views | Compose |
|---|---|---|
| thread scope | `setParentMessageId(Long)` | **`parentMessageId: Long = -1`** param on list AND composer |
| thread header | `setParentMessage(BaseMessage)` | **`parentMessage: BaseMessage`** (required param) |
| search scope | `setSearchIn(List<SearchScope>)` | **`searchScopes: List<SearchScope>`** |
| search target | `setUid` / `setGuid` | `uid: String?` / `guid: String?` |
| affordances | visibility setters | `hideX: Boolean` |
| slots | ViewHolder listeners | `@Composable` lambdas |
Everything else (`user`, `group`, `onThreadRepliesClick: ((BaseMessage) -> Unit)?`) matches by name.

## Custom UI goes IN a slot, not on top
Pass a `@Composable` to the component's slot param (`itemView`, `leadingView`, `subtitleView`, `trailingView`), use `options`/`addOptions` for the long-press menu, and `setBubbleFactories`-equivalent factories for custom message TYPES. Never stack your own composable over a kit component, and never re-implement a list the kit ships. Detail: `cometchat-android-v6-compose-customization`.

> ⚠️ **A slot with a DEFAULT implementation REPLACES it — `CometChatMessageHeader` `auxiliaryView` vs
> `trailingView`** (verified vs installed 6.0.5 source + on device). The header's `auxiliaryView`
> substitutes the built-in `DefaultAuxiliaryView`, which is what HOSTS the voice/video call buttons —
> so putting a custom icon there silently removes them. Extra header icons belong in **`trailingView`**,
> a separate slot that keeps the auxiliary area (and its call buttons) intact. Use `auxiliaryView` only
> when you intend to REPLACE the call-button area (and re-render `CometChatCallButtons` yourself if you
> still want calling).

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

## Components that do NOT exist in v6
No combined shell — `CometChatConversationsWithMessages`, `CometChatUsersWithMessages`, `CometChatGroupsWithMessages`, `CometChatUI` are v4-era. ⚠️ **`CometChatMessageTemplate` is absent from the shipped 6.0.5 artifact** (logged internally) — use bubble factories.

## Common pitfalls
Mixing cohorts (Views artifact in a Compose app) · using a `setX(...)` setter on a composable · unbounded height (sliver) · `showSearchBar`-style thinking (Compose uses `hideSearchBox`) · overlaying instead of slotting · a custom header icon in `CometChatMessageHeader` `auxiliaryView` (replaces the call-button host — use `trailingView`) · emitting `CometChatMessageTemplate` · guessing a param instead of fetching the page's Compose tab.

## Verify it works
Every composable you emitted is in the list above (Tier-1) and it compiles — `./gradlew :app:assembleDebug   # in YOUR app (native-fence.mjs is a pack-repo gate, not installed by the CLI)`. On device: full-size render with the kit's own loading/empty state, slotted composables INSIDE the component.
