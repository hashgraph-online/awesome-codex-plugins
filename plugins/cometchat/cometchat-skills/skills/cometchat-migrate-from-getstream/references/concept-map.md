# Stream → CometChat concept map

This maps **roles**, not code. For every CometChat call, component and prop, take the exact name and signature from the target family's skill (`cometchat-<family>-core` / `-components` / `-features`), its catalog, and the docs (`-core/references/docs-map.md`). The platforms differ: web callbacks are `on*Click`, React Native's are `on*Press`, and Android/iOS/Flutter use their own init shapes. Never port a snippet from one family to another.

## IDs (do this first — everything else depends on it)
CometChat UIDs and GUIDs are **alpha-dash only** (`a-z`, `0-9`, `-`, `_`), **max 100 characters**, and **lowercased automatically** (`/articles/properties-and-constraints`). Stream user IDs may hold `@`/`.`, cids hold `:`, and member-based channel IDs start with `!members-`. Emit ONE deterministic helper per language the repo uses (client, server, and the data script share its logic exactly):

```js
// toCometChatId — the single source of truth for Stream ID → CometChat UID/GUID.
// Deterministic: the same input always yields the same ID, on every platform and in the data script.
// Channels: ALWAYS pass the full cid ("messaging:general"), never the bare id.
export function toCometChatId(id) {
  const raw = String(id);
  let out = raw.toLowerCase().replace(/[^a-z0-9_-]/g, "_");
  // Changed or too long → add a short stable hash of the ORIGINAL, so "A.b" and "a_b" never merge.
  if (out !== raw || out.length > 100) {
    let h = 0;
    for (const c of raw) h = (Math.imul(31, h) + c.codePointAt(0)) >>> 0;
    out = `${out.slice(0, 90)}_${h.toString(36)}`;
  }
  return out;
}
```

```dart
// lib/cometchat/ids.dart — the SAME rule as the JS helper (same 32-bit hash, same base-36 suffix); output-identical.
String toCometChatId(String id) {
  final raw = id;
  var out = raw.toLowerCase().replaceAll(RegExp(r'[^a-z0-9_-]'), '_');
  if (out != raw || out.length > 100) {
    var h = 0;
    for (final c in raw.runes) { h = ((31 * h) + c) & 0xFFFFFFFF; }
    out = '${out.substring(0, out.length > 90 ? 90 : out.length)}_${h.toRadixString(36)}';
  }
  return out;
}
```

The Dart port above is verbatim; port to Swift/Kotlin the same way: same steps, same 32-bit hash, same base-36 suffix. A user ID that is already valid passes through unchanged. Every cid gets a suffix (it contains `:`), and that's expected: the data script and the app compute the same one.

**Wire it into the CLIENT, not only the data script — this is the #1 Stream migration miss.** Stream user IDs often already *look* valid (`john`, `alice42`), so it is tempting to log in with the raw id and convert only inside the import script. Do NOT. The runtime login/user-creation and the data import must agree on every id, so route the current-user id (and every channel cid) through `toCometChatId()` at login/runtime too — **even when it is a no-op for an already-valid id.** Emit the helper ONCE in a shared client module (e.g. `src/cometchat/ids.ts`) that the login code imports, and copy that exact body verbatim into `scripts/cometchat-migration/id.mjs` (the script can't import app `src`). A `toCometChatId` that exists only in the data script is a **failed migration**: a real user whose Stream id wasn't alpha-dash would be imported under one UID and then logged in under a different one, landing on an empty account.

## Core concepts
| Stream | CometChat (role) | Notes |
|---|---|---|
| API key (client) + API secret (server) | App ID + Region (client), plus a REST API key (server only) | Region comes from the dashboard (`us`/`eu`/`in`). |
| `StreamChat.getInstance(key)` / `ChatClient.Builder` / `StreamChatClient` / `ChatClientConfig` / `useCreateChatClient` | the family's `initFromSettings` (UI Kit) or the Chat SDK's init | Per core skill. Init once, before login or render. |
| `connectUser(user, token)` / `tokenProvider` | the auth-token login, with a token from YOUR server (refetch when the session expires) | Production path. |
| `connectUser(user, client.devToken(id))` | the Auth Key login | Dev only. Action item: move to tokens. |
| `disconnectUser()` | logout | Also remove the listeners. |
| User (`id`, `name`, `image`, custom fields) | User (`uid` = `toCometChatId(id)`, name, avatar, metadata) | Users must EXIST before login. The server endpoint creates them; the data script imports the rest. |
| Member-based channel with 2 members (`!members-…`) | a **user** conversation (1:1) | Receiver = the other member's UID. |
| Channel with an ID (`messaging:general`, `team:…`) | Group (`guid` = `toCometChatId(cid)`) | Private membership → `private`. Open/livestream → `public`. |
| `queryChannels` / `ChannelList` filters + sort | the conversations list (UI Kit) or the conversations request builder (SDK) | Stream's filter DSL doesn't carry over. Keep the simple filters (type, membership); list the complex ones as a behavior change. |
| `channel.watch()` / `channel.query({ messages })` | the message list (UI Kit) or the messages request builder (SDK) | |
| Message (`text`, `attachments`, custom fields) | text message / media message / custom message + metadata | |
| `parent_id` / `quoted_message_id` | the parent message ID (thread) / quoted reply (feature row) | |
| `client.on(event)` / `channel.on(event)` | message / group / user / connection listeners | Add on mount, REMOVE on unmount/dispose. |
| Channel roles (`channel_moderator`, owner) | group scope `moderator` / `admin` | |
| `addDevice` | the family's push skill (Notifications product) | |

