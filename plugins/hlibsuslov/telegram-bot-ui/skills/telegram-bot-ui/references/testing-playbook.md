# Testing playbook

> Use the **project's existing test infrastructure**. Do not add a new test
> framework unless the project has none and one is required. Do not send real
> messages or use a real bot token in tests — assert on the **payload** your code
> would send (rendered string, entities, blocks, split parts).

## What to assert

- The **`reply_markup` payload**: rows, labels, action fields, `style` values,
  `icon_custom_emoji_id`, and that every `callback_data` is unchanged and ≤64
  bytes.
- Rendered output string for the chosen `parse_mode`, or the `entities[]` array,
  or the `InputRichMessage` (`markdown`/`html`/`blocks`) structure.
- Split parts: count, boundaries, offsets, preserved keyboards/reply/topic.
- Fallback path selection per failure class.

## Keyboards and UI

- **Structure:** exactly one action field per inline button; ≤1 non-text field
  per reply button; no duplicate labels within a keyboard.
- **Payload stability:** a golden/snapshot test asserting the set of
  `callback_data` values a screen emits — this is what catches an accidental
  scheme change during a redesign.
- **`style`:** only `primary` / `success` / `danger`; at most one `primary` per
  screen; `danger` reachable only through a confirmation screen.
- **Degraded render:** the keyboard with `style` and `icon_custom_emoji_id`
  stripped is still unambiguous (assert on labels alone).
- **Custom emoji:** IDs come from config/fixtures, never literals invented in
  tests; the no-ID path builds a valid button.
- **Navigation:** every screen reachable, every non-root screen has a Back
  target that exists; no `callback_data` without a handler, no handler without a
  producer.
- **State variants:** empty, loading, error, success, stale, and no-permission
  renderings exist for each screen that needs them.
- **Callbacks:** every handler answers the callback query; stale payloads are
  rejected server-side rather than trusted.
- **Local checks:** `python scripts/validate_keyboard.py <file.json>` validates
  keyboard payloads offline (no token, no network).

Local validation runs with any Python 3 (`py -3` on Windows).

## Regular formatting

plain text · HTML · MarkdownV2 · entities · arbitrary user input · special
characters · links · emoji · code · spoilers · block quotes · long messages.

## Rich Markdown

headings · emphasis · lists · task lists · tables · quotes · code blocks ·
formulas · details · references · media.

## Rich HTML

supported tags · unsupported tags (stripped/escaped) · nesting · escaping ·
malformed input · unsafe attributes · URL validation · media references.

## Blocks

paragraph · heading · list · table · quotation · details · mathematical
expression · media · invalid nesting · over-limit (blocks/depth/columns/media).

## Streaming and progress

start · multiple updates · completion · cancellation · timeout · 429 backoff ·
final-send failure. Assert throttling (no per-token edits), stable `draft_id`
reuse, that a draft is always finalized with a real `sendMessage` — including on
the error path — and that the fallback ladder (rich draft → draft → edit →
chat action) is exercised, not merely written.

## Localization

Latin · Cyrillic · Arabic/Persian/Hebrew · mixed direction · emoji · combining
characters. Assert placeholders, offsets, and split boundaries per locale.

## Regression cases (must-have)

- `can't parse entities`.
- wrong entity offset (UTF-16/surrogate off-by-one).
- unclosed tag.
- broken link split across parts.
- code block split mid-fence.
- double escaping.
- lost keyboard on split/edit.
- HTML shown as literal text (wrong/absent parse_mode).
- corrupted localized template.
- over-limit payload.
- `message is not modified` on edit.
- `callback_data` over 64 **bytes** (non-ASCII label accidentally used as a
  payload).
- two action fields on one inline button.
- invalid `style` value reaching the wire.
- SDK silently dropping `style` / `icon_custom_emoji_id` (assert on the outgoing
  request, not on the builder's return value).
- button label truncated in the longest locale.
- callback query never answered.
- streamed draft left unfinalized after a generation error.

## Manual pass (what automation can't cover)

Render the changed screens on **Android, iOS, Desktop, and Web**: row widths and
truncation, color rendering, custom emoji presence, draft/thinking animation,
edit flicker, and RTL layout. Note any client where the result differs — this is
the evidence that belongs in the report.

## Verification checklist before "done"

- [ ] Tests cover each format the change touches.
- [ ] Regression cases above are represented where relevant.
- [ ] No real bot token, no real network sends in tests.
- [ ] Project lint / typecheck / test / smoke commands run and pass.
- [ ] Evidence (command output) captured for the final report.
