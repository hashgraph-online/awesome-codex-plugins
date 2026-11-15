# Security and escaping

> **One escaping function per format.** A single universal escaper is a bug: the
> rules for MarkdownV2, HTML, Rich HTML, and blocks are mutually incompatible.
> Escaping must be **context-aware** (text vs. code vs. URL vs. attribute).

## Golden rules

- Escape at the **boundary** where dynamic data enters a specific format, once.
- Track whether a string is already escaped to prevent **double escaping**.
- Never pass **arbitrary or AI-generated HTML/Markdown** straight to Telegram.
  Convert through a controlled builder and whitelist.
- Whitelist **tags**, **attributes**, and **URL schemes**. Reject everything else.
- Treat **all** of the following as untrusted: user input, AI output, localized
  strings, external API data, file names, usernames.
- Compute offsets/lengths in **UTF-16 code units**.
- Never log bot tokens or full personal message text.

## Per-format escaping

### Plain text
No markup, but beware: if this text is later embedded into an HTML/MarkdownV2
template, it must be escaped **at that point** for the target format. Plain text
sent as plain text needs no escaping; only length/splitting matters.

### Regular HTML (`parse_mode=HTML`)
- Escape in text nodes: `&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`.
- Attribute values (e.g. `href`) additionally need `"` handled; only emit
  attributes from a whitelist and validate the URL scheme.
- **Allowed tags:** `b`,`strong`,`i`,`em`,`u`,`ins`,`s`,`strike`,`del`,
  `span class="tg-spoiler"`/`tg-spoiler`, `a`, `code`, `pre`,
  `pre><code class="language-…">`, `blockquote`, `blockquote expandable`,
  `tg-emoji`. Nothing else. Unknown tags → escape or strip, never forward.

### MarkdownV2 (`parse_mode=MarkdownV2`)
- In normal text, escape each of these with a preceding `\`:
  `_ * [ ] ( ) ~ ` `` ` `` `> # + - = | { } . !`
- **Inside** `` `inline code` `` and ```` ```code blocks``` ````: escape only
  `` ` `` and `\`.
- **Inside** a link/emoji URL `(...)`: escape `)` and `\`.
- Because escaping is so error-prone with user input, prefer HTML or
  MessageEntity for untrusted content unless MarkdownV2 is mandated.

### Rich Markdown (`InputRichMessage.markdown`)
- Different syntax from MarkdownV2 — do **not** reuse the MarkdownV2 escaper.
- Escape the Rich Markdown control characters/sequences (headings `#`, fences,
  table pipes `|`, list markers, math delimiters `\( \) \[ \]`, `---`) inside
  dynamic text so authored content isn't reinterpreted as structure.
- For untrusted structured content, prefer **explicit blocks** over injecting raw
  markdown, so nothing is re-parsed.

### Rich HTML (`InputRichMessage.html`)
- Same discipline as Regular HTML plus the rich-only tags your Bot API version
  supports. Whitelist the exact supported tag/attribute set from official docs.
- Validate every `href`/media URL scheme. Strip disallowed tags rather than
  forwarding them.

### MessageEntity
- No character escaping (there is no parse_mode), but **offsets/lengths must be
  UTF-16 code units** computed against the exact final string. A single
  4-byte emoji (surrogate pair) counts as length 2. Off-by-one here is the most
  common `can't parse entities` cause with entities.
- Validate that entities don't overlap illegally and stay within bounds.

### Explicit blocks (`InputRichMessage.blocks`)
- Safest for untrusted structured data: each text field is data, not markup.
- Still validate URLs, media references, nesting depth, and per-block limits.

## URL scheme whitelist

Allow only expected schemes, typically: `http`, `https`, `tg`, and `mailto`.
Reject `javascript:`, `data:`, and unknown schemes. Validate `tg://…` targets
(e.g. `tg://user?id=`, `tg://emoji?id=`, media `tg://photo?id=`).

## Unicode / emoji / combining characters

- Normalize as the project does; be consistent so offsets stay stable.
- Count surrogate pairs correctly for entity offsets and for length limits.
- Don't split inside a grapheme cluster / combining sequence (see
  `limits-and-splitting.md`).

## AI-generated content

- Never trust AI HTML/Markdown structurally. Route it through: convert →
  whitelist → build blocks or safe HTML → validate → send.
- Strip or neutralize unsupported constructs instead of forwarding them.
- Guard against prompt-injected markup designed to break rendering or leak links.

## Security checklist

- [ ] Exactly one escaper per format is used; no universal escaper.
- [ ] Escaping is applied once at the boundary; double escaping prevented.
- [ ] Tags, attributes, and URL schemes are whitelisted.
- [ ] User input, AI output, localized strings, external data are all escaped.
- [ ] Rich HTML / Rich Markdown use their own rules, not the MarkdownV2 escaper.
- [ ] Offsets/lengths computed in UTF-16 code units; emoji/surrogates handled.
- [ ] AI HTML is never forwarded raw; it is rebuilt through a whitelist.
- [ ] Unsupported tags/constructs are stripped, not passed through.
- [ ] No bot token, no full personal text in logs.
- [ ] Untrusted structured content prefers explicit blocks over injected markup.
