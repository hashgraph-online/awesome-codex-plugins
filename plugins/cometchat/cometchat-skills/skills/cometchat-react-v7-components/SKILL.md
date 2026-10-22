---
name: cometchat-react-v7-components
description: "The React v7 UI Kit component catalog — which drop-in components exist and how to compose/swap them (conversations, messages, users, groups, threads, calling, bubbles). Triggers: 'what cometchat components are there', 'customize the message list', 'swap the message bubble', 'add a users list'."
license: "MIT"
compatibility: "React >=18; @cometchat/chat-uikit-react ^7 (7.1.x, verified 7.1.0)"
metadata:
  author: "CometChat"
  version: "1.0.1"
  tags: "cometchat react components uikit catalog v7"
---

> **Ground truth:** `@cometchat/chat-uikit-react@7`. Component names below are from the live v7 components docs (see `../cometchat-react-v7-core/references/docs-map.md` → `/ui-kit/react/components-overview`). Status: **catalog-verified vs installed 7.1.0 (exports-only `web-v7.json`).** Fetch each component's prop table from its **`.md` twin** (`../cometchat-react-v7-core/references/docs-map.md`) — do NOT bake it; never read `.d.ts`.

## Companion skills (read first)
- `cometchat-react-v7-core` — install, credentials, `init→login→render`, provider. This skill ASSUMES it.

## Use this skill when
Choosing, composing, or swapping UI Kit components; "which components exist"; customizing a list/message/bubble.

## Prerequisites & install
Covered by core. This skill adds no new package.

## Component catalog (BAKED closed list — from live v7 docs; confirm vs web-v7.json)
Conversations & lists: `CometChatConversations`, `CometChatUsers`, `CometChatGroups`, `CometChatGroupMembers`.
Messages: `CometChatMessageHeader`, `CometChatMessageList`, `CometChatMessageComposer`, `CometChatMessageBubble`, `CometChatThreadHeader`, `CometChatMessageInformation`, `CometChatReactions`, `CometChatReactionList`.
Message bubbles: `CometChatTextBubble`, `CometChatImagesBubble`, `CometChatVideosBubble`, `CometChatAudiosBubble`, `CometChatVoiceNoteBubble`, `CometChatFilesBubble`, `CometChatPollBubble`, `CometChatStickerBubble`, `CometChatCollaborativeDocumentBubble`, `CometChatCollaborativeWhiteboardBubble`, `CometChatCardBubble`, `CometChatGroupActionBubble`, `CometChatCallActionBubble`, `CometChatCallBubble`.
Calling UI: `CometChatCallButtons`, `CometChatIncomingCall`, `CometChatOutgoingCall`, `CometChatOngoingCall`, `CometChatCallLogs`.
Search & AI: `CometChatSearch`, `CometChatAIAssistantChat`, `CometChatSmartReplies`, `CometChatConversationStarter`, `CometChatConversationSummary`.
Moderation / notifications feed: `CometChatModerationView`, `CometChatNotificationFeed`, `CometChatFlagMessageDialog` (end-user report/flag dialog).
Interactive/dialogs: `CometChatCreatePoll` (poll-authoring dialog; pairs with `CometChatPollBubble`).
Base/util: `CometChatProvider`, `CometChatAvatar`, `CometChatButton`, `CometChatFullScreenViewer`, `CometChatConfirmDialog`, `CometChatContextMenu`, `CometChatErrorBoundary`.
> This is the closed list — if a name isn't here (and in `web-v7.json`), it does not exist; do not use it.
> **Phantoms removed 2026-07-30 (AUDIT-008 — reviewer G0 catalog sweep vs installed `@cometchat/chat-uikit-react@7.1.0` `.d.ts`).** These names were in earlier drafts but DO NOT exist in v7 — never emit them: `CometChatTypingIndicator` (typing renders inside `CometChatMessageHeader`; `CometChatTypingDisplay` is a *type*, not a component), `CometChatEmojiKeyboard` (emoji is the built-in EMOJI button in `CometChatMessageComposer`), `CometChatMediaRecorder` (voice recording is built into `CometChatMessageComposer`, `hideVoiceRecordingButton` default false), `CometChatListItem` (list items are internal item-views of the list components), `CometChatToast` (no standalone toast component). Note `CometChatNotifications` is a **Chat SDK** class (`@cometchat/chat-sdk-javascript`, push token registration) — NOT a UI Kit component; don't render it.

