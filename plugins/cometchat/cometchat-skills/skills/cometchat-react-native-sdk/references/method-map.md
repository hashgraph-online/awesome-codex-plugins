# method-map — CometChat React Native Chat SDK v4

The **fallback lookup**: which method, what it returns, what it throws, what it refuses to do.

Field names follow the **JavaScript SDK's** contract schema (derived from all 20 of its
documented pages), so the two read identically:
`Package` · `Import` · `Key methods` · `Key classes` · `Primary output` · `Prerequisites` ·
`Constraints` · `Listeners registered` · `Request builder` · `Related`.

Signatures are **verbatim from the installed `.d.ts`** of `@cometchat/chat-sdk-react-native@4.0.28`.
Every symbol is in `catalogs/rn-sdk-v4.json` (317 symbols).

---

## ⚠️ IF IT IS NOT IN THIS MAP — the fallback ladder

This map covers **~60 of the SDK's 127 methods**. That is deliberate: a dump of all 127 would
include internals nobody should call, and a map nobody reads is worse than no map.

**So "not listed here" does NOT mean "does not exist."** Never conclude absence from this file.
Walk the ladder instead — each rung is cheaper than the one below it:

| # | Rung | Answers | Cost |
|---|---|---|---|
| 1 | **this map** | full contract | free |
| 2 | **`catalogs/rn-sdk-v4.json`** | *does it exist at all?* **Not in the catalog ⇒ it does not exist — do not emit it.** | free |
| 3 | **scoped SDK index** — `{DOCS_BASE}/sdk/react-native/llms-react-native-v4.md` | which page covers it | ~3k tok |
| 4 | **that page + `.md`** | its Quick Reference accordion, then prose | 1 page |
| 5 | **the installed `.d.ts`** | the signature, when the page is thin | last resort |

**Rung 5 carries an obligation.** If you had to read the `.d.ts` because the docs did not answer,
that is a **DOCS GAP** — flag it for the developer (page · what is missing · why it mattered).
Never silently source-fill: a gap that is filled quietly is a gap that is never fixed, and the
next agent re-derives it from scratch.

Two things this map will never cover, by design:
- **calls** — a different package (`@cometchat/calls-sdk-react-native`); see the `calls` skill
- **internals** — `getApiKey` · `getAppId` · `connect` · `disconnect` · `isInitialized` ·
  `getConnectionStatus` · `setSource` · `setDemoMetaInfo`. They exist; a chat integration has
  no reason to call them.

> Everything hangs off the namespace: `import { CometChat } from "@cometchat/chat-sdk-react-native"`.
> A bare `sendMessage()` does not exist. The RN docs frequently print the bare form.

Row source: **`D`** = backed by the RN docs · **`T`** = recovered from the `.d.ts` because the RN
page is thin (**RN-G15**). A `T` row is correct but **not documented** — say so if you rely on it.

---

## Lifecycle

| Field | Value |
|---|---|
| Package | `@cometchat/chat-sdk-react-native` |
| Import | `import { CometChat } from "@cometchat/chat-sdk-react-native";` |
| Key classes | `AppSettingsBuilder` · `AppSettings` · `User` · `CometChatException` |
| Prerequisites | none — this is the entry point |
| Constraints | `init` must **resolve** before `login`; `login` must resolve before any fetch or send. Out of order fails **quietly**, not loudly. |

| Method | Signature | Returns | Notes | Src |
|---|---|---|---|---|
| `init` | `init(appId: any, appSettings: AppSettings): Promise<boolean>` | `true` | rejects `CometChatException`; always `await` and log | D |
| `initFromSettings` | `initFromSettings(settings): Promise<boolean>` | `true` | settings-object form; also sets telemetry attribution | T |
| `login` | `login(...args: any): Promise<User>` | `User` | **VARIADIC AND UNTYPED** — TS catches nothing. Real shapes: `login(uid, authKey)` dev, `login(authToken)` prod | T |
| `logout` | `logout(): Promise<Object>` | — | unregister the push token **first** | D |
| `getLoggedinUser` | `getLoggedinUser(): Promise<User \| null>` | `User` or **`null`** | `null` = no session, **not an error**. Lowercase **`in`** | T |

## Messaging — send

