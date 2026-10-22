# app-surface — the production floor for an own-UI Android chat app (Chat SDK v5)

The SDK ships **no UI**, so "build chat with the SDK" has no visual default — without a floor, output
degrades to bare bubbles. This file is that floor: the deterministic minimum for a generic prompt.
Encoded as `contracts.sdk-android-v5.json` → `sdk-chat-surface`; symbols verified against
`catalogs/sdk-android-v5.json`. Exact signatures: `docs-map.md`.

## 1. Shell & sizing
- The chat screen **fills the window**: `Modifier.fillMaxSize()` (Compose) / `match_parent` (Views).
- Three regions: header (who you're talking to) · **scrolling message list** · composer pinned to the
  bottom. The LIST scrolls internally (`LazyColumn` / `RecyclerView`) — never nest it in another
  scrollable, never let the page itself grow.
- **Insets + IME**: `enableEdgeToEdge()` + `imePadding()`/`navigationBarsPadding()` (Compose) or
  `windowSoftInputMode="adjustResize"` (Views), so the composer stays visible while typing and nothing
  sits under the system bars.
- New messages: keep the list pinned to the newest message when the user is already at the bottom;
  don't yank the scroll position when they've scrolled up.

## 2. Design system — reuse, don't invent
Use the app's existing theme (Material3 `MaterialTheme` / your XML styles / your token set). If the app
is brand new, establish a small token layer (colors, spacing, radii, type) and build primitives from it.
**Never** ad-hoc inline colors and one-off dimensions scattered per screen.

## 3. State model (own it explicitly)
Per screen, a single state holder (ViewModel) exposing an immutable UI state:
`{ items, isLoading, isPaginating, error, hasMore }` plus the input/composer state. Rules:
- Never mutate a list in place from a callback thread — reduce into new state on the main dispatcher.
- Keep SDK types at the edge; map to your own UI models so the UI doesn't break on SDK changes.
- One listener registration per screen, tied to the screen's lifecycle (see §6).

## 4. Lists + pagination (every list, every time)
Build the request once, then page:
```kotlin
val request = MessagesRequest.MessagesRequestBuilder()
    .setUID(uid)          // or .setGUID(guid)
    .setLimit(30)
    .build()
// initial load + "load older" → request.fetchPrevious(callback)
```
Same builder discipline for `ConversationsRequest`, `UsersRequest`, `GroupsRequest`,
`GroupMembersRequest`. Rules:
- **Never** one unbounded fetch. Keep the built request instance for subsequent pages.
- **Search** via the builder's search-keyword setter — a server-side query, not a client-side filter
  over the page you happen to have. **Two traps, both real:**
  - **Casing differs per builder.** `UsersRequestBuilder.setSearchKeyword` / `ConversationsRequestBuilder.setSearchKeyword` are lowercase, but `GroupsRequestBuilder.`**`setSearchKeyWord`** has a **capital W** (an SDK inconsistency). Using `setSearchKeyword` on GroupsRequest fails to compile (`Unresolved reference`).
  - **Conversations search is PLAN-GATED.** `ConversationsRequestBuilder.setSearchKeyword` (and `setUnread`) require the **"Conversation & Advanced Search"** feature — **Advanced/Custom plan + a dashboard toggle** (Chats → Settings → General Configuration). Off-plan it **silently returns the full, unfiltered list** (no error) — the app ships a search box that looks broken. Users search and Groups search are NOT plan-gated (work on any plan). On a lower plan, gate the conversations-search UI behind a "requires Advanced plan" hint or fall back to a labelled local filter — never present an unfiltered result as a search result.
- **Scope to the product** (`setConversationType("user")`/`"group"`) rather than filtering after the fact.
- Guard against double-loading (`isPaginating`) and stop at the empty page (`hasMore = false`).

## 5. Optimistic mutations (what makes it feel native)
Send / edit / delete / react must update the UI **immediately**, then reconcile:
1. Insert a local item in a `SENDING` state (key it by the message's `muid` so you can match the ack).
2. Call the SDK.
3. `onSuccess` → replace the temp item with the server message (`SENT`).
4. `onError` → mark it `FAILED` with a retry affordance and surface `CometChatException.message`.
Never block the UI waiting for a round-trip; never leave a failed item looking sent.

## 6. Realtime + listener lifecycle
Register **one** listener per screen with a stable unique id and remove it on teardown:
- Compose: `DisposableEffect(Unit) { add…; onDispose { remove… } }`
- Views/ViewModel: register in `onCreate`/`init`, remove in `onDestroy`/`onCleared`
Cover: `addMessageListener` (incoming text/media), `addUserListener` (presence), `addGroupListener`
(membership), `addConnectionListener` (offline/online banner). De-duplicate against optimistic items
(match on message id / muid) so an echoed own-message doesn't appear twice. **Never poll.**
- **Presence has a config prerequisite.** `addUserListener`'s `onUserOnline`/`onUserOffline` only fire if the settings asset opts in via `chatSDK.presenceSubscription` (`ALL_USERS`/`FRIENDS`/`ROLES`; absent ⇒ no presence — see SKILL.md Prerequisites). The seeded `getUser().status` / list `status` field is a snapshot and works without it; the realtime transition does not. Wiring the header/users presence surface **without** the subscription ships a header stuck on "offline".

## 7. Required surfaces (a generic "build chat" delivers ALL of these)
| Surface | Minimum |
|---|---|
| Conversations | list + last message + unread + searchable + delete-conversation |
| Users / Groups | both lists, searchable, tap → open chat (join group if needed) |
| Message screen | header (name/presence/typing) · paginated history · composer (text + media) |
| Message actions | reply-in-thread · react · edit · delete (edit/delete gated to own messages) · report |
| Thread | `setParentMessageId(...)`-scoped list + its own composer |
| User detail | profile + block/unblock |
| Group detail | members + add/kick/ban + scope change + leave, role-gated |
| Receipts/typing | `markAsRead` on view; `startTyping`/`endTyping` wired to the input |

## 8. Loading / empty / error — on every surface
- **Loading**: skeleton or spinner sized like the content (no layout jump when it resolves).
- **Empty**: a real message ("No conversations yet") — never a blank screen.
- **Error**: readable text from `CometChatException.message` + a retry action. Every `CallbackListener`
  implements `onError`; an empty `onError {}` is a defect, and connection loss must be visible.

## 9. Anti-patterns (auto-fail this floor)
Bare bubbles with no lists/actions · unbounded fetches · client-side "search" · polling for new messages ·
listeners never removed · blank screens on empty/error · swallowed exceptions · main-thread blocking ·
credentials in source · hand-rolled UI when the user would have accepted the UI Kit (offer it first).
