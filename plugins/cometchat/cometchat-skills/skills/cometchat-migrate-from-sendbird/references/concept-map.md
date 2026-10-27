# Sendbird → CometChat concept map

This maps **roles**, not code. For every CometChat call, component and prop, take the exact name and signature from the target family's skill (`cometchat-<family>-core` / `-components` / `-features`), its catalog, and the docs (`-core/references/docs-map.md`). The platforms differ: web callbacks are `on*Click`, React Native's are `on*Press`, and Android/iOS/Flutter use their own init shapes. Never port a snippet from one family to another.

## IDs (do this first — everything else depends on it)
CometChat UIDs and GUIDs are **alpha-dash only** (`a-z`, `0-9`, `-`, `_`), **max 100 characters**, and **lowercased automatically** (`/articles/properties-and-constraints`). Sendbird user IDs and channel URLs are not. Emit ONE deterministic helper per language the repo uses (client, server, and the data script share its logic exactly):

```js
// toCometChatId — the single source of truth for Sendbird ID → CometChat UID/GUID.
// Deterministic: the same input always yields the same ID, on every platform and in the data script.
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

The Dart port above is verbatim; port to Swift/Kotlin the same way: same steps, same 32-bit hash, same base-36 suffix. An ID that is already valid passes through unchanged, so most apps see no difference.

## Core concepts
| Sendbird | CometChat (role) | Notes |
|---|---|---|
| Application ID | App ID + Region | Region comes from the dashboard (`us`/`eu`/`in`). Both go in the family's env/settings file. |
| `SendbirdChat.init` / `new SendBird()` / `SendbirdUIKit.init` / `SendbirdUI.initialize` | the family's `initFromSettings` (UI Kit) or the Chat SDK's init | Per core skill. Init once, before any login or render. |
| `connect(userId, accessToken/sessionToken)` | the auth-token login, with a token from YOUR server | Production path. |
| `connect(userId)` with no token | the Auth Key login | Dev only (`RULES.md` → Credentials). Action item: move to tokens. |
| `SessionHandler` (token refresh) | re-login with a fresh auth token when the SDK reports an expired or invalid session | Fetch the token lifecycle docs. |
| `disconnect()` | logout | Call on sign-out, and clean up listeners. |
| User (`userId`, `nickname`, `profileUrl`, `metadata`) | User (`uid` = `toCometChatId(userId)`, name, avatar, metadata) | Users must EXIST before login. The server endpoint creates them on first login; the data script imports the rest. |
| GroupChannel, **distinct, exactly 2 members** | a **user** conversation (1:1) | Receiver = the other member's UID. Never a 2-person group. |
| GroupChannel (other) / supergroup | Group (`guid` = `toCometChatId(channel_url)`) | Private → `private`. `isPublic` → `public`. A password flow → `password`. |
| OpenChannel | a **public** Group | Users join it. There's no "enter/exit"-only presence. |
| Channel list query / `GroupChannelCollection` | the conversations list (UI Kit) or the conversations request builder (SDK) | |
| `PreviousMessageListQuery` / `MessageCollection` | the message list (UI Kit) or the messages request builder (SDK) | Paging, not a local cache. |
| UserMessage / FileMessage / AdminMessage | text message / media message / (admin → an action or a custom message; usually dropped) | |
| `customType`, `data`, `metaArrays` | custom message type + message metadata | |
| `parentMessageId` (thread) | the parent message ID on the reply | Threads feature row. |
| `GroupChannelHandler`, `ConnectionHandler`, `UserEventHandler` | message / group / user / connection listeners | Add on mount, REMOVE on unmount/dispose (by listener ID). |
| Operators | group scope `admin` / `moderator` | |
| Push token registration | the family's push skill (Notifications product) | |

## UIKit screen map (UIKit mode)
| Sendbird UIKit screen (any platform) | CometChat UI Kit role | Where |
|---|---|---|
| `App` / all-in-one chat | the production-ready core surface (conversation list ↔ message pane) | `-core` golden path |
| Channel list (`GroupChannelList`, `ChannelList`, `SBUGroupChannelListViewController`, `ChannelListFragment`/`ChannelListScreen`, `createGroupChannelListFragment`, `SBUGroupChannelListScreen`) | Conversations | `-components` |
| Channel (`GroupChannel`, `Channel`, `SBUGroupChannelViewController`, `ChannelFragment`/`ChannelScreen`, `createGroupChannelFragment`, `SBUGroupChannelScreen`) | message header + message list + message composer | `-core` / `-components` |
| Channel settings / members | group details + group members | `-placement` (details panel) / `-components` |
| Create channel | the users picker + group creation | `-components` |
| Thread | the thread header + threaded message list | `-features` (`threaded-replies`) |
| Message search | Search | `-features` (`message-search`) |
| Open channel screen | the message pane on a public group | `-core` |
| Edit profile | no kit screen → keep the app's UI and call the SDK's update-current-user method | docs |

On React v7 these are `CometChatConversations`, `CometChatMessageHeader`, `CometChatMessageList`, `CometChatMessageComposer`, `CometChatThreadHeader`, `CometChatSearch`, `CometChatUsers`, `CometChatGroups` and `CometChatGroupMembers`. Other families: take the names from their `-components` skill.

**Routing and navigation:** keep the app's routes and URLs. Swap only what renders inside them. A Sendbird route param like `/chat/:channelUrl` becomes `toCometChatId(channelUrl)`, so deep links and bookmarks keep working after the data import.

**Styling:** delete the Sendbird CSS import and any Sendbird theme providers. Re-apply the brand through the family's `-customization` skill (colors, fonts, dark mode). Follow-the-OS theming is a core obligation (`RULES.md`).

## Behavioral differences to handle (sdk-mode gotchas)
Keeping the app's own UI means matching the vendor's runtime BEHAVIOR, not just method names. The app should look and behave the same after migration — only the data source changed. Watch these:
- **Optimistic send / local echo.** Sendbird's `send` GroupChannel.sendUserMessage returns a pending message immediately (local echo), then a second callback confirms it; the message appears instantly, then updates on confirm. CometChat's `CometChat.sendMessage()` resolves with the sent message on success and rejects on failure — there's no separate pending object. To keep the instant-echo UX, insert a local placeholder yourself on submit and replace it with the resolved message (or roll it back on reject). Don't drop the echo and make sends feel laggy.
- **Pagination.** Sendbird pages with PreviousMessageListQuery / MessageCollection. CometChat uses `new CometChat.MessagesRequestBuilder().setUID/setGUID(...).setLimit(n).build()` and `.fetchPrevious()` (older) / `.fetchNext()` (newer), holding ONE builder instance per conversation for the cursor. Map the app's scroll-to-load to the same builder; a fresh builder per page re-fetches from the top.
- **Listener lifecycle.** Each GroupChannelHandler becomes a CometChat listener added with a unique ID and REMOVED on unmount/dispose. Reuse the app's existing subscribe/unsubscribe points; a listener added on every render without removal duplicates messages.
- **Delivered/read + typing.** These are separate `CometChat` calls and listener events, not fields on the message object. Wire them where the app read the vendor's equivalents.
- **Fetch every method + shape from the SDK docs** (`/sdk/<platform>/*`) and verify against the catalog — never port the vendor's signature by analogy.

## SDK mode (the app draws its own UI)
Keep every component and screen. Replace only the data layer (the service/store/hook that talks to Sendbird): each method calls the CometChat Chat SDK equivalent, and each handler becomes a listener. Keep the app's own model types. Map CometChat objects into them at the boundary, so the UI code doesn't change. **Every CometChat SDK method, its signature, its listener class and its parameter shapes come from the live docs — never from memory and never from the vendor's API by analogy.** For each data-layer call, open the family's SDK docs (`cometchat-<family>-core/references/docs-map.md` → SDK section, or the `-sdk` skill where one ships), fetch the exact method (e.g. `CometChat.getConversationList` via `new CometChat.ConversationsRequestBuilder()`, `CometChat.sendMessage`, `CometChat.addMessageListener`), and verify it against the family catalog before you emit it. A `<vendor>`-method-to-CometChat-method guess that you did not fetch is a defect, even if it compiles. Look up the method list in the family's SDK docs (docs-map → SDK section; React Native: `cometchat-react-native-sdk/references/method-map.md`; Android: `cometchat-android-v5-sdk`).

## Server
| Sendbird server piece | CometChat replacement |
|---|---|
| Session/access-token endpoint (`POST /v3/users/{id}/token`, or `issue_access_token` on user create) | Your endpoint: create the user if missing (`POST /v3/users`), then `POST /v3/users/{uid}/auth_tokens`. Uses the **REST API key**, server env only, never shipped to clients (`/rest-api/auth-tokens`). |
| Webhook receiver (`x-sendbird-signature`) | A CometChat webhook receiver with the events mapped (`/rest-api/management-apis/webhooks/overview`). Delete the Sendbird signature check. |
| User sync on sign-up (Platform API create/update user) | CometChat REST create/update user (docs), called with the same `toCometChatId()` |
| Moderation / admin scripts | CometChat REST equivalents, or REMOVE + list them |
| Env: `SENDBIRD_API_TOKEN` | `COMETCHAT_APP_ID`, `COMETCHAT_REGION`, `COMETCHAT_REST_API_KEY` (placeholders + an action item) |
