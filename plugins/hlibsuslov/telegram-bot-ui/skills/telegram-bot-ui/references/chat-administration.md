# Chat administration and member updates

Bans, restrictions, promotions, permissions, invite links, join requests (incl. the
10.1 join-request queries), member tags, and the `my_chat_member` / `chat_member`
updates that tell the bot what changed. Channel posting and broadcasting belong to
`channels-and-broadcasting.md`; topics to `topics-and-contexts.md`. Checked against
Bot API 10.4 on **2026-11-15** (https://core.telegram.org/bots/api#chatmember and the
methods below). Every JSON block passes `scripts/validate_payload.py`.

Labels: **[API]** spec; **[Heuristic]** this skill's advice.

## The member model

`ChatMember` is one of (discriminator `status`) **[API]**:

| `status` | Type | Notes |
|---|---|---|
| `creator` | `ChatMemberOwner` | `is_anonymous`, `custom_title` |
| `administrator` | `ChatMemberAdministrator` | all `ChatAdministratorRights` + `can_be_edited` |
| `member` | `ChatMemberMember` | `until_date` for subscription members, `tag` (9.5) |
| `restricted` | `ChatMemberRestricted` | every `ChatPermissions` flag explicit, `is_member`, `until_date` (0 = forever) |
| `left` | `ChatMemberLeft` | |
| `kicked` | `ChatMemberBanned` | `until_date` (0 = forever) |

Read with `getChatMember`, `getChatAdministrators` (`return_bots: true` since 10.0
also lists other bot admins), `getChatMemberCount`.

## Member updates

- **[API]** `my_chat_member` — the **bot's** status changed: added to a group, promoted,
  removed, or (private chats) blocked/unblocked. Always delivered (no admin rights
  needed, part of the default set).
- **[API]** `chat_member` — **anyone's** status changed. Requires the bot to be an
  **administrator** and `"chat_member"` listed **explicitly** in `allowed_updates`
  (`updates-and-delivery.md#allowed_updates-is-sticky`).
- **[API]** `ChatMemberUpdated` carries `chat`, `from` (who made the change), `date`,
  `old_chat_member`, `new_chat_member`, and optionally `invite_link`,
  `via_join_request`, `via_chat_folder_invite_link`.
- **[Heuristic]** Derive the event from the **pair** of statuses, not from one:
  `left/kicked → member` = joined; `member → left` = left; `* → kicked` = banned;
  `member → administrator` = promoted; `restricted(is_member) → restricted(!is_member)` =
  left while restricted. Service messages (`new_chat_members`, `left_chat_member`) are
  not reliable in large groups — prefer `chat_member`.

```json
{"update_id": 900000501, "chat_member": {
  "chat": {"id": -1001234567890, "type": "supergroup", "title": "Foodies of Kyiv"},
  "from": {"id": 333333333, "is_bot": false, "first_name": "Admin"},
  "date": 1763191000,
  "old_chat_member": {"status": "left", "user": {"id": 222222222, "is_bot": false, "first_name": "Taras"}},
  "new_chat_member": {"status": "member", "user": {"id": 222222222, "is_bot": false, "first_name": "Taras"}},
  "invite_link": {"invite_link": "https://t.me/+AbCdEf", "creator": {"id": 333333333, "is_bot": false, "first_name": "Admin"},
                  "creates_join_request": false, "is_primary": false, "is_revoked": false, "name": "Spring promo"}
}}
```

## Rights the bot needs

- **[API]** Every moderation method needs the bot to be an **administrator** with the
  matching right: bans/restrictions → `can_restrict_members`; promotion →
  `can_promote_members` (and only a subset of its own rights can be granted);
  invite links and join requests → `can_invite_users`; pins → `can_pin_messages`
  (channels: `can_edit_messages`); deleting others' messages → `can_delete_messages`;
  member tags → `can_manage_tags` (9.5); welcome messages → `can_send_welcome_messages`
  (10.3; `specialized-updates.md#welcome-messages-right`).
- **[API]** `setMyDefaultAdministratorRights(rights, for_channels)` sets the rights
  suggested when users add the bot as admin; `getMyDefaultAdministratorRights` reads
  them. Request the minimum. **[Heuristic]**
- **[API]** `KeyboardButtonRequestChat` / `request_chat` can ask the user to pick a chat
  with `user_administrator_rights` / `bot_administrator_rights` so the bot is added
  with the right rights in one step (`reply-keyboards.md`).

## Moderation

```json
{"method": "restrictChatMember", "params": {
  "chat_id": -1001234567890, "user_id": 222222222,
  "permissions": {"can_send_messages": true, "can_send_photos": false, "can_send_videos": false,
                  "can_send_other_messages": false, "can_add_web_page_previews": false},
  "use_independent_chat_permissions": true,
  "until_date": 1763277400
}}
```

```json
{"method": "banChatMember", "params": {"chat_id": -1001234567890, "user_id": 222222222, "until_date": 0, "revoke_messages": false}}
```

- **[API]** `until_date` < 30 s or > 366 days from now = **forever** (both ban and
  restrict). `restrictChatMember` is supergroups only; "pass True for all
  permissions" lifts restrictions. `banChatMember` in supergroups/channels also
  prevents returning via invite links until `unbanChatMember`.