| Field | Value |
|---|---|
| Key classes | `TextMessage` · `MediaMessage` · `CustomMessage` · `InteractiveMessage` |
| Primary output | `Promise<BaseMessage>` — resolves the **sent** message; rejects `CometChatException` |
| Receiver targeting | `RECEIVER_TYPE.USER` → a **UID** · `RECEIVER_TYPE.GROUP` → a **GUID** |
| Constraints | **There is no `sendCardMessage()`.** Card/interactive messages are **receive-only** from the client — verified absent from the catalog. Do not invent it by symmetry with the three that exist. |
| Receive counterpart | `addMessageListener` — see Listeners |

| Method | Signature | Notes | Src |
|---|---|---|---|
| `sendMessage` | `sendMessage(message: TextMessage \| MediaMessage \| CustomMessage \| InteractiveMessage \| any): Promise<…>` | the one you want in almost every case | D |
| `sendMediaMessage` | `sendMediaMessage(message: Object): Promise<…>` | attachment count is server-capped; over it **rejects**, not truncates | T |
| `sendCustomMessage` | `sendCustomMessage(message): Promise<…>` | app-defined JSON payloads | D |
| `sendInteractiveMessage` | `sendInteractiveMessage(message): Promise<…>` | forms/schedulers | T |
| `sendTransientMessage` | `sendTransientMessage(message): void` | ephemeral (live reactions); **not persisted, returns void** | T |
| `sendDirectMessage` | `sendDirectMessage(message: Object): Promise<…>` | 1:1 variant — **coexists with `sendMessage`, neither marked deprecated.** Prefer `sendMessage`; the docs use it | T |
| `sendGroupMessage` | `sendGroupMessage(message: any): Promise<…>` | group variant, same caveat | T |

## Messaging — modify & moderate

| Method | Signature | Notes | Src |
|---|---|---|---|
| `editMessage` | `editMessage(message): Promise<BaseMessage>` | resolves the edited message | T |
| `deleteMessage` | `deleteMessage(messageId): Promise<BaseMessage>` | soft delete — resolves a **tombstone**, the message does not vanish | T |
| `getMessageDetails` | `getMessageDetails(messageId): Promise<BaseMessage>` | single message by id | T |
| `flagMessage` | `flagMessage(messageId, reason): Promise<…>` | moderation report | T |
| `getFlagReasons` | `getFlagReasons(): Promise<…>` | fetch the allowed reasons — **do not hardcode them** | T |
| `addReaction` | `addReaction(messageId, reaction: string): Promise<BaseMessage>` | reactions are **core** in v5, no extension to enable | T |
| `removeReaction` | `removeReaction(messageId, reaction: string): Promise<BaseMessage>` | | T |

## Receipts, typing & unread

| Method | Signature | Notes | Src |
|---|---|---|---|
| `markAsRead` | `markAsRead(...args: any): any` | **untyped, returns `any`** — treat as fire-and-forget | T |
| `markAsDelivered` | `markAsDelivered(...args): any` | usually automatic; call only for custom flows | T |
| `markAsUnread` | `markAsUnread(message): Promise<…>` | | T |
| `markConversationAsRead` | `markConversationAsRead(conversation): Promise<…>` | whole conversation at once | T |
| `getMessageReceipts` | `getMessageReceipts(messageId): Promise<Array<MessageReceipt>>` | per-recipient delivery/read state | T |
| `markConversationAsDelivered` | `markConversationAsDelivered(conversation): Promise<…>` | conversation-level pair of `markConversationAsRead` | T |
| `markMessageAsUnread` | `markMessageAsUnread(message): Promise<…>` | **coexists with `markAsUnread`**, neither deprecated — prefer `markAsUnread` | T |
| `getLastDeliveredMessageId` | `getLastDeliveredMessageId(...): any` | resume point for a receipt sync | T |
| `markAsInteracted` | `markAsInteracted(messageId, interactionElementId): Promise<…>` | required for **interactive** messages, or engagement never registers | T |
| `startTyping` | `startTyping(typingNotification): void` | **void — do not `await`** | T |
| `endTyping` | `endTyping(typingNotification): void` | must be called explicitly; no client-side auto-expiry | T |
| `getUnreadMessageCount` | `getUnreadMessageCount(...): Promise<Object>` | **Family:** `…ForUser` · `…ForGroup` · `…ForAllUsers` · `…ForAllGroups` are scoped variants with the same shape — pick by scope; not listed individually | T |

## Users

| Field | Value |
|---|---|
| Key classes | `User` · `UsersRequestBuilder` |
| Request builder | `new CometChat.UsersRequestBuilder().setLimit(n).build()` then `.fetchNext()` |
| Constraints | **`createUser` needs the Auth Key** → it is a **backend** call. A client that can create users can create *any* user. |

