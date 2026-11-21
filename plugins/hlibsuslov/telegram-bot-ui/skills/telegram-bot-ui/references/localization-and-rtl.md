# Localization and RTL

The whole interface — message text, button labels, command descriptions — must
survive translation and mixed text direction. Localized strings are **untrusted
input** for the target format: escape them at the boundary.

## The interface is localized, not just the text

- **Button labels** go through the same catalog as message text. A hardcoded
  label inside a keyboard builder is the most common localization leak.
- **Command descriptions** are localized via `setMyCommands` with
  `language_code` (and scoped with `BotCommandScope*`) — a separate call per
  language, easy to forget when copy changes.
- **Reply-keyboard routing must not depend on the displayed label** — resolve
  incoming text through the catalog or a stable key, or the bot works in English
  only (`reply-keyboards.md`).
- **Layout must survive the longest translation.** German, Finnish, and Russian
  labels routinely run 30–60% longer than English; a 3-button row that fits in
  English truncates elsewhere. Design rows against the longest locale, not the
  source one.
- **Emoji and icons are localization-neutral, words are not** — never solve a
  length problem by deleting the word and keeping the emoji.
- **Formality is a per-language decision** (formal vs informal address). Pick one
  per locale and hold it across every string, including buttons.
- **Dates and times:** prefer the `date_time` entity so the client renders in the
  reader's locale and timezone instead of a server-formatted string
  (`navigation-and-flows.md`). Otherwise state the timezone explicitly.
- **Names are user data,** not translatable strings — escape them, and expect
  RTL or emoji-only names (`personalization-and-links.md`).

## What to check in localized templates

- Templates that mix markup with **interpolated variables** — a translator may
  move or break the markup around a placeholder. Prefer placeholders that don't
  sit inside fragile markup; validate rendered output per locale.
- **Cyrillic** and other Latin-adjacent scripts — usually fine, but still escape.
- **Arabic / Persian / Hebrew** (RTL) — direction, punctuation mirroring,
  and placement of LTR runs (numbers, URLs, usernames, code) inside RTL text.
- **Mixed RTL/LTR** — the hardest case; see below.
- Numbers, URLs, `@usernames`, emoji, inline code, formulas, tables, lists,
  quotes — all render inside a direction context and can look reversed or
  mis-grouped.

## RTL guidance

- Do **not** decide direction solely from the UI language. The **message
  content** may be a different direction (e.g. an English quote inside an Arabic
  message, or vice versa).
- Use the `is_rtl` signal where the Bot API/objects expose it (verify for your
  version) to mark direction explicitly rather than guessing.
- Keep **LTR islands** (numbers, URLs, code, usernames) intact within RTL text;
  they should not be visually reordered. Where needed and supported, use
  directional isolation so an LTR span doesn't flip surrounding RTL punctuation.
- For **tables** and **lists** in RTL, confirm column/marker order renders as
  intended per locale.

## Escaping and localization together

- Escape each localized string for the **specific target format** (HTML vs.
  MarkdownV2 vs. Rich HTML vs. Rich Markdown) — not once, generically.
- Never let a translated string introduce unescaped control characters that
  reinterpret as structure (a stray `_`, `*`, `|`, `#`, `<`).
- For structured localized content, prefer **explicit blocks** so translated text
  is treated as data, not markup.

## Testing localization

Cover at minimum: Latin, Cyrillic, Arabic/Persian/Hebrew, mixed-direction,
emoji, and combining characters — for each format the project uses. Verify that
placeholders, entities/offsets, and split boundaries stay correct per locale,
that every button label exists in every locale, and that the longest label still
fits its row. See `testing-playbook.md`.
