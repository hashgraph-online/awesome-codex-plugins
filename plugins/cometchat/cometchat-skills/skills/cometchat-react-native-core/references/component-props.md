# component-props — BAKED stable props + view slots for the React Native v5 drop-ins

Verified against `@cometchat/chat-uikit-react-native@5.4.0` **source**, not prose. Exhaustive prop
lists still come from the docs (`docs-map.md`); this file bakes the ones you need on the hot path
and the ones that are traps.

## THE RULE — custom UI goes in the component's OWN view slot, NEVER as a sibling on top
A custom header, search icon or action button rendered *above* a list double-renders the header and
breaks scrolling. Put it in the component's slot so the component keeps its own layout, scroll and
empty/error states.

⚠️ **RN slot props are PascalCase** (`ItemView`, `TrailingView`). React's camelCase form is
**silently ignored** — no error, nothing renders.

---

## ⚠️ Defaults that differ from React — verified from source

| Prop | React | **React Native** | Consequence |
|---|---|---|---|
| `showSearchBar` | `true` | **`false`** | **The search bar is HIDDEN by default.** `onSearchBarClicked` can never fire unless you also pass `showSearchBar={true}`. Wiring the callback alone silently ships a surface with no search. |
| `showSmartReplies` | `false` | `false` | same |
| `showConversationStarters` | `false` | `false` | same |
| `showConversationSummaryButton` | `false` | `false` | same |
| `showMarkAsUnreadOption` | `false` | `false` | same |

Every `show*` prop is opt-**in**; every `hide*` prop is opt-**out**. When a feature "does nothing
after enabling it in the dashboard", the missing `show*` prop is the usual cause.

---

## CometChatConversations
**Props:** `onItemPress(conversation)` · `onItemLongPress` · `onSearchBarClicked` · `onSelection` ·
`onError` · `onEmpty` · `onLoad` · `showSearchBar` (**default `false`**) · `hideHeader` ·
`hideBackButton` · `hideError` · `disableSoundForMessages` · `conversationsRequestBuilder`.

**View slots (PascalCase):** `ItemView` · `TitleView` · `SubtitleView` · `LeadingView` ·
`TrailingView` · `SearchView` · `EmptyView` · `ErrorView` · `LoadingView`.

> **Search in the list → `showSearchBar={true}` + `onSearchBarClicked` → push a search screen.**
> Both, or search is invisible.

> **Scope the list with `conversationsRequestBuilder`.** 1:1-only app →
> `.setConversationType("user")`; groups-only → `.setConversationType("group")`.
> ⚠️ **Pass the builder INSTANCE, not `.build()`** — the kit calls `.build()` internally
> (`CometChatConversations.tsx:1670`), and the RN docs say so explicitly. Passing the built object
> breaks the list.
> ```tsx
> import { CometChat } from "@cometchat/chat-sdk-react-native";
> <CometChatConversations
>   conversationsRequestBuilder={new CometChat.ConversationsRequestBuilder().setLimit(30)}
> />
> ```

## CometChatUsers / CometChatGroups
**Props:** `onItemPress` · `onError` · `onEmpty` · `onLoad` · `usersRequestBuilder` /
`groupsRequestBuilder` (same instance-not-`.build()` rule).
**Slots:** `ItemView` · `TitleView` · `SubtitleView` · `LeadingView` · `TrailingView` ·
`EmptyView` · `ErrorView` · `LoadingView`.

## CometChatMessageHeader
**Props:** `user` · `group` · `onBack` · `onError` · `showBackButton` · `hideVoiceCallButton` ·
`hideVideoCallButton` · `hideNewChatButton` · `hideChatHistoryButton` ·
`showConversationSummaryButton` (**default `false`**) · `onConversationSummaryPress`.
**Slots:** `ItemView` · `TitleView` · `SubtitleView` · `LeadingView` · `TrailingView` ·
`AuxiliaryButtonView`.

> Call buttons render here **by default** — do not also mount `CometChatCallButtons` in the header
> or they double up.

## CometChatMessageList
**Props:** `user` · `group` · `onThreadRepliesPress` · `onError` · `onEmpty` · `onLoad` ·
`messageRequestBuilder` · `reactionsRequestBuilder` · `showSmartReplies` (**default `false`**) ·
`showConversationStarters` (**default `false`**) · `showMarkAsUnreadOption` (**default `false`**) ·
plus `hide*` toggles for every message option (`hideReplyInThreadOption`, `hideReactionOption`,
`hideCopyMessageOption`, `hideDeleteMessageOption`, `hideEditMessageOption`,
`hideMessagePrivatelyOption`, `hideTranslateMessageOption`, `hideFlagMessageOption`,
`hideMessageInfoOption`, `hideShareMessageOption`, `hideTimestamp`, `hideGroupActionMessages`).
**Slots:** `HeaderView` · `FooterView` · `EmptyView` · `ErrorView` · `LoadingView` ·
`messageBubbleView` · `NewMessageIndicatorView`.

> **Threads:** `onThreadRepliesPress` → push a screen with `CometChatThreadHeader`. Not
> `onThreadRepliesClick` (React's name), and not a side panel.
> **AI features need BOTH** the dashboard toggle **and** the `show*` prop — the prop is `false` by default.

## CometChatMessageComposer
**Props:** `user` · `group` · `disableTypingEvents` · `disableMentions` · `disableMentionAll` ·
`disableSoundForOutgoingMessages` · `hideAttachmentButton` · `hideSendButton` ·
`hideVoiceRecordingButton` · `hideStickersButton` · `hideAuxiliaryButtons` · plus per-attachment
toggles (`hideImageAttachmentOption`, `hideVideoAttachmentOption`, `hideFileAttachmentOption`,
`hideAudioAttachmentOption`, `hideCameraOption`, `hidePollsAttachmentOption`,
`hideCollaborativeDocumentOption`, `hideCollaborativeWhiteboardOption`).
**Slots:** `HeaderView` · `SendButtonView` · `AuxiliaryButtonView` · `CustomView`.

> The composer owns attachments. A hand-rolled `react-native-image-picker` flow means the built-in
> was missed.

## CometChatSearch
**Props:** `onBack` · `onConversationClicked` · `onMessageClicked` · `onError` ·
`hideBackButton` · `conversationsRequestBuilder` · `messagesRequestBuilder`.

> Opened from `onSearchBarClicked` as a **pushed screen**. Wire `onBack` in the same edit — an
> opened surface with no way back is a dead end.
> **In-chat search must be SCOPED** to the open conversation via the request builders; unscoped, a
> header search leaks whole-app results.
