# 02 — Interactive document: compact table, expandable quote, attached file, buttons, quoting

Registry rows: `10.4-Q01`, `10.4-Q02`, `10.4-X02`, `10.3-R01`, `10.3-R02`, `10.3-R03`, `10.3-R04`, `10.3-R05`, `10.3-R06`, `10.3-R07` (`recipes/registry.json`). Verified 2026-11-12, Bot API 10.4.

1. **Request and visible result.** “Send the policy as a proper document: a status table, the long auditor note folded, the PDF attached, an Approve button — and when someone quotes a line, answer that line.” — One rich message: heading, compact table, collapsed note, PDF block, an inline “Ask the owner” button inside the sentence, a button row [Approve] [Copy checklist id]. After Approve the button turns into a disabled “Approved”. A reply quoting “signing key” gets an answer that quotes exactly that fragment.
2. **Why the new feature.** 10.3 adds buttons, `is_compact`, expandable quotations and documents *inside* rich messages (before: a separate file message and a keyboard under the whole document). 10.4 lets the bot read and send quotes from rich messages (`TextQuote.rich_texts`, `quote_rich_texts`).
3. **Requirements.** Bot API ≥ 10.3 (quotes ≥ 10.4). Production, any chat where the bot may send rich messages (media rights for the document). Ephemeral/inline limits: see validator contexts.
4. **Payload.** Full request sequence: `examples/payloads/r02-interactive-document.json` (generated from the code); incoming fixture: `examples/fixtures/message_quote_rich.json`. Key part:
   ```json
   {"type": "buttons", "align": "left", "buttons": [
     {"text": "Approve", "callback_data": "doc:approve:v3", "style": "success"},
     {"text": "Copy checklist id", "copy_text": {"text": "ROT-2026-v3"}}]}
   ```
5. **Code.** `examples/python/tgkit/rich.py` (builders, `quote_text`, `quote_from_paragraph`, `find_ton_addresses`), `examples/python/recipes/r02_interactive_document.py`, TS `examples/ts/recipes.ts::interactiveDocument`. Validate with `scripts/validate_rich.py`.
6. **Sequence and state.** sendRichMessage(blocks) → message_id → user replies with a quote (`quote.text` == "", `rich_texts`) → bot replies with `reply_parameters.quote_rich_texts` → Approve callback → answerCallbackQuery → editMessageText(rich_message with disabled button).
7. **Result.** Mock-up: `## Key rotation policy v3 · [compact table] · ▸ Auditor note… · 📄 Full procedure (PDF) · [Approve] [Copy checklist id]`.
8. **Typical mistake, limits, alternative.** Reading only `quote.text` (empty for rich quotes); `style: link` on a URL button; `pay`/`icon_custom_emoji_id` on rich buttons; > 8 buttons in a row; uploading a new file inside a draft. Alternative: regular message + document message + inline keyboard.
9. **Run and verify.** py -3 examples/python/recipes/r02_interactive_document.py · tests/test_text_and_rich.py · tests/test_keyboard_validator.py. Evidence: offline contract.
10. **Adapt.** Copy the builders; adapt the content mapping; keep callback data stable (`doc:approve:<version>`). Related: `tables.md`, `telegram-capabilities.md#bot-api-103--104-rich-additions`, 04 (personal view of the same doc).
