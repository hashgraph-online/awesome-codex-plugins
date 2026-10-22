# Data migration — Stream history → CometChat (write it; the user runs it)

CometChat supports two approaches (`/fundamentals/data-import-and-migration`):
- **Historical import:** bulk-load users, groups, members and messages before go-live. It uses the Data Import REST API, and this script does it.
- **Live migration:** both systems bridged during a gradual rollout. This needs CometChat's team, so if the app can't have a cut-over window, add the action item "contact CometChat sales for live migration".

Emit `scripts/cometchat-migration/` as its OWN tiny package, so it keeps working after Stream is removed from the app:
- `package.json`: `"type": "module"`. Its only dependency is the Stream server client `stream-chat`, pinned to the major the app's server used.
- `migrate.mjs`: Node ≥18, uses global `fetch` for CometChat.
- `id.mjs`: a copy of `toCometChatId()` from `concept-map.md`. Same logic as the app and server.
- `README.md`: how to run it.
- `.gitignore`: `node_modules/` and `export/`, so `npm install` and the exported user data never show up as changes or get committed.

The script reads its secrets from env (`STREAM_API_KEY`, `STREAM_API_SECRET`, `COMETCHAT_APP_ID`, `COMETCHAT_REGION`, `COMETCHAT_REST_API_KEY`), never from a file in the repo. **The agent runs it for the user** once they provide those credentials (SKILL.md step 8): a `--dry-run` first, then the import — always from env vars, never hardcoded into a repo file, and never committed. If the user declines to share credentials, leave running it as an action item instead.

## 1. Export from Stream (server client)
`const client = StreamChat.getInstance(STREAM_API_KEY, STREAM_API_SECRET)`. The method names come from Stream's server SDK. **Check each one against Stream's current docs while writing the script, and note any difference in the README.**

| Data | Call | Paging |
|---|---|---|
| Users | `client.queryUsers({ id: { $gt: lastId } }, { id: 1 }, { limit: 100 })` | keyset on `id` (offset paging is capped) |
| Channels + members | `client.queryChannels({}, { created_at: 1 }, { limit: 30, offset, state: true, watch: false, member_limit: 100 })` | offset; `channel.queryMembers({}, {}, { limit: 100, offset })` for big channels |
| Messages | `channel.query({ messages: { limit: 300, id_lt: oldestId } })` | walk backwards until empty |
| Bulk alternative | `client.exportChannels([{ type, id }, …])` → poll `client.getExportChannelStatus(taskId)` → download `result.url` | better for very large histories |

Back off on HTTP 429. Write each export to `export/*.jsonl` so a failed run can resume.

## 2. Transform
- **User:** `uid = toCometChatId(user.id)`, `name = user.name || user.id`, `avatar = user.image` (must be a URL), `metadata = { ...customFields, streamUserId: user.id }` (keep it under 5 KB), `createdAt = seconds(user.created_at)`.
- **Channel:**
  - Member-based with exactly 2 members (ID starts with `!members-`) → **no group**; its messages become user-to-user messages.
  - Otherwise: `guid = toCometChatId(channel.cid)`, `name = channel.data.name || channel.id`, `icon = channel.data.image`, `type` = `public` for livestream/open channels, `private` otherwise, `owner = toCometChatId(channel.data.created_by.id)`, `metadata = { streamCid: channel.cid, ...customFields }`, `tags = [channel.type]`.
- **Member:** the key is `${guid}_member_${uid}`. `owner` → `admin`, `channel_moderator` → `moderator`, else `participant`. `banned` → `isBanned: true`.
- **Message:**
  - `muid = message.id`, `sender = toCometChatId(message.user.id)`, `receiverType` + `receiver`, `sentAt = Math.floor(Date.parse(message.created_at) / 1000)`.
  - `regular`/`reply` with text only → `category:"message"`, `type:"text"`, `data.text`.
  - With attachments → one media message per attachment: `type` from the attachment (`image`, `video`, `audio`/`voiceRecording` → `audio`, `file`), `data.attachments = [{ url: asset_url || image_url, name: title, mimeType: mime_type, extension, size: file_size }]`, `data.text` = the caption. **CometChat stores the attachment URL by REFERENCE — it does not copy or re-host the file** (verified against the Data Import API), and Stream CDN URLs also expire. So re-host every attachment to your own / CometChat media storage **before decommissioning Stream**, or media breaks. List re-hosting as an action item.
  - `giphy`/custom attachments → `category:"custom"` with `data.customData` = the attachment.
  - `system` messages: import as `category:"message", type:"text"` from a system UID so "X joined / renamed" history survives (note the styling change); count them. `deleted` messages: skip.
  - Mentions → `<@uid:UID>` in the text + `mentionedUserDetails`.
