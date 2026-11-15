# Telegram message capabilities

> **Last verified against official docs: 2026-11-12** (Bot API 10.4, 9 Nov 2026). All rich
> limits are now official ("Rich Message Limits"). See `official-sources.md`.

This is a compact map, not a copy of the docs. When the task depends on an exact
field, open the official page for that object/method and confirm.

## Two mechanisms, kept separate

| | Regular Messages | Rich Messages |
|---|---|---|
| Sent with | `sendMessage`, `sendPhoto`, … + `parse_mode`/`entities` | `sendRichMessage`, `sendRichMessageDraft` |
| Styling | `parse_mode` = `HTML` / `MarkdownV2`, or `entities[]` | `markdown` **or** `html` **or** `blocks` (exactly one) |
| Model | flat text + inline entities | document tree of typed blocks |
| Text limit | 4096 chars (caption 1024) | up to 32,768 UTF-8 chars |
| Best for | notifications, prompts, short replies | reports, AI answers, docs, tables, math |

Rich Messages are an **addition**, not a replacement. Do not migrate short/regular
messages just because Rich exists.

## Bot API version history (relevant to formatting)

- **10.0 — 2026-05-08:** no Rich Messages (Guest Mode, chats, polls, business).
- **10.1 — 2026-06-11:** introduced Rich Messages. Added `RichMessage`,
  `RichText` + 23 `RichText*` classes, `RichBlock` + `RichBlock*` classes,
  `InputRichMessage`, `InputRichMessageContent`, `sendRichMessage`,
  `sendRichMessageDraft`, `editMessageText` `rich_message` parameter, and the
  `rich_message` field on `Message`.
- **10.2 — 2026-07-14:** added `InputRichMessageMedia` + `media` field on
  `InputRichMessage`; `blocks` field on `InputRichMessage`; the input block
  classes `InputRichBlock*` (Paragraph, SectionHeading, Preformatted, Footer,
  Divider, MathematicalExpression, Anchor, List, ListItem, BlockQuotation,
  PullQuotation, Collage, Slideshow, Table, Details, Map, Animation, Audio,
  Photo, Video, VoiceNote, Thinking); `InputMediaVoiceNote`.

Always confirm the **latest** version in the changelog before starting.

## Object model (high level)

- **`RichMessage`** — a received rich formatted message (read side); appears as
  `Message.rich_message`.
- **`RichBlock`** / **`RichText`** — the parsed block/inline tree Telegram returns.
- **`InputRichMessage`** — what a bot sends. Carries **exactly one** of:
  - `markdown` — a Rich Markdown string;
  - `html` — a Rich HTML string;
  - `blocks` — an array of explicit `InputRichBlock*` objects.
  Plus `media` (array of `InputRichMessageMedia`) to bind media referenced from
  markdown/html, and standard send fields (chat/business/reply/markup). Confirm
  the exact optional-field list in the official object before use.
- **`InputRichMessageContent`** — an `InputMessageContent` variant for inline /
  guest / Web App query results.
- **`InputRichMessageMedia`** — declares a media item (by file_id, `tg://…?id=`
  reference, HTTP(S) URL, or upload) that markdown/html/blocks refer to.

## Send / edit methods

- **`sendRichMessage`** — send a complete rich message.
- **`sendRichMessageDraft`** — stream a partial/updating rich message (see
  `streaming-and-editing.md`). Uses a stable non-zero `draft_id`.
- **`editMessageText` + `rich_message`** — replace a message's rich content.

## Capability matrix (feature × format)

`RegMD` = MarkdownV2, `RegHTML` = regular HTML, `RMd` = Rich Markdown,
`RHTML` = Rich HTML, `Blk` = explicit `InputRichBlock*`. ✅ supported · ➖ n/a.

