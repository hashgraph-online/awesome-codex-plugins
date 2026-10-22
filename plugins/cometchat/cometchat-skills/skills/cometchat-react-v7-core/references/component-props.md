# component-props — BAKED stable props + view slots for the React v7 drop-ins

The high-value, STABLE props **and view slots** for the core drop-in components — baked here (not
fetched) because getting the slots wrong is the #1 recurring UI defect. Verified against live v7
docs (`components/*.md`). Exhaustive/rare props still come from a component's `.md` twin
(`docs-map.md`), but **these — especially the VIEW SLOTS — are baked.**

## THE RULE — custom UI goes in the component's OWN view slot, NEVER as a sibling on top
A search icon, extra action button, banner, or custom header belongs **inside** the component via
its slot (below). Do **NOT** render it as a sibling element above/beside the component. Rendering
a search control "on top of" the conversation list instead of in its `headerView`, or above the
message header instead of in its `trailingView`, is a defect — fix it by using the slot.

> **List-header actions ("New chat" / "Create group" / "+") go in `headerView` — but `headerView` REPLACES the whole default header, so RE-RENDER the title (AUDIT-083).** The list components (`CometChatConversations` / `CometChatUsers` / `CometChatGroups`) show a default header with a **title** ("Chats"/"Users"/"Groups") by default. Their only header slot is `headerView`, which replaces that ENTIRE header — so if you drop a bare button into `headerView` you LOSE the title. Render BOTH: the title (re-created) AND your action button. Do NOT place the button as a sibling above the list (the defect this rule fixes).
> ```tsx
> import { useLocale } from "@cometchat/chat-uikit-react";
> const { getLocalizedString } = useLocale();
> <CometChatGroups
>   headerView={
>     <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 12px", height: 56 }}>
>       <h3 style={{ margin: 0 }}>{getLocalizedString("groups")}</h3>   {/* re-render the default title */}
>       <button aria-label="Create group" onClick={openCreateGroup}>＋</button>  {/* the action, right of the title */}
>     </div>
>   }
>   onItemClick={openGroup}
> />
> ```
> Same for a **"New chat"** button on `CometChatConversations` (title `"chats"`) and `CometChatUsers` (title `"users"`). (Use `useLocale().getLocalizedString(...)` for the title so it stays localized; `<h3>Chats</h3>` is fine if you don't localize.)

---

## CometChatConversations
**Props:** `onItemClick(conversation)` · `onSearchBarClicked` · `showSearchBar` (default `true`) · `selectionMode` (default `"none"`) · `activeConversation` · `onSelect` · `conversationsRequestBuilder` (scope which conversations load) · `searchRequestBuilder` (scope server-side search) · hide toggles (`hideReceipts`, `hideUserStatus`, `hideGroupType`, `hideDeleteConversation`).
**View slots (inject custom UI INSIDE the component):**
- `headerView: ReactNode` — the **entire header area**. → **Custom header controls (a search icon, filter, custom title) go HERE.**
- `searchView: ReactNode` — the search bar within the header.
- `itemView(conversation)` · `leadingView` · `titleView` · `subtitleView` · `trailingView` — per row.
- `options(conversation) => CometChatConversationOption[]` — per-row context-menu actions.
- `loadingView` · `emptyView` · `errorView` — list states.
> **Search icon in the conversation list header → put it in `headerView`** (or wire `onSearchBarClicked` → `CometChatSearch` rendered in the list column). NOT a sibling on top of the list.
> **Scope the list to the request via `conversationsRequestBuilder` (a `CometChat.ConversationsRequestBuilder`).** A **1:1 / DM-only** app → `.setLimit(30).setConversationType("user")` (hides the app's seeded groups); **groups-only** → `.setLimit(30).setConversationType("group")`. **Always include `.setLimit(n)`** — a builder without it renders the kit's error state instead of the list (verified 7.2.0, 2026-09-12, AUDIT-245; STOPGAP until the docs' filter-recipe table adds it). **Pass the builder INSTANCE, not `.build()`** — the kit builds it internally; passing the built object breaks the list (verified vs live v7 `conversations.md`: "Pass the builder instance — not the result of `.build()`"; AUDIT-038). `searchRequestBuilder` scopes server-side search the same way. A generic unscoped "add chat" → OMIT it (show both users and groups). Don't add a Groups tab to a 1:1-only app.
> ```tsx
> import { CometChat } from "@cometchat/chat-sdk-javascript";
> <CometChatConversations conversationsRequestBuilder={new CometChat.ConversationsRequestBuilder().setLimit(30).setConversationType("user")} />
> ```

## CometChatUsers / CometChatGroups (selector-tab lists)
**Props — REFLECT the selection (active state):** `onItemClick(user|group)` · **`activeUser` / `activeGroup`** — pass the currently-selected user/group so the list HIGHLIGHTS the open row (the analogue of `CometChatConversations activeConversation`). In a selector-tabs app you MUST pass these; without them the list shows **no active state** and the user can't tell which item is open (AUDIT-079). Also `usersRequestBuilder` / `groupsRequestBuilder` to scope the list, and the same view slots (`headerView`, `itemView`, `titleView`/`subtitleView`/`trailingView`, `options`, `loadingView`/`emptyView`/`errorView`).
> **Selection has THREE obligations (AUDIT-079):** (1) render the pane, (2) reflect it via `active*` (here), (3) close every panel it opens (round-trip — see `CometChatGroupMembers`/`CometChatSearch`/`CometChatThreadHeader` `onBack`/`onClose`). Wiring only (1) is a composition dead-end.

## CometChatSearch (the companion opened from `onSearchBarClicked`)
**Props (wire the full round-trip — open AND close):** `onBack()` — **fired by the default back button; wire it to CLOSE search and return to the list (the same state that opened it), or the back button dead-ends** · `onConversationClicked(event)` and `onMessageClicked(event)` — result clicks; wire to **close search + select the result** · `hideBackButton` (default `false`) · `uid`/`guid` (scope to one conversation) · `searchIn` (`["conversations","messages"]`) · `loadingView`/`emptyView`/`errorView`.
> **You opened it — you must close it.** Rendering `CometChatSearch` without `onBack` is the #1 search defect (AUDIT-017): the back button shows but does nothing. Minimal wiring: `const [searching, setSearching] = useState(false)` → open on `onSearchBarClicked`, `onBack={() => setSearching(false)}`, and on `onConversationClicked`/`onMessageClicked` set the selected conversation + `setSearching(false)`.
>
> **TWO searches — both default-on:** (1) **GLOBAL** (all conversations) — from `CometChatConversations onSearchBarClicked`, rendered OVER the list column, NO `uid`/`guid`; (2) **IN-CHAT / SCOPED** (this conversation only) — from `CometChatMessageHeader onSearchOptionClicked`, rendered in the **side panel** (same slot as the thread, mutually exclusive), **scoped with `uid`/`guid`** so it only searches the open chat (the official `CometChatHome` sample pattern). The side panel is ONE mutually-exclusive slot: opening scoped search closes the thread and vice-versa. Full side-panel recipe (both searches wired, with the round-trip): `../../cometchat-react-v7-placement/references/recipes.md`.

## CometChatMessageHeader
**Props:** `onItemClick` (open profile) · `onBack` + `hideBackButton` (default `false`) · `showSearchOption` (default `true`) + `onSearchOptionClicked` · `showConversationSummaryButton` + `onSummaryClick`.
**View slots:**
- `trailingView: ReactNode` — the header **right side** (replaces call buttons + overflow menu). → **Custom action buttons (search, call, custom icon) go HERE.**
- `auxiliaryButtonView: ReactNode` — auxiliary button area.
- `leadingView` · `titleView` · `subtitleView` — replace avatar / name / status.
- Compound sub-components for granular control: `Avatar`, `Title`, `Subtitle`, `CallButtons`, `SearchButton`, `SummaryButton`, `OverflowMenu`, `AuxiliaryButtons`.
> **A custom search/action icon in the message header → put it in `trailingView`** (or `auxiliaryButtonView`), or use the built-in `showSearchOption` + `onSearchOptionClicked`. NOT a sibling above the header.

## CometChatMessageList
**Props:** `onThreadRepliesClick(message)` · `hideReplyInThreadOption` · `showSmartReplies` (default `false`; footer) · `showConversationStarters` (default `false`; footer when empty) · hide toggles (`hideReceipts`, `hideDateSeparator`, `hideReactionOption`, …).
**View slots:**
- `bubbleView(message, loggedInUser)` — replace an entire message bubble.
- `headerView: ReactNode` — banner **above** the scroll container. → **A custom banner/notice goes HERE.**
- `footerView: ReactNode` — area **below** the scroll (smart replies render here).
- `loadingView` · `emptyView` · `errorView`.

## CometChatMessageComposer
**Props:** `placeholder` (default `"Type a message..."`) · `onSendButtonClick(message, mode)` · `enterKeyBehavior` (`"send" | "newline" | "none"`) · `enableMultipleAttachments` · `disableTypingEvents` · `disableMentions` · `layout` (`"compact" | "multiline"`).
**View slots:**
- `headerView: ReactNode` — area **above** the input (reply-preview, banner). → **Custom composer header goes HERE.**
- `auxiliaryButtonView: ReactNode` — extra buttons in the actions area **before** send. → **A custom action button goes HERE.**
- `sendButtonView` · `attachmentButtonIconView` · `voiceRecordingButtonIconView` · `emojiButtonIconView` — swap specific icons/buttons.

---
For any component NOT above, or exhaustive props → fetch the component's `.md` twin (`docs-map.md`). But for these four, **use the slots above** — don't render custom controls outside the component.
