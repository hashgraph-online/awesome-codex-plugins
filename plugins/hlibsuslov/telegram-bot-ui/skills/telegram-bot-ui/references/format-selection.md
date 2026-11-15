# Format and surface selection

> Core rule: **pick the format by what the reader has to do with the content** — compare,
> scan, act, read, keep — not by which format is richest. Real tables remain the first choice
> for genuinely tabular data (compare across columns); a short list of facts stays a list.
> Verified against Bot API 10.4 on 2026-11-12. Match the project's existing formatter.

## Choosing the surface

Three different "HTML"s exist and never mix: regular-message `parse_mode=HTML`, **Rich HTML**
(`InputRichMessage.html`), and **widget HTML** (a sandboxed document in `sendWidget`).

| Surface | Choose when | Move to the alternative when |
|---|---|---|
| Regular message (+ HTML / entities) | prompts, statuses, short answers, anything in a menu flow | content gains structure (headings, tables) → rich |
| Rich Message (document) | reports, AI answers, docs, tables, math, attached files | the user must act inside it repeatedly → embedded buttons / widget |
| Inline keyboard | discrete choices, navigation, confirmations | choices need live visual state → widget |
| Rich embedded buttons (`<tg-button-row>`, `RichTextButton`) | actions that belong to a specific section of a document | the action is screen-level navigation → inline keyboard under the message |
| Ephemeral message | one member's private view in a shared chat | it must persist or be proven → private chat / storage |
| Widget (10.4; production: private chats) | a compact card whose state changes in place, taps/drags on a custom layout | text input, network, > 600 px, groups in production → Mini App / keyboard |
| Mini App | forms with typing, long flows, network data, full-screen UI | a single choice → keyboard |

## Decision criteria (ask in order)

1. **Task:** what must the reader do — decide, compare, follow steps, read, copy, act?
2. **Shape:** ≥ 2 attributes per item that people compare across items → **table**;
   ≤ ~5 label→value facts read once → a short list or bold labels; prose → paragraphs.
3. **Volume:** fits one screen? Long → headings + expandable quote/details, or split.
4. **Phone width:** > 4–5 columns or long cells → compact table, fewer columns, or one card per item.
5. **Actions:** does it carry buttons? Screen-level → inline keyboard; section-level → rich buttons.
6. **Accessibility & support:** every rich/widget surface needs a readable text fallback;
   check the SDK and Bot API version (`sdk-compatibility.md`).
7. **Cost:** a second formatter or surface must earn its maintenance; reuse the project's.

Examples: price list of 12 items × (size, price, kcal) → compact table. "Order #1042: 2 items,
$23.50, ready at 19:40" → three short lines, not a table. A 3-step how-to → numbered list.

## Format by content (escape hatches stay valid)

1. Tabular data → table (`tables.md`): Rich Markdown table, Rich HTML `<table>`, or `InputRichBlockTable`.
2. Structured document → Rich Markdown (authored) / Rich HTML (templated) / blocks (generated).
3. Standalone media → media methods (`rich-media.md`).
4. Short prompt or status in an interactive flow → regular HTML (or MarkdownV2 if that is the project standard).
5. Programmatic styling of untrusted text → `MessageEntity` (UTF-16 offsets).
6. No styling → plain text.

## Per-format guidance

### Tables
The first choice for data people compare across columns. Build with a Rich Markdown
pipe table, a Rich HTML `<table>`, or explicit `InputRichBlockTable` blocks —
pick by how the data arrives (authored text vs. server template vs. programmatic
rows). Full guidance, code for all three paths, header/alignment/split rules, and
the monospace fallback: **`tables.md`**.

### Plain text
Zero markup. Cheapest and safest. Prefer for logs, one-line statuses, and any
message where styling adds nothing. Still split long text safely.

### Regular HTML
Best default for compact, predictable styling in interactive flows *if HTML is
already the project's convention*. Whitelist tags/attrs; escape `< > &` in
dynamic parts. Predictable and easy to test.

### MarkdownV2
Only when already the project standard or genuinely best. Every reserved char in
dynamic text must be escaped (`security-and-escaping.md`). Easy to break with
user input; prefer HTML or entities for user-supplied content unless MarkdownV2
is mandated.

### MessageEntity
When you need exact `offset`/`length` control, want no parse_mode, or must
safely interleave untrusted text with styling. Offsets are **UTF-16 code units** —
compute them from the final string, accounting for surrogate pairs (emoji).

### Rich Markdown
For complex, document-like content that is natural to write as Markdown: AI
replies, articles, headings, tables, task lists, formulas, structured docs. Put
it in `InputRichMessage.markdown`. Requires Bot API 10.1+/10.2+; verify support.

### Rich HTML
For complex server-templated content where you want precise control over the
supported Telegram tag set. Put it in `InputRichMessage.html`. Same tag/attr/URL
whitelisting discipline as regular HTML, plus rich-only tags.

### Explicit `InputRichBlock` blocks
For typed generation, CMS/AST output, complex documents, precise structure,
inline media ordering, and to avoid any markdown/HTML parsing ambiguity. Put the
array in `InputRichMessage.blocks`. Most verbose, most deterministic.

### Separate media methods
When the UX is fundamentally a media post — one photo, an album, a document with
a caption. Do **not** also embed the same media in a Rich Message (no
duplication without a product reason). See `rich-media.md`.

## Anti-patterns

- Rendering genuinely tabular data as a monospace `pre` grid or bullets.
- Forcing a table onto 2–3 facts read once — a short list is easier on a phone.
- Blanket-replacing every `sendMessage` with `sendRichMessage`, or every keyboard with a widget.
- Treating Rich Markdown as MarkdownV2, or Rich HTML / widget HTML as regular `parse_mode=HTML`.
- Masking a payload defect by cycling through formats; fix the payload (`errors-and-fallbacks.md`).
- Introducing a second formatter when one already exists in the project.

## Migration stance

Migrate structured content that loses its structure today (broken pseudo-tables, AI answers
flattened to text) first. Leave short messages on their simple format. Keep the old formatter
until the new path is covered by tests, then remove it in its own step.