| Feature | Regular | RMd | RHTML | Blk | Notes |
|---|:--:|:--:|:--:|:--:|---|
| Bold / italic / underline / strike | ✅ | ✅ | ✅ | ✅ | inline entities in all |
| Spoiler | ✅ | ✅ | ✅ | ✅ | |
| Marked / highlight, sub/superscript | ➖ | ✅ | ✅ | ✅ | rich-only inline |
| Inline code / code block | ✅ | ✅ | ✅ | ✅ | fenced blocks get lang highlight |
| Links, `tg://` links | ✅ | ✅ | ✅ | ✅ | validate URL scheme |
| Block quote / expandable quote | ✅ | ✅ | ✅ | ✅ | rich expandable block: 10.3 |
| Pull quote | ➖ | ✅ | ✅ | ✅ | rich-only |
| Headings (H1–H6) | ➖ | ✅ | ✅ | ✅ | levels render differently |
| Lists (ordered/unordered) | ➖ | ✅ | ✅ | ✅ | `InputRichBlockList` + `ListItem` |
| Task lists `- [ ]` / `- [x]` | ➖ | ✅ | ✅ | ✅ | |
| Divider / horizontal rule | ➖ | ✅ | ✅ | ✅ | `---` in Rich Markdown |
| Tables | ➖ | ✅ | ✅ | ✅ | `InputRichBlockTable`; header cells via `is_header` (render bold); `align`/colspan/rowspan; column cap 20 (official) |
| Details (collapsible) | ➖ | ✅ | ✅ | ✅ | |
| Anchors / references / footnotes | ➖ | ✅ | ✅ | ✅ | |
| Math (LaTeX inline `\(…\)` / block `\[…\]`) | ➖ | ✅ | ✅ | ✅ | `MathematicalExpression` |
| Footer | ➖ | ✅ | ✅ | ✅ | |
| Photo / video / animation / audio / voice | caption only | ✅ | ✅ | ✅ | inline media blocks |
| Collage / slideshow | ➖ | ✅ | ✅ | ✅ | grouped media |
| Map | ➖ | ✅ | ✅ | ✅ | `InputRichBlockMap` |
| Thinking block | ➖ | ✅ | ✅ | ✅ | drafts only; real stage labels, never model reasoning |
| Buttons (row / inline in text) | ➖ | ➖ | ✅ | ✅ | 10.3 |
| Document block, `tg://document` | ➖ | ✅ | ✅ | ✅ | 10.3 |
| Compact table | ➖ | ➖ | ✅ | ✅ | 10.3 `is_compact` |
| Custom emoji | ✅ | ✅ | ✅ | ✅ | premium/custom emoji id |
| RTL awareness | limited | ✅ | ✅ | ✅ | see `localization-and-rtl.md` |
| Precise offset control | via entities | ➖ | ➖ | ✅ | blocks are typed, not parsed |

## Regular formatting quick reference

- **Regular HTML tags (whitelist):** `b`/`strong`, `i`/`em`, `u`/`ins`,
  `s`/`strike`/`del`, `span class="tg-spoiler"` (or `tg-spoiler`), `a href`,
  `code`, `pre`, `pre><code class="language-…">`, `blockquote`,
  `blockquote expandable`, `tg-emoji emoji-id`. No other tags/attributes.
- **MarkdownV2:** escape these outside entities with `\`:
  `` _ * [ ] ( ) ~ ` > # + - = | { } . ! ``. Inside `pre`/`code` escape `` ` ``
  and `\`; inside `(...)` link/emoji URLs escape `)` and `\`. See
  `security-and-escaping.md`.
- **MessageEntity:** `type` + `offset` + `length` in **UTF-16 code units**.
  Types include bold, italic, underline, strikethrough, spoiler, blockquote,
  expandable_blockquote, code, pre, text_link, text_mention, custom_emoji,
  mention, hashtag, cashtag, bot_command, url, email, phone_number, date_time,
  bank_card_number and ton_address (both 10.4).

## Authoring conventions (styling defaults)

Apply these by default when generating rich content, so output looks intentional
and consistent. Verify exact field names against the official object for the
project's Bot API version.

### Tables

> **Tables are this skill's first-priority output. For the full build guide
> (Rich Markdown / Rich HTML / `InputRichBlockTable` code, split rules, escaping,
> and the monospace fallback), read `tables.md`.** The essentials:

- **Header row bold:** mark header cells with **`is_header: true`** (clients
  render header cells bold) — in Rich HTML use **`<th>`** for header cells and
  `<td>` for body; in Rich Markdown the first row (above the `---|---` separator)
  is the header. Don't fake a header with manual bold on plain `<td>`/cells —
  use the header semantics so it renders and exports correctly.
- **Alignment:** set cell `align` (`left`/`center`/`right`) and vertical
  alignment (`top`/`middle`/`bottom`); align numeric columns right, text left.
- **Spanning:** use colspan/rowspan (cell field > 1) for merged cells rather than
  padding with empty cells.
- **Splitting:** never split a table mid-row; if a table must span messages,
  **repeat the header row** in each part and keep it with its body
  (`limits-and-splitting.md`). Stay within the column cap.

### Everything else (defaults)

- **Section titles → heading blocks** (`SectionHeading` / `#…` / `<h1–h6>`), not
  a bold paragraph.
