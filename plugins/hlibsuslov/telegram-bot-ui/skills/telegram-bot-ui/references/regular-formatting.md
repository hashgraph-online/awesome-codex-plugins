# Regular formatting — complete reference

> Exhaustive map of **every regular (non-Rich) Telegram text-formatting feature**:
> the two `parse_mode`s, all message entities, nesting rules, custom emoji,
> captions, and the message-level presentation controls that affect how text
> renders (link previews, silent, protected, spoilers, effects).
> **Last verified: 2026-07-15.** Confirm the tag/entity set for the project's Bot
> API version against `#formatting-options`; see `official-sources.md`.
>
> Custom emoji have their own reference — eligibility (Fragment / owner
> Premium), obtaining real IDs, Unicode fallbacks, and the button field
> `icon_custom_emoji_id`: `custom-emoji.md`.

There are three ways to style a **regular** message: `parse_mode="HTML"`,
`parse_mode="MarkdownV2"`, or an explicit `entities` array. Pick **one** per
message (don't combine `parse_mode` and `entities` on the same field). For Rich
Messages instead, see `telegram-capabilities.md`.

## 1. HTML (`parse_mode=HTML`)

Supported tags (whitelist — nothing else is allowed):

| Style | Tag(s) |
|---|---|
| Bold | `<b>`, `<strong>` |
| Italic | `<i>`, `<em>` |
| Underline | `<u>`, `<ins>` |
| Strikethrough | `<s>`, `<strike>`, `<del>` |
| Spoiler | `<tg-spoiler>`, `<span class="tg-spoiler">` |
| Inline link | `<a href="https://example.com/">text</a>` |
| User mention | `<a href="tg://user?id=123456789">name</a>` |
| Custom emoji | `<tg-emoji emoji-id="5368324170671202286">👍</tg-emoji>` |
| Inline code | `<code>code</code>` |
| Code block | `<pre>block</pre>` |
| Code block + language | `<pre><code class="language-python">…</code></pre>` |
| Block quote | `<blockquote>quote</blockquote>` |
| Expandable quote | `<blockquote expandable>quote</blockquote>` |

Escaping (text and attribute values): replace `&`→`&amp;`, `<`→`&lt;`,
`>`→`&gt;`. Escape **inside** `<code>`/`<pre>` too. Only the attributes shown
above are allowed; strip/escape any other tag or attribute. Validate every
`href` scheme (`security-and-escaping.md`).

## 2. MarkdownV2 (`parse_mode=MarkdownV2`)

```
*bold*
_italic_
__underline__
~strikethrough~
||spoiler||
[inline URL](https://example.com/)
[user mention](tg://user?id=123456789)
![👍](tg://emoji?id=5368324170671202286)      <- custom emoji
`inline code`
​```python
code block with language
​```
>Block quotation line 1
>Block quotation line 2
**>Expandable quotation line 1
>Expandable quotation last line||               <- starts with **> , ends with ||
```

Combining example (nest by wrapping):
`*bold _italic bold ~italic bold strike ||spoiler||~ __underline italic___ bold*`

Escaping — in ordinary text, prefix each of these with `\`:
`` _ * [ ] ( ) ~ ` > # + - = | { } . ! ``. **Inside** `` `code` ``/```` ``` ````
blocks escape only `` ` `` and `\`. **Inside** a link/emoji `(...)` target escape
only `)` and `\`. MarkdownV2 is easy to break with user input — prefer HTML or
entities for untrusted text unless MarkdownV2 is mandated.

*(Legacy `parse_mode=Markdown` is deprecated and cannot express underline,
spoiler, blockquote, custom emoji, or nested styles — do not introduce it.)*

## 3. MessageEntity (explicit `entities` array)

No `parse_mode`; you supply `type` + `offset` + `length` (**UTF-16 code units**)
against the exact text. Full type list:

- Formatting: `bold`, `italic`, `underline`, `strikethrough`, `spoiler`,
  `blockquote`, `expandable_blockquote`, `code`, `pre` (with optional
  `language`), `text_link` (with `url`), `text_mention` (with `user`),
  `custom_emoji` (with `custom_emoji_id`).
- Auto-detected/semantic: `mention` (`@user`), `hashtag`, `cashtag` (`$USD`),
  `bot_command`, `url`, `email`, `phone_number`.

Use entities when you need exact offsets, want no parse_mode, or must interleave
untrusted text safely. A 4-byte emoji is **length 2** (surrogate pair). Entities
must not exceed text bounds.

## 4. Nesting rules

- `bold`, `italic`, `underline`, `strikethrough`, `spoiler` can contain and be
  contained by any entity **except** `code`/`pre`.
- `code` and `pre` cannot contain other entities.
- `blockquote` and `expandable_blockquote` **cannot be nested** inside each other.
- Other entities (url, mention, etc.) can't contain each other.

## 5. Captions

Media captions (`sendPhoto`/`sendVideo`/`sendDocument`/`sendAudio`/
`sendAnimation`/`sendVoice`/media groups) support the **same** formatting via
`caption` + `parse_mode`/`caption_entities`. Caption limit is smaller than text
(1024 vs 4096 chars — verify). `show_caption_above_media=True` renders the
caption above the media. For albums, only certain items carry a caption — verify
current behavior.

## 6. Presentation controls that affect rendering

These aren't "styling" but they change how the formatted message appears and are
essential for notifications/broadcasts:

| Field | Effect |
|---|---|
| `link_preview_options` | `is_disabled` (no preview); `url` (which link to preview); `prefer_small_media`; `show_above_text` (preview above the text) |
| `disable_notification` | silent delivery (no sound) |
| `protect_content` | recipients can't forward/save |
| `has_spoiler` | media sent as spoiler |
| `show_caption_above_media` | caption position |
| `message_effect_id` | animated effect (private chats) |
| `reply_parameters` | reply/quote context (can quote a substring with its own entities) |
| `reply_markup` | inline/reply keyboards attached to the message |
| `message_thread_id` | forum topic / direct-message topic |
| `business_connection_id` | send on behalf of a business account |

Keep `link_preview_options` in mind whenever a message contains URLs — an
unwanted large preview is the most common "why does my post look wrong" cause.

## 7. Quick chooser

- Light styling, project uses HTML → **HTML**.
- Project standardizes on it / mandated → **MarkdownV2** (mind escaping).
- Exact offsets / untrusted text / no parse_mode → **entities**.
- Headings/tables/task-lists/math/docs → **Rich** (`telegram-capabilities.md`).

See `format-selection.md` for the full decision order and `security-and-escaping.md`
for the per-format escaping rules.