| Method | Signature | Notes | Src |
|---|---|---|---|
| `getUser` | `getUser(uid: any): Promise<User>` | | D |
| `updateUser` | `updateUser(user, authKey): Promise<User>` | Auth Key ⇒ backend only | T |
| `updateCurrentUserDetails` | `updateCurrentUserDetails(user): Promise<User>` | the **client-safe** way for a user to edit themselves | T |
| `blockUsers` | `blockUsers(uids: Array<string>): Promise<Object>` | takes an **array**, not one uid | T |
| `unblockUsers` | `unblockUsers(uids: Array<string>): Promise<Object>` | | T |
| `getOnlineUserCount` | `getOnlineUserCount(): Promise<number>` | cheaper than paging users just to count presence | T |
| `getOnlineGroupMemberCount` | `getOnlineGroupMemberCount(guids): Promise<Object>` | per-group online counts | T |

## Groups

| Field | Value |
|---|---|
| Key classes | `Group` · `GroupMember` · `GroupMembersRequestBuilder` · `BannedMembersRequestBuilder` |
| Request builder | `GroupMembersRequestBuilder` lists **active** members · `BannedMembersRequestBuilder` lists **banned** ones |
| Constraints | ban/unban/kick/transfer are **admin or owner scope only**. Kit v5 ships **no component** for add-members, banned-members, details or transfer — this is the whole implementation surface. |

| Method | Signature | Notes | Src |
|---|---|---|---|
| `createGroup` | `createGroup(group): Promise<Group>` | | T |
| `createGroupWithMembers` | `createGroupWithMembers(group, members, banned): Promise<Object>` | create + seed in one call — saves an `addMembersToGroup` round trip | T |
| `getGroup` | `getGroup(guid: string \| Object): Promise<Group>` | | D |
| `updateGroup` | `updateGroup(group: any): Promise<Group>` | | T |
| `deleteGroup` | `deleteGroup(guid): Promise<boolean>` | | T |
| `joinGroup` | `joinGroup(guid, type, password?): Promise<Group>` | password only for password-protected groups | T |
| `leaveGroup` | `leaveGroup(guid): Promise<boolean>` | | T |
| `addMembersToGroup` | `addMembersToGroup(guid: string, groupMembers: Array<GroupMember>, bannedMembersList: Array<string>): Promise<Object>` | **THREE args** — the third is easy to forget | T |
| `kickGroupMember` | `kickGroupMember(guid, uid): Promise<boolean>` | reversible — the user may rejoin | T |
| `banGroupMember` | `banGroupMember(guid, uid): Promise<boolean>` | **one half of a round trip** ↓ | T |
| `unbanGroupMember` | `unbanGroupMember(guid, uid): Promise<boolean>` | the other half | T |
| `updateGroupMemberScope` | `updateGroupMemberScope(guid, uid, scope): Promise<string>` | promote/demote | T |
| `transferGroupOwnership` | `transferGroupOwnership(guid, uid): Promise<string>` | resolves a **string**, not a `Group` | T |

> ⚠️ **The ban round trip.** `CometChatGroupMembers` shows **active** members only and v5 ships no
> banned-members UI. An app that offers ban and nothing else leaves the admin unable to see or
> reverse it. Always ship `BannedMembersRequestBuilder` + `unbanGroupMember` alongside `banGroupMember`.

## Conversations

| Field | Value |
|---|---|
| Request builder | `new CometChat.ConversationsRequestBuilder().setLimit(n).build()` → `.fetchNext()`; an **empty array means the end**, it does not throw |

| Method | Signature | Notes | Src |
|---|---|---|---|
| `getConversation` | `getConversation(conversationWith, type): Promise<Conversation>` | | T |
| `deleteConversation` | `deleteConversation(conversationWith, type): Promise<string>` | | T |
| `muteConversations` | `muteConversations(...): Promise<…>` | | T |
| `unmuteConversations` | `unmuteConversations(...): Promise<…>` | | T |
| `tagConversation` | `tagConversation(...): Promise<Conversation>` | custom tags (pin, archive) | T |
| `getMutedConversations` | `getMutedConversations(): Promise<Array<Conversation>>` | the read side of mute/unmute — without it the mute state is write-only | T |

## Listeners — every `add` has a `remove`