- **Code blocks → always set the language** for syntax highlighting
  (`pre><code class="language-…">` / ```` ```lang ````).
- **Links → descriptive anchor text**, not a bare URL; control the preview with
  `link_preview_options` (`regular-formatting.md`).
- **Quotes → blockquote**; make long quotes expandable.
- **Emphasis → sparing and consistent** (don't bold whole paragraphs); use
  bold for labels/headers, italic for asides.
- **Lists → real list blocks**; use task lists (`- [ ]`/`- [x]`) for actionable
  items.
- **Media → captions** (and `credit`/spoiler where relevant); place media blocks
  in reading order (`rich-media.md`).
- **RTL → mark direction by content**, keep LTR islands intact
  (`localization-and-rtl.md`).

## Do / don't

- **Do** choose blocks when you need typed generation, CMS output, or to avoid
  parser ambiguity; choose Rich Markdown/HTML for naturally-authored documents.
- **Don't** call any of this "RTF". Don't treat Rich Markdown as MarkdownV2.
- **Don't** assume the whole feature set below your project's Bot API version is
  available — verify the version first (`project-adaptation.md`,
  `sdk-compatibility.md`).

## Bot API 10.3 / 10.4 rich additions

Verified 2026-11-12. Output (`RichBlock*`) and input (`InputRichBlock*`) types mirror each other.

| Feature | Rich HTML | Block JSON | Notes |
|---|---|---|---|
| Button row (10.3) | `<tg-button-row align="left"><tg-button type="callback_data" data="…" style="link">…</tg-button></tg-button-row>` | `{"type":"buttons","buttons":[RichMessageButton…],"align":"left"}` | 1–8 buttons; see `buttons-and-styles.md#three-button-models` |
| Button in text (10.3) | `<tg-button …>` inside a paragraph | `{"type":"button","button":{…}}` (`RichTextButton`) | text: plain, custom emoji, date-time |
| Disabled button | `<tg-button type="disabled">` | `"disabled": {}` | |
| Compact table (10.3) | `<table compact>` | `"is_compact": true` | `tables.md#compact-tables` |
| Expandable quote (10.3) | `<blockquote expandable>…<cite>…</cite></blockquote>` | `{"type":"expandable_blockquote","text","credit?"}` | |
| Document (10.3) | `<tg-document src="…">` / Markdown `![](file "caption")` | `{"type":"document","document":InputMediaDocument,"caption?":{text,credit?}}` | |
| `tg://document?id=X` (10.3) | in markdown/html, bound by `media: [{id:"X", media: InputMediaDocument}]` | — | ids 1–64 of `A-Za-z0-9_-` |
| TON address (10.4) | — (received) | `{"type":"ton_address","text","address"}` (`RichTextTonAddress`) | read `address` |

Rich drafts can't upload new files or fetch by URL. `scripts/validate_rich.py` checks limits,
draft rules, media references and buttons.

## Quotes from rich messages

10.4: a reply quoting a rich message has `TextQuote.text == ""` (possibly) and the fragment in
`TextQuote.rich_texts` — code that reads only `quote.text` loses it (`tgkit.rich.quote_text`).
To quote back, `ReplyParameters.quote_rich_texts`: one element per quotable text in order (first
and last may be partial), formatting and nesting as received, ≤ 32 texts and ≤ 1024 characters,
buttons/anchors/dividers not quotable; when set, `quote`/`quote_parse_mode`/`quote_entities` are
ignored. Builder: `tgkit.rich.quote_from_paragraph`.