## UI component map (UI SDK mode)
| Stream UI (any platform) | CometChat UI Kit role | Where |
|---|---|---|
| `<Chat>` / `OverlayProvider` / `StreamChat(…)` wrapper | the kit's provider / init gate from the core | `-core` |
| `ChannelList` (`<ChannelList>`, `<stream-channel-list>`, `ChatChannelListVC`/`ChatChannelListView`, `ChannelListView`/`ChannelsScreen`, `StreamChannelListView`) | Conversations | `-components` |
| `Channel` + `Window` + `ChannelHeader` + `MessageList` + `MessageInput` (and platform twins: `ChatChannelVC`, `MessagesScreen`, `MessageListView` + `MessageComposerView`, `StreamMessageListView` + `StreamMessageInput`) | message header + message list + message composer | `-core` / `-components` |
| `Thread` / `ChatThreadVC` | the thread header + threaded message list | `-features` (`threaded-replies`) |
| `ChannelSearch` / `SearchBar` | Search | `-features` (`message-search`) |
| Channel info / members screens (usually app-built) | group details + group members | `-placement` (details panel) |

On React v7 these are `CometChatConversations`, `CometChatMessageHeader`, `CometChatMessageList`, `CometChatMessageComposer`, `CometChatThreadHeader`, `CometChatSearch`, `CometChatUsers`, `CometChatGroups` and `CometChatGroupMembers`. Other families: take the names from their `-components` skill.

**Custom Stream components:** a custom `Message`/`Attachment`/`ChannelPreview` component (passed via props or `ViewFactory`/`Components`) maps to the kit's view slots or a custom message type. Use the family's `-customization` skill (slots first, then custom message types). Keep the app's visual intent; don't copy Stream internals.

**Routing and navigation:** keep the app's routes. A param like `/chat/:channelId` becomes `toCometChatId(cid)`. Rebuild the cid from the type the app used, so deep links keep working after the data import.

**Styling:** delete Stream CSS imports and theme objects (`--str-chat__*` variables, `StreamChatTheme`, `ChatTheme`, `Appearance`). Re-apply the brand through `-customization`. Follow-the-OS theming is a core obligation (`RULES.md`).

## Behavioral differences to handle (client-mode gotchas)
Keeping the app's own UI means matching the vendor's runtime BEHAVIOR, not just method names. The app should look and behave the same after migration — only the data source changed. Watch these:
- **Optimistic send / local echo.** Stream's `send` channel.sendMessage optimistically inserts the message into channel.state, then reconciles on ack; the message appears instantly, then updates on confirm. CometChat's `CometChat.sendMessage()` resolves with the sent message on success and rejects on failure — there's no separate pending object. To keep the instant-echo UX, insert a local placeholder yourself on submit and replace it with the resolved message (or roll it back on reject). Don't drop the echo and make sends feel laggy.
- **Pagination.** Stream pages with channel.query({messages:{limit,id_lt}}) / watch. CometChat uses `new CometChat.MessagesRequestBuilder().setUID/setGUID(...).setLimit(n).build()` and `.fetchPrevious()` (older) / `.fetchNext()` (newer), holding ONE builder instance per conversation for the cursor. Map the app's scroll-to-load to the same builder; a fresh builder per page re-fetches from the top.
- **Listener lifecycle.** Each client.on / channel.on becomes a CometChat listener added with a unique ID and REMOVED on unmount/dispose. Reuse the app's existing subscribe/unsubscribe points; a listener added on every render without removal duplicates messages.
- **Delivered/read + typing.** These are separate `CometChat` calls and listener events, not fields on the message object. Wire them where the app read the vendor's equivalents.
- **Fetch every method + shape from the SDK docs** (`/sdk/<platform>/*`) and verify against the catalog — never port the vendor's signature by analogy.

## Client mode (the app draws its own UI)
Keep every component and screen. Replace only the data layer (the service/store/hook that talks to the Stream client): each method calls the CometChat Chat SDK equivalent, and each `on(...)` subscription becomes a listener. Keep the app's own model types. Map CometChat objects into them at the boundary. **Every CometChat SDK method, its signature, its listener class and its parameter shapes come from the live docs — never from memory and never from the vendor's API by analogy.** For each data-layer call, open the family's SDK docs (`cometchat-<family>-core/references/docs-map.md` → SDK section, or the `-sdk` skill where one ships), fetch the exact method (e.g. `CometChat.getConversationList` via `new CometChat.ConversationsRequestBuilder()`, `CometChat.sendMessage`, `CometChat.addMessageListener`), and verify it against the family catalog before you emit it. A `<vendor>`-method-to-CometChat-method guess that you did not fetch is a defect, even if it compiles. Look up the method list in the family's SDK docs (docs-map → SDK section; React Native: `cometchat-react-native-sdk/references/method-map.md`; Android: `cometchat-android-v5-sdk`).

## Server
| Stream server piece | CometChat replacement |
|---|---|
| Token endpoint (`serverClient.createToken(userId[, exp])`, `upsertUser`) | Your endpoint: create the user if missing (`POST /v3/users`), then `POST /v3/users/{uid}/auth_tokens`. Uses the **REST API key**, server env only (`/rest-api/auth-tokens`). |
| Webhook receiver (`verifyWebhook`, `x-signature`) | A CometChat webhook receiver with the events mapped (`/rest-api/management-apis/webhooks/overview`). Delete the Stream signature check. |
| User sync on sign-up / profile update | CometChat REST create/update user, with the same `toCometChatId()` |
| Before-send hook, custom commands, SQS/SNS | REMOVE + list (feature map) |
| Env: `STREAM_API_KEY`, `STREAM_API_SECRET` | `COMETCHAT_APP_ID`, `COMETCHAT_REGION`, `COMETCHAT_REST_API_KEY` (placeholders + an action item) |
