# Data migration — Twilio Conversations history → CometChat (write it; the user runs it)

CometChat supports historical import (bulk, this script) and live migration (bridged, contact sales) — `/fundamentals/data-import-and-migration`. Default here = **hard switch** in a maintenance window; for zero-downtime, add the "contact CometChat sales for live migration" action item.

Emit `scripts/cometchat-migration/` as its own tiny package (keeps working after Twilio is removed):
- `package.json` (`"type":"module"`), dependency: the `twilio` server SDK pinned to the app's major.
- `migrate.mjs` (Node ≥18, global `fetch` for CometChat), `id.mjs` (a copy of `toCometChatId`), `README.md`.
- `.gitignore`: `node_modules/` and `export/`, so `npm install` and the exported user data never show up as changes or get committed.
Secrets from env (`TWILIO_ACCOUNT_SID`, `TWILIO_API_KEY`, `TWILIO_API_SECRET`, `TWILIO_CONVERSATIONS_SERVICE_SID`, `COMETCHAT_APP_ID`, `COMETCHAT_REGION`, `COMETCHAT_REST_API_KEY`), never a repo file. **The agent runs it for the user** once they provide those credentials (SKILL.md step 8): a `--dry-run` first, then the import — always from env vars, never hardcoded or committed. If the user declines to share credentials, leave running it as an action item instead.

## 1. Export from Twilio (Conversations REST)
Use the `twilio` server SDK against the Conversations Service. **Check method names against Twilio's current REST docs while writing, note diffs in the README.**
| Data | Call | Paging |
|---|---|---|
| Users | `client.conversations.v1.users.list({limit})` | SDK auto-pages |
| Conversations | `client.conversations.v1.services(SERVICE_SID).conversations.list({limit})` | SDK auto-pages |
| Participants | `…conversations(sid).participants.list()` | per conversation |
| Messages | `…conversations(sid).messages.list({order:'asc', limit})` | per conversation, oldest→newest |
| Media | resolve each message's media SID → temporary content URL (Media Content Service) | per media |
Back off on 429. Write each export to `export/*.jsonl` so a failed run resumes.

## 2. Transform
- **User:** `uid = toCometChatId(identity)`, `name = friendlyName || identity`, `avatar` from attributes if present, `metadata = { ...attributes, twilioIdentity: identity }`, `createdAt = seconds(dateCreated)`.
- **Conversation:**
  - exactly 2 participants → **no group**; messages become user-to-user.
  - else: `guid = toCometChatId(uniqueName || sid)`, `name = friendlyName || sid`, `type` per your model (default `private`), `owner` = the creator/first participant uid, `metadata = { twilioSid: sid, ...attributes }`.
- **Member:** key `${guid}_member_${uid}`, scope `participant` (elevate any admin you track), `joinedAt = seconds(dateCreated)`.
- **Message:**
  - `muid = message.sid`, `sender = toCometChatId(author)`, `receiverType`+`receiver`, `sentAt = Math.floor(Date.parse(dateCreated)/1000)`.
  - text → `category:"message"`, `type:"text"`, `data.text = body`.
  - media → one media message per media: `type` from `contentType` (`image`/`video`/`audio`/`file`), `data.attachments=[{url, name:filename, mimeType:contentType, size}]`. Twilio temporary URLs EXPIRE — re-host to your own/CometChat storage (action item).
  - `attributes` → `data.metadata`.
- **Seconds, not milliseconds** everywhere. **Not carried by the import API:** reactions, threads, read horizons beyond `readAt`/`deliveredAt`, typing — say so in the report.

## 3. Import into CometChat (Data Import API)
Base `https://${COMETCHAT_APP_ID}.api-${COMETCHAT_REGION}.cometchat.io/v3/data_import`, headers `apikey`, `content-type: application/json`. Fetch each page for the full payload:
`/rest-api/data-import-apis/users/import-users` · `/groups/import-groups` · `/groups/import-group-members` · `/messages/import-messages`.
| Order | Endpoint | Body |
|---|---|---|
| 1 | `/data_import/users` | `{ "users": { "<uid>": { uid, name, avatar?, metadata?, createdAt? } } }` |
| 2 | `/data_import/groups` | `{ "groups": { "<guid>": { guid, name, type, owner, metadata?, createdAt? } } }` |
| 3 | `/data_import/members` | `{ "members": { "<guid>_member_<uid>": { memberId, guid, uid, scope?, joinedAt? } } }` |
| 4 | `/data_import/messages` | `{ "messages": { "<muid>": { muid, sender, receiverType, receiver, category, type, data, sentAt } } }` |
Batch **≤50 entities/request**, **≤60 requests/min** (throttle ~1/s, retry `ERR_TOO_MANY_REQUESTS`). Per-entity `success`; log failures to `import-errors.jsonl` and continue. Idempotent on re-run. Order: users → groups → members → messages, oldest first. Print counts (exported, imported, skipped, failed).

## README.md (emit it)
1. Create a full-access REST API key in the CometChat dashboard.
2. `cd scripts/cometchat-migration && npm install`; export the env vars.
3. `node migrate.mjs --dry-run` (export + transform + counts, no import).
4. `node migrate.mjs`.
5. Spot-check in the dashboard; re-host media if Twilio URLs expired; delete `export/` (user data) and this folder after cut-over.
