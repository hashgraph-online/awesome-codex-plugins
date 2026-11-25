---
summary: "Custom emoji on buttons and in text: eligibility (Fragment usernames or owner Premium), silent failure, getting real IDs, unicode fallback, checklist; read before using any custom_emoji_id."
verified: "2026-11-15"
bot_api: "10.4"
---

# Custom emoji — on buttons and in text

## Contents

- [Eligibility — check this first](#eligibility--check-this-first)
- [Eligibility per send context](#eligibility-per-send-context)
- [Other surfaces that accept custom emoji (API)](#other-surfaces-that-accept-custom-emoji-api)
- [An ineligible bot fails silently — verify by reading the message back](#an-ineligible-bot-fails-silently--verify-by-reading-the-message-back)
- [Automation](#automation)
- [Getting a real `custom_emoji_id` — never invent one](#getting-a-real-custom_emoji_id--never-invent-one)
- [Buttons](#buttons)
- [In message text](#in-message-text)
- [Unicode emoji vs custom emoji — choosing](#unicode-emoji-vs-custom-emoji--choosing)
- [Checklist](#checklist)

Two different mechanisms, one eligibility rule:

| Where | Mechanism | Since |
|---|---|---|
| **On a button** | `icon_custom_emoji_id` on `KeyboardButton` / `InlineKeyboardButton` | Bot API **9.4** (2026-02-09) |
| **In message text** | `custom_emoji` `MessageEntity`, `<tg-emoji emoji-id="…">😀</tg-emoji>` (HTML), `![😀](tg://emoji?id=…)` (MarkdownV2) | Bot API **6.2** (2022-08-12) |

## Eligibility — check this first

Official Bot API wording for `icon_custom_emoji_id` (identical on both button
classes): *"Unique identifier of the custom emoji shown before the text of the
button. Can only be used by bots that purchased additional usernames on Fragment
or in the messages directly sent by the bot to private, group and supergroup
chats if the owner of the bot has a Telegram Premium subscription."*

So a bot may use custom emoji when **either**:

1. it **purchased additional usernames on Fragment** (the long-standing 6.2-era
   route; the API text sets no chat-type restriction on it); **or**
2. the **bot owner has Telegram Premium** *and* the message is sent **directly
   by the bot** to a **private, group, or supergroup** chat — the relaxation
   introduced by Bot API 9.4.

Consequences to state out loud when you propose custom emoji:

- **Channel posts are not covered by the Premium route.** Route 2 lists private,
  group, and supergroup chats only. For channels, the Fragment route applies.
- **It depends on the *bot owner's* Premium, not the viewer's.** If the owner
  lets Premium lapse, the calls that rely on route 2 start failing — design the
  fallback now, not later.
- **"Directly sent by the bot"** excludes messages sent on behalf of someone
  else (e.g. business-account sending) — this skill's conservative reading; the
  table below lists each send path.
- Before recommending this feature, **ask which route the project qualifies
  for.** If neither, use Unicode emoji and say why.

## Eligibility per send context

Checked 2026-11-15 against Bot API 10.4. The same sentence governs button icons
(`KeyboardButton`, `InlineKeyboardButton`) and custom emoji entities (MarkdownV2 and HTML
sections); the 9.4 changelog adds that button icons work "if they are able to use custom
emoji in the message". `Eligibility.route(SendContext(...))` in
`examples/python/tgkit/icons.py` encodes this table.

| Send context | Fragment usernames | Owner Premium only | Basis |
|---|---|---|---|
| Private / group / supergroup, sent by the bot (incl. edits of its own messages, ephemeral replies) | yes | yes | **API** |
| Channel post | yes | **no** | **API** (channels not listed) |
| Business send (`business_connection_id`, on behalf of a user) | yes | no | conservative reading of "directly sent by the bot" |
| Inline result / `inline_message_id` edit (sent by the user via the bot) | yes | no | conservative reading |
| Checklists (`sendChecklist` is business-only) | yes | no | **API** method scope + reading above |

Decide once per message: the view from `IconSystem.for_context(ctx)` is either all icons or
none, so a message never mixes custom icons and Unicode stand-ins.

## Other surfaces that accept custom emoji (API)

- **Rich Messages (10.1+):** `RichTextCustomEmoji` = `{"type": "custom_emoji",
  "custom_emoji_id", "alternative_text"}` in any RichText field; rich HTML accepts
  `<tg-emoji emoji-id="…">👍</tg-emoji>` and `<img src="tg://emoji?id=…" alt="👍"/>`; rich
  Markdown `![👍](tg://emoji?id=…)`. `RichMessageButton.text` may contain only plain text,
  `RichTextCustomEmoji` and `RichTextDateTime`. Alternative text counts toward the 32768
  character limit. The rich section repeats no eligibility sentence; apply the rule above.
  `<tg-thinking>` blocks: the docs point to `https://t.me/addemoji/AIActions` (**Official**).
- **Captions:** `caption_entities` / `parse_mode` like text.
- **Polls:** question and option entities — "only custom emoji entities are allowed".
- **Checklists:** title/task entities allow `custom_emoji` (business sends only).
- **Gift texts:** entities other than bold, italic, underline, strikethrough, spoiler,
  custom_emoji and date_time are ignored.
- **Quotes:** custom_emoji entities are kept in quotes and `quote_rich_texts`.
- **Not:** legacy `Markdown`; inside `code`, `pre` or links (nesting rules).

## An ineligible bot fails silently — verify by reading the message back

**Result of a live test against the Bot API (2026-08-05)** on a bot with no Fragment
username whose owner had no active Premium: Telegram **returned `ok: true` and stripped the
custom emoji**, leaving only the alternative characters. No error, through every input path:

| How the emoji were sent | What came back |
|---|---|
| `parse_mode=HTML` with `<tg-emoji emoji-id="…">😀</tg-emoji>` | `entities: []` |
| explicit `custom_emoji` `MessageEntity` (correct UTF-16 offset) | `entities: []` |
| `sendRichMessage` with `RichTextCustomEmoji` in a table cell and a paragraph | the cell came back as the plain string `"😀"` |

After Premium was activated on the owner's account, the same code returned the entities
intact on all three paths — the cause was entitlement and nothing else.

Consequences:

- **A `try/except` proves nothing.** There is no exception, so an error-keyed fallback never
  fires and the bot ships plain emoji while the logs look clean.
- **The only reliable check is the round trip:** every send method returns the `Message`;
  compare it with what you sent. `IconSystem.send` does this (`silently_stripped(params,
  message)`): when the request carried custom emoji and the full echo has none, it flips the
  shared kill switch and logs once, so later messages go out with clean Unicode fallbacks
  instead of half-decorated text. The message already delivered is left as is (it reads fine
  with the alternative characters).
- **Premium-only profile fields are not proof of entitlement** (`emoji_status_custom_emoji_id`,
  `background_custom_emoji_id` survive an expired subscription). Only the round trip settles it.
- **When custom emoji "don't work", ask first:** *does the account that created this bot have
  Telegram Premium active right now, or does the bot own a Fragment username?* If neither,
  stop debugging markup; ship the Unicode fallback and say why.

### Runtime errors and the kill switch

Errors still happen on other paths. Telegram does not document the error text for a
refused custom emoji; `IconSystem.send` treats a **400 on a request that carried custom emoji**
whose description matches `CUSTOM_EMOJI_ERROR_HINTS` as a refusal: kill switch, one log line,
**one** retry with every custom emoji stripped (Unicode fallbacks on buttons). A second
failure is raised; unrelated 400s are not retried. Later messages go out plain at the first
attempt until `reset_kill_switch()` after the owner confirms the route is back (recipe 74).

## Automation

`scripts/emoji_packs.py` resolves packs to slot maps, suggests packs, verifies stored ids
(≤ 200 per call), prints the capture steps, and applies or strips custom emoji in payloads.
The workflow an agent follows is in `emoji-packs.md`; posts in `emoji-in-posts.md`.

## Getting a real `custom_emoji_id` — never invent one

The value is the ID of one specific custom emoji sticker. It is **not** a
`file_id`, not a sticker-pack name, not a `t.me/addemoji/...` link, and not a
Unicode character. IDs cannot be derived, guessed, or "looked up by name". A
fabricated ID is a bug that ships silently.

Three legitimate sources:

1. **From a message that already contains the emoji** — `MessageEntity` of type
   `custom_emoji` carries `custom_emoji_id`. Have the owner send the emoji to
   the bot once and log the entity. This is the easiest path for most projects.
2. **From a sticker set** — `getStickerSet` returns `Sticker` objects; each
   custom-emoji sticker exposes `custom_emoji_id` (and `emoji`, the Unicode
   fallback character).
3. **Verifying IDs you already have** — `getCustomEmojiStickers` takes
   `custom_emoji_ids` (**at most 200 per call**) and returns the corresponding
   `Sticker` objects. Use it to confirm an ID resolves and to read its `emoji`.

**Agent protocol when the ID is unknown:** implement the UI with the field
plumbed through but left unset (or read from config), then ask the user for the
ID *and* show them the capture snippet above. Do not block the whole redesign on
it, and do not fill in a placeholder that looks real.

Store IDs in configuration/constants with a comment naming the pack and the
Unicode fallback — not scattered as magic strings.

```python
# config: emoji pack "MyBotIcons", fallback ✅
FINISH_ICON_ID = os.environ.get("TG_ICON_FINISH")  # verified via getCustomEmojiStickers
```

## Buttons

```json
{
  "text": "Finish the test",
  "icon_custom_emoji_id": "5368324170671202286",
  "style": "success",
  "callback_data": "finish_test"
}
```

The icon renders **before** the text. Presentation only — it does not count as
the button's action field (`buttons-and-styles.md`).

Rules:

- **The label must stand alone.** Unlike text entities, a button icon has no
  alternative-emoji field. If the client cannot show the icon, the user sees
  only `text` — so never encode meaning in the icon (`✏️` + empty label is a
  broken button).
- **Icon a set, not a single button.** One icon on one button in an otherwise
  bare keyboard looks like a rendering bug. Icon a whole coherent group, or
  none.
- **Don't mix** custom emoji icons with Unicode emoji pasted into `text` on the
  same keyboard — pick one convention per bot and record it.
- **Keep icons out of destructive confirmation buttons** unless the icon is
  unmistakably a warning; a friendly icon undercuts a `danger` action.
- If the field is set but the bot is not eligible, expect Telegram to reject the
  request — handle it as a validation error and fall back to a plain button
  (`errors-and-fallbacks.md`).

## In message text

HTML: `<tg-emoji emoji-id="5368324170671202286">👍</tg-emoji>`
MarkdownV2: `![👍](tg://emoji?id=5368324170671202286)`
Entities: `MessageEntity` with `type: "custom_emoji"` and `custom_emoji_id`.

Official rule: *"A valid emoji must be provided as an alternative value for the
custom emoji. The emoji will be shown instead of the custom emoji in places
where a custom emoji cannot be displayed (e.g., system notifications) or if the
message is forwarded by a non-premium user. It is recommended to use the emoji
from the `emoji` field of the custom emoji sticker."*

So: **always supply the Unicode fallback**, and take it from the sticker's own
`emoji` field (via `getStickerSet` / `getCustomEmojiStickers`) rather than
picking one that "looks close". Note that MarkdownV2 requires `)` and `\` inside
the `(...)` part to be escaped, and that `parse_mode: Markdown` (legacy) cannot
express custom emoji at all — use MarkdownV2 or HTML.

More on entity mechanics: `regular-formatting.md`.

## Unicode emoji vs custom emoji — choosing

| Situation | Choose |
|---|---|
| Bot has no Fragment usernames and owner has no Premium | Unicode |
| Message goes to a channel and there are no Fragment usernames | Unicode |
| A branded icon set that must look the same everywhere | Custom (with fallbacks) |
| Status markers in dense lists (✅/⏳/❌) | Unicode — universally rendered |
| One-off decoration | Neither; usually cut it |

Whatever you choose, keep the **budget low**: emoji are punctuation for the eye,
not paragraph markers. `microcopy-and-labels.md` has the per-screen limits.

## Checklist

- [ ] Confirmed which eligibility route the bot qualifies for (Fragment /
      owner Premium / neither) — and stated it in the report.
- [ ] Every `custom_emoji_id` came from an entity, `getStickerSet`, or
      `getCustomEmojiStickers` — none invented.
- [ ] Text usages carry a valid Unicode fallback taken from the sticker's own
      `emoji` field.
- [ ] Buttons remain understandable with the icon missing.
- [ ] IDs live in config with a comment, not inline magic strings.
- [ ] Behaviour when the bot loses eligibility is defined and logged.
