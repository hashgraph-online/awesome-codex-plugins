# page-map — CometChat React Native Chat SDK v4: intent → page → contract

**Page-wise, exactly like the JavaScript SDK repo.** One row per docs page: the intent it
answers, the page to fetch, the methods it demonstrates, and the contract facts the RN page
does **not** carry.

Fetch a page as `{SDK_DOCS_BASE}/sdk/react-native/<page>` **+ `.md`**. `QR` marks pages that
already carry an "AI Integration Quick Reference" accordion — read it first when present.

Rows and method lists are **derived from the live RN docs pages**, not hand-typed, so they
cannot drift from what the pages actually demonstrate. Every method named is in
`catalogs/rn-sdk-v4.json`.

---

## ⚠️ IF THE PAGE OR METHOD IS NOT HERE — the fallback ladder

This maps **37 pages**. It is not the whole SDK, and **"not listed" NEVER means "does not
exist."** Walk the ladder, cheapest rung first:

| # | Rung | Answers |
|---|---|---|
| 1 | **this page-map** | which page · which methods · the traps |
| 2 | **`catalogs/rn-sdk-v4.json`** (317 symbols) | *does it exist at all?* **Not in the catalog ⇒ do not emit it.** |
| 3 | **scoped index** `/sdk/react-native/llms-react-native-v4.md` | which page covers it (~3k tok) |
| 4 | **that page + `.md`** | its Quick Reference, then prose |
| 5 | **the installed `.d.ts`** | the signature — last resort, **and flag a DOCS GAP** |

Rung 5 carries an obligation: if the docs did not answer and you read the `.d.ts`, that **is** a
docs gap — flag it (page · what is missing · why it mattered). Silently source-filling
guarantees the next agent re-derives it.

**Not covered here by design:** calls (a different package — see the `calls` skill) and SDK
internals (`getApiKey`, `getAppId`, `connect`, `disconnect`, `isInitialized`, `setSource`).

> Everything is namespaced: `import { CometChat } from "@cometchat/chat-sdk-react-native"`.
> A bare `sendMessage()` does not exist — the RN docs often print the bare form.

---

