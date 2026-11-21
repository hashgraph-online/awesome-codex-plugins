---
name: cometchat-ios-components
description: "The CometChat iOS UI Kit component catalogue — what each component is for, its real API shape, and where custom UI goes. Use when picking or customising an individual component. Triggers: 'which cometchat component', 'customise the conversation row', 'add a custom view to the message list', 'ios component list'."
license: "MIT"
compatibility: "CometChatUIKitSwift 5.2.3+ (Up to Next Major) · iOS 15.1+"
metadata:
  author: "CometChat"
  version: "1.0.0"
  tags: "cometchat ios components swift uikit v5"
---

## Companion skills (read first)
- `cometchat-ios-core` owns install, credentials, `init → login → render` and the golden-path chat surface. This skill ADDS the per-component catalogue; it never restates core's setup. Fetch exact API via `cometchat-ios-core/references/docs-map.md`.

## Use this skill when
Choosing a component, or customising one: "what shows the member list?", "put a badge on the conversation row", "swap the message bubble".

## The catalogue (catalog-verified — nothing else exists)
| Component | For |
|---|---|
| `CometChatConversations` | Recent-chats list · the usual entry point |
| `CometChatMessageHeader` · `CometChatMessageList` · `CometChatCompactMessageComposer` | The chat screen — **you compose these three yourself** |
| `CometChatUsers` · `CometChatGroups` · `CometChatGroupMembers` | Pickers and rosters |
| `CometChatSearch` | Global search over conversations and messages |
| `CometChatThreadedMessageHeader` | Thread parent header |
| `CometChatCallButtons` · `CometChatIncomingCall` · `CometChatOngoingCall` · `CometChatCallLogs` | Calling → `cometchat-ios-calls` |
| `CometChatAvatar` · `CometChatBadge` · `CometChatStatusIndicator` · `CometChatDate` · `CometChatReceipt` | Base building blocks |
| `CometChatMessageInformation` · `CometChatAIAssistanceChatHistory` | Per-message detail · AI history |
| `CometChatScopeChange` | Change a member's role. `set(group:groupMember:)`, `options: [(String, CometChat.MemberScope)]` (property). Present it as a sheet. Through 5.1.22 its Cancel only called `dismiss()`, so a pushed one stranded the user; 5.2.3 pops when pushed (source), but presenting stays the safe default. `CometChatGroupMembers` already presents it on row tap. |

> **There is NO composite component.** `CometChatMessages`, `CometChat{Users,Groups,Conversations}WithMessages`, `CometChatAddMembers`, `CometChatMessageHeaderOption` are v4 or non-existent — never emit them. If a symbol is not in `catalogs/ios-v5.json`, it does not exist in v5, whatever a page says.

## Three API shapes — get this right or nothing compiles
1. **Setters** return `Self` and are chainable: `set(user:)`, `set(onItemClick:)`, `set(subtitle:)`.
2. **Properties** are assigned: `list.avatarStyle = ...`, `conversations.onSearchClick = { ... }`, `groups.onSelectedItemProceed = { ... }`.
3. **Named setters** — `setXxx(xxx:)` with the label repeated: `CometChatMessageInformation` uses `setSubtitle(subtitle:)`, `setBubbleView(bubbleView:)`, `setListItemView(listItemView:)`, `setOnError(onError:)`. Writing them in shape-1 form (`set(subtitle:)`) does not compile on that component.
Which is which is **per component, and the kit is not consistent** — `CometChatConversations` has `set(subtitleView:)`/`set(trailView:)` while `CometChatUsers` and `CometChatGroups` have `set(subtitle:)`/`set(trailingView:)`, and `CometChatGroupMembers` uses the Conversations spelling. **Never generalise a name across components — fetch the component's `.md` twin.**

## Where custom UI goes — IN the component's slot, never beside it
Every list component exposes: `set(listItemView:)` (whole row) · `set(leadingView:)` · `set(titleView:)` · subtitle · trailing · `set(options:)` (swipe/overflow actions). Use these instead of building your own row above the list.
Empty/error/loading are **assignable views** inherited from `CometChatListBase`: `emptyStateView`, `errorStateView`, `loadingView`, plus `emptyStateTitleText` / `emptyStateSubTitleText` to retitle the built-in one. `CometChatSearch` is the exception — it does NOT inherit `CometChatListBase`, so it has none of that chrome; it uses `set(emptyView:)` / `set(errorView:)` / `set(loadingView:)` instead.

## Gotchas
- **`set(controller:)` on any component that presents something** (header, list, composer) or its built-in affordances render and do nothing.
- **`CometChatAvatar` — use `setAvatar(avatarUrl:with:)`** (its `with:` name renders initials when no URL loads). There is no `set(user:)`. On 5.1.19 to 5.1.22 an avatar given a `UIImage` through `set(image:)` or `init(image:)` drew an empty circle (measured on 5.1.19: the kit repainted over it) and there was no no-arg init. 5.2.3 fixes both in source: a supplied image is kept (`hasSuppliedImage` in `CometChatAvatar.swift`) and `CometChatAvatar()` compiles. The image path has not been re-run on a device, so still prefer `setAvatar` for user and group avatars.
- **Search slots are per result TYPE**: `set(listItemViewForMessage:)` plus `...ForImage/Video/Audio/Document/Link/Conversation`. There are no `*ForMessage` granular (title/subtitle/leading/trailing) slots — those exist for conversations only, as properties.

## Verify it works
The component renders at full size, its custom slot appears in the right place (inside the row, not above the list), and every rendered control does something when tapped.
