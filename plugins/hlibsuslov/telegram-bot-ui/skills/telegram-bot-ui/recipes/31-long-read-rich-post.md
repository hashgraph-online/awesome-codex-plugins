# 31 — Long read as one Rich Message

Registry rows: none (channel publishing combines existing methods; see `references/publishing-pipeline.md`). Verified 2026-11-15, Bot API 10.4 (newest on that date).

1. **Request and visible result.** “Our quarterly report is 5,000 characters with a table. Today it is 3 messages and a screenshot of a spreadsheet.” — One channel post: title heading, sections, a compact table with right-aligned numbers, an expandable official quote, the PDF attached inside the post, a footer and a button row (Report a pothole / Copy data link).
2. **Why these features.** Rich Messages (10.1) hold up to 32768 characters in one message; 10.3 added `is_compact` tables, `expandable_blockquote`, `document` blocks and embedded button rows (`InputRichBlockButtons`). A split regular message loses structure and notifies several times.
3. **Requirements.** Bot API ≥ 10.3. Production. Channels accept `sendRichMessage`; media blocks need the right to send that media. Limits: 32768 chars, 500 blocks, 16 levels, 50 media, 20 columns. No `link_preview_options` on `sendRichMessage`.
4. **Payload.** `examples/payloads/r31-long-read-rich-post.json` (preview to the editor, then the channel). Key part:
   ```json
   {"type": "table", "is_compact": true, "is_bordered": true, "caption": "Median, 1 Jul – 30 Sep 2026", "cells": [[{"text": "District", "is_header": true}]]},
   {"type": "expandable_blockquote", "blocks": [{"type": "paragraph", "text": "Old Town streets are narrow…"}], "credit": "Maintenance department, 2 Oct 2026"},
   {"type": "document", "document": {"type": "document", "media": "BQACAgIAAxkBAAIBdemoReportPdf"}, "caption": {"text": "Full data set (PDF, 14 pages)"}},
   {"type": "buttons", "buttons": [{"text": "Report a pothole", "url": "https://example.com/report", "style": "primary"}, {"text": "Copy data link", "copy_text": {"text": "https://example.com/data/q3-2026"}}]}
   ```
   The same post as **Rich Markdown** (`rich_source: "markdown"`, steps 3 of the payload file). Features with no Markdown syntax — compact table, expandable quote with credit, footer, buttons — are written as the documented HTML tags inside the Markdown:
   ```markdown
   # Potholes Q3 2026: Riverside is fastest, Old Town still slowest
   Every quarter we compare how fast the five city districts fix potholes after a report. …
   ## Days from report to repair
   <table bordered compact><caption>Median, 1 Jul – 30 Sep 2026</caption><tr><th align="left">District</th><th align="right">Reports</th>…</tr>…</table>
   <blockquote expandable>Old Town streets are narrow…<cite>Maintenance department, 2 Oct 2026</cite></blockquote>
   ![](tg://document?id=doc1 "Full data set (PDF, 14 pages)")
   ---
   <footer>Data: city open data portal. <i>Next issue in January.</i></footer>
   <tg-button-row><tg-button type="url" url="https://example.com/report" style="primary">Report a pothole</tg-button><tg-button type="copy_text" text="https://example.com/data/q3-2026">Copy data link</tg-button></tg-button-row>
   ```
   And as **Rich HTML** (`rich_source: "html"`, step 4):
   ```html
   <h1>Potholes Q3 2026: Riverside is fastest, Old Town still slowest</h1>
   <p>Every quarter we compare how fast the five city districts fix potholes after a report. …</p>
   <h2>Days from report to repair</h2>
   <table bordered compact><caption>Median, 1 Jul – 30 Sep 2026</caption>…</table>
   <blockquote expandable>Old Town streets are narrow…<cite>Maintenance department, 2 Oct 2026</cite></blockquote>
   <figure><tg-document src="tg://document?id=doc1"></tg-document><figcaption>Full data set (PDF, 14 pages)</figcaption></figure>
   <hr/>
   <footer>Data: city open data portal. <i>Next issue in January.</i></footer>
   <tg-button-row>…</tg-button-row>
   ```
   Both text sources carry the file in `media: [{"id": "doc1", "media": {"type": "document", "media": "BQAC…"}}]`. **Which to author in an automated pipeline:** **blocks** when posts are generated from data (no escaping, validated field by field — the default); **Rich HTML** when a server template or CMS produces text (one escaper for `& < > "`, every feature has a tag, attributes like `compact` / `expandable` are explicit); **Rich Markdown** when people or a model write the body (short, readable in review diffs), keeping in mind that several features still need HTML tags and that escaping beyond the documented `\#` follows CommonMark practice **[Unverified]**. Never interpolate untrusted text into a Markdown or HTML source without the matching escaper (`to_rich_markdown` / `to_rich_html` do it for you).
5. **Code.** `examples/python/tgkit/publish.py` (`to_rich_blocks`, `to_rich_markdown`, `to_rich_html`, `rich_message`, `rich_size`, `resolve_kind`), `examples/python/tgkit/rich.py` (table, quote, document, buttons), `examples/python/recipes/r31_long_read_rich_post.py`.
6. **Sequence and state.** content model → `resolve_kind` = rich (table + headings) → `validate` (limits, rich button rules) → `sendRichMessage` to the editor's private chat (preview) → approval → `sendRichMessage` to the channel → ids in the ledger → later fixes with `editMessageText(rich_message)`.
7. **Result.** Mock-up: # Potholes Q3 2026… / paragraphs / ## Days from report to repair / compact table / ## How we counted / ▸ quote (collapsed) / 📄 Full data set (PDF) / — / footer / [Report a pothole] [Copy data link].
8. **Typical mistake, limits, alternative.** A monospace “table” in `<pre>`; splitting into 3 posts; a `web_app` button (private chats only, refused by `validate`); `style: "link"` on a URL button (callback only); expecting a link preview card. Alternative for older SDKs: send the raw payload (`references/sdk-compatibility.md`) or a regular post + PDF document.
9. **Run and verify.** `py -3 examples/python/recipes/r31_long_read_rich_post.py` · `tests/test_publishing.py` (`PayloadShapes.test_rich`, `ChannelRules.test_rich_limits`). Evidence: offline contract; rich rendering on real clients not verified.
10. **Adapt.** Generate blocks from your CMS/AST; keep tables ≤ 20 columns and compact on phones; attach files by `file_id`; one primary button. Related: `references/telegram-capabilities.md`, `references/tables.md`, R02.