| Intent | Page (`+ .md`) | Methods it demonstrates | QR | Contract facts the page does NOT carry |
|---|---|---|---|---|
| AI agents | [`ai-agents`](/sdk/react-native/ai-agents) | `addAIAssistantListener` · `addMessageListener` · `init` · `login` · `removeAIAssistantListener` · `removeMessageListener` | ✓ |  |
| add members | [`group-add-members`](/sdk/react-native/group-add-members) | `addGroupListener` · `addMembersToGroup` · `removeGroupListener` | ✓ | `addMembersToGroup(guid, groupMembers, bannedMembersList)` takes **three** args — the third is easy to omit. |
| all listeners | [`real-time-listeners`](/sdk/react-native/real-time-listeners) | `addCallListener` · `addGroupListener` · `addMessageListener` · `addUserListener` · `removeCallListener` · `removeGroupListener` … | ✓ | **Every `add*Listener(id, …)` needs `remove*Listener(id)` on teardown.** The SDK holds the listener, not React, so it survives unmount — the top cause of duplicate messages. |
| attachments | [`upload-files`](/sdk/react-native/upload-files) | `logout` · `sendMediaMessage` | — |  |
| block · unblock | [`block-users`](/sdk/react-native/block-users) | `blockUsers` · `unblockUsers` | ✓ | `blockUsers` / `unblockUsers` take an **array** of uids, not a single uid. |
| campaigns · notification feed | [`campaigns`](/sdk/react-native/campaigns) | `addMessageListener` · `addNotificationFeedListener` · `getNotificationFeedItem` · `getNotificationFeedUnreadCount` · `markFeedItemAsDelivered` · `markFeedItemAsRead` … | — |  |
| connection state | [`connection-status`](/sdk/react-native/connection-status) | `addConnectionListener` · `getConnectionStatus` · `init` · `removeConnectionListener` | ✓ | `connect`/`disconnect` are internals — only for manual socket control, which most apps should not do. |
| conversation list | [`retrieve-conversations`](/sdk/react-native/retrieve-conversations) | `getConversation` · `tagConversation` | ✓ | Paginated: `new CometChat.ConversationsRequestBuilder().setLimit(n).build()` → `.fetchNext()`. An **empty array means the end** — it does not throw. |
| create a group | [`create-group`](/sdk/react-native/create-group) | `createGroup` · `createGroupWithMembers` | ✓ |  |
| create/update a user | [`user-management`](/sdk/react-native/user-management) | `createUser` · `updateCurrentUserDetails` · `updateUser` | ✓ | `updateUser` needs the Auth Key ⇒ backend. `updateCurrentUserDetails` is the **client-safe** way for a user to edit themselves. |
| delete a conversation | [`delete-conversation`](/sdk/react-native/delete-conversation) | `deleteConversation` | ✓ |  |
| delete a group | [`delete-group`](/sdk/react-native/delete-group) | `deleteGroup` | ✓ |  |
| delete a message | [`delete-message`](/sdk/react-native/delete-message) | `addMessageListener` · `deleteMessage` | ✓ | Soft delete — resolves a **tombstone**; the message does not vanish. |
| edit a message | [`edit-message`](/sdk/react-native/edit-message) | `addMessageListener` · `editMessage` · `removeMessageListener` | ✓ |  |
| ephemeral messages | [`transient-messages`](/sdk/react-native/transient-messages) | `addMessageListener` · `sendTransientMessage` | ✓ | `sendTransientMessage` returns **void** and is **not persisted**. |
| group list | [`retrieve-groups`](/sdk/react-native/retrieve-groups) | `getGroup` · `getOnlineGroupMemberCount` | ✓ | Paginated via `GroupsRequestBuilder`. |
| install · init | [`setup-sdk`](/sdk/react-native/setup-sdk) | `init` · `login` | ✓ | `init` must **resolve** before `login`. Build settings with `AppSettingsBuilder`. Out of order fails **quietly**. |
| join a group | [`join-group`](/sdk/react-native/join-group) | `addGroupListener` · `joinGroup` · `removeGroupListener` | ✓ |  |
| kick · ban · unban | [`group-kick-ban-members`](/sdk/react-native/group-kick-ban-members) | `addGroupListener` · `banGroupMember` · `kickGroupMember` · `removeGroupListener` · `unbanGroupMember` | ✓ | ⚠️ **The ban round trip.** `CometChatGroupMembers` lists **active** members only and kit v5 ships no banned-members UI. Pair `banGroupMember` with `BannedMembersRequestBuilder` + `unbanGroupMember`, or the admin cannot see or reverse a ban (RN twin of React AUDIT-082). |
| leave a group | [`leave-group`](/sdk/react-native/leave-group) | `addGroupListener` · `leaveGroup` · `removeGroupListener` | ✓ |  |
| login · logout · session | [`authentication-overview`](/sdk/react-native/authentication-overview) | `createUser` · `getLoggedinUser` · `login` · `logout` | ✓ | `login(...args: any)` is **variadic and untyped** — TS catches nothing. Shapes: `login(uid, authKey)` dev, `login(authToken)` prod. `getLoggedinUser()` returns `User \| null`; `null` is the normal no-session answer. Note the lowercase **`in`**. `createUser` needs the Auth Key ⇒ **backend only**. |
| manual socket control | [`managing-web-sockets-connections-manually`](/sdk/react-native/managing-web-sockets-connections-manually) | `connect` · `disconnect` · `getLoggedinUser` · `init` · `login` · `ping` | ✓ |  |
| mentions | [`mentions`](/sdk/react-native/mentions) | `sendMessage` | ✓ |  |
| moderation | [`ai-moderation`](/sdk/react-native/ai-moderation) | `addMessageListener` · `removeMessageListener` · `sendMessage` | ✓ |  |
| online/offline presence | [`user-presence`](/sdk/react-native/user-presence) | `addUserListener` · `init` · `removeUserListener` | ✓ | Requires `subscribePresenceForAllUsers()` in `AppSettingsBuilder` at init. |
| orientation | [`overview`](/sdk/react-native/overview) | `getLoggedinUser` · `init` · `login` | ✓ |  |
| promote/demote a member | [`group-change-member-scope`](/sdk/react-native/group-change-member-scope) | `addGroupListener` · `removeGroupListener` · `updateGroupMemberScope` | ✓ |  |
| reactions | [`reactions`](/sdk/react-native/reactions) | `addMessageListener` · `addReaction` · `removeMessageListener` · `removeReaction` | ✓ | Reactions are **core** in kit v5 — there is no extension to enable. Offering the legacy dashboard extension is a defect (React AUDIT-077). |
| receipts | [`delivery-read-receipts`](/sdk/react-native/delivery-read-receipts) | `addMessageListener` · `getMessageReceipts` · `markAsDelivered` · `markAsRead` · `markConversationAsDelivered` · `markConversationAsRead` … | ✓ | `markAsRead(...args: any): any` is **untyped** — treat as fire-and-forget. |
| receive messages · unread counts | [`receive-messages`](/sdk/react-native/receive-messages) | `addMessageListener` · `getLastDeliveredMessageId` · `getMessageDetails` · `getUnreadMessageCount` · `getUnreadMessageCountForAllGroups` · `getUnreadMessageCountForAllUsers` … | ✓ | `addMessageListener` returns **void**, not a subscription — the string id is your only handle. `getUnreadMessageCount` has scoped variants (`…ForUser` / `ForGroup` / `ForAllUsers` / `ForAllGroups`) with the same shape. |
| report a message | [`flag-message`](/sdk/react-native/flag-message) | `flagMessage` · `getFlagReasons` | ✓ | Fetch the allowed reasons with `getFlagReasons()` — **do not hardcode them**. |
| send a message | [`send-message`](/sdk/react-native/send-message) | `sendCustomMessage` · `sendMediaMessage` · `sendMessage` | ✓ | **There is no `sendCardMessage()`** — card/interactive messages are receive-only from the client (verified absent from the catalog). Do not invent it by symmetry. `receiverType`: `RECEIVER_TYPE.USER` → a **UID**, `GROUP` → a **GUID**. |
| threads | [`threaded-messages`](/sdk/react-native/threaded-messages) | `addMessageListener` · `removeMessageListener` · `sendMessage` | ✓ |  |
| transfer ownership | [`transfer-group-ownership`](/sdk/react-native/transfer-group-ownership) | `transferGroupOwnership` | ✓ | resolves a **string**, not a `Group`. |
| typing | [`typing-indicators`](/sdk/react-native/typing-indicators) | `addMessageListener` · `endTyping` · `removeMessageListener` · `startTyping` | ✓ | `startTyping` / `endTyping` return **void — do not `await`**. `endTyping` must be called explicitly; there is no client-side auto-expiry. |
| update a group | [`update-group`](/sdk/react-native/update-group) | `updateGroup` | ✓ |  |
| user list · presence count | [`retrieve-users`](/sdk/react-native/retrieve-users) | `getLoggedinUser` · `getOnlineUserCount` · `getUser` | ✓ | Paginated via `UsersRequestBuilder`. `getOnlineUserCount()` is cheaper than paging just to count presence. |

---

## RN-G15 — why the "contract facts" column exists at all

The **JavaScript** SDK carries a full contract table on every page — `Package` · `Import` ·
`Key methods` · `Primary output` · `Prerequisites` · `Constraints` · `Key classes` ·
`Listeners registered` · `Request builder` · `Related` · `Full reference` — median **10 rows**
across its 20 documented pages.

The React Native pages carry a name list or a bare code snippet, and are thinner on **13 of 15**
shared pages. So return types, error types and constraints are largely absent.

Everything in the last column was recovered from the installed `.d.ts` or from the kit source.
It is correct, and it is **not documented** — say so when you rely on it, rather than presenting
it as if the page said it. When RN's pages gain the JS-style table, this column shrinks to a
pointer.
