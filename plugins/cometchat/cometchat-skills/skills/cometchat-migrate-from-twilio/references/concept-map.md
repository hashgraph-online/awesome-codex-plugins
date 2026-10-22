# Twilio Conversations → CometChat concept map

Maps **roles**, not code. Take every CometChat name/signature from the target family's skills + catalog + docs (`cometchat-<family>-core/references/docs-map.md`). Platforms differ (web `on*Click`, RN `on*Press`, native init shapes); never port a snippet across families. Twilio is headless, so the default is **client/SDK mode** — keep the app's UI, swap the data layer.

## IDs (do this first)
CometChat UIDs/GUIDs are alpha-dash (`a-z 0-9 - _`), ≤100, lowercased. Twilio `identity` and `uniqueName`/`sid` are not constrained the same way. Emit ONE deterministic helper (client + server + data script share it exactly):
```js
export function toCometChatId(id) {
  const raw = String(id);
  let out = raw.toLowerCase().replace(/[^a-z0-9_-]/g, "_");
  if (out !== raw || out.length > 100) {
    let h = 0; for (const c of raw) h = (Math.imul(31, h) + c.codePointAt(0)) >>> 0;
    out = `${out.slice(0, 90)}_${h.toString(36)}`;
  }
  return out;
}
```
Port literally to Swift/Kotlin/Dart when native. Twilio `identity` → CometChat `uid`; conversation `sid`/`uniqueName` → `guid`.

## Core concepts
| Twilio Conversations | CometChat (role) | Notes |
|---|---|---|
| Account SID + API Key/Secret + Conversations Service SID | App ID + Region (client) + REST API Key (server) | region `us`/`eu`/`in`; keep secrets server-side |
| `new Client(token)` / `Client.create(token)` + `stateChanged`→`initialized` | init (`initFromSettings`) then login (`loginWithAuthToken`) | init once before render; login before any data call |
| Access token (JWT, server-minted, `updateToken` on expiry) | CometChat **auth token** (server-minted; re-login on expiry) | `cometchat-security`; not the Auth Key |
| Conversation with 2 participants | a **user** conversation (1:1) | receiver = the other participant's uid |
| Conversation (3+), `friendlyName`/`uniqueName` | Group (`guid = toCometChatId(uniqueName || sid)`, name = friendlyName) | private vs public per your model |
| Participant (`identity`) | group member (uid) | `add(identity)` → add member; non-chat (SMS/WhatsApp) participants have no equivalent (feature-map) |
| `sendMessage(body)` / `MessageBuilder.addMedia` | send text / media message | media → `data.attachments` |
| `getMessages(...)` (paginator) | messages request builder | paging, not a local store |
| `attributes` (JSON on conversation/message/participant/user) | metadata | carry across |
| `client.on('messageAdded'|...)` / `conversation.on(...)` | CometChat listeners (added with an id, removed on unmount) | one place; remove on teardown |
| `typing()` / read horizon / unread count | typing + delivery/read receipts | separate CometChat calls/events |
| push registration id | the family's push skill | Notifications product |

## Behavioral differences (keep the UX identical)
- **Optimistic send:** if the app inserts a pending message on `sendMessage` and reconciles on the returned message/`messageAdded`, keep that: insert a local placeholder, replace it with CometChat's resolved message (roll back on reject). CometChat's `sendMessage` resolves with the sent message.
- **Pagination:** Twilio's message paginator → CometChat's `MessagesRequestBuilder` (`setLimit(n)`, `fetchPrevious`/`fetchNext`), one builder instance per conversation for the cursor; map scroll-to-load to it.
- **Listeners:** each Twilio `on(...)` becomes a CometChat listener with a unique id, removed on unmount/dispose — reuse the app's existing subscribe/unsubscribe points.
- **Connection state:** Twilio `connectionStateChanged` → CometChat connection listeners; keep the app's online/offline UI wired.
- **Client/SDK mode:** keep the app's components and screens; replace only the service/store/hook talking to Twilio, mapping CometChat objects into the app's existing view models at the boundary. The app should look and behave the same — only the data source changed. Fetch each CometChat method/shape from the SDK docs, never by analogy to the Twilio API.

## Server
| Twilio server piece | CometChat replacement |
|---|---|
| Access-token endpoint (`AccessToken` + `ConversationsGrant`, API Key/Secret + Service SID) | your endpoint: create user if missing → `POST /v3/users/{uid}/auth_tokens` (REST API Key, server env) — `cometchat-security` |
| Webhooks (`onMessageAdded`, scoped/global, `X-Twilio-Signature`) | CometChat webhooks (`/rest-api/management-apis/webhooks/overview`); drop the Twilio signature check |
| Conversations REST (create conversation/participant/message) | CometChat REST equivalents, or REMOVE + list |
| Env `TWILIO_API_KEY`/`TWILIO_API_SECRET`/`TWILIO_CONVERSATIONS_SERVICE_SID` | `COMETCHAT_APP_ID`/`REGION`/`REST_API_KEY` (placeholders + action item) |
