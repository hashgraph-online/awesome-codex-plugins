# Mini-recipes — specialized 10.3/10.4 modules

Registry rows: `10.4-W12`, `10.4-T03`, `10.4-S01`, `10.4-S02`, `10.4-S03`, `10.4-G01`, `10.4-G02`, `10.4-X01`, `10.4-X04`, `10.4-X05`, `10.4-X06`, `10.3-E02`, `10.3-E04`, `10.3-E05`, `10.3-E06`, `10.3-E07`, `10.3-E08`, `10.3-G03`, `10.3-G04`. Each entry follows the recipe format in
short form; the runnable code is `examples/python/recipes/mini_recipes.py` (offline; destructive and
rights-changing calls are dry-run) and the request sequence `examples/payloads/mini-recipes.json`.
Background and limits: `references/specialized-updates.md`. Run: `py -3 examples/python/recipes/mini_recipes.py`.
Evidence level for all: offline contract (no live Telegram call). TypeScript: reuse the same JSON
payloads with `examples/ts/tgkit.ts` `FakeTransport` / your SDK's raw call.

| # | Task (user words) | Feature | Requirements | Request / fixture | Handling and check | Mistake → fix | Adapt |
|---|---|---|---|---|---|---|---|
| M01 | “Greet newcomers privately, not with a public message per join” | `can_send_welcome_messages` (10.3) | admin bot; granting rights = dry-run | `examples/fixtures/chat_member_admin_welcome.json`; `promoteChatMember` plan | detect the right; ephemeral welcome to the newcomer (`m01_welcome_right`) | public welcome spam → ephemeral `receiver_user_id` | your welcome text, i18n |
| M02 | “Welcome people who came from our community” | `community_chat_joined` (10.3) | — | `message_community_chat_joined.json` | community name in an ephemeral welcome; 64-bit id (`m02`) | int32 ids → int64 | analytics hook |
| M03 | “Show the note that came with a gift” | `UniqueGiftInfo.text/entities/is_private` (10.3) | business connection | `message_unique_gift_info.json` | private notes only to the receiver (`m03`) | reposting a private note → keep it with the receiver | rendering |
| M04 | “Look up this collectible by its name” | `getUniqueGift` (10.4) | — | `getUniqueGift {"name": …}` | result + 400 "not found" as validation (`m04`) | retrying a 400 → show "not found" | caching |
| M05 | “Clean old regular gifts from the shop account” | `deleteBusinessAccountGift` (10.4) — **destructive** | `can_convert_gifts_to_stars`; regular, unlimited, not refunded | plan printed, call only with `execute=True` | preconditions + consequence text (`m05`) | deleting limited gifts / expecting Stars → refused / none paid | confirmation UI naming the gift |
| M06 | “Match our card to the user's share screen” | `share_theme`, `EmojiType`, `getChatShareThemeBackdrops` (10.4) | private chat / supergroup / channel | `get_chat_result_wallet_theme.json`, `get_chat_share_theme_backdrops_result.json` | resolve emoji + backdrop (`m06`) | ignoring custom emoji variant → handle the union | cache backdrops |
| M07 | “Create our partner bot as pizzaplace_ai” | `suggested_username` secondary suffixes (10.4) | creator has Premium | `request_managed_bot` button in payloads | validate suffix; read real username after creation (`m07`) | assuming the suggestion became the main username | naming policy |
| M08 | “Link our terms in the verification badge” | `custom_description_entities` (10.4) | verification organization | `verifyChat` in payloads | text_link only, ≤ 70 chars (`m08`) | bold/italic entities → rejected | your URL |
| M09 | “Don't thank people for paying when they used a free link” | `paid_messages_waived` (10.4) | business/private | `message_paid_messages_waived.json` | presence of `{}` (`m09`) | `if msg.paid_messages_waived:` is false for `{}` → test the key | copy |
| M10 | “Don't log card numbers; let users copy TON addresses” | `bank_card_number`, `ton_address` entities (10.4) | — | `message_entities_ton_bank.json` | mask by UTF-16 offsets; copy_text button (`m10`) | char offsets → UTF-16 | your logger |
| M11 | “SDK upgrade broke StoryAreaPosition imports” | rename → `AreaPosition` (10.4) | — | JSON unchanged | alias until upgrade (`m11`) | changing JSON keys → only the type name moved | delete the alias later |
| M12 | “Personal receipt image, editable” | ephemeral media upload, caption above, rich edit, rich send (10.3) | within the ephemeral rules | `editEphemeralMessage*` + `sendRichMessage` ephemeral in payloads | `m12`, plus 10.2 → 10.3 migration helper | top-level `receiver_user_id` (10.2) → `ephemeral_message_parameters` | multipart upload in your HTTP client |
| M13 | “Send the widget in our group” | `can_send_other_messages` covers widgets (10.4) | **test server** (groups) | permissions object | gate on the right (`m13_widget_permission`) | sending without the right → refused | text-card fallback |
| M14 | “Recognise a reply to our widget” | `Message.widget`, `ExternalReplyInfo.widget` (10.4) | — | `message_with_widget.json`, `message_reply_to_widget_external.json` | `m14`, recipe 06 | ignoring `external_reply` → read `widget.id` | routing |
