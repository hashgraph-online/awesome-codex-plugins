---
name: cometchat-react-native-components
description: "The closed list of CometChat React Native UI Kit v5 components, what each one is for, and how to put custom UI INSIDE a component's view slot instead of stacking it on top. Triggers: which CometChat component React Native, custom header RN chat, add a button to the conversation list, custom list item RN, CometChat component list, add an avatar to my chat, show a profile picture, status indicator RN, badge RN, list item RN."
license: "MIT"
compatibility: "React Native >=0.77; @cometchat/chat-uikit-react-native ^5.4.0"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "chat cometchat react-native components slots views composition"
---

> **Ground truth:** catalog `rn-v5.json` (216 public symbols) — the closed list below IS the catalog.
> A component not in it does not exist. Fetch props per component via `core/references/docs-map.md`.

## Companion skills (read first)
- `cometchat-react-native-core` — install, provider chain, init→login→render. Assumed, not repeated here.

## Use this skill when
- "which component do I use for X" · "add a button to the conversation list header"
- "custom list row" · "replace the message bubble" · "what components ship in v5"

## Prerequisites & install
None beyond `core`.

## Component catalog (closed list)

**Lists**
| Component | Purpose |
|---|---|
| `CometChatConversations` | recent-conversations list — the usual entry screen |
| `CometChatUsers` | user directory |
| `CometChatGroups` | group directory |
| `CometChatGroupMembers` | **active** members of a group (not banned — see below) |

**Message pane**
| Component | Purpose |
|---|---|
| `CometChatMessageHeader` | title, presence, back, call buttons |
| `CometChatMessageList` | the scrollback; renders bubbles, receipts, reactions |
| `CometChatMessageComposer` | input, attachments, voice notes |
| `CometChatCompactMessageComposer` | single-line composer for tight layouts |
| `CometChatThreadHeader` | thread replies — a **screen** on RN, not a side panel |
| `CometChatMessageInformation` | per-message delivery/read detail |

**Search · AI · notifications**
| Component | Purpose |
|---|---|
| `CometChatSearch` | message + conversation search |
| `CometChatAIAssistantChatHistory` · `CometChatAIAssistantTools` | AI assistant surfaces |
| `CometChatConversationStarter` · `CometChatSmartReplies` · `CometChatConversationSummary` | AI suggestions |
| `CometChatNotificationFeed` | in-app notification feed |

**Calling** — needs `@cometchat/calls-sdk-react-native`
| Component | Purpose |
|---|---|
| `CometChatCallButtons` | audio/video call triggers |
| `CometChatIncomingCall` · `CometChatOutgoingCall` · `CometChatOngoingCall` | call lifecycle screens |
| `CometChatCallLogs` | call history **list** (detail views were removed in v5) |

**Bubbles** — the list renders these itself; place them only in a custom template
`CometChatTextBubble` · `CometChatImageBubble` · `CometChatVideoBubble` · `CometChatAudioBubble` ·
`CometChatFileBubble` · `CometChatVoiceNoteBubble` · `CometChatStickerBubble` ·
`CometChatCollaborativeDocumentBubble` · `CometChatCollaborativeWhiteBoardBubble` · `CometChatMeetCallBubble`

**Multi-attachment — RN only, no React equivalent**
`CometChatAttachmentPreview` · `CometChatAttachmentPreviewItem` · `CometChatAttachmentTile` ·
`CometChatAttachmentTray` · `CometChatAttachmentViewer` and the **plural** bubbles
`CometChatImagesBubble` · `CometChatVideosBubble` · `CometChatAudiosBubble` · `CometChatFilesBubble`.
> **DOCS GAP (RN-G4):** all nine are undocumented. Build from the kit source and say so.

**Not components — but public and load-bearing**
`ChatConfigurator` · `DataSourceDecorator` · `CometChatMessageTemplate` (custom message types →
`customization`) · `CometChatThemeProvider` + `useTheme()` · `CometChatI18nProvider` ·
`CometChatUIEventHandler` · `CometChatUiKitConstants`.