## Swap / compose slots
- v7 components are **compound components**: compose behavior via namespace sub-components (e.g. `Root`, `View`, `EmptyState`) and prop-driven slots rather than deep prop sprawl. Fetch the exact composition API + props from the component's **`.md` twin** (`../cometchat-react-v7-core/references/docs-map.md`) before emitting — never the `.d.ts`.
- **Custom UI goes in a component's view slot, INSIDE it — never as a sibling on top.** Stable props + view slots for the 4 drop-ins are baked in `../cometchat-react-v7-core/references/component-props.md` (Conversations `headerView`/`searchView`, MessageHeader `trailingView`/`auxiliaryButtonView`, MessageList `headerView`/`footerView`, Composer `auxiliaryButtonView`/`headerView`) — use them before hand-rolling or hanging controls outside the component.
- Prefer configuring the highest-level component (e.g. `CometChatConversations`) over rebuilding it from base components.
- **Reuse built-in triggers before hand-rolling UI.** Map each requested action to an existing prop/callback/slot FIRST; only add custom buttons when none exists. Discovery order: prop table + each prop's "when to use it" note in docs → if undescribed, fetch the component's `.md` twin (`../cometchat-react-v7-core/references/docs-map.md`) → then custom. Known wiring points: `CometChatMessageHeader` `onItemClick` (open user/group profile on header click) and `onSearchOptionClicked` (built-in search button, `showSearchOption` default `true`); `CometChatConversations` `onSearchBarClicked` (conversation search); `CometChatMessageList` `onThreadRepliesClick` (thread panel). See AUDIT-006.

## Creating a group (host-composed — NO kit component; offer ALL THREE types incl. password)
v7 ships **no `CometChatCreateGroup` component** — the create-group form is HOST-BUILT. Build it from the **`guide-group-chat-setup`** guide (docs-map "Task guides"), which shows the full form. **It MUST offer all THREE group types — Public · Private · Password-protected — not just public/private (AUDIT-081).** The Password type REQUIRES a password field; create the group with the Chat SDK (symbols verified vs installed 7.x SDK):
```tsx
import { CometChat } from "@cometchat/chat-sdk-javascript";
// type ∈ CometChat.GROUP_TYPE.PUBLIC | .PRIVATE | .PASSWORD   ("public" | "private" | "password")
const group = new CometChat.Group(guid, groupName, CometChat.GROUP_TYPE.PASSWORD, password); // 4th arg = password (REQUIRED for the PASSWORD type)
await CometChat.createGroup(group);
```
Show the password input ONLY when the Password type is chosen, and require it before submit (public/private need no password). Dropping the Password option (offering only public/private) is a create-group defect — the SDK (`Group(guid, name, type, password?)`, `GROUP_TYPE.PASSWORD`) and the guide both support it.

## Banned members — view + unban (SDK fallback; NO kit component or UI-Kit doc)
The group-details contract requires **`view-banned-members`**, but v7 ships **no banned-members drop-in** — `CometChatGroupMembers` shows only ACTIVE members (it exposes the ban ACTION via `hideBanMemberOption`, not a banned view), and the UI-Kit guide/component docs don't cover viewing banned users (AUDIT-082). So surface them via the **Chat SDK** (UI-Kit-first → SDK-fallback, `RULES.md` §13; symbols verified vs installed 7.x SDK + documented at `sdk/javascript/group-kick-ban-members`). Add a **scope-gated** "Banned members" affordance in group details (admins/owners only):
```tsx
import { CometChat } from "@cometchat/chat-sdk-javascript";

// FETCH — paginate by calling fetchNext() again on the SAME request object (max limit 100)
const req = new CometChat.BannedMembersRequestBuilder(guid).setLimit(30).build(); // .setSearchKeyword(kw) optional
const banned = await req.fetchNext();          // Promise<CometChat.GroupMember[]>

// UNBAN (admin/owner only), then refresh the list
await CometChat.unbanGroupMember(guid, uid);   // Promise<boolean>
```
Gate the whole affordance on the logged-in user's group scope (`admin`/`owner`) — a plain member shouldn't see it. Render the banned list with an "Unban" action per row (refresh on success). Mirrors the official sample app's "Banned Members" section (the `sample_banned_members` string). This closes the ban round-trip: ban (in `CometChatGroupMembers`) → view banned → unban.

## Common pitfalls (BAKED)
- **Default-on affordances that need stitching.** A drop-in can render a live-looking control BY DEFAULT that no-ops until the host wires a callback + companion panel. When FETCHing props, flag these and either wire or hide them — never let one dead-end. Known cases (v7): `CometChatConversations` `showSearchBar` (default `true`) only client-side-filters loaded names → wire `onSearchBarClicked`→`CometChatSearch` or set `showSearchBar={false}`; `CometChatMessageList` thread-reply indicator → wire `onThreadRepliesClick` + thread panel or set `hideReplyInThreadOption`. See `features.json` `needs_stitching` and AUDIT.md.
- Emitting a **contracted** component (e.g. `CometChatConversations`, `CometChatGroupMembers`) without its FULL `contracts.json` min_capabilities ships an incomplete/inconsistent screen — include the full minimum every time (a group details screen MUST have view/add/kick/ban/banned/scope).
- **Create-group form offering only Public/Private (AUDIT-081).** No kit create-group component exists, so the form is host-built — it MUST include the **Password-protected** type (with a password field required on submit), not just public/private. See "Creating a group" above.
- Referencing a component that isn't in the catalog (phantom). Rebuilding a drop-in from base parts when a prop/slot exists. Assuming v6 prop names — v7 changed the composition model; fetch current props.

## Verify it works
The component renders and its data populates (list fills, message sends). If it's empty, confirm it's inside `CometChatProvider` with a logged-in user.