| Field | Value |
|---|---|
| Primary output | **`void`** — not a subscription. The string `name` is your only handle. |
| Constraints | The **SDK** holds the listener, not React — it survives unmount and navigation. Omitting the removal is the top cause of duplicate messages, and it worsens the longer the app runs. |

| Register | Remove | Covers | Src |
|---|---|---|---|
| `addMessageListener(name, l)` | `removeMessageListener(name)` | messages, typing, receipts, reactions | D |
| `addUserListener(name, l)` | `removeUserListener(name)` | presence (online/offline) | T |
| `addGroupListener(name, l)` | `removeGroupListener(name)` | joins, leaves, kicks, bans, scope changes | T |
| `addCallListener(name, l)` | `removeCallListener(name)` | call lifecycle — see the `calls` skill | T |
| `addLoginListener(name, l)` | `removeLoginListener(name)` | session/token expiry | T |
| `addConnectionListener(name, l)` | `removeConnectionListener(name)` | socket connect/disconnect | T |
| `addAIAssistantListener(name, l)` | `removeAIAssistantListener(name)` | AI assistant streaming | T |
| `addNotificationFeedListener(name, l)` | `removeNotificationFeedListener(name)` | in-app notification feed | T |

## Push

| Method | Signature | Notes | Src |
|---|---|---|---|
| `CometChatNotifications.registerPushToken` | `registerPushToken(pushToken: string, platform: PushPlatforms, providerId?: string): Promise<string>` | **the one the docs use.** Register **after** `login` resolves. Platform constant differs per OS — fetch it, do not guess | D |
| `CometChatNotifications.unregisterPushToken` | `unregisterPushToken(): Promise<string>` | on logout — skip it and the next user of the device gets the previous user's pushes | D |
| `markPushNotificationDelivered` | `markPushNotificationDelivered(...): Promise<…>` | delivery analytics; optional | T |
| `markPushNotificationClicked` | `markPushNotificationClicked(...): Promise<…>` | click-through analytics; optional | T |
| `registerTokenForPushNotification` | `registerTokenForPushNotification(token: string, settings?: {}): Promise<string>` | **an older, different signature that still exists and is NOT marked deprecated.** Two live ways to do one thing — prefer `registerPushToken`; flagged so the wrong one is not picked by accident | T |

## AI & feature gates

| Method | Signature | Notes | Src |
|---|---|---|---|
| `getConversationSummary` | `getConversationSummary(receiverId, receiverType): Promise<string>` | dashboard-gated | T |
| `getConversationStarter` | `getConversationStarter(receiverId, receiverType): Promise<Array<string>>` | dashboard-gated | T |
| `getSmartReplies` | `getSmartReplies(receiverId, receiverType): Promise<Object>` | dashboard-gated | T |
| `askBot` | `askBot(...): Promise<Object>` | AI bots | T |
| `isFeatureEnabled` | `isFeatureEnabled(feature: string): boolean` | check before offering a gated feature | T |
| `isAIFeatureEnabled` | `isAIFeatureEnabled(feature: string): boolean` | AI equivalent | T |
| `isExtensionEnabled` | `isExtensionEnabled(extensionId: string): boolean` | check before wiring a dashboard extension | T |
| `getExtensionDetails` | `getExtensionDetails(extensionId): Promise<Object>` | config for an enabled extension | T |

---

## Deliberately excluded — and why

Named here so "absent" reads as *out of scope*, never as *forgotten*:

| Excluded | Count | Why |
|---|---|---|
| calls (`initiateCall`, `acceptCall`, `endCall`, …) | 11 | different package; the `calls` skill owns them |
| internals (`getApiKey`, `connect`, `isInitialized`, …) | 11 | a chat integration has no reason to call them |
| unread-count scoped variants | 4 | same shape as `getUnreadMessageCount`; documented as a family |
| preferences / push-preferences / timezone | 8 | niche; reach them via the ladder |
| notification-feed item methods | 5 | narrow feature; `addNotificationFeedListener` is the entry point |
| `createUploadFileRequest` | 1 | internal upload plumbing — **not even a public export** (absent from `catalogs/rn-sdk-v4.json`); `sendMediaMessage` is the public path |
| `reportFeedEngagement` | 1 | notification-feed analytics; same cluster as above |

**Accounting: 127 of 127.** Every method in the SDK is either mapped above or excluded here with
a reason. Nothing is silently absent — that is the property that makes rung 2 of the ladder
trustworthy.

Anything above is still **in the catalog** — rung 2 confirms it exists, rung 3 finds its page.