**Primitives & building blocks** — exported, and what you reach for when composing a custom row,
header or bubble yourself. Existence is baked here; **fetch each one's props from the docs**
(`core/references/docs-map.md`) — do not infer them from `.d.ts`.
| Group | Exports |
|---|---|
| Identity | `CometChatAvatar` · `CometChatStatusIndicator` · `CometChatBadge` · `CometChatDate` |
| Row shell | `CometChatListItem` |
| Overlays | `CometChatActionSheet` · `CometChatBottomSheet` · `CometChatConfirmDialog` · `CometChatReportDialog` · `CometChatMediaViewer` |
| Composer add-ons | `CometChatEmojiKeyboard` · `CometChatMediaRecorder` · `CometChatInlineAudioRecorder` · `CometChatCreatePoll` · `CometChatSuggestionList` · `CometChatMessagePreview` · `CometChatMessageComposerAction` · `CometChatMessageOption` |
| Reactions | `CometChatReactions` · `CometChatQuickReactions` · `CometChatReactionList` |
| Text formatters | `CometChatTextFormatter` · `CometChatMentionsFormatter` · `CometChatUrlsFormatter` · `CometChatRichTextFormatter` |
| Helpers | `CometChatUIKit` · `CometChatUIKitHelper` · `CometChatSoundManager` |

> Changing a user's own avatar/name is **not** a component — it is the SDK call
> `CometChat.updateCurrentUserDetails()`; see `cometchat-react-native-sdk`.

### Components that do NOT exist in v5
`CometChatErrorBoundary` · `CometChatDetails` · `CometChatAddMembers` · `CometChatBannedMembers` ·
`CometChatTransferOwnership` · `CometChatContacts` · every `*WithMessages` composite ·
`CometChatCallLogDetails` / `History` / `Participants` / `Recordings`.
They were removed in kit v5. Each has an SDK-fallback path in `core/references/docs-map.md` —
**banned members has no UI surface at all**, so an app that bans must also wire view + unban.

## Custom UI goes IN a slot, not on top

Every list and header exposes **view slots**. Custom UI belongs inside the slot so the component keeps
its own layout, scrolling and empty/error states. Stacking a sibling above the list is the classic
mistake — it double-renders headers and breaks scroll.

⚠️ **RN slot props are PascalCase.** React's are camelCase; a ported snippet silently does nothing
because an unknown prop is simply ignored.

| Component | Slots |
|---|---|
| `CometChatConversations` | `ItemView` · `TitleView` · `SubtitleView` · `LeadingView` · `TrailingView` · `SearchView` · `EmptyView` · `ErrorView` · `LoadingView` |
| `CometChatUsers` / `CometChatGroups` | `ItemView` · `TitleView` · `SubtitleView` · `LeadingView` · `TrailingView` · `EmptyView` · `ErrorView` · `LoadingView` |
| `CometChatMessageHeader` | `ItemView` · `TitleView` · `SubtitleView` · `LeadingView` · `TrailingView` · `AuxiliaryButtonView` |
| `CometChatMessageList` | `HeaderView` · `FooterView` · `EmptyView` · `ErrorView` · `LoadingView` |
| `CometChatMessageComposer` | `HeaderView` · `SendButtonView` · `AuxiliaryButtonView` · `CustomView` |

```tsx
import { CometChatConversations } from "@cometchat/chat-uikit-react-native";
import { Pressable, Text } from "react-native";

<CometChatConversations
  TrailingView={() => (
    <Pressable onPress={onArchive}>
      <Text>Archive</Text>
    </Pressable>
  )}
/>;
```

Slot names differ per component — fetch the exact list from that component's docs page rather than
copying from a sibling.

## Common pitfalls
1. **camelCase slot props** — `itemView` is ignored silently. RN uses `ItemView`.
2. **Rendering a sibling above a list** instead of using its slot — duplicate headers, broken scroll.
3. **Placing a bubble component directly** — the list renders bubbles; use a template (`customization`).
4. **Reaching for a removed component** — check the closed list above before emitting.
5. **Assuming `CometChatGroupMembers` covers banned users** — it lists active members only.

## Verify it works
- Every emitted component appears in `catalogs/rn-v5.json`.
- `npm run verify:fences:rn-v5` is green.
- On device: custom slot content renders inside the component, and the list still scrolls.
