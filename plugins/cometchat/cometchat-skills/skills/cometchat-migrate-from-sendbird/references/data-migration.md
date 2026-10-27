# Data migration — Sendbird history → CometChat (write it; the user runs it)

CometChat supports two approaches (`/fundamentals/data-import-and-migration`):
- **Historical import:** bulk-load users, groups, members and messages before go-live. It uses the Data Import REST API, and this script does it.
- **Live migration:** both systems bridged during a gradual rollout. This needs CometChat's team, so if the app can't have a cut-over window, add the action item "contact CometChat sales for live migration".

Emit `scripts/cometchat-migration/` with:
- `migrate.mjs`: Node ≥18, no dependencies, uses global `fetch`.
- `README.md`: how to run it.
- `id.mjs`: a copy of `toCometChatId()` from `concept-map.md`. It must be byte-identical in logic to the one the app and server use.
- `.gitignore`: `export/`, so the exported user data never shows up as a change or gets committed.

The script reads its secrets from env (`SENDBIRD_APP_ID`, `SENDBIRD_API_TOKEN`, `COMETCHAT_APP_ID`, `COMETCHAT_REGION`, `COMETCHAT_REST_API_KEY`), never from a file in the repo. **The agent runs it for the user** once they provide those credentials (SKILL.md step 8): a `--dry-run` first, then the import — always from env vars, never hardcoded into a repo file, and never committed. If the user declines to share credentials, leave running it as an action item instead.

## 1. Export from Sendbird (Platform API)
Base `https://api-${SENDBIRD_APP_ID}.sendbird.com/v3`, with header `Api-Token: ${SENDBIRD_API_TOKEN}`. These endpoints and their paging parameters are from Sendbird's Platform API. **Check each one against Sendbird's current Platform API reference while writing the script, and note any difference in the README.**

| Data | Endpoint | Paging |
|---|---|---|
| Users | `GET /users?limit=100` | `next` token → `&token=` |
| Group channels | `GET /group_channels?limit=100&show_empty=true&show_member=true` | `next` token |
| Channel members | `GET /group_channels/{channel_url}/members?limit=100` | `next` token |
| Messages | `GET /group_channels/{channel_url}/messages?message_ts=<ms>&prev_limit=0&next_limit=200&include=false&with_sorted_meta_array=true` | advance `message_ts` past the last `created_at` |
| Open channels (+ messages) | `GET /open_channels?limit=100`, `GET /open_channels/{channel_url}/messages?…` | same |

Honor Sendbird's rate limits (back off on HTTP 429). Write each export to `export/*.jsonl` so a failed run can resume without re-exporting.

## 2. Transform
- **User:** `uid = toCometChatId(user_id)`, `name = nickname || user_id`, `avatar = profile_url` (must be a URL), `metadata = { ...metadata, sendbirdUserId: user_id }`, `createdAt = seconds(created_at)` when present.
- **Channel:**
  - Distinct with exactly 2 members → **no group**; its messages become user-to-user messages.
  - Otherwise: `guid = toCometChatId(channel_url)`, `name = name || "Group"`, `icon = cover_url`, `type = is_public ? "public" : "private"`, `owner` = the creator's `uid` (else the first operator), `metadata = { sendbirdChannelUrl: channel_url, customType: custom_type, data }`, `tags = custom_type ? [custom_type] : []`.
- **Member:** the key is `${guid}_member_${uid}`. Operators get `scope: "admin"`, everyone else `"participant"`. Banned members get `isBanned: true`.
- **Message:**
  - `muid = String(message_id)`, `sender = toCometChatId(user.user_id)`, `receiverType` + `receiver` (the other member's uid for a 1:1 channel, else the guid), `sentAt = Math.floor(created_at / 1000)`.
  - `MESG` → `category:"message"`, `type:"text"`, `data.text = message`.
  - `FILE` → `type` from the MIME prefix (`image/` → `image`, `video/` → `video`, `audio/` → `audio`, else `file`), `data.attachments = [{ url, name, mimeType, extension, size }]`. **CometChat stores the attachment URL by REFERENCE — it does not copy or re-host the file** (verified against the Data Import API). So the file survives only while the source URL does: re-host every attachment to your own / CometChat media storage **before decommissioning Sendbird**, or images and files break. List re-hosting as an action item.
  - `ADMM` (admin messages, e.g. "X joined"): import as a `category:"message", type:"text"` message from a system/admin UID so the history reads the same (don't silently drop it); if the app rendered them specially, note it as a behavior change. Count them in the summary.
  - `custom_type` / `data` / `sorted_metaarray` → `data.metadata`.
  - Mentions → rewrite each mention in the text to `<@uid:UID>` and fill `mentionedUserDetails`.
- **Filter out messages CometChat will reject BEFORE sending — each one, left in a batch, aborts the whole request with HTTP 500 (`ERR_EXCEPTION`) after the good rows have already imported:**
  - **Older than retention (~6 months):** CometChat retains messages about **6 months** by default and the Data Import API rejects any message whose `sentAt` predates that window (`"Messages older than 6 months cannot be imported"`). This is a **destination limit** — it is the SAME for every source (Sendbird / Stream / Twilio) because it is enforced on the CometChat side, not the vendor's. Compute `cutoff = now − 6 months`, DROP older messages, count them, and add the action item: *"N messages predate CometChat's 6-month retention window and were not migrated — purchase Extended Storage (contact CometChat sales), then re-run to include them."* (`/fundamentals/data-import-and-migration`; retention: CometChat Help Center → Data Retention.)
  - **Empty text:** a `type:"text"` message whose `data.text` is empty/whitespace is rejected (`ERR_EMPTY_MESSAGE_TEXT`) — skip it. This also catches body-less `ADMM`/system lines.
- **Seconds, not milliseconds:** every CometChat timestamp here is a 10-digit UNIX time.
- **Not carried by the import API:** thread parent links, reactions, poll votes, pins, per-user read state beyond `readAt`/`deliveredAt`. Replies import as ordinary messages. Say so in the report.

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

Finish by printing counts: exported, imported, converted (admin→text), skipped (deleted / beyond the 6-month retention window / empty), failed (with a pointer to the error file).

## README.md for the script (emit it)
1. Create a **REST API key** (full access) in the CometChat dashboard.
2. Export the five env vars.
3. Dry run: `node scripts/cometchat-migration/migrate.mjs --dry-run`. This exports and transforms, then prints counts without importing.
4. Import: `node scripts/cometchat-migration/migrate.mjs`.
5. Spot-check a few conversations in the dashboard, then point production at the new build.
6. Delete the export files. They hold user data.