- **Filter out messages CometChat will reject BEFORE sending — each one, left in a batch, aborts the whole request with HTTP 500 (`ERR_EXCEPTION`) after the good rows have already imported:**
  - **Older than retention (~6 months):** CometChat retains messages about **6 months** by default and the Data Import API rejects any message whose `sentAt` predates that window (`"Messages older than 6 months cannot be imported"`). This is a **destination limit on the CometChat side — it is the SAME 6 months whether the source is Stream, Sendbird or Twilio**, not a Stream property. Compute `cutoff = now − 6 months`, DROP older messages, count them, and add the action item: *"N messages predate CometChat's 6-month retention window and were not migrated — purchase Extended Storage (contact CometChat sales), then re-run to include them."* (`/fundamentals/data-import-and-migration`; retention: CometChat Help Center → Data Retention.)
  - **Empty text:** a `type:"text"` message whose `data.text` is empty/whitespace is rejected (`ERR_EMPTY_MESSAGE_TEXT`) — skip it. This also catches body-less `system` lines.
- **Seconds, not milliseconds:** every CometChat timestamp here is a 10-digit UNIX time.
- **Not carried by the import API:** thread parent links, quoted-message links, reactions, poll votes, pins, reminders, per-user read state beyond `readAt`/`deliveredAt`. Say so in the report.

## 3. Import into CometChat (Data Import API)
Base `https://${COMETCHAT_APP_ID}.api-${COMETCHAT_REGION}.cometchat.io/v3/data_import`, with headers `apikey: ${COMETCHAT_REST_API_KEY}` and `content-type: application/json`. Fetch each page for the full payload before writing that call:
- `/rest-api/data-import-apis/users/import-users`
- `/rest-api/data-import-apis/groups/import-groups`
- `/rest-api/data-import-apis/groups/import-group-members`
- `/rest-api/data-import-apis/messages/import-messages`

| Order | Endpoint | Body shape |
|---|---|---|
| 1 | `POST /data_import/users` | `{ "users": { "<uid>": { uid, name, avatar?, metadata?, createdAt? } } }` |
| 2 | `POST /data_import/groups` | `{ "groups": { "<guid>": { guid, name, type, owner, icon?, metadata?, tags?, createdAt? } } }` |
| 3 | `POST /data_import/members` | `{ "members": { "<guid>_member_<uid>": { memberId, guid, uid, scope?, isBanned?, joinedAt? } } }` |
| 4 | `POST /data_import/messages` | `{ "messages": { "<muid>": { muid, sender, receiverType, receiver, category, type, data, sentAt, deliveredAt?, readAt? } } }` |

- **Batching:** at most **50 entities per request** and **60 requests per minute**. Throttle to about one request per second, and retry `ERR_TOO_MANY_REQUESTS` with backoff.
- **Read PER-ROW results, not the HTTP status.** The response body reports `success` (true/false) per key under `data` — count those, not the status code. A request can even return **HTTP 500 (`ERR_EXCEPTION`) while having imported its rows**, so on any non-2xx do NOT assume nothing landed: re-run (idempotency makes that safe) and rely on the per-row / already-exists signal below.
- **Treat "already exists" as success, not failure.** On a re-run — or after a 500 that actually landed — rows come back as `ERR_UID_ALREADY_EXISTS` / `ERR_GUID_ALREADY_EXISTS` / `ERR_ALREADY_JOINED` / `ERR_IMPORT_MUID_ALREADY_EXISTS`. These mean the row is present. Log only genuine failures to `import-errors.jsonl` and carry on; never abort the whole run for one bad row.
- **Idempotency:** re-running with the same uid/guid/muid is safe (overwrite / already-exists).
- **Order matters:** users → groups → members → messages, oldest messages first.

Finish by printing counts: exported, imported, converted (system→text), skipped (deleted / beyond the 6-month retention window / empty), failed (with a pointer to the error file).

## README.md for the script (emit it)
1. Create a **REST API key** (full access) in the CometChat dashboard.
2. `cd scripts/cometchat-migration && npm install`, then export the five env vars.
3. Dry run: `node migrate.mjs --dry-run`. This exports and transforms, then prints counts without importing.
4. Import: `node migrate.mjs`.
5. Spot-check a few conversations in the dashboard, then point production at the new build.
6. Delete the export files (they hold user data), and delete this folder once the cut-over is done.