- **[API]** `use_independent_chat_permissions: false` (default) makes
  `can_send_other_messages` / `can_add_web_page_previews` imply
  `can_send_messages` etc. Pass `true` to set flags exactly as given.
- **[API]** `ChatPermissions` defaults: `can_react_to_messages` defaults to
  `can_send_messages` (10.0); `can_edit_tag` and `can_manage_topics` default to
  `can_pin_messages`. `can_send_other_messages` now also covers widgets (10.4).
- `unbanChatMember(only_if_banned: true)` — without it, unbanning a current member
  **removes** them from the chat. **[API]**
- `banChatSenderChat` / `unbanChatSenderChat` ban a channel identity posting in a
  group. **[API]**

Moderation is visible to the whole chat and hard to undo socially. In tooling,
dry-run by default, log who/why, and confirm with a human admin for bans.
**[Heuristic]**

## Promotion

```json
{"method": "promoteChatMember", "params": {
  "chat_id": -1001234567890, "user_id": 222222222,
  "can_delete_messages": true, "can_restrict_members": false, "can_pin_messages": true, "can_manage_topics": true
}}
```

- **[API]** Pass `false` for all rights to demote. `setChatAdministratorCustomTitle`
  sets a title (0-16 chars, no emoji). Rights flagged "for channels only" / "for supergroups
  only" are ignored elsewhere.

## Invite links and join requests

- **[API]** `createChatInviteLink(name 0-32, expire_date, member_limit 1-99999,
  creates_join_request)` — `member_limit` and `creates_join_request` are mutually
  exclusive. `editChatInviteLink`, `revokeChatInviteLink`, `exportChatInviteLink`
  (primary link; revokes the previous primary one).
- **[API]** `createChatSubscriptionInviteLink(subscription_period = 2592000,
  subscription_price 1-10000)` — paid channel membership in Stars
  (`payments-and-stars.md`).
- **[API]** `chat_join_request` (needs `can_invite_users`) → `approveChatJoinRequest` /
  `declineChatJoinRequest`. `ChatJoinRequest.user_chat_id` lets the bot message the
  applicant privately for **5 minutes**, until the request is processed and unless
  another admin contacted the user.
- **[API]** **Join-request queries (10.1)**: a bot with
  `supports_join_request_queries` (in `getMe`: `User` before 10.5, `BotFullInfo` since; set with
  `setMySettings`) can be assigned (as the chat's "guard bot",
  `ChatFullInfo.guard_bot`) to process join requests. The request then carries
  `query_id`, and the bot **must react within 10 seconds**: answer with `answerChatJoinRequestQuery(result = "approve" | "decline" |
  "queue")` — `queue` leaves the decision to human admins — or first show a Mini App
  with `sendChatJoinRequestWebApp(chat_join_request_query_id, web_app_url)` and
  resolve afterwards.

```json
{"method": "answerChatJoinRequestQuery", "params": {"chat_join_request_query_id": "jrq-7781", "result": "queue"}}
```

```json
{"method": "sendChatJoinRequestWebApp", "params": {"chat_join_request_query_id": "jrq-7781", "web_app_url": "https://example.com/verify?lang=uk"}}
```

## Tags (9.5) and chat settings

```json
{"method": "setChatMemberTag", "params": {"chat_id": -1001234567890, "user_id": 222222222, "tag": "Mentor"}}
```

- **[API]** Tags: regular members only, 0-16 characters, **no emoji**; needs
  `can_manage_tags`. `Message.sender_tag` shows the tag on incoming messages.
- **[API]** Chat settings: `setChatTitle`, `setChatDescription`, `setChatPhoto`,
  `deleteChatPhoto`, `setChatPermissions` (default permissions for everyone),
  `setChatStickerSet`, `pinChatMessage` / `unpinChatMessage` / `unpinAllChatMessages`,
  `leaveChat`.

## State to keep

Per chat: the bot's own `ChatMemberAdministrator` rights (refresh on every
`my_chat_member`), migration id (`migrate_to_chat_id` when a group becomes a
supergroup), and your moderation log. Never cache other members' rights for long —
re-read with `getChatMember` before acting on them. **[Heuristic]**

## What users see

- Bans/restrictions/promotions appear in the admin log and often as service messages;
  restrictions show the user a disabled input field with the reason. Keep the bot's
  own message about the action short and factual, in the chat's language, with the
  duration. **[Heuristic]**

## Common mistakes

| Mistake | Fix |
|---|---|
| Expecting `chat_member` without listing it / without admin | admin + explicit `allowed_updates` |
| `until_date: 60` meaning "60 seconds" | it is a Unix timestamp; `now + 60` |
| `unbanChatMember` on a member | `only_if_banned: true` |
| Restrict with partial flags, others silently implied | `use_independent_chat_permissions: true` |
| Promoting with rights the bot lacks | grant only a subset of its own rights |
| Keying data by the old group id after migration | follow `migrate_to_chat_id` |

## Error handling

- 400 "not enough rights" / 403 "bot was kicked": refresh the bot's status
  (`getChatMember(chat_id, bot_id)`), tell an admin which right is missing, stop
  retrying. **[Heuristic]** (texts vary; branch on `error_code`)
- 400 with `parameters.migrate_to_chat_id`: update the stored id and retry once. **[API]**
