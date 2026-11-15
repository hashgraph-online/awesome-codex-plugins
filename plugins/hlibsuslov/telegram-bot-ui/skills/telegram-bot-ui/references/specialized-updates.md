# Specialized 10.3/10.4 modules (on demand)

> Verified 2026-11-12 against the changelog and each object/method page. Runnable examples:
> `examples/python/recipes/mini_recipes.py` (offline; destructive calls dry-run) and
> [mini-recipes](../recipes/mini-recipes.md). Read only the section the task needs.

## Welcome messages right

10.3: `can_send_welcome_messages` in `ChatAdministratorRights`, `ChatMemberAdministrator` and
`promoteChatMember` — "manage chat welcome messages or directly send them in the case of bots".
Detect it from `my_chat_member`; send the welcome **only to the newcomer** (ephemeral with
`receiver_user_id`, allowed for administrator bots) instead of a public message per join.
Granting rights is a configuration change: dry-run by default. *Unverified:* the API page does not
describe a separate welcome-message method; the recipe uses the documented admin ephemeral path.

## Community joins

10.3: `Message.community_chat_joined` → `CommunityChatJoined{community: Community{id, name}}`.
Community ids exceed 32 bits (store as 64-bit). Use: a tailored welcome ("from *Foodies of Kyiv*"),
analytics. Shown to everyone? It's a service message in the chat; your reply can be ephemeral.

## Gift text and privacy

10.3: `UniqueGiftInfo.text`, `entities`, `is_private`. With `is_private`, the sender and text are
for the **receiver only** — never repost them publicly; in business chats answer the receiver.

## getUniqueGift

10.4: `getUniqueGift(name)` → `UniqueGift`. Unknown name → 400 (validation): say "gift not found",
don't retry.

## deleteBusinessAccountGift

10.4, **destructive**: deletes a *regular* gift of a managed business account **without receiving
Stars**. Needs business right `can_convert_gifts_to_stars`; refused for limited gifts
(`Gift.total_count` present) and refunded ones. Irreversible. Example prints the plan
(`execute=False` default); run only after explicit confirmation naming the gift.

## Chat share themes

10.4: `ChatFullInfo.share_theme` = `ChatShareThemeEmoji{emojis: EmojiType[0..6], background_backdrop_id?}`
or `ChatShareThemeUniqueGift{gift}`. `EmojiType` = `EmojiTypeEmoji{emoji}` | `EmojiTypeCustomEmoji{custom_emoji_id}`.
Resolve backdrops with `getChatShareThemeBackdrops()` → `{backdrops: [{id, name, colors}]}` (cache it).
Use: echo the user's theme in a profile card/widget; absent = default theme.

## Managed bot usernames

10.4: `KeyboardButtonRequestManagedBot.suggested_username` may end with `agent`, `ai`, `app`,
`game` or `gay` if the creating user has Premium — it becomes a **secondary** username (≤ 2 owned
bots) and a regular `…bot` username is still assigned. Read the created bot's username from
`managed_bot` / `managed_bot_created`; don't assume your suggestion was used.

## Verification descriptions

10.4: `verifyUser` / `verifyChat` accept `custom_description_parse_mode` /
`custom_description_entities` — **only `text_link`** entities; description 0–70 characters; must be
empty if the organization may not set custom descriptions. Validate before calling.

## Paid messages waived

10.4: `Message.paid_messages_waived` = `PaidMessagesWaived` (currently **empty object**). Test the
key's presence (`{}` is falsy in Python). Meaning: the sender used a link that waives paid
messages — not a payment; don't thank them for paying.

## Bank card and TON entities

10.4: `MessageEntity` types `bank_card_number` and `ton_address`. Mask card numbers in logs and
analytics; never echo them back in groups. Offsets are UTF-16. See `wallet-and-ton.md`.

## Renamed: AreaPosition

10.4 renamed `StoryAreaPosition` → `AreaPosition` (now also for TON wallet card stickers). JSON is
unchanged; only SDK type names move. Before: `from sdk import StoryAreaPosition`; after:
`AreaPosition` — alias the old name until the SDK upgrade, then delete the alias.

## Ephemeral media and caption edits

10.3: `editEphemeralMessageMedia` accepts new uploads (multipart `attach://name`);
`editEphemeralMessageCaption.show_caption_above_media`; `editEphemeralMessageText.rich_message`;
`sendRichMessage.ephemeral_message_parameters`. See `ephemeral-and-personal.md`.

## Widget permission in groups

10.4: `ChatPermissions.can_send_other_messages` / `ChatMemberRestricted` now also cover widgets
(groups: test server). Check before `sendWidget` in a group; fall back to a text card.
